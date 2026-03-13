#!/usr/bin/env python3
"""
Phase-C CPT Completion Probe
Tests if CPT model completes Motadata code better than base Qwen model
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple

# Test probes - raw code contexts without instructions
PROBES = [
    {
        "id": "probe_01_event_router",
        "category": "Class/Method Completion",
        "prompt": """public class EventRouter {

    private final EventBus eventBus;

    public EventRouter(EventBus eventBus) {
        this.eventBus = eventBus;
    }

    public void route(Event event) {
        // COMPLETE""",
    },
    {
        "id": "probe_02_bootstrap",
        "category": "Registration/Wiring",
        "prompt": """public class BootstrapSecondary {

    public void start() {
        // COMPLETE""",
    },
    {
        "id": "probe_03_event_handler",
        "category": "Handler/Processor Logic",
        "prompt": """public class LocalEventChangeNotificationHandler {

    @Override
    public void handle(Event event) {
        // COMPLETE""",
    },
    {
        "id": "probe_04_vertx_async",
        "category": "Async/Vertx Patterns",
        "prompt": """vertx.executeBlocking(promise -> {
    // COMPLETE""",
    },
    {
        "id": "probe_05_service_registry",
        "category": "Registration/Wiring",
        "prompt": """public class ServiceRegistry {
    
    private Map<String, Service> services = new HashMap<>();
    
    public void register(String name, Service service) {
        // COMPLETE""",
    },
    {
        "id": "probe_06_event_processor",
        "category": "Handler/Processor Logic",
        "prompt": """public class EventProcessor {
    
    private EventQueue queue;
    
    public void processNext() {
        // COMPLETE""",
    },
    {
        "id": "probe_07_config_loader",
        "category": "Class/Method Completion",
        "prompt": """public class ConfigurationLoader {
    
    private Properties config;
    
    public void loadFromFile(String path) {
        // COMPLETE""",
    },
    {
        "id": "probe_08_message_handler",
        "category": "Handler/Processor Logic",
        "prompt": """public class MessageHandler implements Handler<Message> {
    
    @Override
    public void handle(Message message) {
        // COMPLETE""",
    },
    {
        "id": "probe_09_async_callback",
        "category": "Async/Vertx Patterns",
        "prompt": """vertx.eventBus().consumer("events", message -> {
    // COMPLETE""",
    },
    {
        "id": "probe_10_initialization",
        "category": "Registration/Wiring",
        "prompt": """public class SystemInitializer {
    
    private List<Component> components;
    
    public void initialize() {
        // COMPLETE""",
    },
]

# Generation settings - deterministic
GEN_CONFIG = {
    "temperature": 0.2,
    "top_p": 0.95,
    "max_new_tokens": 200,
    "do_sample": False,
    "pad_token_id": None,  # Will be set from tokenizer
}

def load_base_model(device="cuda"):
    """Load base Qwen model"""
    print("📦 Loading base model: Qwen/Qwen2.5-Coder-14B-Instruct")
    model_name = "Qwen/Qwen2.5-Coder-14B-Instruct"
    
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    return model, tokenizer

