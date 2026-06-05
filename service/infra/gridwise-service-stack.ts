import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as ssm from 'aws-cdk-lib/aws-ssm'; // used for valueForStringParameter

export class GridwiseServiceStack extends cdk.Stack {
  /** Public ALB URL — imported by GridwiseAgentStack for the Lambda env var. */
  public readonly serviceUrl: string;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // -------------------------------------------------------------------------
    // Roles
    // -------------------------------------------------------------------------
    const fastApiRole = iam.Role.fromRoleArn(
      this, 'FastApiRole', cdk.Fn.importValue('FastApiRoleArn'),
    );

    // Separate execution role — ECS agent uses this to pull ECR images and
    // write CloudWatch logs. The task role (fastApiRole) handles app-level AWS calls.
    const executionRole = new iam.Role(this, 'EcsExecutionRole', {
      roleName: 'gridwise-ecs-execution-role',
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonECSTaskExecutionRolePolicy'),
      ],
    });
    // Allow execution role to read Secrets Manager secrets for container injection
    executionRole.addToPolicy(new iam.PolicyStatement({
      actions: ['secretsmanager:GetSecretValue'],
      resources: [`arn:aws:secretsmanager:*:${this.account}:secret:gridwise/*`],
    }));

    // -------------------------------------------------------------------------
    // Networking — default VPC, public subnets
    // -------------------------------------------------------------------------
    const vpc = ec2.Vpc.fromLookup(this, 'DefaultVpc', { isDefault: true });

    const albSg = new ec2.SecurityGroup(this, 'AlbSg', {
      vpc,
      description: 'gridwise ALB - allows inbound HTTP from internet',
    });
    albSg.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80), 'HTTP from internet');

    const taskSg = new ec2.SecurityGroup(this, 'TaskSg', {
      vpc,
      description: 'gridwise Fargate tasks - allows inbound from ALB only',
    });
    taskSg.addIngressRule(albSg, ec2.Port.tcp(8080), 'From ALB');

    // -------------------------------------------------------------------------
    // ECS cluster
    // -------------------------------------------------------------------------
    const cluster = new ecs.Cluster(this, 'GridwiseCluster', {
      clusterName: 'gridwise',
      vpc,
    });

    // -------------------------------------------------------------------------
    // Secrets + config resolved at deploy time
    // -------------------------------------------------------------------------
    const mongoSecret = secretsmanager.Secret.fromSecretNameV2(
      this, 'MongoSecret', 'gridwise/mongodb-atlas-uri',
    );

    const cognitoUserPoolId = ssm.StringParameter.valueForStringParameter(
      this, '/gridwise/cognito/user-pool-id',
    );
    const cognitoAppClientId = ssm.StringParameter.valueForStringParameter(
      this, '/gridwise/cognito/app-client-id',
    );

    // -------------------------------------------------------------------------
    // Task definition
    // -------------------------------------------------------------------------
    const taskDef = new ecs.FargateTaskDefinition(this, 'FastApiTaskDef', {
      family: 'gridwise-fastapi',
      cpu: 512,
      memoryLimitMiB: 1024,
      taskRole: fastApiRole,
      executionRole,
    });

    taskDef.addContainer('fastapi', {
      containerName: 'fastapi',
      image: ecs.ContainerImage.fromRegistry(
        `${this.account}.dkr.ecr.${this.region}.amazonaws.com/gridwise-fastapi:latest`,
      ),
      portMappings: [{ containerPort: 8080 }],
      environment: {
        AWS_REGION: this.region,
        COGNITO_USER_POOL_ID: cognitoUserPoolId,
        COGNITO_APP_CLIENT_ID: cognitoAppClientId,
        MONGODB_DB_NAME: 'gridwise_mvp',
        BACKEND_CORS_ORIGINS: JSON.stringify([
          'http://localhost:3000',
          'http://localhost:5173',
          'http://localhost:5174',
          'http://localhost:5175',
        ]),
      },
      secrets: {
        // ECS injects the Secrets Manager value as MONGODB_URL at container start
        MONGODB_URL: ecs.Secret.fromSecretsManager(mongoSecret),
      },
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'fastapi',
        logGroup: new logs.LogGroup(this, 'FastApiLogGroup', {
          logGroupName: '/gridwise/fastapi',
          retention: logs.RetentionDays.ONE_WEEK,
          removalPolicy: cdk.RemovalPolicy.DESTROY,
        }),
      }),
      // No container-level health check — python:3.12-slim has no curl.
      // ALB target group health check on /health is sufficient for service stability.
    });

    // -------------------------------------------------------------------------
    // ALB + Fargate service
    // -------------------------------------------------------------------------
    const alb = new elbv2.ApplicationLoadBalancer(this, 'Alb', {
      loadBalancerName: 'gridwise-fastapi',
      vpc,
      internetFacing: true,
      securityGroup: albSg,
    });

    const service = new ecs.FargateService(this, 'FastApiService', {
      serviceName: 'gridwise-fastapi',
      cluster,
      taskDefinition: taskDef,
      desiredCount: 1,
      assignPublicIp: true,
      securityGroups: [taskSg],
    });

    const listener = alb.addListener('HttpListener', { port: 80, open: true });
    listener.addTargets('FastApiTarget', {
      port: 8080,
      protocol: elbv2.ApplicationProtocol.HTTP,
      targets: [service],
      healthCheck: {
        path: '/health',
        interval: cdk.Duration.seconds(30),
        healthyHttpCodes: '200',
      },
      deregistrationDelay: cdk.Duration.seconds(15),
    });

    this.serviceUrl = `http://${alb.loadBalancerDnsName}`;

    // -------------------------------------------------------------------------
    // Outputs
    // -------------------------------------------------------------------------
    new cdk.CfnOutput(this, 'FastApiServiceUrl', {
      value: this.serviceUrl,
      exportName: 'FastApiServiceUrl',
      description: 'FastAPI ALB URL',
    });
  }
}
