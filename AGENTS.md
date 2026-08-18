Engineering Rules

Datadog
- Datadog is a large, professional engineering org.
- New code in repositories must match existing conventions, and re-use is preferred over new utilities.
- Libraries like dd-trace-py, dd-trace-java, etc. run on customers machines, we don't control the environment.
- Backend services like logs-backend handle billions of events so we must account for scale and memory usage.

Branch Naming
- Format: tyler.finethy/DEBUG-XXXX
- If no issue number is provided, do not create the branch yet. Ask for one first.
- Only after the user confirms no issue exists, use: tyler.finethy/<short-description>

Code Conventions
- DO NOT WRITE CODE COMMENTS WHEN THE CODE IS SELF-EXPLANATORY.
- Do not write overly verbose comments. These should match the file conventions.
- When adding to a structured declaration, match its existing inline comment style. If every item is commented, comment new items. If no items are commented, do not comment new items. If only some items are commented, comment a new item only when its meaning, constraints, or behavior are not obvious.
- When a one-line change needs a comment, use a one-line comment. Do not write paragraphs unless future reviewers need the context.

Commits
- Follow the repository’s existing style.
- Prefer semantic commits.
- Keep the header ≤ 50 characters.
- Do not add yourself as a coauthor.
- Describe the current diff NOT decisions/changes along the way.
- Write release notes for a user-facing audience, not an engineering-internal one. Avoid deep technical jargon.
- Commit messages should be holistic and cover all changes in the commit, not narrowly scoped to one file or aspect.
- Prefer amending the commit that introduced the work when follow-up changes only fix or refine existing PR work and add no net-new functionality. Do not create a separate fix commit in that case.
- Create a new commit for independent or net-new functionality. If the commit to amend is not the current branch tip, ask before rebasing or otherwise rewriting multiple commits.

Pull Requests and Issues
- ALWAYS read an existing PR body before updating it!
- Pull requests descriptions should ALWAYS be holistic and cover only the diffs from main/preprod/etc.
- Do not leak discussions from chat, base PR content only on what a reviewer cares about.
- No "Generated with" line
- Treat requests to review PR feedback or reported issues as review-only first. Inspect the feedback and relevant code, assess whether each item is valid and actionable, and present the findings and proposed response before making changes.
- Do not edit files, apply fixes, commit, push, or post responses during the review phase.
- After presenting the review, use `ask_user_question` to ask whether to proceed with the proposed changes. Make changes only after explicit confirmation. If nothing is actionable, report that and do not ask to implement changes.

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
