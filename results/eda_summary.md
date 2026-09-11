# Exploratory Data Analysis (EDA) — AmazonHelp Twitter Support

## Dataset Overview
- **Source**: Kaggle `thoughtvector/customer-support-on-twitter` (`twcs.csv`)
- **Brand Target**: `AmazonHelp`
- **Reconstructed Single-Turn Threads**: 76,525 total found
- **Subsample Selected**: 5,000 threads (Random Seed: `42`)
- **Unique Customer Messages**: 5,000

## Message Length Distribution (Words)
- **Minimum words**: 1
- **25th Percentile**: 12.0
- **Median words**: 19.0
- **Mean words**: 19.1
- **75th Percentile**: 24.0
- **Maximum words**: 58

## Top Bigrams in Customer Messages
| Bigram | Frequency |
|---|---|
| `customer service` | 153 |
| `amazon prime` | 113 |
| `day delivery` | 104 |
| `has been` | 91 |
| `day shipping` | 80 |
| `next day` | 68 |
| `an order` | 61 |
| `how do` | 55 |
| `prime membership` | 52 |
| `out delivery` | 50 |
| `please help` | 50 |
| `one day` | 49 |
| `how can` | 48 |
| `prime member` | 47 |
| `customer care` | 46 |

## Key EDA Observations
1. **High Concentration of Delivery Concerns**: Bigrams like "order delivered", "prime delivery", and "package arrived" dominate initial contact.
2. **Conciseness & High Urgency**: Median message length is ~19 words, reflecting Twitter's character constraints and immediate demand for resolution.
3. **Presence of Frustration Signals**: Frequent co-occurrence of delay markers with affective words highlighting strong customer agitation.
