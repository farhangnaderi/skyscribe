#!/usr/bin/env python3
"""
Multi-format mission file exporters.

Supports exporting waypoints to various formats:
- KML/KMZ: Google Earth, DJI apps, GIS tools
- CSV: Simple waypoint lists
- Waypoint: Legacy MAVLink format
- GeoJSON: GIS integration
"""

import csv
import json
from datetime import datetime
from xml.etree import ElementTree as ET
from xml.dom import minidom


class FormatExporter:
    """Base class for format exporters"""

    def __init__(self, waypoints, home_position, metadata=None):
        """
        Initialize exporter.

        Args:
            waypoints: List of (lat, lon, alt) tuples
            home_position: Tuple of (home_lat, home_lon, home_alt)
            metadata: Dict with optional metadata (text, font, etc.)
        """
        self.waypoints = waypoints
        self.home_lat, self.home_lon, self.home_alt = home_position
        self.metadata = metadata or {}

    def export(self, filename):
        """Export to file. Override in subclasses."""
        raise NotImplementedError


class KMLExporter(FormatExporter):
    """Export waypoints to KML format (Google Earth compatible)"""

    def export(self, filename):
        """
        Export to KML file.

        Args:
            filename: Output filename (.kml extension)

        Returns:
            Path to created file
        """
        # Create KML structure
        kml = ET.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
        document = ET.SubElement(kml, 'Document')

        # Add metadata
        name = ET.SubElement(document, 'name')
        name.text = self.metadata.get('text', 'Drone Mission')

        description = ET.SubElement(document, 'description')
        desc_text = f"Text-to-Drone Mission\n"
        desc_text += f"Text: {self.metadata.get('text', 'N/A')}\n"
        desc_text += f"Waypoints: {len(self.waypoints)}\n"
        desc_text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        description.text = desc_text

        # Define styles
        # Home marker style
        home_style = ET.SubElement(document, 'Style', id='homeStyle')
        icon_style = ET.SubElement(home_style, 'IconStyle')
        icon = ET.SubElement(icon_style, 'Icon')
        href = ET.SubElement(icon, 'href')
        href.text = 'http://maps.google.com/mapfiles/kml/paddle/grn-circle.png'

        # Waypoint marker style
        wp_style = ET.SubElement(document, 'Style', id='waypointStyle')
        icon_style = ET.SubElement(wp_style, 'IconStyle')
        icon = ET.SubElement(icon_style, 'Icon')
        href = ET.SubElement(icon, 'href')
        href.text = 'http://maps.google.com/mapfiles/kml/paddle/blu-circle.png'

        # Path line style
        line_style = ET.SubElement(document, 'Style', id='pathStyle')
        line_style_elem = ET.SubElement(line_style, 'LineStyle')
        color = ET.SubElement(line_style_elem, 'color')
        color.text = 'ff0000ff'  # Red in ABGR
        width = ET.SubElement(line_style_elem, 'width')
        width.text = '3'

        # Add home position
        home_placemark = ET.SubElement(document, 'Placemark')
        home_name = ET.SubElement(home_placemark, 'name')
        home_name.text = 'Home Position'
        home_styleurl = ET.SubElement(home_placemark, 'styleUrl')
        home_styleurl.text = '#homeStyle'
        home_point = ET.SubElement(home_placemark, 'Point')
        home_coords = ET.SubElement(home_point, 'coordinates')
        home_coords.text = f"{self.home_lon},{self.home_lat},{self.home_alt}"

        # Add waypoints as placemarks
        for i, (lat, lon, alt) in enumerate(self.waypoints, 1):
            placemark = ET.SubElement(document, 'Placemark')
            pm_name = ET.SubElement(placemark, 'name')
            pm_name.text = f'WP{i}'
            pm_desc = ET.SubElement(placemark, 'description')
            pm_desc.text = f'Waypoint {i}\nAlt: {alt:.1f}m'
            pm_styleurl = ET.SubElement(placemark, 'styleUrl')
            pm_styleurl.text = '#waypointStyle'
            point = ET.SubElement(placemark, 'Point')
            coords = ET.SubElement(point, 'coordinates')
            coords.text = f"{lon},{lat},{alt}"

        # Add path as LineString
        path_placemark = ET.SubElement(document, 'Placemark')
        path_name = ET.SubElement(path_placemark, 'name')
        path_name.text = 'Flight Path'
        path_styleurl = ET.SubElement(path_placemark, 'styleUrl')
        path_styleurl.text = '#pathStyle'
        linestring = ET.SubElement(path_placemark, 'LineString')
        altitude_mode = ET.SubElement(linestring, 'altitudeMode')
        altitude_mode.text = 'absolute'
        coords = ET.SubElement(linestring, 'coordinates')
        coords_text = '\n'.join([f"{lon},{lat},{alt}" for lat, lon, alt in self.waypoints])
        coords.text = coords_text

        # Pretty print and save
        xml_str = minidom.parseString(ET.tostring(kml)).toprettyxml(indent='  ')
        with open(filename, 'w') as f:
            f.write(xml_str)

        return filename


