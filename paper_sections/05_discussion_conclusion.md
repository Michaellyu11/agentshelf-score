## 5. Discussion

### 5.1 Two Independent Failure Dimensions

Our results reveal that AI shopping recommendations fail along two independent dimensions:

**Dimension 1: Inconsistency.** Different AI engines give different answers to the same question (45% agreement). The same engine gives different answers to the same question on repeated runs (47-68% self-consistency). This problem can be mitigated through cross-engine consensus: by aggregating recommendations from multiple engines, consumers can filter out noise and identify products with broader agreement.

**Dimension 2: Incomplete coverage.** Some expert-recommended products are entirely invisible to all AI engines. This problem is more insidious than inconsistency: no amount of cross-engine averaging can surface a product that no engine sees. Coverage gaps require a fundamentally different approach — expanding AI training data and web search coverage to include the same breadth of products that expert reviewers evaluate.

We find that these two dimensions are largely orthogonal. A product with high cross-engine consensus (e.g., Anker earbuds, Score 96) may still differ from expert recommendations. Conversely, a product with strong expert endorsement (e.g., The Outset skincare) may be entirely absent from AI recommendations. Addressing both dimensions requires separate strategies: consensus-weighted recommendation for inconsistency, and systematic coverage expansion for invisibility.

### 5.2 Implications

**For consumers:** A single AI shopping engine offers unreliable recommendations. Using multiple engines improves reliability by approximately 15-20 percentage points (from ~45% consensus baseline), but even aggregated recommendations miss expert-approved products. Consumers should triangulate AI recommendations with established review sources.

**For brands and sellers:** Achieving visibility in one AI engine is insufficient. Brands must optimize for visibility across multiple engines simultaneously, as individual engines have distinct biases and blind spots. The "invisible brand" finding is particularly urgent: a Wirecutter-recommended product can have zero AI visibility.

**For AI platforms:** Our findings suggest that recommendation transparency is both measurable and improvable. Publishing cross-engine consensus scores could increase consumer trust. Additionally, addressing coverage gaps — ensuring that products meeting basic quality standards are at least recognizable by AI — is a tractable engineering problem.

**For regulators:** As AI shopping assistants influence consumer purchasing decisions at scale, the lack of recommendation reliability standards is concerning. An open, independently verifiable metric like AgentShelf Score could serve as a baseline for "responsible AI shopping."

### 5.3 Limitations

Our study has several important limitations:

1. **Limited sample size.** Our ground truth validation is based on 10 high-scoring products across 4 categories. This is sufficient for a pilot study but inadequate for definitive statistical validation. A larger study with more categories, more queries, and more repetitions is needed.

2. **Single expert source.** We used only Wirecutter as our expert validation source. Multiple expert sources (RTINGS, Consumer Reports, specialty reviewers) would provide more robust ground truth.

3. **Static snapshot.** Our data represents a single point in time. AI engine behavior changes with model updates, data refreshes, and deployment changes.

4. **Non-causal analysis.** We observe brand concentration but cannot definitively attribute it to algorithm bias vs. training data coverage vs. search result availability. Disentangling these causes requires controlled experiments beyond the scope of this paper.

5. **English-language queries only.** Our queries were conducted in English. AI shopping behavior for non-English queries — particularly in languages where training data is sparser — may differ substantially.

### 5.4 Future Work

We identify several promising directions:

- **Temporal analysis.** Repeating the same experiment at intervals (1 week, 1 month, 3 months) to measure recommendation stability over time and after model updates.
- **Coverage expansion.** Investigating the "knowledge base gap" between AI training data and comprehensive product databases.
- **Multi-source validation.** Expanding ground truth to include RTINGS, Consumer Reports, and category-specific expert sources.
- **Geographic variation.** Testing whether same-engine recommendations differ across geographic markets.
- **Intervention studies.** Testing whether structured product data submission (e.g., schema.org markup, product feeds) improves AI engine coverage for previously invisible brands.

## 6. Conclusion

We demonstrate that AI shopping recommendations exhibit systematic inconsistency and incomplete coverage. Across 5 engines, 60 queries, and 900 responses, engines agree on only 45% of recommendations, no engine consistently agrees with itself (47-68% self-consistency), and expert-recommended products are sometimes entirely invisible to all engines.

We propose the AgentShelf Score, a cross-engine consensus metric that distinguishes high-confidence recommendations (21% of all recommendations) from low-confidence ones (37%). Preliminary validation against Wirecutter expert rankings shows that 60% of high-scoring products are also expert-endorsed, suggesting the Score has meaningful predictive power.

Our central argument is that AI shopping recommendations suffer from two independent problems — inconsistency and incomplete coverage — which require different solutions. Cross-engine consensus addresses the former; systematic coverage expansion addresses the latter.

**Open artifacts.** To support replication and community contribution, we release:
- **Full dataset**: 900 structured AI shopping responses at github.com/Michaellyu11/agentshelf
- **AgentShelf Score calculator**: open-source Python package for computing cross-engine consensus scores
- **Invisible Brand Detector**: tool to check whether a product is visible across 5 AI engines at agentshelf.co

We invite researchers, practitioners, and regulators to use, critique, and extend these tools. The goal is not a single benchmark, but an open, evolving standard for AI shopping recommendation reliability.
