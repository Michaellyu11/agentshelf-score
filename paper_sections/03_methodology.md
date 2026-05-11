## 3. Methodology

### 3.1 Engine Selection

We evaluated five AI shopping engines selected for their relevance to consumer shopping decisions:

| Engine | Model | Provider | Web Search | Key Feature |
|---|---|---|---|---|
| ChatGPT | GPT-5.4-mini | OpenAI | Enabled | Largest consumer install base |
| Gemini | 2.5 Flash | Google | Enabled (grounding) | Deep Google Shopping integration |
| Perplexity | Sonar Pro | Perplexity | Enabled | Native shopping search mode |
| Claude | Sonnet 4.5 (Haiku 4.5) | Anthropic | Enabled | Strong safety / refusal patterns |
| DeepSeek | DeepSeek Chat | DeepSeek | Enabled | Eastern market perspective |

All engines were accessed through their standard API endpoints with default temperature settings, preserving real-world recommendation behavior. Web search was enabled for all engines where supported.

### 3.2 Query Design

We designed 60 shopping queries across 4 product categories:

| Category | Type | # Queries | Price Range |
|---|---|---|---|
| Wireless Earbuds | Electronics, spec-driven | 15 | $30-$250 |
| Mechanical Keyboards | Electronics, enthusiast | 15 | $50-$200 |
| Running Shoes | Apparel, functional | 15 | $50-$200+ |
| Skincare | Beauty, subjective | 15 | $10-$80+ |

Within each category, queries were designed to vary along three dimensions:
- **Price sensitivity**: budget ($30-50), mid-range ($50-100), premium ($100+)
- **Use case specificity**: specific ("best ANC earbuds under $80 for commuting"), moderate ("best wireless earbuds under $100"), vague ("good earbuds")
- **User persona**: student, professional, parent, athlete

Each of the 60 queries was submitted to each of the 5 engines, repeated 3 times (on separate API calls to avoid caching effects), yielding 900 total responses.

### 3.3 Data Collection Pipeline

Each API response was parsed using a structured extraction pipeline that identified:
- Product brand and model name mentioned in the recommendation
- Ranking position (when specified)
- Mentioned price
- Whether a source/citation was provided
- Whether the response contained an actual product recommendation vs. general advice

Brand names were normalized across variations (e.g., "Sony's WF-1000XM5" → "Sony").

### 3.4 AgentShelf Score Formula

We propose the AgentShelf Score, a composite metric designed to quantify recommendation reliability:

```
AgentShelf Score = 100 × (CE_consensus × 0.5 + self_consistency × 0.3 + citation_rate × 0.2)
```

Where:
- **CE_consensus** (0-1): fraction of the 5 engines that recommended this product for the same query. A product recommended by all 5 engines scores 1.0; a product recommended by only 1 engine scores 0.2.
- **Self_consistency** (0-1): fraction of the 3 repetitions where this product appeared in the same engine's recommendations. A product that appears in all 3 runs scores 1.0; appearing in only 1 run scores 0.33.
- **Citation_rate** (0-1): fraction of recommendations that cite a verifiable external source. An engine that always cites sources scores 1.0; never citing scores 0.0.

Score thresholds: 80-100 (high confidence), 50-79 (moderate confidence), 0-49 (low confidence).

These weights were selected to reflect the relative importance of cross-engine agreement (most indicative of reliability), self-consistency (ensures the recommendation is not a random sample), and source quality (adds a verifiability layer). We report sensitivity analysis in Section 4.5.

### 3.5 Expert Validation Method

For each of the 4 product categories, we collected the top-5 product recommendations from Wirecutter (The New York Times' product review service). We compared these expert rankings against AgentShelf Score rankings using:

1. **Top-score agreement rate**: for products achieving AgentShelf Score ≥ 90, what fraction also appear in Wirecutter's recommendations?
2. **Coverage gap**: what fraction of Wirecutter's recommended products appear in 0 or 1 AI engines?
3. **Qualitative analysis**: for products that score highly on AgentShelf but are absent from expert recommendations — and vice versa — we examine the possible causes of disagreement.
