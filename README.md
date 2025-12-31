# SkyInk - Aerial Skywriting with Drones

Convert text to autonomous flight missions for PX4, ArduPilot, and other MAVLink-compatible autopilots. Uses Hershey stroke fonts, Douglas-Peucker path simplification, and GPS coordinate transformation.

## Features

- **Hershey Stroke Fonts**: Single-line glyphs that eliminate the need for complex centerline extraction
- **Douglas-Peucker Simplification**: Reduces waypoint count while preserving letter corners and readability
- **GPS Coordinate Transformation**: Accurate ENU-to-WGS84 conversion using pymap3d
- **Altitude-Separated Transitions**: Clean path transitions between letters with configurable altitude offset
- **Stroke Order Optimization**: Minimizes total transition distance using nearest-neighbor heuristic
- **QGroundControl .plan Generation**: Direct mission file output compatible with PX4 autopilot
- **Smart Home Positioning**: Automatic margins with bottom-left home position
- **Continuous/Cursive Mode**: Connects nearby strokes without altitude transitions
- **Multiple Font Styles**: 8 fonts including bold (futuram) and decorative styles

## Quick Start

### Option 1: Run GUI Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start web GUI
python gui_server.py

# 3. Open browser to http://localhost:5000
# 4. Preview on map, adjust parameters, generate .plan file
```

### Option 2: Command Line

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate your first mission
python text_to_drone_path.py "HELLO" --lat 47.397 --lon 8.545

# 4. Upload HELLO.plan to QGroundControl
```

⚠️ **Always test in PX4 SITL simulation before hardware flight**

## Project Structure

```
skyink/
├── gui_server.py             # 🌐 Web GUI server (Flask)
├── templates/
│   └── index.html            # GUI frontend (HTML/JS/CSS)
├── text_to_drone_path.py     # 💻 Main CLI application
├── visualize_path.py         # ASCII art path preview tool
├── font_extractor.py         # Hershey font stroke extraction
├── path_simplifier.py        # Douglas-Peucker simplification
├── coord_transformer.py      # ENU-to-GPS conversion
├── path_transitions.py       # Altitude transitions & optimization
├── mission_generator.py      # QGroundControl .plan file generator
├── format_exporters.py       # 📤 Multi-format exporters (KML/CSV/etc)
├── requirements.txt          # Python dependencies
├── examples.sh               # Example usage commands
├── README.md                 # This file
├── QUICKSTART_GUI.md         # GUI quick start guide
├── GUI_GUIDE.md              # Full GUI documentation
└── *.{plan,kml,csv}          # Generated mission files
```

## Installation

### Requirements
- Python 3.8+
- Virtual environment (recommended)

### Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Example

```bash
python text_to_drone_path.py "DRONE" --lat 47.397 --lon 8.545 --alt 488
```

This generates a `DRONE.plan` file ready to upload to QGroundControl.

### Advanced Examples

**Custom letter size and flight altitude:**
```bash
python text_to_drone_path.py "HELLO" --lat 47.397 --lon 8.545 \
    --letter-height 30 --flight-alt 50
```

**Rotated text (45° from north):**
```bash
python text_to_drone_path.py "NORTH" --lat 47.397 --lon 8.545 \
    --rotation 45 --output north_45deg.plan
```

**Bold text (thicker strokes):**
```bash
python text_to_drone_path.py "BOLD" --lat 47.397 --lon 8.545 \
    --font futuram
```

**Continuous/cursive mode (connects nearby strokes):**
```bash
python text_to_drone_path.py "SMOOTH" --lat 47.397 --lon 8.545 \
    --continuous-threshold 10
```

**Different font style:**
```bash
python text_to_drone_path.py "SCRIPT" --lat 47.397 --lon 8.545 \
    --font scriptc
```

**Disable optimizations for raw output:**
```bash
python text_to_drone_path.py "RAW" --lat 47.397 --lon 8.545 \
    --no-simplify --no-optimize
```

**Export to KML for Google Earth/DJI:**
```bash
python text_to_drone_path.py "HELLO" --lat 47.397 --lon 8.545 \
    --format kml
```

**Export to CSV spreadsheet:**
```bash
python text_to_drone_path.py "DATA" --lat 47.397 --lon 8.545 \
    --format csv
```

**Verbose output with statistics:**
```bash
python text_to_drone_path.py "TEST" --lat 47.397 --lon 8.545 -v
```

## Command-Line Options

### Required Arguments
- `text`: Text string to convert to drone path
- `--lat`: Home latitude in degrees
- `--lon`: Home longitude in degrees

