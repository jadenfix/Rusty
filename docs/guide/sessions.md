# 6. Quit and return

A session is saved conversation context, not a saved running process. Resuming
does not revive a shell child, roll back changes, or prove the last task finished.

## Normal exit and return

Use `/exit` (aliases `/quit` and `/q`), Ctrl-D on empty input, or the second idle
Ctrl-C. A session containing work prints a `rusty -c <id>` resume hint. Record
that ID if you want a particular conversation rather than whichever is latest.

```sh
rusty --sessions
rusty --sessions 'parser'
rusty -c
rusty -c 3f9a12c0
```

The example ID is illustrative: replace it with one printed by your session
list. Resume is project-local: return to the same project path and tool/backend
identity. A renamed directory, different worktree, or different remote context
can have a different session namespace. A missing session does not imply the
files were deleted. Search/list in the original project before changing data.

Interactive resume shows a short, terminal-sized preview of recent requests
and replies. The preview is an excerpt, not the whole history; absence from the
screen does not mean absence from the model context. Loading it does not send an inference request or replay prior shell commands.
Normal startup can still query a compatible/OpenAI endpoint for its model
catalog to discover context size, unless `--context-tokens` is supplied. A follow-up can use the saved
history. Concurrent writers are locked; use a separate fresh conversation if
a session is already open elsewhere.

## Start over without destroying history

A plain `rusty` launch starts a new conversation. `/new` or `/clear` clears
conversation context within the current process while keeping saved memories.
Those commands do not undo edits or delete the earlier transcript. They also
do not mean every current runtime option was reset to startup defaults.
Use `/resume` to browse/search or `/resume <id>` to load another saved conversation.

## Unexpected closure

After a terminal closes, reopen the same project and inspect saved sessions.
Completed turns can be resumed, but an abrupt closure during streaming or a
tool action may leave partial history or an operation still affecting the world.
Check files, processes and remote state before repeating a command. Treat unsent
text as a draft, not a guaranteed durable message; do not assume it survives
terminal closure. Preserve a damaged transcript before trying recovery.

If you leave permanently, saved transcripts, memory, configuration and credentials
remain until deliberately removed. Uninstalling the executable is a separate
operation. See [data and resources](data.md) before deleting anything.

Check: normal exit prints a usable hint, reopening shows the expected preview,
fresh launches do not inherit the old conversation, and failed resume gives a
readable diagnostic without silently selecting a different task.
