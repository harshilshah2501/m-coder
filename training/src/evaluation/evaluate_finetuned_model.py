#!/usr/bin/env python3
"""
Motadata Finetuned Model Evaluation Script
Based on Motadata-AI-System-Guide-v2.md testing checklist
"""

import requests
import json
import re
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import time

API_URL = "http://localhost:8080/v1/chat/completions"

@dataclass
class TestCase:
    id: str
    category: str  # TYPE_A_KNOWLEDGE, TYPE_B_MULTIFILE, TYPE_C_TOOLS, RCA_DEBUGGING, CODE_REVIEW
    name: str
    system_prompt: str
    user_prompt: str
    expected_patterns: List[str]  # Patterns that SHOULD appear
    forbidden_patterns: List[str]  # Patterns that should NOT appear
    max_tokens: int = 1024

@dataclass
class TestResult:
    test_id: str
    category: str
    name: str
    passed: bool
    score: int  # 1-5
    response: str
    issues: List[str]
    response_time_ms: int
    has_tool_calls: bool
    has_repetition: bool
    has_valid_code: bool

# Issue detection patterns
TOOL_PATTERNS = [
    r'<tool_response>', r'<javaparser>', r'<thought>', r'vector_search\(',
    r'graph_all\(', r'<LMResponse>', r'run_terminal_command', r'find_similar_classes',
    r'"name":\s*"find_', r'"name":\s*"search_', r'<augment_code_snippet'
]

REPETITION_THRESHOLD = 3  # Same phrase repeated X times = issue

def detect_issues(response: str) -> Dict[str, Any]:
    """Detect common issues in model response"""
    issues = []

    # Check for tool calls
    has_tool_calls = any(re.search(p, response, re.IGNORECASE) for p in TOOL_PATTERNS)
    if has_tool_calls:
        issues.append("TOOL_OBSESSION: Response contains tool/XML calls instead of direct answer")

    # Check for repetition
    words = response.split()
    word_chunks = [' '.join(words[i:i+5]) for i in range(len(words)-4)]
    chunk_counts = {}
    for chunk in word_chunks:
        chunk_counts[chunk] = chunk_counts.get(chunk, 0) + 1
    has_repetition = any(c >= REPETITION_THRESHOLD for c in chunk_counts.values())
    if has_repetition:
        issues.append("REPETITION_LOOP: Response contains repeated phrases/patterns")

    # Check for valid code blocks
    has_valid_code = '```' in response or 'class ' in response or 'public ' in response

    # Check for empty/minimal response
    if len(response.strip()) < 50:
        issues.append("MINIMAL_RESPONSE: Response too short/empty")

    # Check for Chinese/garbage artifacts
    if re.search(r'[\u4e00-\u9fff]', response):
        issues.append("GARBAGE_TOKENS: Contains Chinese/garbage characters")

    return {
        "issues": issues,
        "has_tool_calls": has_tool_calls,
        "has_repetition": has_repetition,
        "has_valid_code": has_valid_code
    }

def calculate_score(test: TestCase, response: str, issues: Dict) -> int:
    """Calculate 1-5 score based on response quality"""
    score = 5

    # Deduct for issues
    if issues["has_tool_calls"]:
        score -= 2
    if issues["has_repetition"]:
        score -= 2
    if len(issues["issues"]) > 0:
        score -= len(issues["issues"]) * 0.5

    # Check expected patterns
    expected_found = sum(1 for p in test.expected_patterns if re.search(p, response, re.IGNORECASE))
    expected_ratio = expected_found / len(test.expected_patterns) if test.expected_patterns else 1
    score = score * expected_ratio

    # Check forbidden patterns
    forbidden_found = sum(1 for p in test.forbidden_patterns if re.search(p, response, re.IGNORECASE))
    score -= forbidden_found

    return max(1, min(5, int(round(score))))

def run_test(test: TestCase) -> TestResult:
    """Run a single test case"""
    messages = []
    if test.system_prompt:
        messages.append({"role": "system", "content": test.system_prompt})
    messages.append({"role": "user", "content": test.user_prompt})

    payload = {
        "model": "motadata-coder",
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": test.max_tokens
    }

    start = time.time()
    try:
        resp = requests.post(API_URL, json=payload, timeout=120)
        resp.raise_for_status()
        response_time = int((time.time() - start) * 1000)
        content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        return TestResult(
            test_id=test.id, category=test.category, name=test.name,
            passed=False, score=0, response=f"ERROR: {e}", issues=["API_ERROR"],
            response_time_ms=0, has_tool_calls=False, has_repetition=False, has_valid_code=False
        )

    issues = detect_issues(content)
    score = calculate_score(test, content, issues)
    passed = score >= 3 and not issues["has_tool_calls"] and not issues["has_repetition"]

    return TestResult(
        test_id=test.id, category=test.category, name=test.name,
        passed=passed, score=score, response=content[:2000],
        issues=issues["issues"], response_time_ms=response_time,
        has_tool_calls=issues["has_tool_calls"], has_repetition=issues["has_repetition"],
        has_valid_code=issues["has_valid_code"]
    )

