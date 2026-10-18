# 3. Read and control the terminal

Rusty uses normal terminal scrollback and inherits the terminal background.
Terminal emulators and cmux control window chrome, background, font size and
scrollback; Rusty controls text roles, its banner and input. Applying a Rusty
skin does not rewrite global cmux or Ghostty settings.

## Match the skin to the terminal

Use `/theme rust` with a dark background, `/theme paper` with a light background,
or `/theme mono` for monochrome. Other skins are `neon`, `matrix`, `amber` and
`ice`. [Terminal presets](../themes/README.md) explain the matching Ghostty/cmux
settings. Merge presets with your existing terminal config and keep a backup.
Use `/font compact` for a short header; `rust`, `block`, `thin` and `classic`
select larger banner styles, not the emulator's font size.

Input, warning, success and error have separate roles. Read the words and exit
codes as well as color. `NO_COLOR=1 rusty` removes styling for accessibility or
capture. Narrow headers can clip supplementary metadata; use `/settings`,
`/model` and `/target` for full values. Resize a pane while the menu is open and
while output is streaming, then confirm the draft remains visible and editable.
A blank/stale completion region is a UI defect, not evidence work is still running.

## Input and menus

At idle, type `/` to open completion. Type more to filter, use Up/Down to select,
Tab or Right to complete, and Enter to submit. Commands requiring arguments can
first fill the editor rather than execute. Read the editor after completion;
Enter is not always an immediate action. Accepted aliases can differ from menu
entries on older builds; `/exit` is the canonical quit command.

Paste is different from manually typing: bracketed paste keeps multiline text
as one draft. Inspect it before submission. Entered shell syntax in a normal
message is sent to the model; prefix a line with `!` for direct shell execution.

## While work runs

The progress row identifies the operation and elapsed time. A busy draft lets
you prepare a follow-up: Backspace edits, Ctrl-U clears, and Enter queues it.
Unsent text returns to the ordinary editor when work finishes. Busy editing is
simpler than idle editing: do not assume idle arrow navigation or cursor controls
work identically. Multiple queued entries may be combined into one follow-up;
they are not independent concurrent model turns. Review queued text after an
interruption before sending it again.

Ctrl-C stops the active work. At idle, a second Ctrl-C quits; Ctrl-D on an empty
input also exits. A second rapid Ctrl-C during active work can force-close the process with
status 130 before normal post-turn saving completes. Cancellation is not rollback: a command may already have
changed files or contacted a service. Review `/changes`, Git diff and the target
system as appropriate. Retry status means waiting, not completion; error and
verification messages remain relevant even if the progress line changes.

In cmux, try a narrow split, a wide pane, scrolling away and back, and switching
panes while streaming. Scrollback navigation is controlled by the terminal.
A native visual check is needed for repaint bugs that a text-only test misses.
See the [audit checklist](audit.md) for the full manipulation matrix.

Check: input stays readable in both widths, error labels work without color,
you can keep an unsent draft during work, and completion leaves a usable prompt.
