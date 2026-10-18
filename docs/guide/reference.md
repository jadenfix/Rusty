# 9. Reference and documentation checks

`rusty --help` gives this binary's flags. `/help` gives its interactive command
catalog. `rusty --capabilities` prints accepted values as JSON without requiring
credentials; use it before scripting against a build. Runtime output wins over
an old screenshot or a guide for a different revision.

The checked [documentation contract](../examples/contract.json) records the
capability contract, documented flags/commands and one configuration walkthrough.
`tests/documentation.rs` compares it with the actual built binary, verifies
keyless integration setup and project-specific remote persistence, preference persistence across processes, and checks no-request resume, follow-up
context and fresh-session isolation using a local provider. These are executable
examples, not a substitute for native UI or real-authentication checks.

```sh
cargo test --locked --test documentation
python3 scripts/check-docs.py
python3 scripts/record-lifecycle.py --self-test
cargo xtask qa
```

The Python check validates guide presence, links and heading anchors. It also requires a guide mapping for every source module. In CI it maps
changed user-facing source areas to their guides and existing deep references. To run that check locally:

```sh
python3 scripts/check-docs.py --base origin/main
```

A source change touching a mapped area must update its guide in the same PR,
including relevant example/evidence changes. This is a review reminder, not proof
that the prose is accurate. When behavior intentionally stays the same, add a
short evidence note to the relevant guide explaining what was checked. Do not
silence drift by changing expected values without checking user-visible behavior.

## Accepted settings

| Surface | Values |
|---|---|
| Execution | `auto`, `careful`, `standard`, `vibe` |
| Permissions | `read-only`, `ask`, `auto`, `yolo` |
| Delegation | `off`, `sub`, `swarm`, `auto` |
| Memory | `off`, `recall`, `learn`, `reflect`, `deep` |
| Compaction | `aggressive`, `standard`, `passive`, `smart` |
| Tool location | `local`, `daytona` |
| Toolset | `full`, `shell` |
| View | `default`, `verbose`, `adhd` |
| Theme | `rust`, `neon`, `matrix`, `amber`, `ice`, `mono`, `paper` |
| Banner font | `compact`, `rust`, `block`, `thin`, `classic` |

Some surfaces accept additional subcommands: use the menu or `/help` for syntax.
Keep configuration policy distinct from live endpoint availability: no static
list here guarantees a model or remote tool is available to your account.

## Maintainer map

| Source area | Guide to review |
|---|---|
| Cargo/package/distribution | [Install](install.md) |
| Provider/auth/config/doctor | [Configure](configure.md) |
| Theme/editor/footer/completion/signal/display/markdown | [Terminal](terminal.md) |
| Agent/tools/permissions/execution/verification/budget | [Work](work.md) |
| Repository hosts, remotes and MCP | [Integrations](integrations.md) and the [deep guide](../INTEGRATIONS.md) |
| Session/backend/main lifecycle | [Sessions](sessions.md) |
| Advisor/memory/privacy/context/storage | [Data](data.md) |
| Cloud, memory service, verification, infrastructure | Their linked deep references as well as the journey guide |

After a UI audit, rerun relevant demos on the frozen candidate and record source,
executable hash, dimensions, terminal, environment, real/mock provider and outcomes.
Do not relabel historical recordings as current. The [audit matrix](audit.md)
contains human checks beyond the contract tests.
