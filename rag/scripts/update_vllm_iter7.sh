#!/bin/bash
echo "Updating vLLM configuration to use Iter 7 model..."
sudo sed -i 's|merged_models/motadata-coder-iter6|/home/harshil/Harshil-PoCs/Finetuning-Iter7/merged_models/motadata-coder-iter7|' /etc/systemd/system/motadata-coder.service
echo "Reloading systemd..."
sudo systemctl daemon-reload
echo "Restarting motadata-coder service..."
sudo systemctl restart motadata-coder
echo "Done! vLLM should now be serving Iter 7."
systemctl status motadata-coder --no-pager
