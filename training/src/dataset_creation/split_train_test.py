# save as split_train_test.py and run with: python3 split_train_test.py
import random
import json

INPUT = "/home/harshil/Harshil-PoCs/Finetuning/full_training_data_shuffled.jsonl"
TRAIN_OUT = "/home/harshil/Harshil-PoCs/Finetuning/full_training_train.jsonl"
TEST_OUT = "/home/harshil/Harshil-PoCs/Finetuning/full_training_test.jsonl"
TEST_RATIO = 0.2  # 20% test

def main():
    random.seed(42)
    total = 0
    train_count = 0
    test_count = 0

    with open(INPUT, "r", encoding="utf-8") as fin, \
         open(TRAIN_OUT, "w", encoding="utf-8") as ftrain, \
         open(TEST_OUT, "w", encoding="utf-8") as ftest:
        for line in fin:
            total += 1
            if random.random() < TEST_RATIO:
                ftest.write(line)
                test_count += 1
            else:
                ftrain.write(line)
                train_count += 1

    print(f"Total: {total}, Train: {train_count}, Test: {test_count}")

if __name__ == "__main__":
    main()
