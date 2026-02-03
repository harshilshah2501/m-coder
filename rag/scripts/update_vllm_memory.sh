#!/bin/bash
echo "Updating vLLM configuration..."
sudo sed -i 's/--gpu-memory-utilization 0.90/--gpu-memory-utilization 0.5/' /etc/systemd/system/motadata-coder.service
echo "Reloading systemd..."
sudo systemctl daemon-reload
echo "Restarting motadata-coder service..."
sudo systemctl restart motadata-coder
echo "Done! GPU memory should now be available."
nvidia-smi
