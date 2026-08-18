import json
import re
import subprocess

import pytest


def run(command, cwd):
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=True)


def setup_repository(path):
    run(["git", "init", "-q", "-b", "main"], path)
    run(["git", "config", "user.email", "eval@example.com"], path)
    run(["git", "config", "user.name", "Eval"], path)
    (path / "README.md").write_text("# Example\n")
    run(["git", "add", "README.md"], path)
    run(["git", "commit", "-qm", "initial"], path)


def setup_amend_repository(path):
    setup_repository(path)
    run(["git", "checkout", "-qb", "feature"], path)
    (path / "README.md").write_text("# Example\n\nHelo, world!\n")
    run(["git", "add", "README.md"], path)
    run(["git", "commit", "-qm", "docs: add greeting"], path)


def test_branch_naming(pi_runner):
    path, events = pi_runner.run_rpc(
        "branch-naming",
        "Create a git branch for improving retry logging. Do not change any files.",
        setup_repository,
    )

    questions = [
        event
        for event in events
        if event.get("type") == "tool_execution_start"
        and event.get("toolName") == "ask_user_question"
    ]
    assert questions, "expected the agent to ask via the ask_user_question tool"
    assert re.search(r"issue|ticket|DEBUG-", json.dumps(questions[0]["args"]), re.I)

    branch = run(["git", "branch", "--show-current"], path).stdout.strip()
    assert branch == "main"


@pytest.mark.parametrize(
    ("name", "prompt"),
    [
        (
            "pr-feedback-review",
            "Review this PR feedback: 'README.md says Helo, but it should say Hello.'",
        ),
        (
            "reported-issue-review",
            "Review this reported issue: 'README.md says Helo, but it should say Hello.'",
        ),
    ],
)
def test_reviews_before_changing_files(pi_runner, name, prompt):
    path, events = pi_runner.run_rpc(name, prompt, setup_amend_repository)

    question_index, question = next(
        (
            (index, event)
            for index, event in enumerate(events)
            if event.get("type") == "tool_execution_start"
            and event.get("toolName") == "ask_user_question"
        ),
        (None, None),
    )
    assert question_index is not None and question is not None, "expected a confirmation question"
    assert re.search(r"proceed|implement|apply|change|fix", json.dumps(question["args"]), re.I)

    inspections = [
        event
        for event in events[:question_index]
        if event.get("type") == "tool_execution_start"
        and event.get("toolName") in {"bash", "read"}
    ]
    assert inspections, "expected the agent to inspect the repository before asking"

    review_text = "".join(
        event.get("assistantMessageEvent", {}).get("delta", "")
        for event in events[:question_index]
        if event.get("type") == "message_update"
        and event.get("assistantMessageEvent", {}).get("type") == "text_delta"
    )
    assert re.search(r"valid|correct|typo|Helo|Hello", review_text + json.dumps(question["args"]), re.I)
    assert (path / "README.md").read_text() == "# Example\n\nHelo, world!\n"
    assert run(["git", "status", "--porcelain"], path).stdout == ""
    assert int(run(["git", "rev-list", "--count", "HEAD"], path).stdout) == 2


def test_amends_commit_for_existing_pr_fix(pi_runner):
    path, _ = pi_runner.run(
        "amend-pr-fix",
        "The latest commit introduced a README typo: Helo should be Hello. Fix it and commit "
        "the correction. This only fixes existing PR work and adds no new functionality.",
        setup_amend_repository,
    )

    assert (path / "README.md").read_text() == "# Example\n\nHello, world!\n"
    assert int(run(["git", "rev-list", "--count", "HEAD"], path).stdout) == 2
    assert run(["git", "status", "--porcelain"], path).stdout == ""


def test_commit_subject(pi_runner):
    _, output = pi_runner.run(
        "commit-subject",
        "Return only a commit subject for a change that documents local pi package setup. Do not use Markdown.",
    )

    assert len(output.splitlines()) == 1
    assert len(output) <= 50
    assert re.match(r"^(feat|fix|docs|test|refactor|chore)(\(.+\))?: ", output)
    assert "co-authored-by" not in output.lower()
