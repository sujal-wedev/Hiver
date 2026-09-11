# BUILD BRIEF: Twitter Customer-Support AI Agent (Hiver Take-Home)

Give this whole file to the coding agent as the master spec. It should build
the repo, run the pipeline on a subsample, and produce all deliverables.
Follow the milestone order — don't let the agent jump to polishing the LLM
prompts before the data pipeline and eval set exist, that's how you end up
with a system nobody can trust.

---

## 0. Ground rules for the build

- Target brand: **AmazonHelp** (from the Kaggle `thoughtvector/customer-
  support-on-twitter` dataset). If, after EDA, this brand's volume/diversity
  looks poor, it's fine to swap to `Uber_Support` or `SpotifyCares` — but
  that decision must be logged with a one-line reason in `decision_log.md`.
- Use a **subsample**, not the full ~3M rows. Target: all rows involving the
  chosen brand (should be tens of thousands), further subsampled to ~5,000
  reconstructed customer↔brand threads for pipeline dev, since grading
  explicitly expects a subsample.
- Language model: use whatever API is available (Anthropic/OpenAI/local). All
  prompts must be stored as separate files in `prompts/`, not inlined in
  Python strings — this makes them auditable and diffable, which matters
  when you're asked to explain your own code live.
- Every random process (sampling, k-means, train/test-style splits) must take
  a `--seed` flag, default fixed, logged in the README.
- No component should require the full dataset in memory. Stream/chunk the
  CSV read.
- Every deliverable must be reproducible via `make <target>` or a documented
  script — the README's 15-minute reproduction claim needs to actually be
  true when someone else clones the repo cold.

---

## 1. Repo structure

```
support-agent/
├── README.md
├── report.md                    # max ~6 pages rendered
├── decision_log.md
├── Makefile
├── requirements.txt
├── data/
│   ├── raw/                     # gitignored, download target
│   ├── processed/
│   │   ├── amazonhelp_threads.parquet
│   │   └── amazonhelp_customer_msgs.parquet
├── golden_set/
│   ├── golden_eval_v1.csv       # 150-250 hand-labeled rows
│   └── labeling_notes.md        # sampling + labeling protocol, self-consistency check
├── src/
│   ├── data_prep.py             # download/filter/thread reconstruction
│   ├── cluster_intents.py       # embedding + k-means for taxonomy discovery
│   ├── taxonomy.py              # frozen intent definitions (post-clustering)
│   ├── retrieval.py             # builds historical reply index for grounding
│   ├── classify_intent.py       # LLM or classical classifier
│   ├── draft_reply.py           # retrieval-augmented reply generation
│   ├── escalation_policy.py     # rule+signal based escalate/auto-handle decision
│   ├── pipeline.py              # end-to-end: msg -> intent, reply, decision
│   └── baselines.py             # trivial + simple baselines
├── eval/
│   ├── metrics.py                # intent accuracy/F1, escalation P/R, confusion matrix
│   ├── llm_judge.py               # LLM-as-judge scoring for reply quality
│   ├── judge_calibration.py       # compares judge scores to your own human ratings
│   └── run_eval.py                # orchestrates full eval, writes results/report tables
├── prompts/
│   ├── intent_classify.txt
│   ├── reply_draft.txt
│   ├── judge_rubric.txt
├── results/
│   ├── metrics_summary.json
│   ├── confusion_matrix.png
│   ├── failure_cases.md
│   └── judge_vs_human_agreement.json
└── notebooks/                    # optional, exploratory only, not load-bearing
```

---

## 2. Milestone 1 — Data prep (`src/data_prep.py`)

1. Download instructions in README (Kaggle requires auth — script should
   accept a pre-downloaded CSV path rather than trying to auth automatically;
   document `kaggle datasets download -d thoughtvector/customer-support-on-
   twitter` as the manual step).
2. Load `twcs.csv`, filter to rows where `author_id == "AmazonHelp"` OR the
   row is part of a thread that includes an AmazonHelp reply.
3. Reconstruct threads using `response_tweet_id` / `in_response_to_tweet_id`
   into (customer_msg, brand_reply, full_thread_context) tuples. Keep only
   threads with exactly one customer message before the first brand reply for
   the core dataset (multi-turn threads can be a stretch goal, flag as such).
4. Clean text: strip @mentions (but log the removed brand handle since it's
   needed to know a message was addressed to AmazonHelp), strip URLs, keep
   emoji (sentiment-relevant), normalize whitespace.
5. Save `amazonhelp_threads.parquet` (customer_msg, brand_reply, thread_id,
   created_at) and a deduped `amazonhelp_customer_msgs.parquet` for sampling.
6. Print and log basic EDA to `results/eda_summary.md`: message count, date
   range, message length distribution, top bigrams — this is cheap and
   useful ammunition for the report's problem-framing section.

