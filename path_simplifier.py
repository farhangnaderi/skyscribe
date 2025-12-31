"""
Path simplification using Douglas-Peucker algorithm.
Reduces waypoint count while preserving letter shape and corners.
"""

from simplification.cutil import simplify_coords
import numpy as np


class PathSimplifier:
    """Simplify paths using Douglas-Peucker algorithm."""

    def __init__(self, epsilon=None, letter_height_m=20):
        """
        Initialize path simplifier.

        Args:
            epsilon: Tolerance for simplification in meters.
                     If None, auto-calculated as 2% of letter height.
            letter_height_m: Letter height in meters (for auto-epsilon calculation)
        """
        if epsilon is None:
            # Default: 2% of letter height for good balance
            self.epsilon = letter_height_m * 0.02
        else:
            self.epsilon = epsilon

        self.letter_height_m = letter_height_m

    def simplify_path(self, points):
        """
        Simplify a single path using Douglas-Peucker algorithm.

        Args:
            points: List of (x, y) tuples

        Returns:
            Simplified list of (x, y) tuples
        """
        if len(points) < 3:
            return points  # Cannot simplify

        # Convert to format expected by simplification library
        points_array = np.array(points, dtype=np.float64)

        # Apply Douglas-Peucker simplification
        simplified = simplify_coords(points_array, self.epsilon)

        return [tuple(p) for p in simplified]

    def simplify_paths(self, paths):
        """
        Simplify multiple paths.

        Args:
            paths: List of paths, where each path is a list of (x, y) tuples

        Returns:
            List of simplified paths
        """
        return [self.simplify_path(path) for path in paths]

    def simplify_with_corner_preservation(self, points, corner_angle_threshold=30):
        """
        Simplify path while explicitly preserving sharp corners.
        Detects corners and splits path at these points before simplification.

        Args:
            points: List of (x, y) tuples
            corner_angle_threshold: Angle change in degrees to consider a corner

        Returns:
            Simplified list of (x, y) tuples with corners preserved
        """
        if len(points) < 3:
            return points

        # Detect corners
        corner_indices = self._detect_corners(points, corner_angle_threshold)

        # If no corners, simplify entire path
        if not corner_indices:
            return self.simplify_path(points)

        # Split path at corners, simplify each segment, then recombine
        segments = []
        start_idx = 0

        for corner_idx in corner_indices + [len(points)]:
            segment = points[start_idx:corner_idx+1]
            if len(segment) >= 2:
                simplified_segment = self.simplify_path(segment)
                # Avoid duplicate points when joining segments
                if segments and len(simplified_segment) > 0:
                    segments.append(simplified_segment[1:])
                else:
                    segments.append(simplified_segment)
            start_idx = corner_idx

        # Flatten segments
        result = []
        for seg in segments:
            result.extend(seg)

        return result

    def _detect_corners(self, points, angle_threshold):
        """
        Detect sharp corners in a path based on angle change.

        Args:
            points: List of (x, y) tuples
            angle_threshold: Angle change in degrees to consider a corner

        Returns:
            List of indices where corners occur
        """
        corners = []

        for i in range(1, len(points) - 1):
            # Calculate angle at point i
            p1 = np.array(points[i-1])
            p2 = np.array(points[i])
            p3 = np.array(points[i+1])

            # Vectors
            v1 = p1 - p2
            v2 = p3 - p2

            # Calculate angle between vectors
            v1_norm = np.linalg.norm(v1)
            v2_norm = np.linalg.norm(v2)

            if v1_norm == 0 or v2_norm == 0:
                continue

            cos_angle = np.dot(v1, v2) / (v1_norm * v2_norm)
            # Clamp to [-1, 1] to avoid numerical errors
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            angle_deg = np.degrees(np.arccos(cos_angle))

            # Check if angle change is significant
            if angle_deg > angle_threshold:
                corners.append(i)

        return corners

    def get_recommended_epsilon(self, letter_height_m):
        """
        Get recommended epsilon value based on letter height.

        Args:
            letter_height_m: Letter height in meters

        Returns:
            Recommended epsilon value in meters
        """
        if letter_height_m <= 10:
            return 0.2  # 10m letters: 0.1-0.3m
        elif letter_height_m <= 20:
            return 0.4  # 20m letters: 0.3-0.5m
        elif letter_height_m <= 50:
            return 0.75  # 50m letters: 0.5-1.0m
        else:
            return 1.5  # 100m+ letters: 1.0-2.0m


if __name__ == '__main__':
    # Test path simplification
    simplifier = PathSimplifier(epsilon=0.4, letter_height_m=20)

    # Create a test path with many points (simulating a curve)
    test_path = [(i, np.sin(i * 0.5)) for i in range(20)]

    print(f"Original path: {len(test_path)} points")
    simplified = simplifier.simplify_path(test_path)
    print(f"Simplified path: {len(simplified)} points")
    print(f"Reduction: {100 * (1 - len(simplified)/len(test_path)):.1f}%")

    # Test with corner preservation
    print("\nTesting corner preservation:")
    # Create path with a sharp corner (L shape)
    corner_path = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0),  # Horizontal
                   (4, 1), (4, 2), (4, 3), (4, 4)]  # Vertical

    simplified_corners = simplifier.simplify_with_corner_preservation(
        corner_path, corner_angle_threshold=30
    )
    print(f"L-shape path: {len(corner_path)} -> {len(simplified_corners)} points")
