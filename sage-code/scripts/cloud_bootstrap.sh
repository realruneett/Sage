#!/bin/bash
# One-liner to bootstrap SAGE-CODE on AMD Developer Cloud

sudo apt update && sudo apt install -y docker.io docker-compose firejail
sudo usermod -aG docker $USER

git clone https://github.com/user/sage-code
cd sage-code

echo "Bootstrap complete. Run 'docker compose up' next."
