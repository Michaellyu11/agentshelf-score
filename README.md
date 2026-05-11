# AgentShelf Score: Do AI Shopping Assistants Agree?

We asked 5 AI shopping engines the same 60 questions. **They only agreed 45% of the time.**

Same question, different AI, different product, different price. A consumer asking ChatGPT "best earbuds under $50" gets recommended a $48 product. The same consumer asking DeepSeek gets a $25 product. Gemini can't even agree with itself — it gave a different #1 pick each of the 3 times we asked.

## Key Findings

| Finding | Detail |
|---|---|
| **Cross-engine agreement** | 44.8% average Jaccard similarity across engine pairs |
| **Self-consistency** | Best engine (Claude) still changes its mind 32% of the time. Worst (Gemini): 52% |
| **Brand concentration** | Keychron: 181 mentions in keyboards. CeraVe: 142 in skincare. Small brands nearly invisible |
| **High-confidence recommendations** | Only 21% of product-query pairs score "high confidence" (all engines agree + stable) |
| **Response rate** | Claude only recommends specific products 84% of the time (others: 97%+) |

## What is AgentShelf Score?

A simple reliability metric for AI shopping recommendations, combining:
- **Cross-engine consensus** (do multiple AI engines agree?) — 50% weight
- **Self-consistency** (does the same engine give the same answer twice?) — 30% weight  
- **Source citation rate** (does the recommendation cite sources?) — 20% weight

Score range: 0-100. High (80+) = trustworthy. Low (<50) = likely biased or unreliable.

## Experiment Setup

- **Engines:** ChatGPT (GPT-5.4-mini), Gemini (2.5 Flash), Perplexity (Sonar), Claude (Haiku 4.5), DeepSeek (Chat)
- **Categories:** Wireless earbuds, mechanical keyboards, running shoes, skincare
- **Queries:** 60 real shopping queries varying by price range, use case, and user persona
- **Repetitions:** 3 per (query, engine) pair
- **Total:** 900 API calls, ~$40 cost
- **Date:** May 10, 2026

## Repository Structure

```
├── run_experiment.py          # Data collection script (60 queries × 5 engines × N reps)
├── analyze_results.py         # Analysis: consensus, brand bias, self-consistency, Score
├── index.html                 # Interactive dashboard (deploy to GitHub Pages)
├── results/
│   ├── experiment_*.jsonl     # Raw data (900 responses)
│   └── analysis_*/
│       ├── summary.txt
│       ├── rq0_response_rate.csv
│       ├── rq1_consensus.csv
│       ├── rq2_brand_bias.csv
│       ├── rq3_self_consistency.csv
│       ├── rq4_agentshelf_scores.csv
│       ├── all_products_extracted.csv
│       └── raw_brand_counts.csv
├── app/
│   └── core/
│       ├── api_client.py      # Multi-engine API client
│       └── config.py          # Configuration
├── .env.example               # API key template
└── run.sh                     # Quick-start script
```

## Run It Yourself

```bash
# 1. Clone
git clone https://github.com/Michaellyu11/agentshelf-score.git
cd agentshelf-score

# 2. Set up API keys
cp .env.example .env
# Edit .env with your keys for OpenAI, Anthropic, Google, Perplexity, DeepSeek

# 3. Install dependencies
pip install httpx pydantic-settings python-dotenv

# 4. Test (5 calls, ~$0.25)
python -m app.run_experiment --test

# 5. Run experiment (900 calls, ~$40)
python -m app.run_experiment --full --reps 3

# 6. Analyze
python analyze_results.py
```

## Methodology Notes

- All engines used web search/grounding where available (DeepSeek was the exception)
- Identical system prompt across all engines: "You are a helpful shopping assistant..."
- Brand extraction uses keyword matching against ~150 known brands with word-boundary checks
- AgentShelf Score weights are initial estimates; future work will optimize against expert rankings (Wirecutter, RTINGS)

## Limitations

- 3 reps per query shows patterns but isn't statistically rigorous (10+ would be better)
- Brand extraction is imperfect — some products may be missed or miscategorized
- English queries only — results likely differ in Chinese and other languages
- Cheapest models per engine — premium models (GPT-5.5, Claude Opus, Gemini Pro) may behave differently
- Snapshot in time — AI models update frequently

## License

MIT. Data and code are free to use, cite, and build upon.

## Paper

A full research paper based on this dataset is available:

> **"The Consistency Crisis in AI Shopping Recommendations: Inconsistency, Invisibility, and the AgentShelf Score"**
> Zhiyi (Michael) Lyu — AgentShelf Research / Northeastern University
> [`paper_final.docx`](./paper_final.docx) — draft for arXiv submission (May 2026)

### Abstract

Across 900 AI shopping responses, five major engines agree on only 44.8% of product recommendations. We identify two independent failure modes — **inconsistency** (engines disagree with each other and themselves) and **invisibility** (expert-recommended products absent from all engines). The AgentShelf Score, validated against Wirecutter and logistic regression (ρ = 0.791, p < 0.0001), provides a cross-engine consensus metric for AI shopping reliability.

## Contact

Built by [Zhiyi (Michael) Lyu](https://github.com/Michaellyu11) — AgentShelf

Questions, ideas, or want to contribute more categories/engines? Open an issue or reach out.
