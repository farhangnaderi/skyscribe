#!/usr/bin/env python3
"""
Web-based GUI for Text-to-Drone-Path Converter

Real-time visualization of waypoints on an interactive map before generating .plan files.
Uses Flask for the web server and Folium for interactive maps.

Usage:
    python gui_server.py
    Then open http://localhost:5000 in your browser
"""

from flask import Flask, render_template, request, jsonify, send_file
import folium
from folium import plugins
import json
import os
from datetime import datetime

# Import our existing modules
from skyink.font_extractor import FontExtractor
from skyink.path_simplifier import PathSimplifier
from skyink.coord_transformer import CoordinateTransformer
from skyink.path_transitions import PathTransitionHandler
from skyink.mission_generator import MissionGenerator

# Get the directory where this file is located
_template_dir = os.path.join(os.path.dirname(__file__), 'templates')
app = Flask(__name__, template_folder=_template_dir)

# Store the latest mission data
latest_mission = {
    'waypoints': [],
    'plan_file': None,
    'stats': {}
}


def generate_preview(text, lat, lon, alt=0, **kwargs):
    """Generate waypoints and return data for visualization"""

    # Extract parameters
    font = kwargs.get('font', 'futural')
    letter_height = kwargs.get('letter_height', 20.0)
    flight_alt = kwargs.get('flight_alt', 30.0)
    rotation = kwargs.get('rotation', 0.0)
    simplify = kwargs.get('simplify', True)
    epsilon = kwargs.get('epsilon', None)
    optimize = kwargs.get('optimize', True)
    continuous_threshold = kwargs.get('continuous_threshold', None)

    # Step 1: Extract font strokes
    extractor = FontExtractor(font, letter_height)
    strokes = extractor.extract_continuous_paths(text)

    total_points = sum(len(stroke) for stroke in strokes)

    # Step 2: Simplify paths
    if simplify:
        if epsilon is None:
            epsilon = letter_height * 0.02
        simplifier = PathSimplifier(epsilon, letter_height)
        strokes = simplifier.simplify_paths(strokes)

    simplified_points = sum(len(stroke) for stroke in strokes)

    # Get transit offset from kwargs
    transit_offset = kwargs.get('transit_offset', 10.0)

    # Step 3: Optimize stroke order (optional)
    if optimize:
        handler_temp = PathTransitionHandler(
            write_altitude_m=flight_alt,
            transit_altitude_offset_m=transit_offset
        )
        strokes = handler_temp.optimize_stroke_order(strokes, method='nearest_neighbor')

    # Step 4: Add altitude transitions
    handler = PathTransitionHandler(
        write_altitude_m=flight_alt,
        transit_altitude_offset_m=transit_offset
    )

    if continuous_threshold is None:
        continuous_threshold = letter_height * 0.3

    waypoints_3d = handler.add_transitions(
        strokes,
        continuous_threshold=continuous_threshold
    )

    # Calculate mission time estimate
    flight_speed = kwargs.get('flight_speed', 3.0)  # Default 3 m/s
    time_stats = handler.calculate_mission_time(waypoints_3d, flight_speed_m_s=flight_speed)

    # Step 5: Convert to GPS coordinates
    transformer = CoordinateTransformer(lat, lon, alt, rotation)
    gps_waypoints = []
    for x, y, z in waypoints_3d:
        lat_wp, lon_wp, alt_wp = transformer.local_to_gps(x, y, z)
        gps_waypoints.append({
            'lat': lat_wp,
            'lon': lon_wp,
            'alt': alt_wp,
            'is_transit': z > flight_alt  # Mark transit waypoints
        })

    # Calculate statistics
    stats = {
        'text': text,
        'num_strokes': len(strokes),
        'original_points': total_points,
        'simplified_points': simplified_points,
        'total_waypoints': len(gps_waypoints),
        'reduction_percent': round((1 - simplified_points/total_points) * 100, 1) if total_points > 0 else 0,
        'letter_height': letter_height,
        'flight_alt': flight_alt,
        'font': font,
        'mission_time': time_stats['total_time_formatted'],
        'mission_time_s': round(time_stats['total_time_s'], 1),
        'total_distance': round(time_stats['total_distance_m'], 1)
    }

    return gps_waypoints, stats


@app.route('/')
def index():
    """Serve the main GUI page"""
    return render_template('index.html')


