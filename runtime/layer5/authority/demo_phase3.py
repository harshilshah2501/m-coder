#!/usr/bin/env python3
"""
Phase 3 Authority-Aware Ranking Demo.

Demonstrates:
1. Baseline lexical ranking
2. Authority-aware reranked output
3. Validated owner boost
4. Stale/stale_candidate authority handling
5. Distractor demotion
6. Entry-point supportive boost
"""

from pathlib import Path
from typing import List, Tuple

from runtime.layer5.authority.code_index_builder import build_index
from runtime.layer5.authority.code_index_adapter import create_adapter
from runtime.layer5.authority.ranking import AuthorityRanker, RankedHit, get_ranking_diagnostics
from runtime.layer5.authority.ranking_config import RankingConfig
from runtime.layer5.authority.registry_loader import load_registry


# Paths
FIXTURE_ROOT = Path(__file__).parent.parent / "audit" / "fixture_noisy_aiops_workspace"
REGISTRY_PATH = Path(__file__).parent / "product_authority_registry.yaml"


def create_mock_hits() -> List[Tuple[str, float]]:
    """Create mock lexical retrieval hits for demonstration."""
    return [
        # High lexical score but is a distractor (registry forbidden)
        ("src/main/java/com/mindarray/aiops/AIOpsConstants.java", 85.0),
        # Medium score, is the true owner
        ("src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java", 70.0),
        # High score, collaborator
        ("src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java", 80.0),
        # Medium score, collaborator
        ("src/main/java/com/mindarray/aiops/DependencyManager.java", 65.0),
        # Low score, utility file
        ("motadata/src/main/java/com/mindarray/util/MotadataConfigUtil.java", 50.0),
        # Medium score, unrelated
        ("motadata/src/main/java/com/mindarray/nms/MetricPoller.java", 60.0),
    ]


def print_ranking(title: str, ranked_hits: List[RankedHit], show_diagnostics: bool = False):
    """Print ranking results."""
    print(f"\n{title}")
    print("-" * 70)
    
    for hit in ranked_hits:
        file_name = hit.file_path.split("/")[-1]
        change = hit.final_score - hit.original_score
        change_str = f"+{change:.1f}" if change >= 0 else f"{change:.1f}"
        
        print(f"  Rank {hit.rank}: {file_name}")
        print(f"    Original: {hit.original_score:.1f} → Final: {hit.final_score:.1f} ({change_str})")
        
        if show_diagnostics and hit.diagnostics:
            diag = hit.diagnostics
            if diag.boost_reasons:
                print(f"    Reasons: {', '.join(diag.boost_reasons)}")
            if diag.authority_status:
                print(f"    Authority status: {diag.authority_status}")
        print()


