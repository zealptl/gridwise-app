"""CDK Custom Resource handler — creates/updates/deletes AgentCore Runtime."""
import json
import os
import boto3


def handler(event, context):
    request_type = event['RequestType']
    props = event['ResourceProperties']

    image_uri = props['ImageUri']
    runtime_role_arn = props['RuntimeRoleArn']
    runtime_name = props.get('RuntimeName', 'gridwise_agent_runtime')
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
                networkConfiguration={
                    'networkMode': 'PUBLIC',
                },
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
            if runtime_arn:
                ssm.put_parameter(
                    Name='/gridwise/agentcore/runtime-arn',
                    Value=runtime_arn,
                    Type='String',
                    Overwrite=True,
                )

            return {
                'PhysicalResourceId': runtime_arn or runtime_name,
                'Data': {'RuntimeArn': runtime_arn, 'RuntimeEndpoint': endpoint},
            }
        except client.exceptions.ConflictException:
            # Runtime already exists — look up its ARN
            existing = client.list_agent_runtimes()
            runtime = next(
                (r for r in existing.get('agentRuntimes', []) if r.get('agentRuntimeName') == runtime_name),
                None,
            )
            runtime_arn = runtime['agentRuntimeArn'] if runtime else runtime_name
            endpoint = runtime.get('agentRuntimeEndpoint', '') if runtime else ''
            if endpoint:
                ssm.put_parameter(
                    Name='/gridwise/agentcore/runtime-endpoint',
                    Value=endpoint,
                    Type='String',
                    Overwrite=True,
                )
            if runtime_arn:
                ssm.put_parameter(
                    Name='/gridwise/agentcore/runtime-arn',
                    Value=runtime_arn,
                    Type='String',
                    Overwrite=True,
                )
            return {
                'PhysicalResourceId': runtime_arn,
                'Data': {'RuntimeArn': runtime_arn, 'RuntimeEndpoint': endpoint},
            }
        except Exception as e:
            print(f'Error creating runtime: {e}')
            raise

    elif request_type == 'Delete':
        return {'PhysicalResourceId': event.get('PhysicalResourceId', runtime_name)}
