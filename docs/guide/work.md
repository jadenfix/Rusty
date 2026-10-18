# 4. Work and verify

Start with `/settings`, `/target` and the intended project path. A task's request,
execution profile, display view and permission policy answer different questions.

| Control | What it changes |
|---|---|
| `/mode auto`, `careful`, `standard`, `vibe` | How work is planned, checked and delegated |
| `/view default`, `verbose`, `adhd` | How much output you see |
| `/permissions read-only`, `ask`, `auto`, `yolo` | Whether tools are allowed to act or need confirmation |
| `/agents off`, `sub`, `swarm`, `auto` | Delegation policy |

A quieter view or Vibe profile does not make editing read-only. Careful adds
checking, not a guarantee of correctness. In Auto, inspect the selected profile
and reason; ambiguous language can be classified incorrectly. Override the mode
when you know the intended level of care. Read-only workers report findings;
the lead decides on edits. Workers consume requests/tokens too.

## Direct commands and approvals

Type `!pwd` to run a direct command without a model request. It still uses the
permission and execution infrastructure, shows output/exit status, and can be
stopped with Ctrl-C. Treat `!` as real shell access to the configured workspace,
not a sandbox or an agent explanation. Use `/back` before running it from a side
discussion. Read a command's target before approving it; permissions and target
classification are not operating-system isolation.

Use `/permissions check <command>` to preview classification without executing
it. Deny rules and destructive-operation confirmation still matter in Yolo.
Changing a profile or visibility setting does not grant a command permission.

## A task with an explicit check

For a bounded local repair, pin an acceptance command:

```sh
rusty --goal 'fix the failing tests' --verify 'cargo test' --verify-timeout 120 --max-requests 32
```

The check obeys permissions. A failed, interrupted, denied or timed-out check
keeps a verified goal open; an unfinished verified goal exits 2, interruption
130. A passing check establishes what that check covers, not every unstated
requirement. Keep a critical checker outside editable source or use inline
assertions when checker integrity matters. [Verification details](../VERIFICATION.md)
cover hashes, receipts and goal completion. `/goal status`, `/goal resume` and
`/goal clear` manage the current goal; stopping the process is not proof it finished.

`--max-requests`, `--max-budget-tokens` and `--budget-secs` opt into bounded
provider work. They do not cap OS memory or disk; token admission is not an
exact dollar billing cap and provider time is not a universal tool deadline.
Use `--stats` or `--trajectory <path>` for evidence, and understand their saved-data
implications before sharing.

## Other work surfaces

Use `/btw <question>` for an aside from existing context. `/side` opens persistent
side discussions, `/send` shares selected findings with the main chat, and
`/back` returns. Side history and main history have different ownership; opening
a side discussion is not the same as creating a fresh main conversation.
`/help` is the command catalog for your build. Inspect active work before exiting
or switching context; a hidden view is not evidence that no job is running.

Skills supply task instructions; project instruction files include `AGENTS.md`,
`RUSTY.md` and `CLAUDE.md`. MCP tools come from configured stdio servers; inspect
`rusty --mcp-check` before depending on them. A missing required tool stops startup,
while optional broken servers can be skipped with a warning. Cloud tools require
separate setup: [cloud](../CLOUD.md), [infrastructure](../INFRA.md).

Check: the intended target and policy are visible, work produces inspectable
changes, the acceptance check ran, and failures are not mistaken for success.

For repository host setup, project remotes and MCP management, continue with
[Connect repositories and tools](integrations.md).
