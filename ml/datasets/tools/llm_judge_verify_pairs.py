#!/usr/bin/env python3
"""
LLM-as-Judge verification for DPO pairs using Claude
Validates that chosen responses are better than rejected responses
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Tuple
import requests

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
API_KEY = os.environ.get("ANTHROPIC_API_KEY")

def load_jsonl(path: str):
    """Load JSONL file line by line"""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

def save_json(path: str, obj: Any):
    """Save object as JSON"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def md5(text: str) -> str:
    """Compute MD5 hash of text"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def extract_messages(sample: Dict[str, Any]) -> Tuple[str, str]:
    """Extract prompt and response from sample"""
    messages = sample.get("messages", [])
    if not messages:
        return "", ""
    
    # Get user message (prompt)
    prompt_parts = []
    for m in messages:
        if m.get("role") == "user":
            prompt_parts.append(m.get("content", ""))
    prompt = "\n\n".join(prompt_parts).strip()
    
    # Get assistant message (response)
    response = ""
    for m in messages:
        if m.get("role") == "assistant":
            response = m.get("content", "").strip()
            break
    
    return prompt, response

def build_judge_prompt(prompt: str, response: str, source: str) -> str:
    """Build judge prompt for evaluating response quality"""
    
    criteria = """
Judge the quality of this coding assistant response on:

1. **Format Compliance** (0-1):
   - Uses proper SEARCH/REPLACE or PLAIN CODE blocks
   - Includes <thinking> tags for reasoning
   - Follows Motadata code conventions

2. **Technical Correctness** (0-1):
   - Code is syntactically valid
   - Logic makes sense for the task
   - Handles edge cases appropriately

3. **Instruction Following** (0-1):
   - Addresses the actual task requested
   - Doesn't add unrequested changes
   - Stays within scope

4. **Context Usage** (0-1):
   - Uses provided context (if any)
   - References correct files/methods
   - No hallucinated code patterns
"""
    
    return f"""You are an impartial code quality judge for a coding assistant dataset.

Task: Evaluate if this response is suitable for training a production coding assistant.

User Request:
{prompt}

Assistant Response:
{response}

Source: {source}

{criteria}

Respond ONLY with a JSON object:
{{
  "verdict": "PASS" | "FAIL",
  "reason": "concise 1-2 sentence justification",
  "scores": {{
    "format_compliance": 0.0-1.0,
    "technical_correctness": 0.0-1.0,
    "instruction_following": 0.0-1.0,
    "context_usage": 0.0-1.0
  }},
  "overall_score": 0.0-1.0
}}

