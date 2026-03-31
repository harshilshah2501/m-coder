#!/usr/bin/env python3
"""
Phase 2 Code Index Demo.

Demonstrates:
1. Code index building from Java files
2. File/class/method lookup
3. Entry point detection
4. Call edge extraction (1-hop)
"""

from pathlib import Path

from runtime.layer5.authority.code_index_builder import build_index
from runtime.layer5.authority.code_index_adapter import create_adapter
from runtime.layer5.authority.registry_loader import load_registry
from runtime.layer5.authority.validation import validate_concept


# Use the fixture workspace with Java files
FIXTURE_ROOT = Path(__file__).parent.parent / "audit" / "fixture_noisy_aiops_workspace"
REGISTRY_PATH = Path(__file__).parent / "product_authority_registry.yaml"


def main():
    print("=" * 70)
    print("PHASE 2 CODE INDEX DEMO")
    print("=" * 70)

    # A. Build index
    print("\n1. BUILDING CODE INDEX")
    print("-" * 70)
    
    if not FIXTURE_ROOT.exists():
        print(f"   ERROR: Fixture workspace not found at {FIXTURE_ROOT}")
        print("   Creating synthetic test files for demo...")
        create_synthetic_test_files()
    
    index = build_index(
        FIXTURE_ROOT,
        source_dirs=["motadata/src/main/java"],
        include_tests=False,
    )
    
    stats = index.stats
    print(f"\n   Index Summary:")
    print(f"   - Java files indexed: {stats['files']}")
    print(f"   - Classes extracted:  {stats['classes']}")
    print(f"   - Methods extracted:  {stats['methods']}")
    print(f"   - Entry points found: {stats['entry_points']}")
    print(f"   - Call edges (1-hop): {stats['call_edges']}")

    # B. Show indexed files
    print("\n2. INDEXED FILES")
    print("-" * 70)
    
    for i, (path, file_rec) in enumerate(sorted(index.files.items())[:10]):
        print(f"\n   [{i+1}] {path}")
        print(f"       Package: {file_rec.package or '(default)'}")
        print(f"       Classes: {', '.join(file_rec.class_names) or '(none)'}")
        methods = file_rec.method_names[:3]
        if len(file_rec.method_names) > 3:
            methods_str = ", ".join(methods) + f" (+{len(file_rec.method_names) - 3} more)"
        else:
            methods_str = ", ".join(methods) or "(none)"
        print(f"       Methods: {methods_str}")

    if stats['files'] > 10:
        print(f"\n   ... and {stats['files'] - 10} more files")

    # C. Authority-backed file lookup
    print("\n3. AUTHORITY-BACKED FILE LOOKUP")
    print("-" * 70)
    
    registry = load_registry(REGISTRY_PATH)
    adapter = create_adapter(code_index=index)
    
    for concept_name in registry.list_concepts()[:2]:
        concept = registry.get_concept(concept_name)
        if not concept:
            continue
        
        print(f"\n   Concept: {concept_name}")
        print(f"   Primary owner file: {concept.primary_owner.file}")
        print(f"   Primary owner class: {concept.primary_owner.class_name}")
        
        # Check existence
        file_exists = adapter.file_exists(concept.primary_owner.file)
        class_exists = adapter.class_exists(
            concept.primary_owner.file, concept.primary_owner.class_name
        )
        method_exists = False
        if concept.primary_owner.method:
            method_exists = adapter.method_exists(
                concept.primary_owner.file,
                concept.primary_owner.class_name,
                concept.primary_owner.method,
            )
        
        print(f"\n   Validation:")
        print(f"     file_exists:   {file_exists}")
        print(f"     class_exists:  {class_exists}")
        if concept.primary_owner.method:
            print(f"     method_exists: {method_exists}")
        
        # Check for entry points leading to this file
        entry_points = adapter.get_entry_points_for_file(concept.primary_owner.file)
        if entry_points:
            print(f"\n   Entry points in file:")
            for ep in entry_points[:3]:
                print(f"     - {ep.entry_type.value}: {ep.class_name}.{ep.method_name}()")
        
        # Check for callers/callees if method specified
        if concept.primary_owner.method and class_exists:
            callers = adapter.get_direct_callers(
                concept.primary_owner.class_name, concept.primary_owner.method
            )
            callees = adapter.get_direct_callees(
                concept.primary_owner.class_name, concept.primary_owner.method
            )
            if callers:
                print(f"\n   Direct callers (1-hop):")
                for edge in callers[:3]:
                    print(f"     <- {edge.source_qualified}")
            if callees:
                print(f"\n   Direct callees (1-hop):")
                for edge in callees[:3]:
                    print(f"     -> {edge.target_qualified}")

    # D. Entry point examples
    print("\n4. ENTRY POINT EXAMPLES")
    print("-" * 70)
    
    if index.entry_points:
        for ep in index.entry_points[:5]:
            print(f"\n   Type: {ep.entry_type.value}")
            print(f"   File: {ep.relative_path}")
            print(f"   Method: {ep.class_name}.{ep.method_name}()")
            print(f"   Pattern: {ep.pattern_matched}")
            if ep.invokes:
                print(f"   Invokes: {', '.join(ep.invokes[:3])}")
            if ep.metadata:
                print(f"   Metadata: {ep.metadata}")
    else:
        print("\n   No entry points detected in indexed files.")
        print("   (Entry points require @RestController, *Handler classes, @Scheduled, etc.)")

    # E. Call edges
    print("\n5. CALL EDGE EXAMPLES (1-hop)")
    print("-" * 70)
    
    if index.call_edges:
        for edge in index.call_edges[:10]:
            print(f"   {edge.source_qualified} -> {edge.target_qualified} ({edge.confidence.value})")
    else:
        print("\n   No call edges extracted.")
        print("   (Call edges require method invocations like obj.method())")

    print("\n" + "=" * 70)
    print("PHASE 2 DEMO COMPLETE")
    print("=" * 70)


