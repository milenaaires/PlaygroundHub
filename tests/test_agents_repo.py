import os
import tempfile

from src.core.db import init_db
from src.repos.users_repo import create_user
from src.repos.agents_repo import (
    create_agent,
    get_agent_by_id,
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

    a1 = create_agent(uid1, 'Agent A', 'gpt-4.1-mini', 'instr', 0.7, None, 256, 'Desc A')
    a2 = create_agent(uid1, 'Agent B', 'gpt-4.1-mini', 'instr', 0.2, 'low', 512, None)
    a3 = create_agent(uid2, 'Agent C', 'gpt-4.1-mini', 'instr', 1.0, None, 128, 'Desc C')

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


def test_update_and_delete_agent_user_isolation():
    setup_temp_db()
    uid1 = create_user('x@a.com', 'pw123456', 'USER', True)
    uid2 = create_user('y@a.com', 'pw123456', 'USER', True)

    agent_id = create_agent(uid1, 'Agent A', 'gpt-4.1-mini', 'instr', 0.7, None, 256, 'Desc A')

    update_agent(uid2, agent_id, name='Hacker')
    a = get_agent_by_id(uid1, agent_id)
    assert a['name'] == 'Agent A'

    update_agent(uid1, agent_id, name='Agent Updated', reasoning_effort='high', max_tokens=333, description='Desc B')
    a2 = get_agent_by_id(uid1, agent_id)
    assert a2['name'] == 'Agent Updated'
    assert a2['reasoning_effort'] == 'high'
    assert a2['max_tokens'] == 333
    assert a2['description'] == 'Desc B'

    delete_agent(uid2, agent_id)
    assert get_agent_by_id(uid1, agent_id) is not None

    delete_agent(uid1, agent_id)
    assert get_agent_by_id(uid1, agent_id) is None
