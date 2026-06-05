## ADDED Requirements

### Requirement: SSM FastAPI base URL pre-seeded before CDK deploy
The SSM parameter `/gridwise/service/fastapi-base-url` SHALL be set to the live FastAPI service base URL before running `cdk deploy`. The Lambda proxy function reads this parameter at creation time; a missing parameter SHALL cause the CDK deploy to fail with a clear error.

#### Scenario: SSM param set before deploy
- **WHEN** `/gridwise/service/fastapi-base-url` exists in SSM with a reachable URL before `cdk deploy` runs
- **THEN** `cdk deploy` completes successfully and the Lambda environment includes `FASTAPI_BASE_URL`

#### Scenario: SSM param missing causes deploy failure
- **WHEN** `/gridwise/service/fastapi-base-url` does not exist in SSM and `cdk deploy` is run
- **THEN** CloudFormation fails with a parameter resolution error

### Requirement: CDK stack deployed successfully
The system SHALL have all resources in `gridwise-agent-stack.ts` created in AWS after `cdk deploy` completes: Cognito User Pool + Client, 4 Secrets Manager secrets, `gridwise-fastapi-service-role` IAM role, `gridwise-gateway-service-role` IAM role, `gridwise-tools-proxy` Lambda, and the AgentCore Gateway with a Lambda target containing all 11 tool schemas.

#### Scenario: All CloudFormation outputs present after deploy
- **WHEN** `cdk deploy` completes without error
- **THEN** CloudFormation outputs include `UserPoolId`, `UserPoolClientId`, `FastApiRoleArn`, `AgentCoreGatewayId`, `AgentCoreGatewayUrl`, and `GatewayServiceRoleArn`

#### Scenario: Gateway lists all 11 tools
- **WHEN** `aws bedrock-agentcore list-gateway-tools --gateway-id <id>` is run after deploy
- **THEN** all 11 tool names are present in the response

### Requirement: Secrets populated with real values
After `cdk deploy`, `scripts/populate-secrets.sh` SHALL be run with a populated `secrets.local.env` to replace placeholder `REPLACE_ME` values in all 4 Secrets Manager secrets (`gridwise/weather-api-key`, `gridwise/odds-api-key`, `gridwise/reddit-credentials`, `gridwise/f1-credentials`).

#### Scenario: Secret value updated
- **WHEN** `populate-secrets.sh` runs successfully
- **THEN** `aws secretsmanager get-secret-value --secret-id gridwise/weather-api-key` returns a non-`REPLACE_ME` value

#### Scenario: Missing secrets.local.env causes script to abort
- **WHEN** `populate-secrets.sh` is run without `secrets.local.env` present
- **THEN** the script exits with a non-zero code and prints an error message

### Requirement: SSM parameters written by CDK are readable by FastAPI
After deploy, SSM parameters `/gridwise/cognito/user-pool-id`, `/gridwise/cognito/app-client-id`, and `/gridwise/agentcore/gateway-endpoint` SHALL exist and be readable by the `gridwise-fastapi-service-role`.

#### Scenario: FastAPI reads Cognito user pool ID from SSM
- **WHEN** the FastAPI service starts and `auth.py` fetches the user pool ID
- **THEN** the SSM parameter `/gridwise/cognito/user-pool-id` resolves to the deployed Cognito user pool ID
