#!/usr/bin/env python3
"""
CUDA + PyTorch compatibility check.
Verifies driver vs PyTorch CUDA build and tests bf16 support.

Run with Stage-08 training venv (no system pip):
  ml/training/pipeline/stage6/.venv/bin/python cuda-pytorch_test.py
  # Or project root: .venv/bin/python cuda-pytorch_test.py

PyTorch: use a build matching your GPU. Blackwell (sm_120) needs CUDA 12.8 or 13.0;
  cu126 supports up to sm_90. See https://pytorch.org/get-started/locally
"""

import subprocess
import sys


def get_system_cuda_info():
    """Driver and CUDA version from nvidia-smi."""
    import re
    driver, name = None, None
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=driver_version,name", "--format=csv,noheader"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        driver_line = out.strip().split("\n")[0]
        parts = [p.strip() for p in driver_line.split(",", 1)]
        driver = parts[0] if parts else "unknown"
        name = parts[1] if len(parts) > 1 else "unknown"
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None, None, None
    cuda_sys = None
    try:
        full = subprocess.check_output(["nvidia-smi"], text=True, stderr=subprocess.DEVNULL)
        for line in full.splitlines():
            if "CUDA Version:" in line:
                m = re.search(r"CUDA Version:\s*(\d+\.\d+)", line)
                cuda_sys = m.group(1) if m else None
                break
    except Exception:
        pass
    return driver, name, cuda_sys


def main():
    print("=" * 60)
    print("CUDA + PyTorch compatibility check")
    print("=" * 60)

    # --- System (driver + CUDA) ---
    driver, gpu_name, cuda_sys = get_system_cuda_info()
    if driver is None:
        print("\n[FAIL] nvidia-smi not found or no GPU. Install drivers and ensure GPU is visible.")
        sys.exit(1)
    print(f"\nSystem:")
    print(f"  Driver:     {driver}")
    print(f"  CUDA (smi): {cuda_sys or 'N/A'}")
    print(f"  GPU:        {gpu_name}")

    # --- PyTorch ---
    try:
        import torch
    except ImportError:
        print("\n[FAIL] PyTorch not installed.")
        print("  See script docstring for pip install commands (cu124/cu126 or pytorch.org for CUDA 13).")
        sys.exit(1)

    cuda_pt = torch.version.cuda
    print(f"\nPyTorch:")
    print(f"  Version:    {torch.__version__}")
    print(f"  CUDA (build): {cuda_pt or 'CPU-only'}")

    # --- Compatibility ---
    ok = True
    if not cuda_pt:
        print("\n[WARN] PyTorch was built without CUDA (CPU-only). Reinstall with CUDA for GPU.")
        ok = False
    elif cuda_sys:
        # Driver supports a range; typically driver supports same or higher CUDA.
        # Compare major.minor loosely: e.g. driver 13.1 supports PyTorch built with 13.0/12.x.
        try:
            sys_maj, sys_min = map(int, cuda_sys.split(".")[:2])
            pt_maj, pt_min = map(int, (cuda_pt or "0.0").split(".")[:2])
            if sys_maj < pt_maj or (sys_maj == pt_maj and sys_min < pt_min):
                print(f"\n[WARN] Driver CUDA ({cuda_sys}) may be older than PyTorch CUDA ({cuda_pt}). Consider updating driver.")
                ok = False
            else:
                print(f"\n[OK] Driver CUDA ({cuda_sys}) is compatible with PyTorch CUDA ({cuda_pt}).")
        except (ValueError, IndexError):
            print(f"\n[OK] Driver and PyTorch CUDA reported (manual check: driver {cuda_sys}, PyTorch {cuda_pt}).")

    # --- CUDA available ---
    if not torch.cuda.is_available():
        print("\n[FAIL] torch.cuda.is_available() is False.")
        ok = False
    else:
        print(f"  Device:     {torch.cuda.get_device_name(0)}")
        print(f"  Device cap: {torch.cuda.get_device_capability(0)}")

    # --- bf16 support ---
    print("\nBF16 (bfloat16) support:")
    bf16_ok = False
    if not torch.cuda.is_available():
        print("  Skipped (no CUDA).")
    else:
        try:
            supported = torch.cuda.is_bf16_supported()
            print(f"  torch.cuda.is_bf16_supported(): {supported}")
            if supported:
                # Explicit test: create bf16 tensor on GPU and run an op
                x = torch.randn(4, 4, device="cuda", dtype=torch.bfloat16)
                y = torch.nn.functional.relu(x)
                z = x @ y
                assert z.dtype == torch.bfloat16 and z.is_cuda
                print("  Runtime test: randn -> relu -> matmul on GPU (bf16): OK")
                bf16_ok = True
            else:
                print("  Runtime test: skipped (bf16 not reported supported).")
                ok = False
        except Exception as e:
            print(f"  Runtime test: FAIL - {e}")
            ok = False

    print("\n" + "=" * 60)
    if ok and (bf16_ok or not torch.cuda.is_available()):
        print("Result: All checks passed.")
    else:
        print("Result: Some checks failed or reported warnings.")
    print("=" * 60)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
