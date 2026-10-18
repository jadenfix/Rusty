# 5. Connect repositories and tools

Model login and repository access are separate. A working Codex or NVIDIA response
does not establish a GitHub account or connect an MCP server. The
[deep integration guide](../INTEGRATIONS.md) covers host detection, remote targets,
credential handling and troubleshooting.

## Inspect before connecting

Run these inside the intended repository; no model credential is needed:

```sh
rusty --integrations
rusty --integrations git status
rusty --integrations setup github
```

Status reports the selected host, repository and remote. It explicitly says
**Authentication not checked**. Setup prints instructions; it does not log you in.
GitHub uses `gh`, GitLab uses `glab`, and Git uses your existing SSH or HTTPS
credentials. Follow the printed login instructions yourself, then explicitly run:

```sh
rusty --integrations check
rusty --integrations prs
```

These contact the host; the review list is limited to 20 open PRs or merge
requests. Inside Rusty, use `/integrations` with the same subcommands and
`/git status`, `/git diff` or `/git log`. The native Git views are read-only.
Repository writes, PR creation and merges still use permission-checked agent tools.

## Choose the right project and remote

For a fork, select the upstream remote explicitly if that is where reviews live:

```sh
rusty --integrations configure github upstream
```

For an enterprise GitLab hostname, use `configure gitlab upstream`. Configuration
saves only the provider and remote for this project, with no credentials. Run
status again in a new process to check persistence. `configure auto origin`
restores host detection for origin. SSH aliases are not expanded; unfamiliar
enterprise names need an explicit provider. Bitbucket support is for Cloud, with
credential options described in the deep guide; Data Center is unsupported.

With a remote tools backend, Git and native host CLIs use the remote machine's
state. Bitbucket HTTP runs on the controller. Credentials are not transferred for
you. Return to the main chat before changing project configuration from a side
chat.

## Add a stdio MCP server deliberately

Start by listing configuration; listing does not execute a server:

```sh
rusty --integrations setup mcp
rusty --integrations mcp list
rusty --integrations mcp add example -- /absolute/path/to/server 'argument with spaces'
rusty --integrations mcp check
rusty --integrations mcp remove example
```

Replace the example executable with a server you trust before checking. Add saves
an optional server in `.mcp.json`, or `RUSTY_MCP_CONFIG` when set. It starts on an
explicit check or the next session. Existing sessions do not reload configuration.
The CLI form preserves arguments containing spaces. `--env NAME` stores an
environment reference, not its value; make that variable available when the server
starts. List hides environment values and does not establish authentication.

`integrations mcp check` fails for any disconnected configured server, including
optional ones. The older `--mcp-check` enforces required servers and required tools;
its success can coexist with an optional failure. Direct HTTP transport, OAuth,
resources and prompts are not implied by this stdio tools client. An explicitly
configured stdio bridge can provide its own connection behavior.

MCP requests have bounded frames and deadlines; notifications do not keep a
request alive forever. A lost connection after sending a tool call can leave
its effects unknown. Inspect the external system before retrying an action.
Trajectory records distinguish `not_started`, `settled` (a matching response,
including an invalid body) and `unknown` (sent without a matching response).
`settled` therefore does not mean the tool succeeded. These private outcome tags
are omitted from provider messages, and totals appear in `mcp_outcomes` in an
export. They are observations, not a durable recovery protocol. See
[verification and resource limits](../VERIFICATION.md) for the exact bounds.

Check: status names the intended remote, an explicit access check succeeds when
needed, and a server's tools are actually available after restarting the session.
Keep model response proof, host access proof and MCP health proof separate.
Continue with [Quit and return](sessions.md).
