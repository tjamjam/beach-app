# Beach Status Application

A comprehensive beach water quality monitoring system that tracks Burlington's beaches, sends notifications to subscribers, and provides real-time status updates with historical data visualization.

## 🏗️ Architecture Overview

### Core Components

1. **Python Checker Script** (`backend/check_status.py`)
   - Scrapes PDF reports from Vermont Department of Health
   - Tracks status changes for all Burlington beaches
   - Sends email notifications to subscribers
   - Logs historical data to CSV

2. **Cloudflare Worker API** (`backend/index.js`)
   - Provides weather and air quality data
   - Manages email subscriber list
   - Handles authentication for API calls

3. **Frontend Applications**
   - **Main Page** (`frontend/index.html`): Lakewood Beach status with weather/air quality
   - **Overview Page** (`frontend/overview.html`): Interactive map and historical timeline

4. **GitHub Actions** (`.github/workflows/`)
   - Automated hourly status checks
   - Automated deployments to Cloudflare Workers and GitHub Pages

## 📁 Project Structure

```
beach-app/
├── backend/
│   ├── check_status.py          # Main status checker script
│   ├── index.js                 # Cloudflare Worker API
│   ├── historical_status.csv    # Historical beach data
│   ├── fake_historical_status.csv # Test dataset
│   ├── .env                     # Local environment variables
│   └── wrangler.toml           # Cloudflare Worker config
├── frontend/
│   ├── index.html              # Main beach status page
│   ├── overview.html           # Overview page with map/timeline
│   └── images/
│       └── background.jpg      # Background image
├── .github/workflows/
│   ├── checker.yml             # Hourly status check workflow
│   ├── deploy.yml              # Deployment workflow
│   └── test-deploy.yml         # Test deployment workflow
├── status.json                 # Current beach statuses (root)
├── current_status.txt          # Legacy status file
└── .gitignore                 # Git ignore rules
```

## 🔧 Setup & Configuration

### Environment Variables

#### Required for Python Script (`backend/check_status.py`)
```bash
# Authentication
CF_API_TOKEN=your_cloudflare_api_token

# Email Configuration (Gmail SMTP)
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Test Mode (optional)
TEST_MODE=true  # Only sends to TEST_EMAIL
TEST_EMAIL=terrencefradet@gmail.com
```

#### Required for Cloudflare Worker (`backend/index.js`)
```bash
# API Keys
OPENWEATHER_API_KEY=your_openweather_api_key
AIRNOW_API_KEY=your_airnow_api_key

# Authentication
CF_API_TOKEN=your_cloudflare_api_token
```

### Local Development Setup

1. **Install Dependencies**
   ```bash
   # Python dependencies
   pip install requests pdfplumber python-dotenv
   
   # Node.js dependencies (for Cloudflare Worker)
   npm install -g wrangler
   ```

2. **Configure Environment**
   ```bash
   # Create local environment file
   cp backend/.env.example backend/.env
   # Edit backend/.env with your actual values
   ```

3. **Test Local Setup**
   ```bash
   cd backend
   python check_status.py
   ```

### Cloudflare Worker Setup

1. **Deploy Worker**
   ```bash
   cd backend
   wrangler deploy
   ```

2. **Set Secrets**
   ```bash
   wrangler secret put OPENWEATHER_API_KEY
   wrangler secret put AIRNOW_API_KEY
   wrangler secret put CF_API_TOKEN
   ```

## 🔄 Data Flow

### Status Check Process
1. **PDF Scraping**: `check_status.py` fetches PDF from Vermont Health Department
2. **Status Parsing**: Extracts beach names, status indicators, and notes
3. **Change Detection**: Compares with previous `status.json`
4. **Historical Logging**: Records changes to `historical_status.csv`
5. **Notification**: Sends emails to subscribers if target beach status changes
6. **Data Update**: Writes new status to `status.json`

### API Endpoints
- `GET /weather` - Current weather and forecast
- `GET /air-quality` - Air quality data
- `POST /subscribe` - Add email subscriber
- `GET /get-subscribers` - List subscribers (requires auth)

## 🎨 Frontend Development

### Main Page (`frontend/index.html`)
- **Purpose**: Display Lakewood Beach status with weather/air quality
- **Key Features**:
  - Real-time status display
  - Weather and air quality widgets
  - Alternative beach suggestions
  - Email subscription form

### Overview Page (`frontend/overview.html`)
- **Purpose**: Comprehensive view of all beaches
- **Key Features**:
  - Interactive Leaflet.js map
  - Status table with all beaches
  - D3.js historical timeline heatmap
  - Summer open rate calculations

### Styling Guidelines
- **Colors**: Green (`#00a045`), Yellow (`#c7a900`), Red (`#c21616`)
- **Background**: `images/background.jpg`
- **Layout**: Responsive design with mobile-first approach

## 📊 Data Sources

### Beach Status Data
- **Source**: Vermont Department of Health PDF
- **URL**: `https://anrweb.vt.gov/FPR/SwimWater/CityOfBurlingtonPublicReport.aspx`
- **Format**: PDF table with status indicators
- **Beaches**: 10 Burlington beaches with coordinates