### Position & Orientation
- `--alt`: Home altitude in meters MSL (default: 0)
- `--rotation`: Text rotation in degrees, 0=north (default: 0)

### Text Rendering
- `--font`: Hershey font name (default: futural)
  - `futural` - Roman simplex (single stroke, most readable)
  - `futuram` - Roman duplex (double stroke, **bold/thick**)
  - `scriptc` - Script/cursive style
  - `gothiceng` - Gothic English decorative
  - `timesib` - Times Italic Bold
  - `timesr`, `timesg`, `cursive` - Other styles
- `--letter-height`: Letter height in meters (default: 20)
- `--home-offset-x`: Custom X margin from home to text (default: 50% of letter height)
- `--home-offset-y`: Custom Y margin from home to text (default: 50% of letter height)

### Flight Parameters
- `--flight-alt`: Flight altitude above home in meters (default: 30)
- `--transit-offset`: Additional altitude during transitions (default: 10)
- `--speed`: Flight speed in m/s (default: 3.0)
- `--acceptance-radius`: Waypoint acceptance radius in meters (default: 1.5)

### Path Processing
- `--no-simplify`: Disable Douglas-Peucker path simplification
- `--epsilon`: Custom simplification tolerance in meters (auto-calculated if not specified)
- `--no-optimize`: Disable stroke order optimization
- `--direct-transitions`: Use direct lateral transitions without altitude change
- `--continuous-threshold`: Distance in meters for continuous stroke connections (default: 30% of letter height, 0=disabled)

### Output Options
- `-o, --output`: Output filename (default: `<text>.<format>`)
- `--format`: Output format (default: plan)
  - `plan` - QGroundControl .plan file (PX4/MAVLink)
  - `kml` - Google Earth KML (DJI/GIS compatible)
  - `csv` - CSV spreadsheet
  - `waypoint` - Legacy MAVLink waypoint format
  - `geojson` - GeoJSON for GIS tools
- `--no-takeoff`: Exclude takeoff command from mission (plan format only)
- `--no-rtl`: Exclude RTL command from mission (plan format only)
- `-v, --verbose`: Print detailed processing information

## Export Formats

The tool supports multiple export formats for maximum compatibility:

### `.plan` - QGroundControl (Default)
- **Use for:** PX4/MAVLink autopilots
- **Compatible with:** QGroundControl, MAVProxy, Mission Planner
- **Contains:** Full mission with takeoff, waypoints, RTL, speed commands
- **Format:** JSON-based QGC plan file

### `.kml` - Google Earth/KML
- **Use for:** Visualization, DJI apps, GIS tools
- **Compatible with:** Google Earth, DJI Fly, DJI Pilot 2, QGIS
- **Contains:** Waypoints as placemarks, flight path as LineString
- **Format:** XML-based Keyhole Markup Language

### `.csv` - CSV Spreadsheet
- **Use for:** Data analysis, Excel, custom processing
- **Compatible with:** Excel, Google Sheets, Python pandas
- **Contains:** Waypoint list with lat/lon/alt
- **Format:** Comma-separated values

### `.waypoint` - MAVLink Waypoint
- **Use for:** Legacy MAVLink tools
- **Compatible with:** Older QGC versions, custom MAVLink tools
- **Contains:** Tab-delimited MAVLink MISSION_ITEM format
- **Format:** QGC WPL 110 format

### `.geojson` - GeoJSON
- **Use for:** GIS integration, web mapping
- **Compatible with:** QGIS, ArcGIS, Leaflet.js, Mapbox
- **Contains:** FeatureCollection with waypoints and path
- **Format:** JSON-based geographic data

### Format Comparison

| Format | PX4/MAVLink | Visualization | GIS | DJI | Size |
|--------|-------------|---------------|-----|-----|------|
| `.plan` | ✅ Best | ⚠️ QGC only | ❌ | ❌ | Medium |
| `.kml` | ❌ | ✅ Best | ✅ Good | ✅ Good | Large |
| `.csv` | ⚠️ Basic | ❌ | ✅ Good | ❌ | Small |
| `.waypoint` | ✅ Legacy | ❌ | ❌ | ❌ | Small |
| `.geojson` | ❌ | ✅ Good | ✅ Best | ❌ | Medium |

## Technical Details

### Optimal Parameter Recommendations

| Letter Height | Epsilon | Waypoints/Letter | Acceptance Radius |
|--------------|---------|------------------|-------------------|
| 10m | 0.2m | 8-15 | 1.0-1.5m |
| 20m | 0.4m | 10-20 | 1.5-2.0m |
| 50m | 0.75m | 15-25 | 2.0-3.0m |
| 100m+ | 1.5m | 20-30 | 3.0-5.0m |

