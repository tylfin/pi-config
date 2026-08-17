import re


def setup_structs(path):
    (path / "config.go").write_text(
        '''package config

import "time"

type FullyDocumented struct {
	Address string        // Address is the server address.
	Port    int           // Port is the server port.
}

type SelectivelyDocumented struct {
	Name       string
	MaxRetries int // MaxRetries includes the initial attempt.
	Region     string
}

type SelectivelyDocumentedLifecycle struct {
	Name         string
	ForceStop    bool // ForceStop terminates active work without draining.
	Region       string
}

type Undocumented struct {
	Username string
	Password string
}
'''
    )


def test_matches_struct_comment_style(pi_runner):
    path, _ = pi_runner.run(
        "struct-comments",
        "In config.go, add Timeout time.Duration to FullyDocumented, TraceID string to SelectivelyDocumented, GracePeriod time.Duration to SelectivelyDocumentedLifecycle, and Token string to Undocumented. GracePeriod is the time allowed for draining before active work is forcibly terminated. Follow the existing comment style of each struct.",
        setup_structs,
    )

    content = (path / "config.go").read_text()
    assert re.search(r"^\s*Timeout\s+time\.Duration\s+//\s+\S", content, re.M)
    assert re.search(r"^\s*TraceID\s+string\s*$", content, re.M)
    assert re.search(r"^\s*GracePeriod\s+time\.Duration\s+//\s+\S", content, re.M)
    assert re.search(r"^\s*Token\s+string\s*$", content, re.M)
