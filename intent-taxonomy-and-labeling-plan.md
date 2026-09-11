# Intent Taxonomy & Labeling Plan — AmazonHelp Support Agent

## 0. How this taxonomy was derived (method, not just output)

Don't hand-invent intents from vibes — that's the first thing a grader will
poke at ("how do you know these are the real intents in the data?"). Process:

1. Pull all customer-first tweets (`in_response_to_tweet_id` is null, i.e. the
   thread-starting message) directed at `@AmazonHelp`.
2. Filter to English, strip @mentions/URLs, dedupe near-identical boilerplate
   (e.g. auto-generated "please DM us" chains aren't customer intents).
3. Embed a random sample of ~1,500–2,000 of these (sentence-transformers,
   `all-MiniLM-L6-v2` is fine and free) and run k-means with k swept from
   6–14, inspect silhouette score + eyeball 20 examples per cluster.
4. Use an LLM to propose a short label + definition per cluster from 15
   sampled examples, then you manually merge/split clusters that are
   obviously the same intent split by surface wording (e.g. "refund" and
   "return" often over-split).
5. Freeze a taxonomy of 7–9 intents + an `other/unclear` bucket. Anything
   below ~3% of sampled volume gets folded into a neighbor or into `other` —
   a 25-way taxonomy looks impressive and evaluates like garbage.

**This is a hypothesis until you run it on the real data.** The list below is
my best guess based on general knowledge of what shows up in Amazon customer
support Twitter threads (order/delivery issues, refunds, account lockouts,
billing, damaged/wrong items, app bugs, general complaints). Treat it as the
seed for step 4, not gospel — expect to merge or rename 1–2 categories once
you actually look at clusters.

## 1. Proposed taxonomy (8 intents + other)

| Intent | Definition | Included | Excluded (goes elsewhere) |
|---|---|---|---|
| `order_status_delivery` | Customer asking where an order is, delivery delayed/missing, tracking confusion | "where's my package", carrier issues, delivery marked delivered but not received | Item arrived damaged → `product_issue`; wrong item → `product_issue` |
| `refund_return` | Customer wants money back or wants to send an item back | refund not received, how to return, refund amount wrong | Disputing a charge they don't recognize → `billing_dispute` |
| `billing_dispute` | Charged incorrectly, double-charged, unauthorized charge, subscription billing confusion | Prime renewal disputes, unexpected charges | Refund status follow-up (already agreed) → `refund_return` |
| `account_access` | Locked out, can't log in, 2FA issues, suspicious activity on account | password reset, account suspended | Payment method declined → `billing_dispute` |
| `product_issue` | Item received damaged, wrong, defective, missing parts | DOA electronics, wrong size/color shipped | Just asking when it'll arrive → `order_status_delivery` |
| `app_website_bug` | Technical fault in the app/site itself, not tied to one order | checkout crashing, app won't load, page errors | Can't log in (belongs to account_access) |
| `cancellation` | Wants to cancel an order, subscription, or Prime membership | order cancel request, Prime cancel | Refund already requested for a cancelled order → `refund_return` |
| `general_complaint_vent` | Frustration/complaint with no clear actionable request, or venting about a past bad experience | "worst service ever", rhetorical complaints | Complaint that contains a specific actionable ask → classify by the ask |
| `other_unclear` | Doesn't fit above, non-English, spam, unrelated mentions, ambiguous fragments | — | — |

Note on **multi-intent messages** (common in real tweets, e.g. "my order is
late AND I was double charged"): label the **primary/most urgent** intent per
your own stated priority order (I'd rank: `billing_dispute` >
`account_access` > `product_issue` > `refund_return` > `cancellation` >
`order_status_delivery` > `app_website_bug` > `general_complaint_vent`), and
note the secondary intent in a free-text `notes` column. Document this rule
explicitly — it's exactly the kind of thing a grader will ask about live.

## 2. Labeling protocol for the golden set (150–250 examples)

**Sampling strategy (write this up honestly, it's graded):**
- Don't sample uniformly at random — rare intents will be nearly invisible.
- Do **stratified sampling**: aim for a rough floor of ~15 examples per
  intent bucket (use light keyword filters to pre-bucket candidates, e.g.
  "charge"/"billed" → billing_dispute candidates), then fill the remainder
  with pure random sampling from the full customer-first tweet pool so the
  golden set's overall intent *distribution* still resembles reality (report
  both: the stratified-target counts and the resulting natural-frequency
  estimate from a separate random draw, so you can show "here's what's
  actually common" vs. "here's coverage of rare-but-important cases").
- Include some deliberately hard/ambiguous examples (multi-intent, sarcasm,
  non-English fragments, very short "?" replies) — a golden set with only
  easy cases won't reveal anything.
- Exclude retweets, pure @mention spam, and non-English (or bucket into
  `other_unclear` and note it, don't just drop — dropping silently biases
  your denominator).

**Label schema per example:**
```
tweet_id, text, primary_intent, secondary_intent (nullable),
ideal_action (auto_handle | escalate), escalation_reason (if escalate),
ambiguity_flag (bool), notes (free text)
```

**Single-annotator honesty:** you're almost certainly labeling this alone.
Say so plainly in the report, don't dress it up. Mitigate with a
self-consistency check: re-label a random 10% of your own golden set
"blind" (shuffled, a few days later, without seeing your first label) and
report your own label-label agreement (Cohen's kappa or raw %). This is your
stand-in for inter-annotator reliability and directly answers "how much do
we trust the ground truth itself" in the mandatory misleading-number section.

**`ideal_action` labeling rule** (write this as an explicit rubric before you
start, not post-hoc): I'd suggest auto-handle is appropriate when (a) the
issue is informational/procedural and the brand has a consistent historical
resolution pattern for it, (b) no money/legal/safety language is present,
(c) it's not a repeat complaint in a thread. Escalate otherwise. Apply this
same rubric consistently to build ideal_action labels — then your model's
escalation decisions can be scored against it as precision/recall, not vibes.

## 3. Open decisions to confirm once you've seen real data
- Does `AmazonHelp` actually have enough volume/diversity, or should the
  brand be swapped?
- Do clusters actually match this 8-way structure, or is delivery vs. product
  issue too blurry to separate reliably (a real risk — worth checking
  cluster purity before committing)?
- What's the natural class imbalance? If >50% of traffic is
  `order_status_delivery`, your trivial baseline ("always guess majority
  class") may already look deceptively strong on raw accuracy — flag this
  now so it's not a surprise in the failure analysis.
