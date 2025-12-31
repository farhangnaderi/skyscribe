"""
Hershey font stroke extraction module.
Extracts single-stroke glyph paths from Hershey fonts.
"""

from HersheyFonts import HersheyFonts
import numpy as np


class FontExtractor:
    """Extract stroke paths from Hershey fonts."""

    def __init__(self, font_name='futural', letter_height_m=20):
        """
        Initialize font extractor.

        Args:
            font_name: Hershey font name (futural, futuram, scriptc, gothiceng)
            letter_height_m: Height of letters in meters
        """
        self.font = HersheyFonts()
        self.font.load_default_font(font_name)
        self.font.normalize_rendering(letter_height_m)
        self.letter_height_m = letter_height_m

    def extract_strokes(self, text):
        """
        Extract stroke paths for given text.

        Args:
            text: Text string to convert to strokes

        Returns:
            List of strokes, where each stroke is a list of (x, y) tuples
        """
        strokes = []

        # Get all line segments for the text
        for (x1, y1), (x2, y2) in self.font.lines_for_text(text):
            # Each line segment represents a stroke
            strokes.append([(x1, y1), (x2, y2)])

        return strokes

    def extract_continuous_paths(self, text):
        """
        Extract continuous paths (pen-down segments) for text.
        Groups consecutive connected line segments into continuous paths.

        Args:
            text: Text string to convert

        Returns:
            List of continuous paths, where each path is a list of (x, y) points
        """
        lines = list(self.font.lines_for_text(text))
        if not lines:
            return []

        paths = []
        current_path = [lines[0][0], lines[0][1]]  # Start with first line

        for i in range(1, len(lines)):
            prev_end = lines[i-1][1]
            curr_start = lines[i][0]

            # Check if current line connects to previous (within small tolerance)
            distance = np.sqrt((curr_start[0] - prev_end[0])**2 +
                             (curr_start[1] - prev_end[1])**2)

            if distance < 0.1:  # Connected - continue path
                current_path.append(lines[i][1])
            else:  # Disconnected - start new path
                paths.append(current_path)
                current_path = [lines[i][0], lines[i][1]]

        # Add the last path
        if current_path:
            paths.append(current_path)

        return paths

    def get_available_fonts(self):
        """Return list of available Hershey font names."""
        return ['futural', 'futuram', 'scriptc', 'gothiceng',
                'cursive', 'timesg', 'timesib', 'timesr']


if __name__ == '__main__':
    # Test the font extractor
    extractor = FontExtractor(letter_height_m=20)

    test_text = "HELLO"
    paths = extractor.extract_continuous_paths(test_text)

    print(f"Text: {test_text}")
    print(f"Number of continuous paths: {len(paths)}")
    print(f"Total waypoints: {sum(len(path) for path in paths)}")

    # Print first path as example
    if paths:
        print(f"\nFirst path ({len(paths[0])} points):")
        for i, (x, y) in enumerate(paths[0][:5]):  # Show first 5 points
            print(f"  Point {i}: x={x:.2f}m, y={y:.2f}m")
