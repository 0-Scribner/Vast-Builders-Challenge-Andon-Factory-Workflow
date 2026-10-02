"""/api/stack routes and the VssClient retrieval calls behind them, with no network."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["SCRIBNER_MOCK"] = "1"
os.environ["SCRIBNER_DATA_DIR"] = tempfile.mkdtemp(prefix="scribner-stack-")

import requests  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import config  # noqa: E402
import main  # noqa: E402
import stack_tools  # noqa: E402
from kits import CAMERA_ID, PAYOFF_QUERY  # noqa: E402
from vss_client import VssClient, VssError  # noqa: E402

# Per-run sentinels: any leak of the VSS host, JWT or password carries RUN.
RUN = uuid.uuid4().hex[:12]
HOST = f"vss-{RUN}.example"
BASE = f"https://{HOST}:8443"
TOKEN = f"jwt-{RUN}"
PASSWORD = f"pw-{RUN}"
USER = "team-user"
CONFIG_HOST = f"cfg-{RUN}.example"
CONFIG_URL = f"https://{CONFIG_HOST}"
CONFIG_PASSWORD = f"cfgpw-{RUN}"
LEAKS = (RUN, HOST, TOKEN, PASSWORD, CONFIG_HOST, CONFIG_PASSWORD, "://")

# name: (method, app path, query params, JSON body, VSS route)
ROUTES: Dict[str, Tuple[str, str, Any, Any, str]] = {
    "dashboard": ("GET", "/api/stack/dashboard", {"scope": "public"}, None, "/api/v1/dashboard/stats"),
    "suggestions": ("GET", "/api/stack/suggest", None, None, "/api/v1/suggestions"),
    "metadata_schema": ("GET", "/api/stack/metadata", None, None, "/api/v1/metadata/schema"),
    "metadata_values": (
        "GET",
        "/api/stack/metadata",
        {"field": "location", "prefix": "War", "limit": 5},
        None,
        "/api/v1/metadata/values",
    ),
    "agent_ask": ("POST", "/api/stack/ask", None, {"question": "Was anyone near the dock?"}, "/api/v1/agent/ask"),
}


def _response(status: int, payload: Any, url: str) -> requests.Response:
    r = requests.Response()
    r.status_code = status
    r._content = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
    r.headers["Content-Type"] = "application/json"
    r.encoding = "utf-8"
    r.url = url
    return r


def _http_error(status: int, url: str) -> requests.HTTPError:
    resp = requests.Response()
    resp.status_code = status
    resp.url = url
    return requests.HTTPError(f"{status} Error for url: {url}", response=resp)


class FakeSession:
    """Stands in for requests.Session: records every call and replays scripted replies."""

    def __init__(self, *replies: Any) -> None:
        self.replies = list(replies)
        self.calls: List[Dict[str, Any]] = []
        self.headers: Dict[str, str] = {}

    def _reply(self, method: str, url: str, kwargs: Dict[str, Any]) -> requests.Response:
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self.replies:
            raise AssertionError(f"unexpected {method} {url}")
        reply = self.replies.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        return reply

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        return self._reply("GET", url, kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        return self._reply("POST", url, kwargs)


def _real_client(*replies: Any) -> VssClient:
    client = VssClient(base=BASE, username=USER, password=PASSWORD)
    client.session = FakeSession(*replies)
    client._token = TOKEN
    client._token_at = time.time()
    return client


class FakeVss(VssClient):
    """VssClient whose five retrieval calls return or raise one scripted outcome."""

    def __init__(self, outcome: Any = None) -> None:
        super().__init__(base=BASE, username=USER, password=PASSWORD)
        self._token = TOKEN
        self._token_at = time.time()
        self.session = None
        self.outcome = outcome
        self.calls: List[Tuple[str, Dict[str, Any]]] = []

    def _answer(self, name: str, **kwargs: Any) -> Any:
        self.calls.append((name, kwargs))
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome

    def dashboard(self, scope: str = "all") -> Any:
        return self._answer("dashboard", scope=scope)

    def suggestions(self) -> Any:
        return self._answer("suggestions")

    def metadata_schema(self) -> Any:
        return self._answer("metadata_schema")

    def metadata_values(self, field: str, prefix: str = "", limit: int = 50) -> Any:
        return self._answer("metadata_values", field=field, prefix=prefix, limit=limit)

    def agent_ask(self, question: str, original_video: str = "", top_k: int = 10) -> Any:
        return self._answer(
            "agent_ask", question=question, original_video=original_video, top_k=top_k
        )


class VssClientRequestTests(unittest.TestCase):
    """Each call against the retrieval skills: route, method, params or body, Bearer JWT."""

    def _only_call(self, client: VssClient) -> Dict[str, Any]:
        calls = client.session.calls
        self.assertEqual(len(calls), 1, calls)
        return calls[0]

    def test_suggestions_is_a_bare_get_with_bearer(self) -> None:
        url = BASE + "/api/v1/suggestions"
        payload = {"prompts": ["forklift near a person"], "key_events": []}
        client = _real_client(_response(200, payload, url))
        self.assertEqual(client.suggestions(), payload)
        call = self._only_call(client)
        self.assertEqual((call["method"], call["url"]), ("GET", url))
        self.assertEqual(call["headers"], {"Authorization": "Bearer " + TOKEN})
        self.assertNotIn("params", call)
        self.assertNotIn("json", call)

    def test_suggestions_body_shape_is_passed_through(self) -> None:
        client = _real_client(_response(200, ["forklift near a person"], BASE + "/api/v1/suggestions"))
        self.assertEqual(client.suggestions(), ["forklift near a person"])

    def test_agent_ask_body_uses_skill_fields(self) -> None:
        url = BASE + "/api/v1/agent/ask"
        answer = {"answer": "No.", "tool_used": "search_hybrid", "evidence": []}
        client = _real_client(_response(200, answer, url), _response(200, answer, url))
        self.assertEqual(client.agent_ask("Was anyone near the dock?"), answer)
        client.agent_ask("Is the aisle clear?", original_video="s3://chunks/a.mp4", top_k=50)
        first, second = client.session.calls
        self.assertEqual((first["method"], first["url"]), ("POST", url))
        self.assertEqual(first["headers"], {"Authorization": "Bearer " + TOKEN})
        self.assertEqual(first["json"], {"question": "Was anyone near the dock?", "top_k": 10})
        self.assertEqual(
            second["json"],
            {"question": "Is the aisle clear?", "top_k": 50, "original_video": "s3://chunks/a.mp4"},
        )

    def test_agent_ask_top_k_outside_1_to_50_is_refused_before_http(self) -> None:
        client = _real_client()
        for top_k in (0, 51):
            with self.assertRaises(VssError) as ctx:
                client.agent_ask("Is the aisle clear?", top_k=top_k)
            self.assertIn(f"got {top_k}", str(ctx.exception))
        self.assertEqual(client.session.calls, [])

    def test_dashboard_scope_defaults_to_all(self) -> None:
        url = BASE + "/api/v1/dashboard/stats"
        stats = {"overview": {"unique_videos": 3}}
        client = _real_client(_response(200, stats, url), _response(200, stats, url))
        self.assertEqual(client.dashboard(), stats)
        client.dashboard(scope="mine")
        first, second = client.session.calls
        self.assertEqual((first["method"], first["url"]), ("GET", url))
        self.assertEqual(first["headers"], {"Authorization": "Bearer " + TOKEN})
        self.assertEqual(first["params"], {"scope": "all"})
        self.assertEqual(second["params"], {"scope": "mine"})

    def test_metadata_schema_is_a_bare_get(self) -> None:
        url = BASE + "/api/v1/metadata/schema"
        schema = {
            "schema": [{"name": "location", "type": "string", "ui_type": "select", "label": "Location"}],
            "table": "vss-collection",
        }
        client = _real_client(_response(200, schema, url))
        self.assertEqual(client.metadata_schema(), schema)
        call = self._only_call(client)
        self.assertEqual((call["method"], call["url"]), ("GET", url))
        self.assertEqual(call["headers"], {"Authorization": "Bearer " + TOKEN})
        self.assertNotIn("params", call)

    def test_metadata_values_params(self) -> None:
        url = BASE + "/api/v1/metadata/values"
        body = {"field": "location", "values": ["Warehouse A"], "count": 1}
        client = _real_client(_response(200, body, url), _response(200, body, url))
        self.assertEqual(client.metadata_values("location"), body)
        client.metadata_values("location", prefix="War", limit=5)
        first, second = client.session.calls
        self.assertEqual((first["method"], first["url"]), ("GET", url))
        self.assertEqual(first["headers"], {"Authorization": "Bearer " + TOKEN})
        self.assertEqual(first["params"], {"field": "location", "limit": 50})
        self.assertEqual(second["params"], {"field": "location", "limit": 5, "prefix": "War"})

    def test_metadata_values_400_raises_http_error(self) -> None:
        client = _real_client(_response(400, {"detail": "not filterable"}, BASE + "/api/v1/metadata/values"))
        with self.assertRaises(requests.HTTPError) as ctx:
            client.metadata_values("pk")
        self.assertEqual(ctx.exception.response.status_code, 400)

    def test_object_routes_refuse_non_object_bodies(self) -> None:
        cases = [
            ("dashboard/stats", lambda c: c.dashboard(), "/api/v1/dashboard/stats"),
            ("metadata/schema", lambda c: c.metadata_schema(), "/api/v1/metadata/schema"),
            ("metadata/values", lambda c: c.metadata_values("location"), "/api/v1/metadata/values"),
        ]
        for name, call, path in cases:
            for body in (["not", "an", "object"], None):
                with self.subTest(route=name, body=body):
                    client = _real_client(_response(200, body, BASE + path))
                    with self.assertRaises(VssError) as ctx:
                        call(client)
                    self.assertEqual(str(ctx.exception), f"{name} response is not an object")

    def test_expired_jwt_logs_in_again_once(self) -> None:
        url = BASE + "/api/v1/suggestions"
        login_url = BASE + "/api/v1/auth/login"
        client = _real_client(
            _response(401, {"detail": "expired"}, url),
            _response(200, {"access_token": "fresh-" + RUN, "token_type": "bearer"}, login_url),
            _response(200, {"prompts": []}, url),
        )
        self.assertEqual(client.suggestions(), {"prompts": []})
        stale, login, retry = client.session.calls
        self.assertEqual(stale["headers"], {"Authorization": "Bearer " + TOKEN})
        self.assertEqual((login["method"], login["url"]), ("POST", login_url))
        self.assertEqual(login["json"], {"username": USER, "password": PASSWORD})
        self.assertEqual(retry["headers"], {"Authorization": "Bearer fresh-" + RUN})


class _RouteBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not main.state.store.load_units():
            main.state.scan()
            main.state.run_gate()
        cls.client = TestClient(main.app)
        cls.unit = main.state.store.load_units()[0]

    def setUp(self) -> None:
        saved = stack_tools._client
        self.addCleanup(setattr, stack_tools, "_client", saved)

    def _patch(self, name: str, value: Any) -> None:
        patcher = mock.patch.object(config, name, value)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _send(self, name: str) -> Any:
        method, path, params, body, _ = ROUTES[name]
        if method == "POST":
            return self.client.post(path, json=body)
        return self.client.get(path, params=params)


class MockRouteTests(_RouteBase):
    def setUp(self) -> None:
        super().setUp()
        self._patch("MOCK", True)
        self.vss = FakeVss(AssertionError("mock mode called VSS"))
        stack_tools._client = self.vss

    def tearDown(self) -> None:
        self.assertEqual(self.vss.calls, [])

    def test_every_route_answers_200_with_mock_true(self) -> None:
        self.assertEqual(len(ROUTES), 5)
        for name in ROUTES:
            with self.subTest(name):
                r = self._send(name)
                self.assertEqual(r.status_code, 200, r.text)
                self.assertIs(r.json()["mock"], True)

    def test_mock_payloads(self) -> None:
        dash = self.client.get("/api/stack/dashboard").json()
        self.assertEqual(dash["scope"], "all")
        self.assertEqual(dash["data"]["overview"]["segment_rows"], len(main.state.store.load_units()))
        self.assertIn(PAYOFF_QUERY, self.client.get("/api/stack/suggest").json()["data"]["prompts"])
        schema = self.client.get("/api/stack/metadata").json()
        self.assertIsNone(schema["field"])
        self.assertEqual(schema["data"]["table"], "vss-collection")
        self.assertEqual({row["name"] for row in schema["data"]["schema"]}, set(stack_tools.MOCK_FIELDS))
        values = self.client.get("/api/stack/metadata", params={"field": "camera_id"}).json()
        self.assertEqual(values["data"], {"field": "camera_id", "values": [CAMERA_ID], "count": 1})
        ask = self.client.post(
            "/api/stack/ask", json={"question": "Is the aisle clear?", "unit_id": self.unit["id"]}
        ).json()
        self.assertEqual(ask["unit_id"], self.unit["id"])
        self.assertEqual(ask["original_video"], self.unit["original_video"])
        self.assertEqual(ask["data"]["answer"], stack_tools.MOCK_ANSWER)

    def test_unknown_dashboard_scope_is_400(self) -> None:
        r = self.client.get("/api/stack/dashboard", params={"scope": "everyone"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("'everyone'", r.json()["detail"])

    def test_unknown_metadata_field_is_400(self) -> None:
        r = self.client.get("/api/stack/metadata", params={"field": "pk"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("'pk'", r.json()["detail"])

    def test_empty_question_is_rejected(self) -> None:
        self.assertEqual(self.client.post("/api/stack/ask", json={"question": ""}).status_code, 422)
        self.assertEqual(self.client.post("/api/stack/ask", json={}).status_code, 422)
        r = self.client.post("/api/stack/ask", json={"question": "   "})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["detail"], "question is empty")

    def test_unknown_unit_is_404(self) -> None:
        r = self.client.post(
            "/api/stack/ask", json={"question": "Is the aisle clear?", "unit_id": "wh-unknown"}
        )
        self.assertEqual(r.status_code, 404)
        self.assertIn("'wh-unknown'", r.json()["detail"])


class LiveRouteTests(_RouteBase):
    def setUp(self) -> None:
        super().setUp()
        self._patch("MOCK", False)
        self._patch("VSS_URL", CONFIG_URL)
        self._patch("VSS_PASSWORD", CONFIG_PASSWORD)

    def _fake(self, outcome: Any) -> FakeVss:
        fake = FakeVss(outcome)
        stack_tools._client = fake
        return fake

    def _assert_clean(self, text: str) -> None:
        for leak in LEAKS:
            self.assertNotIn(leak, text)

    def test_success_bodies_pass_through_with_mock_false(self) -> None:
        payloads = {
            "dashboard": {"overview": {"unique_videos": 2}, "objects": []},
            "suggestions": {"prompts": ["forklift near a person"], "key_events": []},
            "metadata_schema": {"schema": [], "table": "vss-collection"},
            "metadata_values": {"field": "location", "values": ["Warehouse A"], "count": 1},
            "agent_ask": {"answer": "No one was near the dock.", "tool_used": "search_hybrid", "evidence": []},
        }
        calls = {
            "dashboard": ("dashboard", {"scope": "public"}),
            "suggestions": ("suggestions", {}),
            "metadata_schema": ("metadata_schema", {}),
            "metadata_values": ("metadata_values", {"field": "location", "prefix": "War", "limit": 5}),
            "agent_ask": (
                "agent_ask",
                {"question": "Was anyone near the dock?", "original_video": "", "top_k": 10},
            ),
        }
        self.assertEqual(set(payloads), set(ROUTES))
        for name, payload in payloads.items():
            with self.subTest(name):
                fake = self._fake(payload)
                r = self._send(name)
                self.assertEqual(r.status_code, 200, r.text)
                body = r.json()
                self.assertIs(body["mock"], False)
                self.assertEqual(body["data"], payload)
                self.assertEqual(fake.calls, [calls[name]])

    def test_unit_scoped_ask_sends_the_units_original_video(self) -> None:
        fake = self._fake({"answer": "Clear.", "tool_used": "video_segments", "evidence": []})
        r = self.client.post(
            "/api/stack/ask", json={"question": "  Is the aisle clear? ", "unit_id": self.unit["id"]}
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["original_video"], self.unit["original_video"])
        self.assertEqual(
            fake.calls,
            [(
                "agent_ask",
                {
                    "question": "Is the aisle clear?",
                    "original_video": self.unit["original_video"],
                    "top_k": 10,
                },
            )],
        )

    def test_errors_become_503_without_url_host_token_or_password(self) -> None:
        for name, (_, _, _, _, path) in ROUTES.items():
            url = f"{BASE}{path}?token={TOKEN}"
            cases = {
                "HTTPError": (_http_error(500, url), f"VSS {path} failed: HTTP 500"),
                "Timeout": (
                    requests.Timeout(f"HTTPSConnectionPool(host='{HOST}', port=8443): Read timed out."),
                    f"VSS {path} timed out",
                ),
                "VssError": (
                    VssError(
                        f"upstream refused {url} for {HOST} with {PASSWORD}"
                        f" and {CONFIG_PASSWORD} via {CONFIG_HOST}"
                    ),
                    f"VSS {path} failed: upstream refused <url> for <redacted>"
                    " with <redacted> and <redacted> via <redacted>",
                ),
            }
            for kind, (exc, expected) in cases.items():
                with self.subTest(route=name, error=kind):
                    self.assertIn(RUN, str(exc))
                    self._fake(exc)
                    with self.assertLogs("scribner.stack_tools", level="WARNING") as logs:
                        r = self._send(name)
                    self.assertEqual(r.status_code, 503, r.text)
                    self.assertEqual(r.json()["detail"], expected)
                    self._assert_clean(r.text)
                    self.assertEqual(logs.output, [f"WARNING:scribner.stack_tools:{expected}"])

    def test_config_secrets_are_redacted_without_a_client(self) -> None:
        reason = stack_tools.failure_reason(
            "/api/v1/suggestions", VssError(f"no route to {CONFIG_HOST} using {CONFIG_PASSWORD}")
        )
        self.assertEqual(reason, "VSS /api/v1/suggestions failed: no route to <redacted> using <redacted>")

    def test_login_http_error_names_login(self) -> None:
        self._fake(_http_error(401, BASE + "/api/v1/auth/login"))
        with self.assertLogs("scribner.stack_tools", level="WARNING"):
            r = self._send("dashboard")
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.json()["detail"], "VSS login failed: HTTP 401")

    def test_ask_without_answer_is_503(self) -> None:
        for payload in ({"tool_used": "search_hybrid", "evidence": []}, ["answer"], None):
            with self.subTest(payload=payload):
                self._fake(payload)
                r = self._send("agent_ask")
                self.assertEqual(r.status_code, 503, r.text)
                self.assertEqual(r.json()["detail"], "VSS /api/v1/agent/ask returned no answer")

    def test_vss_400_for_a_metadata_field_stays_400(self) -> None:
        self._fake(_http_error(400, f"{BASE}/api/v1/metadata/values?field=pk"))
        with self.assertLogs("scribner.stack_tools", level="WARNING"):
            r = self.client.get("/api/stack/metadata", params={"field": "pk"})
        self.assertEqual(r.status_code, 400, r.text)
        self.assertEqual(r.json()["detail"], "field 'pk' is not filterable on VSS: HTTP 400")
        self._assert_clean(r.text)

    def test_vss_400_elsewhere_and_login_400_stay_503(self) -> None:
        cases = [
            ("dashboard", BASE + "/api/v1/dashboard/stats", "VSS /api/v1/dashboard/stats failed: HTTP 400"),
            ("metadata_values", BASE + "/api/v1/auth/login", "VSS login failed: HTTP 400"),
        ]
        for name, url, expected in cases:
            with self.subTest(name):
                self._fake(_http_error(400, url))
                with self.assertLogs("scribner.stack_tools", level="WARNING"):
                    r = self._send(name)
                self.assertEqual(r.status_code, 503, r.text)
                self.assertEqual(r.json()["detail"], expected)

    def test_unknown_scope_never_calls_vss(self) -> None:
        fake = self._fake({"overview": {}})
        r = self.client.get("/api/stack/dashboard", params={"scope": "everyone"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(fake.calls, [])

    def test_route_through_real_client_and_session(self) -> None:
        url = BASE + "/api/v1/dashboard/stats"
        client = _real_client(
            _response(200, {"overview": {"unique_videos": 1}}, url),
            _response(502, {"detail": "bad gateway"}, url),
            _response(200, ["not", "an", "object"], url),
            _response(200, b"<html>bad gateway</html>", url),
            requests.ConnectionError(f"HTTPSConnectionPool(host='{HOST}', port=8443): refused"),
        )
        stack_tools._client = client
        ok = self.client.get("/api/stack/dashboard", params={"scope": "mine"})
        self.assertEqual(ok.status_code, 200, ok.text)
        self.assertEqual(ok.json(), {"mock": False, "scope": "mine", "data": {"overview": {"unique_videos": 1}}})
        expected = [
            "VSS /api/v1/dashboard/stats failed: HTTP 502",
            "VSS /api/v1/dashboard/stats failed: dashboard/stats response is not an object",
            "VSS /api/v1/dashboard/stats returned invalid JSON",
            "VSS /api/v1/dashboard/stats connection failed",
        ]
        for reason in expected:
            with self.subTest(reason):
                with self.assertLogs("scribner.stack_tools", level="WARNING"):
                    r = self.client.get("/api/stack/dashboard")
                self.assertEqual(r.status_code, 503, r.text)
                self.assertEqual(r.json()["detail"], reason)
                self._assert_clean(r.text)
        calls = client.session.calls
        self.assertEqual(len(calls), 5)
        self.assertEqual(
            (calls[0]["method"], calls[0]["url"], calls[0]["params"]), ("GET", url, {"scope": "mine"})
        )
        self.assertEqual(calls[0]["headers"], {"Authorization": "Bearer " + TOKEN})
        self.assertEqual([c["params"] for c in calls[1:]], [{"scope": "all"}] * 4)


if __name__ == "__main__":
    unittest.main()
