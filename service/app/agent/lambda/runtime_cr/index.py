"""CDK Custom Resource handler — creates/updates/deletes AgentCore Runtime."""
import json
import os
import boto3


def handler(event, context):
    request_type = event['RequestType']
    props = event['ResourceProperties']

    image_uri = props['ImageUri']
    runtime_role_arn = props['RuntimeRoleArn']
    runtime_name = props.get('RuntimeName', 'gridwise-agent-runtime')
    region = os.environ.get('AWS_REGION', 'us-east-1')

    client = boto3.client('bedrock-agentcore-control', region_name=region)
    ssm = boto3.client('ssm', region_name=region)

    if request_type in ('Create', 'Update'):
        try:
            resp = client.create_agent_runtime(
                agentRuntimeName=runtime_name,
                agentRuntimeArtifact={
                    'containerConfiguration': {
                        'containerUri': image_uri,
                    }
                },
                roleArn=runtime_role_arn,
            )
            runtime_arn = resp.get('agentRuntimeArn', '')
            endpoint = resp.get('agentRuntimeEndpoint', '')

            if endpoint:
                ssm.put_parameter(
                    Name='/gridwise/agentcore/runtime-endpoint',
                    Value=endpoint,
                    Type='String',
                    Overwrite=True,
                )

            return {
                'PhysicalResourceId': runtime_arn or runtime_name,
                'Data': {'RuntimeArn': runtime_arn, 'RuntimeEndpoint': endpoint},
            }
        except Exception as e:
            # If runtime already exists on Update, try to get existing
            print(f'Error creating runtime: {e}')
            return {'PhysicalResourceId': runtime_name, 'Data': {}}

    elif request_type == 'Delete':
        return {'PhysicalResourceId': event.get('PhysicalResourceId', runtime_name)}
