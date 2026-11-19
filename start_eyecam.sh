#!/bin/bash
set -e

cd /home/eyecam/EyeCam/app/
exec /home/eyecam/miniforge3/envs/ultralytics-env/bin/python -u main.py

