import * as path from 'path';
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as cr from 'aws-cdk-lib/custom-resources';
import { Gateway, GatewayAuthorizer, ToolSchema } from 'aws-cdk-lib/aws-bedrockagentcore';

export class GridwiseAgentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // -------------------------------------------------------------------------
    // Import Foundation stack outputs
    // -------------------------------------------------------------------------
    const fastApiRoleArn        = cdk.Fn.importValue('FastApiRoleArn');
    const gatewayServiceRoleArn = cdk.Fn.importValue('GatewayServiceRoleArn');
    const agentRuntimeRoleArn   = cdk.Fn.importValue('AgentRuntimeRoleArn');
    const userPoolId            = cdk.Fn.importValue('UserPoolId');
    const userPoolClientId      = cdk.Fn.importValue('UserPoolClientId');

    const fastApiRole = iam.Role.fromRoleArn(this, 'ImportedFastApiRole', fastApiRoleArn);
    const gatewayServiceRole = iam.Role.fromRoleArn(this, 'ImportedGatewayServiceRole', gatewayServiceRoleArn);

    // App Runner skipped (not available on free tier).
    // Update /gridwise/service/fastapi-base-url in SSM with your local/ngrok URL when testing.
    const fastApiBaseUrlParam = new ssm.StringParameter(this, 'FastApiBaseUrlParam', {
      parameterName: '/gridwise/service/fastapi-base-url',
      stringValue: 'http://localhost:8080',
    });

    const appRunnerUrl = fastApiBaseUrlParam.stringValue;

    // -------------------------------------------------------------------------
    // Lambda - tools proxy with SigV4 signing (task 5)
    // -------------------------------------------------------------------------
    const toolsProxyLambda = new lambda.Function(this, 'GridwiseToolsProxyFn', {
      functionName: 'gridwise-tools-proxy',
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('../app/agent/lambda/tools_proxy'),
      timeout: cdk.Duration.seconds(60),
      memorySize: 256,
      role: fastApiRole,
      environment: {
        FASTAPI_BASE_URL: appRunnerUrl,
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
        description: 'Fetches a 3-day weather forecast for an F1 circuit location. PREMIUM - requires custom:tier=premium JWT claim.',
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
        description: 'Fetches current F1 race winner betting odds and converts them to implied win probabilities. PREMIUM - requires custom:tier=premium JWT claim.',
        inputSchema: { type: 'object', properties: {}, required: [] },
      },
      {
        name: 'get_reddit_sentiment',
        description: 'Searches r/formula1 and r/FantasyF1 for community discussion about a race or driver. PREMIUM - requires custom:tier=premium JWT claim.',
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
            user_team_count: { type: 'integer', description: 'Number of teams the user has created this season (default 0)' },
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
            validated: { type: 'boolean', description: 'Must be true - set by validate_team result' },
          },
          required: ['team', 'validated'],
        },
      },
    ];

    // -------------------------------------------------------------------------
    // AgentCore Gateway - L2 construct with CUSTOM_JWT Cognito authorizer
    // -------------------------------------------------------------------------
    const cognitoDiscoveryUrl = `https://cognito-idp.${this.region}.amazonaws.com/${userPoolId}/.well-known/openid-configuration`;

    const gateway = new Gateway(this, 'GridwiseAgentCoreGateway', {
      gatewayName: 'gridwise-agent-gateway',
      role: gatewayServiceRole,
      authorizerConfiguration: GatewayAuthorizer.usingCustomJwt({
        discoveryUrl: cognitoDiscoveryUrl,
        allowedClients: [userPoolClientId],
      }),
    });

    gateway.addLambdaTarget('GridwiseToolsTarget', {
      gatewayTargetName: 'gridwise-tools-target',
      lambdaFunction: toolsProxyLambda,
      toolSchema: ToolSchema.fromLocalAsset(path.join(__dirname, 'schemas', 'tools.json')),
    });

    const gatewayId  = gateway.gatewayId;
    const gatewayUrl = gateway.gatewayUrl ?? '';

    // -------------------------------------------------------------------------
    // AgentCore Runtime Custom Resource (task 11)
    // -------------------------------------------------------------------------
    const runtimeCrHandler = new lambda.Function(this, 'RuntimeCrHandler', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('../app/agent/lambda/runtime_cr'),
      timeout: cdk.Duration.minutes(5),
      role: fastApiRole,
    });

    // AgentCore Runtime permissions live on fastApiRole in GridwiseFoundationStack

    const agentRuntimeCr = new cdk.CustomResource(this, 'AgentCoreRuntime', {
      serviceToken: new cr.Provider(this, 'RuntimeCrProvider', {
        onEventHandler: runtimeCrHandler,
      }).serviceToken,
      properties: {
        ImageUri: `${this.account}.dkr.ecr.${this.region}.amazonaws.com/gridwise-agent-runtime:latest`,
        RuntimeRoleArn: agentRuntimeRoleArn,
        RuntimeName: 'gridwise_agent_runtime',
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

    // Memory resources are created via scripts/create_memory_resources.py
    // (CDK L2 Memory construct causes stuck CREATING state on rollback)
  }
}
