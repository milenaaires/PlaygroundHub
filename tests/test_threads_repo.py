import os
import tempfile

from src.core.db import init_db
from src.repos.users_repo import create_user
from src.repos.agents_repo import create_agent
from src.repos.threads_repo import (
    create_thread,
    get_thread,
    get_thread_by_agent,
    update_previous_response_id,
)


def setup_temp_db():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    os.environ['APP_DB_PATH'] = tmp.name
    init_db()
    return tmp.name


def test_create_thread_and_update_previous_response():
    setup_temp_db()
    uid = create_user('t@a.com', 'pw123456', 'USER', True)
    agent_id = create_agent(uid, 'Agent A', 'Desc A', 'gpt-4o-mini', 256, 0.7, 'Prompt A')

    thread_id = create_thread(uid, agent_id)
    t1 = get_thread(uid, thread_id)
    assert t1['previous_response_id'] is None

    update_previous_response_id(uid, thread_id, 'resp_123')
    t2 = get_thread(uid, thread_id)
    assert t2['previous_response_id'] == 'resp_123'

    t3 = get_thread_by_agent(uid, agent_id)
    assert t3['thread_id'] == thread_id


def test_thread_user_isolation():
    setup_temp_db()
    uid1 = create_user('u1@a.com', 'pw123456', 'USER', True)
    uid2 = create_user('u2@a.com', 'pw123456', 'USER', True)
    agent_id = create_agent(uid1, 'Agent A', 'Desc A', 'gpt-4o-mini', 256, 0.7, 'Prompt A')

    thread_id = create_thread(uid1, agent_id)

    assert get_thread(uid2, thread_id) is None

    update_previous_response_id(uid2, thread_id, 'resp_x')
    t = get_thread(uid1, thread_id)
    assert t['previous_response_id'] is None
