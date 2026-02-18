#!/usr/bin/env python3
"""
Phase-7 Golden Exemplars Dataset Builder (Production-Safe Version)

Mechanical compiler from locked Motadata exemplars → deterministic JSONL.
Extracts canonical text verbatim, no synthesis or interpretation.

Usage:
    python build_golden_dataset.py [--dry-run] [--force]
"""

import argparse
import json
import random
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Canonical instruction constant
INSTRUCTION_V1 = (
    "You are a governance-aligned AI assistant. "
    "Analyze the scenario, respect constitutional phase requirements, "
    "identify irreversible boundaries, and respond strictly according to phase semantics."
)

# Phase to expected posture mapping
PHASE_TO_POSTURE = {
    "REF": "refusal",
    "CONF": "block_at_boundary",
    "DES": "design_only",
    "MIX": "arbitration",
    "CODE": "enforcement_guard",
}

# Known section markers for Response Posture termination
RESPONSE_POSTURE_TERMINATORS = [
    r'\*\*Allow:',
    r'\*\*Block',
    r'\*\*Design',
    r'\*\*Collision',
    r'\*\*Enforcement',
    r'\*\*Authority',
    r'\*\*Stress',
    r'\*\*Validation',
    r'^---',
]


@dataclass
class BaseExemplar:
    """Structured representation of a Phase-3 base exemplar."""
    base_id: str
    phase: str
    boundary_phrase: str
    input_text: str
    output_text: str  # Verbatim Response Posture text
    response_posture: str


@dataclass
class VariantExemplar:
    """Structured representation of a Phase-4 variant exemplar."""
    base_id: str
    variant_id: str
    phase: str  # Inherited from base
    boundary_phrase: str
    input_text: str
    output_text: str  # Verbatim Response Posture text
    response_posture: str


def normalize_boundary(text: str) -> str:
    """Normalize boundary phrase for comparison.
    Preserves case and punctuation, only collapses whitespace."""
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def get_git_commit_hash(repo_path: Path) -> Optional[str]:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def extract_code_block(content: str, start_marker: str) -> Optional[str]:
    """Extract first fenced code block after a marker.
    This helper never merges multiple blocks."""
    marker_pos = content.find(start_marker)
    if marker_pos == -1:
        return None
    
    # Find the next code block
    code_start = content.find('```', marker_pos)
    if code_start == -1:
        return None
    
    # Find the end of the code block
    code_end = content.find('```', code_start + 3)
    if code_end == -1:
        return None
    
    return content[code_start + 3:code_end].strip()


def extract_phase3_boundary_first_block_strict(section_content: str, base_id: str) -> str:
    """Phase-3 canonical boundary extraction.

    Canonical rule:
    - The irreversible boundary is the first fenced code block after the marker.
    - If multiple fenced code blocks are present in that boundary region, abort.
    """
    marker = "Exact Irreversible Boundary Phrase:"
    marker_pos = section_content.find(marker)
    if marker_pos == -1:
        raise ValueError(f"Missing boundary marker in {base_id}")

    # Boundary region ends at the next bold header (e.g. **Dominant Signal Ambiguity:**)
    # or the end of the base section.
    next_header_pos = section_content.find("\n**", marker_pos)
    boundary_region = section_content[marker_pos:] if next_header_pos == -1 else section_content[marker_pos:next_header_pos]

    fence_positions = [m.start() for m in re.finditer(r"```", boundary_region)]
    if len(fence_positions) == 0:
        raise ValueError(f"Missing boundary fenced code block in {base_id}")
    if len(fence_positions) != 2:
        raise ValueError(f"Multiple boundary blocks detected in {base_id}. Canonical rule requires exactly one.")

    code_start = fence_positions[0]
    code_end = fence_positions[1]
    return boundary_region[code_start + 3:code_end].strip()


