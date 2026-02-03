import json
import requests
import time
import os

BENCHMARK_FILE = '/home/harshil/Harshil-PoCs/RAG-Datastore/benchmark_jira.jsonl'
RESULTS_FILE = '/home/harshil/Harshil-PoCs/RAG-Datastore/benchmark_results.jsonl'
API_URL = "http://localhost:8081/v1/chat/completions"

def run_benchmark(limit=5):
    print(f"Running benchmark on first {limit} entries...")
    
    results = []
    
    try:
        with open(BENCHMARK_FILE, 'r') as infile:
            lines = infile.readlines()
    except FileNotFoundError:
        print(f"Benchmark file not found: {BENCHMARK_FILE}")
        return

    # Process only the first 'limit' entries
    for i, line in enumerate(lines[:limit]):
        entry = json.loads(line)
        task_id = entry['id']
        instruction = entry['task_description']
        
        print(f"Processing Task {i+1}/{limit}: {task_id}")
        
        # Construct prompt
        # We provide the file content and ask the agent to perform the task
        prompt = f"Task: {instruction}\n\nContext Files:\n"
        for f in entry['files']:
            prompt += f"File: {f['path']}\nContent:\n```java\n{f['content_before']}\n```\n\n"
        
        prompt += "Please provide the code changes required to complete the task. Output the modified code."

        payload = {
            "model": "motadata-coder",
            "messages": [
                {"role": "system", "content": "You are an expert Java developer. You are given a task and some context files. You must modify the code to complete the task."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0
        }
        
        start_time = time.time()
        try:
            response = requests.post(API_URL, json=payload, timeout=120)
            response.raise_for_status()
            result_data = response.json()
            generated_text = result_data['choices'][0]['message']['content']
            
            duration = time.time() - start_time
            print(f"  Success ({duration:.2f}s)")
            
            result_entry = {
                "id": task_id,
                "instruction": instruction,
                "generated_response": generated_text,
                "duration": duration,
                "status": "success"
            }
            
        except Exception as e:
            print(f"  Failed: {e}")
            result_entry = {
                "id": task_id,
                "instruction": instruction,
                "error": str(e),
                "status": "error"
            }
            
        results.append(result_entry)
        
        # Save intermediate results
        with open(RESULTS_FILE, 'a') as outfile:
            outfile.write(json.dumps(result_entry) + '\n')

    print(f"Benchmark run complete. Results saved to {RESULTS_FILE}")

if __name__ == "__main__":
    # Check if API is up
    try:
        requests.get("http://localhost:8081/health", timeout=2)
        print("RAG API is reachable.")
    except:
        print("Warning: RAG API might not be running at http://localhost:8081. Please start it first.")
    
    run_benchmark(limit=2) # Run a small batch first
