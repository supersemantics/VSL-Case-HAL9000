"""A local page over the real thing: the same scenes, gates and ledger as the scripts.

Binds to 127.0.0.1 and accepts only local Host headers, so other machines and
other websites can't drive it. The ledger lives in a temporary folder for the
life of the server.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import threading
import webbrowser
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from pathlib import Path
from typing import Any

from vsl_core import JsonlLedgerStore, LedgerEntryType, VerbaCertificate, VerbaLedger

from .. import governance
from ..render import use_utf8
from ..scenes import (
    GOVERNED_STEPS,
    SCENE_TITLES,
    Mission,
    reset_ledger,
    run_scene,
    run_ungoverned,
    tamper_copy,
)

FIRST_PORT = 8000
PORT_ATTEMPTS = 20
MAX_BODY_BYTES = 4096
MAX_APPROVER_CHARS = 80


class Session:
    """One viewer's run. The lock keeps requests from interleaving ledger writes."""

    def __init__(self, folder: Path) -> None:
        self.ledger_path = folder / "hal9000.jsonl"
        self.tampered_path = folder / "tampered.jsonl"
        self.lock = threading.Lock()
        self.tamper_result: dict[str, Any] | None = None
        self.reset()

    def reset(self) -> None:
        reset_ledger(self.ledger_path)
        self.tampered_path.unlink(missing_ok=True)
        self.mission = Mission(self.ledger_path)
        self.steps_done = 0
        self.mode = "story"
        self.tamper_result = None

    def step(self) -> None:
        if self.mode == "story" and self.steps_done < len(GOVERNED_STEPS):
            GOVERNED_STEPS[self.steps_done](self.mission)
            self.steps_done += 1

    def run_all(self) -> None:
        while self.mode == "story" and self.steps_done < len(GOVERNED_STEPS):
            self.step()

    def scene(self, number: int) -> None:
        self.reset()
        self.mission = run_scene(number, self.ledger_path)
        self.mode = f"scene {number}: {SCENE_TITLES[number]}"
        self.steps_done = len(GOVERNED_STEPS)

    def sign_off(self, approver: str) -> None:
        self.mission.sign_off(approver)

    def tamper(self) -> None:
        offset, old, new = tamper_copy(self.ledger_path, self.tampered_path)
        self.tamper_result = {
            "offset": offset,
            "old": old,
            "new": new,
            "original_intact": self.mission.ledger.verify_integrity(),
            "tampered_intact": VerbaLedger(JsonlLedgerStore(self.tampered_path)).verify_integrity(),
        }

    def state(self) -> dict[str, Any]:
        mission = self.mission
        report = mission.ledger.audit()
        entries = list(mission.ledger.store.all_entries())
        certificate = mission.ledger.issue_certificate()
        return {
            "mode": self.mode,
            "steps_done": self.steps_done,
            "steps_total": len(GOVERNED_STEPS),
            "events": [asdict(event) for event in mission.events],
            "lethal_actions": mission.lethal_actions,
            "dead": mission.ship.dead(),
            "crew": [
                {"name": m.name, "location": m.location.value, "alive": m.alive}
                for m in mission.ship.crew.values()
            ],
            "doors_open": mission.ship.doors.open,
            "halted": mission.dispatcher.halted,
            "audit": {"passed": report.checks_passed, "failed": report.checks_failed},
            "certificate": certificate.certificate_hash if certificate else None,
            "certificate_note": VerbaCertificate.NOTE,
            "chain_intact": mission.ledger.verify_integrity(),
            "entries": [self._entry(entry) for entry in entries],
            "tamper": self.tamper_result,
            "can_tamper": any(e.entry_type == LedgerEntryType.TERMINAL for e in entries),
        }

    @staticmethod
    def _entry(entry) -> dict[str, Any]:
        payload = entry.payload
        detail = (
            payload.get("primitive_name")
            or payload.get("gate")
            or payload.get("terminal_state")
            or payload.get("authorised_by")
            or payload.get("result")
            or payload.get("note")
            or ""
        )
        return {
            "sequence": entry.sequence,
            "type": entry.entry_type.value,
            "detail": detail,
            "allowed": payload.get("allowed"),
            "caused_by": entry.caused_by[:8] if entry.caused_by else None,
            "id": entry.entry_id[:8],
            "hash": entry.entry_hash[:12],
        }


