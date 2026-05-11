"""
AgentShelf — Logistic Regression Decomposition
================================================
Decomposes AI shopping recommendation behavior into three independent factors:
  α_b = brand latent AI visibility (how "recommendable" a brand is across all engines)
  β_e = engine recommendation tendency (how generous/conservative an engine is)
  γ_t = query specificity effect (vague queries → less consistent recommendations)

Uses cluster-robust standard errors grouped by (query_id, engine, rep) to handle
within-response dependence (brands recommended together are not independent).

Usage:
  python logistic_model.py

Reads from: results/analysis_*/all_products_extracted.csv + experiment JSONL
Outputs: results/logistic_decomposition.csv + console summary
"""

import json
import csv
import sys
import warnings
from collections import defaultdict, Counter
from pathlib import Path

# Try importing statsmodels; if not available, use a simpler approach
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("WARNING: numpy not found. Install with: pip install numpy")
    sys.exit(1)

try:
    from scipy.special import expit as sigmoid
    from scipy.optimize import minimize
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("WARNING: scipy not found. Install with: pip install scipy")
    sys.exit(1)

# ── Configuration ──────────────────────────────────────────

MIN_BRAND_MENTIONS = 15  # Brands below this threshold are merged into "other"

# Query specificity tiers (based on query design)
SPECIFIC_QUERIES = {
    # Tier 1: Specific (price + use case + persona)
    "earbuds_03", "earbuds_04", "earbuds_05", "earbuds_06", "earbuds_07",
    "earbuds_09", "earbuds_11", "earbuds_12",
    "kb_03", "kb_05", "kb_06", "kb_07", "kb_10", "kb_11",
    "shoes_02", "shoes_05", "shoes_06", "shoes_07", "shoes_11", "shoes_12",
    "skin_01", "skin_02", "skin_04", "skin_05", "skin_06", "skin_07", "skin_11", "skin_12",
}

VAGUE_QUERIES = {
    # Tier 3: Vague (no constraints)
    "earbuds_13", "earbuds_14", "earbuds_15",
    "kb_13", "kb_14", "kb_15",
    "shoes_13", "shoes_14", "shoes_15",
    "skin_13", "skin_14", "skin_15",
}

# Everything else is Tier 2: Moderate

def get_query_tier(query_id):
    if query_id in SPECIFIC_QUERIES:
        return "specific"
    elif query_id in VAGUE_QUERIES:
        return "vague"
    else:
        return "moderate"


