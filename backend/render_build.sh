#!/usr/bin/env bash
# render_build.sh - Build script for Render deployment
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
