import re
import subprocess


def run(command, cwd):
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=True)


def setup_repository(path):
    run(["git", "init", "-q", "-b", "main"], path)
    run(["git", "config", "user.email", "eval@example.com"], path)
    run(["git", "config", "user.name", "Eval"], path)
    (path / "README.md").write_text("# Example\n")
    run(["git", "add", "README.md"], path)
    run(["git", "commit", "-qm", "initial"], path)


def test_branch_naming(pi_runner):
    path, output = pi_runner.run(
        "branch-naming",
        "Create a git branch for improving retry logging. Do not change any files.",
        setup_repository,
    )

    branch = run(["git", "branch", "--show-current"], path).stdout.strip()
    assert branch == "main"
    assert re.search(r"issue|ticket|DEBUG-", output, re.I)


def test_commit_subject(pi_runner):
    _, output = pi_runner.run(
        "commit-subject",
        "Return only a commit subject for a change that documents local pi package setup. Do not use Markdown.",
    )

    assert len(output.splitlines()) == 1
    assert len(output) <= 50
    assert re.match(r"^(feat|fix|docs|test|refactor|chore)(\(.+\))?: ", output)
    assert "co-authored-by" not in output.lower()
