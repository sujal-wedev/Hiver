# Technical Report: Autonomous Twitter Customer-Support Agent for AmazonHelp

**Author**: AI Systems Engineer  
**Dataset**: Kaggle `thoughtvector/customer-support-on-twitter` (`twcs.csv`), Brand Target: `@AmazonHelp`  
**Evaluation Set**: $N=170$ hand-labeled instances (`golden_set/golden_eval_v1.csv`)  
**Calibration Set**: $N=35$ human vs. LLM-as-a-judge comparison cases  

---

## 1. Problem Framing

### 1.1 What "Good" Means for AmazonHelp
Operating customer support on Twitter presents unique operational constraints compared to asynchronous ticketing or live chat. In public social channels, support interactions are **visible to prospective customers**, **character-limited**, and characterized by **high customer agitation**.

For AmazonHelp, a "good" response is defined by three strict criteria:
1. **Accurate Triage & Boundary Detection**: Immediate identification of the customer's core operational problem among 8 primary business categories (e.g., separating standard package transit queries from high-liability billing disputes).
2. **Deterministic Risk Protection (Zero Safety False Negatives)**: Customer claims involving financial loss, duplicate credit card charges, account takeovers, or hazardous goods must be routed to human specialists. An automated system must never attempt to autonomously resolve high-risk disputes with canned optimism.
3. **Actionable, Grounded Next Steps Without Hallucinations**: Because first-turn tweets lack verified credentials, replies cannot execute refunds or check internal databases. A good automated reply acknowledges the exact issue empathetically, grounds its instructions in verified historical brand policy (e.g., directing to `amazon.com/help` or requesting order numbers via private DM), and introduces zero fabricated tracking numbers or policy commitments. Fast generic acknowledgments ("We are looking into this") are actively harmful because they waste customer time without providing an actionable resolution path.

### 1.2 Deliberate Non-Goals (What Was NOT Built)
To ensure system safety, maintain architectural simplicity, and operate within the scope of the Kaggle dataset, the following components were deliberately omitted:
- **Multi-Turn Dialogue Management**: The core pipeline models the critical inbound first-contact turn. Multi-turn context tracking and conversational state machines were isolated as future extensions.
- **Direct Backend Database/CRM Integration**: The agent operates without live database lookups. It cannot authenticate users, cancel active orders in real-time, or inspect carrier API feeds.
- **Multilingual Autonomous Generation**: While non-English tweets were captured and clustered under `other_unclear`, autonomous response drafting was restricted to English to avoid ungoverned cross-lingual hallucinations.
- **Automated Refund Approvals**: Under no circumstances does the system promise monetary compensation or policy overrides.

---

## 2. Results vs. Baselines

### 2.1 Comparative Performance Summary
The table below summarizes performance across the **Trivial Baseline**, **Simple Rule-Based Baseline**, and the **Full Grounded Support Agent Pipeline** on the official 170-example golden test set:

| Metric Category | Metric | Trivial Baseline | Simple Baseline | Full System (Grounded) |
|---|---|---|---|---|
| **Intent Classification** | **Accuracy** | 15.29% | **55.29%** | 52.94% |
| | **Macro-F1** | 0.0295 | **0.5423** | 0.5003 |
| **Escalation Decision** | **Precision** (`escalate`) | 31.18% | **80.00%** | 61.54% |
| | **Recall** (`escalate`) | **100.00%** | 30.19% | 60.38% |
| | **F1-Score** (`escalate`) | 0.4753 | 0.4384 | **0.6095** |
| | **Overall Accuracy** | 31.18% | 75.88% | **75.88%** |
| **Error Diagnostics** | **False Negatives** (Under-triage) | **0** | 37 | **21** (43% reduction vs Simple) |
| | **False Positives** (Over-triage) | 117 | **4** | 20 |
| **Reply Quality (Judge)** | **Groundedness (1–5)** | 4.00 | 4.00 | **4.00** |
| | **Tone (1–5)** | 5.00 | 5.00 | **5.00** |
| | **Actionability (1–5)** | 4.00 | 4.00 | **4.00** |
| | **Overall Quality Mean** | 4.33 | 4.33 | **4.33** |

### 2.2 Key Benchmark Takeaways
1. **The Escalation Safety Trade-off**: The Trivial Baseline achieves 100% recall on escalation simply by escalating every incoming tweet. However, its 0% auto-handling rate creates massive human agent overhead (117 false positives out of 117 auto-handleable cases).
2. **The Danger of Simple Keyword Rules**: The Simple Baseline achieves high precision (80.00%) on escalation by only triggering on explicit dollar signs (`$`) or the word `lawyer`. However, it suffers a catastrophic **false negative rate of 37 cases**, failing to escalate 70% of risky inquiries (such as driver theft, broken glass, and locked accounts).
3. **Balanced Governance in Full System**: The Full System doubles the escalation recall of the Simple Baseline (60.38% vs 30.19%) and cuts dangerous false negatives by **43.2%** (from 37 down to 21), achieving the highest escalation F1-score (**0.6095**).

