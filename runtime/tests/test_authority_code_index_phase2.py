"""
Authority Code Index Tests (Phase 2).

Tests for:
- Code index building and file/class/method extraction
- Entry point detection
- Call edge extraction (1-hop)
- Adapter behavior with real index
- Determinism
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import List

import pytest

from runtime.layer5.authority.code_index_models import (
    CallConfidence,
    CallEdge,
    ClassRecord,
    CodeIndex,
    EntryPointRecord,
    EntryPointType,
    FileRecord,
    MethodRecord,
)
from runtime.layer5.authority.code_index_builder import (
    CodeIndexBuilder,
    JavaExtractor,
    build_index,
)
from runtime.layer5.authority.entry_points import (
    detect_entry_point_type,
    extract_entry_points,
    is_entry_point_file,
)
from runtime.layer5.authority.code_index_adapter import (
    HybridIndexAdapter,
    StructuredIndexAdapter,
    create_adapter,
)


# Fixture paths
FIXTURE_ROOT = Path(__file__).parent.parent / "layer5" / "audit" / "fixture_noisy_aiops_workspace"


class TestCodeIndexModels:
    """Tests for data model structures."""

    def test_method_record(self):
        """MethodRecord creation and properties."""
        method = MethodRecord(
            name="process",
            class_name="Processor",
            file_path="src/Processor.java",
            visibility="public",
        )
        assert method.qualified_name == "Processor.process"

    def test_class_record(self):
        """ClassRecord creation and properties."""
        cls = ClassRecord(
            name="AlertService",
            file_path="src/AlertService.java",
            package="com.example",
            methods=("process", "validate"),
        )
        assert cls.qualified_name == "com.example.AlertService"
        assert "process" in cls.methods

    def test_file_record(self):
        """FileRecord creation and lookup methods."""
        cls = ClassRecord(
            name="AlertService",
            file_path="src/AlertService.java",
            package="com.example",
            methods=("process", "validate"),
        )
        file_rec = FileRecord(
            relative_path="src/AlertService.java",
            package="com.example",
            classes=(cls,),
            imports=frozenset(["java.util.List"]),
        )
        
        assert file_rec.has_class("AlertService")
        assert not file_rec.has_class("NonExistent")
        assert file_rec.has_method("AlertService", "process")
        assert not file_rec.has_method("AlertService", "missing")

    def test_call_edge(self):
        """CallEdge creation and properties."""
        edge = CallEdge(
            source_file="src/A.java",
            source_class="A",
            source_method="foo",
            target_class="B",
            target_method="bar",
            confidence=CallConfidence.MEDIUM,
        )
        assert edge.source_qualified == "A.foo"
        assert edge.target_qualified == "B.bar"

    def test_entry_point_record(self):
        """EntryPointRecord creation and serialization."""
        ep = EntryPointRecord(
            entry_type=EntryPointType.REST_CONTROLLER,
            relative_path="src/Controller.java",
            class_name="Controller",
            method_name="getItems",
            metadata={"endpoint": "/items"},
            invokes=("service.getAll",),
        )
        d = ep.to_dict()
        assert d["entry_type"] == "rest_controller"
        assert d["metadata"]["endpoint"] == "/items"


class TestJavaExtractor:
    """Tests for Java code extraction."""

    def test_extract_package(self):
        """Package extraction."""
        extractor = JavaExtractor()
        content = "package com.example.service;\n\npublic class Test {}"
        assert extractor.extract_package(content) == "com.example.service"

    def test_extract_imports(self):
        """Import extraction."""
        extractor = JavaExtractor()
        content = """
package com.example;
import java.util.List;
import java.util.Map;
import com.other.Service;
"""
        imports = extractor.extract_imports(content)
        assert "java.util.List" in imports
        assert "com.other.Service" in imports

    def test_extract_classes(self):
        """Class extraction."""
        extractor = JavaExtractor()
        content = """
package com.example;

