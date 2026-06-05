## Context

The GridWise F1 Fantasy Advisor is a Google ADK multi-agent graph running on AWS AgentCore. The root agent (`F1FantasyAdvisor`, Claude Sonnet) orchestrates a `ParallelAgent` (`DataGathering`) that fans out to three sub-agents (F1DataAgent, IntelAgent, FantasyContextAgent — all Claude Haiku) before synthesizing a recommendation.

Three bugs make the system unusable in its current state:

1. **Event leak**: `Runner.run_async` emits ADK `Event` objects for every agent in the graph. The streaming layer in `routers/agent.py` blindly converts every text-bearing event to `TEXT_MESSAGE_CONTENT`, so all sub-agent intermediate responses reach the user verbatim.

2. **Hallucination on missing tools**: When `amazon_bedrock_agentcore` is not installed (local dev), `AgentCoreGateway.get_toolset_for_agent` returns `None` and sub-agents are built with `tools=[]`. Their instructions still tell them to call tools, so Haiku hallucinates JSON tool-call blocks in plain text.

3. **Session API mismatch**: `service/app/agent/session.py` calls `client.create_event(messages=[{"role": "system", "content": payload}])`. The actual SDK signature is `create_event(messages: List[Tuple[str, str]])` where tuples are `(text, role)` and valid roles are `USER | ASSISTANT | TOOL | OTHER`. Every session write silently fails.

The reference implementation at `aws-agentcore/shared/session.py` already contains the correct pattern; the service version was written independently and diverged.

## Goals / Non-Goals

**Goals:**
- Only `F1FantasyAdvisor` text reaches the user as `TEXT_MESSAGE_CONTENT`
- Sub-agent activity produces real-time `STATE_SNAPSHOT` progress events consumable by a CopilotKit frontend component
- When AgentCore tools are unavailable, the advisor responds with an honest error — no hallucinated tool calls or JSON
- Session event persistence works correctly end-to-end (correct API format, non-blocking calls, correct role mapping)

**Non-Goals:**
- Redesigning the agent graph topology (sub-agent count, model selection, tool routing)
- Frontend implementation of the progress panel component (scoped to backend `STATE_SNAPSHOT` emission; frontend wiring is a separate task)
- Changing how AgentCore Runtime (`runtime_entry.py`) invokes the graph in production

## Decisions

### Decision 1: Filter ADK events by `event.author` in the streaming layer

ADK `Event` objects carry an `author` field containing the agent name that produced the event. Filtering on `event.author == "F1FantasyAdvisor"` is the minimal, correct way to identify root-level responses.

**Alternative considered**: Filter on `event.is_final_response()`. Rejected — ADK marks the final event in a turn as final, but intermediate events from the root agent (partial streaming chunks) are not marked final. Filtering by author is more reliable for the multi-agent case.

**Alternative considered**: Check model tier (Sonnet events only). Rejected — model ID is not available on the `Event` object without additional plumbing.

### Decision 2: Sub-agent events → `STATE_SNAPSHOT` with a structured progress payload

When an event's author is a sub-agent name, emit a `STATE_SNAPSHOT` AG-UI event with:

```json
{
  "type": "STATE_SNAPSHOT",
  "snapshot": {
    "agentProgress": {
      "f1DataAgent": "working|done|error",
      "intelAgent":  "working|done|error",
      "fantasyContextAgent": "working|done|error"
    }
  }
}
```

The frontend's `useCoAgentStateRender` can subscribe to the `agentProgress` key and render an animated status panel.

**Alternative considered**: Emit progress as `TEXT_MESSAGE_CONTENT` prefixed lines (e.g., `_Gathering F1 data…_`). Rejected by user — text-only progress pollutes the chat history and cannot be styled independently.

### Decision 3: No-tools fallback via sentinel state injection before graph execution

When all sub-agent toolsets are `None` (gateway unavailable), skip `DataGathering` entirely and inject sentinel values directly into the ADK session state before invoking the runner:

```python
sentinel = {
    "f1_data":        {"available": False, "reason": "AgentCore tools unavailable"},
    "intel":          {"available": False, "reason": "AgentCore tools unavailable"},
    "fantasy_context":{"available": False, "reason": "AgentCore tools unavailable"},
}
session.state.update(sentinel)
```

The `F1FantasyAdvisor` system prompt already handles the no-data case ("if data unavailable, state this and reduce confidence"). A small addition explicitly instructs it to respond with an honest error when all three slots are `available: false`.

**Alternative considered**: Give sub-agents a local stub tool (e.g., `memory_write`) that writes the sentinel. Rejected — requires packaging and registering stub tools, adds testing surface, and is indistinguishable from the real tool path during code review.

**Alternative considered**: Raise an HTTP error at the router layer when tools are unavailable. Rejected — too blunt; the advisor can and should explain the situation gracefully.

### Decision 4: Replace `session.py` wholesale with the reference pattern

The reference implementation (`aws-agentcore/shared/session.py`) solves all three sub-problems correctly: tuple format, role mapping, `asyncio.to_thread` wrapping. Patching individual lines risks missing the blocking-call issue. A full replacement from the reference is lower risk and produces a file that is auditable against the known-good version.

Key adaptations from reference to service:
- `memory_id` loaded from env var / SSM (same as current code)
- `get_session_service()` factory signature unchanged (called from `agents.py`)
- `MemoryClient` import guarded with `try/except ImportError` (same as current) so local dev without `bedrock_agentcore` falls back gracefully

## Risks / Trade-offs

- **Author string fragility**: Filtering on `event.author == "F1FantasyAdvisor"` couples the filter to the agent's `name` kwarg. If the name changes, the filter silently breaks. Mitigation: define the name as a module-level constant and reference it in both the `LlmAgent` constructor and the filter.

- **STATE_SNAPSHOT ordering**: CopilotKit merges `STATE_SNAPSHOT` payloads; if multiple sub-agent events arrive close together, intermediate states may be skipped on the frontend. This is acceptable — the panel shows final per-agent status, not a log.

- **Sentinel injection race**: If `session.state.update(sentinel)` runs after the runner's first tick, sub-agents might see empty state. Mitigation: inject before `runner.run_async` is called, inside the same async function, with no `await` between injection and run.

- **Session rewrite scope**: The reference `delete_session` implementation iterates and deletes individual events. Current code only removes from the in-memory cache. The rewrite correctly deletes remote events, which is a behaviour change — benign but worth noting.

## Open Questions

- Should the progress panel differentiate between "no tools (expected in free tier)" and "no tools (infrastructure error)"? Currently both map to the same sentinel. Could add a `reason_code` field later.
- Should partial ADK events (streaming chunks from the advisor) be forwarded as they arrive, or buffered until `event.partial == False`? Current plan: forward partials for lower perceived latency.
