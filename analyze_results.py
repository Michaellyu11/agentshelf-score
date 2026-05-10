"""
AgentShelf Score — Analyze Experiment Results
=============================================
Reads the JSONL output from run_experiment.py and produces:
1. RQ0: What % of responses contain actual product recommendations?
2. RQ1: Cross-engine consensus (Jaccard similarity between engine pairs)
3. RQ2: Brand bias analysis (do engines favor big brands?)
4. RQ3: Self-consistency (does the same engine give the same answer twice?)
5. RQ4: AgentShelf Score computation for every product found
6. Summary stats + key findings for HN post / paper

Usage:
  python analyze_results.py results/experiment_YYYYMMDD_HHMMSS.jsonl

Output:
  results/analysis_YYYYMMDD_HHMMSS/
    ├── summary.txt           # Key findings (human-readable)
    ├── rq0_response_rate.csv
    ├── rq1_consensus.csv
    ├── rq2_brand_bias.csv
    ├── rq3_self_consistency.csv
    ├── rq4_agentshelf_scores.csv
    ├── all_products_extracted.csv
    └── raw_brand_counts.csv
"""

import json
import re
import sys
import csv
from collections import Counter, defaultdict
from pathlib import Path
from itertools import combinations

# ── Brand extraction ──────────────────────────────────────────────

# Known brands for fuzzy matching (add more as needed)
KNOWN_BRANDS = {
    # Earbuds
    "sony", "apple", "samsung", "bose", "jabra", "sennheiser", "anker",
    "soundcore", "jbl", "beats", "google", "pixel", "nothing",
    "earfun", "edifier", "skullcandy", "shure", "jaybird", "tozo",
    "1more", "technics", "bang & olufsen", "b&o", "fiio", "moondrop",
    "soundpeats", "liberty", "huawei", "oneplus", "oppo", "realme",
    "marshall", "audio-technica", "audio technica", "beyerdynamic",
    # Keyboards
    "keychron", "logitech", "razer", "corsair", "ducky", "leopold",
    "varmilo", "anne pro", "akko", "royal kludge", "rk", "glorious",
    "wooting", "nuphy", "hhkb", "realforce", "topre", "das keyboard",
    "steelseries", "hyperx", "kinesis", "ergodox", "zsa", "monsgeek",
    "epomaker", "yunzii", "gamakay", "redragon", "havit", "ajazz",
    # Running shoes
    "nike", "adidas", "asics", "brooks", "new balance", "hoka",
    "saucony", "mizuno", "on running", "on cloud", "puma", "reebok",
    "under armour", "altra", "salomon", "merrell", "la sportiva",
    "newton", "topo athletic", "craft", "karhu",
    # Skincare
    "cerave", "la roche-posay", "la roche posay", "neutrogena", "olay",
    "the ordinary", "paula's choice", "paulas choice", "drunk elephant",
    "skinceuticals", "tatcha", "clinique", "estee lauder", "shiseido",
    "sk-ii", "sk ii", "murad", "retinol", "differin", "adapalene",
    "niacinamide", "cetaphil", "aveeno", "eucerin", "vanicream",
    "versed", "inkey list", "good molecules", "cosrx", "beauty of joseon",
    "innisfree", "laneige", "sulwhasoo", "kiehl's", "kiehls",
    "dermalogica", "vichy", "bioderma", "avene", "elta md", "eltamd",
    "supergoop", "sun bum",
}

# Normalize brand name
def normalize_brand(brand: str) -> str:
    b = brand.lower().strip()
    # Common aliases
    aliases = {
        "b&o": "bang & olufsen",
        "b and o": "bang & olufsen",
        "audio technica": "audio-technica",
        "paulas choice": "paula's choice",
        "la roche posay": "la roche-posay",
        "sk ii": "sk-ii",
        "kiehls": "kiehl's",
        "on running": "on running",
        "on cloud": "on running",
        "rk": "royal kludge",
        "elta md": "eltamd",
        "inkey list": "the inkey list",
    }
    return aliases.get(b, b)


