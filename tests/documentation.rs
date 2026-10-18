//! User-facing documentation contracts; no credentials or external endpoint.
mod support;

use serde_json::Value;
use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Output, Stdio};
use std::sync::{Arc, Mutex};
use std::time::Duration;

fn contract() -> Value {
    serde_json::from_str(include_str!("../docs/examples/contract.json")).unwrap()
}

struct Trial {
    root: support::TempDir,
    project: PathBuf,
}

impl Trial {
    fn new() -> Self {
        let root = support::TempDir::new("documentation");
        let project = root.path().join("project");
        std::fs::create_dir_all(&project).unwrap();
        Self { root, project }
    }

    fn cmd(&self) -> Command {
        let mut cmd = Command::new(support::RUSTY);
        cmd.env_clear()
            .env("PATH", "/usr/bin:/bin")
            .env("HOME", self.root.path().join("user"))
            .env("CODEX_HOME", self.root.path().join("codex"))
            .env("RUSTY_HOME", self.root.path().join("home"))
            .env("RUSTY_NO_DOTENV", "1")
            .env("RUSTY_INFRA", "off")
            .env("RUSTY_CONTEXT_TOKENS", "128000")
            .env("RUSTY_PROVIDER", "compatible")
            .env("NVIDIA_API_KEY", "offline-documentation-test")
            .env("RUSTY_BASE_URL", "http://127.0.0.1:1/v1")
            .env("RUSTY_RETRY_SECS", "0")
            .env("NO_COLOR", "1")
            .args(["--memory", "off", "--agents", "off"])
            .current_dir(&self.project)
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());
        cmd
    }

    fn run(&self, args: &[&str], input: Option<&str>, endpoint: Option<&str>) -> Output {
        let mut cmd = self.cmd();
        cmd.args(args);
        if let Some(url) = endpoint {
            cmd.env("RUSTY_BASE_URL", url);
        }
        if input.is_some() {
            cmd.stdin(Stdio::piped());
        }
        let mut child = cmd.spawn().unwrap();
        if let Some(text) = input {
            child.stdin.take().unwrap().write_all(text.as_bytes()).unwrap();
        }
        let out = support::wait(child, Duration::from_secs(15));
        assert!(out.status.success(), "{}", String::from_utf8_lossy(&out.stderr));
        out
    }
}

#[test]
fn documented_flags_commands_and_capabilities_match_the_binary() {
    let trial = Trial::new();
    let expected = contract();
    let output = trial.run(&["--capabilities"], None, None);
    let mut actual: Value = serde_json::from_slice(&output.stdout).unwrap();
    actual.as_object_mut().unwrap().remove("version");
    assert_eq!(actual, expected["capabilities"], "update the guide and its contract when capabilities change");
    let help = trial.run(&["--help"], None, None);
    let help = String::from_utf8_lossy(&help.stdout);
    for flag in expected["cli_flags"].as_array().unwrap() {
        assert!(help.contains(flag.as_str().unwrap()), "documented flag missing from --help: {flag}");
    }
    let help = trial.run(&[], Some("/help\n/exit\n"), None);
    let help = String::from_utf8_lossy(&help.stdout);
    for cmd in expected["commands"].as_array().unwrap() {
        let name = cmd.as_str().unwrap();
        assert!(help.split_whitespace().any(|word| word == name), "documented command missing from /help: {name}");
    }
}

