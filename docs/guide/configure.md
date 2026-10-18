# 2. Configure and connect

Rusty preferences, provider credentials and Codex configuration are separate.
Use `/settings` to inspect the running session, `/model` to inspect its model,
and `/doctor` to probe configured providers. Provider probes may access the
network; a saved credential alone does not prove a successful model response.

## Credentials and provider choice

Keys are loaded from the shell first, then `$RUSTY_HOME/.env` (normally
`~/.config/rusty/.env`), then the `.env` beside the source crate used to build
Rusty. Existing shell values win. Set `RUSTY_NO_DOTENV=1` to skip both dotenv
files. Do not commit keys or put them in command-line arguments.

Compatible/NVIDIA uses `NVIDIA_API_KEY` (or `RUSTY_API_KEY`), Anthropic uses
`ANTHROPIC_API_KEY`, and OpenAI uses `OPENAI_API_KEY`. `RUSTY_BASE_URL` selects a
compatible endpoint. With multiple configured providers, automatic default
selection tries compatible, Anthropic, OpenAI, then saved Codex sign-in. Pin
`RUSTY_PROVIDER` if that ordering is not what you intend.

For a Codex session, install and sign in with the Codex CLI using `codex login`,
then launch `RUSTY_PROVIDER=codex rusty`. Rusty reads the saved Codex sign-in;
a question typed into Rusty asking how to log in does not itself sign you in.
Do not publish credential files or enter tokens into a chat transcript.

A model name can influence provider routing: bare Claude names select Anthropic,
bare GPT/o-series names select OpenAI, and slash-qualified names use the
compatible provider. `RUSTY_PROVIDER` overrides that inference. An OpenAI model
may use Codex sign-in when there is no OpenAI API key. Inspect the displayed
provider instead of treating the model name as connection proof.

Model selection at startup uses `--model` / `RUSTY_MODEL` first, then an
explicit profile's `RUSTY_CAREFUL_MODEL`, `RUSTY_STANDARD_MODEL` or
`RUSTY_VIBE_MODEL`, then the default model of the selected/configured provider.
Check both model and provider after changing either layer.

## Connection labels

The idle status distinguishes configured credentials/unverified state from
an observed successful response or failure. A previous successful request is
not a health guarantee for the next one. `/doctor` probes providers;
`/models` or `--list-models` can contact endpoints. For a meaningful login
check, send one small prompt and verify a response under the intended provider.

## What persists

| Setting | How to change it | Scope |
|---|---|---|
| Theme, font, view, tips | `/theme`, `/font`, `/view`, `/tips` | Rusty preferences, saved for later launches |
| Execution/delegation defaults | `/mode`, `/agents`, `/swarm` | Saved preferences; explicit flags/environment can override |
| Tool location | `/tools local`, `/tools daytona`, `/tools ssh` | Saved default for the next session; remote choices require their bridge launcher |
| Current model | `/model <id>` or `--model` | Current session; inspect again after restarting |
| Permissions | `/permissions <mode>` or `--permissions` | Current policy; do not infer persistence from `/settings` |
| Codex default model | `/codex model <id>` | Shared Codex config, also applied here when routed to Codex |
| Full Codex config | `/codex config` | External editor; other settings apply on restart |

Rusty stores preferences in `settings.json` under `RUSTY_HOME`; it is not
Codex's `config.toml`. `/settings` displays runtime values as well as preferences,
so its output is not a complete promise of what survives restart. The Codex
editor uses the configured editor and may affect other applications sharing
that configuration. Use `/codex models` for cached names; absence from that
cache is not proof a provider cannot serve a model.

After changing a preference, quit, relaunch and inspect `/settings`. If it
reverts, check directory permissions, free space and JSON validity. This build
falls back to default preferences when the settings file cannot be read or
parsed; preserve that file before repairing it. Do not
assume a confirmation line alone proves a durable save; audited persistence
failure behavior must be checked on the build you are using.

Check: provider, model and credential source are understood; one real response
works when desired; saved appearance survives restarting; session-only options
are set explicitly when they matter.
