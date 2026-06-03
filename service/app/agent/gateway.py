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

# Maps each sub-agent to the list of tool names it requires via the Gateway.
TOOL_REGISTRY = {
    "f1_data_agent": ["get_live_session_data", "get_historical_performance"],
    "intel_agent": ["get_weather", "get_odds", "get_reddit_sentiment"],
    "fantasy_context_agent": [
        "get_user_team",
        "get_current_prices",
        "get_available_chips",
        "get_active_rules",
    ],
    "submission_agent": ["validate_team", "submit_team"],
}


class AgentCoreGateway:
    """Adapter between Google ADK agents and the AWS AgentCore Gateway."""

    def __init__(self) -> None:
        self.endpoint_url: str = self._load_endpoint()
        self._client = None  # lazy init

    # ------------------------------------------------------------------
    # Configuration loading
    # ------------------------------------------------------------------

    def _load_endpoint(self) -> str:
        """Return the Gateway URL.

        Resolution order:
        1. Environment variable ``AGENTCORE_GATEWAY_ENDPOINT`` (fast path for
           local dev and Lambda environments where the value is already injected).
        2. SSM Parameter Store (``/gridwise/agentcore/gateway-endpoint``).
        3. Empty string if both sources fail — module stays importable even when
           AWS credentials are absent.
        """
        if url := os.getenv("AGENTCORE_GATEWAY_ENDPOINT"):
            logger.debug("AgentCore Gateway endpoint loaded from environment variable.")
            return url

        try:
            ssm = boto3.client("ssm", region_name=AWS_REGION)
            resp = ssm.get_parameter(Name=GATEWAY_ENDPOINT_SSM)
            url = resp["Parameter"]["Value"]
            logger.info("AgentCore Gateway endpoint loaded from SSM: %s", url)
            return url
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Could not load AgentCore Gateway endpoint from SSM (%s). "
                "Set AGENTCORE_GATEWAY_ENDPOINT env var for local dev.",
                exc,
            )
            return ""

    # ------------------------------------------------------------------
    # Toolset factory
    # ------------------------------------------------------------------

    def get_toolset_for_agent(self, agent_name: str, tool_names: list[str]):
        """Return an ADK MCPToolset for *tool_names* served via the Gateway.

        Falls back to ``None`` when the ``amazon_bedrock_agentcore`` package is
        not installed (e.g. during local development without the full SDK).

        Args:
            agent_name: Logical name of the sub-agent (used for logging only).
            tool_names: List of tool names to expose through the toolset.

        Returns:
            An ``MCPToolset`` instance, or ``None`` if unavailable.
        """
        if not self.endpoint_url:
            logger.warning(
                "Gateway endpoint not configured — skipping toolset for agent '%s'.",
                agent_name,
            )
            return None

        try:
            from amazon_bedrock_agentcore.tools import MCPToolset  # type: ignore[import]

            logger.debug(
                "Creating MCPToolset for agent '%s' with tools: %s",
                agent_name,
                tool_names,
            )
            return MCPToolset(
                endpoint=self.endpoint_url,
                tool_names=tool_names,
            )
        except ImportError:
            logger.warning(
                "amazon_bedrock_agentcore not installed — returning None toolset for agent '%s'.",
                agent_name,
            )
            return None
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Failed to create MCPToolset for agent '%s': %s",
                agent_name,
                exc,
            )
            return None

    def get_toolset(self, agent_name: str):
        """Convenience wrapper that looks up tool names from TOOL_REGISTRY.

        Args:
            agent_name: Key in :data:`TOOL_REGISTRY`.

        Returns:
            MCPToolset or ``None``.
        """
        tool_names = TOOL_REGISTRY.get(agent_name, [])
        if not tool_names:
            logger.warning(
                "No tools registered for agent '%s' in TOOL_REGISTRY.", agent_name
            )
            return None
        return self.get_toolset_for_agent(agent_name, tool_names)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def verify_gateway_connection(gateway: Optional[AgentCoreGateway] = None) -> bool:
    """Attempt a lightweight connectivity check against the AgentCore Gateway.

    This is called at FastAPI startup.  A failure logs a warning but does *not*
    prevent the application from starting.

    Args:
        gateway: An existing :class:`AgentCoreGateway` instance.  A new one is
            created if not provided.

    Returns:
        ``True`` if the gateway is reachable, ``False`` otherwise.
    """
    if gateway is None:
        try:
            gateway = AgentCoreGateway()
        except Exception as exc:  # noqa: BLE001
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
    except Exception as exc:  # noqa: BLE001
        logger.warning("AgentCore Gateway ping failed: %s", exc)
        return False
