import json
import os
import botocore.auth
import botocore.awsrequest
import botocore.credentials
import botocore.session
import urllib.request
import urllib.error
import urllib.parse

BASE = os.environ['FASTAPI_BASE_URL'].rstrip('/')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

ROUTES = {
    'get_live_session_data': '/api/v1/agent/tools/get-live-session-data',
    'get_historical_performance': '/api/v1/agent/tools/get-historical-performance',
    'get_weather': '/api/v1/agent/tools/get-weather',
    'get_odds': '/api/v1/agent/tools/get-odds',
    'get_reddit_sentiment': '/api/v1/agent/tools/get-reddit-sentiment',
    'get_user_team': '/api/v1/agent/tools/get-user-team',
    'get_current_prices': '/api/v1/agent/tools/get-current-prices',
    'get_available_chips': '/api/v1/agent/tools/get-available-chips',
    'get_active_rules': '/api/v1/agent/tools/get-active-rules',
    'validate_team': '/api/v1/agent/tools/validate-team',
    'submit_team': '/api/v1/agent/tools/submit-team',
}


def _sign_request(url: str, body: bytes) -> dict:
    """Sign an HTTP request with AWS SigV4 using the Lambda execution role."""
    session = botocore.session.get_session()
    credentials = session.get_credentials().get_frozen_credentials()

    parsed = urllib.parse.urlparse(url)
    request = botocore.awsrequest.AWSRequest(
        method='POST',
        url=url,
        data=body,
        headers={'Content-Type': 'application/json', 'Host': parsed.netloc},
    )

    signer = botocore.auth.SigV4Auth(credentials, 'execute-api', AWS_REGION)
    signer.add_auth(request)
    return dict(request.headers)


def handler(event, context):
    tool = event.get('toolName', '')
    if tool not in ROUTES:
        return {'error': f'Unknown tool: {tool}'}

    body = json.dumps(event.get('toolInput', {})).encode()
    url = BASE + ROUTES[tool]
    signed_headers = _sign_request(url, body)

    req = urllib.request.Request(url, data=body, headers=signed_headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=55) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {'error': f'HTTP {e.code}: {e.reason}'}
