import json, re

SECRET_REGEX = re.compile(
    r"(api[_-]?key|password|secret|token)\s*[:=]\s*[\"'][^\"']+",
    re.IGNORECASE
)

clean = 0
removed = 0

with open("/home/harshil/Harshil-PoCs/datasets/cpt/cpt_dataset.jsonl") as fin, open("/home/harshil/Harshil-PoCs/datasets/cpt/cpt_dataset_clean.jsonl", "w") as fout:
    for line in fin:
        obj = json.loads(line)
        if SECRET_REGEX.search(obj["text"]):
            removed += 1
            continue
        fout.write(json.dumps(obj) + "\n")
        clean += 1

print(f"Removed samples: {removed}")
print(f"Remaining samples: {clean}")