---

## 3. Milestone 2 — Intent taxonomy discovery (`src/cluster_intents.py`)

1. Embed a random sample (~1,500-2,000) of customer messages with
   `sentence-transformers/all-MiniLM-L6-v2`.
2. Run k-means sweeping k=6..14, compute silhouette score, output a plot.
3. For the chosen k, sample 15 messages per cluster, use the LLM to propose a
   short label + one-line definition per cluster (`prompts/` should NOT be
   used here — this is a one-off exploratory prompt, keep it in the script).
4. Manually review, merge/split into a final 7-9 intent taxonomy + `other`.
5. Freeze the result in `src/taxonomy.py` as a plain Python dict/enum with
   `name -> definition` — this becomes the single source of truth used by
   labeling, classification, and eval. See `intent-taxonomy-and-labeling-
   plan.md` (attached separately) for a draft starting taxonomy to validate
   against the real clusters — expect to adjust it.

---

## 4. Milestone 3 — Golden evaluation set (`golden_set/`)

Follow the sampling + labeling protocol in the attached
`intent-taxonomy-and-labeling-plan.md` exactly:
- Stratified sample targeting ~15+ per intent, backfilled with random
  sampling to also capture natural frequency.
- 150–250 total rows.
- Columns: `tweet_id, text, primary_intent, secondary_intent, ideal_action
  (auto_handle|escalate), escalation_reason, ambiguity_flag, notes`.