def run_analysis():
    # ── Load data ──────────────────────────────────────────
    results_dir = Path("results")
    
    # Find the experiment JSONL
    jsonl_files = sorted(results_dir.glob("experiment_*.jsonl"))
    if not jsonl_files:
        print("ERROR: No experiment JSONL found in results/")
        sys.exit(1)
    
    jsonl_path = jsonl_files[-1]
    print(f"Loading: {jsonl_path}")
    
    # Find the analysis directory
    analysis_dirs = sorted(results_dir.glob("analysis_*"))
    if not analysis_dirs:
        print("ERROR: No analysis directory found. Run analyze_results.py first.")
        sys.exit(1)
    
    analysis_dir = analysis_dirs[-1]
    products_csv = analysis_dir / "all_products_extracted.csv"
    
    if not products_csv.exists():
        print(f"ERROR: {products_csv} not found. Run analyze_results.py first.")
        sys.exit(1)
    
    # Load extracted products
    products = []
    with open(products_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append(row)
    
    print(f"Loaded {len(products)} product mentions")
    
    # ── Identify brands to model ──────────────────────────
    brand_counts = Counter(p["brand"] for p in products)
    modeled_brands = {b for b, c in brand_counts.items() if c >= MIN_BRAND_MENTIONS}
    
    print(f"\nBrands with >= {MIN_BRAND_MENTIONS} mentions: {len(modeled_brands)}")
    for b in sorted(modeled_brands):
        print(f"  {b}: {brand_counts[b]}")
    
    # ── Build binary matrix ────────────────────────────────
    # For each (query_id, engine, rep), determine which modeled brands were recommended
    
    # First, get all unique (query_id, engine, rep) combinations from the JSONL
    responses = []
    with open(jsonl_path) as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                if not r.get("has_error"):
                    responses.append(r)
    
    print(f"Loaded {len(responses)} responses from JSONL")
    
    # Build a lookup: (query_id, engine, rep) -> set of brands recommended
    rec_lookup = defaultdict(set)
    for p in products:
        key = (p["query_id"], p["engine"], int(p["rep"]))
        if p["brand"] in modeled_brands:
            rec_lookup[key].add(p["brand"])
        # else: brand is merged into "other" (not modeled individually)
    
    # Get unique engines and query_ids
    engines = sorted(set(r["engine"] for r in responses))
    query_ids = sorted(set(r["query_id"] for r in responses))
    brand_list = sorted(modeled_brands)
    
    print(f"\nDesign matrix dimensions:")
    print(f"  Responses: {len(responses)}")
    print(f"  Modeled brands: {len(brand_list)}")
    print(f"  Engines: {len(engines)}")
    print(f"  Observations (responses x brands): {len(responses) * len(brand_list)}")
    
    # ── Build design matrix X and response vector y ────────
    # Each row: one (response, brand) pair
    # y = 1 if brand was recommended in that response, 0 otherwise
    # X columns: [brand dummies | engine dummies | tier dummies]
    
    # Reference categories (absorbed into intercept):
    #   brand: first alphabetically
    #   engine: first alphabetically  
    #   tier: "moderate" (middle category)
    
    ref_brand = brand_list[0]
    ref_engine = engines[0]
    ref_tier = "moderate"
    
    n_brand_params = len(brand_list) - 1  # exclude reference
    n_engine_params = len(engines) - 1
    n_tier_params = 2  # specific and vague (moderate is reference)
    n_params = 1 + n_brand_params + n_engine_params + n_tier_params  # +1 for intercept
    
    print(f"\nModel parameters: {n_params}")
    print(f"  Intercept: 1")
    print(f"  Brand effects (α): {n_brand_params} (reference: {ref_brand})")
    print(f"  Engine effects (β): {n_engine_params} (reference: {ref_engine})")
    print(f"  Tier effects (γ): {n_tier_params} (reference: {ref_tier})")
    
    # Build arrays
    rows = []
    cluster_ids = []  # for cluster-robust SEs
    
    for resp in responses:
        qid = resp["query_id"]
        eng = resp["engine"]
        rep = resp["rep"]
        tier = get_query_tier(qid)
        key = (qid, eng, rep)
        recommended_brands = rec_lookup[key]
        cluster_id = f"{qid}_{eng}_{rep}"
        
        for brand in brand_list:
            y_val = 1 if brand in recommended_brands else 0
            
            # Build feature vector
            x = np.zeros(n_params)
            x[0] = 1.0  # intercept
            
            # Brand dummy
            if brand != ref_brand:
                idx = 1 + brand_list.index(brand) - (1 if brand_list.index(brand) > brand_list.index(ref_brand) else 0)
                # Simpler: just map non-reference brands to positions 1..n_brand_params
                non_ref_brands = [b for b in brand_list if b != ref_brand]
                idx = 1 + non_ref_brands.index(brand)
                x[idx] = 1.0
            
            # Engine dummy
            if eng != ref_engine:
                non_ref_engines = [e for e in engines if e != ref_engine]
                idx = 1 + n_brand_params + non_ref_engines.index(eng)
                x[idx] = 1.0
            
            # Tier dummy
            if tier == "specific":
                x[1 + n_brand_params + n_engine_params] = 1.0
            elif tier == "vague":
                x[1 + n_brand_params + n_engine_params + 1] = 1.0
            
            rows.append((x, y_val))
            cluster_ids.append(cluster_id)
    
    X = np.array([r[0] for r in rows])
    y = np.array([r[1] for r in rows])
    
    print(f"\nFinal dataset: {X.shape[0]} observations, {X.shape[1]} features")
    print(f"  Positive (recommended): {y.sum()} ({y.mean()*100:.1f}%)")
    print(f"  Negative (not recommended): {(1-y).sum()} ({(1-y.mean())*100:.1f}%)")
    print(f"  Clusters: {len(set(cluster_ids))}")
    
    # ── Fit logistic regression ────────────────────────────
    print(f"\nFitting logistic regression...")
    
    # Use scipy minimize with L-BFGS-B
    def neg_log_likelihood(beta):
        z = X @ beta
        # Clip for numerical stability
        z = np.clip(z, -30, 30)
        ll = y * z - np.log(1 + np.exp(z))
        return -ll.sum()
    
    def neg_log_likelihood_grad(beta):
        z = X @ beta
        z = np.clip(z, -30, 30)
        p = sigmoid(z)
        grad = -X.T @ (y - p)
        return grad
    
    # Initial guess: all zeros
    beta0 = np.zeros(n_params)
    
    result = minimize(neg_log_likelihood, beta0, jac=neg_log_likelihood_grad,
                      method='L-BFGS-B', options={'maxiter': 1000, 'ftol': 1e-10})
    
    if not result.success:
        print(f"WARNING: Optimization did not converge: {result.message}")
    else:
        print(f"Converged in {result.nit} iterations")
    
    beta = result.x
    
    # ── Compute cluster-robust standard errors ─────────────
    print("Computing cluster-robust standard errors...")
    
    z = X @ beta
    z = np.clip(z, -30, 30)
    p_hat = sigmoid(z)
    residuals = y - p_hat
    
    # Meat matrix: sum of outer products of score vectors within clusters
    unique_clusters = sorted(set(cluster_ids))
    cluster_array = np.array(cluster_ids)
    
    # Score for each observation: (y_i - p_i) * x_i
    scores = (residuals[:, None] * X)  # N x K
    
    # Bread: inverse of Hessian (Fisher information)
    W = p_hat * (1 - p_hat)
    bread = np.linalg.inv(X.T @ (W[:, None] * X))
    
    # Meat: cluster-summed outer products
    meat = np.zeros((n_params, n_params))
    for cl in unique_clusters:
        mask = cluster_array == cl
        s_cl = scores[mask].sum(axis=0, keepdims=True)  # 1 x K
        meat += s_cl.T @ s_cl
    
    # Sandwich estimator
    V_robust = bread @ meat @ bread
    se_robust = np.sqrt(np.diag(V_robust))
    
    # ── Extract and display results ────────────────────────
    print("\n" + "=" * 70)
    print("LOGISTIC REGRESSION RESULTS")
    print("=" * 70)
    
    non_ref_brands = [b for b in brand_list if b != ref_brand]
    non_ref_engines = [e for e in engines if e != ref_engine]
    
    param_names = ["intercept"]
    param_names += [f"α_{b}" for b in non_ref_brands]
    param_names += [f"β_{e}" for e in non_ref_engines]
    param_names += ["γ_specific", "γ_vague"]
    
    print(f"\n{'Parameter':<25s} {'Coef':>8s} {'SE(robust)':>12s} {'z':>8s} {'p-value':>10s}")
    print("-" * 70)
    
    results_data = []
    for i, name in enumerate(param_names):
        coef = beta[i]
        se = se_robust[i]
        z_val = coef / se if se > 0 else 0
        # Two-tailed p-value (approximate)
        from scipy.stats import norm
        p_val = 2 * (1 - norm.cdf(abs(z_val)))
        
        sig = ""
        if p_val < 0.001:
            sig = "***"
        elif p_val < 0.01:
            sig = "**"
        elif p_val < 0.05:
            sig = "*"
        
        print(f"{name:<25s} {coef:>8.3f} {se:>12.4f} {z_val:>8.2f} {p_val:>10.4f} {sig}")
        
        results_data.append({
            "parameter": name,
            "coefficient": round(coef, 4),
            "se_robust": round(se, 4),
            "z_value": round(z_val, 2),
            "p_value": round(p_val, 4),
        })
    
    # ── Brand effects ranking (α) ──────────────────────────
    print("\n" + "=" * 70)
    print("BRAND LATENT AI VISIBILITY RANKING (α)")
    print("=" * 70)
    print(f"(Reference brand: {ref_brand}, α=0)")
    
    brand_effects = {ref_brand: 0.0}
    for i, b in enumerate(non_ref_brands):
        brand_effects[b] = beta[1 + i]
    
    sorted_brands = sorted(brand_effects.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n{'Rank':<6s} {'Brand':<25s} {'α (visibility)':>15s} {'Mentions':>10s}")
    print("-" * 60)
    for rank, (brand, alpha) in enumerate(sorted_brands, 1):
        mentions = brand_counts.get(brand, 0)
        print(f"{rank:<6d} {brand:<25s} {alpha:>15.3f} {mentions:>10d}")
    
    # ── Engine effects (β) ─────────────────────────────────
    print("\n" + "=" * 70)
    print("ENGINE RECOMMENDATION TENDENCY (β)")
    print("=" * 70)
    print(f"(Reference engine: {ref_engine}, β=0)")
    print(f"(Positive β = more generous recommender, Negative β = more conservative)")
    
    engine_effects = {ref_engine: 0.0}
    for i, e in enumerate(non_ref_engines):
        engine_effects[e] = beta[1 + n_brand_params + i]
    
    sorted_engines = sorted(engine_effects.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n{'Engine':<15s} {'β (tendency)':>15s} {'Interpretation'}")
    print("-" * 60)
    for eng, b_val in sorted_engines:
        interp = "most generous" if b_val == max(engine_effects.values()) else \
                 "most conservative" if b_val == min(engine_effects.values()) else ""
        print(f"{eng:<15s} {b_val:>15.3f} {interp}")
    
    # ── Query tier effects (γ) ─────────────────────────────
    print("\n" + "=" * 70)
    print("QUERY SPECIFICITY EFFECT (γ)")
    print("=" * 70)
    print(f"(Reference: moderate queries, γ=0)")
    
    gamma_specific = beta[1 + n_brand_params + n_engine_params]
    gamma_vague = beta[1 + n_brand_params + n_engine_params + 1]
    
    print(f"\n  Specific queries: γ = {gamma_specific:.3f}")
    print(f"  Moderate queries: γ = 0.000 (reference)")
    print(f"  Vague queries:    γ = {gamma_vague:.3f}")
    
    if gamma_vague < gamma_specific:
        print(f"\n  → Vague queries reduce recommendation probability relative to specific queries")
        print(f"    (difference: {gamma_vague - gamma_specific:.3f})")
    
    # ── Correlation with AgentShelf Score ───────────────────
    print("\n" + "=" * 70)
    print("VALIDATION: α vs AgentShelf Score correlation")
    print("=" * 70)
    
    # Load AgentShelf scores and compute mean score per brand
    scores_csv = analysis_dir / "rq4_agentshelf_scores.csv"
    if scores_csv.exists():
        brand_scores = defaultdict(list)
        with open(scores_csv) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["brand"] in modeled_brands:
                    brand_scores[row["brand"]].append(float(row["agentshelf_score"]))
        
        # Compute mean score per brand
        mean_scores = {b: np.mean(s) for b, s in brand_scores.items() if s}
        
        # Compute Spearman correlation between α and mean AgentShelf Score
        common_brands = sorted(set(brand_effects.keys()) & set(mean_scores.keys()))
        if len(common_brands) >= 5:
            alphas = np.array([brand_effects[b] for b in common_brands])
            scores_arr = np.array([mean_scores[b] for b in common_brands])
            
            # Spearman correlation (rank-based)
            from scipy.stats import spearmanr
            rho, p_val = spearmanr(alphas, scores_arr)
            
            print(f"\n  Brands compared: {len(common_brands)}")
            print(f"  Spearman ρ (α vs AgentShelf Score): {rho:.3f}")
            print(f"  p-value: {p_val:.4f}")
            
            if rho > 0.6:
                print(f"  → STRONG correlation: logistic model validates AgentShelf Score")
            elif rho > 0.3:
                print(f"  → MODERATE correlation: partial alignment between model and Score")
            else:
                print(f"  → WEAK correlation: model and Score capture different aspects")
            
            print(f"\n  Per-brand comparison:")
            print(f"  {'Brand':<25s} {'α':>8s} {'Score':>8s}")
            print(f"  {'-'*45}")
            for b in sorted(common_brands, key=lambda x: brand_effects[x], reverse=True):
                print(f"  {b:<25s} {brand_effects[b]:>8.3f} {mean_scores[b]:>8.1f}")
    else:
        print("  AgentShelf scores CSV not found. Skipping validation.")
    
    # ── Save results ───────────────────────────────────────
    output_path = results_dir / "logistic_decomposition.csv"
    with open(output_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results_data[0].keys())
        w.writeheader()
        w.writerows(results_data)
    
    print(f"\nResults saved to: {output_path}")
    print("\n" + "=" * 70)
    print("SUMMARY FOR PAPER")
    print("=" * 70)
    print(f"""
A logistic regression model decomposing recommendation probability into 
brand visibility (α), engine tendency (β), and query specificity (γ) 
factors was fitted to {X.shape[0]:,} binary observations across {len(brand_list)} brands, 
{len(engines)} engines, and 3 query specificity tiers.

Key findings:
- Brand effects (α) span {max(brand_effects.values()):.2f} to {min(brand_effects.values()):.2f}, 
  confirming large differences in latent AI visibility across brands.
- Engine effects (β) show {ref_engine} as the reference; deviations reveal 
  systematic differences in recommendation generosity.
- Query specificity (γ): specific={gamma_specific:.3f}, vague={gamma_vague:.3f}, 
  {"confirming" if gamma_vague < gamma_specific else "not confirming"} that vague 
  queries receive fewer specific brand recommendations.
- Cluster-robust standard errors (clustered by response) account for 
  within-response dependence among recommended brands.
""")


if __name__ == "__main__":
    run_analysis()
