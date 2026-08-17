Engineering Rules

Datadog
- Datadog is a large, professional engineering org.
- New code in repositories must match existing conventions, and re-use is preferred over new utilities.
- Libraries like dd-trace-py, dd-trace-java, etc. run on customers machines, we don't control the environment.
- Backend services like logs-backend handle billions of events so we must account for scale and memory usage.

Branch Naming
- Format: tyler.finethy/DEBUG-XXXX
- If no issue number is provided, ask for one.
- If none exists, use: tyler.finethy/<short-description>

Code Conventions
- DO NOT WRITE CODE COMMENTS WHEN THE CODE IS SELF-EXPLANATORY.
- Do not write overly verbose comments. These should match the file conventions.
- This means a one line change gets a ONE LINE COMMENT. NO PARAGRAPHS UNLESS IT IS IMPERATIVE FOR FUTURE REVIEWERS.

Commits
- Follow the repository’s existing style.
- Prefer semantic commits.
- Keep the header ≤ 50 characters.
- Do not add yourself as a coauthor.
- Describe the current diff NOT decisions/changes along the way.
- Write release notes for a user-facing audience, not an engineering-internal one. Avoid deep technical jargon.
- Commit messages should be holistic and cover all changes in the commit, not narrowly scoped to one file or aspect.

Pull Requests
- ALWAYS read an existing PR body before updating it!
- Pull requests descriptions should ALWAYS be holistic and cover only the diffs from main/preprod/etc.
- Do not leak discussions from chat, base PR content only on what a reviewer cares about.
- No "Generated with" line

Refactoring
- Prefer existing utilities over reimplementing logic: e.g., `isGovcloud()` for GovCloud checks, `fibonacci_backoff_with_jitter` for retries, DRUIDS `toggleSwitch` helper in tests.
- Prefer minimal, targeted changes over introducing new files/packages/dependencies.

Tests
- Match test count to change complexity.
- Avoid over-testing small changes.
- Target ~1–2 tests per affected file.

Misc
- Don't touch config files without asking.
- Don't add dependencies without asking.
- NO em dashes