def main():
    print("=" * 70)
    print("PHASE 3 AUTHORITY-AWARE RANKING DEMO")
    print("=" * 70)

    # Load registry and build index
    print("\n1. LOADING AUTHORITY REGISTRY AND CODE INDEX")
    print("-" * 70)
    
    registry = load_registry(REGISTRY_PATH)
    print(f"   Registry loaded: {len(registry.concepts)} concepts")
    
    code_index = None
    adapter = None
    if FIXTURE_ROOT.exists():
        code_index = build_index(FIXTURE_ROOT, source_dirs=["motadata/src/main/java"])
        adapter = create_adapter(code_index=code_index)
        print(f"   Code index built: {code_index.stats['files']} files, {code_index.stats['entry_points']} entry points")
    else:
        print("   Code index: Not available (fixture not found)")

    # Create ranker
    config = RankingConfig(enable_authority_reranking=True)
    ranker = AuthorityRanker(registry, adapter, config)

    # Demo A: Baseline vs Authority-Aware Ranking
    print("\n" + "=" * 70)
    print("A. BASELINE vs AUTHORITY-AWARE RANKING")
    print("=" * 70)
    
    query = "alert correlation"
    mock_hits = create_mock_hits()
    
    print(f"\n   Query: \"{query}\"")
    print(f"   Concept matched: alert_correlation")
    
    # Baseline (feature flag off)
    config_off = RankingConfig(enable_authority_reranking=False)
    ranker_off = AuthorityRanker(registry, adapter, config_off)
    context_off = ranker_off.build_context(query)
    baseline_ranked = ranker_off.rank_hits(mock_hits, context_off)
    
    print_ranking("Baseline (authority reranking OFF):", baseline_ranked)
    
    # Authority-aware
    context = ranker.build_context(query)
    ranked = ranker.rank_hits(mock_hits, context)
    
    print_ranking("Authority-Aware Reranked:", ranked, show_diagnostics=True)

    # Demo B: Validated Owner Case
    print("\n" + "=" * 70)
    print("B. VALIDATED OWNER CASE")
    print("=" * 70)
    
    print(f"\n   Concept: alert_correlation")
    print(f"   Authority status: {context.authority_status}")
    print(f"   Owner file: AvailabilityCorrelationEngine.java")
    
    owner_hit = next((h for h in ranked if "AvailabilityCorrelationEngine" in h.file_path), None)
    if owner_hit:
        print(f"\n   Owner ranking:")
        print(f"     Original score: {owner_hit.original_score:.1f}")
        print(f"     Final score: {owner_hit.final_score:.1f}")
        print(f"     Boost applied: +{owner_hit.diagnostics.owner_boost:.1f}")
        print(f"     Final rank: #{owner_hit.rank}")
        print(f"     Authority status: {owner_hit.diagnostics.authority_status}")

    # Demo C: Stale/Stale_Candidate Case
    print("\n" + "=" * 70)
    print("C. STALE/STALE_CANDIDATE CASE")
    print("=" * 70)
    
    # Simulate stale authority by using a concept that would be stale
    query_escalation = "alert escalation"
    context_escalation = ranker.build_context(query_escalation)
    
    print(f"\n   Query: \"{query_escalation}\"")
    print(f"   Concept matched: alert_escalation")
    print(f"   Authority status: {context_escalation.authority_status}")
    
    # Create hits for this case
    escalation_hits = [
        ("src/main/java/com/mindarray/aiops/DependencyManager.java", 75.0),
        ("src/main/java/com/mindarray/aiops/AIOpsConstants.java", 70.0),
        ("motadata/src/main/java/com/mindarray/nms/MetricPoller.java", 60.0),
    ]
    
    ranked_escalation = ranker.rank_hits(escalation_hits, context_escalation)
    
    print_ranking("Stale/Stale_Candidate Ranking:", ranked_escalation, show_diagnostics=True)
    
    owner_esc = next((h for h in ranked_escalation if "DependencyManager" in h.file_path), None)
    if owner_esc:
        print(f"   Note: Owner boost is partial (+{owner_esc.diagnostics.owner_boost:.1f})")
        print(f"   because authority status is '{context_escalation.authority_status}'")
        print(f"   (not 'validated' which would give +{config.owner_boost_validated:.1f})")

    # Demo D: Distractor Demotion
    print("\n" + "=" * 70)
    print("D. DISTRACTOR DEMOTION")
    print("=" * 70)
    
    query = "incident deduplication"
    context_dedup = ranker.build_context(query)
    
    print(f"\n   Query: \"{query}\"")
    print(f"   Concept matched: incident_deduplication")
    print(f"   Distractor: AvailabilityCorrelationEngine.java (wrong domain)")
    
    dedup_hits = [
        # Distractor with high lexical score
        ("src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java", 90.0),
        # True owner with lower lexical score
        ("src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java", 65.0),
        # Package metadata (also a distractor for this concept)
        ("src/main/java/com/mindarray/aiops/package-info.java", 80.0),
    ]
    
    ranked_dedup = ranker.rank_hits(dedup_hits, context_dedup)
    
    print_ranking("Distractor Demotion Ranking:", ranked_dedup, show_diagnostics=True)
    
    distractor = next((h for h in ranked_dedup if "AvailabilityCorrelationEngine" in h.file_path), None)
    if distractor:
        print(f"   Distractor result:")
        print(f"     Original score: {distractor.original_score:.1f}")
        print(f"     Penalty applied: {distractor.diagnostics.distractor_penalty:.1f}")
        print(f"     Final score: {distractor.final_score:.1f}")
        print(f"     Final rank: #{distractor.rank} (demoted)")

    # Demo E: Entry-Point Supportive Boost
    print("\n" + "=" * 70)
    print("E. ENTRY-POINT SUPPORTIVE BOOST (not owner override)")
    print("=" * 70)
    
    query = "alert correlation"
    context = ranker.build_context(query)
    
    print(f"\n   Query: \"{query}\"")
    print(f"   Entry: AvailabilityCorrelationEngine (registry primary)")
    print(f"   Related: DependencyQueryProcessor in collaborator set")
    
    entry_hits = [
        # Collaborator / high lexical
        ("src/main/java/com/mindarray/aiops/DependencyQueryProcessor.java", 85.0),
        # True owner
        ("src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java", 70.0),
        # Random file
        ("motadata/src/main/java/com/mindarray/nms/MetricPoller.java", 60.0),
    ]
    
    ranked_entry = ranker.rank_hits(entry_hits, context)
    
    print_ranking("Entry-Point Supportive Boost:", ranked_entry, show_diagnostics=True)
    
    entry_point = next((h for h in ranked_entry if "DependencyQueryProcessor" in h.file_path), None)
    owner = next((h for h in ranked_entry if "AvailabilityCorrelationEngine" in h.file_path), None)
    
    if entry_point and owner:
        print(f"   Key observation:")
        print(f"     Entry point gets supportive boost: +{entry_point.diagnostics.entry_point_boost:.1f}")
        print(f"     But owner still ranks higher due to owner boost: +{owner.diagnostics.owner_boost:.1f}")
        print(f"     Entry point rank: #{entry_point.rank}")
        print(f"     Owner rank: #{owner.rank}")
        print(f"\n   Entry-point boost is supportive, NOT owner-overriding.")

    # Demo F: Feature Flag OFF
    print("\n" + "=" * 70)
    print("F. FEATURE FLAG OFF (preserves original order)")
    print("=" * 70)
    
    config_disabled = RankingConfig(enable_authority_reranking=False)
    ranker_disabled = AuthorityRanker(registry, adapter, config_disabled)
    
    context_disabled = ranker_disabled.build_context(query)
    ranked_disabled = ranker_disabled.rank_hits(mock_hits, context_disabled)
    
    print(f"\n   Feature flag: enable_authority_reranking = False")
    print(f"\n   Original order preserved:")
    for hit in ranked_disabled:
        file_name = hit.file_path.split("/")[-1]
        print(f"     Rank {hit.rank}: {file_name} (score: {hit.final_score:.1f})")

    print("\n" + "=" * 70)
    print("PHASE 3 DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
