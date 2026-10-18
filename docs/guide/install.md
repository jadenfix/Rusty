# 1. Install and verify

You need Git, a Rust toolchain with Cargo, and a native linker/build environment.
Check `git --version`, `rustc --version` and `cargo --version` before starting.
Use your platform's Rust installation instructions if a command is missing.
The documented distribution route is a source build; the commands below do not
assume a published release archive exists.

```sh
git clone https://github.com/jadenfix/rusty
cd rusty
cargo install --locked --path .
command -v rusty
rusty --version
rusty --help
rusty --capabilities
```

Cargo normally installs into `~/.cargo/bin`; a custom `CARGO_HOME` or install
root changes that destination. Add the actual bin directory to PATH if
`command -v rusty` fails, then open a new shell. If another installation comes
first on PATH, run your intended executable by absolute path. `--version` is a
package version, not proof of a particular source commit. For a source build,
record `git rev-parse HEAD` alongside the executable's SHA-256 (`shasum -a 256`
on macOS or `sha256sum` on Linux).

## A reproducible update

Finish or stop work and preserve the current executable before replacing it.
Choose the revision you intend to install, inspect local Git changes before
switching it, then run `cargo install --locked --path . --force`. Record the
new source revision and hash. Already running CLI processes keep their loaded
executable: quit and relaunch, then check the launch path. Companion processes
have their own lifecycle; see [data and resources](data.md).

To try a build without replacing your normal command, use
`cargo install --locked --path . --root /absolute/path/to/trial` and launch
`/absolute/path/to/trial/bin/rusty`. Use a separate `RUSTY_HOME` for trial
preferences and sessions. A separate home does not by itself disable provider
traffic or isolate a shell command from your machine.

Keep your old executable and configuration backup until the new build passes
[your lifecycle check](audit.md). Restore the old executable to roll back; do
not delete saved sessions as part of an executable rollback. An older build
may not understand newer saved data, so preserve a backup rather than assuming
backward compatibility.

## First launch

Run `rusty` inside the project you want it to work on. Without credentials it
prints setup guidance. Configure one provider using the [next guide](configure.md),
then use `/settings` and `/model` to inspect the actual session. Start in an
ordinary project directory before trying cloud tools or automation.

Check: the intended executable is on PATH, its source/hash is recorded, startup
opens in the intended project, and a restart launches the same intended build.
