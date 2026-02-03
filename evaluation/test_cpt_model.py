#!/usr/bin/env python3
"""
Phase-C: CPT Completion Probe

Objective: Does the CPT model complete Motadata code more like a Motadata 
engineer than the base Qwen model?

Test Design:
- 10 minimal prompts (pure code, no instructions)
- 4 categories: Class/Method, Registration, Handler, Async
- Compare Base Qwen vs CPT model deterministically
- Score: Domain tokens, Structure, Brevity, Hallucinations

Pass Condition: CPT wins ≥70% of probes
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from typing import Dict, List, Tuple


# 10 Frozen Prompts (Pure code context, cursor-style completion)
FROZEN_PROBES = [
    # Category A: Class/Method Completion (3 probes)
    {
        "id": "probe_01",
        "category": "Class/Method",
        "name": "EventRouter.route",
        "prompt": """public class EventRouter {

    private final EventBus eventBus;

    public EventRouter(EventBus eventBus) {
        this.eventBus = eventBus;
    }

    public void route(Event event) {
        // COMPLETE
""",
        "motadata_tokens": ["eventBus.publish", "EventBusConstants", "JsonObject", "vertx"],
        "alien_tokens": ["Spring", "ApplicationEvent", "@Autowired", "Guava"]
    },
    {
        "id": "probe_02",
        "category": "Class/Method",
        "name": "AbstractAPI Extension",
        "prompt": """public class DiscoveryAPI extends AbstractAPI {
    
    @Override
    public void initialize() {
        // COMPLETE
""",
        "motadata_tokens": ["APIRouter", "ConfigStore", "eventBus", "router"],
        "alien_tokens": ["@RestController", "@RequestMapping", "SpringBoot", "@Bean"]
    },
    {
        "id": "probe_03",
        "category": "Class/Method",
        "name": "ConfigStore Getter",
        "prompt": """public class ServiceConfig extends AbstractConfigStore {
    
    public String getServiceUrl() {
        // COMPLETE
""",
        "motadata_tokens": ["get(", "getString(", "configStore", "AbstractConfigStore"],
        "alien_tokens": ["@Value", "Environment", "application.properties", "@ConfigurationProperties"]
    },
    
    # Category B: Registration/Wiring (2 probes)
    {
        "id": "probe_04",
        "category": "Registration/Wiring",
        "name": "Bootstrap Startup",
        "prompt": """public class BootstrapSecondary {
    
    public void start() {
        // COMPLETE
""",
        "motadata_tokens": ["vertx", "deploy", "APIRouter", "eventBus"],
        "alien_tokens": ["SpringApplication", "@SpringBootApplication", "ApplicationContext"]
    },
    {
        "id": "probe_05",
        "category": "Registration/Wiring",
        "name": "APIRouter Registration",
        "prompt": """public void registerAPIs(APIRouter router) {
    // COMPLETE
""",
        "motadata_tokens": ["router.register", "AbstractAPI", "API", "endpoint"],
        "alien_tokens": ["@Bean", "@Configuration", "DispatcherServlet", "@Component"]
    },
    
    # Category C: Handler/Processor Logic (3 probes)
    {
        "id": "probe_06",
        "category": "Handler/Processor",
        "name": "LocalEventChangeNotificationHandler",
        "prompt": """public class LocalEventChangeNotificationHandler {
    
    @Override
    public void handle(Event event) {
        // COMPLETE
""",
        "motadata_tokens": ["event.get", "JsonObject", "EventBusConstants", "notification"],
        "alien_tokens": ["@EventListener", "@Async", "ApplicationEvent", "@TransactionalEventListener"]
    },
    {
        "id": "probe_07",
        "category": "Handler/Processor",
        "name": "Event Processing",
        "prompt": """private void processEvent(JsonObject event) {
    String type = event.getString(EVENT_TYPE);
    // COMPLETE
""",
        "motadata_tokens": ["switch", "EventBusConstants", "publish", "handler"],
        "alien_tokens": ["@Service", "MessageConverter", "RabbitTemplate"]
    },
    {
        "id": "probe_08",
        "category": "Handler/Processor",
        "name": "Message Handler",
        "prompt": """eventBus.consumer(EventBusConstants.EVENT_NOTIFICATION, message -> {
    JsonObject body = message.body();
    // COMPLETE
""",
        "motadata_tokens": ["body.get", "getString", "handle", "reply"],
        "alien_tokens": ["@MessageMapping", "SimpMessagingTemplate", "@SendTo"]
    },
    
    # Category D: Async/Vertx Patterns (2 probes)
    {
        "id": "probe_09",
        "category": "Async/Vertx",
        "name": "Vertx Execute Blocking",
        "prompt": """vertx.executeBlocking(promise -> {
    // COMPLETE
""",
        "motadata_tokens": ["promise.complete", "try", "catch", "result"],
        "alien_tokens": ["CompletableFuture", "@Async", "ExecutorService", "ForkJoinPool"]
    },
    {
        "id": "probe_10",
        "category": "Async/Vertx",
        "name": "EventBus Async Publish",
        "prompt": """public void notifyChange(String entityId) {
    Event event = new EntityChangeEvent(entityId);
    // COMPLETE
""",
        "motadata_tokens": ["eventBus.publish", "EventBusConstants", "JsonObject", "vertx"],
        "alien_tokens": ["ApplicationEventPublisher", "@Autowired", "publishEvent"]
    }
]


def load_model(model_path: str, model_name: str) -> Tuple:
    """Load model and tokenizer"""
    print(f"🔧 Loading {model_name} from {model_path}...")
    sys.stdout.flush()
    
    print(f"  → Loading tokenizer...")
    sys.stdout.flush()
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True
    )
    print(f"  ✓ Tokenizer loaded")
    sys.stdout.flush()
    
    print(f"  → Loading model weights...")
    sys.stdout.flush()
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    print(f"  ✓ Model weights loaded")
    sys.stdout.flush()
    
    print(f"  → Setting eval mode...")
    sys.stdout.flush()
    model.eval()
    
    print(f"✅ {model_name} loaded successfully")
    sys.stdout.flush()
    return model, tokenizer


def generate_completion(
    model, 
    tokenizer, 
    prompt: str,
    max_tokens: int = 150  # Reduced from 200 for faster generation
) -> str:
    """Generate deterministic completion (no sampling for reproducibility)"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=False,  # Deterministic - no sampling
            pad_token_id=tokenizer.eos_token_id,
        )
    
    completion = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract only generated part
    completion = completion[len(prompt):].strip()
    
    return completion


def score_completion(completion: str, probe: Dict) -> Dict:
    """
    Score completion on 4 criteria:
    1. Domain Token Usage (0-2): Motadata classes vs alien frameworks
    2. Structural Correctness (0-2): Valid syntax, reasonable logic
    3. Brevity & Confidence (0-1): Short, decisive vs verbose/TODO-style
    4. Hallucination Penalty (-2/0): Invented classes/APIs
    """
    score_data = {
        "domain_fit": 0,
        "structure": 0,
        "brevity": 0,
        "hallucinations": 0,
        "details": {}
    }
    
    completion_lower = completion.lower()
    
    # 1. Domain Token Usage (0-2)
    motadata_matches = [t for t in probe["motadata_tokens"] if t.lower() in completion_lower]
    alien_matches = [t for t in probe["alien_tokens"] if t.lower() in completion_lower]
    
    if len(motadata_matches) >= 2:
        score_data["domain_fit"] = 2
    elif len(motadata_matches) >= 1:
        score_data["domain_fit"] = 1
    
    score_data["details"]["motadata_tokens"] = motadata_matches
    score_data["details"]["alien_tokens"] = alien_matches
    
    # 2. Structural Correctness (0-2)
    # Check for basic Java structure indicators
    structure_indicators = {
        "has_semicolon": ";" in completion,
        "has_braces": "{" in completion or "}" in completion,
        "has_method_call": "(" in completion and ")" in completion,
        "reasonable_length": 10 < len(completion) < 1000
    }
    
    structure_score = sum([
        structure_indicators["has_semicolon"] or structure_indicators["has_braces"],
        structure_indicators["has_method_call"],
        structure_indicators["reasonable_length"]
    ])
    score_data["structure"] = min(2, structure_score)
    score_data["details"]["structure"] = structure_indicators
    
    # 3. Brevity & Confidence (0-1)
    # Penalize verbose, TODO-style, over-explained code
    verbosity_markers = ["todo", "//", "/*", "...", "note:", "example:"]
    is_brief = len(completion) < 300 and sum(1 for m in verbosity_markers if m in completion_lower) <= 1
    score_data["brevity"] = 1 if is_brief else 0
    score_data["details"]["length"] = len(completion)
    
    # 4. Hallucination Penalty (-2/0)
    # Detect invented identifiers (capitalized words not in standard Java/Motadata vocab)
    hallucination_markers = [
        "FantasyClass", "MadeUpAPI", "NonExistentService",
        # Check for alien frameworks as hallucinations in Motadata context
    ]
    
    has_hallucination = any(h.lower() in completion_lower for h in hallucination_markers)
    # Alien framework usage counts as hallucination in Motadata context
    if len(alien_matches) > 0:
        has_hallucination = True
    
    score_data["hallucinations"] = -2 if has_hallucination else 0
    score_data["details"]["has_hallucination"] = has_hallucination
    
    # Total score
    score_data["total"] = (
        score_data["domain_fit"] +
        score_data["structure"] +
        score_data["brevity"] +
        score_data["hallucinations"]
    )
    
    return score_data


def save_outputs(probe_id: str, base_output: str, cpt_output: str, output_dir: Path):
    """Save raw outputs for manual review"""
    (output_dir / f"{probe_id}_base.txt").write_text(base_output)
    (output_dir / f"{probe_id}_cpt.txt").write_text(cpt_output)


def run_phase_c(base_model_path: str, cpt_model_path: str, output_dir: str = "./evaluation/results/phase_c"):
    """Run Phase-C CPT Completion Probe"""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("=" * 80)
    print("🔬 PHASE-C: CPT COMPLETION PROBE")
    print("=" * 80)
    print(f"📅 Timestamp: {timestamp}")
    print(f"🎯 Objective: Does CPT complete Motadata code better than base?")
    print(f"📊 Test Design: 10 minimal prompts, 4 categories")
    print(f"✅ Pass Condition: CPT wins ≥70% of probes")
    print("=" * 80)
    print(f"\n📦 Models:")
    print(f"   Base: {base_model_path}")
    print(f"   CPT:  {cpt_model_path}")
    print(f"\n⚙️  Generation Settings:")
    print(f"   max_new_tokens = 150")
    print(f"   do_sample = False (deterministic)")
    print("=" * 80)
    
    results = []
    wins = {"base": 0, "cpt": 0, "tie": 0}
    
    print(f"\n🧪 Running {len(FROZEN_PROBES)} probes...\n")
    print("⏳ Strategy: Load/test BASE first, then unload and test CPT (avoids OOM)\n")
    
    # PHASE 1: Generate all BASE completions
    print("=" * 80)
    print("📦 PHASE 1: Loading BASE model and generating completions...")
    print("=" * 80)
    base_model, base_tokenizer = load_model(base_model_path, "BASE")
    
    base_completions = {}
    for i, probe in enumerate(FROZEN_PROBES, 1):
        probe_name = probe['name']
        print(f"[{i}/{len(FROZEN_PROBES)}] BASE: {probe_name}")
        sys.stdout.flush()
        try:
            completion = generate_completion(base_model, base_tokenizer, probe["prompt"])
            base_completions[probe['id']] = completion
            print(f"   ✓ Generated ({len(completion)} chars)")
            sys.stdout.flush()
        except Exception as e:
            print(f"   ❌ Error generating {probe_name}: {e}")
            import traceback
            traceback.print_exc()
            base_completions[probe['id']] = ""
            sys.stdout.flush()
    
    # Unload base model to free VRAM
    print("\n🗑️  Unloading BASE model to free VRAM...")
    del base_model
    del base_tokenizer
    torch.cuda.empty_cache()
    print("✓ VRAM cleared\n")
    
    # PHASE 2: Generate all CPT completions
    print("=" * 80)
    print("📦 PHASE 2: Loading CPT model and generating completions...")
    print("=" * 80)
    cpt_model, cpt_tokenizer = load_model(cpt_model_path, "CPT")
    
    cpt_completions = {}
    for i, probe in enumerate(FROZEN_PROBES, 1):
        probe_name = probe['name']
        print(f"[{i}/{len(FROZEN_PROBES)}] CPT: {probe_name}")
        sys.stdout.flush()
        try:
            completion = generate_completion(cpt_model, cpt_tokenizer, probe["prompt"])
            cpt_completions[probe['id']] = completion
            print(f"   ✓ Generated ({len(completion)} chars)")
            sys.stdout.flush()
        except Exception as e:
            print(f"   ❌ Error generating {probe_name}: {e}")
            import traceback
            traceback.print_exc()
            cpt_completions[probe['id']] = ""
            sys.stdout.flush()
    
    # Unload CPT model
    print("\n🗑️  Unloading CPT model...")
    del cpt_model
    del cpt_tokenizer
    torch.cuda.empty_cache()
    print("✓ Done\n")
    
    # PHASE 3: Score and compare all completions
    print("=" * 80)
    print("📊 PHASE 3: Scoring and comparing completions...")
    print("=" * 80)
    
    for i, probe in enumerate(FROZEN_PROBES, 1):
        print(f"\n[{i}/{len(FROZEN_PROBES)}] {probe['category']}: {probe['name']}")
        
        base_completion = base_completions[probe['id']]
        cpt_completion = cpt_completions[probe['id']]
        
        base_score = score_completion(base_completion, probe)
        cpt_score = score_completion(cpt_completion, probe)
        
        print(f"   BASE score: {base_score['total']}/5")
        print(f"   CPT score:  {cpt_score['total']}/5")
        
        # Determine winner
        if cpt_score["total"] > base_score["total"]:
            winner = "CPT"
            wins["cpt"] += 1
            print(f"   ✅ Winner: CPT (+{cpt_score['total'] - base_score['total']})")
        elif base_score["total"] > cpt_score["total"]:
            winner = "BASE"
            wins["base"] += 1
            print(f"   ⚠️  Winner: BASE (+{base_score['total'] - cpt_score['total']})")
        else:
            winner = "TIE"
            wins["tie"] += 1
            print(f"   ≈ TIE (both scored {cpt_score['total']})")
        
        # Save outputs
        save_outputs(probe["id"], base_completion, cpt_completion, output_path)
        
        # Store result
        result = {
            "probe_id": probe["id"],
            "category": probe["category"],
            "name": probe["name"],
            "prompt": probe["prompt"],
            "base": {
                "completion": base_completion,
                "score": base_score
            },
            "cpt": {
                "completion": cpt_completion,
                "score": cpt_score
            },
            "winner": winner
        }
        results.append(result)
        print()
    
    # Calculate metrics
    total_probes = len(FROZEN_PROBES)
    cpt_win_rate = (wins["cpt"] / total_probes) * 100
    
    # Aggregate scores
    avg_base_domain = sum(r["base"]["score"]["domain_fit"] for r in results) / total_probes
    avg_cpt_domain = sum(r["cpt"]["score"]["domain_fit"] for r in results) / total_probes
    
    base_motadata_tokens = sum(len(r["base"]["score"]["details"]["motadata_tokens"]) for r in results)
    cpt_motadata_tokens = sum(len(r["cpt"]["score"]["details"]["motadata_tokens"]) for r in results)
    
    base_hallucinations = sum(1 for r in results if r["base"]["score"]["hallucinations"] < 0)
    cpt_hallucinations = sum(1 for r in results if r["cpt"]["score"]["hallucinations"] < 0)
    
    # Final verdict
    print("=" * 80)
    print("📊 PHASE-C RESULTS")
    print("=" * 80)
    print(f"\n🏆 Win/Loss/Tie: CPT {wins['cpt']} | BASE {wins['base']} | TIE {wins['tie']}")
    print(f"📈 CPT Win Rate: {cpt_win_rate:.1f}%")
    print(f"\n📝 Domain Token Usage:")
    print(f"   BASE: {avg_base_domain:.2f}/2.0 avg ({base_motadata_tokens} total Motadata tokens)")
    print(f"   CPT:  {avg_cpt_domain:.2f}/2.0 avg ({cpt_motadata_tokens} total Motadata tokens)")
    print(f"\n🚫 Hallucinations:")
    print(f"   BASE: {base_hallucinations}/{total_probes} probes")
    print(f"   CPT:  {cpt_hallucinations}/{total_probes} probes")
    print("=" * 80)
    
    # Pass/Fail determination
    passed = (
        cpt_win_rate >= 70 and
        cpt_motadata_tokens > base_motadata_tokens and
        cpt_hallucinations <= base_hallucinations
    )
    
    if passed:
        verdict = "✅ PHASE-C PASSED"
        verdict_details = "CPT shows clear Motadata instinct advantage"
    elif cpt_win_rate >= 50:
        verdict = "⚠️  PHASE-C MARGINAL"
        verdict_details = "CPT shows improvement but not decisive"
    else:
        verdict = "❌ PHASE-C FAILED"
        verdict_details = "CPT did not improve over base model"
    
    print(f"\n{verdict}")
    print(f"💡 {verdict_details}")
    print("=" * 80)
    
    # Save detailed report
    report = {
        "phase": "C - CPT Completion Probe",
        "timestamp": timestamp,
        "models": {
            "base": base_model_path,
            "cpt": cpt_model_path
        },
        "generation_settings": {
            "temperature": 0.2,
            "top_p": 0.95,
            "max_new_tokens": 200,
            "do_sample": False
        },
        "summary": {
            "total_probes": total_probes,
            "wins": wins,
            "cpt_win_rate": cpt_win_rate,
            "avg_domain_scores": {
                "base": avg_base_domain,
                "cpt": avg_cpt_domain
            },
            "motadata_token_count": {
                "base": base_motadata_tokens,
                "cpt": cpt_motadata_tokens
            },
            "hallucination_count": {
                "base": base_hallucinations,
                "cpt": cpt_hallucinations
            }
        },
        "verdict": verdict,
        "verdict_details": verdict_details,
        "passed": passed,
        "probe_results": results
    }
    
    report_path = output_path / f"phase_c_report_{timestamp}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📁 Detailed report: {report_path}")
    
    # Generate human-readable comparison
    comparison_path = output_path / f"phase_c_comparison_{timestamp}.md"
    with open(comparison_path, "w") as f:
        f.write("# Phase-C: CPT Completion Probe - Detailed Comparison\n\n")
        f.write(f"**Timestamp:** {timestamp}\n\n")
        f.write(f"**Verdict:** {verdict}\n\n")
        f.write(f"**CPT Win Rate:** {cpt_win_rate:.1f}%\n\n")
        f.write("---\n\n")
        
        for result in results:
            f.write(f"## {result['probe_id']}: {result['name']}\n\n")
            f.write(f"**Category:** {result['category']}\n\n")
            f.write(f"**Winner:** {result['winner']}\n\n")
            f.write("### Prompt\n```java\n")
            f.write(result['prompt'])
            f.write("\n```\n\n")
            f.write("### BASE Completion\n```java\n")
            f.write(result['base']['completion'])
            f.write("\n```\n")
            f.write(f"**Score:** {result['base']['score']['total']}/5 ")
            f.write(f"(Domain: {result['base']['score']['domain_fit']}, ")
            f.write(f"Structure: {result['base']['score']['structure']}, ")
            f.write(f"Brevity: {result['base']['score']['brevity']}, ")
            f.write(f"Hallucinations: {result['base']['score']['hallucinations']})\n\n")
            f.write(f"**Motadata tokens:** {', '.join(result['base']['score']['details']['motadata_tokens']) if result['base']['score']['details']['motadata_tokens'] else 'none'}\n\n")
            
            f.write("### CPT Completion\n```java\n")
            f.write(result['cpt']['completion'])
            f.write("\n```\n")
            f.write(f"**Score:** {result['cpt']['score']['total']}/5 ")
            f.write(f"(Domain: {result['cpt']['score']['domain_fit']}, ")
            f.write(f"Structure: {result['cpt']['score']['structure']}, ")
            f.write(f"Brevity: {result['cpt']['score']['brevity']}, ")
            f.write(f"Hallucinations: {result['cpt']['score']['hallucinations']})\n\n")
            f.write(f"**Motadata tokens:** {', '.join(result['cpt']['score']['details']['motadata_tokens']) if result['cpt']['score']['details']['motadata_tokens'] else 'none'}\n\n")
            f.write("---\n\n")
    
    print(f"📝 Comparison report: {comparison_path}")
    print()
    
    return report


def main():
    base_model_path = "Qwen/Qwen2.5-Coder-14B"
    cpt_model_path = "./models/motadata-cpt-checkpoint"
    
    if len(sys.argv) > 1:
        cpt_model_path = sys.argv[1]
    if len(sys.argv) > 2:
        base_model_path = sys.argv[2]
    
    if not Path(cpt_model_path).exists():
        print(f"❌ Error: CPT checkpoint not found at {cpt_model_path}")
        print(f"💡 Train CPT first: python training/train_cpt.py")
        return 1
    
    try:
        report = run_phase_c(base_model_path, cpt_model_path)
        return 0 if report["passed"] else 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

