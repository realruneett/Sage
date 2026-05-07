#!/bin/bash
# Record OOM contrast demo

tmux new-session -d -s sage_code_demo
tmux send-keys -t sage_code_demo "python3 demos/demo_sage_code.py" C-m
tmux split-window -h -t sage_code_demo
tmux send-keys -t sage_code_demo "python3 demos/demo_h100_simulation.py" C-m
tmux attach-session -t sage_code_demo
