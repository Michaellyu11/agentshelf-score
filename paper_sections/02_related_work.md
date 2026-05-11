## 2. Related Work

### 2.1 LLM Recommendation Bias

A growing body of literature examines bias in LLM-generated recommendations. Chen et al. (2025) show that ChatGPT's product recommendations exhibit systematic brand bias, favoring well-known brands over lesser-known alternatives. Ouyang et al. (2023) demonstrate that LLMs produce different outputs under the same prompt at temperature > 0, raising fundamental questions about recommendation determinism. More recently, Sharma (2026) — in the closest methodological predecessor to our work — tests the discoverability of 112 Product Hunt startups across two AI engines (ChatGPT and Perplexity), finding that AI assistants recognize 99% of products but actively recommend only 3%, suggesting a severe coverage bottleneck in startup contexts.

Our work extends Sharma's findings in three ways. First, we move from the startup domain to everyday consumer goods (electronics, apparel, beauty), where the consequences of biased recommendations are more widely felt. Second, we expand from 2 engines to 5, enabling cross-engine consensus analysis that Sharma's binary engine setup could not support. Third, we introduce a structured reliability score validated against expert product rankings.

### 2.2 AI Shopping Capability Benchmarks

A parallel line of work benchmarks the overall capability of AI agents in shopping scenarios. ShoppingComp (2025) evaluates AI models on 145 real-world shopping instances, finding that even GPT-5 achieves only 17.76% F1 on tasks requiring product search, attribute matching, and safe transaction execution. While ShoppingComp provides a comprehensive measure of shopping capability ceilings, it answers a different question from ours: it asks "how capable are AI agents at shopping" while we ask "how consistent are the shopping recommendations that AI agents already make." These are complementary perspectives: ShoppingComp establishes an upper bound on performance, while we measure the variance in real-world recommendation behavior.

### 2.3 GEO and AEO Tools

The commercial landscape includes several "Generative Engine Optimization" (GEO) and "Answer Engine Optimization" (AEO) tools. Profound, Otterly AI, and AIPRM offer dashboards that track brand visibility across AI search results. However, these tools operate behind proprietary paywalls, their methodologies are unpublished, and none provides an open, reproducible benchmark. To our knowledge, no commercial tool proposes a quantified reliability score or validates its outputs against expert human judgment.

### 2.4 LLM Non-Determinism

The non-deterministic nature of LLMs is well-documented. Studies have shown that even at temperature = 0, floating-point determinism is not guaranteed across hardware configurations (Zhu et al., 2024). For shopping recommendations specifically, this non-determinism creates a practical problem: a consumer asking the same question may receive different answers on different days, from the same engine. No prior work has measured this phenomenon in a shopping context across multiple engines.
