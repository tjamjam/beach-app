# Beach Status Checker

This script checks the status of beaches and sends notifications to subscribers when the status changes.

## Setup

### Environment Variables

You need to set the following environment variable:

- `CF_API_TOKEN`: Your Cloudflare API token for authenticating with the Cloudflare Worker

### How to get your CF_API_TOKEN

1. Go to your Cloudflare Worker dashboard
2. Navigate to Settings > Variables
3. Find the `CF_API_TOKEN` secret
4. Copy the token value

### Setting up the environment variable

You have several options:

#### Option 1: Export the variable in your shell
```bash
export CF_API_TOKEN='your_token_here'
python check_status.py
```

#### Option 2: Create a .env file
Create a file named `.env` in the backend directory with:
```
CF_API_TOKEN=your_token_here
```

Then install python-dotenv:
```bash
pip install python-dotenv
```

#### Option 3: Set it when running the script
```bash
CF_API_TOKEN=your_token_here python check_status.py
```

## Running the script

```bash
python check_status.py
```

## Troubleshooting

If you get a 401 Unauthorized error, it means:
1. The CF_API_TOKEN is not set
2. The token is incorrect
3. The token has expired

Check that your token is correct and try again. 