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

SESSION_STORE_NAME = 'gridwise_session_store'
MEMORY_NAME = 'gridwise_memory'


def get_ssm_param(name: str) -> str | None:
    try:
        return ssm.get_parameter(Name=name)['Parameter']['Value']
    except ssm.exceptions.ParameterNotFound:
        return None
    except Exception:
        return None


def find_existing(client, name: str) -> str | None:
    """Return memory ID if a resource with this name prefix already exists."""
    for existing in client.list_memories(max_results=100):
        existing_id = existing.get('id', '')
        if existing_id.startswith(name + '-'):
            return existing_id
    return None


def create_memory_resources():
    from bedrock_agentcore.memory import MemoryClient
    from bedrock_agentcore.memory.constants import StrategyType

    client = MemoryClient(region_name=AWS_REGION)

    # Session store — no extraction strategies, 30-day expiry
    session_id = get_ssm_param('/gridwise/agentcore/session-memory-id')
    if not session_id:
        session_id = find_existing(client, SESSION_STORE_NAME)
    if not session_id:
        print('Creating session store memory resource...')
        memory = client.create_memory_and_wait(
            name=SESSION_STORE_NAME,
            description='Durable event log for ADK session state',
            strategies=[],
            event_expiry_days=30,
        )
        session_id = memory['id']
        print(f'Session store created: {session_id}')
    else:
        print(f'Session store already exists: {session_id}')
    ssm.put_parameter(Name='/gridwise/agentcore/session-memory-id', Value=session_id, Type='String', Overwrite=True)

    # Long-term memory — USER_PREFERENCE + SEMANTIC, 90-day expiry
    ltm_id = get_ssm_param('/gridwise/agentcore/memory-id')
    if not ltm_id:
        ltm_id = find_existing(client, MEMORY_NAME)
    if not ltm_id:
        print('Creating long-term memory resource...')
        memory = client.create_memory_and_wait(
            name=MEMORY_NAME,
            description='Long-term memory with USER_PREFERENCE + SEMANTIC extraction',
            strategies=[
                {
                    StrategyType.USER_PREFERENCE.value: {
                        'name': 'GridwiseUserPreferences',
                        'description': 'Captures user fantasy preferences and behaviour',
                        'namespaces': ['/strategies/{memoryStrategyId}/actors/{actorId}/'],
                    }
                },
                {
                    StrategyType.SEMANTIC.value: {
                        'name': 'GridwiseSemantic',
                        'description': 'Stores facts from conversations',
                        'namespaces': ['/strategies/{memoryStrategyId}/actors/{actorId}/'],
                    }
                },
            ],
            event_expiry_days=90,
        )
        ltm_id = memory['id']
        print(f'Long-term memory created: {ltm_id}')
    else:
        print(f'Long-term memory already exists: {ltm_id}')
    ssm.put_parameter(Name='/gridwise/agentcore/memory-id', Value=ltm_id, Type='String', Overwrite=True)

    print(f'\nSSM params written:')
    print(f'  /gridwise/agentcore/session-memory-id = {session_id}')
    print(f'  /gridwise/agentcore/memory-id = {ltm_id}')


if __name__ == '__main__':
    create_memory_resources()