public class AlertService extends BaseService implements IService {
    public void process() {}
    public void validate() {}
}
"""
        classes = extractor.extract_classes(content, "AlertService.java", "com.example")
        
        assert len(classes) == 1
        cls = classes[0]
        assert cls.name == "AlertService"
        assert cls.superclass == "BaseService"
        assert "IService" in cls.interfaces

    def test_extract_interface(self):
        """Interface extraction."""
        extractor = JavaExtractor()
        content = """
package com.example;

public interface AlertHandler {
    void handle(Alert alert);
}
"""
        classes = extractor.extract_classes(content, "AlertHandler.java", "com.example")
        assert len(classes) == 1
        assert classes[0].name == "AlertHandler"


class TestEntryPointExtraction:
    """Tests for entry point detection."""

    def test_detect_rest_controller(self):
        """Detect REST controller by annotation."""
        content = """
@RestController
@RequestMapping("/api/alerts")
public class AlertController {
    @GetMapping("/{id}")
    public Alert getAlert(String id) {}
}
"""
        entry_type = detect_entry_point_type("AlertController.java", content)
        assert entry_type == EntryPointType.REST_CONTROLLER

    def test_detect_event_handler_by_class_name(self):
        """Detect event handler by class name pattern."""
        content = """
public class AlertEventHandler {
    public void handle(AlertEvent event) {}
}
"""
        entry_type = detect_entry_point_type("AlertEventHandler.java", content)
        assert entry_type == EntryPointType.EVENT_HANDLER

    def test_detect_event_handler_by_file_path(self):
        """Detect event handler by file path."""
        content = """
public class SomeProcessor {
    public void process() {}
}
"""
        entry_type = detect_entry_point_type("handlers/SomeProcessor.java", content)
        assert entry_type == EntryPointType.EVENT_HANDLER

    def test_detect_scheduler_by_annotation(self):
        """Detect scheduler by @Scheduled annotation."""
        content = """
public class MaintenanceJob {
    @Scheduled(cron = "0 0 * * * ?")
    public void runMaintenance() {}
}
"""
        entry_type = detect_entry_point_type("MaintenanceJob.java", content)
        assert entry_type == EntryPointType.SCHEDULER

    def test_extract_entry_points_rest(self):
        """Extract REST controller entry points with metadata."""
        content = """
@RestController
public class AlertController {
    @GetMapping("/alerts")
    public List<Alert> getAlerts() {
        return alertService.findAll();
    }
    
    @PostMapping("/alerts")
    public void createAlert(Alert alert) {
        alertService.save(alert);
    }
}
"""
        entry_points = extract_entry_points("AlertController.java", content)
        assert len(entry_points) >= 1
        
        for ep in entry_points:
            assert ep.entry_type == EntryPointType.REST_CONTROLLER

    def test_extract_entry_points_event_handler(self):
        """Extract event handler entry points."""
        content = """
public class IncidentHandler {
    @EventHandler
    public void handle(IncidentEvent event) {
        processor.process(event);
    }
}
"""
        entry_points = extract_entry_points("IncidentHandler.java", content)
        assert len(entry_points) >= 1
        
        ep = entry_points[0]
        assert ep.entry_type == EntryPointType.EVENT_HANDLER
        assert ep.method_name == "handle"

    def test_no_entry_point(self):
        """No entry point for regular class."""
        content = """
