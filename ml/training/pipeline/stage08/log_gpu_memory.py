"""Step 6: Log GPU memory after loading base model in bf16."""
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM

SCRIPT_DIR = Path(__file__).resolve().parent
model_path = SCRIPT_DIR / "base_model"

torch.backends.cuda.enable_flash_sdp(False)
torch.backends.cuda.enable_mem_efficient_sdp(False)
torch.backends.cuda.enable_math_sdp(True)

dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
model = AutoModelForCausalLM.from_pretrained(
    str(model_path),
    dtype=dtype,
    device_map="auto",
    trust_remote_code=True,
)

allocated_gb = torch.cuda.memory_allocated(0) / 1e9
reserved_gb = torch.cuda.memory_reserved(0) / 1e9
total_vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9

lines = [
    f"Allocated memory (GB): {allocated_gb:.2f}",
    f"Reserved memory (GB): {reserved_gb:.2f}",
    f"Total VRAM (GB): {total_vram_gb:.2f}",
    f"< 60GB allocated: {allocated_gb < 60}",
]
out = SCRIPT_DIR / "logs" / "gpu_memory_post_fix.txt"
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, "w") as f:
    f.write("\n".join(lines))
print("\n".join(lines))
