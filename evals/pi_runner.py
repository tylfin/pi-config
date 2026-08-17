import os
from pathlib import Path
import shlex
import shutil
import subprocess
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
