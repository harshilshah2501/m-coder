#!/usr/bin/env python3
"""
Enhanced DPO Pair Generator with LLM-as-Judge Verification

Pipeline:
1. Extract real evaluation failures (~135 pairs, 30%)
2. Generate synthetic pairs with rich task_type tagging (~315 pairs, 70%)
3. Enhance context-usage with real Motadata code snippets
4. Use Claude API to verify chosen > rejected for quality
5. Output: v17_dpo_pairs_enhanced.jsonl + llm_judge_report.json

Task types supported:
- single_file: Edit one file (SEARCH-REPLACE)
- multi_file: Edit multiple files
- bugfix: Fix a bug (NPE, logic error, etc.)
- refactoring: Improve code structure
- feature_add: Add new feature
- file_creation: Create new file (PLAIN CODE)
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import Counter
import requests


# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path("/home/harshil/Harshil-PoCs")
EVAL_RESULTS_FILE = BASE_DIR / "evaluation/results/comprehensive_evaluation_20260107_074916.json"
OUTPUT_FILE = BASE_DIR / "datasets/v17_dpo_pairs_enhanced.jsonl"
JUDGE_REPORT = BASE_DIR / "datasets/v17_dpo_llm_judge_report.json"

# Pair generation targets
TARGET_EVAL_PAIRS = 135  # 30% from real failures
TARGET_SYNTHETIC_PAIRS = 315  # 70% synthetic
TARGET_TOTAL = TARGET_EVAL_PAIRS + TARGET_SYNTHETIC_PAIRS

# Claude API
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"

# Motadata code snippets (for context-usage pairs RAG simulation)
MOTADATA_SNIPPETS = {
    "EventBusConstants": """
public class EventBusConstants {
    public static final String EVENT_TYPE = "event_type";
    public static final String EVENT_ID = "event_id";
    
    public enum EventType {
        PLUGIN_RUNBOOK,
        PLUGIN_SNMP_DEVICE_CATALOG,
        PLUGIN_USER_PROFILE
    }
}
""",
    "DataSecurity": """
public static JsonArray qualifyObjects(long userId, JsonArray objects) {
    return objects.stream()
        .map(JsonObject::mapFrom)
        .filter(obj -> hasAccess(userId, obj))
        .collect(Collectors.toCollection(JsonArray::new));
}
""",
    "CommonConfigStore": """
public class CommonConfigStore {
    public static final String RUNBOOK_PLUGIN_ID = "runbook_plugin_id";
    public static final String USER_PROFILE_ID = "user_profile_id";
    
    public static synchronized CommonConfigStore getStore() {
        if (instance == null) {
            instance = new CommonConfigStore();
        }
        return instance;
    }
}
""",
}


# ============================================================================
# EVALUATION PAIR EXTRACTION
# ============================================================================

def load_evaluation_failures() -> List[Dict]:
    """Extract real evaluation failures to use as DPO pairs."""
    print(f"\n[1/4] Loading evaluation failures from {EVAL_RESULTS_FILE.name}...")
    
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
        
        # User input = prompt/question
        prompt = failure.get("user_input", "")
        
        # Chosen = expected output (ground truth)
        chosen_code = failure.get("expected_output", "")
        
        # Rejected = model's incorrect output
        rejected_code = failure.get("model_output", "")
        
        # Determine task type from use_case
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
            "_rejected_response": rejected_code,  # For LLM judge
        }
        pairs.append(pair)
    
    print(f"  ✓ Extracted {len(pairs)} evaluation-derived pairs")
    return pairs


# ============================================================================
# SYNTHETIC PAIR GENERATION WITH TASK TYPES
# ============================================================================

def synth_single_file_pair(index: int) -> Dict:
    """Single-file SEARCH-REPLACE edit."""
    task_id = f"synth_sf_{index:04d}"
    
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
    
    rejected = f"""File: {file_path}
<<<< SEARCH
    public boolean isValid(String input) {{
        if (input == null) {{
            return false;
        }}
        return true;
    }}
====
    public boolean isValid(String input) {{
        return input != null;
    }}
>>>> REPLACE"""
    
    return {
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": chosen},
        ],
        "category": "single_file",
        "task_type": "single_file",
        "difficulty": "beginner",
        "tags": ["validation", "null_safety"],
        "task_id": task_id,
        "source": "synthetic_single_file",
        "metadata": {"file_count": 1},
        "_rejected_response": rejected,
    }


def synth_multi_file_pair(index: int) -> Dict:
    """Multi-file edit scenario."""
    task_id = f"synth_mf_{index:04d}"
    
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
    
    rejected = f"""File: {file1}