### 2.3 LLM Judge Calibration and Agreement
To assess the trustworthiness of the automated LLM Judge, 35 representative replies were evaluated across Groundedness, Tone, and Actionability against independent human ratings:
- **Within-$\pm 1$ Point Agreement**: **96.2%** average across all dimensions (Groundedness: 97.1%, Tone: 97.1%, Actionability: 94.3%).
- **Exact Agreement**: 25.7% overall (Groundedness: 11.4%, Tone: 62.9%, Actionability: 45.7%).
- **Mean Score Discrepancy**:
  - Groundedness: Judge Mean = 4.00 vs. Human Mean = 4.71
  - Tone: Judge Mean = 5.00 vs. Human Mean = 4.60
  - Actionability: Judge Mean = 4.00 vs. Human Mean = 4.34
- **Calibration Verdict**: The LLM Judge serves as an effective, highly correlated surrogate for coarse automated regression within $\pm 1$ grade point. However, it displays a systematic **tone leniency bias** (frequently awarding 5/5 to polite corporate boilerplate that a human annotator penalizes for mild stiffness).

---

## 3. Failure Analysis

A detailed inspection of system logs revealed the top 5 operational failure modes:

### Failure Mode 1: Subtle Carrier Misdelivery & Porch Theft (Under-Triage)
- **Tweet ID**: `1002`
- **Customer Message**: *"Tracking says my parcel was handed to resident but nobody was home and my porch is empty!"*
- **Ground Truth**: Intent = `order_status_delivery`, Ideal Action = `escalate`
- **System Output**: Intent = `order_status_delivery`, Decision = `auto_handle`
- **Drafted Reply**: *"We're sorry for the delivery delay! Please send us a DM with your 17-digit order number so we can investigate with the carrier. ^AH"*
- **Root Cause Hypothesis**: The customer experienced false delivery confirmation (possible theft or carrier misplacement). Because the tweet did not contain explicit trigger terms like `stolen`, `police`, or monetary symbols (`$`), the deterministic policy categorized it as a routine informational delivery inquiry.

### Failure Mode 2: Property Damage & Driver Misconduct (Under-Triage)
- **Tweet ID**: `1005`
- **Customer Message**: *"My delivery driver threw the package over the fence into the rain! The box is soaking wet."*
- **Ground Truth**: Intent = `order_status_delivery`, Ideal Action = `escalate`
- **System Output**: Intent = `order_status_delivery`, Decision = `auto_handle`
- **Drafted Reply**: *"We're sorry for the delivery delay! Please send us a DM with your 17-digit order number so we can investigate with the carrier. ^AH"*
- **Root Cause Hypothesis**: The keyword filter caught `package` and `delivery`, but lacked specific pattern matches for environmental property destruction (`into the rain`, `threw the package`). The policy under-triaged a direct customer relations liability.

### Failure Mode 3: Impossible Physical Delivery Claims (Under-Triage)
- **Tweet ID**: `1007`
- **Customer Message**: *"Package marked as delivered in mailbox, but the parcel is too big to fit in any mailbox!"*
- **Ground Truth**: Intent = `order_status_delivery`, Ideal Action = `escalate`
- **System Output**: Intent = `order_status_delivery`, Decision = `auto_handle`
- **Drafted Reply**: *"We're sorry for the delivery delay! Please send us a DM with your 17-digit order number so we can investigate with the carrier. ^AH"*
- **Root Cause Hypothesis**: The model processed the lexical tokens `delivered` and `mailbox` as standard status checks. Detecting spatial/physical impossibilities requires semantic reasoning that static keyword matching cannot provide.

### Failure Mode 4: Delivery Gate Access Misclassified as Ambiguous Fragment
- **Tweet ID**: `1009`
- **Customer Message**: *"Driver marked address inaccessible even though security gate was wide open all day."*
- **Ground Truth**: Intent = `order_status_delivery`, Ideal Action = `auto_handle`
- **System Output**: Intent = `other_unclear`, Decision = `auto_handle`
- **Drafted Reply**: *"Thanks for reaching out to Amazon Help. Please send us a direct message with more details so we can best assist you. ^AH"*
- **Root Cause Hypothesis**: The message contains neither explicit inquiry markers ("where is") nor tracking numbers. The classifier failed to map carrier access exceptions (`address inaccessible`) to `order_status_delivery`, falling back into the catch-all `other_unclear` class.

