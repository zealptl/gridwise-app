import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as apprunner from 'aws-cdk-lib/aws-apprunner';
import * as cr from 'aws-cdk-lib/custom-resources';

export class GridwiseAgentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // -------------------------------------------------------------------------
    // Import Foundation stack outputs
    // -------------------------------------------------------------------------
    const fastApiRoleArn       = cdk.Fn.importValue('FastApiRoleArn');
    const gatewayServiceRoleArn = cdk.Fn.importValue('GatewayServiceRoleArn');
    const agentRuntimeRoleArn  = cdk.Fn.importValue('AgentRuntimeRoleArn');
    const userPoolId           = cdk.Fn.importValue('UserPoolId');
    const userPoolClientId     = cdk.Fn.importValue('UserPoolClientId');

    const fastApiRole = iam.Role.fromRoleArn(this, 'ImportedFastApiRole', fastApiRoleArn);
    const gatewayServiceRole = iam.Role.fromRoleArn(this, 'ImportedGatewayServiceRole', gatewayServiceRoleArn);

    // -------------------------------------------------------------------------
    // App Runner — FastAPI service (task 12)
    // -------------------------------------------------------------------------
    const appRunnerService = new apprunner.CfnService(this, 'GridwiseFastApiService', {
      serviceName: 'gridwise-fastapi',
      sourceConfiguration: {
        imageRepository: {
          imageIdentifier: `${this.account}.dkr.ecr.${this.region}.amazonaws.com/gridwise-fastapi:latest`,
          imageRepositoryType: 'ECR',
          imageConfiguration: {
            port: '8080',
            runtimeEnvironmentVariables: [
              { name: 'AWS_REGION', value: this.region },
              { name: 'ENVIRONMENT', value: 'production' },
            ],
          },
        },
        autoDeploymentsEnabled: false,
      },
      instanceConfiguration: {
        instanceRoleArn: fastApiRoleArn,
      },
      healthCheckConfiguration: {
        path: '/health',
        protocol: 'HTTP',
      },
    });

    const appRunnerUrl = `https://${appRunnerService.attrServiceUrl}`;

    new cdk.CfnOutput(this, 'AppRunnerUrl', { value: appRunnerUrl });

    new ssm.StringParameter(this, 'FastApiBaseUrlParam', {
      parameterName: '/gridwise/service/fastapi-base-url',
      stringValue: appRunnerUrl,
    });

    // -------------------------------------------------------------------------
    // Lambda — tools proxy with SigV4 signing (task 5)
    // -------------------------------------------------------------------------
    const fastApiBaseUrl = ssm.StringParameter.valueForStringParameter(
      this,
      '/gridwise/service/fastapi-base-url',
    );

    const toolsProxyLambda = new lambda.Function(this, 'GridwiseToolsProxyFn', {
      functionName: 'gridwise-tools-proxy',
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('../../app/agent/lambda/tools_proxy'),
      timeout: cdk.Duration.seconds(60),
      memorySize: 256,
      role: fastApiRole,
      environment: {
        FASTAPI_BASE_URL: fastApiBaseUrl,
      },
    });

    // Resource-based permission on the Lambda so AgentCore Gateway can invoke it
    toolsProxyLambda.addPermission('AgentCoreGatewayInvoke', {
      principal: new iam.ArnPrincipal(gatewayServiceRoleArn),
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

    const cognitoDiscoveryUrl = `https://cognito-idp.${this.region}.amazonaws.com/${userPoolId}/.well-known/openid-configuration`;

    const createGateway = new cr.AwsCustomResource(this, 'GridwiseAgentCoreGateway', {
      installLatestAwsSdk: true,
      onCreate: {
        service: 'BedrockAgentCoreControl',
        action: 'createGateway',
        parameters: {
          name: 'gridwise-agent-gateway',
          roleArn: gatewayServiceRoleArn,
          protocolType: 'MCP',
          authorizerType: 'CUSTOM_JWT',
          authorizerConfiguration: {
            customJWTAuthorizer: {
              discoveryUrl: cognitoDiscoveryUrl,
              allowedClients: [userPoolClientId],
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
    // AgentCore Runtime Custom Resource (task 11)
    // -------------------------------------------------------------------------
    const runtimeCrHandler = new lambda.Function(this, 'RuntimeCrHandler', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('../../app/agent/lambda/runtime_cr'),
      timeout: cdk.Duration.minutes(5),
      role: fastApiRole,
    });

    runtimeCrHandler.addToRolePolicy(new iam.PolicyStatement({
      actions: ['bedrock-agentcore:CreateAgentRuntime', 'bedrock-agentcore:GetAgentRuntime'],
      resources: ['*'],
    }));

    const agentRuntimeCr = new cdk.CustomResource(this, 'AgentCoreRuntime', {
      serviceToken: new cr.Provider(this, 'RuntimeCrProvider', {
        onEventHandler: runtimeCrHandler,
      }).serviceToken,
      properties: {
        ImageUri: `${this.account}.dkr.ecr.${this.region}.amazonaws.com/gridwise-agent-runtime:latest`,
        RuntimeRoleArn: agentRuntimeRoleArn,
        RuntimeName: 'gridwise-agent-runtime',
      },
    });

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

    new cdk.CfnOutput(this, 'AgentCoreRuntimeArn', {
      value: agentRuntimeCr.getAttString('RuntimeArn'),
    });

    new ssm.StringParameter(this, 'GatewayEndpointParam', {
      parameterName: '/gridwise/agentcore/gateway-endpoint',
      stringValue: gatewayUrl,
      description: 'AgentCore Gateway MCP endpoint URL for gateway.py',
    });
  }
}
