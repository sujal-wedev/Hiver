<div align="center">

# 🤖 AmazonHelp AI Support Agent

### Autonomous, Retrieval-Grounded Twitter Customer Support Pipeline

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-Render-46E3B7?style=for-the-badge)](https://hiver-43h0.onrender.com/)

<br/>

**An auditable, retrieval-augmented AI agent that triages inbound `@AmazonHelp` tweets, classifies customer intent across 9 operational categories, drafts grounded responses using historical brand resolutions, and makes deterministic escalation decisions — all with full transparency and zero hallucinated commitments.**

<br/>

[🚀 Live Demo](https://hiver-43h0.onrender.com/) · [Quick Start](#-quickstart) · [Architecture](#-system-architecture) · [Evaluation](#-evaluation-results) · [Report](report.md) · [Decision Log](decision_log.md)

---

</div>

<br/>

## ✨ Key Highlights

<table>
<tr>
<td width="50%">

### 🎯 Intent Classification
9-class operational taxonomy discovered via **K-Means clustering** over sentence embeddings, validated against **170 hand-labeled golden examples**

</td>
<td width="50%">

### 🛡️ Deterministic Escalation
Rule-based, **fully auditable** escalation engine with 7 signal categories — legal keywords, monetary values, safety hazards, frustration markers, repeat contacts, and confidence thresholds

</td>
</tr>
<tr>
<td width="50%">

### 📚 RAG-Grounded Replies
Responses grounded in **top-k historical AmazonHelp resolutions** via semantic cosine similarity over `all-MiniLM-L6-v2` embeddings — no hallucinated policies or fabricated tracking numbers

</td>
<td width="50%">

### 🧪 Rigorous Evaluation
Full eval harness with **Trivial + Simple baselines**, LLM-as-Judge scoring across 3 rubric dimensions, and **human calibration** (Spearman ρ = 1.0, 96.2% within ±1)

</td>
</tr>
</table>

<br/>

## 🏗️ System Architecture

```
                    ┌──────────────────────────────────────────────────────────┐
                    │                 INCOMING CUSTOMER TWEET                  │
                    │    "@AmazonHelp my package tracking hasn't moved in      │
                    │     3 days and I was charged twice!!"                    │
                    └───────────────────────┬──────────────────────────────────┘
                                            │
                                            ▼
                    ┌───────────────────────────────────────────────────────────┐
                    │              ① TEXT PREPROCESSING                        │
                    │  • Strip @mentions • Normalize whitespace                │
                    │  • Preserve emoji (sentiment-relevant)                   │
                    └───────────────────────┬───────────────────────────────────┘
                                            │
                        ┌───────────────────┼───────────────────┐
                        ▼                   ▼                   ▼
            ┌───────────────────┐ ┌──────────────────┐ ┌───────────────────┐
            │  ② CLASSIFY       │ │  ③ RETRIEVE       │ │  ④ ESCALATION     │
            │     INTENT        │ │     CONTEXT       │ │     POLICY        │
            │                   │ │                   │ │                   │
            │ LLM zero-shot     │ │ Semantic search   │ │ 7 deterministic   │
            │ classifier with   │ │ over 5K historic  │ │ signal categories │
            │ frozen 9-class    │ │ (msg, reply) pairs│ │ with auditable    │
            │ taxonomy          │ │ via MiniLM-L6-v2  │ │ justification     │
            │                   │ │ embeddings        │ │ strings           │
            │ → intent +        │ │ → top-3 grounding │ │ → escalate /      │
            │   confidence      │ │   exemplars       │ │   auto_handle +   │
            └─────────┬─────────┘ └────────┬──────────┘ │   reason          │
                      │                    │            └─────────┬─────────┘
                      └────────┬───────────┘                      │
                               ▼                                  │
                    ┌───────────────────────────────────────┐     │
                    │          ⑤ DRAFT GROUNDED REPLY       │     │
                    │                                       │     │
                    │  LLM generates response constrained   │     │
                    │  by retrieved historical exemplars     │     │
                    │  + regex hallucination guards for      │     │
                    │  fake order IDs, tracking numbers,     │     │
                    │  and unauthorized $ commitments        │     │
                    └───────────────────┬───────────────────┘     │
                                        │                         │
                                        ▼                         ▼
                    ┌──────────────────────────────────────────────────────────┐
                    │                   ⑥ UNIFIED OUTPUT                       │
                    │  {intent, confidence, reply, decision, reason,           │
                    │   retrieved_context, hallucination_flags}                │
                    └──────────────────────────────────────────────────────────┘
```

<br/>

## 📂 Project Structure

```
├── 🔧 backend/
│   ├── app.py                      # Flask REST API (CORS, /api/process, /api/health, etc.)
│   ├── requirements.txt            # Python dependencies
│   ├── src/                        # Core ML & Agent Pipeline
│   │   ├── pipeline.py             # Unified SupportAgentPipeline controller
│   │   ├── classify_intent.py      # LLM + TF-IDF intent classifiers
│   │   ├── retrieval.py            # Semantic retrieval index (all-MiniLM-L6-v2)
│   │   ├── draft_reply.py          # RAG reply generator + hallucination guards
│   │   ├── escalation_policy.py    # 7-signal deterministic escalation engine
│   │   ├── llm_client.py           # Multi-provider LLM client (Groq/OpenAI/Gemini)
│   │   ├── taxonomy.py             # Frozen 9-class intent taxonomy (Enum)
│   │   ├── data_prep.py            # Dataset chunking & thread reconstruction
│   │   ├── cluster_intents.py      # K-Means intent discovery + silhouette sweep
│   │   ├── baselines.py            # Trivial & Simple baseline agents
│   │   └── build_golden_set.py     # Golden evaluation dataset builder
│   └── eval/                       # Evaluation Suite
│       ├── run_eval.py             # Master eval runner (170 golden items × 3 systems)
│       ├── llm_judge.py            # LLM-as-Judge rubric evaluator (3 dimensions)
│       ├── metrics.py              # Classification & escalation metrics
│       └── judge_calibration.py    # Human vs. Judge agreement analysis
│
├── ⚛️  frontend/                    # Vite + React Interactive Dashboard
│   ├── vite.config.js              # Dev server + API proxy
│   └── src/
│       ├── App.jsx                 # Chat-based UI with real-time pipeline execution
│       ├── index.css               # Design system & styling
│       └── components/
│           ├── Header.jsx          # Navigation + backend health indicator
│           └── ChatView.jsx        # Live inference sandbox with stage visualizer
│
├── 📊 data/                        # Raw & processed parquet datasets
├── 🏷️  golden_set/                  # 170 hand-labeled evaluation examples
│   ├── golden_eval_v1.csv          # Primary golden dataset
│   ├── golden_eval_relabel_10pct.csv  # Blind 10% re-label for self-consistency
│   └── labeling_notes.md           # Annotation protocol & Cohen's κ = 1.000
├── 📈 results/                     # Output metrics, confusion matrices, failure analysis
├── 📝 prompts/                     # Versioned prompt templates (auditable, diffable)
│   ├── intent_classify.txt         # Intent classification prompt
│   ├── reply_draft.txt             # RAG reply generation prompt
│   └── judge_rubric.txt            # LLM judge scoring rubric
│
├── api/index.py                    # Vercel serverless function entrypoint
├── render.yaml                     # Render deployment config
├── vercel.json                     # Vercel deployment config
├── Makefile                        # Build & run automation shortcuts
├── report.md                       # Full technical report (~6 pages)
├── decision_log.md                 # 13 non-obvious engineering decisions
└── requirements.txt                # Python dependency manifest
```

<br/>

## 📊 Evaluation Results

### Headline Metrics — Full System vs. Baselines

> Evaluated on **170 hand-labeled golden examples** spanning all 9 intent categories.

| Metric | Trivial Baseline | Simple Baseline | **Full System** | Δ vs. Simple |
|:---|:---:|:---:|:---:|:---:|
| **Intent Accuracy** | 15.29% | 55.29% | **52.94%** | -2.35pp |
| **Intent Macro F1** | 2.95% | 54.23% | **50.03%** | -4.20pp |
| **Escalation Precision** | 31.18% | 80.00% | **61.54%** | -18.46pp |
| **Escalation Recall** | 100.00% | 30.19% | **60.38%** | **+30.19pp** ✅ |
| **Escalation F1** | 47.53% | 43.84% | **60.95%** | **+17.11pp** ✅ |
| **False Negatives** ⚠️ | 0 | 37 _(dangerous)_ | **21** | **-43.2%** ✅ |
| **LLM Judge Quality** | 4.33/5 | 4.33/5 | **4.33/5** | — |

<br/>

### 🔬 LLM Judge Calibration

| Calibration Metric | Value |
|:---|:---:|
| **Spearman ρ (Rank Correlation)** | **1.0** |
| **Within ±1 Agreement** | **96.2%** |
| **Exact Agreement** | 25.7% |
| **Calibration Sample Size** | N = 35 |

> **Verdict**: The LLM Judge is a reliable coarse surrogate for human evaluation within ±1 grade point. Systematic bias: tone leniency (awards 5/5 to polite corporate boilerplate that humans score lower).

<br/>

### 🧠 Intent Taxonomy

| Intent Category | Description | Risk Level |
|:---|:---|:---:|
| `order_status_delivery` | Package tracking, delays, lost/missing deliveries | 🟡 Medium |
| `refund_return` | Return requests, refund status, return policies | 🟡 Medium |
| `billing_dispute` | Unauthorized charges, double billing, payment errors | 🔴 **High** |
| `account_access` | Login failures, 2FA issues, account lockouts | 🔴 **High** |
| `product_issue` | Damaged, defective, or incorrect items | 🟡 Medium |
| `app_website_bug` | Technical issues with Amazon app/website | 🟢 Low |
| `cancellation` | Order or subscription cancellation requests | 🟢 Low |
| `general_complaint_vent` | Frustration/anger without specific actionable request | 🟡 Medium |
| `other_unclear` | Ambiguous or off-topic messages requiring clarification | 🟡 Medium |

<br/>

## 🚀 Quickstart

### Prerequisites

| Requirement | Version |
|:---|:---|
| Python | 3.10+ |
| Node.js | 18+ |
| npm | 9+ |

### 1️⃣ Clone & Install

```bash
# Clone the repository
git clone https://github.com/your-username/amazonhelp-support-agent.git
cd amazonhelp-support-agent

# Install all dependencies
make install

# Or manually:
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### 2️⃣ Configure Environment

```bash
# Create .env file in project root
cp .env.example .env

# Add your LLM API key (one of the following):
GROQ_API_KEY=your_groq_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

### 3️⃣ Launch the Application

```bash
# Terminal 1 — Start Flask Backend
make backend
# → Runs on http://127.0.0.1:5000

# Terminal 2 — Start React Frontend
make frontend
# → Runs on http://localhost:5173 (proxied to backend)
```

### 4️⃣ Test the Pipeline (CLI)

```bash
# Single message inference
python backend/src/pipeline.py --message "Where is my package? It's been stuck for 3 days!"

# Interactive terminal mode
python backend/src/pipeline.py --interactive
```

### 5️⃣ Run Full Evaluation

```bash
# Execute evaluation harness over 170 golden examples
make eval
# → Outputs: results/metrics_summary.json, confusion matrices, failure analysis
```

<br/>

## 🔌 API Reference

### `POST /api/process`

Process a customer tweet through the full agent pipeline.

```json
// Request
{
  "text": "My package tracking hasn't updated in 5 days!",
  "thread_length": 1
}

// Response
{
  "status": "success",
  "data": {
    "intent": "order_status_delivery",
    "confidence": 0.92,
    "reply": "We're sorry about the delay! Please DM us your 17-digit order number so we can investigate. ^AH",
    "decision": "auto_handle",
    "reason": "Auto-handled: Procedural/informational request with zero risk signals detected",
    "retrieved_context": "...",
    "hallucination_detected": false,
    "hallucination_flags": []
  }
}
```

### Other Endpoints

| Endpoint | Method | Description |
|:---|:---:|:---|
| `/api/health` | `GET` | Backend health check & status |
| `/api/process` | `POST` | Full pipeline inference |
| `/api/stats` | `GET` | Dataset statistics |
| `/api/samples` | `GET` | Sample tweets from dataset |
| `/api/eval` | `GET` | Cached evaluation results |

<br/>

## 🛡️ Escalation Policy — Signal Architecture

The escalation engine is **fully deterministic and auditable** — no LLM black-box decisions for safety-critical routing. Seven signal categories are evaluated in parallel:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ESCALATION SIGNAL MATRIX                         │
├─────────────────────────┬───────────────────────────────────────────┤
│ 🔴 High-Risk Intent     │ billing_dispute, account_access           │
│ ⚖️  Legal/Regulatory     │ lawyer, attorney, BBB, chargeback, fraud  │
│ 💰 Monetary Values      │ Any dollar amounts ($XX.XX)               │
│ 🚨 Safety/Severe        │ stolen, hacked, shattered, injury, hazard │
│ 😤 High Frustration     │ supervisor, manager, scam, unacceptable   │
│ 🔁 Repeat Contact       │ "3rd time", "already called", "promised"  │
│ ❓ Low Confidence       │ Intent classification confidence < 0.60   │
├─────────────────────────┴───────────────────────────────────────────┤
│ ANY signal fires → ESCALATE + human-readable justification string  │
│ ZERO signals     → AUTO_HANDLE                                     │
└─────────────────────────────────────────────────────────────────────┘
```

<br/>

## 🧰 Makefile Commands

| Command | Description |
|:---|:---|
| `make install` | Install all Python & Node.js dependencies |
| `make backend` | Launch Flask API server on port 5000 |
| `make frontend` | Launch Vite React dev server on port 5173 |
| `make eval` | Run full evaluation harness (3 systems × 170 examples) |
| `make demo` | Quick single-message pipeline test |
| `make clean` | Remove all `__pycache__` and build artifacts |

<br/>

## 📦 Deliverables Map

| Deliverable | Location | Description |
|:---|:---|:---|
| **Technical Report** | [`report.md`](report.md) | 6-page analysis: problem framing, results, failure modes, honest limitations |
| **Decision Log** | [`decision_log.md`](decision_log.md) | 13 non-obvious engineering decisions with rationale |
| **Golden Eval Set** | [`golden_set/`](golden_set/) | 170 hand-labeled examples + annotation protocol |
| **Labeling Notes** | [`golden_set/labeling_notes.md`](golden_set/labeling_notes.md) | Sampling strategy + self-consistency (Cohen's κ = 1.000) |
| **Metrics Summary** | [`results/metrics_summary.json`](results/metrics_summary.json) | Machine-readable evaluation results |
| **Confusion Matrices** | [`results/`](results/) | Visual confusion matrices for all 3 systems |
| **Failure Analysis** | [`results/failure_cases.md`](results/failure_cases.md) | Top 5 failure modes with root cause hypotheses |
| **Judge Calibration** | [`results/judge_vs_human_agreement.json`](results/judge_vs_human_agreement.json) | Human vs. LLM Judge agreement statistics |
| **Prompt Templates** | [`prompts/`](prompts/) | Auditable, versioned prompt files |

<br/>

## 🔧 Tech Stack

<div align="center">

| Layer | Technologies |
|:---|:---|
| **Backend** | Python · Flask · Gunicorn · Pandas · NumPy · Scikit-Learn |
| **ML / NLP** | Sentence-Transformers (`all-MiniLM-L6-v2`) · OpenAI API · Groq API |
| **Frontend** | React 18 · Vite · Tailwind CSS · Lucide Icons |
| **Evaluation** | LLM-as-Judge · Spearman ρ · Cohen's Kappa · Macro F1 |
| **Deployment** | Vercel (Frontend + Serverless API) · Render (Full-stack) |
| **Data** | Apache Parquet · CSV · JSON |

</div>

<br/>

## ⚠️ Honest Limitations

> Transparency is a core design principle. These are the known limitations of the current system:

1. **Single-Annotator Golden Set** — All 170 evaluation labels come from one annotator. While intra-annotator consistency is perfect (κ = 1.0), this measures self-agreement, not universal ground truth.

2. **Single-Turn Only** — The pipeline handles first-contact tweets only. Multi-turn conversation memory, DM transitions, and follow-up tracking are deliberate non-goals for v1.

3. **No Live Backend Integration** — The agent cannot authenticate users, check real order statuses, or process actual refunds. All replies are grounded in historical patterns, not live data.

4. **Grounded ≠ Good** — Historical `@AmazonHelp` replies are often deflections ("Please DM us"). An agent that perfectly mimics this pattern scores high on groundedness while providing zero first-contact resolution.

5. **Small Calibration Sample** — Judge-human agreement measured on N=35 yields wide confidence intervals. Rare edge cases may be underrepresented.

<br/>

## 📖 Attributions & Data License

| Resource | License | Usage |
|:---|:---|:---|
| [Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter) | Open Data Commons Attribution | Primary dataset (`twcs.csv`) |
| [`sentence-transformers/all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | Apache 2.0 | Semantic embedding model |
| [Flask](https://flask.palletsprojects.com/) | BSD-3-Clause | Backend API framework |
| [React](https://react.dev) | MIT | Frontend UI library |
| [Vite](https://vitejs.dev) | MIT | Frontend build toolchain |
| [Scikit-Learn](https://scikit-learn.org) | BSD-3-Clause | K-Means clustering, TF-IDF |
| [Lucide Icons](https://lucide.dev) | ISC | UI iconography |

<br/>

---

<div align="center">

**Built as a take-home assignment for [Hiver](https://hiverhq.com/)** · Designed with safety, auditability, and honest evaluation at its core.

<sub>Random seed: `42` · All results reproducible via `make eval` · Expected wall-clock: ~10 minutes on standard hardware</sub>

</div>