def create_synthetic_test_files():
    """Create synthetic Java files for testing if fixture doesn't exist."""
    test_root = FIXTURE_ROOT / "motadata" / "src" / "main" / "java" / "com" / "mindarray"
    
    # Create directories
    (test_root / "aiops" / "correlation").mkdir(parents=True, exist_ok=True)
    (test_root / "eventbus" / "handlers").mkdir(parents=True, exist_ok=True)
    
    # Create a controller
    controller = test_root / "aiops" / "IncidentController.java"
    controller.write_text("""package com.mindarray.aiops;

@RestController
@RequestMapping("/api/incidents")
public class IncidentController {
    
    private final IncidentService incidentService;
    
    @GetMapping("/{id}")
    public Incident getIncident(String id) {
        return incidentService.findById(id);
    }
    
    @PostMapping
    public void createIncident(Incident incident) {
        incidentService.create(incident);
    }
}
""", encoding="utf-8")
    
    # Create an event handler
    handler = test_root / "eventbus" / "handlers" / "IncidentEventHandler.java"
    handler.write_text("""package com.mindarray.eventbus.handlers;

public class IncidentEventHandler {
    
    private final CorrelationEngine correlationEngine;
    private final DeduplicationProcessor deduplicationProcessor;
    
    @EventHandler
    public void handle(IncidentEvent event) {
        correlationEngine.correlate(event);
        deduplicationProcessor.process(event);
    }
    
    public void onIncidentCreated(IncidentCreatedEvent event) {
        // Process created event
    }
}
""", encoding="utf-8")
    
    # Create correlation engine
    engine = test_root / "aiops" / "correlation" / "CorrelationEngine.java"
    engine.write_text("""package com.mindarray.aiops.correlation;

public class CorrelationEngine {
    
    private final TopologyCache topologyCache;
    
    public void correlate(Event event) {
        topologyCache.getTopology();
        // Correlation logic
    }
    
    public void correlateAlerts(Alert alert) {
        // Alert correlation
    }
}
""", encoding="utf-8")
    
    # Create scheduler
    scheduler = test_root / "aiops" / "MaintenanceScheduler.java"
    scheduler.write_text("""package com.mindarray.aiops;

public class MaintenanceScheduler {
    
    @Scheduled(cron = "0 0 * * * ?")
    public void runMaintenance() {
        // Scheduled maintenance
    }
}
""", encoding="utf-8")
    
    print(f"   Created synthetic test files in {test_root}")


if __name__ == "__main__":
    main()
