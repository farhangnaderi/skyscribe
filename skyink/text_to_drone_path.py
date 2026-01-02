#!/usr/bin/env python3
"""
Text-to-Drone-Path Converter for PX4 Autopilot

Converts text strings into QGroundControl .plan mission files using:
- Hershey stroke fonts for single-line glyphs
- Douglas-Peucker path simplification
- ENU-to-GPS coordinate transformation
- Altitude-separated letter transitions

Usage:
    python text_to_drone_path.py "HELLO" --lat 47.397 --lon 8.545 --alt 488
"""

import argparse
import sys
from skyink.font_extractor import FontExtractor
from skyink.path_simplifier import PathSimplifier
from skyink.coord_transformer import CoordinateTransformer
from skyink.path_transitions import PathTransitionHandler
from skyink.mission_generator import MissionGenerator
from skyink.format_exporters import export_mission


def main():
    parser = argparse.ArgumentParser(
        description='Convert text to PX4 drone flight path (.plan file)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Basic usage:
    python text_to_drone_path.py "HELLO" --lat 47.397 --lon 8.545

  Custom letter size and altitude:
    python text_to_drone_path.py "DRONE" --lat 47.397 --lon 8.545 --letter-height 30 --flight-alt 50

  Different font and no simplification:
    python text_to_drone_path.py "TEXT" --lat 47.397 --lon 8.545 --font futuram --no-simplify

  Rotated text (45 degrees from north):
    python text_to_drone_path.py "NORTH" --lat 47.397 --lon 8.545 --rotation 45
        """
    )

    # Required arguments
    parser.add_argument('text', type=str, help='Text to convert to drone path')
    parser.add_argument('--lat', type=float, required=True,
                       help='Home latitude in degrees')
    parser.add_argument('--lon', type=float, required=True,
                       help='Home longitude in degrees')

    # Optional position arguments
    parser.add_argument('--alt', type=float, default=0.0,
                       help='Home altitude in meters MSL (default: 0)')
    parser.add_argument('--rotation', type=float, default=0.0,
                       help='Text rotation in degrees (0=north, default: 0)')

    # Text rendering options
    parser.add_argument('--font', type=str, default='futural',
                       choices=['futural', 'futuram', 'scriptc', 'gothiceng',
                               'cursive', 'timesg', 'timesib', 'timesr'],
                       help='Hershey font name (default: futural)')
    parser.add_argument('--letter-height', type=float, default=20.0,
                       help='Letter height in meters (default: 20)')

    # Flight parameters
    parser.add_argument('--flight-alt', type=float, default=30.0,
                       help='Flight altitude in meters above home (default: 30)')
    parser.add_argument('--transit-offset', type=float, default=10.0,
                       help='Additional altitude during transitions in meters (default: 10)')
    parser.add_argument('--speed', type=float, default=3.0,
                       help='Flight speed in m/s (default: 3.0)')
    parser.add_argument('--acceptance-radius', type=float, default=1.5,
                       help='Waypoint acceptance radius in meters (default: 1.5)')
    parser.add_argument('--home-offset-x', type=float, default=None,
                       help='Home offset West of text in meters (default: 50%% of letter height)')
    parser.add_argument('--home-offset-y', type=float, default=None,
                       help='Home offset South of text in meters (default: 50%% of letter height)')

    # Path processing options
    parser.add_argument('--no-simplify', action='store_true',
                       help='Disable path simplification')
    parser.add_argument('--epsilon', type=float, default=None,
                       help='Path simplification tolerance in meters (auto if not specified)')
    parser.add_argument('--no-optimize', action='store_true',
                       help='Disable stroke order optimization')
    parser.add_argument('--direct-transitions', action='store_true',
                       help='Use direct transitions without altitude separation')
    parser.add_argument('--continuous-threshold', type=float, default=None,
                       help='Connect strokes closer than this (meters) without altitude change (cursive). Default: 30%% of letter height')

    # Output options
    parser.add_argument('-o', '--output', type=str, default=None,
                       help='Output filename (default: <text>.<format>)')
    parser.add_argument('--format', type=str, default='plan',
                       choices=['plan', 'kml', 'csv', 'waypoint', 'geojson'],
                       help='Output format (default: plan)')
    parser.add_argument('--no-takeoff', action='store_true',
                       help='Exclude takeoff command from mission (plan format only)')
    parser.add_argument('--no-rtl', action='store_true',
                       help='Exclude RTL command from mission (plan format only)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Print detailed information')

    args = parser.parse_args()

    # Set default output filename
    if args.output is None:
        safe_text = "".join(c if c.isalnum() else "_" for c in args.text)
        args.output = f"{safe_text}"  # Extension will be added by exporter

    if args.verbose:
        print(f"Text-to-Drone-Path Converter")
        print(f"=" * 50)
        print(f"Text: {args.text}")
        print(f"Font: {args.font}")
        print(f"Letter height: {args.letter_height}m")
        print(f"Home position: ({args.lat:.6f}°, {args.lon:.6f}°, {args.alt:.1f}m)")
        print(f"Flight altitude: {args.flight_alt}m")
        print(f"Rotation: {args.rotation}°")
        print()

    # Step 1: Extract font strokes
    if args.verbose:
        print("[1/6] Extracting Hershey font strokes...")

    extractor = FontExtractor(font_name=args.font, letter_height_m=args.letter_height)
    paths = extractor.extract_continuous_paths(args.text)

    if args.verbose:
        total_points = sum(len(p) for p in paths)
        print(f"  Extracted {len(paths)} strokes with {total_points} points")

    if not paths:
        print(f"Error: No paths extracted for text '{args.text}'", file=sys.stderr)
        return 1

    # Step 2: Simplify paths (optional)
    if not args.no_simplify:
        if args.verbose:
            print("[2/6] Simplifying paths with Douglas-Peucker...")

        simplifier = PathSimplifier(epsilon=args.epsilon, letter_height_m=args.letter_height)
        simplified_paths = simplifier.simplify_paths(paths)

        if args.verbose:
            original_count = sum(len(p) for p in paths)
            simplified_count = sum(len(p) for p in simplified_paths)
            reduction = 100 * (1 - simplified_count / original_count)
            print(f"  {original_count} -> {simplified_count} points ({reduction:.1f}% reduction)")
            print(f"  Epsilon: {simplifier.epsilon:.3f}m")

        paths = simplified_paths
    else:
        if args.verbose:
            print("[2/6] Skipping path simplification")

    # Step 3: Optimize stroke order (optional)
    if not args.no_optimize:
        if args.verbose:
            print("[3/6] Optimizing stroke order...")

        handler = PathTransitionHandler(
            write_altitude_m=args.flight_alt,
            transit_altitude_offset_m=args.transit_offset
        )
        stats_before = handler.calculate_transition_stats(paths)
        paths = handler.optimize_stroke_order(paths, method='nearest_neighbor')
        stats_after = handler.calculate_transition_stats(paths)

        if args.verbose:
            improvement = stats_before['total_transition_distance'] - stats_after['total_transition_distance']
            print(f"  Transition distance: {stats_before['total_transition_distance']:.1f}m -> {stats_after['total_transition_distance']:.1f}m")
            print(f"  Improvement: {improvement:.1f}m")
    else:
        if args.verbose:
            print("[3/6] Skipping stroke order optimization")

    # Step 4: Add altitude transitions
    if args.verbose:
        print("[4/6] Adding altitude transitions...")

    handler = PathTransitionHandler(
        write_altitude_m=args.flight_alt,
        transit_altitude_offset_m=args.transit_offset
    )

    # Determine continuous threshold
    # Direct transitions = connect all strokes (infinite threshold)
    # Default = 30% of letter height (cursive within letters)
    if args.direct_transitions:
        continuous_threshold = float('inf')  # Connect everything
    elif args.continuous_threshold is None:
        continuous_threshold = args.letter_height * 0.3  # Default cursive
    else:
        continuous_threshold = args.continuous_threshold  # User specified

    waypoints_3d = handler.add_transitions(paths, continuous_threshold=continuous_threshold)

    if args.verbose:
        print(f"  Flight altitude: {args.flight_alt}m (constant)")
        print(f"  Total 3D waypoints: {len(waypoints_3d)}")

        # Calculate and display mission time estimate
        time_stats = handler.calculate_mission_time(waypoints_3d, flight_speed_m_s=args.speed)
        print(f"  Estimated mission time: {time_stats['total_time_formatted']} ({time_stats['total_distance_m']:.1f}m total distance)")

    # Step 5: Convert to GPS coordinates
    if args.verbose:
        print("[5/6] Converting to GPS coordinates...")

    # Calculate bounds to offset text so home is at bottom-left (southwest)
    all_xy = [(x, y) for x, y, z in waypoints_3d]
    min_x = min(p[0] for p in all_xy)
    min_y = min(p[1] for p in all_xy)
    max_x = max(p[0] for p in all_xy)
    max_y = max(p[1] for p in all_xy)

    # Default margin: 50% of letter height (scales with text size)
    default_margin = args.letter_height * 0.5
    margin_x = args.home_offset_x if args.home_offset_x is not None else default_margin
    margin_y = args.home_offset_y if args.home_offset_y is not None else default_margin

    # Offset so bottom-left of text is margin distance from home
    offset_x = -min_x + margin_x
    offset_y = -min_y + margin_y

    if args.verbose:
        print(f"  Text bounds: x=[{min_x:.1f}, {max_x:.1f}]m, y=[{min_y:.1f}, {max_y:.1f}]m")
        print(f"  Applying offset: x+={offset_x:.1f}m, y+={offset_y:.1f}m")
        print(f"  Home will be {margin_x:.1f}m West and {margin_y:.1f}m South of text start")

    transformer = CoordinateTransformer(
        home_lat=args.lat,
        home_lon=args.lon,
        home_alt=args.alt,
        rotation_deg=args.rotation
    )

    gps_waypoints = []
    for x, y, z in waypoints_3d:
        # Apply offset before GPS conversion
        lat, lon, alt = transformer.local_to_gps(x + offset_x, y + offset_y, z)
        gps_waypoints.append((lat, lon, z))  # Use relative altitude

    if args.verbose:
        print(f"  Converted {len(gps_waypoints)} waypoints to GPS")

    # Step 6: Generate mission file
    if args.verbose:
        print("[6/6] Generating QGroundControl .plan file...")

    generator = MissionGenerator(
        acceptance_radius_m=args.acceptance_radius,
        flight_speed_m_s=args.speed
    )

    # Validate mission
    is_valid, issues = generator.validate_mission(gps_waypoints, max_waypoints=500)
    if not is_valid:
        print(f"Warning: Mission validation issues:", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)

    # Generate mission file in requested format
    if args.verbose:
        print(f"[6/6] Generating {args.format.upper()} file...")
        print()

    home_position = (args.lat, args.lon, args.alt)
    metadata = {
        'text': args.text,
        'font': args.font,
        'letter_height': args.letter_height,
        'rotation': args.rotation
    }

    if args.format == 'plan':
        # Use original mission generator
        output_path = generator.generate_plan(
            gps_waypoints,
            home_position,
            output_file=args.output,
            include_takeoff=not args.no_takeoff,
            include_rtl=not args.no_rtl
        )
    else:
        # Use format exporters
        output_path = export_mission(
            gps_waypoints,
            home_position,
            args.output,
            format=args.format,
            metadata=metadata
        )

    if args.verbose:
        print(f"Mission Statistics:")
        print(f"  Total waypoints: {len(gps_waypoints)}")
        print(f"  Output format: {args.format.upper()}")
        print(f"  Acceptance radius: {args.acceptance_radius}m")
        print(f"  Flight speed: {args.speed}m/s")
        print(f"  Estimated flight time: {len(gps_waypoints) * 2:.0f}s (rough estimate)")
        print()

    print(f"Successfully generated: {output_path}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
