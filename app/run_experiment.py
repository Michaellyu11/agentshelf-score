"""
AgentShelf Score Experiment: Cross-Engine AI Shopping Recommendation Consistency
================================================================================
Sends the same shopping queries to 5 AI engines, records what they recommend,
and measures how much they agree or disagree.

Usage:
  1. Copy this file into your agentshelf/app/ directory (next to core/)
  2. Make sure your .env has all 5 API keys set
  3. Run: cd agentshelf && python -m app.run_experiment
  
  Or run standalone: python run_experiment.py (after adjusting imports)

Output: results/experiment_YYYYMMDD_HHMMSS.jsonl  (one JSON object per response)
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent to path so we can import from app.core
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.api_client import (
    anthropic_request, deepseek_request, gemini_request,
    perplexity_request, openai_request,
    extract_text, extract_text_deepseek, extract_text_gemini,
    extract_text_perplexity, extract_text_openai,
    extract_citations_gemini, extract_citations_perplexity,
    extract_citations_openai,
)

# ── Configuration ─────────────────────────────────────────────────

REPS_PER_QUERY = 10          # repetitions per (query, engine) pair
DELAY_BETWEEN_CALLS = 3.0    # seconds between API calls (avoid rate limits)
DELAY_BETWEEN_REPS = 1.0     # seconds between reps of same query
OUTPUT_DIR = Path("results")

# ── Query Bank ────────────────────────────────────────────────────
# 15 queries × 4 categories = 60 total
# Each query varies: price range, use case, user persona, specificity

QUERIES = {
    "earbuds": [
        # Budget
        {"id": "earbuds_01", "query": "What are the best wireless earbuds under $50?"},
        {"id": "earbuds_02", "query": "Recommend cheap wireless earbuds for a college student on a tight budget"},
        {"id": "earbuds_03", "query": "Best budget earbuds for daily commuting under $40"},
        # Mid-range
        {"id": "earbuds_04", "query": "Recommend the best wireless noise-cancelling earbuds under $100"},
        {"id": "earbuds_05", "query": "I work in a noisy office and need good ANC earbuds around $80. What do you suggest?"},
        {"id": "earbuds_06", "query": "What wireless earbuds have the best sound quality between $60 and $100?"},
        {"id": "earbuds_07", "query": "Best earbuds for working out and running, water resistant, under $80"},
        # Premium
        {"id": "earbuds_08", "query": "What are the best premium wireless earbuds money can buy in 2026?"},
        {"id": "earbuds_09", "query": "Recommend high-end noise cancelling earbuds for frequent flyers, budget $150-250"},
        {"id": "earbuds_10", "query": "Best wireless earbuds for audiophiles who care about sound quality above all else"},
        # Specific personas
        {"id": "earbuds_11", "query": "I'm a parent who needs earbuds I can wear while my kids are around. Need to hear them. Suggestions?"},
        {"id": "earbuds_12", "query": "Recommend wireless earbuds for gaming with low latency"},
        # Vague
        {"id": "earbuds_13", "query": "What earbuds should I buy?"},
        {"id": "earbuds_14", "query": "Good earbuds?"},
        {"id": "earbuds_15", "query": "I need new earbuds. Help me pick."},
    ],
    "keyboards": [
        # Budget
        {"id": "kb_01", "query": "Best mechanical keyboard under $50 for a beginner"},
        {"id": "kb_02", "query": "Recommend a cheap but good mechanical keyboard for typing"},
        {"id": "kb_03", "query": "Budget mechanical keyboard for a college student who codes"},
        # Mid-range
        {"id": "kb_04", "query": "What's the best mechanical keyboard between $80 and $150?"},
        {"id": "kb_05", "query": "Recommend a wireless mechanical keyboard for office work, quiet switches preferred"},
        {"id": "kb_06", "query": "Best 75% layout mechanical keyboard for programming under $120"},
        {"id": "kb_07", "query": "I want a hot-swappable mechanical keyboard with RGB under $100"},
        # Premium
        {"id": "kb_08", "query": "What's the best premium mechanical keyboard regardless of price?"},
        {"id": "kb_09", "query": "Recommend a high-end custom mechanical keyboard for enthusiasts"},
        {"id": "kb_10", "query": "Best ergonomic split mechanical keyboard for someone with RSI"},
        # Specific personas
        {"id": "kb_11", "query": "I'm a gamer who needs a fast mechanical keyboard with linear switches. Budget $100"},
        {"id": "kb_12", "query": "Recommend a mechanical keyboard that's good for both coding and gaming"},
        # Vague
        {"id": "kb_13", "query": "What keyboard should I get?"},
        {"id": "kb_14", "query": "Good mechanical keyboard recommendation?"},
        {"id": "kb_15", "query": "Help me choose a mechanical keyboard"},
    ],
    "running_shoes": [
        # Budget
        {"id": "shoes_01", "query": "Best running shoes under $80 for beginners"},
        {"id": "shoes_02", "query": "Recommend affordable running shoes for someone just starting to jog"},
        {"id": "shoes_03", "query": "Cheap but good running shoes for casual runners under $60"},
        # Mid-range
        {"id": "shoes_04", "query": "What are the best running shoes between $100 and $150?"},
        {"id": "shoes_05", "query": "Recommend running shoes for half marathon training, cushioned, around $120"},
        {"id": "shoes_06", "query": "Best daily training shoes for runners who do 30-40 miles per week"},
        {"id": "shoes_07", "query": "Recommend stability running shoes for someone with flat feet, under $140"},
        # Premium
        {"id": "shoes_08", "query": "What are the best carbon plate racing shoes for marathon?"},
        {"id": "shoes_09", "query": "Best premium running shoes money can buy in 2026"},
        {"id": "shoes_10", "query": "Recommend top-tier trail running shoes for ultramarathon"},
        # Specific personas
        {"id": "shoes_11", "query": "I'm overweight (250 lbs) and starting to run. What shoes have enough support?"},
        {"id": "shoes_12", "query": "Best running shoes for women with wide feet"},
        # Vague
        {"id": "shoes_13", "query": "What running shoes should I buy?"},
        {"id": "shoes_14", "query": "Good running shoes?"},
        {"id": "shoes_15", "query": "Recommend me some running shoes"},
    ],
    "skincare": [
        # Budget
        {"id": "skin_01", "query": "Best daily moisturizer for oily skin under $20"},
        {"id": "skin_02", "query": "Recommend a cheap but effective face sunscreen for everyday use"},
        {"id": "skin_03", "query": "What's a good drugstore retinol product for beginners?"},
        # Mid-range
        {"id": "skin_04", "query": "Best vitamin C serum between $20 and $50"},
        {"id": "skin_05", "query": "Recommend a good anti-aging skincare routine for someone in their 30s, budget $100 total"},
        {"id": "skin_06", "query": "What's the best hyaluronic acid serum under $40?"},
        {"id": "skin_07", "query": "Best moisturizer for sensitive skin that doesn't cause breakouts, under $35"},
        # Premium
        {"id": "skin_08", "query": "What's the best luxury skincare brand for anti-aging?"},
        {"id": "skin_09", "query": "Recommend premium skincare products worth the splurge"},
        {"id": "skin_10", "query": "Best high-end retinol product regardless of price"},
        # Specific personas
        {"id": "skin_11", "query": "I'm a teenage boy with bad acne. What skincare products should I use?"},
        {"id": "skin_12", "query": "Best skincare routine for a man who has never used any products before"},
        # Vague
        {"id": "skin_13", "query": "What skincare products should I use?"},
        {"id": "skin_14", "query": "Good moisturizer recommendation?"},
        {"id": "skin_15", "query": "Help me build a skincare routine"},
    ],
}

# ── System Prompt ─────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a helpful shopping assistant. When the user asks for product recommendations, provide specific product names, brands, and approximate prices. Be concrete — name actual products, not just categories. If you recommend multiple products, rank them from most recommended to least."""

