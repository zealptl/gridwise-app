import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as cr from 'aws-cdk-lib/custom-resources';

export class GridwiseAgentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // -------------------------------------------------------------------------
    // Cognito User Pool — email + password auth
    // -------------------------------------------------------------------------
    const userPool = new cognito.UserPool(this, 'GridwiseUserPool', {
      userPoolName: 'gridwise-user-pool',
      selfSignUpEnabled: true,
      signInAliases: { email: true },
      autoVerify: { email: true },
      passwordPolicy: {
        minLength: 8,
        requireUppercase: true,
        requireLowercase: true,
        requireDigits: true,
        requireSymbols: false,
      },
      accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      customAttributes: {
        tier: new cognito.StringAttribute({ mutable: true }),
      },
    });

    const userPoolClient = new cognito.UserPoolClient(this, 'GridwiseUserPoolClient', {
      userPool,
      userPoolClientName: 'gridwise-app-client',
      authFlows: {
        userPassword: true,
        userSrp: true,
      },
      generateSecret: false,
    });

    new cdk.CfnOutput(this, 'UserPoolId', { value: userPool.userPoolId });
    new cdk.CfnOutput(this, 'UserPoolClientId', { value: userPoolClient.userPoolClientId });

    new ssm.StringParameter(this, 'UserPoolIdParam', {
      parameterName: '/gridwise/cognito/user-pool-id',
      stringValue: userPool.userPoolId,
    });
    new ssm.StringParameter(this, 'UserPoolClientIdParam', {
      parameterName: '/gridwise/cognito/app-client-id',
      stringValue: userPoolClient.userPoolClientId,
    });

    // -------------------------------------------------------------------------
    // Secrets Manager — placeholder values only, never real keys
    // -------------------------------------------------------------------------
    new secretsmanager.Secret(this, 'WeatherApiKey', {
      secretName: 'gridwise/weather-api-key',
      description: 'WeatherAPI key for F1 circuit forecasts',
      secretStringValue: cdk.SecretValue.unsafePlainText(JSON.stringify({ value: 'REPLACE_ME' })),
    });

    new secretsmanager.Secret(this, 'OddsApiKey', {
      secretName: 'gridwise/odds-api-key',
      description: 'The Odds API key for F1 race winner markets',
      secretStringValue: cdk.SecretValue.unsafePlainText(JSON.stringify({ value: 'REPLACE_ME' })),
    });

    new secretsmanager.Secret(this, 'RedditCredentials', {
      secretName: 'gridwise/reddit-credentials',
      description: 'Reddit OAuth credentials for sentiment analysis',
      secretStringValue: cdk.SecretValue.unsafePlainText(
        JSON.stringify({ client_id: 'REPLACE_ME', client_secret: 'REPLACE_ME' })
      ),
    });

    new secretsmanager.Secret(this, 'F1Credentials', {
      secretName: 'gridwise/f1-credentials',
      description: 'F1 account credentials for Fantasy API auth',
      secretStringValue: cdk.SecretValue.unsafePlainText(
        JSON.stringify({ username: 'REPLACE_ME', password: 'REPLACE_ME' })
      ),
    });

    // -------------------------------------------------------------------------
    // IAM Role — FastAPI service (EC2 / ECS / Lambda)
    // -------------------------------------------------------------------------
    const fastApiRole = new iam.Role(this, 'GridwiseFastApiRole', {
      roleName: 'gridwise-fastapi-service-role',
      assumedBy: new iam.CompositePrincipal(
        new iam.ServicePrincipal('ec2.amazonaws.com'),
        new iam.ServicePrincipal('lambda.amazonaws.com'),
        new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
      ),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
      description: 'IAM role for GridWise FastAPI service',
    });

    fastApiRole.addToPolicy(new iam.PolicyStatement({
      actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
      resources: [
        `arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0`,
        `arn:aws:bedrock:*::foundation-model/anthropic.claude-3-haiku-20240307-v1:0`,
      ],
    }));

    fastApiRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        'bedrock-agentcore:InvokeGateway',
        'bedrock-agentcore:GetGateway',
        'bedrock-agentcore:ListGatewayTargets',
      ],
      resources: ['*'],
    }));

    fastApiRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        'bedrock-agentcore:GetMemory',
        'bedrock-agentcore:PutMemoryRecord',
        'bedrock-agentcore:SearchMemory',
        'bedrock-agentcore:DeleteMemoryRecord',
      ],
      resources: ['*'],
    }));

    fastApiRole.addToPolicy(new iam.PolicyStatement({
      actions: ['secretsmanager:GetSecretValue'],
      resources: [`arn:aws:secretsmanager:*:${this.account}:secret:gridwise/*`],
    }));

    fastApiRole.addToPolicy(new iam.PolicyStatement({
      actions: ['ssm:GetParameter', 'ssm:GetParameters'],
      resources: [`arn:aws:ssm:*:${this.account}:parameter/gridwise/*`],
    }));

    new cdk.CfnOutput(this, 'FastApiRoleArn', { value: fastApiRole.roleArn });
    new ssm.StringParameter(this, 'FastApiRoleArnParam', {
      parameterName: '/gridwise/iam/fastapi-role-arn',
      stringValue: fastApiRole.roleArn,
    });

    // -------------------------------------------------------------------------
    // IAM Role — AgentCore Gateway service role
    // The gateway assumes this role to invoke Lambda targets.
    // Trust policy uses bedrock-agentcore.amazonaws.com as the principal.
    // After first deploy, tighten the Condition to the specific gateway ARN.
    // -------------------------------------------------------------------------
    const gatewayServiceRole = new iam.Role(this, 'GridwiseGatewayServiceRole', {
      roleName: 'gridwise-gateway-service-role',
      assumedBy: new iam.ServicePrincipal('bedrock-agentcore.amazonaws.com', {
        conditions: {
          StringEquals: { 'aws:SourceAccount': this.account },
        },
      }),
      description: 'AgentCore Gateway service role — invokes the tools-proxy Lambda on behalf of agents',
    });

    // -------------------------------------------------------------------------
    // Lambda — tools proxy
    // Routes AgentCore Gateway tool calls to the FastAPI service.
    // FASTAPI_BASE_URL is injected at deploy time from SSM; the value is
    // populated after the ECS/EC2 service is running.
    // -------------------------------------------------------------------------
    const fastApiBaseUrl = ssm.StringParameter.valueForStringParameter(
      this,
      '/gridwise/service/fastapi-base-url',
    );

    const toolsProxyLambda = new lambda.Function(this, 'GridwiseToolsProxyFn', {
      functionName: 'gridwise-tools-proxy',
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.handler',
      // Inline proxy — routes by toolName to the matching FastAPI endpoint.
      // Replace with lambda.Code.fromAsset(...) once the handler grows beyond
      // what fits comfortably inline.
      code: lambda.Code.fromInline(`
import json, os, urllib.request, urllib.error

BASE = os.environ['FASTAPI_BASE_URL'].rstrip('/')

ROUTES = {
  'get_live_session_data':     '/api/v1/agent/tools/get-live-session-data',
  'get_historical_performance':'/api/v1/agent/tools/get-historical-performance',
  'get_weather':               '/api/v1/agent/tools/get-weather',
  'get_odds':                  '/api/v1/agent/tools/get-odds',
  'get_reddit_sentiment':      '/api/v1/agent/tools/get-reddit-sentiment',
  'get_user_team':             '/api/v1/agent/tools/get-user-team',
  'get_current_prices':        '/api/v1/agent/tools/get-current-prices',
  'get_available_chips':       '/api/v1/agent/tools/get-available-chips',
  'get_active_rules':          '/api/v1/agent/tools/get-active-rules',
  'validate_team':             '/api/v1/agent/tools/validate-team',
  'submit_team':               '/api/v1/agent/tools/submit-team',
}

def handler(event, context):
  tool = event.get('toolName', '')
  if tool not in ROUTES:
    return {'error': f'Unknown tool: {tool}'}
  body = json.dumps(event.get('toolInput', {})).encode()
  req = urllib.request.Request(
    BASE + ROUTES[tool], data=body,
    headers={'Content-Type': 'application/json'}, method='POST',
  )
  with urllib.request.urlopen(req, timeout=55) as resp:
    return json.loads(resp.read())
`),
      timeout: cdk.Duration.seconds(60),
      memorySize: 256,
      role: fastApiRole,
      environment: {
        FASTAPI_BASE_URL: fastApiBaseUrl,
      },
    });

    // Allow the gateway service role to invoke the proxy
    gatewayServiceRole.addToPolicy(new iam.PolicyStatement({
      actions: ['lambda:InvokeFunction'],
      resources: [toolsProxyLambda.functionArn],
    }));

    // Resource-based permission on the Lambda so AgentCore Gateway can invoke it
    toolsProxyLambda.addPermission('AgentCoreGatewayInvoke', {
      principal: new iam.ArnPrincipal(gatewayServiceRole.roleArn),
      action: 'lambda:InvokeFunction',
    });

    // -------------------------------------------------------------------------
    // Inline tool schemas for the gateway target
    // -------------------------------------------------------------------------
    const INLINE_TOOLS = [
      {
        name: 'get_live_session_data',
        description: 'Fetches real-time F1 session data (lap times, tyre stints, weather, race control messages) from the OpenF1 API for the current race weekend session.',
        inputSchema: { type: 'object', properties: {}, required: [] },
      },
      {
        name: 'get_historical_performance',
        description: 'Fetches season-to-date driver standings, constructor standings, and recent race results from the Jolpica/Ergast F1 API.',
        inputSchema: { type: 'object', properties: {}, required: [] },
      },
      {
        name: 'get_weather',
        description: 'Fetches a 3-day weather forecast for an F1 circuit location. PREMIUM — requires custom:tier=premium JWT claim.',
        inputSchema: {
          type: 'object',
          properties: {
            circuit_location: { type: 'string', description: 'Circuit city or country, e.g. "Monaco"' },
          },
          required: ['circuit_location'],
        },
      },
      {
        name: 'get_odds',
        description: 'Fetches current F1 race winner betting odds and converts them to implied win probabilities. PREMIUM — requires custom:tier=premium JWT claim.',
        inputSchema: { type: 'object', properties: {}, required: [] },
      },
      {
        name: 'get_reddit_sentiment',
        description: 'Searches r/formula1 and r/FantasyF1 for community discussion about a race or driver. PREMIUM — requires custom:tier=premium JWT claim.',
        inputSchema: {
          type: 'object',
          properties: {
            race_name: { type: 'string', description: 'Race or driver name to search for' },
          },
          required: ['race_name'],
        },
      },
      {
        name: 'get_user_team',
        description: "Retrieves the authenticated user's current F1 Fantasy team from the GridWise database.",
        inputSchema: {
          type: 'object',
          properties: {
            session_state: { type: 'object', description: 'Session state containing user_id' },
          },
          required: [],
        },
      },
      {
        name: 'get_current_prices',
        description: 'Returns live market prices for every active F1 driver and constructor in the GridWise fantasy game.',
        inputSchema: { type: 'object', properties: {}, required: [] },
      },
      {
        name: 'get_available_chips',
        description: "Returns chip/booster availability for the authenticated user this season (wildcard, limitless, no_negative, triple_boost, autopilot, final_fix).",
        inputSchema: {
          type: 'object',
          properties: {
            session_state: { type: 'object', description: 'Session state containing user_id' },
          },
          required: [],
        },
      },
      {
        name: 'get_active_rules',
        description: 'Fetches all currently active fantasy rules and constraints from the GridWise rules engine.',
        inputSchema: { type: 'object', properties: {}, required: [] },
      },
      {
        name: 'validate_team',
        description: 'Validates a proposed fantasy team against all active GridWise rules. MUST be called before submit_team.',
        inputSchema: {
          type: 'object',
          properties: {
            team: { type: 'object', description: 'Full team dict with team_name, drivers, constructors, drs_boost_driver_id, budget_cap' },
            user_team_count: { type: 'integer', description: 'Number of teams the user has created this season', default: 0 },
          },
          required: ['team'],
        },
      },
      {
        name: 'submit_team',
        description: "Persists the validated fantasy team to the GridWise database. Only call after validate_team returns valid:true and the user has confirmed.",
        inputSchema: {
          type: 'object',
          properties: {
            session_state: { type: 'object', description: 'Session state containing user_id' },
            team: { type: 'object', description: 'Validated team dict' },
            validated: { type: 'boolean', description: 'Must be true — set by validate_team result' },
          },
          required: ['team', 'validated'],
        },
      },
    ];

    // -------------------------------------------------------------------------
    // AgentCore Gateway — CUSTOM_JWT authorizer backed by Cognito OIDC
    //
    // The CreateGateway / CreateGatewayTarget APIs are called via AwsCustomResource
    // because CDK L2 constructs for AgentCore Gateway are not yet available.
    // Set installLatestAwsSdk: true so the Lambda runtime picks up the
    // bedrock-agentcore-control client even on first deploy.
    // -------------------------------------------------------------------------
    const customResourcePolicy = cr.AwsCustomResourcePolicy.fromStatements([
      new iam.PolicyStatement({
        actions: [
          'bedrock-agentcore:CreateGateway',
          'bedrock-agentcore:DeleteGateway',
          'bedrock-agentcore:CreateGatewayTarget',
          'bedrock-agentcore:DeleteGatewayTarget',
          'iam:PassRole',
        ],
        resources: ['*'],
      }),
    ]);

    const cognitoDiscoveryUrl = `https://cognito-idp.${this.region}.amazonaws.com/${userPool.userPoolId}/.well-known/openid-configuration`;

    const createGateway = new cr.AwsCustomResource(this, 'GridwiseAgentCoreGateway', {
      installLatestAwsSdk: true,
      onCreate: {
        service: 'BedrockAgentCoreControl',
        action: 'createGateway',
        parameters: {
          name: 'gridwise-agent-gateway',
          roleArn: gatewayServiceRole.roleArn,
          protocolType: 'MCP',
          authorizerType: 'CUSTOM_JWT',
          authorizerConfiguration: {
            customJWTAuthorizer: {
              discoveryUrl: cognitoDiscoveryUrl,
              allowedClients: [userPoolClient.userPoolClientId],
            },
          },
        },
        physicalResourceId: cr.PhysicalResourceId.fromResponse('gatewayId'),
      },
      onDelete: {
        service: 'BedrockAgentCoreControl',
        action: 'deleteGateway',
        parameters: {
          gatewayIdentifier: new cr.PhysicalResourceIdReference(),
        },
      },
      policy: customResourcePolicy,
    });

    const gatewayId  = createGateway.getResponseField('gatewayId');
    const gatewayUrl = createGateway.getResponseField('gatewayUrl');

    // -------------------------------------------------------------------------
    // Gateway Target — Lambda proxy with all 11 inline tool schemas
    // -------------------------------------------------------------------------
    const createTarget = new cr.AwsCustomResource(this, 'GridwiseToolsTarget', {
      installLatestAwsSdk: true,
      onCreate: {
        service: 'BedrockAgentCoreControl',
        action: 'createGatewayTarget',
        parameters: {
          gatewayIdentifier: gatewayId,
          name: 'gridwise-f1-tools',
          description: 'All GridWise F1 Fantasy agent tools served via FastAPI proxy Lambda',
          targetConfiguration: {
            mcp: {
              lambda: {
                lambdaArn: toolsProxyLambda.functionArn,
                toolSchema: {
                  inlinePayload: INLINE_TOOLS,
                },
              },
            },
          },
          credentialProviderConfigurations: [
            { credentialProviderType: 'GATEWAY_IAM_ROLE' },
          ],
        },
        physicalResourceId: cr.PhysicalResourceId.fromResponse('targetId'),
      },
      onDelete: {
        service: 'BedrockAgentCoreControl',
        action: 'deleteGatewayTarget',
        parameters: {
          gatewayIdentifier: gatewayId,
          targetIdentifier: new cr.PhysicalResourceIdReference(),
        },
      },
      policy: customResourcePolicy,
    });

    createTarget.node.addDependency(createGateway);

    // -------------------------------------------------------------------------
    // Outputs
    // -------------------------------------------------------------------------
    new cdk.CfnOutput(this, 'AgentCoreGatewayId', {
      value: gatewayId,
      description: 'AgentCore Gateway ID',
    });

    new cdk.CfnOutput(this, 'AgentCoreGatewayUrl', {
      value: gatewayUrl,
      description: 'AgentCore Gateway MCP endpoint URL',
    });

    new cdk.CfnOutput(this, 'GatewayServiceRoleArn', {
      value: gatewayServiceRole.roleArn,
      description: 'Gateway service role — tighten the trust Condition to the gateway ARN after first deploy',
    });

    new ssm.StringParameter(this, 'GatewayEndpointParam', {
      parameterName: '/gridwise/agentcore/gateway-endpoint',
      stringValue: gatewayUrl,
      description: 'AgentCore Gateway MCP endpoint URL for gateway.py',
    });
  }
}