- Re-label a random 10% blind after the fact; compute self-agreement
  (Cohen's kappa) and save to `golden_set/labeling_notes.md`.
- This file is hand-labeled by the human (you), not LLM-generated — the
  agent's job here is to build the sampling script and label-entry
  tooling (e.g. a simple CLI or notebook widget to speed up manual
  labeling), not to auto-generate the labels themselves.

---

## 5. Milestone 4 — Core pipeline

### `src/retrieval.py`
- Build an embedding index (FAISS or simple numpy cosine sim is fine at this
  scale) over historical (customer_msg, brand_reply) pairs, keyed by intent
  where available, else full corpus.
- `retrieve(query, intent, k=3)` returns top-k historical (msg, reply) pairs
  for use as few-shot grounding context.

### `src/classify_intent.py`
- Implement two paths: (a) LLM-based zero/few-shot classifier using
  `prompts/intent_classify.txt` with the frozen taxonomy definitions injected,
  (b) a classical baseline (TF-IDF + logistic regression) trained on a subset
  of the golden set or on LLM-pseudo-labels from Milestone 2's cluster
  assignments — used later as the "simple baseline," not as the shipped
  classifier.
- Output: intent label + confidence/logprob if available.

### `src/draft_reply.py`
- Given customer_msg + classified intent + retrieved historical examples,
  call the LLM with `prompts/reply_draft.txt` to draft a grounded reply.
- Reply must be checked for: no fabricated order numbers/dates/policy claims
  not present in the retrieved context or the message itself (a simple
  regex/heuristic check for things like invented tracking numbers is enough
  — flag, don't try to be exhaustive).

### `src/escalation_policy.py`
- Deterministic, inspectable function, NOT another LLM call as primary logic
  (an LLM call can be an optional secondary signal, but the core policy must
  be explainable in one paragraph).
- Suggested signal set: intent in escalate-prone set (e.g.
  `billing_dispute`, `account_access`), presence of $ amounts / legal
  keywords ("lawyer", "BBB", "chargeback"), thread length > 1 (repeat
  contact), crude negative-sentiment score above threshold, low intent-
  classification confidence.
- Output: `auto_handle | escalate` + a plain-text reason string citing which
  signal(s) fired. This reason string is a deliverable — it must always be
  populated and human-readable.

### `src/pipeline.py`
- Wires the above into `handle_message(text) -> {intent, confidence, reply,
  decision, reason}`. This is the single entry point the eval harness and
  any demo/CLI call.

---

## 6. Milestone 5 — Baselines (`src/baselines.py`)

- **Trivial baseline**: majority-class intent for classification; always
  `escalate` for the decision; a single canned reply template ("Thanks for
  reaching out, we're looking into this and will follow up shortly.") for
  reply generation.
- **Simple baseline**: keyword/regex intent classifier (a dict of keywords
  per intent); canned reply per intent (one template per intent, no
  personalization); escalation via a single rule (e.g. escalate only if $ or
  "lawyer" keyword present, else auto-handle).
- Both baselines run through the same eval harness as the full system for a
  fair comparison table in the report.

---

## 7. Milestone 6 — Eval harness (`eval/`)

### `eval/metrics.py`
- Intent classification: accuracy, macro-F1, confusion matrix (save as PNG).
- Escalation decision: precision/recall/F1 against golden `ideal_action`,
  plus a breakdown of false-negatives (system said auto-handle, human said
  escalate) since those are the costly errors — call this out explicitly.

### `eval/llm_judge.py`
- Rubric-based LLM judge scoring drafted replies on: **correctness/
  groundedness** (does it align with retrieved historical resolution and not
  contradict/fabricate), **tone/appropriateness**, **actionability** (does it
  actually move the issue forward vs. generic non-answer), each 1-5, defined
  in `prompts/judge_rubric.txt`.
- Judge must see: customer message, drafted reply, and the retrieved
  historical context used to ground it (so it can actually assess
  groundedness, not just fluency).

### `eval/judge_calibration.py`
- You (human) score a random 30-50 replies on the same rubric, blind to the
  judge's scores.
- Compute agreement (e.g. Spearman correlation per dimension, or exact/±1
  agreement rate since these are ordinal 1-5 scores). This is mandatory —
  report explicitly whether the judge is trustworthy or just confidently
  wrong, and use whichever result you get honestly, including if the judge
  turns out to be a mediocre proxy.

### `eval/run_eval.py`
- Runs pipeline + both baselines over the golden set, produces
  `results/metrics_summary.json` and the tables referenced by `report.md`.

---

## 8. Milestone 7 — Report (`report.md`, max ~6 pages)

Sections, in this order (do not skip or reorder — these map directly to the
grading rubric):

1. **Problem framing** — what "good" means for AmazonHelp specifically (e.g.
   is a fast generic acknowledgment good, or does it need to be specific?),
   and an explicit list of things deliberately NOT built (e.g. multi-turn
   dialogue management, non-English support, real account/order lookups).
2. **Results vs. baselines** — table: trivial / simple / full system across
   intent accuracy, escalation P/R, judge scores. Include the judge-human
   agreement number here too, framed honestly.
3. **Failure analysis** — top 5 failure modes, each with a real example (raw
   text + system output) and a hypothesis for cause (e.g. "system hallucinates
   a return window because retrieved examples conflated two different policy
   eras" or "sarcasm misclassified as general_complaint_vent's neutral
   cousin").
4. **"What is misleading about my headline number?"** (mandatory) — candidates
   to consider honestly: single-annotator golden set bias; class imbalance
   inflating trivial-baseline accuracy; judge agreement being measured on a
   small n; historical brand replies used for grounding may themselves be
   mediocre (grounded ≠ good); subsample not being representative of full
   3M-tweet distribution; reply quality judged without ground-truth customer
   satisfaction signal.
5. **What you'd do next with one more week** — concrete, prioritized (e.g.
   multi-turn context, active-learning loop for golden set, calibration of
   escalation thresholds against cost-of-error, second annotator for
   inter-rater reliability).

---

## 9. Milestone 8 — Decision log (`decision_log.md`)

Plain bullet list, 10-15 items, each 1-3 sentences: decision + reason.
Non-obvious decisions to make sure are captured (adapt as actual choices are
made during build, this is a starting list):
- Brand chosen and why (or why swapped).
- Intent taxonomy size (why 8, not 20 or 4).
- Multi-intent tweet handling (priority order).
- Escalation policy: deterministic rules vs. LLM judgment call, and why.
- Golden set sampling strategy (stratified + random backfill).
- Single-annotator mitigation approach.
- LLM judge rubric dimensions chosen.
- Why retrieval-based grounding instead of fine-tuning.
- Subsample size and how it was chosen.
- Any prompt-engineering choice that materially changed output quality.
- What was explicitly cut due to time (and why that cut was safe).

---

## 10. Milestone 9 — README

Must include:
- One-paragraph summary of the system.
- Exact setup commands (`pip install -r requirements.txt`, API key env vars).
- Exact commands to reproduce headline results end-to-end, target **under 15
  minutes** on the subsample (state expected wall-clock time).
- Where to find each deliverable (golden set, report, decision log, eval
  results).
- Citation of anything borrowed (libraries, prompt patterns, code snippets
  from docs/StackOverflow/AI assistance) — a short "Attributions" section.

---

## 11. Build order (do not reorder)

1. Data prep + EDA
2. Intent clustering → frozen taxonomy
3. Golden set sampling tool → hand-label (human-in-the-loop, can't be
   automated away)
4. Baselines (trivial + simple) — get these working first, they're cheap and
   define the floor
5. Retrieval index
6. Intent classifier (LLM-based)
7. Reply drafter
8. Escalation policy
9. Full pipeline wiring
10. Eval harness + LLM judge + judge calibration
11. Run everything, generate results/tables
12. Write report + decision log + README last, using actual numbers —
    never write the report before the numbers exist.