def extract_products(text: str) -> list[dict]:
    """
    Extract brand names and product names from AI response text.
    Returns list of {"brand": str, "product": str, "rank": int}
    """
    if not text:
        return []
    
    products = []
    seen_brands = set()
    rank = 0
    
    # Strategy 1: Look for numbered lists (most common AI response format)
    # Matches: "1. Brand Product", "1) Brand Product", "**1. Brand Product**"
    lines = text.split("\n")
    
    # Brands that need word-boundary matching (too short / common words)
    SHORT_BRANDS = {"on", "rk", "jbl", "1more", "b&o"}
    
    def brand_in_text(brand: str, text: str) -> bool:
        """Check if brand appears in text, using word boundaries for short/ambiguous brands."""
        b = brand.lower()
        t = text.lower()
        if b in SHORT_BRANDS or len(b) <= 3:
            # Use word boundary regex for short brands
            # "on" should match "On Running" or "On Cloud" but not "commuting on the subway"
            # Require brand to be at start of a word, followed by space+capital letter or known product term
            pattern = r'(?<![a-z])' + re.escape(b) + r'(?![a-z])'
            match = re.search(pattern, t)
            if match and b == "on":
                # Extra check for "on": only match if followed by running/cloud/cloudmonster
                # or preceded by brand-like context (numbered list start, bold, etc.)
                after = t[match.end():match.end()+30].strip()
                # Check if "on" is used as a brand (On Running, On Cloud, etc.)
                on_brand_patterns = ["running", "cloud", "cloudmonster", "cloudflow", 
                                     "cloudnova", "cloudswift", "cloudace", "cloudventure",
                                     "cloudultra", "cloudgo", "cloudsurfer", "roger"]
                if any(after.startswith(p) for p in on_brand_patterns):
                    return True
                # Also match "On " at start of a numbered list item
                before = t[max(0,match.start()-5):match.start()]
                if re.search(r'[\d.)]\s*\**\s*$', before):
                    return True
                return False
            return bool(match)
        else:
            return b in t
    
    for line in lines:
        line_clean = line.strip().strip("*").strip()
        
        # Check for numbered items
        num_match = re.match(r'^[\*\s]*(\d+)[.)]\s*\**\s*(.+)', line_clean)
        if num_match:
            item_text = num_match.group(2).strip().strip("*").strip()
            # Try to find a known brand in this line
            for brand in KNOWN_BRANDS:
                if brand_in_text(brand, item_text):
                    norm = normalize_brand(brand)
                    if norm not in seen_brands:
                        rank += 1
                        seen_brands.add(norm)
                        # Extract product name: text up to first dash, paren, or period
                        prod_match = re.match(r'^([^—\-\(]+)', item_text)
                        prod_name = prod_match.group(1).strip().strip("*") if prod_match else item_text[:60]
                        products.append({
                            "brand": norm,
                            "product": prod_name,
                            "rank": rank,
                        })
                    break
    
    # Strategy 2: If numbered list extraction found nothing, scan full text
    if not products:
        rank = 0
        for brand in KNOWN_BRANDS:
            if brand_in_text(brand, text) and normalize_brand(brand) not in seen_brands:
                norm = normalize_brand(brand)
                seen_brands.add(norm)
                rank += 1
                products.append({
                    "brand": norm,
                    "product": f"(mentioned: {brand})",
                    "rank": rank,
                })
    
    return products


def has_specific_recommendation(text: str) -> bool:
    """Check if response contains at least one specific product recommendation."""
    if not text:
        return False
    products = extract_products(text)
    return len(products) >= 1


# ── Analysis Functions ────────────────────────────────────────────

