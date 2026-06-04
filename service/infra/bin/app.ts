#!/usr/bin/env node
import 'source-map-support/register'
import * as cdk from 'aws-cdk-lib'
import { GridwiseFoundationStack } from '../gridwise-foundation-stack'
import { GridwiseAgentStack } from '../gridwise-agent-stack'

const app = new cdk.App()

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION,
}

const foundation = new GridwiseFoundationStack(app, 'GridwiseFoundationStack', { env })

const agent = new GridwiseAgentStack(app, 'GridwiseAgentStack', { env })
agent.addDependency(foundation)
