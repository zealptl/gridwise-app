#!/usr/bin/env bash
# Reads from secrets.local.env and pushes values to AWS Secrets Manager.
# Run this locally after filling in secrets.local.env.
# NEVER commit secrets.local.env or add real values to this script.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../secrets.local.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found. Copy secrets.local.env.example to secrets.local.env and fill in real values."
  exit 1
fi

source "$ENV_FILE"

aws secretsmanager put-secret-value \
  --secret-id gridwise/weather-api-key \
  --secret-string "{\"value\":\"$WEATHER_API_KEY\"}"
echo "✓ gridwise/weather-api-key populated"

aws secretsmanager put-secret-value \
  --secret-id gridwise/odds-api-key \
  --secret-string "{\"value\":\"$ODDS_API_KEY\"}"
echo "✓ gridwise/odds-api-key populated"

aws secretsmanager put-secret-value \
  --secret-id gridwise/reddit-credentials \
  --secret-string "{\"client_id\":\"$REDDIT_CLIENT_ID\",\"client_secret\":\"$REDDIT_CLIENT_SECRET\"}"
echo "✓ gridwise/reddit-credentials populated"

aws secretsmanager put-secret-value \
  --secret-id gridwise/f1-credentials \
  --secret-string "{\"username\":\"$F1_USERNAME\",\"password\":\"$F1_PASSWORD\"}"
echo "✓ gridwise/f1-credentials populated"

echo "All secrets populated successfully."
