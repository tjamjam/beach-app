# 🏖️ Burlington Beach Status Monitor

A real-time water quality monitoring system for Burlington, Vermont beaches on Lake Champlain. Tracks beach safety status by parsing official Vermont ANR reports and provides weather conditions with sophisticated wave estimation specifically for Lake Champlain.

## 🌟 Features

### 🚦 Beach Water Quality Monitoring
- **PDF Parsing**: Automatically extracts data from Vermont ANR Public Swimming Reports
- **10 Beach Coverage**: Monitors all Burlington area beaches including Leddy, North Beach, Texaco, Blanchard, etc.
- **Real-time Status**: Green (Open), Yellow (Caution), Red (Closed) status indicators
- **Historical Tracking**: CSV logging of all status changes with timestamps

### 🌤️ Weather & Wave Conditions
- **OpenWeatherMap Integration**: Current conditions and 3-hour forecast for Burlington area
- **Advanced Wave Estimation**: Lake Champlain-specific algorithm considering:
  - 16-direction wind analysis (not basic 4-direction)
  - Actual fetch distances across Appletree Bay (0-8 miles depending on wind direction)
  - Geographic accuracy for Lakewood Beach location
- **Air Quality**: Real-time AQI data from AirNow API

### 📊 Two Web Applications

#### Main App (`index.html`)
- **Single Beach Focus**: Shows Lakewood Beach status (using Leddy Beach South data)
- **Traffic Light Display**: Visual stoplight with animated status
- **Detailed Weather**: Current conditions, 3-hour forecast, wave predictions
- **Smart Suggestions**: Activity recommendations based on weather/wave conditions
- **Email Subscriptions**: Users can subscribe to status change notifications

#### Overview App (`overview.html`)
- **All Beaches Table**: Complete status overview with sortable data
- **Interactive Map**: Leaflet map with color-coded pins for each beach
- **Historical Timeline**: D3.js heatmap showing status changes over time
- **Summer Statistics**: Beach availability percentages for August 2025

### 📧 Notification System
- **Email Alerts**: SMTP-based notifications when target beach status changes
- **Push Notifications**: ntfy.sh integration for instant mobile alerts
- **Subscriber Management**: Cloudflare KV storage for email lists

## 🏗️ Architecture

### Frontend
- **Pure HTML/CSS/JS**: No build process required
- **Responsive Design**: Mobile-first approach
- **External Libraries**: 
  - Leaflet for mapping
  - D3.js for data visualization
  - FontAwesome for icons

### Backend
- **Cloudflare Worker** (`backend/index.js`): API endpoints for weather, air quality, and subscriptions
- **Python Monitor** (`backend/check_status.py`): PDF parsing and status checking
- **Data Storage**: JSON status files and CSV historical logs

### Data Sources
- **Beach Status**: Vermont ANR Public Swimming Reports (PDF parsing)
- **Weather**: OpenWeatherMap API (05408 Burlington area)
- **Air Quality**: AirNow API (05401 Burlington)

## 🚀 Deployment

### Live Application
- **API**: Deployed on Cloudflare Workers at `beach-api.terrencefradet.workers.dev`
- **Frontend**: Static hosting (GitHub Pages, Cloudflare Pages, etc.)

### Cloudflare Setup
```bash
# Deploy the worker
npx wrangler deploy

# Set environment secrets
npx wrangler secret put OPENWEATHER_API_KEY
npx wrangler secret put AIRNOW_API_KEY
npx wrangler secret put CF_API_TOKEN
```

## 🛠️ Development

### Prerequisites
- **Node.js**: For Cloudflare Workers development
- **Python 3.8+**: For beach status monitoring
- **API Keys**: 
  - OpenWeatherMap (free tier sufficient)
  - AirNow API (free government API)
  - Cloudflare account

### Python Dependencies
```bash
pip install requests pdfplumber python-dotenv
```

### Environment Variables
```bash
# For Python monitoring script (.env file)
CF_API_TOKEN=your_cloudflare_worker_api_token
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_specific_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
TEST_MODE=false
DAILY_LOGGING=true

# For Cloudflare Worker (via wrangler secrets)
OPENWEATHER_API_KEY=your_openweather_api_key
AIRNOW_API_KEY=your_airnow_api_key
```

