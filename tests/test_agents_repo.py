import os
import tempfile

from src.core.db import init_db
from src.repos.users_repo import create_user
from src.repos.agents_repo import (
    create_agent,
    get_agent,
    list_agents_by_user,
    update_agent,
    delete_agent,
)


def setup_temp_db():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    os.environ['APP_DB_PATH'] = tmp.name
    init_db()
    return tmp.name


def test_create_and_list_agents_by_user():
    setup_temp_db()
    uid1 = create_user('a@a.com', 'pw123456', 'USER', True)
    uid2 = create_user('b@a.com', 'pw123456', 'USER', True)

    a1 = create_agent(uid1, 'Agent A', 'Desc A', 'gpt-4o-mini', 256, 0.7, 'Prompt A')
    a2 = create_agent(uid1, 'Agent B', None, 'gpt-4o-mini', 512, 0.2, 'Prompt B')
    a3 = create_agent(uid2, 'Agent C', 'Desc C', 'gpt-4o-mini', 128, 1.0, 'Prompt C')

    agents1 = list_agents_by_user(uid1)
    agents2 = list_agents_by_user(uid2)

    assert {a['id'] for a in agents1} == {a1, a2}
    assert {a['id'] for a in agents2} == {a3}

    by_id = {a['id']: a for a in agents1 + agents2}
    assert by_id[a1]['max_tokens'] == 256
    assert by_id[a2]['max_tokens'] == 512
    assert by_id[a3]['max_tokens'] == 128
    assert by_id[a1]['description'] == 'Desc A'
    assert by_id[a2]['description'] is None
    assert by_id[a3]['description'] == 'Desc C'
    assert by_id[a1]['system_prompt'] == 'Prompt A'


def test_update_and_delete_agent_user_isolation():
    setup_temp_db()
    uid1 = create_user('x@a.com', 'pw123456', 'USER', True)
    uid2 = create_user('y@a.com', 'pw123456', 'USER', True)

    agent_id = create_agent(uid1, 'Agent A', 'Desc A', 'gpt-4o-mini', 256, 0.7, 'Prompt A')

    update_agent(agent_id, uid2, name='Hacker')
    a = get_agent(agent_id, uid1)
    assert a['name'] == 'Agent A'

    update_agent(agent_id, uid1, name='Agent Updated', description='Desc B', max_tokens=333, system_prompt='Prompt B')
    a2 = get_agent(agent_id, uid1)
    assert a2['name'] == 'Agent Updated'
    assert a2['max_tokens'] == 333
    assert a2['description'] == 'Desc B'
    assert a2['system_prompt'] == 'Prompt B'

    delete_agent(agent_id, uid2)
    assert get_agent(agent_id, uid1) is not None

    delete_agent(agent_id, uid1)
    assert get_agent(agent_id, uid1) is None
