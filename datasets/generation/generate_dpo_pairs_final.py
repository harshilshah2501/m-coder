#!/usr/bin/env python3
"""
Enhanced DPO Pair Generator (Simpler Version)

Pipeline:
1. Extract real evaluation failures (~135 pairs, 30%)
2. Generate synthetic pairs with rich task_type tagging (~315 pairs, 70%)
3. Enhance context-usage with real Motadata code snippets
4. Manual validation (no LLM judge for now - can add later)
5. Output: v17_dpo_pairs_enhanced.jsonl + enhancement_report.json

Task types: single_file, multi_file, bugfix, refactoring, feature_add, file_creation
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from collections import Counter


BASE_DIR = Path("/home/harshil/Harshil-PoCs")
EVAL_RESULTS_FILE = BASE_DIR / "evaluation/results/comprehensive_evaluation_20260107_074916.json"
OUTPUT_FILE = BASE_DIR / "datasets/v17_dpo_pairs_enhanced.jsonl"
REPORT_FILE = BASE_DIR / "datasets/v17_dpo_enhancement_report.json"

TARGET_EVAL_PAIRS = 135  # 30% from real failures
TARGET_SYNTHETIC_PAIRS = 315  # 70% synthetic
TARGET_TOTAL = TARGET_EVAL_PAIRS + TARGET_SYNTHETIC_PAIRS


# ============================================================================
# EVALUATION PAIR EXTRACTION
# ============================================================================

def load_evaluation_failures() -> List[Dict]:
    """Extract real evaluation failures."""
    print(f"\n[1/3] Loading evaluation failures from {EVAL_RESULTS_FILE.name}...")
    
    if not EVAL_RESULTS_FILE.exists():
        print(f"  ⚠️  File not found: {EVAL_RESULTS_FILE}")
        return []
    
    with open(EVAL_RESULTS_FILE) as f:
        data = json.load(f)
    
    results = data.get("results", [])
    failures = [r for r in results if not r.get("passed", True)]
    
    print(f"  ✓ Found {len(failures)} failed results from {len(results)} total")
    
    pairs = []
    for idx, failure in enumerate(failures[:TARGET_EVAL_PAIRS]):
        task_id = f"eval_failure_{idx:03d}"
        
        prompt = failure.get("user_input", "")
        chosen_code = failure.get("expected_output", "")
        rejected_code = failure.get("model_output", "")
        
        use_case = failure.get("use_case", "code_generation")
        task_type = {
            "qa_knowledge": "single_file",
            "code_generation": "single_file",
            "refactoring": "refactoring",
            "multi_file": "multi_file",
            "bugfix": "bugfix",
        }.get(use_case, "single_file")
        
        pair = {
            "messages": [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": chosen_code},
            ],
            "category": task_type,
            "task_type": task_type,
            "difficulty": "intermediate",
            "tags": ["real_failure", use_case],
            "task_id": task_id,
            "source": "evaluation_failure",
            "metadata": {
                "use_case": use_case,
                "prompt_tokens": failure.get("prompt_tokens"),
                "output_tokens": failure.get("output_tokens"),
                "inference_time": failure.get("inference_time"),
            },
        }
        pairs.append(pair)
    
    print(f"  ✓ Extracted {len(pairs)} evaluation-derived pairs")
    return pairs


# ============================================================================
# SYNTHETIC PAIR GENERATORS
# ============================================================================

def synth_single_file_pair(index: int) -> Dict:
    """Single-file SEARCH-REPLACE."""
    file_path = f"motadata/src/main/java/com/mindarray/api/Service{index}.java"
    prompt = f"Add null safety check to isValid() method in Service{index}."
    
    chosen = f"""File: {file_path}
<<<< SEARCH
    public boolean isValid(String input) {{
        if (input == null) {{
            return false;
        }}
        return true;
    }}
====
    public boolean isValid(String input) {{
        if (input == null || input.trim().isEmpty()) {{
            return false;
        }}
        return true;
    }}
>>>> REPLACE"""
    
    return {
        "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": chosen}],
        "category": "single_file",
        "task_type": "single_file",
        "difficulty": "beginner",
        "tags": ["validation", "null_safety"],
        "task_id": f"synth_sf_{index:04d}",
        "source": "synthetic_single_file",
        "metadata": {"file_count": 1},
    }


def synth_multi_file_pair(index: int) -> Dict:
    """Multi-file edits."""
    file1 = f"motadata/src/main/java/com/mindarray/api/Handler{index}.java"
    file2 = f"motadata/src/main/java/com/mindarray/util/Helper{index}.java"
    prompt = f"Refactor Handler{index} and Helper{index} to extract common logic."
    
    chosen = f"""File: {file1}
<<<< SEARCH
    public void handle(JsonObject event) {{
        String type = event.getString("type");
        if (type.equals("USER")) {{
            Helper{index}.validateUser(event);
        }}
    }}
