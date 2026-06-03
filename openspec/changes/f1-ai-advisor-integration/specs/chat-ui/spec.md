## ADDED Requirements

### Requirement: Chat page provides a conversational interface to the AI advisor
The system SHALL provide a dedicated React chat page (route `/advisor`) where authenticated users can converse with the F1 Fantasy Advisor. The page SHALL render streaming assistant responses in real time using the SSE endpoint.

#### Scenario: User sends a message and sees streaming response
- **WHEN** the user types a message and submits it on the chat page
- **THEN** the message appears in the conversation thread, and the assistant's response streams in token-by-token until complete

#### Scenario: Conversation history persists within the page session
- **WHEN** the user sends multiple messages in one browser session
- **THEN** all prior messages and responses are visible in the conversation thread in chronological order

#### Scenario: Unauthenticated user is redirected to login
- **WHEN** an unauthenticated user navigates to `/advisor`
- **THEN** they are redirected to the login page before the chat interface is rendered

### Requirement: Session is created when the chat page loads
The system SHALL call `POST /api/v1/agent/sessions` when the chat page mounts to obtain a `session_id`. The `session_id` SHALL be used for all subsequent chat requests within that page visit.

#### Scenario: Session ID obtained on page load
- **WHEN** the chat page component mounts
- **THEN** it calls the session creation endpoint and stores the returned `session_id` in component state before rendering the message input

#### Scenario: Failed session creation shows error state
- **WHEN** the session creation request fails
- **THEN** the chat page renders an error message and disables the message input until the session is successfully created

### Requirement: Chat input is disabled while the assistant is responding
The system SHALL disable the message input and send button while an SSE stream is active, preventing the user from sending a new message before the current response completes.

#### Scenario: Input disabled during streaming
- **WHEN** the user submits a message and the SSE stream begins
- **THEN** the message input field and send button are disabled and a loading indicator is visible

#### Scenario: Input re-enabled after stream completes
- **WHEN** the SSE stream closes (assistant response complete or error)
- **THEN** the message input and send button are re-enabled and focus is returned to the input field

### Requirement: Recommended team changes are rendered as structured UI
The system SHALL detect when the assistant's response contains a team recommendation and render it as a structured card (not just plain text) showing drivers, constructors, DRS Boost pick, and transfer diff.

#### Scenario: Recommendation card rendered for team suggestions
- **WHEN** the assistant response includes a structured team recommendation
- **THEN** the chat UI renders a recommendation card listing the 5 drivers, 2 constructors, DRS Boost assignment, and any transfers required from the user's current team

#### Scenario: Apply button triggers team submission
- **WHEN** the user clicks "Apply Recommendation" on a recommendation card
- **THEN** the UI sends a follow-up chat message confirming the selection, which triggers the agent's SubmissionAgent to validate and submit the team