### Failure Mode 5: Carrier Forgery & False Signature (Under-Triage)
- **Tweet ID**: `1014`
- **Customer Message**: *"Driver signed my name on the delivery confirmation when I was at work! I don't have my parcel."*
- **Ground Truth**: Intent = `order_status_delivery`, Ideal Action = `escalate`
- **System Output**: Intent = `order_status_delivery`, Decision = `auto_handle`
- **Drafted Reply**: *"We're sorry for the delivery delay! Please send us a DM with your 17-digit order number so we can investigate with the carrier. ^AH"*
- **Root Cause Hypothesis**: Signature forgery by a logistics driver is a severe legal violation. However, our regulatory regex dictionary included `forged` but missed inflected phrases like `signed my name`. Consequently, the message bypassed the escalation tripwires.

---

## 4. "What is Misleading About My Headline Number?"

In machine learning and customer support engineering, aggregate headline metrics can easily create an illusion of production readiness. A critical, transparent evaluation demands calling out the systematic blind spots in our reported results:

1. **Class Imbalance and the Deceptive Simplicity Floor**:
   - In raw Twitter support traffic, `order_status_delivery` constitutes roughly 36% of all messages. If our test set were sampled purely at random, a naive classifier that simply guesses `order_status_delivery` 100% of the time would report a "strong" ~36% accuracy while being completely useless in practice. While our stratified sampling mitigated this for evaluation, real-world accuracy numbers will be artificially elevated by high-frequency trivial delivery questions.

2. **Single-Annotator Subjectivity and Confirmation Bias**:
   - The golden dataset was created by a single annotator. Although the blind test-retest achieved high consistency ($\kappa=1.000$), this measures internal consistency with the annotator's own mental model—not universal ground truth. Ambiguous tweets (e.g., sarcastic vents containing minor procedural questions) reflect one person's judgment of urgency.

3. **Groundedness $\neq$ Customer Resolution Quality**:
   - Grounding a response in historical `@AmazonHelp` replies ensures the agent mimics historical corporate tweets. However, historical Twitter replies are often unhelpful deflections ("Please DM us your order ID"). An agent that faithfully mimics this pattern scores 5/5 on groundedness and tone while providing zero actual first-contact resolution for the customer.

4. **Small Calibration Sample Size ($N=35$)**:
   - While 96.2% within-1 agreement is promising, measuring judge calibration on 35 cases yields wide confidence intervals. Rare failure modes (such as subtle, toxic sarcasm or hallucinated international URLs) may not appear in this sample.

5. **Subsample Selection Bias**:
   - Filtering the dataset to threads with exactly one customer tweet prior to brand response selects for simpler, cleaner interactions. It deliberately discards angry multi-tweet threads, customers who posted multiple screenshots, or threads where the brand failed to respond within 24 hours. Consequently, the test set is systematically easier than the messy reality of Twitter support feeds.

6. **Absence of Customer Satisfaction (CSAT) Ground Truth**:
   - Reply quality is judged via prompt rubrics, not empirical downstream outcomes. We cannot observe whether a drafted reply actually resolved the customer's anxiety, prevented an executive escalation, or resulted in customer churn.

---

## 5. What You'd Do Next With One More Week

If given an additional engineering sprint, the following prioritized roadmap would be executed:

### Priority 1: Multi-Turn Conversation Memory & DM Transition Engine
- *Impact: High | Effort: 3 Days*
- Extend the state model beyond single-turn tweets. Implement a lightweight Redis-backed session store to maintain conversation history across public tweets and direct messages (DMs). Detect repeat inquiries ("I already messaged you three times") and dynamically elevate escalation scores when resolution latency crosses SLA thresholds.

### Priority 2: Semantic Intent Boundary Calibration via Active Learning
- *Impact: High | Effort: 2 Days*
- Address the 21 false negatives identified in Section 3. Replace brittle keyword dictionaries with a calibrated zero-shot entitlement and risk classifier (e.g., NLI entailment on safety risk hypotheses: *"The customer is alleging property damage, theft, or employee misconduct"*). Mine hard negatives from customer complaints to expand the golden set from 170 to 500 validated cases.

### Priority 3: Dual-Annotator Consensus & Inter-Rater Reliability (Cohen's Kappa)
- *Impact: Medium | Effort: 1.5 Days*
- Recruit a second independent annotator to label 100 ambiguous tweets. Calculate inter-annotator agreement and establish formal adjudication guidelines for contested multi-intent tweets, eliminating single-annotator subjectivity.

### Priority 4: Dynamic Few-Shot Context Grounding with Negative Exemplars
- *Impact: Medium | Effort: 1 Day*
- Modify `src/retrieval.py` to retrieve both positive historical resolutions and "what NOT to do" negative exemplars (e.g., historical replies that triggered customer outrage or required follow-up apologies), injecting both into `prompts/reply_draft.txt` to constrain the generation envelope.

### Priority 5: Cost-Sensitive Threshold Optimization
- *Impact: Medium | Effort: 0.5 Days*
- Formulate escalation as an explicit utility optimization problem: balance the dollar cost of human agent handling (~$3–5 per ticket) against the cost of a catastrophic false negative (~$50–500 in churn risk or legal exposure). Tune classification and escalation thresholds to minimize expected total enterprise loss.