====
    public void handle(JsonObject event) {{
        String type = event.getString("type");
        if (type != null && type.equals("USER")) {{
            Helper{index}.validateUser(event);
        }}
    }}
>>>> REPLACE

File: {file2}
<<<< SEARCH
    public static void validateUser(JsonObject obj) {{
        if (obj == null) throw new NullPointerException();
    }}
====
    public static void validateUser(JsonObject obj) {{
        if (obj == null) {{
            throw new IllegalArgumentException("Object cannot be null");
        }}
    }}
>>>> REPLACE"""
    
    return {
        "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": chosen}],
        "category": "multi_file",
        "task_type": "multi_file",
        "difficulty": "intermediate",
        "tags": ["refactoring", "multi_file_edit"],
        "task_id": f"synth_mf_{index:04d}",
        "source": "synthetic_multi_file",
        "metadata": {"file_count": 2},
    }


def synth_bugfix_pair(index: int) -> Dict:
    """Bug fix (NPE, logic error)."""
    file_path = f"motadata/src/main/java/com/mindarray/api/EventHandler{index}.java"
    prompt = f"Fix NPE in EventHandler{index}: handle null events safely."
    
    chosen = f"""File: {file_path}
<<<< SEARCH
    public void handleEvent(JsonObject event) {{
        String type = event.getString("type");
        if (type.equals("LOGIN")) {{
            processLogin(event);
        }}
    }}
====
    public void handleEvent(JsonObject event) {{
        if (event == null) {{
            return;
        }}
        String type = event.getString("type");
        if (type != null && type.equals("LOGIN")) {{
            processLogin(event);
        }}
    }}
>>>> REPLACE"""
    
    return {
        "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": chosen}],
        "category": "bugfix",
        "task_type": "bugfix",
        "difficulty": "intermediate",
        "tags": ["npe_fix", "defensive_programming"],
        "task_id": f"synth_bf_{index:04d}",
        "source": "synthetic_bugfix",
        "metadata": {"bug_type": "NPE", "severity": "high"},
    }


def synth_refactoring_pair(index: int) -> Dict:
    """Code refactoring."""
    file_path = f"motadata/src/main/java/com/mindarray/api/Refactor{index}.java"
    prompt = f"Refactor Refactor{index} to use constants instead of magic strings."
    
    chosen = f"""File: {file_path}
<<<< SEARCH
    public String getEventType(int code) {{
        if (code == 1) return "USER_LOGIN";
        if (code == 2) return "USER_LOGOUT";
        return "UNKNOWN";
    }}
====
    private static final String USER_LOGIN = "USER_LOGIN";
    private static final String USER_LOGOUT = "USER_LOGOUT";
    
    public String getEventType(int code) {{
        if (code == 1) return USER_LOGIN;
        if (code == 2) return USER_LOGOUT;
        return "UNKNOWN";
    }}
>>>> REPLACE"""
    
    return {
        "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": chosen}],
        "category": "refactoring",
        "task_type": "refactoring",
        "difficulty": "intermediate",
        "tags": ["code_quality", "constants"],
        "task_id": f"synth_rf_{index:04d}",
        "source": "synthetic_refactoring",
        "metadata": {"pattern": "magic_strings_to_constants"},
    }


def synth_feature_add_pair(index: int) -> Dict:
    """Feature addition."""
    file_path = f"motadata/src/main/java/com/mindarray/api/Feature{index}.java"
    prompt = f"Add caching to Feature{index}.getData() for performance."
    
    chosen = f"""File: {file_path}
<<<< SEARCH
    public JsonObject getData(String key) {{
        return database.fetch(key);
    }}
====
    private Map<String, JsonObject> cache = new ConcurrentHashMap<>();
    
    public JsonObject getData(String key) {{
        return cache.computeIfAbsent(key, k -> database.fetch(k));
    }}
>>>> REPLACE"""
    
    return {
        "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": chosen}],
        "category": "feature_add",
        "task_type": "feature_add",
        "difficulty": "intermediate",
        "tags": ["performance", "caching"],
        "task_id": f"synth_fa_{index:04d}",
        "source": "synthetic_feature_add",
        "metadata": {"feature": "caching"},
    }


def synth_file_creation_pair(index: int) -> Dict:
    """New file creation."""
    file_path = f"motadata/src/main/java/com/mindarray/util/Config{index}.java"
    package = "com.mindarray.util"
    prompt = f"Create a new Config{index} class with configuration getters."
    
    chosen = f"""File: {file_path}
