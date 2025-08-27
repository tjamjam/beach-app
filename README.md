# 🏖️ Burlington Beach Status App

A comprehensive real-time beach water quality monitoring system for Burlington, Vermont beaches on Lake Champlain. This app provides current beach status, detailed weather conditions with sophisticated wave estimation, and historical data visualization.

## 🌟 Features

### 🚦 Real-Time Beach Status
- **Traffic Light System**: Intuitive green/yellow/red status indicators
- **Water Quality Monitoring**: Tracks E. coli levels and advisories
- **Multiple Beach Coverage**: Monitors 10+ Burlington area beaches
- **Official Data**: Pulls from Vermont Agency of Natural Resources reports

### 🌊 Advanced Wave Estimation
- **Sophisticated Algorithm**: Considers wind speed, direction, and fetch distance
- **Geographic Accuracy**: Specific calculations for Appletree Bay geography  
- **16-Direction Wind Analysis**: More precise than basic 4-direction systems
- **Real-Time Explanations**: Shows actual fetch distances (e.g., "Strong winds with good fetch across bay (8 miles)")

### 🌤️ Comprehensive Weather
- **Current Conditions**: Temperature, humidity, wind speed/direction
- **3-Hour Forecast**: Upcoming weather with wave predictions
- **Air Quality Index**: Real-time AQI with color-coded status
- **Smart Suggestions**: Activity recommendations based on conditions

### 📊 Data Visualization
- **Interactive Map**: Clickable beach locations with status pins
- **Status Table**: Sortable overview of all beaches
- **Historical Timeline**: D3.js heatmap showing status changes over time
- **Trend Analysis**: Beach availability percentages

### 📧 Notifications
- **Email Subscriptions**: Get notified when beach status changes
- **Push Notifications**: Via ntfy.sh for instant updates
- **Status Changes**: Automatic alerts for water quality updates

## 🏗️ Architecture

### Frontend
- **Main App** (`index.html`): Single beach focus with detailed weather
- **Overview App** (`overview.html`): All beaches with map and timeline
- **Tailwind CSS**: Modern responsive design
- **D3.js**: Interactive data visualizations
- **Leaflet**: Interactive mapping

### Backend
- **Cloudflare Workers** (`backend/index.js`): API endpoints
- **Python Monitor** (`backend/check_status.py`): Status checking and notifications
- **Data Storage**: JSON files and CSV historical logs

### Data Sources
- **Beach Status**: Vermont ANR Public Swimming Reports (PDF parsing)
- **Weather**: OpenWeatherMap API (current + forecast)
- **Air Quality**: AirNow API
- **Coordinates**: Precise GPS locations for all beaches

## 🚀 Deployment

### Live URLs
- **Main App**: `https://your-domain.com/index.html`
- **Overview**: `https://your-domain.com/overview.html`
- **API**: `https://beach-api.terrencefradet.workers.dev`

### Cloudflare Setup
```bash
# Deploy the API worker
npx wrangler deploy

# Set environment variables
npx wrangler secret put OPENWEATHER_API_KEY
npx wrangler secret put AIRNOW_API_KEY
```

### Frontend Deployment
- Host static files on any CDN/static hosting
- Files are ready-to-deploy (no build step required)
- Or deploy via Cloudflare Pages for seamless integration

## 🛠️ Development

### Prerequisites
- **Node.js**: For Cloudflare Workers
- **Python 3.8+**: For monitoring scripts
- **API Keys**: OpenWeatherMap, AirNow

### Environment Variables
```bash
# Backend monitoring (.env or environment)
CF_API_TOKEN=your_cloudflare_api_token
EMAIL_SENDER=your_email@domain.com
EMAIL_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
TEST_MODE=false

# Cloudflare Worker (via wrangler)
OPENWEATHER_API_KEY=your_openweather_key
AIRNOW_API_KEY=your_airnow_key
```

### Local Development
```bash
# Install dependencies
npm install

# Start local worker
npx wrangler dev

# Run status checker
cd backend
python check_status.py

# Build CSS (if modifying styles)
npx tailwindcss -i ./src/input.css -o ./dist/output.css --watch
```

## 📁 Project Structure