### Local Development
```bash
# Start Cloudflare Worker locally
npx wrangler dev

# Run beach status checker
cd backend
python check_status.py

# Test individual components
python test_github_token.py
python test_notification.py

# Backfill historical data for testing
python daily_snapshot_helper.py backfill 30
```

## 📁 Project Structure

```
beach-app/
├── frontend/
│   ├── index.html          # Main Lakewood Beach app
│   ├── overview.html       # All beaches overview with map/timeline
│   └── images/
│       └── background.jpg  # Lake Champlain background image
├── backend/
│   ├── index.js            # Cloudflare Worker (weather/AQI/subscriptions)
│   ├── check_status.py     # PDF parser and status monitor
│   ├── daily_snapshot_helper.py # Historical data management
│   ├── get_token.py        # Cloudflare token utility
│   ├── test_*.py          # Testing utilities
│   ├── historical_status.csv # Real historical data
│   ├── fake_historical_status.csv # Test data for development
│   └── status.json        # Current beach status (backend copy)
├── status.json            # Current beach status (main file)
├── current_status.txt     # Simple status file
└── wrangler.toml         # Cloudflare Worker configuration
```

## 🎯 Wave Estimation Algorithm

The wave estimation system is specifically calibrated for Lake Champlain's Appletree Bay:

### Fetch Distance Calculation
- **West winds**: 8-mile fetch across Appletree Bay → larger waves
- **East winds**: 0-mile fetch (blocked by land) → calm conditions  
- **16 directions**: More accurate than basic N/S/E/W systems

### Conservative Estimates
- **Light winds (< 8 mph)**: 0-1 ft waves regardless of fetch
- **Moderate winds (8-18 mph)**: 1-2 ft with good fetch, 0-1 ft with limited fetch
- **Strong winds (18+ mph)**: 2-4 ft maximum with full fetch across bay

### Real-time Explanations
Examples of wave prediction output:
- "Moderate winds with good fetch across Appletree Bay (8 miles)"
- "Strong winds but limited fetch - land blocks (0 miles)"

## 📊 Data Management

### Beach Status Format
```json
[
  {
    "beach_name": "Leddy Beach South",
    "status": "green",
    "date": "Aug 27 2025 11:13AM", 
    "note": "Open",
    "coordinates": {"lat": 44.501457, "lon": -73.252218}
  }
]
```

### Historical Data
- **CSV Format**: Timestamped records of all status changes
- **Daily Snapshots**: Automatic logging for timeline visualization
- **Backfill Capability**: Can generate historical data for testing

## 🔧 Configuration

### Target Beach
- **Display Name**: "Lakewood Beach" (user-facing)
- **Data Source**: "Leddy Beach South" (closest official monitoring point)
- **Distance**: 729.57 feet from Lakewood Beach

### Monitoring Schedule
- **PDF Checks**: Hourly via cron job
- **Notifications**: Sent only when status changes
- **Historical Logging**: Daily snapshots + change events

## 🧪 Testing

```bash
cd backend

# Test PDF parsing
python check_status.py  # Includes built-in test

# Test API authentication
python test_github_token.py

# Test notification system
python test_notification.py

# Run in test mode (notifications only to test email)
TEST_MODE=true python check_status.py
```

## 📱 API Endpoints

- `GET /weather` - Current weather and 3-hour forecast
- `GET /air-quality` - Air quality index with AirNow data  
- `POST /subscribe` - Add email to notification list
- `GET /get-subscribers` - List subscribers (requires API token)

## 🤝 Contributing

### Known Limitations
- PDF parsing depends on consistent Vermont ANR report format
- Wave estimates are conservative and Lake Champlain-specific
- Historical data starts from deployment date

### Enhancement Ideas
- Mobile app version
- Webcam integration
- Water temperature data
- Social reporting features

## 🏆 Data Sources & Acknowledgments

- **Vermont Agency of Natural Resources**: Official beach water quality reports
- **OpenWeatherMap**: Weather data and forecasting
- **AirNow**: Government air quality monitoring
- **Cloudflare**: Edge computing and KV storage
- **D3.js**: Data visualization library
- **Leaflet**: Interactive mapping

---

*Built for the Burlington, VT community to make informed decisions about Lake Champlain beach safety.*