# Define test cases based on Motadata-AI-System-Guide-v2.md checklist
TEST_CASES = [
    # TYPE A: Knowledge Tests
    TestCase(
        id="A1", category="TYPE_A_KNOWLEDGE", name="Query Class Methods",
        system_prompt="You are a Motadata expert. Answer directly without tools.",
        user_prompt="What methods does the Query class have in Motadata?",
        expected_patterns=[r"execute", r"method", r"Query"],
        forbidden_patterns=[r"<tool_response>", r"<javaparser>"]
    ),
    TestCase(
        id="A2", category="TYPE_A_KNOWLEDGE", name="AbstractConfigStore Knowledge",
        system_prompt="You are a Motadata expert. Answer directly without tools or XML.",
        user_prompt="Explain what AbstractConfigStore does in Motadata and list 3 different classes that extend it.",
        expected_patterns=[r"AbstractConfigStore", r"extend", r"Store"],
        forbidden_patterns=[r"<tool_response>", r"vector_search"]
    ),
    TestCase(
        id="A3", category="TYPE_A_KNOWLEDGE", name="EventBus Architecture",
        system_prompt="Answer directly about Motadata architecture. No tools.",
        user_prompt="How does EventBus work in Motadata's Vert.x architecture?",
        expected_patterns=[r"EventBus", r"Vert\.x|vertx|verticle", r"address|message|handler"],
        forbidden_patterns=[r"<tool_response>", r"graph_all"]
    ),

    # TYPE B: Multi-File Feature Tests
    TestCase(
        id="B1", category="TYPE_B_MULTIFILE", name="Create Full API Feature",
        system_prompt="You are a Motadata Architect. Create complete implementation with execution plan. Do NOT use tools or XML.",
        user_prompt="Create a CorrectionProfile API with ConfigStore. List ALL files needed: API class, ConfigStore, APIRouter registration, DBConstants, and schema.",
        expected_patterns=[r"CorrectionProfile", r"ConfigStore", r"APIRouter", r"DBConstants"],
        forbidden_patterns=[r"<tool_response>"],
        max_tokens=2048
    ),
    TestCase(
        id="B2", category="TYPE_B_MULTIFILE", name="New Monitor Plugin",
        system_prompt="You are a Motadata developer. Provide complete code. No tools.",
        user_prompt="Add a new NetApp storage monitor plugin. Show the plugin class, config store, and registration code.",
        expected_patterns=[r"class.*Plugin|Plugin.*class", r"NetApp|Storage", r"extends"],
        forbidden_patterns=[r"<tool_response>"],
        max_tokens=2048
    ),

    # RCA/Debugging Tests
    TestCase(
        id="R1", category="RCA_DEBUGGING", name="NullPointer RCA",
        system_prompt="You are a Motadata RCA expert. Analyze errors directly. No tools.",
        user_prompt="""Analyze this Vert.x error and provide root cause + fix:
java.lang.NullPointerException at com.mindarray.api.Discovery.handleDiscoveryRequest(Discovery.java:145)
  at io.vertx.core.impl.ContextImpl.executeBlocking
Address: com.mindarray.api.discovery""",
        expected_patterns=[r"NullPointer|null", r"Discovery", r"fix|solution|check"],
        forbidden_patterns=[r"<tool_response>"]
    ),
    TestCase(
        id="R2", category="RCA_DEBUGGING", name="Timeout RCA",
        system_prompt="Analyze this production error. Provide root cause and code fix.",
        user_prompt="""Production error log:
ERROR [vert.x-eventloop-thread-3] TimeoutException: Response not received within 30000ms
Handler: com.mindarray.store.AgentCacheStore.refreshCache
Correlation-ID: abc-123

What's the root cause and how to fix it?""",
        expected_patterns=[r"timeout|Timeout", r"async|blocking|cache", r"fix|increase|optimize"],
        forbidden_patterns=[r"<tool_response>"]
    ),

    # Code Review Tests
    TestCase(
        id="C1", category="CODE_REVIEW", name="API Pattern Review",
        system_prompt="You are a Motadata code reviewer. Review for pattern violations.",
        user_prompt="""Review this code for Motadata pattern issues:

public class MyNewAPI extends AbstractAPI {
    @Override
    public void init() {
        // empty
    }

    public void handleRequest(JsonObject request) {
        var id = request.getLong("id");
        var item = ConfigStore.getStore().getItem(id);
        item.put("status", "active");
    }
}

List all issues and show corrected code.""",
        expected_patterns=[r"issue|problem|missing", r"null|check|validation"],
        forbidden_patterns=[r"<tool_response>"]
    ),
    TestCase(
        id="C2", category="CODE_REVIEW", name="ConfigStore Review",
        system_prompt="Review this Motadata ConfigStore implementation.",
        user_prompt="""Is this ConfigStore correct?

public class TestConfigStore extends AbstractConfigStore {
    public JsonObject getItem(long id) {
        return db.query("SELECT * FROM test WHERE id = " + id);
    }
}

What's wrong and how to fix it?""",
        expected_patterns=[r"SQL|injection|prepared|parameter", r"fix|correct"],
        forbidden_patterns=[r"<tool_response>"]
    ),

    # Direct Reasoning (No Tools)
    TestCase(
        id="D1", category="DIRECT_REASONING", name="Memory Leak Analysis",
        system_prompt="Analyze this code for memory issues. Reason directly, NO tools.",
        user_prompt="""Check this code for memory leaks:

public class CacheManager {
    private static Map<String, Object> cache = new HashMap<>();

    public void addToCache(String key, Object value) {
        cache.put(key, value);
    }

    public Object getFromCache(String key) {
        return cache.get(key);
    }
}

Any memory leak risks? How to fix?""",
        expected_patterns=[r"memory|leak|unbounded|grow", r"eviction|limit|clear|TTL"],
        forbidden_patterns=[r"<tool_response>", r"grep", r"run_command"]
    ),
]


