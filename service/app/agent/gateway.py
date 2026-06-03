"""
AgentCore Gateway module.
Connects to the AgentCore Gateway and returns ADK-compatible MCPToolset objects.
Gateway endpoint URL is read from SSM parameter /gridwise/agentcore/gateway-endpoint.
"""
import os
import logging
import boto3
from typing import Optional

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

    def get_toolset_for_agent(self, agent_name: str, discovery_query: str):
        """Return an ADK MCPToolset using semantic discovery for the given query.

        Injects the user JWT as a bearer token so the gateway can apply
        tier-based tool filtering per user.

        Args:
            agent_name: Logical name of the sub-agent (used for logging only).
            discovery_query: Natural language description sent to the gateway
                for semantic tool selection.

        Returns:
            An MCPToolset instance, or None if unavailable.
        """
        if not self.endpoint_url:
            logger.warning(
                "Gateway endpoint not configured — skipping toolset for agent '%s'.",
                agent_name,
            )
            return None

        try:
            from amazon_bedrock_agentcore.tools import MCPToolset  # type: ignore[import]

            headers = {}
            if self.jwt:
                headers["Authorization"] = f"Bearer {self.jwt}"

            logger.debug(
                "Creating MCPToolset for agent '%s' with semantic query: %s",
                agent_name,
                discovery_query,
            )
            return MCPToolset(
                endpoint=self.endpoint_url,
                discovery_query=discovery_query,
                headers=headers,
            )
        except ImportError:
            logger.warning(
                "amazon_bedrock_agentcore not installed — returning None toolset for agent '%s'.",
                agent_name,
            )
            return None
        except Exception as exc:
            logger.error(
                "Failed to create MCPToolset for agent '%s': %s",
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
        import urllib.request

        ping_url = gateway.endpoint_url.rstrip("/") + "/health"
        with urllib.request.urlopen(ping_url, timeout=3) as response:  # noqa: S310
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
