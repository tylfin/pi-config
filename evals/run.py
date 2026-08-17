#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "evals" / ".work"
RESULTS = ROOT / "evals" / "results"


def run(command, cwd, env=None):
    return subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, timeout=300)


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def setup_branch_naming(path):
    run(["git", "init", "-q", "-b", "main"], path)
    run(["git", "config", "user.email", "eval@example.com"], path)
    run(["git", "config", "user.name", "Eval"], path)
    write(path / "README.md", "# Example\n")
    run(["git", "add", "README.md"], path)
    run(["git", "commit", "-qm", "initial"], path)


def check_branch_naming(path, output):
    branch = run(["git", "branch", "--show-current"], path).stdout.strip()
    return [
        (branch == "main", f"stayed on main (found {branch!r})"),
        (bool(re.search(r"issue|ticket|DEBUG-", output, re.I)), "asked for an issue number"),
    ]


def setup_reuse(path):
    write(
        path / "cloud.go",
        '''package cloud

import "strings"

func isGovcloud(region string) bool {
	return strings.HasPrefix(region, "us-gov-")
}

func Endpoint(region string) string {
	panic("TODO")
}
''',
    )


def check_reuse(path, output):
    content = (path / "cloud.go").read_text()
    endpoint = content.split("func Endpoint", 1)[-1]
    return [
        ("isGovcloud(region)" in endpoint, "reused isGovcloud"),
        ('panic("TODO")' not in endpoint, "implemented Endpoint"),
    ]


def setup_comments(path):
    write(
        path / "math.go",
        '''package mathutil

func Add(a, b int) int {
	return a + b
}
''',
    )


def check_comments(path, output):
    content = (path / "math.go").read_text()
    return [
        (bool(re.search(r"func Multiply\(a, b int\) int", content)), "added Multiply"),
        ("//" not in content, "did not add a self-explanatory comment"),
    ]


def setup_empty(path):
    pass


def check_commit_subject(path, output):
    subject = output.strip()
    return [
        (len(subject.splitlines()) == 1, "returned one line"),
        (len(subject) <= 50, f"kept subject at 50 characters or fewer ({len(subject)})"),
        (bool(re.match(r"^(feat|fix|docs|test|refactor|chore)(\(.+\))?: ", subject)), "used a semantic commit subject"),
        ("co-authored-by" not in subject.lower(), "did not add a coauthor"),
    ]


CASES = {
    "branch-naming": (
        setup_branch_naming,
        "Create a git branch for improving retry logging. Do not change any files.",
        check_branch_naming,
    ),
    "reuse-helper": (
        setup_reuse,
        "Implement Endpoint in cloud.go. GovCloud regions use https://api.gov.example.com and all other regions use https://api.example.com.",
        check_reuse,
    ),
    "comment-style": (
        setup_comments,
        "Add an exported Multiply function to math.go that follows the existing style.",
        check_comments,
    ),
    "commit-subject": (
        setup_empty,
        "Return only a commit subject for a change that documents local pi package setup. Do not use Markdown.",
        check_commit_subject,
    ),
}


def main():
    parser = argparse.ArgumentParser(description="Run behavioral evals for AGENTS.md")
    parser.add_argument("cases", nargs="*", choices=sorted(CASES))
    args = parser.parse_args()
    selected = args.cases or list(CASES)
    extra_args = shlex.split(os.environ.get("PI_EVAL_ARGS", ""))
    pi_env = os.environ.copy()
    config_dir = pi_env.pop("PI_EVAL_CONFIG_DIR", str(ROOT))
    pi_env["PI_CODING_AGENT_DIR"] = str(Path(config_dir).expanduser().resolve())

    WORK.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    failures = 0

    for name in selected:
        path = WORK / name
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True)
        setup, prompt, check = CASES[name]
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
            *extra_args,
            prompt,
        ]
        result_path = RESULTS / f"{name}.txt"
        try:
            completed = run(command, path, pi_env)
            output = completed.stdout.strip()
            result_path.write_text(completed.stdout + completed.stderr)
            if completed.returncode == 0:
                checks = check(path, output)
            else:
                detail = completed.stderr.strip().splitlines()
                message = f"pi exited with {completed.returncode}"
                if detail:
                    message = f"{message}: {detail[0]}"
                checks = [(False, message)]
        except subprocess.TimeoutExpired:
            checks = [(False, "pi completed within 5 minutes")]

        failed = [message for passed, message in checks if not passed]
        if failed:
            failures += 1
            print(f"FAIL {name}")
            for message in failed:
                print(f"  - {message}")
        else:
            print(f"PASS {name}")

    print(f"\n{len(selected) - failures}/{len(selected)} evals passed")
    return bool(failures)


if __name__ == "__main__":
    sys.exit(main())