def generate_report(results: List[TestResult]) -> Dict[str, Any]:
    """Generate comprehensive evaluation report"""

    # Group by category
    by_category = {}
    for r in results:
        if r.category not in by_category:
            by_category[r.category] = []
        by_category[r.category].append(r)

    # Calculate metrics
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.passed)
    avg_score = sum(r.score for r in results) / total_tests if total_tests > 0 else 0
    tool_obsession_rate = sum(1 for r in results if r.has_tool_calls) / total_tests * 100
    repetition_rate = sum(1 for r in results if r.has_repetition) / total_tests * 100
    avg_response_time = sum(r.response_time_ms for r in results) / total_tests if total_tests > 0 else 0

    # Category breakdown
    category_scores = {}
    for cat, cat_results in by_category.items():
        category_scores[cat] = {
            "total": len(cat_results),
            "passed": sum(1 for r in cat_results if r.passed),
            "avg_score": sum(r.score for r in cat_results) / len(cat_results),
            "pass_rate": sum(1 for r in cat_results if r.passed) / len(cat_results) * 100
        }

    # Identify critical issues
    critical_issues = []
    if tool_obsession_rate > 30:
        critical_issues.append(f"HIGH TOOL OBSESSION: {tool_obsession_rate:.1f}% of responses contain tool calls")
    if repetition_rate > 20:
        critical_issues.append(f"REPETITION LOOPS: {repetition_rate:.1f}% of responses have repetition issues")
    if avg_score < 3:
        critical_issues.append(f"LOW QUALITY: Average score {avg_score:.2f}/5 is below threshold")

    report = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "model_endpoint": API_URL,
            "total_tests": total_tests
        },
        "summary": {
            "overall_pass_rate": f"{passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)",
            "average_score": f"{avg_score:.2f}/5",
            "tool_obsession_rate": f"{tool_obsession_rate:.1f}%",
            "repetition_rate": f"{repetition_rate:.1f}%",
            "avg_response_time_ms": int(avg_response_time),
            "critical_issues": critical_issues
        },
        "category_breakdown": category_scores,
        "detailed_results": [asdict(r) for r in results],
        "recommendations": generate_recommendations(results, category_scores)
    }

    return report

