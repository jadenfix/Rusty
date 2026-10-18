# Lifecycle acceptance checklist

Run against one frozen source revision and executable hash. Record a separate
result for each row; do not carry a pass from an older binary to a new build.

| Stage | Journey and evidence |
|---|---|
| Acquire/install | Fresh documented download/source checkout, prerequisites, install, PATH resolution, source/hash and rollback copy |
| First open | No credentials, configured credentials, invalid credential, explicit provider, readable recovery |
| Configure | Skin/background pairing, compact font, saved/reapplied values, environment overrides, wrong/unwritable config |
| Use | Small real prompt on the intended provider, output/exit, direct shell without a model call, approval then cancellation |
| Manipulate UI | Wide/narrow/short panes; grow/shrink with completion open and while streaming; scroll and switch panes; light/dark/NO_COLOR |
| Input | Unicode, multiline/bracketed paste, unsent busy draft, queued follow-up, Ctrl-U, Ctrl-C, review before resending |
| Work surfaces | Modes/views/permissions independently; side/main ownership, active jobs, stop/redirect, explicit verification |
| Quit | `/exit` and aliases, Ctrl-D, repeated idle Ctrl-C and rapid active-work double Ctrl-C; no duplicate command or stray cursor below the editor |
| Return | New process, recent preview, no replay/model call on load, continued context, fresh session and `/new` separation |
| Unexpected close | Close after completed turn and during stream/tool; inspect partial state before repeat |
| Never return | Owned child/service/FD cleanup, data retained intentionally, uninstall and credential/data removal kept separate |
| Constraints | Long history, huge bounded output/paste, read-only/corrupt storage, actual full-volume and RAM-cap failure where supported |

## Evidence levels

- Documentation contract tests check accepted options, command discovery,
  linked pages and selected persistence/session behavior through the real binary.
- Offline PTYs exercise terminal control and a deterministic mock provider.
- Native cmux checks inspect pixels and interaction in the actual emulator.
- Real provider checks establish observed sign-in/routing/response for that run.
- Resource-failure checks must name the actual enforced limit and recovery result.

None alone proves the others. Mark unsupported environments or unexecuted rows
as pending rather than passing. An OOM simulation that the OS refuses is not an
OOM test. A file-size limit is not a truly full disk. A service disabled for a
run does not prove default service shutdown. Human IME, screen-reader and
accessibility behavior need their own checks.

The historical live demo manifest and lifecycle recordings have their own
source receipts. Update a recording only after inspecting raw playback,
asserted outcomes and the resulting project state. See [demo instructions](../demo/README.md).
