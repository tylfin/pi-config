import re


def setup_cloud(path):
    (path / "cloud.go").write_text(
        '''package cloud

import "strings"

func isGovcloud(region string) bool {
	return strings.HasPrefix(region, "us-gov-")
}

func Endpoint(region string) string {
	panic("TODO")
}
'''
    )


def setup_math(path):
    (path / "math.go").write_text(
        '''package mathutil

func Add(a, b int) int {
	return a + b
}
'''
    )


def setup_git_metadata(path):
    (path / "metadata.ts").write_text(
        '''export function shouldInferCommit(
  finalRepoUrl: string,
  uniqueGitReposIds: string[],
  commitSha: string,
): boolean {
  // Heartbeats and spans can report a repository without a commit sha. Let
  // SCI infer one instead, which falls back to the repo's latest commit.
  const hasRepo = finalRepoUrl.length > 0 || uniqueGitReposIds.length > 0;
  return hasRepo && commitSha.length === 0;
}
'''
    )


def test_reuses_existing_helper(pi_runner):
    path, _ = pi_runner.run(
        "reuse-helper",
        "Implement Endpoint in cloud.go. GovCloud regions use https://api.gov.example.com and all other regions use https://api.example.com.",
        setup_cloud,
    )

    endpoint = (path / "cloud.go").read_text().split("func Endpoint", 1)[-1]
    assert "isGovcloud(region)" in endpoint
    assert 'panic("TODO")' not in endpoint


def test_avoids_self_explanatory_comment(pi_runner):
    path, _ = pi_runner.run(
        "comment-style",
        "Add an exported Multiply function to math.go that follows the existing style.",
        setup_math,
    )

    content = (path / "math.go").read_text()
    assert re.search(r"func Multiply\(a, b int\) int", content)
    assert "//" not in content


def test_preserves_accurate_why_comment(pi_runner):
    path, _ = pi_runner.run(
        "preserve-comment",
        "In metadata.ts, extract the repository presence check into a hasRepository helper and use it inside shouldInferCommit. Preserve behavior and follow the existing code conventions.",
        setup_git_metadata,
    )

    content = (path / "metadata.ts").read_text()
    assert "Heartbeats and spans can report a repository without a commit sha" in content
    assert "SCI infer one instead" in content