### Weather Data
- **Source**: OpenWeatherMap API
- **Location**: Burlington, VT (44.51, -73.24)
- **Data**: Current weather, hourly forecast, conditions

### Air Quality Data
- **Source**: AirNow API
- **Location**: Burlington, VT (05401)
- **Data**: AQI, category, pollutant levels

## 🔐 Authentication & Security

### API Token Management
- **CF_API_TOKEN**: Used for Cloudflare Worker API authentication
- **GitHub Secrets**: Store sensitive tokens for CI/CD
- **Local Development**: Use `.env` files (gitignored)

### Email Authentication
- **Gmail SMTP**: Requires app password (not regular password)
- **Test Mode**: Restricts notifications to single email during development

## 🚀 Deployment

### GitHub Actions Workflows

#### `checker.yml` (Hourly Status Check)
- **Trigger**: Every hour via cron
- **Actions**:
  - Runs `check_status.py`
  - Commits updated `status.json`
  - Sends notifications on status changes

#### `deploy.yml` (Deployment)
- **Trigger**: Push to main branch
- **Actions**:
  - Deploys Cloudflare Worker
  - Deploys frontend to GitHub Pages

### Manual Deployment
```bash
# Deploy Cloudflare Worker
cd backend
wrangler deploy

# Deploy frontend (GitHub Pages)
# Push to main branch triggers automatic deployment
```

## 🧪 Testing

### Local Testing
```bash
# Test PDF parsing
cd backend
python check_status.py

# Test notifications
python test_notification.py

# Test API token
python test_github_token.py
```

### GitHub Actions Testing
- **Workflow**: `test-deploy.yml`
- **Purpose**: Test deployment configuration
- **Trigger**: Manual workflow dispatch

## 📈 Adding New Features

### Adding a New Beach
1. **Update Coordinates** in `backend/check_status.py`:
   ```python
   BEACH_COORDINATES = {
       "New Beach Name": {"lat": 44.123, "lon": -73.456},
       # ... existing beaches
   }
   ```

2. **Update Map** in `frontend/overview.html`:
   ```javascript
   const beaches = [
       { name: "New Beach Name", lat: 44.123, lon: -73.456 },
       // ... existing beaches
   ];
   ```

### Adding New Data Sources
1. **Update Python Script** to fetch new data
2. **Update Cloudflare Worker** to serve new endpoints
3. **Update Frontend** to display new data

### Adding New Notifications
1. **Update `send_notifications()`** in `check_status.py`
2. **Configure new service** (email, SMS, webhook, etc.)
3. **Test locally** before deploying

## 🐛 Troubleshooting

### Common Issues

#### 401 Unauthorized Errors
- **Cause**: Missing or incorrect `CF_API_TOKEN`
- **Solution**: Verify token in Cloudflare Worker secrets

#### Email Not Sending
- **Cause**: Incorrect Gmail credentials or app password
- **Solution**: Use Gmail app password, not regular password

#### PDF Parsing Failures
- **Cause**: PDF format changes or network issues
- **Solution**: Check PDF URL and table structure

#### Deployment Failures
- **Cause**: Node.js version or API token permissions
- **Solution**: Update Node.js to v20+ and verify token permissions

### Debug Commands
```bash
# Test API connectivity
curl -H "X-API-Token: your_token" https://beach-api.terrencefradet.workers.dev/get-subscribers

# Test PDF parsing
cd backend
python -c "from check_status import test_pdf_parsing; test_pdf_parsing()"

# Check Cloudflare Worker logs
wrangler tail
```

## 📝 Development Guidelines

### Code Style
- **Python**: Follow PEP 8 guidelines
- **JavaScript**: Use ES6+ features, consistent formatting
- **HTML/CSS**: Semantic HTML, responsive CSS

### File Organization
- **Backend**: All server-side code in `backend/`
- **Frontend**: All client-side code in `frontend/`
- **Configuration**: Environment-specific configs in root

### Data Management
- **Current Status**: `status.json` in project root
- **Historical Data**: `backend/historical_status.csv`
- **Configuration**: Environment variables and secrets

### Security Best Practices
- **Never commit secrets** to repository
- **Use environment variables** for sensitive data
- **Validate all inputs** in API endpoints
- **Implement proper CORS** headers

## 🔄 Maintenance

### Regular Tasks
- **Monitor PDF format changes** from Vermont Health Department
- **Update API keys** before expiration
- **Review notification logs** for delivery issues
- **Backup historical data** regularly

### Performance Monitoring
- **API response times** for weather/air quality
- **PDF parsing success rate**
- **Email delivery rates**
- **Frontend load times**

## 📞 Support

### Key Files for Development
- `backend/check_status.py` - Core status checking logic
- `backend/index.js` - API endpoints
- `frontend/index.html` - Main user interface
- `frontend/overview.html` - Overview page with visualizations
- `.github/workflows/checker.yml` - Automated status checking

### Environment Setup Checklist
- [ ] Python dependencies installed
- [ ] Node.js v20+ installed
- [ ] Cloudflare Worker deployed
- [ ] Environment variables configured
- [ ] GitHub secrets set
- [ ] Local testing completed

This README serves as your comprehensive guide for maintaining and extending the beach status application. Use it as a reference when adding new features or troubleshooting issues. 