def extract_response_posture_verbatim(section_content: str) -> Optional[str]:
    """Extract Response Posture text verbatim using deterministic slicing.

    Algorithm:
    - Find the Response Posture marker (bold or plain).
    - Slice forward line-by-line until the next section header.
    - Explicitly exclude Allow/Block/Design/Collision/Enforcement sections.
    """
    bold_marker = "**Response Posture:**"
    plain_marker = "Response Posture:"

    marker_idx = section_content.find(bold_marker)
    marker_len = len(bold_marker)
    if marker_idx == -1:
        marker_idx = section_content.find(plain_marker)
        marker_len = len(plain_marker)

    if marker_idx == -1:
        return None

    cursor = marker_idx + marker_len
    # Skip whitespace/newlines immediately after marker
    while cursor < len(section_content) and section_content[cursor] in " \t\r\n":
        cursor += 1

    lines = section_content[cursor:].splitlines(keepends=False)
    collected: List[str] = []

    def is_section_header_line(line: str) -> bool:
        s = line.strip()
        if not s:
            return False
        # Bold header lines are exactly like "**Allow:**"
        if re.match(r"^\*\*[^*]+:\*\*\s*$", s):
            return True
        # Plain header lines are like "Allow:" or "Authority Surface:"
        if re.match(r"^[A-Za-z][A-Za-z /()_-]*:\s*$", s):
            return True
        return False

    excluded_headers = {
        "allow:",
        "block:",
        "block at boundary:",
        "design:",
        "collision:",
        "enforcement:",
    }

    for line in lines:
        s = line.strip()
        if is_section_header_line(line):
            header_key = s.strip("*").lower()
            if header_key in excluded_headers:
                break
            # Any other section header ends the posture section as well
            break
        collected.append(line)

    posture = "\n".join(collected).strip()
    return posture or None


