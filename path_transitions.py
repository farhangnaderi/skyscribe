"""
Path transition handling for multi-stroke text paths.
Manages transitions between letters and strokes with altitude separation.
"""

import numpy as np


class PathTransitionHandler:
    """Handle transitions between letter strokes with altitude separation."""

    def __init__(self, write_altitude_m=30, transit_altitude_offset_m=10):
        """
        Initialize path transition handler.

        Args:
            write_altitude_m: Altitude for writing/tracing letters
            transit_altitude_offset_m: Additional altitude during transitions
        """
        self.write_altitude = write_altitude_m
        self.transit_altitude = write_altitude_m + transit_altitude_offset_m

    def add_transitions(self, paths, continuous_threshold=None):
        """
        Convert 2D paths to 3D with constant altitude.
        All waypoints are at the same flight altitude.

        Args:
            paths: List of 2D paths, where each path is a list of (x, y) tuples
            continuous_threshold: Unused (kept for API compatibility)

        Returns:
            Single continuous 3D path at constant altitude: [(x, y, z), ...]
        """
        if not paths:
            return []

        waypoints_3d = []

        for i, path in enumerate(paths):
            if not path:
                continue

            # Skip first point if it's the same as previous end (avoid duplicate)
            start_idx = 0
            if i > 0 and paths[i-1]:
                prev_end = paths[i-1][-1]
                curr_start = path[0]
                if prev_end[0] == curr_start[0] and prev_end[1] == curr_start[1]:
                    start_idx = 1

            # Add all points at constant write altitude
            for x, y in path[start_idx:]:
                waypoints_3d.append((x, y, self.write_altitude))

        return waypoints_3d


    def optimize_stroke_order(self, paths, method='nearest_neighbor'):
        """
        Optimize the order of paths to minimize total transition distance.

        Args:
            paths: List of paths to reorder
            method: 'nearest_neighbor' or 'original'

        Returns:
            Reordered list of paths
        """
        if method == 'original' or len(paths) <= 1:
            return paths

        if method == 'nearest_neighbor':
            return self._nearest_neighbor_order(paths)

        return paths

    def _nearest_neighbor_order(self, paths):
        """
        Reorder paths using nearest-neighbor heuristic.
        Minimizes total pen-up transition distance.

        Args:
            paths: List of paths

        Returns:
            Reordered paths
        """
        if not paths:
            return []

        # Start with first path
        ordered = [paths[0]]
        remaining = list(paths[1:])

        while remaining:
            # Find nearest path to the end of current path
            current_end = ordered[-1][-1]
            min_dist = float('inf')
            nearest_idx = 0

            for i, path in enumerate(remaining):
                # Distance from current end to next path start
                dist = self._point_distance(current_end, path[0])

                # Also consider distance to end (can reverse path)
                dist_reverse = self._point_distance(current_end, path[-1])

                if dist_reverse < dist:
                    dist = dist_reverse
                    # Mark for reversal (negative index)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_idx = -i - 1  # Negative means reverse
                else:
                    if dist < min_dist:
                        min_dist = dist
                        nearest_idx = i

            # Add nearest path
            if nearest_idx < 0:
                # Reverse the path
                path_idx = -nearest_idx - 1
                ordered.append(list(reversed(remaining[path_idx])))
                remaining.pop(path_idx)
            else:
                ordered.append(remaining[nearest_idx])
                remaining.pop(nearest_idx)

        return ordered

    def _point_distance(self, p1, p2):
        """Calculate Euclidean distance between two points."""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def calculate_transition_stats(self, paths):
        """
        Calculate statistics about path transitions.

        Args:
            paths: List of paths

        Returns:
            Dictionary with transition statistics
        """
        if len(paths) <= 1:
            return {
                'num_transitions': 0,
                'total_transition_distance': 0,
                'avg_transition_distance': 0,
                'max_transition_distance': 0
            }

        distances = []
        for i in range(1, len(paths)):
            prev_end = paths[i-1][-1]
            curr_start = paths[i][0]
            dist = self._point_distance(prev_end, curr_start)
            distances.append(dist)

        return {
            'num_transitions': len(distances),
            'total_transition_distance': sum(distances),
            'avg_transition_distance': np.mean(distances) if distances else 0,
            'max_transition_distance': max(distances) if distances else 0
        }

    def calculate_mission_time(self, waypoints_3d, flight_speed_m_s=3.0, acceleration_m_s2=3.0):
        """
        Calculate estimated mission time based on physics (acceleration, cruise, deceleration).

        Uses trapezoidal velocity profile for each segment:
        - Acceleration phase: 0 -> cruise speed
        - Cruise phase: constant speed
        - Deceleration phase: cruise speed -> 0

        Based on PX4 default acceleration values (~3 m/s²).

        Args:
            waypoints_3d: List of 3D waypoints [(x, y, z), ...]
            flight_speed_m_s: Cruise speed in meters per second
            acceleration_m_s2: Acceleration/deceleration in m/s² (default 3.0 based on PX4)

        Returns:
            Dictionary with time estimates in seconds
        """
        if len(waypoints_3d) <= 1:
            return {
                'total_time_s': 0,
                'total_time_formatted': '0s',
                'total_distance_m': 0
            }

        total_time = 0
        total_distance = 0

        for i in range(1, len(waypoints_3d)):
            prev = waypoints_3d[i-1]
            curr = waypoints_3d[i]

            # 3D distance for this segment
            dist = np.sqrt(
                (curr[0] - prev[0])**2 +
                (curr[1] - prev[1])**2 +
                (curr[2] - prev[2])**2
            )
            total_distance += dist

            # Time to accelerate from 0 to cruise speed: t = v / a
            t_accel = flight_speed_m_s / acceleration_m_s2

            # Distance covered during acceleration: d = 0.5 * a * t²
            d_accel = 0.5 * acceleration_m_s2 * t_accel**2

            # Same for deceleration
            t_decel = t_accel
            d_decel = d_accel

            # Check if segment is long enough for full accel/decel
            if dist <= (d_accel + d_decel):
                # Short segment: triangular velocity profile (never reach cruise speed)
                # Max speed reached: v_max = sqrt(a * dist)
                # Time: t = 2 * sqrt(dist / a)
                segment_time = 2 * np.sqrt(dist / acceleration_m_s2)
            else:
                # Long segment: trapezoidal profile
                d_cruise = dist - d_accel - d_decel
                t_cruise = d_cruise / flight_speed_m_s
                segment_time = t_accel + t_cruise + t_decel

            total_time += segment_time

        # Format time as minutes and seconds
        minutes = int(total_time // 60)
        seconds = int(total_time % 60)
        if minutes > 0:
            time_formatted = f"{minutes}m {seconds}s"
        else:
            time_formatted = f"{seconds}s"

        return {
            'total_time_s': total_time,
            'total_time_formatted': time_formatted,
            'total_distance_m': total_distance
        }


if __name__ == '__main__':
    # Test transition handling
    handler = PathTransitionHandler(write_altitude_m=30, transit_altitude_offset_m=10)

    # Create test paths (three disconnected line segments)
    test_paths = [
        [(0, 0), (10, 0), (10, 10)],      # First stroke
        [(20, 0), (20, 10), (30, 10)],    # Second stroke (disconnected)
        [(40, 0), (40, 10)]               # Third stroke
    ]

    print("Original paths:")
    for i, path in enumerate(test_paths):
        print(f"  Path {i}: {len(path)} points")

    # Add altitude transitions
    waypoints_3d = handler.add_transitions(test_paths)

    print(f"\nWith altitude transitions:")
    print(f"  Total waypoints: {len(waypoints_3d)}")
    print(f"  Sample waypoints:")
    for i in range(min(10, len(waypoints_3d))):
        x, y, z = waypoints_3d[i]
        print(f"    WP{i}: ({x:5.1f}, {y:5.1f}, {z:5.1f}m)")

    # Calculate transition stats
    stats = handler.calculate_transition_stats(test_paths)
    print(f"\nTransition statistics:")
    print(f"  Number of transitions: {stats['num_transitions']}")
    print(f"  Total transition distance: {stats['total_transition_distance']:.1f}m")
    print(f"  Average transition distance: {stats['avg_transition_distance']:.1f}m")
    print(f"  Max transition distance: {stats['max_transition_distance']:.1f}m")

    # Test path optimization
    print(f"\nPath optimization:")
    optimized = handler.optimize_stroke_order(test_paths, method='nearest_neighbor')
    optimized_stats = handler.calculate_transition_stats(optimized)
    print(f"  Original total distance: {stats['total_transition_distance']:.1f}m")
    print(f"  Optimized total distance: {optimized_stats['total_transition_distance']:.1f}m")
    print(f"  Improvement: {stats['total_transition_distance'] - optimized_stats['total_transition_distance']:.1f}m")
