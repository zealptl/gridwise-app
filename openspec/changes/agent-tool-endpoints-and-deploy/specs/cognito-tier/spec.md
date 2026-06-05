## ADDED Requirements

### Requirement: custom:tier attribute on Cognito user pool
The CDK stack SHALL define a `custom:tier` custom attribute (string, mutable) on the Cognito user pool. New users SHALL have `custom:tier` set to `"free"` at registration. The attribute SHALL be included in the Cognito ID token so downstream services can read it without a DB lookup.

#### Scenario: New user registration sets tier to free
- **WHEN** a user registers via `POST /auth/register`
- **THEN** their Cognito user record has `custom:tier = "free"`

#### Scenario: Tier claim present in JWT
- **WHEN** a registered user authenticates and receives a Cognito ID token
- **THEN** the decoded JWT includes `custom:tier` with value `"free"` (or `"premium"` if upgraded)

### Requirement: get_user_tier utility in auth.py
The system SHALL expose `get_user_tier(jwt_token: str) -> str` in `service/app/auth.py` that decodes the Cognito JWT, reads `custom:tier`, and returns the string value. If the claim is absent, it SHALL return `"free"` as the default.

#### Scenario: Premium user tier extracted
- **WHEN** `get_user_tier` is called with a JWT containing `custom:tier = "premium"`
- **THEN** the function returns `"premium"`

#### Scenario: Missing claim defaults to free
- **WHEN** `get_user_tier` is called with a JWT that does not contain `custom:tier`
- **THEN** the function returns `"free"`

### Requirement: Register endpoint sets custom:tier attribute
The `/auth/register` endpoint SHALL call Cognito `AdminUpdateUserAttributes` after user creation to set `custom:tier = "free"`. This SHALL complete before returning the registration response.

#### Scenario: Attribute set after registration
- **WHEN** `POST /auth/register` succeeds
- **THEN** the Cognito user's `custom:tier` attribute is `"free"` verifiable via `aws cognito-idp admin-get-user`