### Coordinate Transformation

The tool uses **pymap3d** for accurate ENU (East-North-Up) to WGS84 geodetic conversion:

1. Text coordinates are generated in local XY meters
2. Optional rotation is applied
3. ENU coordinates are converted to GPS using the home position as origin
4. All calculations use the WGS84 ellipsoid model

For patterns under 1km, flat-Earth approximation error is sub-centimeter (negligible compared to GPS accuracy).

### Path Simplification

**Douglas-Peucker algorithm** is used because it:
- Preserves sharp corners essential for letter recognition
- Reduces waypoint count by 10-30% typically
- Uses perpendicular distance tolerance (epsilon)
- Automatically scales epsilon to 2% of letter height by default

### Altitude Transitions

Between disconnected strokes (letters), the drone:
1. Rises to transit altitude (write altitude + offset)
2. Travels laterally to next stroke start
3. Descends to write altitude
4. Continues tracing

This creates clean separation in GPS logs when viewed from above.

### PX4 Mission Limits

- **Maximum waypoints**: ~500-600 per mission (SD card storage limit)
- **Waypoint command**: MAV_CMD_NAV_WAYPOINT (16) with fly-through enabled
- **Frame**: GLOBAL_RELATIVE_ALT (3) for altitude relative to home
- **Speed**: Set via MAV_CMD_DO_CHANGE_SPEED (178)

## Module Architecture

The tool is organized into focused modules:

- `font_extractor.py`: Hershey font stroke extraction
- `path_simplifier.py`: Douglas-Peucker algorithm implementation
- `coord_transformer.py`: ENU-to-GPS coordinate conversion
- `path_transitions.py`: Altitude transitions and stroke order optimization
- `mission_generator.py`: QGroundControl .plan file generation
- `text_to_drone_path.py`: Main CLI interface
- `visualize_path.py`: ASCII art path visualization utility

Each module is independently testable with `__main__` test blocks.

### Dependency Graph

```
Main Program:
┌──────────────────────────┐
│ text_to_drone_path.py    │  (Main Entry Point)
│ - Orchestrates pipeline  │
│ - CLI argument parsing   │
└─────────┬────────────────┘
          │
          ├─────────────────────────────────────┐
          │                                     │
          ▼                                     ▼
┌──────────────────────┐           ┌──────────────────────┐
│  font_extractor.py   │           │  path_simplifier.py  │
│  - Hershey fonts     │           │  - Douglas-Peucker   │
│  - Stroke extraction │           │  - Waypoint reduction│
└──────────────────────┘           └──────────────────────┘
          │                                     │
          └─────────────┬───────────────────────┘
                        ▼
          ┌──────────────────────────┐
          │ coord_transformer.py     │
          │ - ENU to WGS84          │
          │ - GPS conversion         │
          └────────┬─────────────────┘
                   ▼
          ┌──────────────────────────┐
          │ path_transitions.py      │
          │ - Altitude transitions   │
          │ - Stroke optimization    │
          └────────┬─────────────────┘
                   ▼
          ┌──────────────────────────┐
          │ mission_generator.py     │
          │ - QGC .plan generation   │
          │ - MAVLink encoding       │
          └──────────────────────────┘

Utility Program:
┌──────────────────────┐
│ visualize_path.py    │  (Standalone Tool)
│ - ASCII art preview  │
└─────────┬────────────┘
          │
          ├───────────────┐
          ▼               ▼
    font_extractor   path_simplifier
```

### External Dependencies

```python
# Core dependencies (4 total)
HersheyFonts>=0.2.0    # Single-stroke font library
pymap3d>=3.0.0         # Geodetic coordinate transformations
simplification>=0.7.0   # Rust-backed Douglas-Peucker algorithm
numpy>=1.24.0          # Numerical operations
```

## Testing in Simulation

### PX4 SITL (Software-in-the-Loop)

PX4 SITL uses default coordinates in **Zurich, Switzerland**:
- Latitude: `47.3977432`
- Longitude: `8.5455942`
- Altitude: `488m` MSL

```bash
# Start PX4 SITL with Gazebo
make px4_sitl gazebo

# Generate mission for SITL default location
python text_to_drone_path.py "TEST" \
  --lat 47.3977432 --lon 8.5455942 --alt 488

# Upload mission via QGroundControl or MAVProxy
# Test mission execution in simulation before hardware flight
```

### QGroundControl

