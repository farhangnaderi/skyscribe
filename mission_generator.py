"""
QGroundControl mission file generator for PX4 autopilot.
Creates .plan files with waypoint missions for text-to-drone-path conversion.
"""

import json
from datetime import datetime


class MissionGenerator:
    """Generate QGroundControl .plan mission files."""

    def __init__(self, acceptance_radius_m=1.5, flight_speed_m_s=3.0):
        """
        Initialize mission generator.

        Args:
            acceptance_radius_m: Waypoint acceptance radius in meters (1.5-2.0 recommended)
            flight_speed_m_s: Flight speed in m/s (2-5 recommended for text tracing)
        """
        self.acceptance_radius = acceptance_radius_m
        self.flight_speed = flight_speed_m_s

    def _create_mission_item(self, command, frame, item_id, params):
        """Helper to create mission item with common structure."""
        return {
            "type": "SimpleItem",
            "command": command,
            "frame": frame,
            "autoContinue": True,
            "doJumpId": item_id,
            "params": params
        }

    def create_waypoint_item(self, lat, lon, alt, item_id,
                            hold_time=0, yaw=None, is_fly_through=True):
        """Create waypoint mission item."""
        return self._create_mission_item(
            16,  # MAV_CMD_NAV_WAYPOINT
            3,   # MAV_FRAME_GLOBAL_RELATIVE_ALT
            item_id,
            [hold_time, self.acceptance_radius,
             self.acceptance_radius if is_fly_through else 0,
             yaw, lat, lon, alt]
        )

    def create_takeoff_item(self, lat, lon, alt, item_id=1, min_pitch=0, yaw=None):
        """Create takeoff mission item."""
        return self._create_mission_item(
            22,  # MAV_CMD_NAV_TAKEOFF
            3,   # MAV_FRAME_GLOBAL_RELATIVE_ALT
            item_id,
            [min_pitch, 0, 0, yaw, lat, lon, alt]
        )

    def create_rtl_item(self, item_id):
        """Create Return-to-Launch mission item."""
        return self._create_mission_item(
            20,  # MAV_CMD_NAV_RETURN_TO_LAUNCH
            2,   # MAV_FRAME_MISSION
            item_id,
            [0, 0, 0, 0, 0, 0, 0]
        )

    def create_speed_item(self, speed_m_s, item_id):
        """Create speed change command item."""
        return self._create_mission_item(
            178,  # MAV_CMD_DO_CHANGE_SPEED
            2,    # MAV_FRAME_MISSION
            item_id,
            [1, speed_m_s, -1, 0, 0, 0, 0]  # 1 = airspeed type
        )

    def generate_plan(self, gps_waypoints, home_position,
                     output_file='mission.plan', include_takeoff=True,
                     include_rtl=True):
        """
        Generate complete QGroundControl .plan file.

        Args:
            gps_waypoints: List of (lat, lon, alt) tuples
            home_position: Tuple of (lat, lon, alt) for home/launch position
            output_file: Output filename
            include_takeoff: Whether to include takeoff command
            include_rtl: Whether to include RTL command

        Returns:
            Path to generated .plan file
        """
        mission_items = []
        item_id = 1

        # Add takeoff if requested
        if include_takeoff:
            mission_items.append(
                self.create_takeoff_item(
                    home_position[0],
                    home_position[1],
                    gps_waypoints[0][2] if gps_waypoints else 30,
                    item_id=item_id
                )
            )
            item_id += 1

        # Add speed command
        mission_items.append(
            self.create_speed_item(self.flight_speed, item_id)
        )
        item_id += 1

        # Add all waypoints
        for lat, lon, alt in gps_waypoints:
            mission_items.append(
                self.create_waypoint_item(lat, lon, alt, item_id)
            )
            item_id += 1

        # Add RTL if requested
        if include_rtl:
            mission_items.append(
                self.create_rtl_item(item_id)
            )

        # Create complete plan structure
        plan = {
            "fileType": "Plan",
            "geoFence": {
                "circles": [],
                "polygons": [],
                "version": 2
            },
            "groundStation": "QGroundControl",
            "mission": {
                "cruiseSpeed": self.flight_speed,
                "firmwareType": 12,  # PX4 Pro
                "globalPlanAltitudeMode": 1,  # Relative altitude
                "hoverSpeed": self.flight_speed,
                "items": mission_items,
                "plannedHomePosition": [
                    home_position[0],
                    home_position[1],
                    home_position[2]
                ],
                "vehicleType": 2,  # Multi-rotor
                "version": 2
            },
            "rallyPoints": {
                "points": [],
                "version": 2
            },
            "version": 1
        }

        # Write to file
        with open(output_file, 'w') as f:
            json.dump(plan, f, indent=2)

        return output_file

    def validate_mission(self, gps_waypoints, max_waypoints=500):
        """
        Validate mission parameters.

        Args:
            gps_waypoints: List of waypoints to validate
            max_waypoints: Maximum allowed waypoints

        Returns:
            Tuple of (is_valid, issues_list)
        """
        issues = []

        # Check waypoint count
        if len(gps_waypoints) > max_waypoints:
            issues.append(f"Too many waypoints: {len(gps_waypoints)} > {max_waypoints}")

        if len(gps_waypoints) == 0:
            issues.append("No waypoints provided")

        # Check altitude consistency
        if gps_waypoints:
            altitudes = [wp[2] for wp in gps_waypoints]
            if max(altitudes) - min(altitudes) > 1000:
                issues.append(f"Large altitude variation: {max(altitudes) - min(altitudes):.1f}m")

        return (len(issues) == 0, issues)


if __name__ == '__main__':
    # Test mission generation
    generator = MissionGenerator(acceptance_radius_m=1.5, flight_speed_m_s=3.0)

    # Create test waypoints (simple square pattern)
    home = (47.397, 8.545, 488.0)

    test_waypoints = [
        (47.397, 8.545, 30.0),
        (47.397100, 8.545, 30.0),
        (47.397100, 8.545100, 30.0),
        (47.397, 8.545100, 30.0),
        (47.397, 8.545, 30.0),
    ]

    # Validate
    is_valid, issues = generator.validate_mission(test_waypoints)
    print(f"Mission valid: {is_valid}")
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  - {issue}")

    # Generate plan file
    output = generator.generate_plan(
        test_waypoints,
        home,
        output_file='test_mission.plan'
    )

    print(f"\nGenerated mission file: {output}")
    print(f"Waypoints: {len(test_waypoints)}")
    print(f"Acceptance radius: {generator.acceptance_radius}m")
    print(f"Flight speed: {generator.flight_speed}m/s")
