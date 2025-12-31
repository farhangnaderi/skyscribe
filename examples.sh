#!/bin/bash
# Example usage scripts for text-to-drone-path converter

# Ensure virtual environment is activated
source venv/bin/activate

echo "Text-to-Drone-Path Converter Examples"
echo "======================================"
echo ""

# Example 1: Basic usage
echo "Example 1: Basic 'HELLO' message"
python text_to_drone_path.py "HELLO" --lat 47.397 --lon 8.545 --alt 488 -v
echo ""

# Example 2: Large letters at high altitude
echo "Example 2: Large letters (50m) at 100m altitude"
python text_to_drone_path.py "BIG" --lat 47.397 --lon 8.545 --alt 488 \
    --letter-height 50 --flight-alt 100 -v
echo ""

# Example 3: Rotated text
echo "Example 3: Rotated 45 degrees"
python text_to_drone_path.py "NORTH" --lat 47.397 --lon 8.545 --alt 488 \
    --rotation 45 --output north_rotated.plan -v
echo ""

# Example 4: Different font
echo "Example 4: Script font"
python text_to_drone_path.py "Sky" --lat 47.397 --lon 8.545 --alt 488 \
    --font scriptc --output sky_script.plan -v
echo ""

# Example 5: Fast flight, no optimizations
echo "Example 5: Fast flight, raw waypoints"
python text_to_drone_path.py "FAST" --lat 47.397 --lon 8.545 --alt 488 \
    --speed 5.0 --no-simplify --no-optimize -v
echo ""

echo "All examples completed!"
echo "Generated .plan files can be uploaded to QGroundControl"
