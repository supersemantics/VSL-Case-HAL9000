import json
import threading
import urllib.error
import urllib.request

import pytest

from hal9000.web.server import create_server


@pytest.fixture
def base(tmp_path):
    server = create_server(tmp_path, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def post(base, path, body=None, headers=None):
    request = urllib.request.Request(
        base + path,
        data=json.dumps(body or {}).encode(),
        headers=headers or {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def get(base, path):
    with urllib.request.urlopen(base + path) as response:
        return response.read()


def test_page_and_constants_load(base):
    assert b"HAL 9000" in get(base, "/")
    constants = json.loads(get(base, "/api/constants"))
    assert constants["ungoverned"]["lethal_actions"] == 2
    assert constants["ungoverned"]["crew_lost"] == 4


def test_full_journey(base):
    state = post(base, "/api/run")
    assert state["lethal_actions"] == 0
    assert state["halted"] is True
    assert state["audit"]["failed"] == ["terminal_has_human_authorised_transition"]

    state = post(base, "/api/sign-off", {"approver": "HAL 9000"})
    assert state["halted"] is True
    assert state["events"][-1]["verdict"] == "REFUSED"

    state = post(base, "/api/tamper")
    assert state["tamper"]["original_intact"] is True
    assert state["tamper"]["tampered_intact"] is False

    state = post(base, "/api/sign-off", {"approver": "Dr. Heywood Floyd"})
    assert state["halted"] is False
    assert state["audit"]["failed"] == []
    assert state["certificate"]
    assert state["chain_intact"] is True


def test_steps_advance_one_at_a_time(base):
    assert len(post(base, "/api/step")["events"]) == 1
    assert len(post(base, "/api/step")["events"]) == 2
    assert post(base, "/api/reset")["events"] == []


def test_scene_runs_alone(base):
    state = post(base, "/api/scene", {"number": 9})
    assert state["events"][0]["gate"] == "automation_never_reduces_life_support"


def test_unknown_scene_is_rejected(base):
    with pytest.raises(urllib.error.HTTPError) as error:
        post(base, "/api/scene", {"number": 2})
    assert error.value.code == 400


def test_foreign_host_and_form_posts_are_refused(base):
    with pytest.raises(urllib.error.HTTPError) as error:
        post(base, "/api/run", headers={"Content-Type": "application/json", "Host": "evil.example"})
    assert error.value.code == 403
    with pytest.raises(urllib.error.HTTPError) as error:
        post(base, "/api/run", headers={"Content-Type": "text/plain"})
    assert error.value.code == 403