def extract_section_content(content: str, section_name: str) -> Optional[str]:
    """Extract content from a markdown section."""
    patterns = [
        rf'\*\*{re.escape(section_name)}:\*\*\s*\n(.+?)(?=\n\*\*[A-Z]|\n\n---|\Z)',
        rf'\*\*{re.escape(section_name)}:\*\*\s*(.+?)(?=\n\*\*[A-Z]|\n\n---|\Z)',
        rf'^{re.escape(section_name)}:\s*\n(.+?)(?=\n[A-Z]|\Z)',
        rf'^{re.escape(section_name)}:\s*(.+?)(?=\n[A-Z]|\Z)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            return match.group(1).strip() if match.groups() else content[match.end():].strip()
    
    return None


def extract_phase3_structured(file_path: Path) -> List[BaseExemplar]:
    """Extract base exemplars from Phase-3 document.
    Returns structured dataclass instances."""
    print(f"Reading Phase-3 document: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    bases = []
    
    # Find all base exemplar sections
    base_pattern = r'^### (BASE-\d{3}):\s*(.+?)\s*\((\w+)\)'
    matches = list(re.finditer(base_pattern, content, re.MULTILINE))
    
    if len(matches) != 17:
        raise ValueError(f"Expected 17 base exemplars, found {len(matches)}")
    
    for match in matches:
        base_id = match.group(1)
        title = match.group(2)
        phase = match.group(3)
        
        # Find the section content
        section_start = match.start()
        next_header = re.search(r'^### ', content[section_start + 1:], re.MULTILINE)
        if next_header:
            section_end = section_start + 1 + next_header.start()
        else:
            section_end = len(content)
        
        section_content = content[section_start:section_end]
        
        # Extract boundary phrase (canonical rule: exactly one fenced block)
        boundary_phrase = extract_phase3_boundary_first_block_strict(section_content, base_id)
        
        # Extract Response Posture verbatim
        response_posture_text = extract_response_posture_verbatim(section_content)
        if not response_posture_text:
            raise ValueError(f"Could not find Response Posture for {base_id}")
        
        # Input must preserve canonical wording/structure (verbatim slicing).
        # Concatenate Dominant Signal Ambiguity + Intent Pressure as written, without synthetic prefixes.
        dom_marker_bold = "**Dominant Signal Ambiguity:**"
        dom_marker_plain = "Dominant Signal Ambiguity:"
        rp_marker_bold = "**Response Posture:**"
        rp_marker_plain = "Response Posture:"

        dom_idx = section_content.find(dom_marker_bold)
        if dom_idx == -1:
            dom_idx = section_content.find(dom_marker_plain)
        if dom_idx == -1:
            raise ValueError(f"Missing Dominant Signal Ambiguity section in {base_id}")

        rp_idx = section_content.find(rp_marker_bold, dom_idx)
        if rp_idx == -1:
            rp_idx = section_content.find(rp_marker_plain, dom_idx)
        if rp_idx == -1:
            raise ValueError(f"Missing Response Posture section marker in {base_id}")

        input_text = section_content[dom_idx:rp_idx].strip() if dom_idx < rp_idx else title
        
        bases.append(BaseExemplar(
            base_id=base_id,
            phase=phase,
            boundary_phrase=normalize_boundary(boundary_phrase),
            input_text=input_text,
            output_text=response_posture_text,
            response_posture=response_posture_text
        ))
    
    print(f"Parsed {len(bases)} base exemplars")
    return bases


def extract_phase4_structured(file_path: Path, bases: Dict[str, BaseExemplar]) -> List[VariantExemplar]:
    """Extract variants from Phase-4 document.
    Requires bases dict to inherit phase."""
    print(f"Reading Phase-4 document: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    variants = []
    
    # Find all variant sections
    variant_pattern = r'^### (BASE-\d{3}-V[1-4]):\s*(.+?)$'
    matches = list(re.finditer(variant_pattern, content, re.MULTILINE))
    
    if len(matches) != 68:
        raise ValueError(f"Expected 68 variants, found {len(matches)}")
    
    for match in matches:
        variant_id = match.group(1)
        variant_type = match.group(2)
        
        # Extract base_id
        base_match = re.match(r'(BASE-\d{3})-V\d', variant_id)
        if not base_match:
            raise ValueError(f"Invalid variant ID format: {variant_id}")
        base_id = base_match.group(1)
        
        if base_id not in bases:
            raise ValueError(f"Variant {variant_id} references unknown base {base_id}")
        
        base = bases[base_id]
        
        # Find the section content
        section_start = match.start()
        next_header = re.search(r'^### ', content[section_start + 1:], re.MULTILINE)
        if next_header:
            section_end = section_start + 1 + next_header.start()
        else:
            section_end = len(content)
        
        section_content = content[section_start:section_end]
        
        # Extract boundary phrase (first code block only)
        boundary_phrase = extract_code_block(section_content, "Boundary Phrase:")
        if not boundary_phrase:
            boundary_phrase = extract_code_block(section_content, "Boundary phrase:")
        
        if not boundary_phrase:
            raise ValueError(f"Could not find boundary phrase for {variant_id}")
        
        # Verify boundary matches base exactly (strict full-string equality).
        normalized_variant_boundary = normalize_boundary(boundary_phrase)
        if normalized_variant_boundary != base.boundary_phrase:
            raise ValueError(
                f"Boundary phrase mismatch for {variant_id}:\n"
                f"Base:     {base.boundary_phrase[:100]}...\n"
                f"Variant:  {normalized_variant_boundary[:100]}..."
            )
        
        # Extract input text via verbatim slicing from the first context section to Response Posture/Validation.
        context_markers = [
            "**Variant Text:**",
            "**Collision Context:**",
            "**Illegitimacy Context:**",
            "**Enforcement Context:**",
            "Variant Text:",
            "Collision Context:",
            "Illegitimacy Context:",
            "Enforcement Context:",
        ]
        ctx_positions = [(m, section_content.find(m)) for m in context_markers]
        ctx_positions = [(m, p) for (m, p) in ctx_positions if p != -1]
        if not ctx_positions:
            raise ValueError(f"Missing context section (Variant/Collision/Illegitimacy/Enforcement) in {variant_id}")

        ctx_start = min(p for (_m, p) in ctx_positions)

        # End at Response Posture marker if present, otherwise stop at Validation (DES variants may omit posture).
        rp_bold = section_content.find("**Response Posture:**", ctx_start)
        rp_plain = section_content.find("Response Posture:", ctx_start)
        end_candidates = [p for p in [rp_bold, rp_plain] if p != -1]
        if not end_candidates:
            val_bold = section_content.find("**Validation:**", ctx_start)
            val_plain = section_content.find("Validation:", ctx_start)
            end_candidates = [p for p in [val_bold, val_plain] if p != -1]
        ctx_end = min(end_candidates) if end_candidates else len(section_content)

        input_text = section_content[ctx_start:ctx_end].strip()
        
        # Extract Response Posture verbatim
        response_posture_text = extract_response_posture_verbatim(section_content)
        if not response_posture_text:
            # For DES variants, Response Posture may be implicit - use base posture
            if base.phase == "DES":
                # Design invariant: DES variants reuse base response posture.
                # Variants do not alter design semantics.
                response_posture_text = base.response_posture
            else:
                raise ValueError(f"Could not find Response Posture for {variant_id}")
        
        variants.append(VariantExemplar(
            base_id=base_id,
            variant_id=variant_id,
            phase=base.phase,
            boundary_phrase=normalized_variant_boundary,
            input_text=input_text.strip(),
            output_text=response_posture_text,
            response_posture=response_posture_text
        ))
    
    print(f"Parsed {len(variants)} variants across {len(set(v.base_id for v in variants))} bases")
    return variants


def parse_phase_distribution_from_phase3(file_path: Path) -> Dict[str, int]:
    """Parse expected phase distribution from Phase-3 summary section."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find Phase Distribution section
    dist_section_match = re.search(
        r'## Phase Distribution\s*\n(.*?)(?=\n##|\Z)',
        content,
        re.DOTALL
    )
    
    if not dist_section_match:
        raise ValueError("Could not find Phase Distribution section in Phase-3 document")
    
    dist_section = dist_section_match.group(1)
    
    # Extract phase counts
    phase_counts = {}
    patterns = [
        r'\*\*REF.*?:\*\*\s*(\d+)',
        r'\*\*CONF.*?:\*\*\s*(\d+)',
        r'\*\*DES.*?:\*\*\s*(\d+)',
        r'\*\*MIX.*?:\*\*\s*(\d+)',
        r'\*\*CODE.*?:\*\*\s*(\d+)',
    ]
    
    phase_names = ["REF", "CONF", "DES", "MIX", "CODE"]
    for pattern, phase in zip(patterns, phase_names):
        match = re.search(pattern, dist_section)
        if match:
            phase_counts[phase] = int(match.group(1))
    
    return phase_counts


def validate_extracted_data(
    bases: List[BaseExemplar],
    variants: List[VariantExemplar],
    phase3_file: Path
) -> Tuple[bool, List[str], List[str]]:
    """Validate extracted data. Compute distributions from data, don't hardcode."""
    errors = []
    warnings = []
    
    # Count validation
    base_ids = [b.base_id for b in bases]
    variant_ids = [v.variant_id for v in variants]
    
    if len(set(base_ids)) != 17:
        errors.append(f"Expected 17 unique base_ids, found {len(set(base_ids))}")
    
    if len(set(variant_ids)) != 68:
        errors.append(f"Expected 68 unique variant_ids, found {len(set(variant_ids))}")
    
    if len(bases) + len(variants) != 85:
        errors.append(f"Expected 85 total records, found {len(bases) + len(variants)}")
    
    # Duplicate check
    all_sample_ids = base_ids + variant_ids
    duplicates = [sid for sid in all_sample_ids if all_sample_ids.count(sid) > 1]
    if duplicates:
        errors.append(f"Duplicate sample_id values found: {set(duplicates)}")

    # Enforce structural symmetry: exactly 4 variants per base
    variants_per_base = defaultdict(int)
    for v in variants:
        variants_per_base[v.base_id] += 1
    for base_id in set(base_ids):
        if variants_per_base[base_id] != 4:
            errors.append(
                f"Base {base_id} has {variants_per_base[base_id]} variants; expected exactly 4."
            )
    
    # Phase distribution validation (from Phase-3 summary)
    expected_phase_dist = parse_phase_distribution_from_phase3(phase3_file)
    actual_phase_dist = defaultdict(int)
    for base in bases:
        actual_phase_dist[base.phase] += 1
    
    for phase, expected_count in expected_phase_dist.items():
        actual_count = actual_phase_dist.get(phase, 0)
        if actual_count != expected_count:
            errors.append(
                f"Phase {phase}: expected {expected_count} bases (from Phase-3 summary), found {actual_count}"
            )
    
    # Required fields check
    for base in bases:
        if not all([base.base_id, base.phase, base.boundary_phrase, base.input_text, base.output_text]):
            errors.append(f"Base {base.base_id} missing required fields")
    
    for variant in variants:
        if not all([variant.base_id, variant.variant_id, variant.phase, variant.boundary_phrase, variant.input_text, variant.output_text]):
            errors.append(f"Variant {variant.variant_id} missing required fields")
    
    # Optional semantic sanity checks (warnings only)
    for base in bases:
        if base.phase == "REF" and "cannot" not in base.output_text.lower() and "refuse" not in base.output_text.lower():
            warnings.append(f"Base {base.base_id} (REF) output may not contain refusal language")
        if base.phase == "CONF" and base.boundary_phrase.lower() not in base.output_text.lower():
            warnings.append(f"Base {base.base_id} (CONF) output may not mention boundary phrase")
        if base.phase == "CODE" and "guard" not in base.output_text.lower() and "enforcement" not in base.output_text.lower():
            warnings.append(f"Base {base.base_id} (CODE) output may not mention guard/enforcement")
    
    return len(errors) == 0, errors, warnings


def create_stratified_split(
    records: List[Dict],
    seed: int = 42
) -> Tuple[List[Dict], List[Dict], List[str]]:
    """Create train/val split with edge-case handling for small classes."""
    random.seed(seed)
    
    records_by_phase = defaultdict(list)
    for record in records:
        records_by_phase[record["phase"]].append(record)
    
    train_records = []
    val_records = []
    warnings = []
    
    for phase, phase_records in records_by_phase.items():
        class_count = len(phase_records)
        
        if class_count >= 3:
            # Can stratify
            random.shuffle(phase_records)
            n_val = round(class_count * 0.1)
            if n_val == 0:
                n_val = 1
            
            train_records.extend(phase_records[:class_count - n_val])
            val_records.extend(phase_records[class_count - n_val:])
        else:
            # Too small to stratify - keep all in train
            train_records.extend(phase_records)
            warnings.append(f"Phase {phase} has {class_count} samples, keeping all in train")
    
    # Shuffle final lists for deterministic but random order
    random.shuffle(train_records)
    random.shuffle(val_records)
    
    return train_records, val_records, warnings


def map_to_dataset_record(
    exemplar: Union[BaseExemplar, VariantExemplar],
    instruction: str
) -> Dict:
    """Map structured exemplar to dataset record format."""
    if isinstance(exemplar, BaseExemplar):
        return {
            "sample_id": exemplar.base_id,
            "base_id": exemplar.base_id,
            "variant_id": None,
            "phase": exemplar.phase,
            "instruction": instruction,
            "input": exemplar.input_text,
            "output": exemplar.output_text,
            "irreversible_boundary": exemplar.boundary_phrase,
            "expected_posture": PHASE_TO_POSTURE[exemplar.phase],
        }
    else:
        return {
            "sample_id": exemplar.variant_id,
            "base_id": exemplar.base_id,
            "variant_id": exemplar.variant_id,
            "phase": exemplar.phase,
            "instruction": instruction,
            "input": exemplar.input_text,
            "output": exemplar.output_text,
            "irreversible_boundary": exemplar.boundary_phrase,
            "expected_posture": PHASE_TO_POSTURE[exemplar.phase],
        }


def generate_statistics(
    records: List[Dict],
    train_records: List[Dict],
    val_records: List[Dict],
    warnings: List[str],
    repo_path: Path
) -> Dict:
    """Generate comprehensive statistics."""
    phase_counts = defaultdict(int)
    train_phase_counts = defaultdict(int)
    val_phase_counts = defaultdict(int)
    
    for record in records:
        phase_counts[record["phase"]] += 1
    for record in train_records:
        train_phase_counts[record["phase"]] += 1
    for record in val_records:
        val_phase_counts[record["phase"]] += 1
    
    input_lengths = [len(r["input"]) for r in records]
    output_lengths = [len(r["output"]) for r in records]
    
    # Token approximation: split on whitespace
    input_tokens = [len(r["input"].split()) for r in records]
    output_tokens = [len(r["output"].split()) for r in records]
    
    stats = {
        "total_samples": len(records),
        "phase_counts": dict(phase_counts),
        "train_phase_counts": dict(train_phase_counts),
        "val_phase_counts": dict(val_phase_counts),
        "instruction_version": "v1",
        "seed": 42,
        "build_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_commit_hash": get_git_commit_hash(repo_path),
        "avg_input_chars": sum(input_lengths) / len(input_lengths) if input_lengths else 0,
        "avg_output_chars": sum(output_lengths) / len(output_lengths) if output_lengths else 0,
        "approx_input_tokens": sum(input_tokens) / len(input_tokens) if input_tokens else 0,
        "approx_output_tokens": sum(output_tokens) / len(output_tokens) if output_tokens else 0,
        "max_input_chars": max(input_lengths) if input_lengths else 0,
        "max_output_chars": max(output_lengths) if output_lengths else 0,
        "warnings": warnings,
    }
    
    return stats


def write_jsonl(records: List[Dict], file_path: Path):
    """Write records to JSONL file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')


def write_output_files(
    records: List[Dict],
    train_records: List[Dict],
    val_records: List[Dict],
    stats: Dict,
    output_dir: Path,
    force: bool = False
) -> List[Path]:
    """Write output files. Require --force to overwrite."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    created_files = []
    
    output_files = {
        "golden_exemplars_v1.jsonl": records,
        "golden_exemplars_v1_train.jsonl": train_records,
        "golden_exemplars_v1_val.jsonl": val_records,
    }
    
    for filename, data in output_files.items():
        file_path = output_dir / filename
        if file_path.exists() and not force:
            print(f"  ⚠ Skipping {filename} (exists, use --force to overwrite)")
            continue
        
        write_jsonl(data, file_path)
        created_files.append(file_path)
        print(f"  ✓ Wrote {filename} ({len(data)} records)")
    
    # Write statistics
    stats_file = output_dir / "golden_exemplars_v1_stats.json"
    if stats_file.exists() and not force:
        print(f"  ⚠ Skipping stats file (exists, use --force to overwrite)")
    else:
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        created_files.append(stats_file)
        print(f"  ✓ Wrote golden_exemplars_v1_stats.json")
    
    return created_files


def print_summary(records: List[Dict], train_records: List[Dict], val_records: List[Dict], stats: Dict, warnings: List[str]):
    """Print dataset summary."""
    print("\n" + "="*80)
    print("DATASET SUMMARY")
    print("="*80)
    
    print(f"\nTotal Samples: {stats['total_samples']}")
    print(f"  - Training: {len(train_records)}")
    print(f"  - Validation: {len(val_records)}")
    
    print("\nPhase Distribution (All Records):")
    for phase, count in sorted(stats['phase_counts'].items()):
        print(f"  - {phase}: {count}")
    
    print("\nTrain/Val Split by Phase:")
    for phase in sorted(set(stats['train_phase_counts'].keys()) | set(stats['val_phase_counts'].keys())):
        train_count = stats['train_phase_counts'].get(phase, 0)
        val_count = stats['val_phase_counts'].get(phase, 0)
        print(f"  - {phase}: Train={train_count}, Val={val_count}")
    
    print("\nLength Statistics:")
    print(f"  - Avg Input: {stats['avg_input_chars']:.1f} chars ({stats['approx_input_tokens']:.1f} tokens)")
    print(f"  - Avg Output: {stats['avg_output_chars']:.1f} chars ({stats['approx_output_tokens']:.1f} tokens)")
    print(f"  - Max Input: {stats['max_input_chars']} chars")
    print(f"  - Max Output: {stats['max_output_chars']} chars")
    
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  ⚠ {warning}")
    
    print("\n" + "="*80)


def main():
    parser = argparse.ArgumentParser(description="Build Golden Exemplars Dataset")
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing files")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()
    
    # Set up paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent.parent
    source_dir = repo_root / "ml" / "training" / "src" / "sources" / "Motadata"
    output_dir = repo_root / "datasets" / "sft"
    
    phase3_file = source_dir / "PHASE3_BASE_EXEMPLAR_MAPPING.md"
    phase4_file = source_dir / "PHASE4_VARIANT_GENERATION.md"
    
    if not phase3_file.exists():
        print(f"ERROR: Phase-3 file not found: {phase3_file}", file=sys.stderr)
        sys.exit(1)
    
    if not phase4_file.exists():
        print(f"ERROR: Phase-4 file not found: {phase4_file}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Extract structured data
        bases_list = extract_phase3_structured(phase3_file)
        bases_dict = {b.base_id: b for b in bases_list}
        variants_list = extract_phase4_structured(phase4_file, bases_dict)
        
        # Validate
        print("\nValidating extracted data...")
        is_valid, errors, warnings = validate_extracted_data(bases_list, variants_list, phase3_file)
        
        if errors:
            print("ERROR: Validation failed:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            sys.exit(1)
        
        print("✓ Validation passed")
        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"  ⚠ {warning}")
        
        # Map to dataset records
        print("\nConstructing dataset records...")
        base_records = [map_to_dataset_record(b, INSTRUCTION_V1) for b in bases_list]
        variant_records = [map_to_dataset_record(v, INSTRUCTION_V1) for v in variants_list]
        all_records = base_records + variant_records
        
        # Sort for deterministic ordering
        all_records.sort(key=lambda r: (r["base_id"], r["variant_id"] or ""))
        
        # Create train/val split
        print("\nCreating train/val split...")
        train_records, val_records, split_warnings = create_stratified_split(all_records)
        all_warnings = warnings + split_warnings
        
        # Generate statistics
        stats = generate_statistics(all_records, train_records, val_records, all_warnings, repo_root)
        
        # Print summary
        print_summary(all_records, train_records, val_records, stats, all_warnings)
        
        if args.dry_run:
            print("\n✓ Dry-run complete. No files written.")
            return
        
        # Write files
        print("\nWriting output files...")
        created_files = write_output_files(
            all_records, train_records, val_records, stats, output_dir, args.force
        )
        
        print("\n✓ Dataset build complete!")
        print(f"\nOutput directory: {output_dir}")
        print("Files created:")
        for file_path in created_files:
            print(f"  - {file_path}")
        
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