class CSVExporter(FormatExporter):
    """Export waypoints to CSV format"""

    def export(self, filename):
        """
        Export to CSV file.

        Args:
            filename: Output filename (.csv extension)

        Returns:
            Path to created file
        """
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(['Waypoint', 'Latitude', 'Longitude', 'Altitude_MSL', 'Description'])

            # Home position
            writer.writerow([
                'HOME',
                f"{self.home_lat:.7f}",
                f"{self.home_lon:.7f}",
                f"{self.home_alt:.2f}",
                'Home/Takeoff position'
            ])

            # Waypoints
            for i, (lat, lon, alt) in enumerate(self.waypoints, 1):
                writer.writerow([
                    f'WP{i}',
                    f"{lat:.7f}",
                    f"{lon:.7f}",
                    f"{alt:.2f}",
                    f'Waypoint {i}'
                ])

        return filename


class WaypointExporter(FormatExporter):
    """Export waypoints to MAVLink Waypoint format"""

    def __init__(self, waypoints, home_position, metadata=None, acceptance_radius=1.5):
        """
        Initialize WaypointExporter.

        Args:
            waypoints: List of (lat, lon, alt) tuples
            home_position: Tuple of (home_lat, home_lon, home_alt)
            metadata: Dict with optional metadata (text, font, etc.)
            acceptance_radius: Waypoint acceptance radius in meters (default 1.5)
        """
        super().__init__(waypoints, home_position, metadata)
        self.acceptance_radius = acceptance_radius

    def export(self, filename):
        """
        Export to .waypoint file (tab-delimited MAVLink format).

        Args:
            filename: Output filename (.waypoint extension)

        Returns:
            Path to created file
        """
        with open(filename, 'w') as f:
            # Header: QGC WPL <VERSION>
            f.write('QGC WPL 110\n')

            # Format: INDEX CURRENT FRAME COMMAND PARAM1 PARAM2 PARAM3 PARAM4 PARAM5(X/LAT) PARAM6(Y/LON) PARAM7(Z/ALT) AUTOCONTINUE

            # Home position (item 0)
            f.write(f'0\t1\t0\t16\t0\t0\t0\t0\t{self.home_lat:.7f}\t{self.home_lon:.7f}\t{self.home_alt:.2f}\t1\n')

            # Waypoints
            for i, (lat, lon, alt) in enumerate(self.waypoints, 1):
                # MAV_CMD_NAV_WAYPOINT = 16
                # FRAME: 3 = MAV_FRAME_GLOBAL_RELATIVE_ALT
                current = 0  # Not current waypoint
                frame = 3    # Global relative altitude
                command = 16 # NAV_WAYPOINT
                param1 = 0   # Hold time
                param2 = self.acceptance_radius  # Acceptance radius
                param3 = 0   # Pass through
                param4 = 0   # Yaw
                autocontinue = 1

                f.write(f'{i}\t{current}\t{frame}\t{command}\t{param1}\t{param2}\t{param3}\t{param4}\t{lat:.7f}\t{lon:.7f}\t{alt:.2f}\t{autocontinue}\n')

        return filename