1. Open QGroundControl
2. Connect to vehicle (real or SITL)
3. Go to Plan View
4. File → Open → Select generated `.plan` file
5. Upload to Vehicle
6. Switch to Fly View and start mission

## Safety Considerations

⚠️ **Always test in simulation (SITL) before hardware flights**

- Verify waypoint count < 500
- Check altitude constraints against local regulations
- Ensure geofence boundaries are appropriate
- Validate GPS coordinate accuracy
- Test with small text first (fewer waypoints)
- Monitor battery capacity for mission duration
- Have emergency RTL procedures ready

## Example Output

**Input:**
```bash
python text_to_drone_path.py "DRONE" --lat 47.397 --lon 8.545 --alt 488 -v
```

**Output:**
```
Text-to-Drone-Path Converter
==================================================
Text: DRONE
Font: futural
Letter height: 20.0m
Home position: (47.397000°, 8.545000°, 488.0m)
Flight altitude: 30.0m

[1/6] Extracting Hershey font strokes...
  Extracted 13 strokes with 63 points
[2/6] Simplifying paths with Douglas-Peucker...
  63 -> 55 points (12.7% reduction)
  Epsilon: 0.400m
[3/6] Optimizing stroke order...
  Transition distance: 168.1m -> 102.6m
  Improvement: 65.6m
[4/6] Adding altitude transitions...
  Write altitude: 30.0m
  Transit altitude: 40.0m
  Total 3D waypoints: 79
[5/6] Converting to GPS coordinates...
  Converted 79 waypoints to GPS
[6/6] Generating QGroundControl .plan file...

Mission Statistics:
  Total waypoints: 79
  Acceptance radius: 1.5m
  Flight speed: 3.0m/s

Successfully generated: DRONE.plan
```

## Common Use Cases

### Maximum Clarity (competitions/photography)
```bash
python text_to_drone_path.py "CLEAR" \
  --lat 47.397 --lon 8.545 --alt 488 \
  --letter-height 30 --flight-alt 50 \
  --speed 2.5 --acceptance-radius 1.0 --epsilon 0.2
```

### Maximum Efficiency (short flight, minimal waypoints)
```bash
python text_to_drone_path.py "GO" \
  --lat 47.397 --lon 8.545 \
  --letter-height 20 --speed 5.0 --epsilon 1.0 \
  --direct-transitions
```

### Bold + Continuous (smooth, thick letters)
```bash
python text_to_drone_path.py "HAPPY NEW YEAR" \
  --lat 47.3977432 --lon 8.5455942 --alt 488 \
  --font futuram --continuous-threshold 10 \
  --letter-height 15 --flight-alt 30 -v
```

## Troubleshooting

### "Too many waypoints" error
- Use shorter text
- Increase `--epsilon` for more aggressive simplification
- Reduce `--letter-height` to make letters smaller

### GPS coordinates seem wrong
- Verify home latitude/longitude are correct
- Check that altitude is MSL (mean sea level), not AGL
- Ensure rotation angle is in degrees (0-360)

### Letters appear distorted
- Check rotation parameter
- Verify coordinate transformation with small test pattern
- Ensure home coordinates use correct datum (WGS84)

### Mission won't upload to drone
- Verify .plan file is valid JSON
- Check waypoint count is under vehicle limit
- Ensure QGroundControl version is compatible with PX4

### Drone doesn't follow path accurately
- GPS accuracy insufficient (RTK recommended for <1m precision)
- Wind drift (reduce speed, increase altitude)
- Acceptance radius too large (reduce to 1.0-1.5m)
- Waypoints too far apart (reduce epsilon)

## References

- **Hershey Fonts**: [PyPI Package](https://pypi.org/project/Hershey-Fonts/)
- **pymap3d**: [Geodetic Transformations](https://pypi.org/project/pymap3d/)
- **Douglas-Peucker**: [simplification library](https://pypi.org/project/simplification/)
- **QGroundControl**: [Official Site](http://qgroundcontrol.com/)
- **PX4 Autopilot**: [Documentation](https://docs.px4.io/)

## License

MIT License - see [LICENSE](LICENSE) file for details.

**Safety Disclaimer:** This software generates autonomous drone flight paths. Users are solely responsible for safe operation, testing in simulation, compliance with regulations, and all risks associated with drone operations. No warranties or guarantees are provided.

## Contributing

Contributions welcome! Areas for enhancement:
- Additional font support (TrueType with centerline extraction)
- 3D path visualization before flight
- MAVSDK Python integration for direct mission upload
- Geofence boundary checking
- Battery capacity estimation
- Multi-drone swarm formation support
