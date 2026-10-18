# 8. Recover by symptom

| Symptom | First useful check |
|---|---|
| `rusty` not found | `command -v rusty`; inspect the actual Cargo install bin directory and PATH |
| Old UI after update | Check executable path/hash, then fully quit and relaunch the CLI process |
| No key / login required | Review credential precedence and explicitly select the intended provider |
| Credentials saved but requests fail | Inspect provider/model/base URL and HTTP error; use `/doctor`; a saved token is not response proof |
| HTTP 404 | Check the endpoint and provider/model routing before assuming authentication failed |
| Unexpected provider | Pin `RUSTY_PROVIDER`, inspect `/model` and status, and account for shell variables overriding dotenv |
| Skin hard to read | Pair `paper` with a light terminal or `rust` with a dark one; test `NO_COLOR=1` |
| Hidden/stale prompt after resize | Return to the input, finish/dismiss completion, test another pane size, and capture the exact reproduction |
| Cannot edit busy text like idle text | Busy draft controls are limited; review the [input guide](terminal.md) |
| Command seems stuck | Read active operation/retry/approval state; elapsed time alone is not failure or success |
| Preference reverts | Restart and inspect `/settings`; check writable home, valid JSON and free space |
| Missing resumed conversation | Return to its original project path/backend, list/search there, and inspect the resume ID |
| Session already in use | Keep the owning process intact; open a new conversation or close the original deliberately |
| Goal stopped but not finished | Inspect goal/verification status and exit code; check what actually ran before resuming |
| Terminal closed mid-command | Inspect files, child processes and external state before repeating a potentially effectful command |

For a useful bug report include source revision, executable hash, OS/terminal,
rows/columns, skin/background, color mode, exact keystrokes, expected/observed
behavior, exit status and a sanitized capture. State whether the provider was
real or mocked, and whether the problem occurs with a fresh isolated home.
Do not attach tokens, `.env`, Codex auth or an unreviewed transcript.

Keep the failing saved data unchanged when possible. A renamed configuration
backup is safer evidence than deleting it and losing the reproducer. A passing
unit test does not settle an unresolved native repaint bug; share both results.
