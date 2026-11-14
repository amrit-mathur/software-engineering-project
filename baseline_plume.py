import math
import numpy as np
import pandas as pd
import pydeck as pdk

# 1. Target City Coordinates (Greater Noida / City Center)
center_lat, center_lon = 28.4744, 77.5040

# 2. Live / Baseline Conditions (0% Restrictions - Normal Business As Usual)
wind_speed = 15.0  # km/h
wind_direction_deg = 315.0  # NW Wind
wind_rad = math.radians((wind_direction_deg + 180) % 360)

# 💡 Zero policy cuts means full emissions
factory_curtailment_pct = 0.0
traffic_reduction_pct = 0.0

base_emission = (150 * (1.0 - factory_curtailment_pct / 100.0)) + (
    100 * (1.0 - traffic_reduction_pct / 100.0
))  # Results in a higher base emission of 250

# 3. Generate Spatial Grid
grid_points = []
lats = np.linspace(center_lat - 0.06, center_lat + 0.06, 25)
lons = np.linspace(center_lon - 0.06, center_lon + 0.06, 25)

for lat in lats:
  for lon in lons:
    dx = (lon - center_lon) * 111
    dy = (lat - center_lat) * 111

    downwind = dx * math.sin(wind_rad) + dy * math.cos(wind_rad)
    crosswind = -dx * math.cos(wind_rad) + dy * math.sin(wind_rad)

    if downwind > 0:
      sigma = 0.5 + 0.1 * downwind * (15 / max(wind_speed, 1))
      aqi_val = base_emission * math.exp(
          -(crosswind**2) / (2 * sigma**2)
      ) / (1 + 0.15 * downwind)
    else:
      aqi_val = 30.0

    aqi_val = max(10, min(500, float(aqi_val)))

    # Granular color mapping (higher peak values will trigger intense reds/purples)
    if aqi_val > 200:
      color = [150, 20, 80, 220]  # Hazardous / Dark Magenta
    elif aqi_val > 150:
      color = [220, 30, 60, 210]  # Severe Red
    elif aqi_val > 100:
      color = [230, 80, 20, 200]  # Orange-Red
    elif aqi_val > 60:
      color = [245, 158, 11, 180]  # Amber
    else:
      color = [16, 185, 129, 90]  # Soft Green

    grid_points.append({
        "lat": float(lat),
        "lon": float(lon),
        "aqi": round(aqi_val, 1),
        "elevation": round(aqi_val * 22, 1),
        "color": color,
    })

df = pd.DataFrame(grid_points)

# 4. Build PyDeck 3D Layer
layer = pdk.Layer(
    "ColumnLayer",
    data=df,
    get_position=["lon", "lat"],
    get_elevation="elevation",
    radius=250,
    get_fill_color="color",
    elevation_scale=1,
    pickable=True,
    auto_highlight=True,
)

# Same side-profile view for easy comparison
view_state = pdk.ViewState(
    latitude=center_lat,
    longitude=center_lon,
    zoom=12.5,
    pitch=68,
    bearing=35,
)

r = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={
        "text": (
            "LIVE BASELINE (No Restrictions)\nCoordinates: {lat}, {lon}\nAQI:"
            " {aqi}"
        )
    },
)

# 💡 Export to a separate file so you have both!
r.to_html("baseline_simulation.html")
print("✅ Generated 'baseline_simulation.html' (Live Unmitigated AQI)!")