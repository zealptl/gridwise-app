#!/usr/bin/env python3
"""
Create AgentCore Memory resources for GridWise.
Idempotent — checks SSM before creating.
Run: python scripts/create_memory_resources.py
"""
import os
import boto3

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
ssm = boto3.client('ssm', region_name=AWS_REGION)


def get_ssm_param(name: str) -> str | None:
    try:
        return ssm.get_parameter(Name=name)['Parameter']['Value']
    except ssm.exceptions.ParameterNotFound:
        return None
    except Exception:
        return None


def create_memory_resources():
    from bedrock_agentcore.memory import MemoryClient
    client = MemoryClient(region_name=AWS_REGION)

    # Session store
    session_id = get_ssm_param('/gridwise/agentcore/session-memory-id')
    if not session_id:
        print('Creating session store memory resource...')
        resp = client.create_memory(
            name='gridwise-session-store',
            description='Durable event log for ADK session state',
            memoryStrategies=[],
            eventExpiryDuration=30,  # days
        )
        session_id = resp['memoryId']
        ssm.put_parameter(Name='/gridwise/agentcore/session-memory-id', Value=session_id, Type='String', Overwrite=True)
        print(f'Session store created: {session_id}')
    else:
        print(f'Session store already exists: {session_id}')

    # Long-term memory store
    ltm_id = get_ssm_param('/gridwise/agentcore/memory-id')
    if not ltm_id:
        print('Creating long-term memory resource...')
        resp = client.create_memory(
            name='gridwise-memory',
            description='Long-term memory with USER_PREFERENCE + SEMANTIC extraction',
            memoryStrategies=[
                {'type': 'USER_PREFERENCE'},
                {'type': 'SEMANTIC'},
            ],
            eventExpiryDuration=90,  # days
        )
        ltm_id = resp['memoryId']
        ssm.put_parameter(Name='/gridwise/agentcore/memory-id', Value=ltm_id, Type='String', Overwrite=True)
        print(f'Long-term memory created: {ltm_id}')
    else:
        print(f'Long-term memory already exists: {ltm_id}')

    print(f'\nSSM params written:')
    print(f'  /gridwise/agentcore/session-memory-id = {session_id}')
    print(f'  /gridwise/agentcore/memory-id = {ltm_id}')


if __name__ == '__main__':
    create_memory_resources()
