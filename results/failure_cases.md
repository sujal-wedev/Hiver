# Systematic Failure Analysis — AmazonHelp Support Agent

This document examines 5 real representative failure cases encountered during evaluation on the golden evaluation set (`golden_set/golden_eval_v1.csv`). Each case details the customer input, system prediction vs. ground truth, and root cause diagnosis.

## Failure Case 1: False Negative Escalation (Safety/Financial Under-triage)
- **Tweet ID**: `1002`
- **Customer Message**: "Tracking says my parcel was handed to resident but nobody was home and my porch is empty!"
- **Ground Truth**: Intent = `order_status_delivery`, Ideal Action = `escalate`
- **System Output**: Intent = `order_status_delivery`, Decision = `auto_handle`
- **System Escalation Justification**: "Auto-handled: Procedural/informational request with zero risk signals detected"
- **Drafted Reply**: "We're sorry for the delivery delay! Please send us a DM with your 17-digit order number so we can investigate with the carrier. ^AH"
- **Root Cause Hypothesis**: The customer's message expressed subtle dispute or indirect fraud indicators without explicit trigger keywords ($ or legal threats), causing the deterministic policy to default to auto-handle.

---

## Failure Case 2: False Negative Escalation (Safety/Financial Under-triage)
- **Tweet ID**: `1005`
- **Customer Message**: "My delivery driver threw the package over the fence into the rain! The box is soaking wet."
- **Ground Truth**: Intent = `order_status_delivery`, Ideal Action = `escalate`
- **System Output**: Intent = `order_status_delivery`, Decision = `auto_handle`
- **System Escalation Justification**: "Auto-handled: Procedural/informational request with zero risk signals detected"
- **Drafted Reply**: "We're sorry for the delivery delay! Please send us a DM with your 17-digit order number so we can investigate with the carrier. ^AH"
- **Root Cause Hypothesis**: The customer's message expressed subtle dispute or indirect fraud indicators without explicit trigger keywords ($ or legal threats), causing the deterministic policy to default to auto-handle.

---

## Failure Case 3: False Negative Escalation (Safety/Financial Under-triage)
- **Tweet ID**: `1007`
- **Customer Message**: "Package marked as delivered in mailbox, but the parcel is too big to fit in any mailbox!"
- **Ground Truth**: Intent = `order_status_delivery`, Ideal Action = `escalate`
- **System Output**: Intent = `order_status_delivery`, Decision = `auto_handle`
- **System Escalation Justification**: "Auto-handled: Procedural/informational request with zero risk signals detected"
- **Drafted Reply**: "We're sorry for the delivery delay! Please send us a DM with your 17-digit order number so we can investigate with the carrier. ^AH"
- **Root Cause Hypothesis**: The customer's message expressed subtle dispute or indirect fraud indicators without explicit trigger keywords ($ or legal threats), causing the deterministic policy to default to auto-handle.

---

## Failure Case 4: Intent Misclassification (order_status_delivery -> other_unclear)
- **Tweet ID**: `1009`
- **Customer Message**: "Driver marked address inaccessible even though security gate was wide open all day."
- **Ground Truth**: Intent = `order_status_delivery`, Ideal Action = `auto_handle`
- **System Output**: Intent = `other_unclear`, Decision = `auto_handle`
- **System Escalation Justification**: "Auto-handled: Procedural/informational request with zero risk signals detected"
- **Drafted Reply**: "Thanks for reaching out to Amazon Help. Please send us a direct message with more details so we can best assist you. ^AH"
- **Root Cause Hypothesis**: Surface overlap between related operational categories (e.g., return vs billing dispute) or complex multi-intent phrasing where secondary intent was favored.

---

## Failure Case 5: False Negative Escalation (Safety/Financial Under-triage)
- **Tweet ID**: `1014`
- **Customer Message**: "Driver signed my name on the delivery confirmation when I was at work! I don't have my parcel."
- **Ground Truth**: Intent = `order_status_delivery`, Ideal Action = `escalate`
- **System Output**: Intent = `order_status_delivery`, Decision = `auto_handle`
- **System Escalation Justification**: "Auto-handled: Procedural/informational request with zero risk signals detected"
- **Drafted Reply**: "We're sorry for the delivery delay! Please send us a DM with your 17-digit order number so we can investigate with the carrier. ^AH"
- **Root Cause Hypothesis**: The customer's message expressed subtle dispute or indirect fraud indicators without explicit trigger keywords ($ or legal threats), causing the deterministic policy to default to auto-handle.

---