#[test]
fn configuration_walkthrough_persists_preferences_but_not_session_policy() {
    let trial = Trial::new();
    let spec = &contract()["configure"];
    let lines = spec["lines"].as_array().unwrap().iter().map(|s| s.as_str().unwrap()).collect::<Vec<_>>();
    trial.run(&[], Some(&(lines.join("\n") + "\n")), None);
    let saved: Value =
        serde_json::from_slice(&std::fs::read(trial.root.path().join("home/settings.json")).unwrap()).unwrap();
    for (key, value) in spec["saved"].as_object().unwrap() {
        assert_eq!(&saved[key], value, "walkthrough did not save {key}");
    }
    for key in spec["not_saved"].as_array().unwrap() {
        assert!(saved.get(key.as_str().unwrap()).is_none(), "guide says {key} is not a preference");
    }
    let restarted = trial.run(&[], Some("/settings\n/exit\n"), None);
    let restarted = String::from_utf8_lossy(&restarted.stdout);
    for value in ["neon", "compact", "verbose"] {
        assert!(restarted.contains(value), "preference not reapplied after restart: {value}");
    }
    assert!(restarted.contains("permissions     auto"), "a session-only policy unexpectedly persisted: {restarted}");
}

#[test]
fn direct_command_walkthrough_uses_the_project_without_a_model_request() {
    let trial = Trial::new();
    let requests = Arc::new(Mutex::new(0usize));
    let seen = requests.clone();
    let server = support::serve(Arc::new(move |_| {
        *seen.lock().unwrap() += 1;
        support::reply(0, None, "unexpected model request")
    }));
    let endpoint = format!("{}/v1", server.url);
    let output = trial.run(&[], Some("!pwd\n/exit\n"), Some(&endpoint));
    let text = String::from_utf8_lossy(&output.stdout);
    let expected = std::fs::canonicalize(&trial.project).unwrap();
    assert!(text.contains(expected.to_str().unwrap()), "{text}");
    assert_eq!(*requests.lock().unwrap(), 0, "the documented direct command must not ask a model");
}

#[test]
fn resume_walkthrough_keeps_context_without_replaying_and_new_starts_fresh() {
    let trial = Trial::new();
    let requests = Arc::new(Mutex::new(Vec::<Value>::new()));
    let seen = requests.clone();
    let server = support::serve(Arc::new(move |request| {
        seen.lock().unwrap().push(request.json());
        support::reply(0, None, &("DOCUMENTED_REPLY".to_owned() + &"x".repeat(128 * 1024)))
    }));
    let endpoint = format!("{}/v1", server.url);
    trial.run(&["--mode", "standard", "DOCUMENTED_FIRST"], None, Some(&endpoint));
    assert_eq!(requests.lock().unwrap().len(), 1);
    // Session filenames remain .json even when the on-disk content is gzip.
    fn compressed_transcripts(dir: &std::path::Path) -> usize {
        std::fs::read_dir(dir)
            .unwrap()
            .map(|entry| {
                let path = entry.unwrap().path();
                if path.is_dir() {
                    compressed_transcripts(&path)
                } else if path.extension().is_some_and(|ext| ext == "json") {
                    usize::from(std::fs::read(path).unwrap().starts_with(&[0x1f, 0x8b]))
                } else {
                    0
                }
            })
            .sum()
    }
    assert_eq!(compressed_transcripts(&trial.root.path().join("home")), 1);
    let resumed = trial.run(&["-c"], None, Some(&endpoint));
    let resumed = String::from_utf8_lossy(&resumed.stdout);
    assert!(resumed.contains("DOCUMENTED_FIRST") && resumed.contains("DOCUMENTED_REPLY"), "{resumed}");
    assert_eq!(requests.lock().unwrap().len(), 1, "loading a session must not request a model response");
    trial.run(&["--mode", "standard", "-c", "latest", "DOCUMENTED_FOLLOWUP"], None, Some(&endpoint));
    let history = requests.lock().unwrap()[1]["messages"].to_string();
    assert!(history.contains("DOCUMENTED_FIRST") && history.contains("DOCUMENTED_REPLY"));
    trial.run(&["--mode", "standard", "DOCUMENTED_FRESH"], None, Some(&endpoint));
    assert!(!requests.lock().unwrap()[2]["messages"].to_string().contains("DOCUMENTED_FIRST"));
    let cleared = trial.run(&[], Some("/new\n/exit\n"), None);
    assert!(String::from_utf8_lossy(&cleared.stdout).contains("fresh context"));
    for alias in ["/exit", "/quit", "/q"] {
        trial.run(&[], Some(&format!("{alias}\n")), None);
    }
}

