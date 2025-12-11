#!/bin/bash
cd ~/projects/NQHUB_v0

# Si ya existe la sesión, conectarse
tmux has-session -t nqhub 2>/dev/null

if [ $? != 0 ]; then
    # Crear sesión con 4 paneles
    tmux new-session -d -s nqhub -c ~/projects/NQHUB_v0
    tmux split-window -h -c ~/projects/NQHUB_v0
    tmux split-window -v -c ~/projects/NQHUB_v0
    tmux select-pane -t 0
    tmux split-window -v -c ~/projects/NQHUB_v0
    tmux select-pane -t 0
fi

tmux attach -t nqhub