def generate_recommendations(results: List[TestResult], category_scores: Dict) -> List[str]:
    """Generate actionable recommendations based on results"""
    recs = []

    # Check tool obsession
    tool_issues = sum(1 for r in results if r.has_tool_calls)
    if tool_issues > 0:
        recs.append({
            "priority": "HIGH",
            "issue": "Tool Obsession",
            "description": f"{tool_issues} tests showed tool/XML output instead of direct answers",
            "fix": "Add 50-100 Dataset D examples (direct reasoning, no tools). Update system prompt to explicitly forbid tool calls."
        })

    # Check repetition
    rep_issues = sum(1 for r in results if r.has_repetition)
    if rep_issues > 0:
        recs.append({
            "priority": "HIGH",
            "issue": "Repetition Loops",
            "description": f"{rep_issues} tests showed repeated content patterns",
            "fix": "Review training data for duplicates. Add repetition_penalty=1.2 to generation config."
        })

    # Check category-specific issues
    for cat, scores in category_scores.items():
        if scores["pass_rate"] < 50:
            recs.append({
                "priority": "MEDIUM",
                "issue": f"Low {cat} Performance",
                "description": f"Only {scores['pass_rate']:.1f}% pass rate in {cat}",
                "fix": f"Add more training examples for {cat} category"
            })

    # Check if RAG is needed
    knowledge_cats = [c for c in category_scores if "KNOWLEDGE" in c or "MULTIFILE" in c]
    if knowledge_cats:
        avg_knowledge = sum(category_scores[c]["avg_score"] for c in knowledge_cats) / len(knowledge_cats)
        if avg_knowledge < 3.5:
            recs.append({
                "priority": "HIGH",
                "issue": "Knowledge Gaps / Hallucinations",
                "description": "Model struggling with factual accuracy",
                "fix": "Implement RAG with Qdrant to ground responses in actual codebase"
            })

    return recs

def print_report(report: Dict):
    """Print formatted report to console"""
    print("\n" + "="*70)
    print("   MOTADATA FINETUNED MODEL EVALUATION REPORT")
    print("="*70)
    print(f"\nGenerated: {report['metadata']['generated_at']}")
    print(f"Endpoint: {report['metadata']['model_endpoint']}")

    print("\n" + "-"*70)
    print("SUMMARY")
    print("-"*70)
    s = report["summary"]
    print(f"  Overall Pass Rate:    {s['overall_pass_rate']}")
    print(f"  Average Score:        {s['average_score']}")
    print(f"  Tool Obsession Rate:  {s['tool_obsession_rate']}")
    print(f"  Repetition Rate:      {s['repetition_rate']}")
    print(f"  Avg Response Time:    {s['avg_response_time_ms']}ms")

    if s["critical_issues"]:
        print(f"\n  ⚠️  CRITICAL ISSUES:")
        for issue in s["critical_issues"]:
            print(f"      • {issue}")

    print("\n" + "-"*70)
    print("CATEGORY BREAKDOWN")
    print("-"*70)
    for cat, scores in report["category_breakdown"].items():
        status = "✅" if scores["pass_rate"] >= 70 else "⚠️" if scores["pass_rate"] >= 40 else "❌"
        print(f"  {status} {cat}: {scores['passed']}/{scores['total']} passed, avg score: {scores['avg_score']:.2f}/5")

    print("\n" + "-"*70)
    print("DETAILED RESULTS")
    print("-"*70)
    for r in report["detailed_results"]:
        status = "✅" if r["passed"] else "❌"
        print(f"  {status} [{r['test_id']}] {r['name']}: {r['score']}/5")
        if r["issues"]:
            for issue in r["issues"]:
                print(f"       ⚠️ {issue}")

    print("\n" + "-"*70)
    print("RECOMMENDATIONS")
    print("-"*70)
    for rec in report["recommendations"]:
        print(f"\n  [{rec['priority']}] {rec['issue']}")
        print(f"      Problem: {rec['description']}")
        print(f"      Fix: {rec['fix']}")

    print("\n" + "="*70)


def main():
    print("🚀 Starting Motadata Finetuned Model Evaluation...")
    print(f"   Running {len(TEST_CASES)} test cases\n")

    results = []
    for i, test in enumerate(TEST_CASES, 1):
        print(f"[{i}/{len(TEST_CASES)}] Running: {test.name}...", end=" ", flush=True)
        result = run_test(test)
        results.append(result)
        status = "✅" if result.passed else "❌"
        print(f"{status} Score: {result.score}/5 ({result.response_time_ms}ms)")

    # Generate report
    report = generate_report(results)

    # Save to file
    report_path = "/home/harshil/Harshil-PoCs/Finetuning/finetuning_evaluation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n📄 Report saved to: {report_path}")

    # Print to console
    print_report(report)

    return report


if __name__ == "__main__":
    main()


