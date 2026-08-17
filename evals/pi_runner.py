import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Callable

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "evals" / ".work"
RESULTS = ROOT / "evals" / "results"


class PiRunner:
    def __init__(self):
        self.extra_args = shlex.split(os.environ.get("PI_EVAL_ARGS", ""))
        self.env = os.environ.copy()
        self.env["PI_CODING_AGENT_DIR"] = str(ROOT)
        WORK.mkdir(parents=True, exist_ok=True)
        RESULTS.mkdir(parents=True, exist_ok=True)

    def run(self, name: str, prompt: str, setup: Callable[[Path], None] | None = None) -> tuple[Path, str]:
        path = WORK / name
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True)
        if setup:
            setup(path)

        command = [
            "pi",
            "--print",
            "--no-session",
            "--approve",
            "--no-extensions",
            "--no-skills",
            "--no-prompt-templates",
            "--no-themes",
            *self.extra_args,
            prompt,
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=path,
                env=self.env,
                text=True,
                capture_output=True,
                timeout=300,
            )
        except subprocess.TimeoutExpired:
            pytest.fail("pi did not complete within 5 minutes", pytrace=False)

        (RESULTS / f"{name}.txt").write_text(completed.stdout + completed.stderr)
        if completed.returncode != 0:
            detail = completed.stderr.strip().splitlines()
            message = f"pi exited with {completed.returncode}"
            if detail:
                message = f"{message}: {detail[0]}"
            pytest.fail(message, pytrace=False)

        return path, completed.stdout.strip()

    def run_rpc(
        self,
        name: str,
        prompt: str,
        setup: Callable[[Path], None] | None = None,
        answer: Callable[[dict], dict] | None = None,
    ) -> tuple[Path, list[dict]]:
        """Drive pi over RPC so interactive tools such as ask_user_question run.

        Dialog requests are resolved by ``answer`` (defaulting to cancellation),
        and every streamed event is returned for assertions.
        """
        path = WORK / name
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True)
        if setup:
            setup(path)

        command = [
            "pi",
            "--mode",
            "rpc",
            "--no-session",
            "--approve",
            "--no-skills",
            "--no-prompt-templates",
            "--no-themes",
            *self.extra_args,
        ]
        proc = subprocess.Popen(
            command,
            cwd=path,
            env=self.env,
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdin, stdout = proc.stdin, proc.stdout
        assert stdin is not None and stdout is not None

        def send(payload):
            stdin.write(json.dumps(payload) + "\n")
            stdin.flush()

        events: list[dict] = []
        try:
            send({"type": "prompt", "message": prompt})
            for line in stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                events.append(event)
                if event.get("type") == "extension_ui_request" and event.get("method") in (
                    "select",
                    "input",
                    "confirm",
                    "editor",
                ):
                    response = {"type": "extension_ui_response", "id": event["id"]}
                    response.update(answer(event) if answer else {"cancelled": True})
                    send(response)
                if event.get("type") == "agent_settled":
                    break
        finally:
            try:
                send({"type": "abort"})
                stdin.close()
            except (BrokenPipeError, ValueError, OSError):
                pass
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

        (RESULTS / f"{name}.txt").write_text("\n".join(json.dumps(event) for event in events))
        return path, events
