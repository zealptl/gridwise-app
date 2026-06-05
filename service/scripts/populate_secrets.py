"""
Push local secrets from secrets.local.env to AWS Secrets Manager.

Usage:
    uv run python scripts/populate_secrets.py [--env-file secrets.local.env] [--region us-east-1]

The script reads key=value pairs from the env file and maps them to
Secrets Manager secret names under the gridwise/ prefix. Only keys
listed in SECRET_MAP are processed — everything else is ignored.
"""
import argparse
import os
import sys


SECRET_MAP = {
    # env file key              → Secrets Manager secret name
    "MONGODB_ATLAS_URI":          "gridwise/mongodb-atlas-uri",
    "WEATHER_API_KEY":            "gridwise/weather-api-key",
    "ODDS_API_KEY":               "gridwise/odds-api-key",
    "REDDIT_CLIENT_ID":           "gridwise/reddit-credentials",
    "F1_USERNAME":                "gridwise/f1-credentials",
}

# Keys that are combined into a single JSON secret
COMPOSITE_SECRETS = {
    "gridwise/reddit-credentials": {
        "REDDIT_CLIENT_ID": "client_id",
        "REDDIT_CLIENT_SECRET": "client_secret",
    },
    "gridwise/f1-credentials": {
        "F1_USERNAME": "username",
        "F1_PASSWORD": "password",
    },
}


def load_env_file(path: str) -> dict[str, str]:
    values: dict[str, str] = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            values[key] = val
    return values


def put_secret(client, name: str, value: str) -> None:
    try:
        client.put_secret_value(SecretId=name, SecretString=value)
        print(f"  updated  {name}")
    except client.exceptions.ResourceNotFoundException:
        client.create_secret(Name=name, SecretString=value)
        print(f"  created  {name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default="secrets.local.env")
    parser.add_argument("--region", default=os.getenv("AWS_REGION", "us-east-1"))
    args = parser.parse_args()

    env_path = args.env_file
    if not os.path.exists(env_path):
        # Also try relative to script location
        env_path = os.path.join(os.path.dirname(__file__), "..", args.env_file)
    if not os.path.exists(env_path):
        print(f"ERROR: env file not found: {args.env_file}", file=sys.stderr)
        sys.exit(1)

    env = load_env_file(env_path)
    print(f"Loaded {len(env)} keys from {args.env_file}")

    import boto3
    import json
    client = boto3.client("secretsmanager", region_name=args.region)

    pushed: set[str] = set()

    # Handle composite secrets first
    for secret_name, field_map in COMPOSITE_SECRETS.items():
        payload: dict[str, str] = {}
        for env_key, json_key in field_map.items():
            if env_key in env:
                payload[json_key] = env[env_key]
        if payload:
            put_secret(client, secret_name, json.dumps(payload))
            pushed.add(secret_name)

    # Handle simple (plain string) secrets
    for env_key, secret_name in SECRET_MAP.items():
        if secret_name in pushed:
            continue
        if env_key not in env:
            continue
        put_secret(client, secret_name, env[env_key])

    print("Done.")


if __name__ == "__main__":
    main()
