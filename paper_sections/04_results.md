## 4. Results

### 4.1 RQ0: Response Rate — Do Engines Actually Recommend Products?

Across 900 API responses, 95.1% contained specific product recommendations. However, engine-level variance is significant:

| Engine | Recommendation Rate |
|---|---|
| ChatGPT | 98.4% |
| Gemini | 97.8% |
| Perplexity | 100.0% |
| DeepSeek | 98.3% |
| **Claude** | **84.0%** |

Claude's 84% recommendation rate is a statistically significant outlier (p < 0.01, χ² test). Claude's non-recommendation responses tended to provide general buying advice ("look for earbuds with ANC and good battery life") rather than specific product recommendations. This hedging pattern appears to be a feature of Anthropic's safety alignment — the model is trained to avoid making claims it cannot verify conclusively.

**Finding 1:** 1 in 6 queries to Claude yields no specific product recommendation. For consumers relying on a single AI engine, this means a non-trivial fraction of shopping queries go unanswered.

### 4.2 RQ1: Cross-Engine Consensus — Do Engines Agree?

We computed the Jaccard similarity index between all engine pairs. The average pairwise Jaccard score across all 10 engine pairs was **0.448** — engines agree on fewer than half of their product recommendations.

| Engine Pair | Jaccard Similarity |
|---|---|
| deepseek ↔ gemini | **0.571** (highest agreement) |
| chatgpt ↔ gemini | 0.515 |
| chatgpt ↔ deepseek | 0.492 |
| gemini ↔ perplexity | 0.470 |
| chatgpt ↔ perplexity | 0.449 |
| deepseek ↔ perplexity | 0.409 |
| claude ↔ gemini | 0.430 |
| claude ↔ chatgpt | 0.386 |
| claude ↔ deepseek | 0.381 |
| claude ↔ perplexity | **0.375** (lowest agreement) |

Several patterns emerge:
- **DeepSeek and Gemini show the closest alignment** (0.571), suggesting some shared training signal or evaluation criteria.
- **Claude is the consistent outlier**, showing the lowest agreement with every other engine. This aligns with Claude's distinct safety-based response pattern observed in RQ0.
- **No engine pair exceeds 0.6 Jaccard**, meaning even the most similar engines disagree on at least 40% of their recommendations.

**Finding 2:** A consumer who switches AI shopping engines may receive a completely different set of product recommendations more than half the time.

### 4.3 RQ2: Brand Bias — Do Engines Favor Big Brands?

The concentration of recommendations among dominant brands is striking. The top 3 brands across all categories (Keychron, ASICS, CeraVe) account for **16.0%** of all product mentions — despite representing a tiny fraction of the total available product universe.

| Category | Dominant Brand | % of Category Mentions |
|---|---|---|
| Keyboards | Keychron | 54.7% |
| Skincare | CeraVe | 42.1% |
| Running Shoes | ASICS | 31.2% |
| Earbuds | Anker | 28.6% |

These patterns cannot be fully explained by market share. Keychron holds an estimated 8-12% of the mechanical keyboard market, yet accounts for over half of all AI recommendations in the category. Similarly, CeraVe's market share in skincare is well below 42%. This suggests that AI engines are not simply reflecting market share — they are amplifying the visibility of brands that have strong online review presence, SEO optimization, and extensive product data.

**Finding 3:** AI shopping engines exhibit extreme brand concentration. Dominant brands receive recommendations at rates 3-5× their market share, while smaller brands are largely invisible.

### 4.4 RQ3: Determinism — Do Engines Agree with Themselves?

We measured each engine's self-consistency: for each query, what fraction of 3 repeated runs produced the same product?

| Engine | Self-Consistency Score |
|---|---|
| **Claude** | **0.679** (most self-consistent) |
| ChatGPT | 0.510 |
| DeepSeek | 0.497 |
| Perplexity | 0.485 |
| **Gemini** | **0.479** (least self-consistent) |

Even Claude, the most self-consistent engine, changes its recommendation about one-third of the time across repeated queries. The other four engines operate close to random — asking the same question three times produces the same answer only about half the time.

**Finding 4:** AI shopping recommendations are fundamentally non-deterministic at default settings. A consumer asking the same question one hour later has a substantial chance of receiving a different answer from the same engine.

### 4.5 RQ4: AgentShelf Score — Distribution and Validation

The AgentShelf Score was computed for all 606 unique product-query pairs. The distribution is skewed toward lower confidence:

| Confidence Tier | Score Range | % of Recommendations |
|---|---|---|
| Low | 0-49 | 37.2% |
| Moderate | 50-79 | 41.8% |
| High | 80-100 | 21.0% |

Only 1 in 5 product recommendations qualifies as "high confidence" — recommended consistently by multiple engines across multiple trials.

#### Validation Against Expert Recommendations

We cross-referenced the 10 products achieving the highest AgentShelf Score (96) against Wirecutter expert recommendations:

| Brand | Category | Score | Wirecutter Recommended? |
|---|---|---|---|
| Anker | earbuds | 96 | ❌ |
| TOZO | earbuds | 96 | ❌ |
| EarFun | earbuds | 96 | ✅ |
| Sony | earbuds | 96 | ✅ |
| Keychron | keyboards | 96 | ✅ |
| Nike | running_shoes | 96 | ❌ |
| ASICS | running_shoes | 96 | ✅ |
| Brooks | running_shoes | 96 | ❌ |
| CeraVe | skincare | 96 | ✅ |
| Neutrogena | skincare | 96 | ✅ |

**6 of 10 (60%)** high-scoring products also appeared in Wirecutter's expert recommendations — better than random chance but not diagnostic for a definitive validation given the small sample (n=10).

#### Sensitivity Analysis

We tested the sensitivity of the Score to weight variations by modifying each weight by ±0.1 while holding others constant. The relative ranking of top-scoring products remained stable, with no single product moving by more than 5 Score points across all weight variations.

### 4.6 Invisible Brands: Products Experts Love but AI Can't See

We identified products that receive top recommendations from Wirecutter experts but appear in zero or near-zero AI recommendations:

| Brand | Category | Wirecutter Recommendation | AI Mentions | Max Score |
|---|---|---|---|---|
| The Outset | skincare | ✅ Best for normal skin | **0** | N/A |
| Altra | running shoes | ✅ Best low-drop | **0** | N/A |
| Beats | earbuds | ✅ Best for working out | Minimal | Very low |
| Vanicream | skincare | ✅ Best for sensitive + extra-dry | 30 mentions | ~20 |

These "invisible brands" represent products that are objectively high-quality by expert standards but are systematically absent from AI shopping recommendations.

**Finding 5:** AI shopping recommendations suffer from two distinct problems — **inconsistency** (engines disagree with each other and with themselves), and **incomplete coverage** (good products are invisible to all engines). These are independent failures requiring different solutions.

We note that AI engines' knowledge bases are naturally narrower than Wirecutter's comprehensive testing scope. What appears as "bias" may partially reflect training data coverage limitations. However, the practical effect is the same: consumers who rely on AI for shopping advice are systematically missing out on expert-recommended products.