```
beach-app/
├── frontend/
│   ├── index.html          # Main single-beach app
│   ├── overview.html       # Multi-beach overview with map
│   ├── images/             # Background and assets
│   └── src/
│       └── input.css       # Tailwind source styles
├── backend/
│   ├── index.js            # Cloudflare Worker API
│   ├── check_status.py     # Beach status monitor
│   ├── historical_status.csv # Historical data
│   └── README.md           # Backend documentation
├── status.json             # Current beach status data
├── wrangler.toml           # Cloudflare configuration
└── tailwind.config.js      # Tailwind CSS config
```

## 🔧 Configuration

### Beach Monitoring
- **Target Beach**: Configurable in `check_status.py`
- **Check Frequency**: Set via cron/scheduler
- **Notification Topics**: Customizable ntfy topics

### Wave Estimation
- **Fetch Distances**: Accurate measurements for each wind direction
- **Wind Thresholds**: Conservative estimates based on real observations
- **Geographic Model**: Specific to Appletree Bay/Lake Champlain

### API Endpoints
- `GET /weather` - Current weather and forecast
- `GET /aqi` - Air quality index
- `GET /beaches` - All beach statuses (if implemented)

## 📊 Data Management

### Historical Data
- **CSV Storage**: `backend/historical_status.csv`
- **Automatic Logging**: Status changes tracked with timestamps
- **Visualization**: D3.js heatmap in overview app

### Status File Format
```json
{
  "beaches": [
    {
      "beach_name": "Leddy Beach South",
      "status": "green",
      "last_updated": "Aug 2 2025 11:17AM",
      "note": "Open",
      "coordinates": {"lat": 44.501457, "lon": -73.252218}
    }
  ],
  "last_checked": "2025-01-10T19:04:44Z"
}
```

## 🎯 Wave Estimation Details

### Algorithm Features
- **Geographic Precision**: 16 wind directions vs basic 4
- **Fetch Distance Calculation**: Real measurements across Appletree Bay
- **Conservative Estimates**: Validated against real observations
- **Dynamic Explanations**: Educational content with actual distances

### Example Predictions
- **West 15 mph**: "Moderate winds with good fetch across Appletree Bay (8 miles)" → 1-2 ft
- **East 15 mph**: "Moderate winds but limited fetch - land blocks (0 miles)" → 0-1 ft
- **Southwest 8 mph**: "Light winds with good fetch across bay (6 miles)" → 0-1 ft

## 🚨 Monitoring & Alerts

### Notification System
- **Email**: SMTP-based notifications for subscribers
- **Push**: ntfy.sh integration for instant alerts
- **Status Changes**: Automatic detection and notification

### Health Monitoring
- **API Status**: Cloudflare Worker health
- **Data Freshness**: PDF parsing success/failure
- **Error Handling**: Graceful degradation when APIs fail

## 📱 Responsive Design

- **Mobile-First**: Optimized for phone usage
- **Progressive Enhancement**: Works on all device sizes
- **Touch-Friendly**: Large interactive elements
- **Fast Loading**: Minimal dependencies, optimized assets

## 🔐 Security & Privacy

- **No User Data Storage**: Minimal data collection
- **CORS Headers**: Secure API access
- **Environment Variables**: Sensitive data protected
- **Rate Limiting**: Built-in Cloudflare protection

## 📈 Performance

- **Global CDN**: Cloudflare Workers edge computing
- **Caching**: Appropriate cache headers
- **Minimal JS**: Lightweight vanilla JavaScript
- **Progressive Loading**: Graceful loading states

## 🤝 Contributing

### Areas for Enhancement
- [ ] Mobile app version
- [ ] More sophisticated wave modeling
- [ ] Historical trend analysis
- [ ] Weather radar integration
- [ ] Social features (user reports)

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Test locally with `wrangler dev`
4. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🏆 Acknowledgments

- **Vermont ANR**: Beach water quality data
- **OpenWeatherMap**: Weather data API
- **AirNow**: Air quality information
- **D3.js**: Data visualization
- **Leaflet**: Interactive mapping
- **Cloudflare**: Edge computing platform

---

*Built with ❤️ for the Burlington, VT community*