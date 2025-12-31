#!/usr/bin/env python3
"""
Simple path visualization tool (text-based).
Shows the 2D layout of text paths before GPS conversion.
"""

import sys
from skyink.font_extractor import FontExtractor
from skyink.path_simplifier import PathSimplifier


def visualize_paths_ascii(paths, width=80, height=24):
    """
    Create ASCII art visualization of paths.

    Args:
        paths: List of paths to visualize
        width: Terminal width in characters
        height: Terminal height in characters
    """
    if not paths:
        print("No paths to visualize")
        return

    # Find bounds
    all_points = []
    for path in paths:
        all_points.extend(path)

    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # Add padding
    padding = 0.1
    range_x = max_x - min_x
    range_y = max_y - min_y
    min_x -= range_x * padding
    max_x += range_x * padding
    min_y -= range_y * padding
    max_y += range_y * padding

    # Create canvas
    canvas = [[' ' for _ in range(width)] for _ in range(height)]

    # Draw paths
    for path_idx, path in enumerate(paths):
        for i, (x, y) in enumerate(path):
            # Convert to canvas coordinates
            col = int((x - min_x) / (max_x - min_x) * (width - 1))
            row = int((1 - (y - min_y) / (max_y - min_y)) * (height - 1))

            # Clip to canvas
            col = max(0, min(width - 1, col))
            row = max(0, min(height - 1, row))

            # Draw point
            if i == 0:
                canvas[row][col] = 'o'  # Start of stroke
            else:
                canvas[row][col] = '*'  # Path point

    # Print canvas
    print("+" + "-" * width + "+")
    for row in canvas:
        print("|" + "".join(row) + "|")
    print("+" + "-" * width + "+")

    # Print stats
    print(f"\nBounds: x=[{min_x:.1f}, {max_x:.1f}]m, y=[{min_y:.1f}, {max_y:.1f}]m")
    print(f"Strokes: {len(paths)}")
    print(f"Total points: {sum(len(p) for p in paths)}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python visualize_path.py <text> [--font <font>] [--height <meters>]")
        print("\nExample:")
        print("  python visualize_path.py HELLO")
        print("  python visualize_path.py DRONE --font scriptc --height 30")
        return 1

    # Simple argument parsing
    text = sys.argv[1]
    font_name = 'futural'
    letter_height = 20.0

    for i in range(2, len(sys.argv)):
        if sys.argv[i] == '--font' and i + 1 < len(sys.argv):
            font_name = sys.argv[i + 1]
        elif sys.argv[i] == '--height' and i + 1 < len(sys.argv):
            letter_height = float(sys.argv[i + 1])

    print(f"Text: {text}")
    print(f"Font: {font_name}")
    print(f"Letter height: {letter_height}m")
    print()

    # Extract paths
    extractor = FontExtractor(font_name=font_name, letter_height_m=letter_height)
    paths = extractor.extract_continuous_paths(text)

    print(f"Original paths ({sum(len(p) for p in paths)} points):")
    visualize_paths_ascii(paths)

    # Show simplified version
    simplifier = PathSimplifier(letter_height_m=letter_height)
    simplified_paths = simplifier.simplify_paths(paths)

    print(f"\nSimplified paths ({sum(len(p) for p in simplified_paths)} points):")
    visualize_paths_ascii(simplified_paths)

    reduction = 100 * (1 - sum(len(p) for p in simplified_paths) / sum(len(p) for p in paths))
    print(f"\nPath simplification: {reduction:.1f}% reduction")

    return 0


if __name__ == '__main__':
    sys.exit(main())
