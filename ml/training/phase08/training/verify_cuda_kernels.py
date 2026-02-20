"""Step 4 verification: Core CUDA functionality for sm_120."""
import torch
import torch.nn as nn

print("Torch version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
print("Device:", torch.cuda.get_device_name(0))
print("Capability:", torch.cuda.get_device_capability(0))
print("bf16 supported:", torch.cuda.is_bf16_supported())

# Basic CUDA tensor op
x = torch.randn(4, 4, device="cuda")
print("Matmul:", (x @ x).shape)

# LayerNorm forward + backward
x = torch.randn(8, 16, device="cuda", requires_grad=True)
ln = nn.LayerNorm(16).cuda()
y = ln(x).sum()
y.backward()
print("LayerNorm backward: OK")

# Simple AdamW step test
model = nn.Linear(16, 16).cuda()
opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
inp = torch.randn(8, 16, device="cuda")
out = model(inp).sum()
out.backward()
opt.step()
print("Optimizer step: OK")
