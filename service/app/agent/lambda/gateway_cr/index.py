"""CDK Custom Resource handler — creates/deletes AgentCore Gateway + Target."""
import json
import os
import boto3


def handler(event, context):
    request_type = event['RequestType']
    props = event['ResourceProperties']

    region = os.environ.get('AWS_REGION', 'us-east-1')
    client = boto3.client('bedrock-agentcore-control', region_name=region)
    ssm = boto3.client('ssm', region_name=region)

    if request_type in ('Create', 'Update'):
        # Create gateway, or reuse existing one with the same name
        try:
            gw_resp = client.create_gateway(
                name=props['GatewayName'],
                roleArn=props['RoleArn'],
                protocolType='MCP',
                authorizerType='CUSTOM_JWT',
                authorizerConfiguration={
                    'customJWTAuthorizer': {
                        'discoveryUrl': props['DiscoveryUrl'],
                        'allowedClients': [props['AllowedClient']],
                    }
                },
            )
            gateway_id = gw_resp['gatewayId']
            gateway_url = gw_resp.get('gatewayUrl', '')
        except client.exceptions.ConflictException:
            # Gateway already exists — look it up by name
            gateways = client.list_gateways().get('items', [])
            existing = next((g for g in gateways if g['name'] == props['GatewayName']), None)
            if not existing:
                raise RuntimeError(f"Gateway {props['GatewayName']} exists but could not be found in list")
            gateway_id = existing['gatewayId']
            gateway_url = existing.get('gatewayUrl', '')

        # Create gateway target (skip if already exists)
        existing_targets = client.list_gateway_targets(gatewayIdentifier=gateway_id).get('items', [])
        if not existing_targets:
            client.create_gateway_target(
                gatewayIdentifier=gateway_id,
                name='gridwise-tools-target',
                targetConfiguration={
                    'mcp': {
                        'lambda': {
                            'lambdaArn': props['LambdaArn'],
                            'toolSchema': {
                                'inlinePayload': json.loads(props['InlineTools']),
                            },
                        }
                    }
                },
                credentialProviderConfigurations=[{
                    'credentialProviderType': 'GATEWAY_IAM_ROLE',
                }],
            )

        ssm.put_parameter(
            Name='/gridwise/agentcore/gateway-id',
            Value=gateway_id,
            Type='String',
            Overwrite=True,
        )
        ssm.put_parameter(
            Name='/gridwise/agentcore/gateway-endpoint',
            Value=gateway_url,
            Type='String',
            Overwrite=True,
        )

        return {
            'PhysicalResourceId': gateway_id,
            'Data': {'GatewayId': gateway_id, 'GatewayUrl': gateway_url},
        }

    elif request_type == 'Delete':
        gateway_id = event.get('PhysicalResourceId', '')
        if gateway_id:
            try:
                # Delete targets first
                targets = client.list_gateway_targets(gatewayIdentifier=gateway_id).get('items', [])
                for t in targets:
                    client.delete_gateway_target(
                        gatewayIdentifier=gateway_id,
                        targetId=t['targetId'],
                    )
                client.delete_gateway(gatewayIdentifier=gateway_id)
            except Exception as e:
                print(f'Delete error (ignoring): {e}')
        return {'PhysicalResourceId': gateway_id}