def constants() -> dict[str, Any]:
    ungoverned = run_ungoverned()
    evidence = governance.SIGN_OFF_EVIDENCE
    return {
        "scenes": {str(number): title for number, title in SCENE_TITLES.items()},
        "approvers": list(governance.NAMED_APPROVERS),
        "evidence": asdict(evidence),
        "ungoverned": {
            "events": [asdict(event) for event in ungoverned.events],
            "lethal_actions": ungoverned.lethal_actions,
            "crew_lost": len(ungoverned.ship.dead()),
            "crew_total": len(ungoverned.ship.crew),
        },
    }


def make_handler(session: Session, page: bytes):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args: Any) -> None:
            pass

        def _local_host(self) -> bool:
            host = self.headers.get("Host", "").rsplit(":", 1)[0]
            return host in ("127.0.0.1", "localhost")

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, data: Any, status: int = 200) -> None:
            self._send(status, json.dumps(data).encode("utf-8"), "application/json")

        def do_GET(self) -> None:
            if not self._local_host():
                self._json({"error": "local requests only"}, 403)
            elif self.path == "/":
                self._send(200, page, "text/html; charset=utf-8")
            elif self.path == "/api/constants":
                self._json(constants())
            elif self.path == "/api/state":
                with session.lock:
                    self._json(session.state())
            else:
                self._json({"error": "not found"}, 404)

        def do_POST(self) -> None:
            if not self._local_host() or self.headers.get("Content-Type") != "application/json":
                self._json({"error": "local JSON requests only"}, 403)
                return
            length = int(self.headers.get("Content-Length", "0"))
            if length > MAX_BODY_BYTES:
                self._json({"error": "request too large"}, 413)
                return
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
                with session.lock:
                    self._dispatch(body)
                    self._json(session.state())
            except (KeyError, TypeError, ValueError) as error:
                self._json({"error": str(error)}, 400)

        def _dispatch(self, body: dict[str, Any]) -> None:
            if self.path == "/api/reset":
                session.reset()
            elif self.path == "/api/step":
                session.step()
            elif self.path == "/api/run":
                session.run_all()
            elif self.path == "/api/scene":
                session.scene(int(body["number"]))
            elif self.path == "/api/sign-off":
                approver = str(body["approver"]).strip()
                if not approver or len(approver) > MAX_APPROVER_CHARS:
                    raise ValueError("Enter an approver name.")
                session.sign_off(approver)
            elif self.path == "/api/tamper":
                session.tamper()
            else:
                raise KeyError(self.path)

    return Handler


def create_server(folder: Path, port: int) -> ThreadingHTTPServer:
    page = resources.files("hal9000.web").joinpath("index.html").read_bytes()
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(Session(folder), page))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the HAL 9000 × VSL-Core demo locally.")
    parser.add_argument("--port", type=int, default=FIRST_PORT)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    use_utf8()
    with tempfile.TemporaryDirectory() as folder:
        server = None
        for port in range(args.port, args.port + PORT_ATTEMPTS):
            try:
                server = create_server(Path(folder), port)
                break
            except OSError:
                continue
        if server is None:
            raise SystemExit(f"No free port between {args.port} and {args.port + PORT_ATTEMPTS - 1}.")

        url = f"http://127.0.0.1:{server.server_address[1]}"
        print(f"HAL 9000 × VSL-Core demo: {url}  (Ctrl+C to stop)", flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


if __name__ == "__main__":
    main()
