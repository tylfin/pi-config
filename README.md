# pi-config

Version-controlled pi configuration and behavioral evals for `AGENTS.md`.

## Packages

Set this repository as pi's global configuration directory with an absolute path:

```sh
export PI_CODING_AGENT_DIR="$HOME/path/to/pi-config"
```

Pi loads the root [`AGENTS.md`](AGENTS.md) and [`settings.json`](settings.json) from that directory. Package declarations in `settings.json` are version controlled, while downloaded npm and git contents are ignored.

Add packages and pin their versions or refs:

```sh
pi install npm:@scope/package@1.2.3
pi install git:github.com/owner/repository@v1.2.3
```

Commit the resulting `settings.json` change. Do not use `-l`, which writes project-local `.pi/settings.json` instead. Use `pi list` to inspect configured packages and `pi update --extensions` to reconcile installed contents with their pinned declarations.

Credentials remain local in the ignored `auth.json`. Authenticate this config by running `make login`, then use `/login` in pi.

## AGENTS.md evals

The eval runner starts pi in isolated fixture directories beneath this repository, so pi discovers the repository's `AGENTS.md`. It disables optional resources to keep the instructions under test isolated. The cases cover branch naming, utility reuse, general and structured declaration comment style, and commit subjects.

The Python environment is managed by uv from `requirements.txt`. Run all evals through Make:

```sh
make evals
```

Run selected evals with `EVALS`:

```sh
make evals EVALS='branch-naming comment-style'
```

Use a particular model or thinking level by passing pi arguments through `PI_EVAL_ARGS`:

```sh
PI_EVAL_ARGS='--model openai-codex/gpt-5.3-codex --thinking low' make evals
```

Runs make model API calls using this repository's pi configuration and its ignored `auth.json`. Set `PI_EVAL_CONFIG_DIR` to use another authenticated config directory. Outputs are written to `evals/results/`, and generated fixtures remain in `evals/.work/` for debugging. Both directories are ignored by git.
