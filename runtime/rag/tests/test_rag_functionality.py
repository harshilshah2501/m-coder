import requests
import json
import time
import os
from datetime import datetime

# Configuration
API_URL = "http://localhost:8081/v1/chat/completions"
OUTPUT_FILE = "FUNCTIONAL_TEST_REPORT.txt"
MAX_TOKENS = 1024
TEMPERATURE = 0.6
MODEL = "motadata-coder"

TEST_CASES = [
    # 1. ANALYZING (RCA_DEBUGGING)
    {
        "category": "ANALYZING",
        "name": "R1: NullPointer Analysis",
        "prompt": "Analyze this NPE: java.lang.NullPointerException at com.mindarray.api.Discovery.handleDiscoveryRequest",
        "expected_keywords": ["map", "check", "null", "if"]
    },
    {
        "category": "ANALYZING",
        "name": "R2: Vert.x Timeout",
        "prompt": "Error: TimeoutException in AgentCacheStore.refreshCache. Address: com.mindarray.agent.cache. Root cause?",
        "expected_keywords": ["eventbus", "timeout", "worker", "consumer"]
    },

    # 2. CODING (TYPE_B_MULTIFILE)
    {
        "category": "CODING",
        "name": "B1: New API Feature",
        "prompt": "Create CorrectionProfile API. List ALL required files.",
        "expected_keywords": ["CorrectionProfile", "extends AbstractAPI", "CorrectionProfileConfigStore", "APIRouter"]
    },
    {
        "category": "CODING",
        "name": "B2: New Monitor Plugin",
        "prompt": "Add a new NetApp storage monitor plugin.",
        "expected_keywords": ["implements MonitorPlugin", "plugin.json", "metric", "collect"]
    },

    # 3. REVIEWING (CODE_REVIEW)
    {
        "category": "REVIEWING",
        "name": "C1: Anti-Pattern Detection",
        "prompt": "Review this: public class MyAPI { @Autowired private Service s; }",
        "expected_keywords": ["autowired", "spring", "constructor injection", "serviceregistry"]
    },
    {
        "category": "REVIEWING",
        "name": "C2: Security/SQLi",
        "prompt": "Review: db.query('SELECT * FROM t WHERE id=' + id)",
        "expected_keywords": ["injection", "prepared", "jsonarray", "vulnerability"]
    },

    # 4. DESIGN/ARCHITECTURE (TYPE_A_KNOWLEDGE)
    {
        "category": "ARCHITECTURE",
        "name": "K1: AbstractConfigStore Knowledge",
        "prompt": "What is AbstractConfigStore?",
        "expected_keywords": ["base class", "config", "persistence", "store"]
    },
    {
        "category": "ARCHITECTURE",
        "name": "K5: Database Constants",
        "prompt": "Where are database constants defined?",
        "expected_keywords": ["DBConstants", "class"]
    }
]

def run_test(test_case):
    print(f"Running: [{test_case['category']}] {test_case['name']}...")
    
    start_time = time.time()
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": test_case['prompt']}],
        "temperature": TEMPERATURE, # Use configured temperature
        "max_tokens": 1024
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        elapsed = (time.time() - start_time) * 1000
        content = result['choices'][0]['message']['content']
        rag_context = result.get('rag_context', {})
        
        # Grading
        lower_content = content.lower()
        missing_keywords = [k for k in test_case['expected_keywords'] if k.lower() not in lower_content]
        passed = len(missing_keywords) == 0 and len(content) > 50
        
        return {
            "test_id": test_case['name'],
            "category": test_case['category'],
            "passed": passed,
            "response_time_ms": int(elapsed),
            "content": content,
            "rag_context": rag_context,
            "missing_keywords": missing_keywords
        }
        
    except Exception as e:
        print(f"FAILED: {e}")
        return {
            "test_id": test_case['name'],
            "category": test_case['category'],
            "passed": False,
            "response_time_ms": 0,
            "content": f"ERROR: {str(e)}",
            "rag_context": {},
            "missing_keywords": []
        }

def generate_report(results):
    report_lines = []
    report_lines.append("="*80)
    report_lines.append(f"MOTADATA AI FUNCTIONAL TEST REPORT - {datetime.now().isoformat()}")
    report_lines.append("="*80)
    
    # Summary
    total = len(results)
    passed = sum(1 for r in results if r['passed'])
    pass_rate = (passed / total) * 100
    
    report_lines.append(f"\nSUMMARY:")
    report_lines.append(f"Total Tests: {total}")
    report_lines.append(f"Passed:      {passed}")
    report_lines.append(f"Pass Rate:   {pass_rate:.1f}%")
    report_lines.append("-" * 80)
    
    # Detailed Results
    for res in results:
        status = "✅ PASS" if res['passed'] else "❌ FAIL"
        report_lines.append(f"\n{status} | [{res['category']}] {res['test_id']}")
        report_lines.append(f"Time: {res['response_time_ms']}ms")
        
        if not res['passed']:
            if res['missing_keywords']:
                report_lines.append(f"Missing Keywords: {res['missing_keywords']}")
            if len(res['content']) < 50:
                report_lines.append("Issue: Response too short")
        
        report_lines.append("Response Preview:")
        preview = res['content'][:200].replace('\n', ' ') + "..."
        report_lines.append(f"  {preview}")
        
        if res.get('rag_context'):
            grounded = res['rag_context'].get('grounded', False)
            sources = len(res['rag_context'].get('sources', []))
            report_lines.append(f"RAG: Grounded={grounded}, Sources={sources}")
            
    report_lines.append("\n" + "="*80)
    
    with open(OUTPUT_FILE, 'w') as f:
        f.write('\n'.join(report_lines))
        
    print(f"\nReport written to {OUTPUT_FILE}")

def main():
    results = []
    for test in TEST_CASES:
        results.append(run_test(test))
    generate_report(results)

if __name__ == "__main__":
    main()
