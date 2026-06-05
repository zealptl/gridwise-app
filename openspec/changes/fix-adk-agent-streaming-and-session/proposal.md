## Why

The ADK agent graph has three critical bugs that make it unusable: all sub-agent intermediate messages (including system-level reasoning) are streamed directly to the user instead of only the final synthesized response; sub-agents hallucinate fake tool calls when the AgentCore toolset is unavailable instead of reporting the limitation cleanly; and the session persistence layer uses the wrong API format (`dict` instead of `(text, role)` tuples), causing every event write to fail silently.

## What Changes

- **Event filtering in the streaming layer**: Only text events authored by `F1FantasyAdvisor` are forwarded as `TEXT_MESSAGE_CONTENT` to the user. Sub-agent events are converted to `STATE_SNAPSHOT` progress updates instead.
- **Animated progress panel**: Sub-agent lifecycle events (working / done / error) are emitted as `STATE_SNAPSHOT` so a CopilotKit `useCoAgentStateRender` frontend component can display a per-agent status panel while data is being gathered.
- **No-tools honest fallback**: When `AgentCoreGateway` cannot return a toolset (package not installed or endpoint not configured), the orchestrator pre-injects sentinel state (`{available: false}`) for each sub-agent slot and skips the `DataGathering` parallel agent. The `F1FantasyAdvisor` reads the sentinel state and responds with an honest error message rather than hallucinating.
- **Session service rewrite**: `service/app/agent/session.py` is replaced with a correct implementation that matches the reference in `aws-agentcore/shared/session.py` — using `(text, role)` tuple format for `create_event`, a `_role_for_event` mapper (USER / ASSISTANT / TOOL / OTHER), and `asyncio.to_thread` for all blocking SDK calls.

## Capabilities

### New Capabilities

- `agent-progress-streaming`: Real-time per-agent status updates streamed as `STATE_SNAPSHOT` AG-UI events during parallel data gathering, consumed by a CopilotKit frontend component.
- `agent-no-tools-fallback`: Deterministic, hallucination-free behavior when AgentCore tools are unavailable — sentinel state injection + advisor honest-error response path.

### Modified Capabilities

<!-- No existing spec-level capability requirements are changing. -->

## Impact

- `service/app/routers/agent.py` — `_adk_event_to_ag_ui` and `_stream_ag_ui` event loop modified
- `service/app/agent/agents.py` — `build_f1_advisor_graph` and sub-agent builders modified; no-tools detection added
- `service/app/agent/session.py` — full rewrite
- `app/` (frontend) — new CopilotKit `useCoAgentStateRender` component for the progress panel
- No API contract changes; no new dependencies
