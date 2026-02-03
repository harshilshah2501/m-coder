#!/usr/bin/env python3
"""
V15 Post-Fine-tuning Evaluation
Comprehensive evaluation including quantitative metrics and qualitative analysis
"""

import json
import torch
from pathlib import Path
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import numpy as np
from datetime import datetime

# Configuration
MODEL_PATH = "training/results/v15_finetuned"
TEST_FILE = "datasets/splits/test.jsonl"
OUTPUT_DIR = "training/results/v15_evaluation"

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

def load_finetuned_model():
    """Load the fine-tuned model with LoRA adapter"""
    print("🔧 Loading base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        "Qwen/Qwen2.5-Coder-7B-Instruct",
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    
    print("🔧 Loading LoRA adapter...")
    model = PeftModel.from_pretrained(base_model, MODEL_PATH)
    model = model.merge_and_unload()
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    
    return model, tokenizer

def compute_test_loss(model, tokenizer, test_file):
    """Compute loss on test dataset"""
    print("\n📊 Computing test loss...")
    test_data = load_dataset("json", data_files=test_file)["train"]
    
    total_loss = 0
    num_batches = 0
    
    for i, example in enumerate(test_data):
        if i >= 100:  # Sample 100 examples for speed
            break
            
        messages = example["messages"]
        text = tokenizer.apply_chat_template(messages, tokenize=False)
        
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=4096)
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs, labels=inputs["input_ids"])
            total_loss += outputs.loss.item()
        
        num_batches += 1
        if (i + 1) % 20 == 0:
            print(f"  Processed {i + 1} examples...")
    
    avg_loss = total_loss / num_batches
    perplexity = np.exp(avg_loss)
    
    return {"test_loss": avg_loss, "perplexity": perplexity}

def sample_qualitative_analysis(model, tokenizer, test_file):
    """Generate sample predictions for qualitative analysis"""
    print("\n🎯 Running qualitative analysis...")
    test_data = load_dataset("json", data_files=test_file)["train"]
    
    samples = []
    categories = {}
    
    for i, example in enumerate(test_data):
        if i >= 20:  # Sample 20 examples
            break
        
        category = example.get("metadata", {}).get("category", "unknown")
        if category not in categories:
            categories[category] = []
        
        messages = example["messages"]
        user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
        
        # Generate response
        inputs = tokenizer(user_msg, return_tensors="pt", truncation=True, max_length=2048)
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        sample = {
            "category": category,
            "prompt": user_msg[:200],
            "response": response[:500],
            "expected": messages[-1]["content"][:500] if messages[-1]["role"] == "assistant" else ""
        }
        
        samples.append(sample)
        categories[category].append(sample)
    
    return samples, categories

def main():
    print("="*80)
    print("V15 POST-FINE-TUNING EVALUATION")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Load model
    model, tokenizer = load_finetuned_model()
    
    # Compute metrics
    metrics = compute_test_loss(model, tokenizer, TEST_FILE)
    
    # Qualitative analysis
    samples, categories = sample_qualitative_analysis(model, tokenizer, TEST_FILE)
    
    # Compile report
    report = {
        "timestamp": datetime.now().isoformat(),
        "model_path": MODEL_PATH,
        "quantitative_metrics": metrics,
        "qualitative_samples": samples,
        "category_distribution": {cat: len(samples) for cat, samples in categories.items()}
    }
    
    # Save report
    report_path = Path(OUTPUT_DIR) / "v15_evaluation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "="*80)
    print("✅ EVALUATION COMPLETE")
    print("="*80)
    print(f"\n📊 Quantitative Metrics:")
    print(f"  Test Loss: {metrics['test_loss']:.4f}")
    print(f"  Perplexity: {metrics['perplexity']:.2f}")
    print(f"\n📄 Report saved to: {report_path}")

if __name__ == "__main__":
    main()

