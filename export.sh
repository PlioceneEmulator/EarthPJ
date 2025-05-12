#!/bin/bash

# This script will help you export exact versions from your local environment

# Activate your virtual environment
source env/bin/activate  # or source venv/bin/activate

# Export exact versions
pip freeze > requirements-exact.txt

# Show what was exported
echo "Exported the following packages:"
cat requirements-exact.txt