# ── Engine Runners ────────────────────────────────────────────────

async def run_query_on_engine(engine: str, query: str) -> dict:
    """Run a single query on a single engine. Returns raw response + extracted data."""
    
    result = {
        "engine": engine,
        "raw_text": "",
        "citations": [],
        "error": None,
    }
    
    try:
        if engine == "chatgpt":
            resp = await openai_request(system=SYSTEM_PROMPT, user_message=query)
            result["raw_text"] = extract_text_openai(resp)
            result["citations"] = extract_citations_openai(resp)
            
        elif engine == "gemini":
            resp = await gemini_request(system=SYSTEM_PROMPT, user_message=query, use_search=True)
            result["raw_text"] = extract_text_gemini(resp)
            result["citations"] = extract_citations_gemini(resp)
            
        elif engine == "perplexity":
            resp = await perplexity_request(system=SYSTEM_PROMPT, user_message=query)
            result["raw_text"] = extract_text_perplexity(resp)
            result["citations"] = extract_citations_perplexity(resp)
            
        elif engine == "claude":
            resp = await anthropic_request(
                system=SYSTEM_PROMPT,
                user_message=query,
                model="claude-haiku-4-5-20251001",
                max_tokens=2048,
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 3,
                }],
                timeout=60.0,
            )
            # Parse text from response blocks
            text_parts = []
            for block in resp.get("content", []):
                if block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                if block.get("type") == "web_search_tool_result":
                    for item in block.get("content", []):
                        if item.get("type") == "web_search_result":
                            url = item.get("url", "")
                            if url:
                                result["citations"].append(url)
            result["raw_text"] = "\n".join(text_parts)
            
        elif engine == "deepseek":
            resp = await deepseek_request(system=SYSTEM_PROMPT, user_message=query)
            result["raw_text"] = extract_text_deepseek(resp)
            result["citations"] = []  # DeepSeek doesn't provide citations
            
    except Exception as e:
        result["error"] = str(e)
        
    return result