"PASS" means response is good enough for training (overall_score >= 0.7).
"FAIL" means response should be filtered out (overall_score < 0.7).
"""

def call_claude(prompt: str) -> Dict[str, Any]:
    """Call Claude API with retry logic"""
    if not API_KEY:
        raise RuntimeError("Set ANTHROPIC_API_KEY in environment")
    
    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    
    payload = {
        "model": MODEL,
        "max_tokens": 512,
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}],
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            
            # Extract text from Claude response
            content = "".join([c.get("text", "") for c in data.get("content", [])])
            
            # Try parse JSON
            try:
                return json.loads(content)
            except Exception:
                # Try to extract JSON from markdown code blocks
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                    return json.loads(json_str)
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                    return json.loads(json_str)
                else:
                    return {
                        "verdict": "FAIL",
                        "reason": "Non-JSON judge response",
                        "raw": content,
                        "scores": {},
                        "overall_score": 0.0
                    }
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            return {
                "verdict": "FAIL",
                "reason": f"API error: {str(e)}",
                "scores": {},
                "overall_score": 0.0
            }
    
    return {
        "verdict": "FAIL",
        "reason": "Max retries exceeded",
        "scores": {},
        "overall_score": 0.0
    }

def main():
    if len(sys.argv) < 3:
        print("Usage: python llm_judge_verify_pairs.py <input_jsonl> <output_report_json> [--sample N]")
        print("\nExample:")
        print("  python llm_judge_verify_pairs.py datasets/v17_dpo_pairs_enhanced.jsonl datasets/v17_judge_report.json")
        print("  python llm_judge_verify_pairs.py datasets/v17_dpo_pairs_enhanced.jsonl datasets/v17_judge_report.json --sample 50")
        sys.exit(1)
    
    inp = sys.argv[1]
    out = sys.argv[2]
    
    # Optional sampling for quick validation
    sample_size = None
    if "--sample" in sys.argv:
        idx = sys.argv.index("--sample")
        if idx + 1 < len(sys.argv):
            sample_size = int(sys.argv[idx + 1])
    
    print(f"Loading dataset from: {inp}")
    samples = list(load_jsonl(inp))
    
    if sample_size and sample_size < len(samples):
        import random
        random.seed(42)
        samples = random.sample(samples, sample_size)
        print(f"Sampling {sample_size} pairs for validation")
    
    print(f"Total pairs to judge: {len(samples)}")
    print(f"Using model: {MODEL}\n")
    
    results = []
    pass_count = 0
    score_sum = 0.0
    
    for i, s in enumerate(samples, 1):
        task_id = s.get("task_id", i)
        source = s.get("source", "unknown")
        
        prompt, response = extract_messages(s)
        
        if not prompt or not response:
            results.append({
                "task_id": task_id,
                "verdict": "FAIL",
                "reason": "Missing prompt or response",
                "scores": {},
                "overall_score": 0.0
            })
            continue
        
        judge_prompt = build_judge_prompt(prompt, response, source)
        
        print(f"[{i}/{len(samples)}] Judging {task_id}...", end=" ", flush=True)
        
        try:
            verdict = call_claude(judge_prompt)
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                "task_id": task_id,
                "verdict": "FAIL",
                "reason": f"Judge error: {str(e)}",
                "scores": {},
                "overall_score": 0.0
            })
            time.sleep(1)
            continue
        
        v = verdict.get("verdict", "FAIL")
        score = verdict.get("overall_score", 0.0)
        
        if v == "PASS":
            pass_count += 1
            print(f"✓ PASS (score: {score:.2f})")
        else:
            print(f"✗ FAIL (score: {score:.2f}) - {verdict.get('reason', 'N/A')[:50]}")
        
        score_sum += score
        
        results.append({
            "task_id": task_id,
            "source": source,
            "category": s.get("category"),
            "task_type": s.get("task_type"),
            "verdict": v,
            "reason": verdict.get("reason", ""),
            "scores": verdict.get("scores", {}),
            "overall_score": score,
            "hash": md5(prompt + response),
        })
        
        # Rate limiting
        time.sleep(0.5)
    
    # Compute statistics
    avg_score = score_sum / max(1, len(samples))
    pass_rate = pass_count / max(1, len(samples))
    
    # Aggregate by source
    from collections import Counter
    source_stats = {}
    for r in results:
        src = r.get("source", "unknown")
        if src not in source_stats:
            source_stats[src] = {"pass": 0, "fail": 0, "total": 0, "avg_score": 0.0}
        source_stats[src]["total"] += 1
        if r["verdict"] == "PASS":
            source_stats[src]["pass"] += 1
        else:
            source_stats[src]["fail"] += 1
        source_stats[src]["avg_score"] += r["overall_score"]
    
    for src in source_stats:
        source_stats[src]["avg_score"] /= max(1, source_stats[src]["total"])
        source_stats[src]["pass_rate"] = source_stats[src]["pass"] / max(1, source_stats[src]["total"])
    
    summary = {
        "total": len(samples),
        "pass": pass_count,
        "fail": len(samples) - pass_count,
        "pass_rate": round(pass_rate, 4),
        "avg_score": round(avg_score, 4),
        "model": MODEL,
        "timestamp": int(time.time()),
        "source_breakdown": source_stats,
    }
    
    save_json(out, {"summary": summary, "results": results})
    
    print("\n" + "="*80)
    print("LLM-as-Judge Report")
    print("="*80)
    print(f"Total pairs: {len(samples)}")
    print(f"Pass: {pass_count} ({pass_rate*100:.1f}%)")
    print(f"Fail: {len(samples) - pass_count} ({(1-pass_rate)*100:.1f}%)")
    print(f"Average score: {avg_score:.3f}")
    print(f"\nReport saved: {out}")
    
    print("\nBreakdown by source:")
    for src, stats in sorted(source_stats.items(), key=lambda x: x[1]["pass_rate"], reverse=True):
        print(f"  {src}: {stats['pass']}/{stats['total']} ({stats['pass_rate']*100:.1f}%) - avg {stats['avg_score']:.3f}")
    
    if pass_rate < 0.9:
        print(f"\n⚠️  Warning: Pass rate {pass_rate*100:.1f}% is below 90% threshold")
        print("Consider filtering out failed pairs before training.")
    else:
        print(f"\n✅ Pass rate {pass_rate*100:.1f}% meets quality threshold")

if __name__ == "__main__":
    main()
