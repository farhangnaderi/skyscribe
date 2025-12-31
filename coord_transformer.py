"""
Coordinate transformation from local ENU (East-North-Up) to GPS (WGS84).
Handles rotation and geodetic conversion using pymap3d.
"""

import pymap3d as pm
import numpy as np


class CoordinateTransformer:
    """Transform local XY coordinates to GPS coordinates."""

    def __init__(self, home_lat, home_lon, home_alt=0.0, rotation_deg=0.0):
        """
        Initialize coordinate transformer.

        Args:
            home_lat: Home latitude in degrees (reference point)
            home_lon: Home longitude in degrees (reference point)
            home_alt: Home altitude in meters above sea level (default 0)
            rotation_deg: Rotation angle in degrees (0 = text reads north)
        """
        self.home_lat = home_lat
        self.home_lon = home_lon
        self.home_alt = home_alt
        self.rotation_deg = rotation_deg

        # Pre-calculate rotation matrix
        rad = np.radians(rotation_deg)
        self.cos_r = np.cos(rad)
        self.sin_r = np.sin(rad)

    def local_to_gps(self, x, y, altitude):
        """
        Convert local XY coordinates to GPS coordinates.

        Args:
            x: East coordinate in meters
            y: North coordinate in meters
            altitude: Altitude in meters (relative to home altitude)

        Returns:
            Tuple of (latitude, longitude, altitude_msl)
        """
        # Apply rotation if specified
        if self.rotation_deg != 0:
            rotated_x = x * self.cos_r - y * self.sin_r
            rotated_y = x * self.sin_r + y * self.cos_r
        else:
            rotated_x = x
            rotated_y = y

        # Convert ENU to geodetic (WGS84)
        lat, lon, alt_msl = pm.enu2geodetic(
            e=rotated_x,
            n=rotated_y,
            u=altitude,
            lat0=self.home_lat,
            lon0=self.home_lon,
            h0=self.home_alt
        )

        # Return altitude relative to home for mission planning
        # (since MAV_FRAME_GLOBAL_RELATIVE_ALT expects relative altitude)
        alt_relative = altitude

        return lat, lon, alt_relative

    def path_to_gps(self, path, altitude):
        """
        Convert a path of XY points to GPS coordinates.

        Args:
            path: List of (x, y) tuples in meters
            altitude: Flight altitude in meters (relative to home)

        Returns:
            List of (lat, lon, alt) tuples
        """
        gps_path = []
        for x, y in path:
            lat, lon, alt = self.local_to_gps(x, y, altitude)
            gps_path.append((lat, lon, alt))

        return gps_path

    def get_bounds(self, paths):
        """
        Calculate bounding box of all paths in local coordinates.

        Args:
            paths: List of paths with (x, y) points

        Returns:
            Tuple of (min_x, max_x, min_y, max_y)
        """
        all_points = []
        for path in paths:
            all_points.extend(path)

        if not all_points:
            return (0, 0, 0, 0)

        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]

        return (min(xs), max(xs), min(ys), max(ys))



if __name__ == '__main__':
    import sys

    # Simple command-line test tool
    if len(sys.argv) < 3:
        print("Usage: python coord_transformer.py <lat> <lon> [alt] [rotation]")
        print("Example: python coord_transformer.py 47.397 8.545 488 0")
        print("\nConverts a 10m square test pattern to GPS coordinates")
        sys.exit(1)

    home_lat = float(sys.argv[1])
    home_lon = float(sys.argv[2])
    home_alt = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    rotation_deg = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0

    transformer = CoordinateTransformer(home_lat, home_lon, home_alt, rotation_deg)

    # Test 10m square pattern
    test_path = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
    gps_path = transformer.path_to_gps(test_path, altitude=30)

    print(f"Home: ({home_lat:.6f}°, {home_lon:.6f}°, {home_alt:.1f}m)")
    print(f"Rotation: {rotation_deg}°\n")
    print("10m square test pattern at 30m altitude:")
    for i, (lat, lon, alt) in enumerate(gps_path):
        print(f"  WP{i}: {lat:.8f}, {lon:.8f}, {alt:.1f}m")