# ── Main Experiment Loop ──────────────────────────────────────────

async def run_experiment():
    """Run the full cross-engine shopping experiment."""
    
    # Setup output
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"experiment_{timestamp}.jsonl"
    
    engines = ["chatgpt", "gemini", "perplexity", "claude", "deepseek"]
    
    # Flatten all queries
    all_queries = []
    for category, queries in QUERIES.items():
        for q in queries:
            all_queries.append({**q, "category": category})
    
    total_calls = len(all_queries) * len(engines) * REPS_PER_QUERY
    completed = 0
    errors = 0
    
    print(f"=" * 60)
    print(f"AgentShelf Score Experiment")
    print(f"=" * 60)
    print(f"Queries:    {len(all_queries)}")
    print(f"Engines:    {len(engines)}")
    print(f"Reps:       {REPS_PER_QUERY}")
    print(f"Total calls: {total_calls}")
    print(f"Output:     {output_file}")
    print(f"=" * 60)
    print()
    
    with open(output_file, "w") as f:
        for qi, q_data in enumerate(all_queries):
            for engine in engines:
                for rep in range(REPS_PER_QUERY):
                    # Progress
                    completed += 1
                    pct = (completed / total_calls) * 100
                    print(
                        f"[{pct:5.1f}%] {q_data['category']}/{q_data['id']} "
                        f"→ {engine} (rep {rep+1}/{REPS_PER_QUERY})",
                        end="",
                    )
                    
                    # Run query
                    result = await run_query_on_engine(engine, q_data["query"])
                    
                    # Build record
                    record = {
                        "query_id": q_data["id"],
                        "category": q_data["category"],
                        "query_text": q_data["query"],
                        "engine": engine,
                        "rep": rep + 1,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "response_text": result["raw_text"],
                        "citations": result["citations"],
                        "citation_count": len(result["citations"]),
                        "response_length": len(result["raw_text"]),
                        "has_error": result["error"] is not None,
                        "error_message": result["error"],
                    }
                    
                    # Write immediately (crash-safe)
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    f.flush()
                    
                    if result["error"]:
                        errors += 1
                        print(f"  ✗ ERROR: {result['error'][:50]}")
                    else:
                        text_preview = result["raw_text"][:60].replace("\n", " ")
                        print(f"  ✓ ({len(result['raw_text'])} chars)")
                    
                    # Rate limit delay
                    if rep < REPS_PER_QUERY - 1:
                        await asyncio.sleep(DELAY_BETWEEN_REPS)
                    else:
                        await asyncio.sleep(DELAY_BETWEEN_CALLS)
    
    # Summary
    print()
    print(f"=" * 60)
    print(f"EXPERIMENT COMPLETE")
    print(f"=" * 60)
    print(f"Total calls: {completed}")
    print(f"Errors:      {errors} ({errors/completed*100:.1f}%)")
    print(f"Output:      {output_file}")
    print(f"=" * 60)
    print()
    print("Next step: run `python analyze_results.py` to compute AgentShelf Scores")


# ── Quick Test Mode ───────────────────────────────────────────────

async def run_test():
    """Quick test: 1 query × 5 engines × 1 rep = 5 calls. ~$0.25 total."""
    
    print("=" * 60)
    print("TEST MODE: 1 query × 5 engines × 1 rep")
    print("=" * 60)
    
    test_query = "Recommend the best wireless earbuds under $100 for commuting"
    engines = ["chatgpt", "gemini", "perplexity", "claude", "deepseek"]
    
    for engine in engines:
        print(f"\n→ {engine}...")
        result = await run_query_on_engine(engine, test_query)
        
        if result["error"]:
            print(f"  ✗ ERROR: {result['error']}")
        else:
            print(f"  ✓ Response: {len(result['raw_text'])} chars, {len(result['citations'])} citations")
            # Print first 200 chars
            preview = result["raw_text"][:200].replace("\n", " ")
            print(f"  Preview: {preview}...")
        
        await asyncio.sleep(2)
    
    print("\n✓ All engines working. Ready to run full experiment.")
    print("  Run with: python run_experiment.py --full")


# ── Entry Point ───────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AgentShelf Cross-Engine Experiment")
    parser.add_argument("--full", action="store_true", help="Run full experiment (3000 calls)")
    parser.add_argument("--test", action="store_true", help="Quick test (5 calls)")
    parser.add_argument("--reps", type=int, default=REPS_PER_QUERY, help="Reps per query (default 10)")
    args = parser.parse_args()
    
    if args.reps != REPS_PER_QUERY:
        REPS_PER_QUERY = args.reps
    
    if args.full:
        asyncio.run(run_experiment())
    elif args.test:
        asyncio.run(run_test())
    else:
        print("Usage:")
        print("  python run_experiment.py --test   # Quick test (5 calls, ~$0.25)")
        print("  python run_experiment.py --full   # Full experiment (3000 calls, ~$135)")
        print("  python run_experiment.py --full --reps 5  # Half reps (1500 calls, ~$68)")