@app.route('/preview', methods=['POST'])
def preview():
    """Generate preview waypoints"""
    try:
        data = request.json

        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data received'
            }), 400

        # Required parameters
        text = data.get('text', 'HELLO')
        if not text or text.strip() == '':
            return jsonify({
                'success': False,
                'error': 'Text cannot be empty'
            }), 400

        lat = float(data.get('lat', 47.3977432))
        lon = float(data.get('lon', 8.5455942))
        alt = float(data.get('alt', 488))

        # Optional parameters
        kwargs = {
            'font': data.get('font', 'futural'),
            'letter_height': float(data.get('letter_height', 20)),
            'flight_alt': float(data.get('flight_alt', 30)),
            'rotation': float(data.get('rotation', 0)),
            'simplify': data.get('simplify', True),
            'epsilon': float(data.get('epsilon')) if data.get('epsilon') else None,
            'optimize': data.get('optimize', True),
            'continuous_threshold': float(data.get('continuous_threshold')) if data.get('continuous_threshold') else None,
            'flight_speed': float(data.get('flight_speed', 3.0)),
            'acceptance_radius': float(data.get('acceptance_radius', 1.5)),
            'transit_offset': float(data.get('transit_offset', 10.0))
        }

        waypoints, stats = generate_preview(text, lat, lon, alt, **kwargs)

        # Store for download
        global latest_mission
        latest_mission['waypoints'] = waypoints
        latest_mission['stats'] = stats
        latest_mission['params'] = {
            'text': text,
            'lat': lat,
            'lon': lon,
            'alt': alt,
            **kwargs
        }

        return jsonify({
            'success': True,
            'waypoints': waypoints,
            'stats': stats,
            'home': {'lat': lat, 'lon': lon, 'alt': alt}
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print("ERROR in /preview:")
        print(error_details)
        return jsonify({
            'success': False,
            'error': str(e),
            'details': error_details
        }), 400


@app.route('/generate', methods=['POST'])
def generate_plan():
    """Generate the mission file in requested format"""
    try:
        global latest_mission

        if not latest_mission['waypoints']:
            return jsonify({
                'success': False,
                'error': 'No waypoints to generate. Create a preview first.'
            }), 400

        # Get format from request
        data = request.json or {}
        export_format = data.get('format', 'plan')

        params = latest_mission['params']
        waypoints = latest_mission['waypoints']

        # Convert waypoints to the format exporters expect
        waypoints_list = [(wp['lat'], wp['lon'], wp['alt']) for wp in waypoints]

        # Generate base filename
        base_filename = f"{params['text'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Prepare metadata
        home_position = (params['lat'], params['lon'], params['alt'])
        metadata = {
            'text': params['text'],
            'font': params.get('font', 'futural'),
            'letter_height': params.get('letter_height', 20),
            'rotation': params.get('rotation', 0)
        }

        # Generate file in requested format
        if export_format == 'plan':
            # Use original mission generator
            flight_speed = params.get('flight_speed', 3.0)
            acceptance_radius = params.get('acceptance_radius', 1.5)
            generator = MissionGenerator(acceptance_radius_m=acceptance_radius, flight_speed_m_s=flight_speed)
            filepath = generator.generate_plan(
                waypoints_list,
                home_position,
                output_file=f"{base_filename}.plan",
                include_takeoff=True,
                include_rtl=True
            )
            filename = os.path.basename(filepath)
        else:
            # Use format exporters
            from skyink.format_exporters import export_mission
            acceptance_radius = params.get('acceptance_radius', 1.5)
            filepath = export_mission(
                waypoints_list,
                home_position,
                base_filename,
                format=export_format,
                metadata=metadata,
                acceptance_radius=acceptance_radius
            )
            filename = os.path.basename(filepath)

        latest_mission['plan_file'] = filepath

        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'waypoint_count': len(waypoints_list),
            'format': export_format
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/download/<filename>')
def download(filename):
    """Download the generated .plan file"""
    filepath = os.path.join(os.getcwd(), filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        return "File not found", 404


def main():
    """Main entry point for GUI server."""
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'

    print("=" * 50)
    print("Text-to-Drone-Path GUI Server")
    print("=" * 50)
    print("\nStarting server...")
    print(f"Port: {port}")
    print(f"Debug mode: {debug}")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)

    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    main()
