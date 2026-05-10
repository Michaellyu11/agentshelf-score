# HN Post — Final Draft
# Copy everything below the line into Hacker News

---

## Title:
I asked 5 AI shopping assistants the same 60 questions. They only agreed 45% of the time.

## Body:

I've been curious about how reliable AI shopping recommendations actually are, so I ran an experiment.

**Setup:** 60 real shopping queries across 4 categories (wireless earbuds, mechanical keyboards, running shoes, skincare), sent to 5 AI engines (ChatGPT, Gemini, Perplexity, Claude, DeepSeek), each repeated 3 times. 900 total API calls. All queries used the cheapest available model per engine (GPT-5.4-mini, Gemini 2.5 Flash, Sonar, Claude Haiku 4.5, DeepSeek Chat). Total cost: ~$40.

**Key findings:**

1. **Engines barely agree with each other.** Average pairwise Jaccard similarity was 0.448. The most aligned pair (DeepSeek + Gemini) agreed 57% of the time. The least aligned (Claude + Perplexity) agreed only 38%. Asking ChatGPT vs Gemini for "best earbuds under $100" gives you a meaningfully different answer more often than not.

2. **No engine even agrees with itself.** Each query was repeated 3 times. The most self-consistent engine was Claude at 0.679 — it still changes its recommendations ~1/3 of the time. Gemini was the most volatile at 0.479. Same prompt, same model, different products.

3. **Claude hedges more than others.** Only 84% of Claude's responses contained specific product names, vs 97%+ for every other engine. Claude tends to give criteria ("look for X feature") rather than specific products. Whether that's a bug or a feature is debatable.

4. **Brand concentration is striking.** Keychron appeared 181 times across keyboard queries — 3x more than the #2 brand (Royal Kludge at 60). CeraVe dominated skincare at 142 mentions. In earbuds, Anker (117) and Sony (114) were far ahead of Apple (63). Small/indie brands were nearly invisible across all engines.

5. **I tried defining a "consensus score"** — combining cross-engine agreement, self-consistency, and source citation rate. Only 21% of product-query pairs scored "high confidence" (all engines agree, stable across reps). 37% scored "low confidence" (one engine, inconsistent). The remaining 42% were somewhere in between.

**What surprised me most:** I expected brand bias. I didn't expect the sheer randomness. The same engine giving different top picks on the same query minutes apart feels like a fundamental problem for anyone relying on AI for purchase decisions.

**Methodology notes:**

- All engines used web search / grounding where available (ChatGPT web search, Gemini grounding, Perplexity native search, Claude web search tool, DeepSeek without search)
- System prompt was identical: "You are a helpful shopping assistant. When the user asks for product recommendations, provide specific product names, brands, and approximate prices. Be concrete — name actual products, not just categories. If you recommend multiple products, rank them from most recommended to least."
- Brand extraction used keyword matching against a known brands list (~150 brands), with word-boundary checks for short names
- DeepSeek has no web search capability, which may explain some divergence from web-grounded engines

**Limitations:**

- 3 reps per query is enough to see patterns but not statistically rigorous. 10+ would be better.
- Brand extraction is imperfect — some products may be missed or miscategorized
- Only tested English queries. Results could differ significantly in Chinese/other languages.
- Used cheapest models per engine — premium models (GPT-5.5, Claude Opus, Gemini Pro) may behave differently

Full dataset (900 responses as JSONL), analysis code, and all CSV outputs are on GitHub: [LINK]

Happy to answer questions about methodology or share any specific cuts of the data.