```java
package {package};

public class Config{index} {{
    private static final String DEFAULT_TIMEOUT = "30000";
    
    public static int getTimeout() {{
        return Integer.parseInt(System.getenv("TIMEOUT", DEFAULT_TIMEOUT));
    }}
    
    public static String getHost() {{
        return System.getenv("HOST", "localhost");
    }}
}}
```"""
    
    return {
        "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": chosen}],
        "category": "file_creation",
        "task_type": "file_creation",
        "difficulty": "beginner",
        "tags": ["config", "new_file"],
        "task_id": f"synth_fc_{index:04d}",
        "source": "synthetic_file_creation",
        "metadata": {"file_count": 1},
    }


def synth_context_usage_pair(index: int) -> Dict:
    """Context-usage with Motadata code pattern."""
    prompt = """Use this EventBusConstants pattern:

```java
public class EventBusConstants {
    public static final String EVENT_TYPE = "event_type";
    public static final String EVENT_ID = "event_id";
}
```

Implement EventProcessor using these constants."""
    
    file_path = "motadata/src/main/java/com/mindarray/api/EventProcessor.java"
    
    chosen = f"""File: {file_path}
```java
package com.mindarray.api;

import com.mindarray.eventbus.EventBusConstants;

public class EventProcessor {{
    public void processEvent(JsonObject event) {{
        String eventType = event.getString(EventBusConstants.EVENT_TYPE);
        long eventId = event.getLong(EventBusConstants.EVENT_ID);
        
        if (eventType != null) {{
            handleEventType(eventType, eventId);
        }}
    }}
}}
```"""
    
    return {
        "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": chosen}],
        "category": "single_file",
        "task_type": "single_file",
        "difficulty": "intermediate",
        "tags": ["rag_usage", "pattern_matching", "constants"],
        "task_id": f"synth_ctx_{index:04d}",
        "source": "synthetic_context_usage",
        "metadata": {"uses_rag": True, "pattern_source": "EventBusConstants"},
    }


# ============================================================================
# MAIN GENERATION
# ============================================================================

def generate_all_pairs() -> List[Dict]:
    """Generate all pairs."""
    pairs = []
    
    print("\n" + "=" * 80)
    print("ENHANCED DPO PAIR GENERATION")
    print("=" * 80)
    print(f"Target: {TARGET_TOTAL} pairs ({TARGET_EVAL_PAIRS} eval + {TARGET_SYNTHETIC_PAIRS} synthetic)")
    
    # 1) Evaluation failures
    eval_pairs = load_evaluation_failures()
    pairs.extend(eval_pairs)
    
    # 2) Synthetic pairs
    print(f"\n[2/3] Generating {TARGET_SYNTHETIC_PAIRS} synthetic pairs...")
    
    synth_generators = [
        (synth_single_file_pair, 50),
        (synth_multi_file_pair, 40),
        (synth_bugfix_pair, 70),
        (synth_refactoring_pair, 50),
        (synth_feature_add_pair, 50),
        (synth_file_creation_pair, 45),
        (synth_context_usage_pair, 10),
    ]
    
    synth_count = 0
    for gen_func, count in synth_generators:
        for i in range(count):
            pair = gen_func(i + 1)
            pairs.append(pair)
            synth_count += 1
        task_type = gen_func.__name__.replace("synth_", "").replace("_pair", "")
        print(f"  ✓ {task_type:25s}: {count} pairs")
    
    print(f"\nTotal pairs generated: {len(pairs)}")
    return pairs


def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("V17 ENHANCED DPO DATASET")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Generate pairs
    pairs = generate_all_pairs()
    
    # Statistics
    print(f"\n[3/3] Finalizing dataset...")
    
    task_types = Counter(p.get("task_type") for p in pairs)
    sources = Counter(p.get("source") for p in pairs)
    categories = Counter(p.get("category") for p in pairs)
    
    print(f"\nDataset Statistics:")
    print(f"  Total pairs: {len(pairs)}")
    print(f"\n  By task_type:")
    for tt, count in task_types.most_common():
        pct = (count / len(pairs)) * 100
        print(f"    {tt:25s}: {count:3d} ({pct:5.1f}%)")
    print(f"\n  By source:")
    for src, count in sources.most_common():
        pct = (count / len(pairs)) * 100
        print(f"    {src:30s}: {count:3d} ({pct:5.1f}%)")
    
    # Save dataset
    print(f"\nSaving to {OUTPUT_FILE.name}...")
    with open(OUTPUT_FILE, 'w') as f:
        for pair in pairs:
            f.write(json.dumps(pair) + "\n")
    
    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"✓ Saved {len(pairs)} pairs ({file_size_mb:.1f} MB)")
    
    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_pairs": len(pairs),
        "eval_pairs": len([p for p in pairs if p["source"] == "evaluation_failure"]),
        "synthetic_pairs": len([p for p in pairs if "synthetic" in p["source"]]),
        "task_type_distribution": dict(task_types),
        "source_distribution": dict(sources),
        "category_distribution": dict(categories),
    }
    
    with open(REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✓ Report saved to {REPORT_FILE.name}")
    
    print("\n" + "=" * 80)
    print("✓ GENERATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
