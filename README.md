# Autonomous Twitter Support Agent for AmazonHelp (@AmazonHelp)

An auditable, retrieval-grounded AI agent designed to triage, evaluate risk, and autonomously draft grounded responses to inbound customer inquiries directed at `@AmazonHelp` on Twitter.

Built with a **Flask Python Backend** (`backend/`) housing ML pipelines and evaluation engines, and a modern **Vite + React Frontend** (`frontend/`) interactive dashboard.

---

## 1. Project Architecture & Folder Structure

```
├── backend/
│   ├── app.py                   # Flask REST API server (ports, CORS, endpoints)
│   ├── requirements.txt         # Python dependencies
│   ├── src/                     # Core ML & Agent Pipeline Modules
│   │   ├── pipeline.py          # Unified SupportAgentPipeline controller
│   │   ├── classify_intent.py   # LLM & Classical TF-IDF intent classifiers
│   │   ├── retrieval.py         # Historical Retrieval Index (all-MiniLM-L6-v2)
│   │   ├── draft_reply.py       # Grounded reply generator + hallucination checks
│   │   ├── escalation_policy.py # Deterministic multi-signal escalation policy
│   │   ├── llm_client.py        # Multi-provider LLM client (Groq / OpenAI / Gemini / Mock)
│   │   ├── taxonomy.py          # Operational Intent Taxonomy
│   │   ├── data_prep.py         # Dataset chunking & thread reconstruction
│   │   ├── cluster_intents.py   # Unsupervised K-Means clustering
│   │   ├── baselines.py         # Trivial & Simple baseline agents
│   │   └── build_golden_set.py  # Golden evaluation dataset builder
│   └── eval/                    # Evaluation Suite & Judge Calibration
│       ├── run_eval.py          # Master evaluation runner over 170 golden items
│       ├── llm_judge.py         # LLM-as-a-judge rubric evaluator
│       ├── metrics.py           # Classification & escalation metric calculators
│       └── judge_calibration.py # Judge vs Human annotator agreement analyzer
│
├── frontend/                    # Vite + React + JavaScript Interactive UI
│   ├── package.json
│   ├── vite.config.js           # Vite dev server + proxy to Flask API
│   ├── index.html
│   └── src/
│       ├── App.jsx              # Main dashboard container & state controller
│       ├── index.css            # Glassmorphism design system & styles
│       └── components/
│           ├── Header.jsx       # Header navigation bar & backend status indicator
│           ├── SandboxTab.jsx   # Interactive live inference sandbox & 4-stage visualizer
│           ├── MetricsTab.jsx   # Headline metrics table & baseline comparison
│           ├── JudgeAgreementTab.jsx # LLM Judge vs Human calibration stats (Spearman ρ = 1.0)
│           ├── FailureAnalysisTab.jsx # Deep-dive into Top 5 failure cases & hypotheses
│           ├── DecisionLogTab.jsx    # 10 non-obvious engineering decisions
│           └── GoldenSetTab.jsx      # Golden evaluation set taxonomy & methodology
│
├── data/                        # Datasets (raw & processed parquet threads)
├── golden_set/                  # Hand-labeled golden evaluation CSVs
├── results/                     # Output metrics JSON, plots, and failure case markdown
├── prompts/                     # Prompt templates
├── Makefile                     # Build & run automation
├── report.md                    # Technical report
└── decision_log.md              # Detailed decision log
```

---

## 2. Quickstart & How to Run

### Prerequisites
- **Python 3.10+** (Flask, Pandas, SentenceTransformers, Scikit-Learn)
- **Node.js 18+** & **npm 9+** (Vite + React)

### 1. Install Backend Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

## 3. Running the Application End-to-End

### Running the Flask Backend API Server
```bash
python backend/app.py
```
*Backend runs on `http://127.0.0.1:5000` exposing REST endpoints (`/api/process`, `/api/stats`, `/api/samples`, `/api/eval`, `/api/health`).*

### Running the Vite React Frontend
In a separate terminal window:
```bash
cd frontend
npm run dev
```
*Frontend runs on `http://localhost:5173` with live hot-reloading and proxying to backend.*

---

## 4. Pipeline Execution & Evaluation Commands

### Test Single Message Pipeline in Terminal
```bash
python backend/src/pipeline.py --message "Where is my package? It has been stuck at the facility for 3 days!"
```

### Run Full Evaluation Harness
```bash
python backend/eval/run_eval.py
```
*Evaluates Trivial Baseline, Simple Baseline, and Full System across 170 golden dataset cases and outputs `results/metrics_summary.json` and `results/judge_vs_human_agreement.json`.*

### Using Makefile Shortcuts
- `make backend`: Launches Flask API server.
- `make frontend`: Launches Vite React dev server.
- `make eval`: Runs evaluation suite.
- `make demo`: Executes test inference pipeline.

---

## 5. Summary of Headline Evaluation Results

| Metric | Trivial Baseline | Simple Baseline | Full System (Our Agent) |
|---|:---:|:---:|:---:|
| **Intent Accuracy** | 15.29% | **55.29%** | 52.94% |
| **Intent Macro F1** | 2.95% | **54.23%** | 50.03% |
| **Escalation Precision** | 31.18% | **80.00%** | 61.54% |
| **Escalation Recall** | 100.00% | 30.19% | **60.38%** |
| **Escalation F1 Score** | 47.53% | 43.84% | **60.95%** (+17.1% gain) |
| **False Negatives (Safety Risk)** | 0 | 37 (High Risk) | **21** (56% Reduction) |
| **LLM Judge Quality** | 4.33 / 5 | 4.33 / 5 | **4.33 / 5** |
| **Human vs LLM Judge Agreement** | - | - | **Spearman ρ = 1.0, 96.2% within ±1** |

---

## 6. Attributions & Data License

- **Primary Dataset**: Kaggle Customer Support on Twitter (`thoughtvector/customer-support-on-twitter`) under Open Data Commons Attribution License.
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (Apache 2.0 license) via Hugging Face.
- **Libraries**: Flask, Flask-CORS, Vite, React, Lucide-React, Pandas, Scikit-Learn, SentenceTransformers, OpenAI.
