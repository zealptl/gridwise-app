"""
AgentCore Gateway module.
Connects to the AgentCore Gateway and returns ADK-compatible MCPToolset objects.
Gateway endpoint URL is read from SSM parameter /gridwise/agentcore/gateway-endpoint.

Authentication: The gateway uses CUSTOM_JWT auth backed by Cognito. The user's
Cognito JWT (from the Authorization header) is passed directly as the Bearer token.
"""
import logging
import os
from typing import Optional

import boto3

logger = logging.getLogger(__name__)

GATEWAY_ENDPOINT_SSM = "/gridwise/agentcore/gateway-endpoint"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


class AgentCoreGateway:
    """Adapter between Google ADK agents and the AWS AgentCore Gateway."""

    def __init__(self, jwt: Optional[str] = None) -> None:
        self.endpoint_url: str = self._load_endpoint()
        self.jwt = jwt

    def _load_endpoint(self) -> str:
        """Return the Gateway URL from env var or SSM."""
        if url := os.getenv("AGENTCORE_GATEWAY_ENDPOINT"):
            logger.debug("AgentCore Gateway endpoint loaded from environment variable.")
            return url

        try:
            ssm = boto3.client("ssm", region_name=AWS_REGION)
            resp = ssm.get_parameter(Name=GATEWAY_ENDPOINT_SSM)
            url = resp["Parameter"]["Value"]
            logger.info("AgentCore Gateway endpoint loaded from SSM: %s", url)
            return url
        except Exception as exc:
            logger.warning(
                "Could not load AgentCore Gateway endpoint from SSM (%s). "
                "Set AGENTCORE_GATEWAY_ENDPOINT env var for local dev.",
                exc,
            )
            return ""

    def _probe_gateway(self) -> None:
        """Make a test MCP initialize request to log the actual HTTP response code."""
        import json
        try:
            import httpx
            body = json.dumps({
                "jsonrpc": "2.0", "method": "initialize", "id": 1,
                "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                           "clientInfo": {"name": "probe", "version": "1.0"}},
            })
            # Decode JWT to log token_use claim (id vs access token)
            try:
                import base64
                parts = self.jwt.split(".")
                padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
                claims = json.loads(base64.urlsafe_b64decode(padded))
                token_use = claims.get("token_use", "unknown")
                aud = claims.get("aud", claims.get("client_id", "unknown"))
                logger.info("Gateway probe: JWT token_use=%s aud/client_id=%s", token_use, aud)
            except Exception:
                pass

            resp = httpx.post(
                self.endpoint_url,
                content=body,
                headers={
                    "Authorization": f"Bearer {self.jwt}",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
                timeout=5,
            )
            logger.info("Gateway probe HTTP %s: %s", resp.status_code, resp.text[:200])
        except Exception as exc:
            logger.warning("Gateway probe failed: %s", exc)

    def get_toolset_for_agent(self, agent_name: str, discovery_query: str):
        """Return an ADK McpToolset connected to the AgentCore Gateway.

        The gateway endpoint is a Streamable HTTP MCP server. ADK's own
        McpToolset + StreamableHTTPConnectionParams is the correct way to
        consume it — amazon_bedrock_agentcore.tools.MCPToolset does not exist.

        Args:
            agent_name: Logical name of the sub-agent (used for logging only).
            discovery_query: Unused for now; reserved for future semantic
                filtering at the gateway level.

        Returns:
            An McpToolset instance, or None if unavailable.
        """
        if not self.endpoint_url:
            logger.warning(
                "Gateway endpoint not configured — skipping toolset for agent '%s'.",
                agent_name,
            )
            return None

        if not self.jwt:
            logger.warning(
                "No user JWT — skipping toolset for agent '%s'. "
                "Gateway uses Cognito JWT auth; unauthenticated requests will be rejected.",
                agent_name,
            )
            return None

        # Probe the gateway once per gateway instance to surface the real HTTP error.
        if not getattr(self, "_probe_done", False):
            self._probe_done = True
            self._probe_gateway()

        try:
            from google.adk.tools.mcp_tool.mcp_toolset import McpToolset  # type: ignore[import]
            from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams  # type: ignore[import]

            auth_headers = {"Authorization": f"Bearer {self.jwt}"}

            logger.debug(
                "Creating McpToolset for agent '%s' via StreamableHTTP (Cognito JWT): %s",
                agent_name,
                self.endpoint_url,
            )
            return McpToolset(
                connection_params=StreamableHTTPConnectionParams(
                    url=self.endpoint_url,
                    headers=auth_headers,
                ),
            )
        except Exception as exc:
            logger.error(
                "Failed to create McpToolset for agent '%s': %s",
                agent_name,
                exc,
            )
            return None


def verify_gateway_connection(gateway: Optional[AgentCoreGateway] = None) -> bool:
    """Attempt a lightweight connectivity check against the AgentCore Gateway.

    Called at FastAPI startup. Failure logs a warning but does not prevent startup.
    """
    if gateway is None:
        try:
            gateway = AgentCoreGateway()
        except Exception as exc:
            logger.warning("Could not instantiate AgentCoreGateway: %s", exc)
            return False

    if not gateway.endpoint_url:
        logger.warning(
            "AgentCore Gateway endpoint is not configured — gateway unavailable."
        )
        return False

    try:
        import ssl
        import urllib.request

        # AgentCore Gateway health check is at /ping (not /health)
        base = gateway.endpoint_url.rstrip("/")
        # Strip /mcp suffix — ping lives at the root gateway URL
        if base.endswith("/mcp"):
            base = base[:-4]
        ping_url = base + "/ping"
        ssl_ctx = ssl.create_default_context()
        try:
            import certifi
            ssl_ctx.load_verify_locations(certifi.where())
        except ImportError:
            pass
        with urllib.request.urlopen(ping_url, timeout=3, context=ssl_ctx) as response:  # noqa: S310
            if response.status < 400:
                logger.info("AgentCore Gateway ping succeeded (%s).", ping_url)
                return True
            logger.warning(
                "AgentCore Gateway ping returned HTTP %s.", response.status
            )
            return False
    except Exception as exc:
        logger.warning("AgentCore Gateway ping failed: %s", exc)
        return False
