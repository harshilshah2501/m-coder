import os
import yaml
from pathlib import Path
from task_executor import TaskExecutor
from task_loader import TaskLoader

def verify_task4():
    loader = TaskLoader("evaluation/motadata_tasks")
    task_path = Path("evaluation/motadata_tasks/tasks/refactored_snmp.yaml")
    task = loader.load_task_yaml(task_path)
    
    executor = TaskExecutor()
    print(f"Executing Task: {task.task_id}")
    result = executor.execute_task(task, verbose=True)
    
    print("-" * 50)
    print(f"Task ID: {task.task_id}")
    print(f"Status:  {'PASS ✅' if result.status == 'PASS' else 'FAIL ❌'}")
    print(f"Verification Exit Code: {result.verification_exit_code}")
    
    if result.status != 'PASS':
        print("\nVerification Output (last 1000 chars):")
        print(result.verification_output[-1000:] if result.verification_output else "No output")

if __name__ == "__main__":
    verify_task4()
