# AgentShelf Score: Measuring AI Shopping Recommendation Reliability Through Cross-Engine Consensus

## 1. Introduction

Consider this scenario: a consumer asks five different AI shopping assistants for the same recommendation — "What are the best wireless earbuds under $50?" One engine recommends Anker. Another suggests TOZO. A third recommends EarFun. The fourth picks Sony. The fifth picks Anker again. Across 60 such queries, we find that AI shopping engines agree on only 45% of their product recommendations.

This is not merely an academic curiosity. AI shopping assistants — including ChatGPT with web search (OpenAI, 2026), Google Gemini, Perplexity, Claude (Anthropic), and DeepSeek — are increasingly serving as primary purchase advisors for consumers. OpenAI's ChatGPT Shopping feature alone reaches hundreds of millions of monthly active users. Perplexity's shopping integration surfaces product recommendations alongside search results. Google's AI Overviews now include purchase recommendations. Yet no independent, cross-engine benchmark exists to measure how reliable, consistent, or biased these recommendations are.

Prior work has examined LLM-based recommendation bias (Sharma et al., 2025; Chen et al., 2025), non-determinism in LLM responses (Ouyang et al., 2023), and the general capability of AI shopping agents (ShoppingComp, 2025). The closest work in spirit, Sharma's "The Discovery Gap" (2026), finds that AI assistants recognize 99% of Product Hunt startups but actively recommend only 3% — a striking demonstration of recommendation coverage bias in the startup domain. ShoppingComp (2025) shows that even the most advanced models achieve only 17.76% F1 on complex shopping tasks. However, no existing study systematically compares recommendation outputs across multiple AI shopping engines for the same consumer queries, at the same time, with multiple repetitions.

In this paper, we introduce the AgentShelf Score, a cross-engine consensus metric that quantifies the reliability of AI shopping recommendations. Our contributions are threefold:

1. **A multi-engine benchmark.** We evaluate 5 AI shopping engines (ChatGPT, Gemini, Perplexity, Claude, DeepSeek) across 60 shopping queries, 4 product categories, and 3 repetitions per query, producing 900 structured responses.

2. **The AgentShelf Score.** We propose a weighted metric combining cross-engine agreement (consensus), recommendation stability (self-consistency), and source citation rate, and provide an initial validation against expert recommendations from Wirecutter.

3. **Two-dimensional failure analysis.** We decompose AI shopping recommendation failures into two independent problems — *consistency* (do engines agree with each other?) and *coverage* (do engines see the same products at all?) — and demonstrate that these require different solutions.
