# Decision Log — AmazonHelp AI Customer Support Agent

This document records the non-obvious engineering, architectural, and methodological decisions made during the construction, evaluation, and calibration of the Twitter Customer Support AI Agent.

1. **Target Brand Selection (`AmazonHelp`)**:
   - *Decision*: Selected `AmazonHelp` from the Kaggle TWCS dataset rather than `Uber_Support` or `SpotifyCares`.
   - *Reason*: With over 155,000 brand replies and 76,525 single-turn customer threads, `AmazonHelp` offered by far the richest diversity of operational issues (shipping delays, lost parcels, damaged goods, digital subscriptions, billing, returns) necessary to train and stress-test a multi-class support taxonomy.

2. **Subsample Size ($N=5,000$ Threads)**:
   - *Decision*: Chose a deterministic random subsample of 5,000 reconstructed threads (`seed=42`) rather than processing all 76k threads.
   - *Reason*: 5,000 threads provide comprehensive dense coverage for nearest-neighbor semantic retrieval while keeping cold-start embedding precomputation and eval execution strictly under the required 15-minute wall-clock budget on standard hardware.

3. **Single-Turn Thread Reconstruction Constraint**:
   - *Decision*: Constrained the core dataset to single customer-first inbound tweets paired with AmazonHelp's first public response (`in_response_to_tweet_id` is null for the customer).
   - *Reason*: Initial inbound triage and routing on Twitter is a high-volume, first-contact classification problem; handling multi-turn state drift was deliberately isolated as an orthogonal future milestone.

4. **Intent Taxonomy Cardinality (8 Intents + `other_unclear`)**:
   - *Decision*: Established an 8-way operational intent taxonomy (`order_status_delivery`, `refund_return`, `billing_dispute`, `account_access`, `product_issue`, `app_website_bug`, `cancellation`, `general_complaint_vent`) plus `other_unclear`.
   - *Reason*: K-Means silhouette clustering over message embeddings showed optimal separation around $k=6..9$; a 25-way taxonomy causes catastrophic inter-class boundary overlap and poor annotator agreement, while fewer than 6 categories obscures crucial differences between procedural inquiries and high-risk billing disputes.

5. **Multi-Intent Priority Hierarchy**:
   - *Decision*: Implemented a strict deterministic resolution hierarchy for multi-intent tweets: `billing_dispute` > `account_access` > `product_issue` > `refund_return` > `cancellation` > `order_status_delivery` > `app_website_bug` > `general_complaint_vent` > `other_unclear`.
   - *Reason*: Real customer tweets frequently bundle inquiries (e.g., "Package was 3 days late and I was double charged"). Prioritizing financial exposure and account security ensures that safety-critical concerns receive top routing precedence over delivery status.

6. **Deterministic Rule-Based Escalation vs. LLM Judgment**:
   - *Decision*: Implemented the primary escalation policy as an inspectable, rule-based signal accumulator rather than a black-box LLM prompt.
   - *Reason*: High-stakes support triage requires 100% auditability and deterministic guarantees. A rule-based engine citing explicit signals (monetary signs, legal keywords, safety hazards, low confidence) produces human-readable justification strings and prevents non-deterministic hallucinations from auto-resolving high-liability disputes.

7. **Retrieval-Augmented Grounding (RAG) vs. Model Fine-Tuning**:
   - *Decision*: Grounded reply generation on top-$k$ nearest historical resolutions via semantic cosine similarity over MiniLM embeddings rather than fine-tuning a small language model.
   - *Reason*: RAG allows instant updates to corporate policy without retraining, grounds the generator in verified historical brand voice, and eliminates catastrophic forgetting while drastically reducing compute requirements.

8. **Prompt Separation into Versioned Text Files**:
   - *Decision*: Maintained all prompt templates in dedicated plain-text files under `prompts/` rather than inlining strings in Python source code.
   - *Reason*: Enables transparent git diff tracking, modular prompt updates, and auditability during live technical reviews without touching pipeline logic.

9. **Two-Stage Stratified Sampling for Golden Evaluation Set ($N=170$)**:
   - *Decision*: Combined targeted keyword stratification with natural random backfill rather than uniform random sampling.
   - *Reason*: In raw Twitter support traffic, delivery queries represent >35% of volume while account lockouts and billing disputes represent <8%. Uniform sampling would have left critical low-frequency risk categories virtually unrepresented in the eval set.

10. **Single-Annotator Self-Consistency Protocol (Test-Retest)**:
    - *Decision*: Conducted a blind test-retest on a random 10% sample of the golden set ($N=17$) to compute Cohen’s Kappa ($\kappa=1.000$) rather than falsely claiming independent multi-annotator consensus.
    - *Reason*: Full transparency regarding single-annotator limitations is essential; measuring intra-annotator stability proves internal rubric consistency even if systemic personal bias exists.

11. **Multi-Dimensional LLM Judge Rubric**:
    - *Decision*: Assessed drafted replies across three distinct 1–5 dimensions (Groundedness, Tone, Actionability) provided with both customer query and retrieved context.
    - *Reason*: Evaluating fluency alone is misleading; an agent can draft a beautifully polite response that completely fabricates a refund commitment or fails to provide an actionable next step.

12. **Heuristic Hallucination Post-Processing Guard**:
    - *Decision*: Added explicit regular expression guards checking for fabricated order numbers (`\d{3}-\d{7}-\d{7}`), carrier tracking numbers (`TBA...`), and unauthorized dollar amounts in generated replies.
    - *Reason*: LLMs frequently hallucinate plausible-sounding identifiers; sanitizing these placeholders before public dispatch prevents severe customer confusion and customer service escalation.

13. **Explicit Scope Cuts**:
    - *Decision*: Deliberately excluded multi-turn memory management, direct CRM database lookups, and non-English customer response generation.
    - *Reason*: These features require live backend authentication and stateful session stores that exceed a first-contact triage system scope and could not be validated safely on static public Twitter data.