#[test]
fn reference_tables_and_appearance_choices_are_executable() {
    let spec = contract();
    let guide = include_str!("../docs/guide/reference.md");
    let rows = [
        ("Execution", "mode"),
        ("Permissions", "permissions"),
        ("Delegation", "agents"),
        ("Memory", "memory"),
        ("Compaction", "compaction"),
        ("Tool location", "tools"),
        ("Toolset", "toolset"),
        ("View", "view"),
        ("Theme", "theme"),
        ("Banner font", "font"),
    ];
    for (label, key) in rows {
        let row = guide.lines().find(|line| line.starts_with(&format!("| {label} |"))).expect("reference table row");
        let documented: Vec<_> = row.split('`').enumerate().filter(|(n, _)| n % 2 == 1).map(|(_, v)| v).collect();
        let values = spec["capabilities"].get(key).unwrap_or(&spec["appearance"][key]);
        let expected: Vec<_> = values.as_array().unwrap().iter().map(|v| v.as_str().unwrap()).collect();
        assert_eq!(documented, expected, "reference table drift: {label}");
    }
    let trial = Trial::new();
    for (setting, values) in spec["appearance"].as_object().unwrap() {
        for value in values.as_array().unwrap() {
            let value = value.as_str().unwrap();
            trial.run(&[], Some(&format!("/{setting} {value}\n/exit\n")), None);
            let saved: Value =
                serde_json::from_slice(&std::fs::read(trial.root.path().join("home/settings.json")).unwrap()).unwrap();
            assert_eq!(saved[setting], value, "documented appearance choice rejected: {setting} {value}");
        }
    }
}

#[test]
fn integration_walkthrough_is_keyless_and_keeps_project_remote_selection() {
    let trial = Trial::new();
    for args in [
        vec!["init", "-q"],
        vec!["remote", "add", "origin", "https://github.com/example/project.git"],
        vec!["remote", "add", "upstream", "https://gitlab.example.test/team/project.git"],
    ] {
        let output = Command::new("git")
            .env_clear()
            .env("PATH", "/usr/bin:/bin")
            .env("HOME", trial.root.path().join("user"))
            .env("GIT_CONFIG_NOSYSTEM", "1")
            .current_dir(&trial.project)
            .args(args)
            .output()
            .unwrap();
        assert!(output.status.success(), "{}", String::from_utf8_lossy(&output.stderr));
    }
    let run = |args: &[&str]| {
        let mut cmd = trial.cmd();
        cmd.env_remove("NVIDIA_API_KEY").args(["--integrations"]).args(args);
        let output = support::wait(cmd.spawn().unwrap(), Duration::from_secs(15));
        assert!(output.status.success(), "{}", String::from_utf8_lossy(&output.stderr));
        String::from_utf8(output.stdout).unwrap()
    };
    let status = run(&[]);
    assert!(status.contains("github: github.com/example/project"), "{status}");
    assert!(status.contains("Authentication not checked"), "{status}");
    assert!(run(&["setup", "github"]).contains("gh auth login"));
    assert!(run(&["configure", "gitlab", "upstream"]).contains("no credentials stored"));
    let restarted = run(&["status"]);
    assert!(restarted.contains("gitlab: gitlab.example.test/team/project"), "{restarted}");
    assert!(restarted.contains("remote: upstream"), "{restarted}");
    assert!(run(&["setup", "gitlab"]).contains("gitlab.example.test"));
    let listed: Value = serde_json::from_str(&run(&["mcp", "list"])).unwrap();
    assert_eq!(listed, serde_json::json!({"servers":[]}));
    assert!(!trial.project.join(".mcp.json").exists(), "listing must not create configuration");
    run(&["configure", "auto", "origin"]);
    assert!(run(&["status"]).contains("github: github.com/example/project"));
}
