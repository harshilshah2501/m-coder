import yaml
import os

task_path = '/home/harshil/Harshil-PoCs/RAG-Datastore/evaluation/motadata_tasks/tasks/topology_testcases_parallelism.yaml'
with open(task_path) as f:
    task = yaml.safe_load(f)

setup_script = task.get('setup_script', '')
with open('/tmp/task3_setup.sh', 'w') as f:
    f.write(setup_script)

print(f"Extracted setup script to /tmp/task3_setup.sh ({len(setup_script)} bytes)")