class GeoJSONExporter(FormatExporter):
    """Export waypoints to GeoJSON format"""

    def export(self, filename):
        """
        Export to GeoJSON file.

        Args:
            filename: Output filename (.geojson extension)

        Returns:
            Path to created file
        """
        # Create GeoJSON structure
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        # Add home position
        home_feature = {
            "type": "Feature",
            "properties": {
                "name": "Home Position",
                "type": "home",
                "altitude": self.home_alt
            },
            "geometry": {
                "type": "Point",
                "coordinates": [self.home_lon, self.home_lat, self.home_alt]
            }
        }
        geojson["features"].append(home_feature)

        # Add waypoints
        for i, (lat, lon, alt) in enumerate(self.waypoints, 1):
            feature = {
                "type": "Feature",
                "properties": {
                    "name": f"WP{i}",
                    "type": "waypoint",
                    "index": i,
                    "altitude": alt
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat, alt]
                }
            }
            geojson["features"].append(feature)

        # Add path as LineString
        path_coords = [[lon, lat, alt] for lat, lon, alt in self.waypoints]
        path_feature = {
            "type": "Feature",
            "properties": {
                "name": "Flight Path",
                "type": "path",
                "waypoint_count": len(self.waypoints)
            },
            "geometry": {
                "type": "LineString",
                "coordinates": path_coords
            }
        }
        geojson["features"].append(path_feature)

        # Save to file
        with open(filename, 'w') as f:
            json.dump(geojson, f, indent=2)

        return filename


def export_mission(waypoints, home_position, output_file, format='plan', metadata=None, acceptance_radius=1.5):
    """
    Export mission to specified format.

    Args:
        waypoints: List of (lat, lon, alt) tuples
        home_position: Tuple of (home_lat, home_lon, home_alt)
        output_file: Base output filename (extension will be added)
        format: Output format ('plan', 'kml', 'csv', 'waypoint', 'geojson')
        metadata: Optional dict with metadata
        acceptance_radius: Waypoint acceptance radius in meters (default 1.5, used for waypoint format)

    Returns:
        Path to created file
    """
    # Remove extension from output_file if present
    import os
    base_name = os.path.splitext(output_file)[0]

    if format == 'kml':
        exporter = KMLExporter(waypoints, home_position, metadata)
        return exporter.export(f"{base_name}.kml")

    elif format == 'csv':
        exporter = CSVExporter(waypoints, home_position, metadata)
        return exporter.export(f"{base_name}.csv")

    elif format == 'waypoint':
        exporter = WaypointExporter(waypoints, home_position, metadata, acceptance_radius)
        return exporter.export(f"{base_name}.waypoint")

    elif format == 'geojson':
        exporter = GeoJSONExporter(waypoints, home_position, metadata)
        return exporter.export(f"{base_name}.geojson")

    elif format == 'plan':
        # Use existing mission_generator
        from mission_generator import MissionGenerator
        generator = MissionGenerator()
        return generator.generate_plan(
            waypoints,
            home_position,
            output_file=f"{base_name}.plan",
            include_takeoff=True,
            include_rtl=True
        )

    else:
        raise ValueError(f"Unsupported format: {format}. Use 'plan', 'kml', 'csv', 'waypoint', or 'geojson'")


# Test code
if __name__ == '__main__':
    # Test waypoints (Zurich area)
    test_waypoints = [
        (47.3977432, 8.5455942, 518),
        (47.3978000, 8.5456000, 518),
        (47.3978500, 8.5457000, 518),
        (47.3979000, 8.5458000, 520),
    ]
    home = (47.3977432, 8.5455942, 488)
    metadata = {'text': 'TEST', 'font': 'futural'}

    print("Testing format exporters...")
    print("\n1. KML export:")
    kml_file = export_mission(test_waypoints, home, 'test', format='kml', metadata=metadata)
    print(f"   Created: {kml_file}")

    print("\n2. CSV export:")
    csv_file = export_mission(test_waypoints, home, 'test', format='csv', metadata=metadata)
    print(f"   Created: {csv_file}")

    print("\n3. Waypoint export:")
    wp_file = export_mission(test_waypoints, home, 'test', format='waypoint', metadata=metadata)
    print(f"   Created: {wp_file}")

    print("\n4. GeoJSON export:")
    geojson_file = export_mission(test_waypoints, home, 'test', format='geojson', metadata=metadata)
    print(f"   Created: {geojson_file}")

    print("\nAll formats exported successfully!")