<<<< SEARCH
    public void handle(JsonObject event) {{
        String type = event.getString("type");
        if (type.equals("USER")) {{
            Helper{index}.validateUser(event);
        }}
    }}
====
    public void handle(JsonObject event) {{
        Helper{index}.validateUser(event.getString("type"));
    }}
>>>> REPLACE"""
    
    return {
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": chosen},
        ],
        "category": "multi_file",
        "task_type": "multi_file",
        "difficulty": "intermediate",
        "tags": ["refactoring", "multi_file_edit"],
        "task_id": task_id,
        "source": "synthetic_multi_file",
        "metadata": {"file_count": 2},
        "_rejected_response": rejected,
    }


def synth_bugfix_pair(index: int) -> Dict:
    """Bug fix scenario (NPE, logic error)."""
    task_id = f"synth_bf_{index:04d}"
    
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
    
    rejected = f"""File: {file_path}
<<<< SEARCH
    public void handleEvent(JsonObject event) {{
        String type = event.getString("type");
        if (type.equals("LOGIN")) {{
            processLogin(event);
        }}
    }}
====
    public void handleEvent(JsonObject event) {{
        if (event == null) return;
        if (event.getString("type").equals("LOGIN")) {{
            processLogin(event);
        }}
    }}
>>>> REPLACE"""
    
    return {
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": chosen},
        ],
        "category": "bugfix",
        "task_type": "bugfix",
        "difficulty": "intermediate",
        "tags": ["npe_fix", "defensive_programming"],
        "task_id": task_id,
        "source": "synthetic_bugfix",
        "metadata": {"bug_type": "NPE", "severity": "high"},
        "_rejected_response": rejected,
    }


def synth_refactoring_pair(index: int) -> Dict:
    """Code refactoring scenario."""
    task_id = f"synth_rf_{index:04d}"
    
    file_path = f"motadata/src/main/java/com/mindarray/api/Refactor{index}.java"
    
    prompt = f"Refactor Refactor{index} to use constants instead of magic strings."
    
    chosen = f"""File: {file_path}
<<<< SEARCH
    public String getEventType(int code) {{
        if (code == 1) return "USER_LOGIN";
        if (code == 2) return "USER_LOGOUT";
        if (code == 3) return "SYSTEM_ERROR";
        return "UNKNOWN";
    }}
====
    private static final String USER_LOGIN = "USER_LOGIN";
    private static final String USER_LOGOUT = "USER_LOGOUT";
    private static final String SYSTEM_ERROR = "SYSTEM_ERROR";
    
    public String getEventType(int code) {{
        if (code == 1) return USER_LOGIN;
        if (code == 2) return USER_LOGOUT;
        if (code == 3) return SYSTEM_ERROR;
        return "UNKNOWN";
    }}
>>>> REPLACE"""
    
    rejected = f"""File: {file_path}
<<<< SEARCH
    public String getEventType(int code) {{
        if (code == 1) return "USER_LOGIN";
        if (code == 2) return "USER_LOGOUT";
        if (code == 3) return "SYSTEM_ERROR";
        return "UNKNOWN";
    }}
====
    public static final Map<Integer, String> EVENT_MAP = new HashMap<>();
    static {{
        EVENT_MAP.put(1, "USER_LOGIN");
    }}
    
    public String getEventType(int code) {{
        return EVENT_MAP.getOrDefault(code, "UNKNOWN");
    }}
>>>> REPLACE"""
    
    return {
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": chosen},
        ],
        "category": "refactoring",
        "task_type": "refactoring",
        "difficulty": "intermediate",
        "tags": ["code_quality", "constants"],
        "task_id": task_id,
        "source": "synthetic_refactoring",
        "metadata": {"pattern": "magic_strings_to_constants"},
        "_rejected_response": rejected,
    }


def synth_feature_add_pair(index: int) -> Dict:
    """Feature addition scenario."""
    task_id = f"synth_fa_{index:04d}"
    
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
    
    rejected = f"""File: {file_path}
<<<< SEARCH
    public JsonObject getData(String key) {{
        return database.fetch(key);
    }}
====
    public JsonObject getData(String key) {{
        JsonObject cached = getFromCache(key);
        if (cached != null) {{
            return cached;
        }}
        return database.fetch(key);
    }}