def load_cpt_model(base_model_path, cpt_adapter_path, device="cuda"):
    """Load CPT fine-tuned model"""
    print(f"📦 Loading CPT model from: {cpt_adapter_path}")
    
    tokenizer = AutoTokenizer.from_pretrained(base_model_path, trust_remote_code=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    
    model = PeftModel.from_pretrained(base_model, cpt_adapter_path)
    model = model.merge_and_unload()
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    return model, tokenizer

def generate_completion(model, tokenizer, prompt: str, config: dict) -> str:
    """Generate completion for a probe"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    gen_config = config.copy()
    gen_config["pad_token_id"] = tokenizer.pad_token_id
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            **gen_config
        )
    
    full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    completion = full_output[len(prompt):]
    
    return completion

def score_completion(completion: str, probe_id: str) -> Dict[str, int]:
    """
    Score completion based on Phase-C criteria
    
    Returns:
        dict with scores for domain_fit, structure, brevity, hallucination
    """
    scores = {
        "domain_fit": 0,      # 0-2: Motadata-specific terms
        "structure": 0,       # 0-2: Correct method calls, control flow
        "brevity": 0,         # 0-1: Short and decisive
        "hallucination": 0,   # 0 or -2: Penalize invented APIs
    }
    
    # Domain-specific indicators for Motadata
    domain_terms = [
        "EventBus", "Event", "Motadata", "Handler", "Processor",
        "vertx", "eventBus", "queue", "message", "service"
    ]
    
    # Hallucination indicators (frameworks not in codebase)
    hallucination_terms = [
        "Spring", "spring", "@Autowired", "@Component",
        "Netty", "netty", "Guice", "inject"
    ]
    
    completion_lower = completion.lower()
    
    # Score domain fit
    domain_hits = sum(1 for term in domain_terms if term.lower() in completion_lower)
    if domain_hits >= 3:
        scores["domain_fit"] = 2
    elif domain_hits >= 1:
        scores["domain_fit"] = 1
    
    # Score structure (basic heuristics)
    has_method_calls = "(" in completion and ")" in completion
    has_control_flow = any(kw in completion for kw in ["if", "for", "while", "try"])
    
    if has_method_calls and has_control_flow:
        scores["structure"] = 2
    elif has_method_calls or has_control_flow:
        scores["structure"] = 1
    
    # Score brevity (shorter is better for completion)
    lines = [l for l in completion.split("\n") if l.strip()]
    if len(lines) <= 5:
        scores["brevity"] = 1
    
    # Penalize hallucinations
    hallucination_hits = sum(1 for term in hallucination_terms if term in completion)
    if hallucination_hits > 0:
        scores["hallucination"] = -2
    
    return scores

def run_phase_c_validation(output_dir: str):
    """Run complete Phase-C validation"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load models
    print("\n" + "="*80)
    print("🚀 Phase-C CPT Completion Probe - Starting")
    print("="*80 + "\n")
    
    base_model, base_tokenizer = load_base_model()
    
    cpt_model, cpt_tokenizer = load_cpt_model(
        base_model_path="Qwen/Qwen2.5-Coder-14B-Instruct",
        cpt_adapter_path="/home/harshil/Harshil-PoCs/models/motadata-cpt-checkpoint/checkpoint-2000"
    )
    
    results = []
    
    print("\n" + "="*80)
    print("🧪 Running Probes")
    print("="*80 + "\n")
    
    for i, probe in enumerate(PROBES, 1):
        probe_id = probe["id"]
        category = probe["category"]
        prompt = probe["prompt"]
        
        print(f"[{i}/{len(PROBES)}] {probe_id} ({category})")
        
        # Generate base completion
        print("  → Base model generating...")
        base_completion = generate_completion(base_model, base_tokenizer, prompt, GEN_CONFIG)
        
        # Generate CPT completion
        print("  → CPT model generating...")
        cpt_completion = generate_completion(cpt_model, cpt_tokenizer, prompt, GEN_CONFIG)
        
        # Score both
        base_scores = score_completion(base_completion, probe_id)
        cpt_scores = score_completion(cpt_completion, probe_id)
        
        # Calculate totals
        base_total = sum(base_scores.values())
        cpt_total = sum(cpt_scores.values())
        
        winner = "CPT" if cpt_total > base_total else ("BASE" if base_total > cpt_total else "TIE")
        
        print(f"  → Scores: BASE={base_total}, CPT={cpt_total} [{winner}]")
        
        # Save outputs
        with open(f"{output_dir}/{probe_id}_base.txt", "w") as f:
            f.write(base_completion)
        
        with open(f"{output_dir}/{probe_id}_cpt.txt", "w") as f:
            f.write(cpt_completion)
        
        result = {
            "probe_id": probe_id,
            "category": category,
            "prompt": prompt,
            "base_completion": base_completion,
            "cpt_completion": cpt_completion,
            "base_scores": base_scores,
            "cpt_scores": cpt_scores,
            "base_total": base_total,
            "cpt_total": cpt_total,
            "winner": winner,
        }
        
        results.append(result)
        print()
    
    # Generate report
    print("\n" + "="*80)
    print("📊 Phase-C Results Summary")
    print("="*80 + "\n")
    
    cpt_wins = sum(1 for r in results if r["winner"] == "CPT")
    base_wins = sum(1 for r in results if r["winner"] == "BASE")
    ties = sum(1 for r in results if r["winner"] == "TIE")
    
    cpt_win_rate = (cpt_wins / len(results)) * 100
    
    print(f"CPT Wins:  {cpt_wins}/{len(results)} ({cpt_win_rate:.1f}%)")
    print(f"Base Wins: {base_wins}/{len(results)}")
    print(f"Ties:      {ties}/{len(results)}")
    print()
    
    # Category breakdown
    print("Category Breakdown:")
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"cpt_wins": 0, "total": 0}
        categories[cat]["total"] += 1
        if r["winner"] == "CPT":
            categories[cat]["cpt_wins"] += 1
    
    for cat, stats in categories.items():
        win_rate = (stats["cpt_wins"] / stats["total"]) * 100
        print(f"  {cat}: {stats['cpt_wins']}/{stats['total']} ({win_rate:.0f}%)")
    
    print()
    
    # Pass/Fail decision
    phase_c_passed = cpt_win_rate >= 70
    
    print("="*80)
    if phase_c_passed:
        print("✅ PHASE-C PASSED")
        print(f"   CPT wins on {cpt_win_rate:.1f}% of probes (≥70% required)")
    else:
        print("❌ PHASE-C FAILED")
        print(f"   CPT wins on {cpt_win_rate:.1f}% of probes (<70% required)")
    print("="*80)
    print()
    
    # Save detailed report
    report = {
        "timestamp": datetime.now().isoformat(),
        "phase": "Phase-C",
        "test_type": "Completion Probe",
        "models": {
            "base": "Qwen/Qwen2.5-Coder-14B-Instruct",
            "cpt": "motadata-cpt-checkpoint/checkpoint-2000"
        },
        "generation_config": GEN_CONFIG,
        "summary": {
            "total_probes": len(results),
            "cpt_wins": cpt_wins,
            "base_wins": base_wins,
            "ties": ties,
            "cpt_win_rate": cpt_win_rate,
            "phase_c_passed": phase_c_passed,
        },
        "category_breakdown": categories,
        "detailed_results": results,
    }
    
    report_path = f"{output_dir}/phase_c_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"📄 Detailed report saved: {report_path}")
    
    # Save comparison markdown
    comparison_md = generate_comparison_markdown(results)
    comparison_path = f"{output_dir}/phase_c_comparison.md"
    with open(comparison_path, "w") as f:
        f.write(comparison_md)
    
    print(f"📄 Comparison report saved: {comparison_path}")
    
    return report

