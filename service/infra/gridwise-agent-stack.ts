import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as ssm from 'aws-cdk-lib/aws-ssm';

export class GridwiseAgentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // -------------------------------------------------------------------------
    // 2.2 Cognito User Pool — email + password auth
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

    // NOTE: AgentCore Gateway + Memory Store are commented out until
    // AWS::BedrockAgentCore resources are broadly available in us-east-1.
    // new cdk.CfnResource(this, 'GridwiseAgentCoreGateway', { type: 'AWS::BedrockAgentCore::Gateway', ... })
    // new cdk.CfnResource(this, 'GridwiseAgentCoreMemory', { type: 'AWS::BedrockAgentCore::MemoryStore', ... })

    // -------------------------------------------------------------------------
    // 2.5 Secrets Manager — placeholder values only, never real keys
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
    // 2.6 IAM Role for the FastAPI service
    // -------------------------------------------------------------------------
    const fastApiRole = new iam.Role(this, 'GridwiseFastApiRole', {
      roleName: 'gridwise-fastapi-service-role',
      assumedBy: new iam.CompositePrincipal(
        new iam.ServicePrincipal('ec2.amazonaws.com'),
        new iam.ServicePrincipal('lambda.amazonaws.com'),
        new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
      ),
      description: 'IAM role for GridWise FastAPI service - Bedrock, AgentCore, Secrets Manager',
    });

    // Bedrock InvokeModel for Claude Sonnet and Haiku
    fastApiRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
      resources: [
        `arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0`,
        `arn:aws:bedrock:*::foundation-model/anthropic.claude-3-haiku-20240307-v1:0`,
      ],
    }));

    // AgentCore Gateway invoke
    fastApiRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock-agentcore:InvokeGateway',
        'bedrock-agentcore:GetGateway',
        'bedrock-agentcore:ListGatewayTools',
      ],
      resources: ['*'],
    }));

    // AgentCore Memory read/write
    fastApiRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock-agentcore:GetMemory',
        'bedrock-agentcore:PutMemoryRecord',
        'bedrock-agentcore:SearchMemory',
        'bedrock-agentcore:DeleteMemoryRecord',
      ],
      resources: ['*'],
    }));

    // Secrets Manager — gridwise/* only
    fastApiRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['secretsmanager:GetSecretValue'],
      resources: [
        `arn:aws:secretsmanager:*:${this.account}:secret:gridwise/*`,
      ],
    }));

    // SSM Parameter Store read — gridwise/* only
    fastApiRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['ssm:GetParameter', 'ssm:GetParameters'],
      resources: [
        `arn:aws:ssm:*:${this.account}:parameter/gridwise/*`,
      ],
    }));

    new cdk.CfnOutput(this, 'FastApiRoleArn', { value: fastApiRole.roleArn });
    new ssm.StringParameter(this, 'FastApiRoleArnParam', {
      parameterName: '/gridwise/iam/fastapi-role-arn',
      stringValue: fastApiRole.roleArn,
    });

    // -------------------------------------------------------------------------
    // AgentCore Gateway with 11 registered tools
    // -------------------------------------------------------------------------

    // FastAPI service base URL — read from SSM or env (set after ECS deploy)
    const fastApiBaseUrl = ssm.StringParameter.valueForStringParameter(
      this,
      '/gridwise/service/fastapi-base-url',
    );

    const TOOL_DESCRIPTIONS: Record<string, string> = {
      get_live_session_data:
        "Fetches real-time F1 session data from the OpenF1 API for the latest race weekend session (practice, qualifying, sprint, or race). Call this first in any recommendation flow to get current lap times, tyre stints, on-track weather conditions, and race control messages (flags, safety car, penalties). Returns a structured dict with keys: session, laps, stints, weather, race_control. If OpenF1 is unavailable, returns {\"error\": \"OpenF1 API unavailable\", \"available\": false} — treat this as reduced-confidence input, do not abort the recommendation.",
      get_historical_performance:
        "Fetches season-to-date historical performance data from the Jolpica/Ergast F1 API. Use this to understand driver and constructor championship standings, recent race results, and form trends that live session data cannot provide. Returns a structured dict with keys: driver_standings, constructor_standings, recent_results. Individual endpoint failures return {\"error\": \"...\"} under the relevant key — use whatever data is available and note any gaps.",
      get_weather:
        "Fetches a 3-day weather forecast for a given F1 circuit location from WeatherAPI. Use this to assess rain probability, wind conditions, and temperature shifts that affect tyre strategy and car setup. Pass the circuit city or country as circuit_location (e.g. \"Monaco\", \"Silverstone\"). Returns location, forecast (array of daily forecasts), and race_day_forecast (last day in the forecast window). PREMIUM TOOL — only available to premium-tier users. On API failure, returns {\"error\": \"WeatherAPI unavailable\"}.",
      get_odds:
        "Fetches current Formula 1 race winner betting odds from The Odds API and converts them to implied win probabilities per driver. Use this as a market-consensus signal to validate or challenge your own predictions — high implied probability for a driver suggests broad agreement across bookmakers. Returns event (race name and date) and probabilities (dict mapping driver name to implied probability 0–1). PREMIUM TOOL — only available to premium-tier users. On API failure, returns {\"error\": \"Odds API unavailable\"}.",
      get_reddit_sentiment:
        "Searches recent posts in r/formula1 and r/FantasyF1 for community discussion about a specific race or driver. Use this to surface grassroots intelligence: upgrade rumours, mechanical concerns, driver form commentary, and fantasy community consensus picks that may not appear in official data. Pass the race name or driver name as race_name. Returns r_formula1 posts, r_FantasyF1 posts, and a sentiment_summary string. PREMIUM TOOL — only available to premium-tier users. On API failure, returns {\"error\": \"Reddit API unavailable\"}.",
      get_user_team:
        "Retrieves the authenticated user's current F1 Fantasy team from the GridWise database. Use this at the start of every recommendation to understand the user's existing picks before suggesting changes. Requires user_id in session state. Returns the user's current drivers, constructors, DRS Boost selection, total team cost, budget remaining, and transfer count used this race week.",
      get_current_prices:
        "Returns the live market price for every active F1 driver and constructor in the GridWise fantasy game. Use this alongside the user's current team to calculate transfer costs and budget headroom for proposed changes. Returns a dict with drivers and constructors arrays, each entry containing id, name, team, and price in millions.",
      get_available_chips:
        "Returns the chip/booster availability for the authenticated user this season. Use this before making any chip-dependent recommendation (e.g. Limitless, Wildcard). Requires user_id in session state. Returns a dict mapping each of the six chip names (wildcard, limitless, no_negative, triple_boost, autopilot, final_fix) to a boolean indicating whether it has been used.",
      get_active_rules:
        "Fetches all currently active fantasy rules and constraints from the GridWise rules engine. Call this before constructing or validating any team recommendation to ensure compliance. Returns {\"rules\": [...]} where each rule has rule_type, name, description, and a human-readable constraint string (e.g. \"Total team cost must not exceed 100M\", \"Team must include exactly 5 drivers and 2 constructors\").",
      validate_team:
        "Validates a proposed fantasy team composition against all active GridWise rules. MUST be called before submit_team — submission without prior validation will be rejected. Pass the full proposed team as a dict with team_name, drivers (list of driver dicts with driver_id, driver_name, team_name, price), constructors, drs_boost_driver_id, and budget_cap. Returns {\"valid\": true, \"violations\": []} on success, or {\"valid\": false, \"violations\": [...]} with violation details on failure. Never submit a team that failed validation.",
      submit_team:
        "Persists the user's validated fantasy team to the GridWise database. Only call this after validate_team returns valid: true AND the user has given explicit confirmation they want to apply the recommendation. Requires user_id in session state and the validated team dict. Automatically creates a new team or updates the existing active team for the current season. Returns {\"success\": true, \"team_id\": \"...\"} on success or {\"error\": \"...\"} on failure.",
    };

    // Premium tools require custom:tier = "premium" JWT claim
    const PREMIUM_TOOLS = new Set(['get_weather', 'get_odds', 'get_reddit_sentiment']);

    function makeToolDef(
      toolName: string,
      endpointPath: string,
      inputSchema: object,
      isPremium: boolean,
    ): object {
      const accessPolicy = isPremium
        ? {
            type: 'JWT_CLAIM',
            claimName: 'custom:tier',
            claimValues: ['premium'],
          }
        : { type: 'ANY_AUTHENTICATED' };

      return {
        name: toolName,
        description: TOOL_DESCRIPTIONS[toolName],
        inputSchema: { json: inputSchema },
        handler: {
          http: {
            url: `${fastApiBaseUrl}/api/v1${endpointPath}`,
            authConfig: {
              iamConfig: {
                roleArn: fastApiRole.roleArn,
              },
            },
          },
        },
        accessPolicy,
      };
    }

    const tools = [
      makeToolDef('get_live_session_data', '/agent/tools/get-live-session-data', {
        type: 'object', properties: {}, required: [],
      }, false),
      makeToolDef('get_historical_performance', '/agent/tools/get-historical-performance', {
        type: 'object', properties: {}, required: [],
      }, false),
      makeToolDef('get_weather', '/agent/tools/get-weather', {
        type: 'object',
        properties: { circuit_location: { type: 'string', description: 'Circuit city or country, e.g. "Monaco"' } },
        required: ['circuit_location'],
      }, true),
      makeToolDef('get_odds', '/agent/tools/get-odds', {
        type: 'object', properties: {}, required: [],
      }, true),
      makeToolDef('get_reddit_sentiment', '/agent/tools/get-reddit-sentiment', {
        type: 'object',
        properties: { race_name: { type: 'string', description: 'Race or driver name to search for' } },
        required: ['race_name'],
      }, true),
      makeToolDef('get_user_team', '/agent/tools/get-user-team', {
        type: 'object',
        properties: { session_state: { type: 'object', description: 'Session state containing user_id' } },
        required: [],
      }, false),
      makeToolDef('get_current_prices', '/agent/tools/get-current-prices', {
        type: 'object', properties: {}, required: [],
      }, false),
      makeToolDef('get_available_chips', '/agent/tools/get-available-chips', {
        type: 'object',
        properties: { session_state: { type: 'object', description: 'Session state containing user_id' } },
        required: [],
      }, false),
      makeToolDef('get_active_rules', '/agent/tools/get-active-rules', {
        type: 'object', properties: {}, required: [],
      }, false),
      makeToolDef('validate_team', '/agent/tools/validate-team', {
        type: 'object',
        properties: {
          team: { type: 'object', description: 'Full team dict with team_name, drivers, constructors, drs_boost_driver_id, budget_cap' },
          user_team_count: { type: 'integer', description: 'Number of teams the user has created this season', default: 0 },
        },
        required: ['team'],
      }, false),
      makeToolDef('submit_team', '/agent/tools/submit-team', {
        type: 'object',
        properties: {
          session_state: { type: 'object', description: 'Session state containing user_id' },
          team: { type: 'object', description: 'Validated team dict' },
          validated: { type: 'boolean', description: 'Must be true — set by validate_team result' },
        },
        required: ['team', 'validated'],
      }, false),
    ];

    const gateway = new cdk.CfnResource(this, 'GridwiseAgentCoreGateway', {
      type: 'AWS::BedrockAgentCore::Gateway',
      properties: {
        Name: 'gridwise-agent-gateway',
        Description: 'AgentCore Gateway for GridWise F1 Fantasy Advisor — serves all 11 agent tools via FastAPI',
        RoleArn: fastApiRole.roleArn,
        AuthorizerConfig: {
          type: 'COGNITO_USER_POOL',
          cognitoConfig: {
            userPoolIds: [userPool.userPoolId],
            clientIds: [userPoolClient.userPoolClientId],
          },
        },
        Tools: tools,
      },
    });

    new cdk.CfnOutput(this, 'AgentCoreGatewayId', {
      value: gateway.ref,
      description: 'AgentCore Gateway resource ID',
    });

    new ssm.StringParameter(this, 'GatewayEndpointParam', {
      parameterName: '/gridwise/agentcore/gateway-endpoint',
      stringValue: cdk.Fn.getAtt('GridwiseAgentCoreGateway', 'Endpoint').toString(),
      description: 'AgentCore Gateway endpoint URL for gateway.py',
    });
  }
}