def jaccard(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def analyze(input_file: str):
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}")
        sys.exit(1)
    
    # Create output directory
    timestamp = input_path.stem.replace("experiment_", "")
    output_dir = input_path.parent / f"analysis_{timestamp}"
    output_dir.mkdir(exist_ok=True)
    
    # Load data
    records = []
    with open(input_path) as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    
    print(f"Loaded {len(records)} records from {input_path}")
    print(f"Output: {output_dir}/")
    print()
    
    # Extract products from all responses
    for r in records:
        r["products"] = extract_products(r["response_text"])
        r["brands"] = {p["brand"] for p in r["products"]}
        r["has_recommendation"] = has_specific_recommendation(r["response_text"])
    
    # Save all extracted products
    all_prods = []
    for r in records:
        for p in r["products"]:
            all_prods.append({
                "query_id": r["query_id"],
                "category": r["category"],
                "engine": r["engine"],
                "rep": r["rep"],
                "brand": p["brand"],
                "product": p["product"],
                "rank": p["rank"],
            })
    
    with open(output_dir / "all_products_extracted.csv", "w", newline="") as f:
        if all_prods:
            w = csv.DictWriter(f, fieldnames=all_prods[0].keys())
            w.writeheader()
            w.writerows(all_prods)
    
    print(f"Extracted {len(all_prods)} product mentions from {len(records)} responses")
    print()
    
    engines = sorted(set(r["engine"] for r in records))
    categories = sorted(set(r["category"] for r in records))
    queries = sorted(set(r["query_id"] for r in records))
    
    # ────────────────────────────────────────────────────────────
    # RQ0: What % of responses contain actual product recommendations?
    # ────────────────────────────────────────────────────────────
    print("=" * 60)
    print("RQ0: Do AI engines actually recommend specific products?")
    print("=" * 60)
    
    rq0_data = []
    for engine in engines:
        engine_records = [r for r in records if r["engine"] == engine]
        has_rec = sum(1 for r in engine_records if r["has_recommendation"])
        total = len(engine_records)
        rate = has_rec / total * 100 if total > 0 else 0
        rq0_data.append({"engine": engine, "has_recommendation": has_rec, "total": total, "rate_pct": round(rate, 1)})
        print(f"  {engine:12s}: {rate:5.1f}% ({has_rec}/{total})")
    
    # By category
    print()
    for cat in categories:
        cat_records = [r for r in records if r["category"] == cat]
        has_rec = sum(1 for r in cat_records if r["has_recommendation"])
        total = len(cat_records)
        rate = has_rec / total * 100 if total > 0 else 0
        print(f"  {cat:15s}: {rate:5.1f}% ({has_rec}/{total})")
    
    with open(output_dir / "rq0_response_rate.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rq0_data[0].keys())
        w.writeheader()
        w.writerows(rq0_data)
    
    overall_rate = sum(1 for r in records if r["has_recommendation"]) / len(records) * 100
    print(f"\n  OVERALL: {overall_rate:.1f}%")
    print()
    
    # ────────────────────────────────────────────────────────────
    # RQ1: Cross-engine consensus
    # ────────────────────────────────────────────────────────────
    print("=" * 60)
    print("RQ1: How much do engines agree on recommendations?")
    print("=" * 60)
    
    # For each query, collect the set of brands recommended by each engine (across all reps)
    # Then compute pairwise Jaccard similarity
    
    pairwise_jaccards = defaultdict(list)
    
    for qid in queries:
        engine_brands = {}
        for engine in engines:
            brands = set()
            for r in records:
                if r["query_id"] == qid and r["engine"] == engine:
                    brands.update(r["brands"])
            engine_brands[engine] = brands
        
        for e1, e2 in combinations(engines, 2):
            j = jaccard(engine_brands[e1], engine_brands[e2])
            pairwise_jaccards[(e1, e2)].append(j)
    
    rq1_data = []
    print(f"\n  Pairwise Jaccard Similarity (averaged across {len(queries)} queries):")
    print(f"  {'':15s}", end="")
    for e in engines:
        print(f"{e:>12s}", end="")
    print()
    
    for e1 in engines:
        print(f"  {e1:15s}", end="")
        for e2 in engines:
            if e1 == e2:
                print(f"{'1.00':>12s}", end="")
            else:
                key = (min(e1, e2), max(e1, e2))
                avg_j = sum(pairwise_jaccards[key]) / len(pairwise_jaccards[key]) if pairwise_jaccards[key] else 0
                print(f"{avg_j:>12.2f}", end="")
                if e1 < e2:
                    rq1_data.append({"engine_1": e1, "engine_2": e2, "jaccard_mean": round(avg_j, 4)})
        print()
    
    overall_jaccard = sum(
        sum(v) / len(v) for v in pairwise_jaccards.values()
    ) / len(pairwise_jaccards) if pairwise_jaccards else 0
    print(f"\n  OVERALL MEAN JACCARD: {overall_jaccard:.3f}")
    print(f"  (0 = complete disagreement, 1 = perfect agreement)")
    print()
    
    with open(output_dir / "rq1_consensus.csv", "w", newline="") as f:
        if rq1_data:
            w = csv.DictWriter(f, fieldnames=rq1_data[0].keys())
            w.writeheader()
            w.writerows(rq1_data)
    
    # ────────────────────────────────────────────────────────────
    # RQ2: Brand bias
    # ────────────────────────────────────────────────────────────
    print("=" * 60)
    print("RQ2: Which brands do AI engines favor?")
    print("=" * 60)
    
    # Count brand mentions per engine and overall
    brand_counts_by_engine = defaultdict(Counter)
    brand_counts_overall = Counter()
    brand_counts_by_category = defaultdict(Counter)
    
    for r in records:
        for p in r["products"]:
            brand_counts_by_engine[r["engine"]][p["brand"]] += 1
            brand_counts_overall[p["brand"]] += 1
            brand_counts_by_category[r["category"]][p["brand"]] += 1
    
    # Top brands overall
    print("\n  Top 20 most recommended brands (across all engines):")
    rq2_data = []
    for brand, count in brand_counts_overall.most_common(20):
        # Which engines mention it?
        engine_mentions = {e: brand_counts_by_engine[e].get(brand, 0) for e in engines}
        engine_str = ", ".join(f"{e}:{c}" for e, c in sorted(engine_mentions.items()) if c > 0)
        n_engines = sum(1 for c in engine_mentions.values() if c > 0)
        consensus = n_engines / len(engines) * 100
        print(f"  {brand:25s}: {count:4d} mentions, {n_engines}/{len(engines)} engines ({consensus:.0f}%) — {engine_str}")
        rq2_data.append({
            "brand": brand,
            "total_mentions": count,
            "engines_mentioning": n_engines,
            "consensus_pct": round(consensus, 1),
            **{f"mentions_{e}": engine_mentions.get(e, 0) for e in engines},
        })
    
    # Top brands per category
    for cat in categories:
        print(f"\n  Top 10 in {cat}:")
        for brand, count in brand_counts_by_category[cat].most_common(10):
            print(f"    {brand:25s}: {count:4d} mentions")
    
    with open(output_dir / "rq2_brand_bias.csv", "w", newline="") as f:
        if rq2_data:
            w = csv.DictWriter(f, fieldnames=rq2_data[0].keys())
            w.writeheader()
            w.writerows(rq2_data)
    
    # Save full brand counts
    raw_brand_data = []
    for brand, count in brand_counts_overall.most_common():
        raw_brand_data.append({"brand": brand, "total_mentions": count})
    with open(output_dir / "raw_brand_counts.csv", "w", newline="") as f:
        if raw_brand_data:
            w = csv.DictWriter(f, fieldnames=raw_brand_data[0].keys())
            w.writeheader()
            w.writerows(raw_brand_data)
    
    print()
    
    # ────────────────────────────────────────────────────────────
    # RQ3: Self-consistency
    # ────────────────────────────────────────────────────────────
    print("=" * 60)
    print("RQ3: How consistent is the same engine across repetitions?")
    print("=" * 60)
    
    rq3_data = []
    for engine in engines:
        consistencies = []
        for qid in queries:
            # Get all brands recommended across reps for this query+engine
            reps_brands = []
            for r in records:
                if r["query_id"] == qid and r["engine"] == engine:
                    reps_brands.append(r["brands"])
            
            if len(reps_brands) < 2:
                continue
            
            # Pairwise Jaccard between reps
            rep_jaccards = []
            for i in range(len(reps_brands)):
                for j in range(i + 1, len(reps_brands)):
                    rep_jaccards.append(jaccard(reps_brands[i], reps_brands[j]))
            
            if rep_jaccards:
                consistencies.append(sum(rep_jaccards) / len(rep_jaccards))
        
        avg_consistency = sum(consistencies) / len(consistencies) if consistencies else 0
        rq3_data.append({"engine": engine, "self_consistency": round(avg_consistency, 4)})
        print(f"  {engine:12s}: {avg_consistency:.3f}")
    
    print(f"\n  (1.0 = always recommends the same products, 0.0 = completely random)")
    print()
    
    with open(output_dir / "rq3_self_consistency.csv", "w", newline="") as f:
        if rq3_data:
            w = csv.DictWriter(f, fieldnames=rq3_data[0].keys())
            w.writeheader()
            w.writerows(rq3_data)
    
    # ────────────────────────────────────────────────────────────
    # RQ4: AgentShelf Score
    # ────────────────────────────────────────────────────────────
    print("=" * 60)
    print("RQ4: AgentShelf Score — Product Reliability Rating")
    print("=" * 60)
    
    # For each (query, brand), compute:
    # - cross_engine_consensus: fraction of engines that recommended this brand
    # - self_consistency: average within-engine consistency for this brand
    # - source_citation_rate: fraction of responses mentioning this brand that had citations
    
    rq4_data = []
    
    for qid in queries:
        query_records = [r for r in records if r["query_id"] == qid]
        all_brands_in_query = set()
        for r in query_records:
            all_brands_in_query.update(r["brands"])
        
        category = query_records[0]["category"] if query_records else ""
        query_text = query_records[0]["query_text"] if query_records else ""
        
        for brand in all_brands_in_query:
            # Cross-engine consensus
            engines_recommending = set()
            for engine in engines:
                engine_recs = [r for r in query_records if r["engine"] == engine]
                if any(brand in r["brands"] for r in engine_recs):
                    engines_recommending.add(engine)
            cross_engine = len(engines_recommending) / len(engines)
            
            # Self-consistency (how often does each engine that mentions this brand, mention it across reps?)
            consistency_scores = []
            for engine in engines_recommending:
                engine_reps = [r for r in query_records if r["engine"] == engine]
                if engine_reps:
                    mention_rate = sum(1 for r in engine_reps if brand in r["brands"]) / len(engine_reps)
                    consistency_scores.append(mention_rate)
            self_consistency = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0
            
            # Citation rate
            brand_responses = [r for r in query_records if brand in r["brands"]]
            if brand_responses:
                citation_rate = sum(1 for r in brand_responses if r["citation_count"] > 0) / len(brand_responses)
            else:
                citation_rate = 0
            
            # AgentShelf Score (initial weights: 0.5 consensus + 0.3 consistency + 0.2 citation)
            score = (cross_engine * 0.5 + self_consistency * 0.3 + citation_rate * 0.2) * 100
            
            rq4_data.append({
                "query_id": qid,
                "category": category,
                "query_text": query_text[:80],
                "brand": brand,
                "cross_engine_consensus": round(cross_engine, 3),
                "engines_recommending": ",".join(sorted(engines_recommending)),
                "n_engines": len(engines_recommending),
                "self_consistency": round(self_consistency, 3),
                "citation_rate": round(citation_rate, 3),
                "agentshelf_score": round(score, 1),
            })
    
    # Sort by score descending
    rq4_data.sort(key=lambda x: x["agentshelf_score"], reverse=True)
    
    # Print top scored products
    print("\n  Top 20 highest-scored products:")
    for i, d in enumerate(rq4_data[:20]):
        print(f"  {i+1:3d}. Score {d['agentshelf_score']:5.1f} | {d['brand']:20s} | {d['n_engines']}/{len(engines)} engines | consistency {d['self_consistency']:.2f} | {d['category']} | {d['query_text'][:40]}...")
    
    print(f"\n  Lowest 10 scored products:")
    for d in rq4_data[-10:]:
        print(f"       Score {d['agentshelf_score']:5.1f} | {d['brand']:20s} | {d['n_engines']}/{len(engines)} engines | consistency {d['self_consistency']:.2f} | {d['category']}")
    
    # Score distribution
    score_buckets = {"high (80-100)": 0, "moderate (50-79)": 0, "low (0-49)": 0}
    for d in rq4_data:
        s = d["agentshelf_score"]
        if s >= 80:
            score_buckets["high (80-100)"] += 1
        elif s >= 50:
            score_buckets["moderate (50-79)"] += 1
        else:
            score_buckets["low (0-49)"] += 1
    
    print(f"\n  Score distribution ({len(rq4_data)} total product-query pairs):")
    for bucket, count in score_buckets.items():
        pct = count / len(rq4_data) * 100 if rq4_data else 0
        bar = "█" * int(pct / 2)
        print(f"    {bucket:20s}: {count:4d} ({pct:5.1f}%) {bar}")
    
    with open(output_dir / "rq4_agentshelf_scores.csv", "w", newline="") as f:
        if rq4_data:
            w = csv.DictWriter(f, fieldnames=rq4_data[0].keys())
            w.writeheader()
            w.writerows(rq4_data)
    
    print()
    
    # ────────────────────────────────────────────────────────────
    # Summary
    # ────────────────────────────────────────────────────────────
    print("=" * 60)
    print("KEY FINDINGS SUMMARY")
    print("=" * 60)
    
    findings = []
    
    f1 = f"RQ0: {overall_rate:.1f}% of AI shopping responses contain specific product recommendations."
    findings.append(f1)
    print(f"\n  {f1}")
    
    f2 = f"RQ1: Average cross-engine agreement (Jaccard) is {overall_jaccard:.3f} — engines agree on only {overall_jaccard*100:.0f}% of their recommendations."
    findings.append(f2)
    print(f"  {f2}")
    
    # Most and least consistent engines
    most_consistent = max(rq3_data, key=lambda x: x["self_consistency"])
    least_consistent = min(rq3_data, key=lambda x: x["self_consistency"])
    f3 = f"RQ3: Most self-consistent engine: {most_consistent['engine']} ({most_consistent['self_consistency']:.3f}). Least: {least_consistent['engine']} ({least_consistent['self_consistency']:.3f})."
    findings.append(f3)
    print(f"  {f3}")
    
    # Brand concentration
    top3_brands = brand_counts_overall.most_common(3)
    total_mentions = sum(brand_counts_overall.values())
    top3_share = sum(c for _, c in top3_brands) / total_mentions * 100 if total_mentions else 0
    top3_names = ", ".join(b for b, _ in top3_brands)
    f4 = f"RQ2: Top 3 brands ({top3_names}) account for {top3_share:.1f}% of all recommendations."
    findings.append(f4)
    print(f"  {f4}")
    
    # Score distribution
    high_pct = score_buckets["high (80-100)"] / len(rq4_data) * 100 if rq4_data else 0
    low_pct = score_buckets["low (0-49)"] / len(rq4_data) * 100 if rq4_data else 0
    f5 = f"RQ4: Only {high_pct:.1f}% of product recommendations score 'high confidence' (80+). {low_pct:.1f}% score 'low confidence' (<50)."
    findings.append(f5)
    print(f"  {f5}")
    
    print()
    print("=" * 60)
    print(f"All results saved to: {output_dir}/")
    print("=" * 60)
    
    # Save summary
    with open(output_dir / "summary.txt", "w") as f:
        f.write("AgentShelf Score Experiment — Key Findings\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Data: {len(records)} API responses\n")
        f.write(f"Engines: {', '.join(engines)}\n")
        f.write(f"Categories: {', '.join(categories)}\n")
        f.write(f"Queries: {len(queries)}\n")
        f.write(f"Products extracted: {len(all_prods)} mentions\n\n")
        for finding in findings:
            f.write(f"• {finding}\n\n")


# ── Entry Point ───────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Try to find most recent experiment file
        results_dir = Path("results")
        if results_dir.exists():
            files = sorted(results_dir.glob("experiment_*.jsonl"))
            if files:
                print(f"Using most recent: {files[-1]}")
                analyze(str(files[-1]))
            else:
                print("No experiment files found in results/")
                print("Usage: python analyze_results.py results/experiment_XXXXXXXX_XXXXXX.jsonl")
        else:
            print("No results/ directory found.")
            print("Usage: python analyze_results.py results/experiment_XXXXXXXX_XXXXXX.jsonl")
    else:
        analyze(sys.argv[1])
