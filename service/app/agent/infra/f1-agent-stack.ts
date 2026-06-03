import * as cdk from 'aws-cdk-lib';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as opensearchserverless from 'aws-cdk-lib/aws-opensearchserverless';
import { Construct } from 'constructs';
import * as path from 'path';

export class F1FantasyBedrockAgentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ═══════════════════════════════════════════════════════════
    // 1. SECRETS — Store all API credentials
    // ═══════════════════════════════════════════════════════════

    // You'll populate these via Console or CLI after deployment
    const openF1Secret = new secretsmanager.Secret(this, 'OpenF1Credentials', {
      secretName: 'f1-agent/openf1-credentials',
      description: 'OpenF1 API credentials for real-time data access',
      generateSecretString: {
        secretStringTemplate: JSON.stringify({
          username: 'REPLACE_ME',
          password: 'REPLACE_ME',
        }),
        generateStringKey: 'placeholder',
      },
    });

    const weatherApiSecret = new secretsmanager.Secret(this, 'WeatherApiKey', {
      secretName: 'f1-agent/weather-api-key',
      description: 'WeatherAPI.com API key',
    });

    const oddsApiSecret = new secretsmanager.Secret(this, 'OddsApiKey', {
      secretName: 'f1-agent/odds-api-key',
      description: 'The Odds API key for betting market data',
    });

    const redditSecret = new secretsmanager.Secret(this, 'RedditCredentials', {
      secretName: 'f1-agent/reddit-credentials',
      description: 'Reddit API OAuth2 client credentials',
    });

    const f1FantasySecret = new secretsmanager.Secret(this, 'F1FantasyCredentials', {
      secretName: 'f1-agent/f1-fantasy-credentials',
      description: 'F1 Fantasy API Bearer token and user GUID',
    });

    // ═══════════════════════════════════════════════════════════
    // 2. S3 BUCKETS — Schemas + Knowledge Base documents
    // ═══════════════════════════════════════════════════════════

    const schemaBucket = new s3.Bucket(this, 'SchemaBucket', {
      bucketName: `f1-agent-schemas-${this.account}`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    const knowledgeBaseBucket = new s3.Bucket(this, 'KnowledgeBaseBucket', {
      bucketName: `f1-agent-knowledge-base-${this.account}`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // Upload OpenAPI schemas to S3
    new s3deploy.BucketDeployment(this, 'DeploySchemas', {
      sources: [s3deploy.Source.asset(path.join(__dirname, '../schemas'))],
      destinationBucket: schemaBucket,
      destinationKeyPrefix: 'openapi-schemas/',
    });

    // Upload knowledge base documents (scoring rules, circuit profiles, etc.)
    new s3deploy.BucketDeployment(this, 'DeployKnowledgeBase', {
      sources: [s3deploy.Source.asset(path.join(__dirname, '../knowledge-base'))],
      destinationBucket: knowledgeBaseBucket,
      destinationKeyPrefix: 'documents/',
    });

    // ═══════════════════════════════════════════════════════════
    // 3. IAM ROLE — For the Bedrock Agent
    // ═══════════════════════════════════════════════════════════

    const agentRole = new iam.Role(this, 'BedrockAgentRole', {
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com'),
      description: 'IAM role for the F1 Fantasy Bedrock Agent',
    });

    agentRole.addToPolicy(new iam.PolicyStatement({
      actions: ['bedrock:InvokeModel'],
      resources: [
        `arn:aws:bedrock:${this.region}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0`,
        `arn:aws:bedrock:${this.region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0`,
      ],
    }));

    agentRole.addToPolicy(new iam.PolicyStatement({
      actions: ['s3:GetObject'],
      resources: [
        `${schemaBucket.bucketArn}/*`,
        `${knowledgeBaseBucket.bucketArn}/*`,
      ],
    }));

    // ═══════════════════════════════════════════════════════════
    // 4. LAMBDA FUNCTIONS — One per Action Group
    // ═══════════════════════════════════════════════════════════

    // Shared Lambda execution role
    const lambdaRole = new iam.Role(this, 'LambdaExecutionRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    // Grant access to all secrets
    [openF1Secret, weatherApiSecret, oddsApiSecret, redditSecret, f1FantasySecret].forEach(secret => {
      secret.grantRead(lambdaRole);
    });

    // --- Lambda: GetLiveSessionData (OpenF1 API) ---
    const liveSessionLambda = new lambda.Function(this, 'GetLiveSessionDataFn', {
      functionName: 'f1-agent-get-live-session-data',
      runtime: lambda.Runtime.NODEJS_20_X,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/get-live-session-data')),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      role: lambdaRole,
      environment: {
        OPENF1_SECRET_NAME: openF1Secret.secretName,
        OPENF1_BASE_URL: 'https://api.openf1.org/v1',
      },
    });

    // --- Lambda: GetHistoricalPerformance (Jolpica API) ---
    const historicalLambda = new lambda.Function(this, 'GetHistoricalPerformanceFn', {
      functionName: 'f1-agent-get-historical-performance',
      runtime: lambda.Runtime.NODEJS_20_X,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/get-historical-performance')),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      role: lambdaRole,
      environment: {
        JOLPICA_BASE_URL: 'https://api.jolpi.ca/ergast/f1',
      },
    });

    // --- Lambda: GetFantasyData (F1 Fantasy API + User Team API) ---
    const fantasyDataLambda = new lambda.Function(this, 'GetFantasyDataFn', {
      functionName: 'f1-agent-get-fantasy-data',
      runtime: lambda.Runtime.NODEJS_20_X,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/get-fantasy-data')),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      role: lambdaRole,
      environment: {
        F1_FANTASY_SECRET_NAME: f1FantasySecret.secretName,
        F1_FANTASY_BASE_URL: 'https://fantasy-api.formula1.com/partner_games/f1',
        USER_TEAM_API_URL: 'YOUR_CUSTOM_API_URL_HERE',  // Replace with your API
      },
    });

    // --- Lambda: GetExternalIntelligence (Weather, Odds, Reddit, News) ---
    const externalIntelLambda = new lambda.Function(this, 'GetExternalIntelligenceFn', {
      functionName: 'f1-agent-get-external-intelligence',
      runtime: lambda.Runtime.NODEJS_20_X,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/get-external-intelligence')),
      timeout: cdk.Duration.seconds(45),  // Longer timeout for multiple API calls
      memorySize: 512,
      role: lambdaRole,
      environment: {
        WEATHER_SECRET_NAME: weatherApiSecret.secretName,
        ODDS_SECRET_NAME: oddsApiSecret.secretName,
        REDDIT_SECRET_NAME: redditSecret.secretName,
      },
    });

    // --- Lambda: RunPredictionEngine (ML Model + Optimizer) ---
    const predictionLambda = new lambda.Function(this, 'RunPredictionEngineFn', {
      functionName: 'f1-agent-run-prediction-engine',
      runtime: lambda.Runtime.PYTHON_3_12,  // Python for ML libraries
      handler: 'handler.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/run-prediction-engine')),
      timeout: cdk.Duration.seconds(120),  // ML inference can be slow
      memorySize: 1024,  // More memory for model inference
      role: lambdaRole,
      environment: {
        MODEL_BUCKET: knowledgeBaseBucket.bucketName,
        MODEL_KEY: 'models/f1_fantasy_predictor.pkl',
      },
    });

    // --- Lambda: ValidateAndSubmit (Your validation engine) ---
    const validateLambda = new lambda.Function(this, 'ValidateAndSubmitFn', {
      functionName: 'f1-agent-validate-and-submit',
      runtime: lambda.Runtime.NODEJS_20_X,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/validate-and-submit')),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      role: lambdaRole,
      environment: {
        VALIDATION_ENGINE_URL: 'YOUR_VALIDATION_ENGINE_URL_HERE',  // Replace
      },
    });

    // Grant Bedrock permission to invoke all Lambdas
    const allLambdas = [
      liveSessionLambda,
      historicalLambda,
      fantasyDataLambda,
      externalIntelLambda,
      predictionLambda,
      validateLambda,
    ];

    allLambdas.forEach(fn => {
      fn.addPermission('BedrockInvoke', {
        principal: new iam.ServicePrincipal('bedrock.amazonaws.com'),
        action: 'lambda:InvokeFunction',
        sourceArn: `arn:aws:bedrock:${this.region}:${this.account}:agent/*`,
      });
    });

    // ═══════════════════════════════════════════════════════════
    // 5. OUTPUTS — Values you'll need for Bedrock console setup
    // ═══════════════════════════════════════════════════════════
    //
    // NOTE: As of mid-2025, Bedrock Agent L2 constructs in CDK
    // are still evolving. You may need to create the Agent and
    // Action Groups in the Bedrock console, referencing these
    // Lambda ARNs and S3 schema locations.
    //
    // Alternatively, use the bedrock-agents-cdk npm package:
    //   npm install bedrock-agents-cdk
    // ═══════════════════════════════════════════════════════════

    new cdk.CfnOutput(this, 'AgentRoleArn', {
      value: agentRole.roleArn,
      description: 'IAM Role ARN for the Bedrock Agent',
    });

    new cdk.CfnOutput(this, 'SchemaBucketName', {
      value: schemaBucket.bucketName,
      description: 'S3 bucket containing OpenAPI schemas',
    });

    new cdk.CfnOutput(this, 'KnowledgeBaseBucketName', {
      value: knowledgeBaseBucket.bucketName,
      description: 'S3 bucket for Knowledge Base documents',
    });

    const lambdaOutputs = {
      'LiveSessionLambdaArn': liveSessionLambda.functionArn,
      'HistoricalLambdaArn': historicalLambda.functionArn,
      'FantasyDataLambdaArn': fantasyDataLambda.functionArn,
      'ExternalIntelLambdaArn': externalIntelLambda.functionArn,
      'PredictionLambdaArn': predictionLambda.functionArn,
      'ValidateLambdaArn': validateLambda.functionArn,
    };

    Object.entries(lambdaOutputs).forEach(([name, arn]) => {
      new cdk.CfnOutput(this, name, { value: arn });
    });
  }
}

// ═══════════════════════════════════════════════════════════
// App entry point
// ═══════════════════════════════════════════════════════════
const app = new cdk.App();
new F1FantasyBedrockAgentStack(app, 'F1FantasyBedrockAgentStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
});
