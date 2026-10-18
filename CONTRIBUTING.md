# Contributing

Thanks for helping. Two things matter more than anything else here: commits
that follow the standard, and pull requests a person would enjoy reading.

## Commits: Conventional Commits 1.0

Every commit subject follows [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

```
<type>(<optional scope>)<optional !>: <description>

<optional body: why, not what>

<optional footers, e.g. BREAKING CHANGE: ..., Refs: #12>
```

| type | use it for | release |
|---|---|---|
| `feat` | something users can do that they couldn't before | minor |
| `fix` | a bug fix | patch |
| `perf` | faster or cheaper, same behaviour | patch |
| `refactor` | restructuring with no behaviour change | none |
| `docs` | documentation only | none |
| `test` | adding or fixing tests | none |
| `build` | Cargo, Docker, dependencies | none |
| `ci` | workflows | none |
| `style` | formatting only | none |
| `chore` | everything else that ships nothing | none |
| `revert` | undoing an earlier commit | depends |

The rules:

- Description in the imperative, lower case, no full stop, 72 characters or
  fewer: `fix(compact): keep the user's messages verbatim`.
- Scope is optional and names the area: `agent`, `tools`, `permissions`,
  `memory`, `context`, `display`, `ui`, `llm`, `skills`, `evals`, `cloud`.
- A breaking change gets `!` after the type or scope, plus a
  `BREAKING CHANGE:` footer that says what breaks and how to migrate.
- The body explains **why**. The diff already shows what.
- One logical change per commit. If the subject needs "and", it's probably two
  commits.

Turn on the local check once per clone:

```bash
cargo xtask install-hooks
```

CI runs the same check on every commit in a pull request, and on its title.

## Pull requests

Write pull requests the way you'd explain the change to a teammate over
coffee. That means:

- **Plain, human language.** Short sentences. Say what was wrong, what you
  changed, and why this approach. Skip the buzzwords and the walls of
  bullet points.
- **No tool attribution.** Don't mention AI assistants, coding agents or any
  tool that helped write the change, and don't add "generated with" lines or
  co-author trailers for tools. You're the author and you own the change.
- **Show it works.** Say how you tested it. For anything visible in the
  terminal, include a before-and-after capture.
- **Small and focused.** One idea per pull request. The title follows the same
  Conventional Commits format as a commit subject.

The template in `.github/pull_request_template.md` keeps this short.

## Before you push

```bash
cargo xtask qa         # fmt, clippy -D warnings, unit and end-to-end tests
cargo xtask qa --live  # needs NVIDIA_API_KEY: live tests, terminal checks, evals
cargo xtask eval TASK  # one eval (or a comma-separated list, or multi)
cargo xtask tty        # terminal UI changes: real-terminal checks, no key needed
```

## Documentation follows behavior

Use the [ordered user guide](docs/guide/README.md) and its
[source-area map](docs/guide/reference.md) when changing user-facing behavior.
Update the relevant section plus executable examples/contracts in the same PR.
A refactor with no behavior change should leave a short check/evidence note in
that section and any mapped deep reference instead of inventing a user-visible
change. Name the invariant and actual check; do not make a whitespace-only edit
to satisfy the coverage guard. `AGENTS.md` is the
shared repository instruction; there is no second duplicated policy to drift.

Run `python3 scripts/check-docs.py --base origin/main`,
`python3 scripts/check-docs.py --self-test`, and
`cargo test --locked --test documentation` in addition to the existing QA gate.
The contract test exercises the actual built CLI, not a copied implementation.
CI also checks navigation and source-area documentation coverage. These checks
cannot prove prose semantics or native visual quality; review both.

After a UI audit, rerun affected demos against the frozen audited build and
inspect raw playback before replacing public media. Record the source revision,
binary hash, dimensions, provider type and observed result. Preserve historical
provenance and name any pending native/authentication/resource checks.