>>>> REPLACE"""
    
    return {
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": chosen},
        ],
        "category": "feature_add",
        "task_type": "feature_add",
        "difficulty": "intermediate",
        "tags": ["performance", "caching"],
        "task_id": task_id,
        "source": "synthetic_feature_add",
        "metadata": {"feature": "caching"},
        "_rejected_response": rejected,
    }


def synth_file_creation_pair(index: int) -> Dict:
    """New file creation (PLAIN CODE format)."""
    task_id = f"synth_fc_{index:04d}"
    
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
    
    rejected = f"""File: {file_path}
```java
package {package};

public class Config{index} {{
    public static String timeout = "30000";
    
    public static void setConfig(String key, String value) {{
        // implementation missing
    }}
}}
```"""
    
    return {
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": chosen},
        ],
        "category": "file_creation",
        "task_type": "file_creation",
        "difficulty": "beginner",
        "tags": ["config", "new_file"],
        "task_id": task_id,
        "source": "synthetic_file_creation",
        "metadata": {"file_count": 1},
        "_rejected_response": rejected,
    }


def synth_context_usage_pair(index: int) -> Dict:
    """Context-usage with real Motadata snippet."""
    task_id = f"synth_ctx_{index:04d}"
    
    # Pick a random snippet
    snippet_name = list(MOTADATA_SNIPPETS.keys())[index % len(MOTADATA_SNIPPETS)]
    snippet = MOTADATA_SNIPPETS[snippet_name]
    
    prompt = f"""Use this code pattern from {snippet_name}:

```java
{snippet.strip()}
```

Implement a similar pattern for EventProcessor."""
    
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
    
    private void handleEventType(String type, long id) {{
        // process event
    }}
}}
```"""
    
    rejected = f"""File: {file_path}
```java
public class EventProcessor {{
    public void processEvent(JsonObject event) {{
        String eventType = event.getString("event_type");
        long eventId = event.getLong("event_id");
        handleEventType(eventType, eventId);
    }}
}}
```"""
    
    return {
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": chosen},
        ],
        "category": "single_file",
        "task_type": "single_file",
        "difficulty": "intermediate",
        "tags": ["rag_usage", "pattern_matching", snippet_name.lower()],
        "task_id": task_id,
        "source": "synthetic_context_usage",
        "metadata": {
            "uses_rag": True,
            "pattern_source": snippet_name,
        },
        "_rejected_response": rejected,
    }


# ============================================================================
# LLM-AS-JUDGE VERIFICATION
# ============================================================================

def verify_pair_with_claude(pair: Dict) -> Tuple[bool, str]:
    """Use Claude to verify that chosen > rejected."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    prompt = pair["messages"][0]["content"]
    chosen = pair["messages"][1]["content"]
    rejected = pair["_rejected_response"]
    
    judge_prompt = f"""You are a code quality judge. 

PROMPT:
{prompt}

CHOSEN RESPONSE:
{chosen}

REJECTED RESPONSE:
{rejected}

Evaluate: Is the CHOSEN response clearly better than the REJECTED response?
Consider: correctness, safety, completeness, adherence to best practices.

Respond with ONLY "YES" or "NO" followed by a brief reason (1 sentence).

Example: "YES: Chosen has null safety check while rejected misses it."
"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return False, "Error: ANTHROPIC_API_KEY not set"
        
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        
        data = {
            "model": CLAUDE_MODEL,
            "max_tokens": 100,
            "messages": [{"role": "user", "content": judge_prompt}],
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=30,
        )
        
        if response.status_code != 200:
            return False, f"API Error {response.status_code}: {response.text[:100]}"
        
        result = response.json()
        )
        verdict = response.content[0].text.strip()
        is_valid = verdict.startswith("YES")
        return is_valid, verdict
        return False, f"Error: {str(e)[:50]}"
        return False, f"Error: {str(e)}"


# ============================================================================
# MAIN GENERATION
# ============================================================================