def generate_comparison_markdown(results: List[Dict]) -> str:
    """Generate human-readable comparison markdown"""
    
    lines = [
        "# Phase-C Completion Probe - Detailed Comparison",
        "",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
    ]
    
    cpt_wins = sum(1 for r in results if r["winner"] == "CPT")
    base_wins = sum(1 for r in results if r["winner"] == "BASE")
    ties = sum(1 for r in results if r["winner"] == "TIE")
    cpt_win_rate = (cpt_wins / len(results)) * 100
    
    lines.extend([
        f"- **CPT Wins**: {cpt_wins}/{len(results)} ({cpt_win_rate:.1f}%)",
        f"- **Base Wins**: {base_wins}/{len(results)}",
        f"- **Ties**: {ties}/{len(results)}",
        f"- **Result**: {'✅ PASSED' if cpt_win_rate >= 70 else '❌ FAILED'}",
        "",
        "---",
        "",
    ])
    
    for result in results:
        lines.extend([
            f"## {result['probe_id']}",
            "",
            f"**Category**: {result['category']}",
            "",
            f"**Winner**: {result['winner']}",
            "",
            "### Prompt",
            "",
            "```java",
            result['prompt'],
            "```",
            "",
            "### Base Model Output",
            "",
            f"**Scores**: Domain={result['base_scores']['domain_fit']}, Structure={result['base_scores']['structure']}, Brevity={result['base_scores']['brevity']}, Hallucination={result['base_scores']['hallucination']} | **Total={result['base_total']}**",
            "",
            "```java",
            result['base_completion'],
            "```",
            "",
            "### CPT Model Output",
            "",
            f"**Scores**: Domain={result['cpt_scores']['domain_fit']}, Structure={result['cpt_scores']['structure']}, Brevity={result['cpt_scores']['brevity']}, Hallucination={result['cpt_scores']['hallucination']} | **Total={result['cpt_total']}**",
            "",
            "```java",
            result['cpt_completion'],
            "```",
            "",
            "---",
            "",
        ])
    
    return "\n".join(lines)

if __name__ == "__main__":
    output_dir = "/home/harshil/Harshil-PoCs/evaluation/phase_c_results"
    report = run_phase_c_validation(output_dir)
    
    print("\n✅ Phase-C validation complete!")
