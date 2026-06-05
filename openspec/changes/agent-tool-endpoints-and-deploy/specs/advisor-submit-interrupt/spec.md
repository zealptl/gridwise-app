## ADDED Requirements

### Requirement: Apply Recommendation button resolves CopilotKit interrupt
The advisor page SHALL render an "Apply Recommendation" button within the `TeamRecommendationCard` component. Clicking the button SHALL resolve the active CopilotKit Human-in-the-Loop interrupt with a confirmation payload — it SHALL NOT send a raw text message. The button SHALL be disabled while no interrupt is pending and SHALL disable itself immediately after being clicked to prevent double-submission.

#### Scenario: Button resolves interrupt on click
- **WHEN** the agent has emitted a pending interrupt and the user clicks "Apply Recommendation"
- **THEN** CopilotKit resolves the interrupt with a confirmation event that triggers `SubmissionAgent`

#### Scenario: Button disabled when no interrupt pending
- **WHEN** `TeamRecommendationCard` is rendered but no interrupt is active
- **THEN** the "Apply Recommendation" button is rendered in a disabled state

#### Scenario: Button disables after click to prevent double-submit
- **WHEN** the user clicks "Apply Recommendation"
- **THEN** the button becomes disabled immediately and remains disabled until the stream closes

### Requirement: Submission outcome displayed in chat thread
After `SubmissionAgent` processes the interrupt, the system SHALL display either a success message (including the persisted team ID) or a failure message (with validation violations) in the chat thread as a CopilotKit message event.

#### Scenario: Successful submission shows team ID
- **WHEN** `submit_team` succeeds
- **THEN** the chat thread shows a success message containing the persisted team ID

#### Scenario: Validation failure shown to user
- **WHEN** `validate_team` returns violations
- **THEN** the chat thread shows the violations and does NOT call `submit_team`