def generate_all_pairs() -> List[Dict]:
    """Generate all pairs: eval + synthetic."""
    pairs = []
    
    print("\n" + "=" * 80)
    print("ENHANCED DPO PAIR GENERATION (Eval + Synthetic + LLM Judge)")
    print("=" * 80)
    print(f"Target: {TARGET_TOTAL} pairs ({TARGET_EVAL_PAIRS} eval + {TARGET_SYNTHETIC_PAIRS} synthetic)")
    
    # 1) Evaluation failures
    eval_pairs = load_evaluation_failures()
    pairs.extend(eval_pairs)
    
    # 2) Synthetic pairs
    print(f"\n[2/4] Generating synthetic pairs...")
    synth_generators = [
        (synth_single_file_pair, 50, "single_file"),
        (synth_multi_file_pair, 40, "multi_file"),
        (synth_bugfix_pair, 70, "bugfix"),
        (synth_refactoring_pair, 50, "refactoring"),
        (synth_feature_add_pair, 50, "feature_add"),
        (synth_file_creation_pair, 45, "file_creation"),
        (synth_context_usage_pair, 10, "context_usage"),
    ]
    
    synth_count = 0
    for gen_func, count, task_type in synth_generators:
        for i in range(count):
            pair = gen_func(i + 1)
            pairs.append(pair)
            synth_count += 1
        print(f"  ✓ {task_type:20s}: {count} pairs")
    
    print(f"  ✓ Total synthetic: {synth_count} pairs")
    
    print(f"\nTotal pairs before LLM judge: {len(pairs)}")
    
    return pairs


def filter_with_llm_judge(pairs: List[Dict]) -> Tuple[List[Dict], Dict]:
    """Filter pairs using Claude as judge."""
    print(f"\n[3/4] LLM-as-Judge verification (Claude API)...")
    print(f"Verifying {len(pairs)} pairs...")
    
    valid_pairs = []
    judge_results = {
        "total_checked": len(pairs),
        "passed": 0,
        "failed": 0,
        "results": []
    }
    
    for idx, pair in enumerate(pairs):
        task_id = pair.get("task_id")
        source = pair.get("source")
        
        # Skip judge for real evaluation pairs (already validated)
        if source == "evaluation_failure":
            valid_pairs.append(pair)
            judge_results["passed"] += 1
        else:
            # Judge synthetic pairs
            is_valid, verdict = verify_pair_with_claude(pair)
            
            judge_results["results"].append({
                "task_id": task_id,
                "passed": is_valid,
                "verdict": verdict,
            })
            
            if is_valid:
                valid_pairs.append(pair)
                judge_results["passed"] += 1
            else:
                judge_results["failed"] += 1
        
        if (idx + 1) % 20 == 0:
            print(f"  Progress: {idx + 1}/{len(pairs)}")
    
    judge_results["pass_rate"] = (judge_results["passed"] / judge_results["total_checked"]) * 100
    
    print(f"\nJudge Results:")
    print(f"  Passed: {judge_results['passed']}/{judge_results['total_checked']} ({judge_results['pass_rate']:.1f}%)")
    print(f"  Failed: {judge_results['failed']}")
    
    return valid_pairs, judge_results


def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("ENHANCED V17 DPO DATASET GENERATION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Claude API Model: {CLAUDE_MODEL}")
    
    # Generate pairs
    pairs = generate_all_pairs()
    
    # LLM judge verification
    valid_pairs, judge_report = filter_with_llm_judge(pairs)
    
    # Remove judge helper field
    for pair in valid_pairs:
        if "_rejected_response" in pair:
            del pair["_rejected_response"]
    
    # Statistics
    print(f"\n[4/4] Finalizing dataset...")
    
    task_types = Counter(p.get("task_type") for p in valid_pairs)
    sources = Counter(p.get("source") for p in valid_pairs)
    
    print(f"\nFinal Dataset Statistics:")
    print(f"  Total pairs: {len(valid_pairs)}")
    print(f"  Task types:")
    for tt, count in task_types.most_common():
        pct = (count / len(valid_pairs)) * 100
        print(f"    {tt:20s}: {count:3d} ({pct:5.1f}%)")
    print(f"  Sources:")
    for src, count in sources.most_common():
        pct = (count / len(valid_pairs)) * 100
        print(f"    {src:30s}: {count:3d} ({pct:5.1f}%)")
    
    # Save dataset
    print(f"\nSaving to {OUTPUT_FILE.name}...")
    with open(OUTPUT_FILE, 'w') as f:
        for pair in valid_pairs:
            f.write(json.dumps(pair) + "\n")
    
    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"✓ Saved {len(valid_pairs)} pairs ({file_size_mb:.1f} MB)")
    
    # Save judge report
    judge_report["timestamp"] = datetime.now().isoformat()
    judge_report["final_pair_count"] = len(valid_pairs)
    judge_report["task_type_distribution"] = dict(task_types)
    judge_report["source_distribution"] = dict(sources)
    
    with open(JUDGE_REPORT, 'w') as f:
        json.dump(judge_report, f, indent=2)
    
    print(f"✓ Judge report saved to {JUDGE_REPORT.name}")
    
    print("\n" + "=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
