import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as ecr from 'aws-cdk-lib/aws-ecr';

export class GridwiseFoundationStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // -------------------------------------------------------------------------
    // Cognito User Pool - email + password auth
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
        'tier': new cognito.StringAttribute({ mutable: true }),
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

    new cdk.CfnOutput(this, 'UserPoolId', {
      value: userPool.userPoolId,
      exportName: 'UserPoolId',
    });
    new cdk.CfnOutput(this, 'UserPoolClientId', {
      value: userPoolClient.userPoolClientId,
      exportName: 'UserPoolClientId',
    });

    new ssm.StringParameter(this, 'UserPoolIdParam', {
      parameterName: '/gridwise/cognito/user-pool-id',
      stringValue: userPool.userPoolId,
    });
    new ssm.StringParameter(this, 'UserPoolClientIdParam', {
      parameterName: '/gridwise/cognito/app-client-id',
      stringValue: userPoolClient.userPoolClientId,
    });

    // -------------------------------------------------------------------------
    // Secrets Manager - placeholder values only, never real keys
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
    // IAM Role - FastAPI service (EC2 / ECS / App Runner)
    // -------------------------------------------------------------------------
    const fastApiRole = new iam.Role(this, 'GridwiseFastApiRole', {
      roleName: 'gridwise-fastapi-service-role',
      assumedBy: new iam.CompositePrincipal(
        new iam.ServicePrincipal('ec2.amazonaws.com'),
        new iam.ServicePrincipal('lambda.amazonaws.com'),
        new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
        new iam.ServicePrincipal('tasks.apprunner.amazonaws.com'),
      ),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
      description: 'IAM role for GridWise FastAPI service',
    });

    fastApiRole.addToPolicy(new iam.PolicyStatement({
      actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
      resources: [
        `arn:aws:bedrock:*::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0`,
        `arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-5-20250929-v1:0`,
        `arn:aws:bedrock:${this.region}:${this.account}:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0`,
        `arn:aws:bedrock:${this.region}:${this.account}:inference-profile/us.anthropic.claude-sonnet-4-5-20250929-v1:0`,
      ],
    }));

    fastApiRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        'bedrock-agentcore:InvokeGateway',
        'bedrock-agentcore:GetGateway',
        'bedrock-agentcore:ListGateways',
        'bedrock-agentcore:ListGatewayTargets',
        'bedrock-agentcore:CreateAgentRuntime',
        'bedrock-agentcore:GetAgentRuntime',
        'bedrock-agentcore:ListAgentRuntimes',
        'bedrock-agentcore:CreateAgentRuntimeEndpoint',
        'bedrock-agentcore:GetAgentRuntimeEndpoint',
        'bedrock-agentcore:DeleteAgentRuntime',
        'bedrock-agentcore:DeleteAgentRuntimeEndpoint',
        'bedrock-agentcore:CreateWorkloadIdentity',
        'bedrock-agentcore:GetWorkloadIdentity',
      ],
      resources: ['*'],
    }));

    fastApiRole.addToPolicy(new iam.PolicyStatement({
      actions: ['iam:CreateServiceLinkedRole', 'iam:PassRole'],
      resources: ['*'],
    }));

    // Updated memory permissions (task 0.5)
    fastApiRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        'bedrock-agentcore:CreateEvent',
        'bedrock-agentcore:ListEvents',
        'bedrock-agentcore:GetMemory',
        'bedrock-agentcore:RetrieveMemories',
        'bedrock-agentcore:GetLastKTurns',
      ],
      resources: [`arn:aws:bedrock-agentcore:*:${this.account}:memory/*`],
    }));

    fastApiRole.addToPolicy(new iam.PolicyStatement({
      actions: ['secretsmanager:GetSecretValue'],
      resources: [`arn:aws:secretsmanager:*:${this.account}:secret:gridwise/*`],
    }));

    fastApiRole.addToPolicy(new iam.PolicyStatement({
      actions: ['ssm:GetParameter', 'ssm:GetParameters'],
      resources: [`arn:aws:ssm:*:${this.account}:parameter/gridwise/*`],
    }));

    new cdk.CfnOutput(this, 'FastApiRoleArn', {
      value: fastApiRole.roleArn,
      exportName: 'FastApiRoleArn',
    });
    new ssm.StringParameter(this, 'FastApiRoleArnParam', {
      parameterName: '/gridwise/iam/fastapi-role-arn',
      stringValue: fastApiRole.roleArn,
    });

    // -------------------------------------------------------------------------
    // IAM Role - AgentCore Gateway service role
    // -------------------------------------------------------------------------
    const gatewayServiceRole = new iam.Role(this, 'GridwiseGatewayServiceRole', {
      roleName: 'gridwise-gateway-service-role',
      assumedBy: new iam.ServicePrincipal('bedrock-agentcore.amazonaws.com', {
        conditions: {
          StringEquals: { 'aws:SourceAccount': this.account },
        },
      }),
      description: 'AgentCore Gateway service role - invokes the tools-proxy Lambda on behalf of agents',
    });

    new cdk.CfnOutput(this, 'GatewayServiceRoleArn', {
      value: gatewayServiceRole.roleArn,
      exportName: 'GatewayServiceRoleArn',
      description: 'Gateway service role - tighten the trust Condition to the gateway ARN after first deploy',
    });

    // -------------------------------------------------------------------------
    // IAM Role - AgentCore Runtime role (task 0.2)
    // -------------------------------------------------------------------------
    const agentRuntimeRole = new iam.Role(this, 'GridwiseAgentRuntimeRole', {
      roleName: 'gridwise-agent-runtime-role',
      assumedBy: new iam.ServicePrincipal('bedrock-agentcore.amazonaws.com'),
      description: 'IAM role assumed by the AgentCore Runtime container',
    });

    agentRuntimeRole.addToPolicy(new iam.PolicyStatement({
      actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
      resources: [
        `arn:aws:bedrock:*::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0`,
        `arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-5-20250929-v1:0`,
        `arn:aws:bedrock:${this.region}:${this.account}:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0`,
        `arn:aws:bedrock:${this.region}:${this.account}:inference-profile/us.anthropic.claude-sonnet-4-5-20250929-v1:0`,
      ],
    }));

    agentRuntimeRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        'bedrock-agentcore:CreateEvent',
        'bedrock-agentcore:ListEvents',
        'bedrock-agentcore:GetMemory',
        'bedrock-agentcore:RetrieveMemories',
        'bedrock-agentcore:GetLastKTurns',
      ],
      resources: [`arn:aws:bedrock-agentcore:*:${this.account}:memory/*`],
    }));

    agentRuntimeRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        'bedrock-agentcore:InvokeGateway',
        'bedrock-agentcore:GetGateway',
        'bedrock-agentcore:ListGatewayTargets',
      ],
      resources: ['*'],
    }));

    agentRuntimeRole.addToPolicy(new iam.PolicyStatement({
      actions: ['secretsmanager:GetSecretValue'],
      resources: [`arn:aws:secretsmanager:*:${this.account}:secret:gridwise/*`],
    }));

    agentRuntimeRole.addToPolicy(new iam.PolicyStatement({
      actions: ['ssm:GetParameter', 'ssm:GetParameters'],
      resources: [`arn:aws:ssm:*:${this.account}:parameter/gridwise/*`],
    }));

    agentRuntimeRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        'ecr:GetAuthorizationToken',
        'ecr:BatchGetImage',
        'ecr:GetDownloadUrlForLayer',
        'ecr:BatchCheckLayerAvailability',
      ],
      resources: ['*'],
    }));

    new cdk.CfnOutput(this, 'AgentRuntimeRoleArn', {
      value: agentRuntimeRole.roleArn,
      exportName: 'AgentRuntimeRoleArn',
    });
    new ssm.StringParameter(this, 'AgentRuntimeRoleArnParam', {
      parameterName: '/gridwise/iam/agent-runtime-role-arn',
      stringValue: agentRuntimeRole.roleArn,
    });

    // -------------------------------------------------------------------------
    // IAM Role - App Runner ECR access role (pull images from ECR)
    // -------------------------------------------------------------------------
    const appRunnerEcrRole = new iam.Role(this, 'GridwiseAppRunnerEcrRole', {
      roleName: 'gridwise-apprunner-ecr-role',
      assumedBy: new iam.ServicePrincipal('build.apprunner.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSAppRunnerServicePolicyForECRAccess'),
      ],
      description: 'Allows App Runner to pull images from ECR',
    });

    new cdk.CfnOutput(this, 'AppRunnerEcrRoleArn', {
      value: appRunnerEcrRole.roleArn,
      exportName: 'AppRunnerEcrRoleArn',
    });

    // -------------------------------------------------------------------------
    // ECR Repositories (task 3.3) - created here so images can be pushed before
    // GridwiseAgentStack deploys App Runner
    // -------------------------------------------------------------------------
    const fastApiRepo = new ecr.Repository(this, 'GridwiseFastApiRepo', {
      repositoryName: 'gridwise-fastapi',
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      lifecycleRules: [{ maxImageCount: 5 }],
    });

    const agentRuntimeRepo = new ecr.Repository(this, 'GridwiseAgentRuntimeRepo', {
      repositoryName: 'gridwise-agent-runtime',
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      lifecycleRules: [{ maxImageCount: 5 }],
    });

    new cdk.CfnOutput(this, 'FastApiRepoUri', {
      value: fastApiRepo.repositoryUri,
      exportName: 'FastApiRepoUri',
    });
    new cdk.CfnOutput(this, 'AgentRuntimeRepoUri', {
      value: agentRuntimeRepo.repositoryUri,
      exportName: 'AgentRuntimeRepoUri',
    });
  }
}
