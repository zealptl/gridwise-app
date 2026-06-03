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
  }
}
