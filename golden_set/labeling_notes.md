# Golden Evaluation Set: Sampling Protocol, Rubric, and Self-Consistency Notes

## 1. Sampling Strategy
To evaluate customer-support triage with statistical rigor, uniform random sampling is inadequate because high-frequency intents (like generic tracking inquiries) overwhelm low-frequency, high-stakes intents (like security lockouts or billing disputes).

We utilized a **two-stage stratified sampling protocol** applied to the processed corpus of 5,000 real AmazonHelp threads:
1. **Keyword-Heuristic Stratification**: We defined targeted keyword patterns across the 8 primary intent categories to identify candidate pools from the actual customer tweet corpus (`data/processed/amazonhelp_threads.parquet`). From each pool, we drew a quota of 15–20 tweets closest to category centroids.
2. **Natural Random Backfill**: We drew an unstratified random sample of customer-first tweets to reflect natural tweet distributions, including short fragments, non-English tweets, and social banter.
3. **Non-English & Edge Case Inclusion**: We explicitly sampled 8 non-English or highly ambiguous tweets to ensure the `other_unclear` category has realistic edge case coverage.
4. **Total Dataset**: 208 hand-labeled examples saved in `golden_set/golden_eval_v1.csv`.

**Source Data**: All tweets are sourced from the Kaggle `thoughtvector/customer-support-on-twitter` dataset (`twcs.csv`), filtered to single-turn customer→AmazonHelp threads. Tweet IDs are the original dataset IDs, not sequential integers.

### Intent Class Distribution (N=208)
| Intent | Count | Stratified Proportion | Natural Est. Proportion |
|---|---|---|---|
| `order_status_delivery` | 33 | 15.9% | ~36% |
| `refund_return` | 22 | 10.6% | ~12% |
| `billing_dispute` | 21 | 10.1% | ~8% |
| `product_issue` | 20 | 9.6% | ~14% |
| `account_access` | 20 | 9.6% | ~5% |
| `app_website_bug` | 7 | 3.4% | ~2% |
| `cancellation` | 21 | 10.1% | ~5% |
| `general_complaint_vent` | 20 | 9.6% | ~9% |
| `other_unclear` | 44 | 21.2% | ~9% |

**Note on `other_unclear` proportion**: This category is over-represented because the stratified sampling includes non-English tweets, ambiguous fragments, and tweets that do not match any keyword heuristic. In production traffic, this proportion would be lower.

---

## 2. Ideal Action Rubric (`auto_handle` vs. `escalate`)
The label `ideal_action` reflects whether the tweet can be handled procedurally by an automated workflow or requires human agent intervention:

### `auto_handle` Criteria:
1. **Informational & Procedural**: The customer inquiry can be answered using standard public knowledge, clear self-serve steps, or standard tracking instructions (e.g. tracking URL, return QR code instructions, password reset link reissue).
2. **Absence of Risk**: No financial dispute claims (over $10), no legal threats (lawyer, BBB), no report of fraud/account takeover, and no broken glass or hazardous product reports.
3. **Single Turn**: The customer has not stated that previous support agents failed or hung up.

### `escalate` Criteria:
1. **Financial & Billing Risk**: Duplicate charges, unauthorized transactions, disputed restocking fees, or unfulfilled refund promises.
2. **Account Security**: Account lockouts, hacked profiles, 2FA recovery without phone access.
3. **Severe Product / Safety Defects**: Shattered glass, leaked hazmat chemicals, expired food/medicine, tampered empty box deliveries.
4. **Legal / Churn Threats**: Mentions of "lawyer", "BBB", "chargeback", or supervisor demands.

---

## 3. Multi-Intent Priority Resolution Rule
When a tweet expresses multiple intents simultaneously (e.g., late package leading to demand for full refund or chargeback), the annotator assigns the single most urgent category as `primary_intent` according to this strict priority ranking:
```
billing_dispute > account_access > product_issue > refund_return > cancellation > order_status_delivery > app_website_bug > general_complaint_vent > other_unclear
```
The secondary concern is recorded in the `secondary_intent` column.

---

## 4. Labeling Process & Heuristic Pre-Fill Disclosure
The golden set labels were produced via a **two-pass human annotation process**:

1. **Pass 1 (Heuristic Pre-Fill)**: An automated keyword-matching script (`src/build_golden_set.py`) pre-populated `primary_intent` and `ideal_action` columns with best-guess heuristic labels based on keyword patterns. This served as a starting point to accelerate human review, NOT as ground truth.
2. **Pass 2 (Human Review & Correction)**: The annotator manually reviewed every row, correcting mislabeled intents (especially multi-intent tweets, sarcastic vents, and ambiguous fragments), adjusting `ideal_action` based on the rubric above, and adding `secondary_intent`, `escalation_reason`, `ambiguity_flag`, and `notes` where applicable.

## 5. Single-Annotator Disclosure & Self-Consistency Check
Because this dataset was created by a single annotator, inter-rater reliability was measured using a **blind test-retest self-consistency protocol**:
- A random 10% sample (N=20 rows) was extracted, shuffled, and re-labeled blind without viewing the original labels.
- Agreement was calculated using Cohen's Kappa (κ) and raw exact agreement percentage.

### Reliability Results:
- **Primary Intent Agreement**:
  - **Cohen's Kappa (κ)**: To be computed after re-labeling pass
  - **Exact Agreement Rate**: To be computed after re-labeling pass
- **Ideal Action Agreement**:
  - **Cohen's Kappa (κ)**: To be computed after re-labeling pass
  - **Exact Agreement Rate**: To be computed after re-labeling pass

*Note on Bias*: While self-consistency is expected to be high due to strict adherence to the written rubric, single-annotator bias may still reflect systematic personal interpretations of ambiguous sarcasm or edge cases. This is discussed transparently in `report.md`.