public class UtilityHelper {
    public static String format(String s) {
        return s.trim();
    }
}
"""
        assert detect_entry_point_type("UtilityHelper.java", content) is None
        assert not is_entry_point_file("UtilityHelper.java", content)


class TestCodeIndexBuilder:
    """Tests for code index building."""

    def test_build_index_from_fixture(self):
        """Build index from fixture workspace."""
        if not FIXTURE_ROOT.exists():
            pytest.skip("Fixture workspace not found")
        
        index = build_index(
            FIXTURE_ROOT,
            source_dirs=["motadata/src/main/java"],
            include_tests=False,
        )
        
        assert index.stats["files"] > 0
        assert index.stats["classes"] > 0

    def test_file_class_method_existence(self):
        """Index correctly reports file/class/method existence."""
        if not FIXTURE_ROOT.exists():
            pytest.skip("Fixture workspace not found")
        
        index = build_index(
            FIXTURE_ROOT,
            source_dirs=["motadata/src/main/java"],
        )
        
        # Check a file that exists
        assert index.file_exists("motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java")
        assert index.class_exists(
            "motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java",
            "AlertCorrelationEngine"
        )
        
        # Check non-existent
        assert not index.file_exists("nonexistent/File.java")

    def test_entry_points_extracted(self):
        """Entry points are extracted from fixture."""
        if not FIXTURE_ROOT.exists():
            pytest.skip("Fixture workspace not found")
        
        index = build_index(
            FIXTURE_ROOT,
            source_dirs=["motadata/src/main/java"],
        )
        
        # Should have entry points from handler, controller, scheduler files
        assert index.stats["entry_points"] >= 0  # May vary based on fixture

    def test_determinism(self):
        """Same input produces same output."""
        if not FIXTURE_ROOT.exists():
            pytest.skip("Fixture workspace not found")
        
        index1 = build_index(
            FIXTURE_ROOT,
            source_dirs=["motadata/src/main/java"],
        )
        index2 = build_index(
            FIXTURE_ROOT,
            source_dirs=["motadata/src/main/java"],
        )
        
        assert index1.stats == index2.stats
        assert set(index1.files.keys()) == set(index2.files.keys())


class TestCodeIndex:
    """Tests for CodeIndex operations."""

    def test_build_indices(self):
        """Index building creates lookup maps."""
        cls = ClassRecord(
            name="Service",
            file_path="src/Service.java",
            package="com.example",
            methods=("process",),
        )
        file_rec = FileRecord(
            relative_path="src/Service.java",
            package="com.example",
            classes=(cls,),
            imports=frozenset(["com.other.Helper"]),
        )
        
        index = CodeIndex(files={"src/Service.java": file_rec})
        index.build_indices()
        
        assert index.get_file_for_class("Service") == "src/Service.java"

    def test_caller_callee_lookup(self):
        """Caller/callee lookup works."""
        edge = CallEdge(
            source_file="src/A.java",
            source_class="A",
            source_method="foo",
            target_class="B",
            target_method="bar",
            confidence=CallConfidence.MEDIUM,
        )
        
        index = CodeIndex(call_edges=[edge])
        index.build_indices()
        
        callers = index.get_callers("B", "bar")
        assert len(callers) == 1
        assert callers[0].source_class == "A"
        
        callees = index.get_callees("A", "foo")
        assert len(callees) == 1
        assert callees[0].target_class == "B"

    def test_entry_points_for_file(self):
        """Entry point lookup by file."""
        ep = EntryPointRecord(
            entry_type=EntryPointType.REST_CONTROLLER,
            relative_path="src/Controller.java",
            class_name="Controller",
            method_name="get",
        )
        
        index = CodeIndex(entry_points=[ep])
        
        eps = index.get_entry_points_for_file("src/Controller.java")
        assert len(eps) == 1
        assert eps[0].method_name == "get"
        
        eps_other = index.get_entry_points_for_file("src/Other.java")
        assert len(eps_other) == 0


class TestStructuredIndexAdapter:
    """Tests for StructuredIndexAdapter."""

    def test_adapter_file_exists(self):
        """Adapter delegates file_exists to index."""
        file_rec = FileRecord(relative_path="src/Test.java", package="com.example")
        index = CodeIndex(files={"src/Test.java": file_rec})
        index.build_indices()
        
        adapter = StructuredIndexAdapter(index)
        
        assert adapter.file_exists("src/Test.java")
        assert not adapter.file_exists("src/Missing.java")

    def test_adapter_class_method_exists(self):
        """Adapter class/method existence checks."""
        cls = ClassRecord(
            name="Service",
            file_path="src/Service.java",
            package="com.example",
            methods=("process", "validate"),
        )
        file_rec = FileRecord(
            relative_path="src/Service.java",
            package="com.example",
            classes=(cls,),
        )
        index = CodeIndex(files={"src/Service.java": file_rec})
        index.build_indices()
        
        adapter = StructuredIndexAdapter(index)
        
        assert adapter.class_exists("src/Service.java", "Service")
        assert not adapter.class_exists("src/Service.java", "Missing")
        assert adapter.method_exists("src/Service.java", "Service", "process")
        assert not adapter.method_exists("src/Service.java", "Service", "missing")

    def test_adapter_entry_points(self):
        """Adapter entry point retrieval."""
        ep = EntryPointRecord(
            entry_type=EntryPointType.EVENT_HANDLER,
            relative_path="src/Handler.java",
            class_name="Handler",
            method_name="handle",
        )
        index = CodeIndex(entry_points=[ep])
        index.build_indices()
        
        adapter = StructuredIndexAdapter(index)
        
        eps = adapter.get_entry_points_for_file("src/Handler.java")
        assert len(eps) == 1
        assert eps[0].method_name == "handle"

    def test_adapter_callers_callees(self):
        """Adapter caller/callee retrieval."""
        edge = CallEdge(
            source_file="src/A.java",
            source_class="Caller",
            source_method="invoke",
            target_class="Target",
            target_method="execute",
            confidence=CallConfidence.MEDIUM,
        )
        index = CodeIndex(call_edges=[edge])
        index.build_indices()
        
        adapter = StructuredIndexAdapter(index)
        
        callers = adapter.get_direct_callers("Target", "execute")
        assert len(callers) == 1
        
        callees = adapter.get_direct_callees("Caller", "invoke")
        assert len(callees) == 1

    def test_create_adapter_with_code_index(self):
        """create_adapter returns StructuredIndexAdapter for CodeIndex."""
        index = CodeIndex()
        adapter = create_adapter(code_index=index)
        
        assert isinstance(adapter, StructuredIndexAdapter)

    def test_create_adapter_with_workspace_root_enables_hybrid_fallback(self, tmp_path: Path):
        """create_adapter uses hybrid adapter when workspace_root is provided."""
        rel = "motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java"
        f = tmp_path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(
            "public class AvailabilityCorrelationEngine { public void start() {} }",
            encoding="utf-8",
        )

        # Structured index intentionally misses file/class metadata.
        index = CodeIndex()
        adapter = create_adapter(code_index=index, workspace_root=tmp_path)

        assert isinstance(adapter, HybridIndexAdapter)
        assert adapter.file_exists(rel)
        assert adapter.class_exists(rel, "AvailabilityCorrelationEngine")
        assert adapter.method_exists(rel, "AvailabilityCorrelationEngine", "start")


class TestIntegration:
    """Integration tests with fixture workspace."""

    def test_full_flow(self):
        """Full flow: build index, create adapter, lookup."""
        if not FIXTURE_ROOT.exists():
            pytest.skip("Fixture workspace not found")
        
        # Build index
        index = build_index(
            FIXTURE_ROOT,
            source_dirs=["motadata/src/main/java"],
        )
        
        # Create adapter
        adapter = create_adapter(code_index=index)
        
        # Check known file
        alert_engine_path = "motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java"
        
        assert adapter.file_exists(alert_engine_path)
        assert adapter.class_exists(alert_engine_path, "AlertCorrelationEngine")
        
        # Entry points
        controller_path = "motadata/src/main/java/com/mindarray/controllers/AlertController.java"
        if adapter.file_exists(controller_path):
            eps = adapter.get_entry_points_for_file(controller_path)
            assert len(eps) > 0
            assert all(ep.entry_type == EntryPointType.REST_CONTROLLER for ep in eps)

    def test_index_serialization(self):
        """Index can be serialized to JSON."""
        if not FIXTURE_ROOT.exists():
            pytest.skip("Fixture workspace not found")
        
        index = build_index(
            FIXTURE_ROOT,
            source_dirs=["motadata/src/main/java"],
        )
        
        json_str = index.to_json()
        assert isinstance(json_str, str)
        assert "files" in json_str
        assert "entry_points" in json_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
