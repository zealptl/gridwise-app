## 1. Define Agent Name Constant

- [ ] 1.1 Add `ADVISOR_AGENT_NAME = "F1FantasyAdvisor"` as a module-level constant in `service/app/agent/agents.py`
- [ ] 1.2 Replace the `name="F1FantasyAdvisor"` string literal in the `LlmAgent` constructor with the new constant
- [ ] 1.3 Export the constant from `service/app/agent/__init__.py` so the router can import it

## 2. Fix Event Streaming — Filter by Author

- [ ] 2.1 In `service/app/routers/agent.py`, import `ADVISOR_AGENT_NAME` from `app.agent`
- [ ] 2.2 Refactor `_adk_event_to_ag_ui` to accept the event author and return `TEXT_MESSAGE_CONTENT` only when `event.author == ADVISOR_AGENT_NAME`
- [ ] 2.3 For sub-agent events (author in known sub-agent names), emit a `STATE_SNAPSHOT` with `agentProgress.<agentKey>` set to `"working"`
- [ ] 2.4 Define the sub-agent name → `agentProgress` key mapping (e.g., `"F1DataAgent"` → `"f1DataAgent"`) as a module-level dict in `routers/agent.py`
- [ ] 2.5 Emit a final `STATE_SNAPSHOT` with all sub-agent keys set to `"done"` after the `runner.run_async` loop completes successfully

## 3. No-Tools Fallback — Sentinel State Injection

- [ ] 3.1 In `build_f1_advisor_graph` in `agents.py`, collect the toolset result for each sub-agent and check if all are `None`
- [ ] 3.2 When all toolsets are `None`, skip constructing the `DataGathering` `ParallelAgent` and set a flag `tools_available = False`
- [ ] 3.3 In `_stream_ag_ui` in `routers/agent.py`, after session creation and before `runner.run_async`, check `tools_available`; if `False`, call `session.state.update(sentinel)` with the sentinel dict for all three data keys
- [ ] 3.4 Update `ADVISOR_SYSTEM_PROMPT` in `agents.py` to add an explicit instruction: when all three session state keys are `available: false`, respond with a clear error message and do not produce a team recommendation
- [ ] 3.5 When `tools_available = False`, omit the `DataGathering` agent from the advisor's `sub_agents` list so it does not attempt to delegate

## 4. Rewrite Session Service

- [ ] 4.1 Replace the body of `service/app/agent/session.py` with the reference implementation pattern from `aws-agentcore/shared/session.py`, adapting: memory ID loading from env/SSM (keep existing `_load_memory_id` logic), `get_session_service()` factory signature, and `ImportError` guard on `MemoryClient`
- [ ] 4.2 Implement `_role_for_event(event) -> str` static method: `author == "user"` → `"USER"`, has function responses → `"TOOL"`, non-empty author → `"ASSISTANT"`, else → `"OTHER"`
- [ ] 4.3 Update `append_event` to call `create_event(messages=[(serialized_event, role)])` using the tuple format
- [ ] 4.4 Update `create_session` init event to use `messages=[(serialized_init_event, "OTHER")]`
- [ ] 4.5 Wrap all `MemoryClient` calls in `append_event` and `get_session` with `asyncio.to_thread`
- [ ] 4.6 Update `delete_session` to iterate and delete individual remote events (matching reference implementation)

## 5. Backend Verification

- [ ] 5.1 Run the local dev server (`uvicorn`) and send "what should be my team for monaco 2026" — verify only one response block appears (not three)
- [ ] 5.2 Verify no `<tool_use>` JSON blocks or hallucinated tool calls appear in the response
- [ ] 5.3 Verify `STATE_SNAPSHOT` events appear in the SSE stream for each sub-agent (inspect raw SSE in browser devtools or curl)
- [ ] 5.4 Verify session `append_event` no longer logs `Invalid role` warnings in the server logs
- [ ] 5.5 Verify the advisor responds with an honest "data unavailable" message (not a hallucinated team) when AgentCore is not reachable

## 6. Frontend — Progress Panel Component

- [x] 6.1 In the frontend (`app/`), create a `AgentProgressPanel` React component that subscribes to the `agentProgress` coagent state via `useCoAgentStateRender`
- [x] 6.2 Render a row per agent (F1 Data, Intel, Fantasy Context) with an animated spinner for `"working"` and a checkmark for `"done"`
- [x] 6.3 Mount the `AgentProgressPanel` above the `CopilotChat` component in the advisor page
- [x] 6.4 Hide the panel when `agentProgress` state is absent or all agents are `"done"` and the advisor has responded
