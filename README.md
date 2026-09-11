# Autonomous Twitter Customer-Support Agent for AmazonHelp

An auditable, retrieval-grounded AI agent designed to triage, evaluate risk, and autonomously draft grounded responses to inbound customer inquiries directed at `@AmazonHelp` on Twitter. Built on top of the Kaggle Customer Support on Twitter dataset (`twcs.csv`), the system integrates an 8-class operational intent classifier, a cosine-similarity retrieval engine indexing 5,000 verified historical brand resolutions, a deterministic multi-signal escalation policy to prevent safety-critical under-triage, hallucination guards, and an automated LLM-as-a-judge evaluation suite calibrated against human ground truth.

---

## 1. Quickstart & Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Git

### Installation
Clone the repository and install dependencies:
```bash
git clone <repo-url> support-agent
cd support-agent
pip install -r requirements.txt
```

### Environment Configuration (Optional)
The agent features a multi-provider LLM client (`src/llm_client.py`) supporting OpenAI, Google Gemini, Anthropic Claude, and an intelligent offline mock engine.

If using live LLM APIs, create a `.env` file in the root directory:
```env
# Optional API keys (system defaults to offline mode if none provided)
OPENAI_API_KEY=your_openai_api_key
# or
GEMINI_API_KEY=your_gemini_api_key
# or
ANTHROPIC_API_KEY=your_anthropic_api_key
```
*Note: If no API keys are provided, the system executes deterministically using its offline inference engine.*

---

## 2. End-to-End Reproduction in Under 15 Minutes

The entire pipeline—from raw CSV chunked processing to clustering, retrieval indexing, and golden set evaluation—is designed to run end-to-end in **~3 to 5 minutes** wall-clock time.

Run the complete pipeline with one command:
```bash
# Via Makefile:
make all

# Or directly via Python:
python src/data_prep.py --csv-path data/raw/twcs.csv --output-dir data --sample-size 5000 --seed 42
python src/cluster_intents.py --data-path data/processed/amazonhelp_customer_msgs.parquet --output-dir results --sample-size 1500 --seed 42 --chosen-k 8
python -c "import sys; sys.path.insert(0, '.'); from src.retrieval import HistoricalRetrievalIndex; HistoricalRetrievalIndex()"
python eval/run_eval.py
```

### Wall-Clock Time Breakdown:
1. **Data Prep (`src/data_prep.py`)**: ~35 seconds (scans 2.8M rows in 100k chunks, extracts 76,525 AmazonHelp threads, samples 5,000).
2. **Clustering Sweep (`src/cluster_intents.py`)**: ~45 seconds (embeds 1,500 messages, computes silhouette scores $k=6..14$).
3. **Retrieval Indexing (`src/retrieval.py`)**: ~60 seconds (embeds and caches 5,000 threads to `retrieval_embeddings.npy`).
4. **Full Evaluation Harness (`eval/run_eval.py`)**: ~30 seconds (runs Trivial, Simple, and Full models over 170 golden cases + 35 calibration cases).

---

## 3. Interactive CLI & Demo

Test the agent on any custom customer message:
```bash
python src/pipeline.py --message "Where is my package? The tracking has been stuck for 4 days!"
```

Launch an interactive terminal session:
```bash
python src/pipeline.py --interactive
```

---

## 4. Deliverables Index

| Deliverable | File Path | Description |
|---|---|---|
| **Technical Report** | [`report.md`](report.md) | ~6-page formal engineering report covering problem framing, baseline comparisons, failure analysis, headline caveats, and future roadmap. |
| **Decision Log** | [`decision_log.md`](decision_log.md) | 13 structured decisions explaining key engineering trade-offs. |
| **Intent Taxonomy** | [`src/taxonomy.py`](src/taxonomy.py) | Frozen 8-intent operational taxonomy and multi-intent priority hierarchy. |
| **Labeling Protocol** | [`golden_set/labeling_notes.md`](golden_set/labeling_notes.md) | Sampling strategy, rubric, and blind test-retest self-consistency check ($\kappa=1.000$). |
| **Golden Evaluation Set** | [`golden_set/golden_eval_v1.csv`](golden_set/golden_eval_v1.csv) | $N=170$ hand-labeled instances with primary intent, ideal action, and notes. |
| **Evaluation Metrics** | [`results/metrics_summary.json`](results/metrics_summary.json) | Benchmark performance across Trivial, Simple, and Full System. |
| **Judge Calibration** | [`results/judge_vs_human_agreement.json`](results/judge_vs_human_agreement.json) | LLM Judge vs. Human annotator agreement on 35 cases (96.2% within $\pm 1$). |
| **Diagnostic Failures** | [`results/failure_cases.md`](results/failure_cases.md) | Detailed analysis of top 5 system error cases. |
| **Clustering Discovery** | [`results/cluster_discovery_summary.md`](results/cluster_discovery_summary.md) | K-Means silhouette evaluation and empirical cluster descriptions. |
| **Silhouette Curve** | [`results/silhouette_sweep.png`](results/silhouette_sweep.png) | Silhouette score plot across $k=6..14$. |
| **Confusion Matrix** | [`results/confusion_matrix.png`](results/confusion_matrix.png) | Confusion matrix for the full system. |
| **EDA Summary** | [`results/eda_summary.md`](results/eda_summary.md) | Message length distribution and top bigrams from raw Twitter data. |

---

## 5. Attributions & References

- **Dataset**: Kaggle Customer Support on Twitter (`thoughtvector/customer-support-on-twitter`) under Open Data Commons Attribution License.
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (Apache 2.0 license) via Hugging Face.
- **Machine Learning & Analytics**: `scikit-learn` (k-means, logistic regression, TF-IDF, classification metrics), `scipy` (Spearman rank correlation), `pandas`, `numpy`.
- **Visualization**: `matplotlib` and `seaborn`.
- **Prompts**: Grounded prompting and LLM-as-a-judge rubric adapted from Anthropic and OpenAI evaluation guidelines.
