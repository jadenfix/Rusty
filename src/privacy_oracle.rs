//! The redaction code before the single-pass rewrite, kept only to check
//! that the rewrite gives byte-for-byte the same answers.
use super::{is_common_type, split_kv, Expect, REDACTED, SECRET_KEYS, SECRET_PREFIXES};

pub fn redact_by(text: &str, mark: &mut dyn FnMut(&str) -> String) -> (String, usize) {
    let mut lines: Vec<String> = Vec::new();
    let mut count = 0;
    let mut in_pem = false;
    let mut in_secret_data = false;
    let is_secret_object = text.contains("kind: Secret") || text.contains("\"kind\": \"Secret\"");
    for line in text.lines() {
        if in_pem {
            in_pem = !line.contains("-----END");
            continue;
        }
        if line.contains("-----BEGIN") && line.contains("PRIVATE KEY") {
            in_pem = true;
            count += 1;
            lines.push("[redacted private key]".into());
            continue;
        }
        let trimmed = line.trim_start();
        if is_secret_object {
            // Values under `data:` / `stringData:` until the block dedents.
            let indent = line.len() - trimmed.len();
            if matches!(trimmed.trim_end_matches(" {"), "data:" | "stringData:" | "\"data\":" | "\"stringData\":") {
                in_secret_data = true;
                lines.push(line.into());
                continue;
            }
            if in_secret_data && (indent == 0 || trimmed.starts_with('}')) {
                in_secret_data = false;
            }
            if in_secret_data {
                if let Some((k, v)) = split_kv(trimmed) {
                    count += 1;
                    let (v, tail) = match v.strip_suffix(',') {
                        Some(v) => (v, ","),
                        None => (v, ""),
                    };
                    let quoted = v.len() >= 2 && v.starts_with('"') && v.ends_with('"');
                    let v = if quoted { &v[1..v.len() - 1] } else { v };
                    let q = if quoted { "\"" } else { "" };
                    lines.push(format!("{}{k} {q}{}{q}{tail}", &line[..indent], mark(v)));
                    continue;
                }
            }
        }
        let (redacted, n) = redact_line(line, mark);
        count += n;
        lines.push(redacted);
    }
    let mut out = lines.join("\n");
    if text.ends_with('\n') {
        out.push('\n');
    }
    // Also hide actual configured secrets, including providers with unfamiliar
    // token formats. Capture once; inspecting the environment is not a hook cost.
    static SECRETS: std::sync::OnceLock<Vec<String>> = std::sync::OnceLock::new();
    for secret in SECRETS.get_or_init(|| {
        std::env::vars_os()
            .filter_map(|(k, v)| {
                let (k, v) = (k.to_str()?, v.to_str()?);
                (secret_key(k) && v.len() >= 8).then(|| v.to_owned())
            })
            .collect()
    }) {
        if out.contains(secret) {
            count += out.matches(secret).count();
            out = out.replace(secret, REDACTED);
        }
    }
    (out, count)
}

fn redact_line(line: &str, mark: &mut dyn FnMut(&str) -> String) -> (String, usize) {
    let (line, mut count) = redact_urls(line, mark);
    let mut out = String::with_capacity(line.len());
    let mut rest = line.as_str();
    let mut expect: Option<Expect> = None;
    let mut key = "";
    while !rest.is_empty() {
        let start = rest.find(is_token_char).unwrap_or(rest.len());
        let (sep, after) = rest.split_at(start);
        let end = after.find(|c| !is_token_char(c)).unwrap_or(after.len());
        let (token, after) = after.split_at(end);
        rest = after;
        out.push_str(sep);
        if token.is_empty() {
            break;
        }
        let wanted = match expect.take() {
            // `Bearer <api key>` in docs is a placeholder, not a credential.
            Some(Expect::Header) => !sep.is_empty() && sep.trim().is_empty(),
            Some(Expect::Key) => is_assignment(sep),
            Some(Expect::Flag) => is_assignment(sep) || (!sep.is_empty() && sep.trim().is_empty()),
            None => false,
        };
        let prefix_len = line.len() - rest.len() - token.len() - sep.len();
        if (wanted && secret_value(token) && !code_expression(key, sep, token, rest, &line[..prefix_len]))
            || secret_shape(token)
        {
            let padded = rest.trim_start_matches('='); // base64 padding
            let value = &line[line.len() - rest.len() - token.len()..line.len() - padded.len()];
            out.push_str(&mark(value));
            count += 1;
            rest = padded;
            continue;
        }
        out.push_str(token);
        key = token;
        expect = if matches!(token.to_ascii_lowercase().as_str(), "bearer" | "basic") {
            Some(Expect::Header)
        } else if secret_key(token) {
            Some(if token.starts_with("--") { Expect::Flag } else { Expect::Key })
        } else {
            None
        };
    }
    (out, count)
}

pub fn secret_key(key: &str) -> bool {
    let k = key.trim_end_matches(|c: char| c.is_ascii_digit() || c == '_').to_ascii_lowercase();
    // The shell's working-directory variables end in "pwd" but hold paths.
    if matches!(k.as_str(), "pwd" | "oldpwd") {
        return false;
    }
    SECRET_KEYS.iter().any(|s| k.ends_with(s))
}

/// Short values and placeholders are not secrets. `${VAR}` and `<value>`
/// never reach here: `$` and `<` are not token characters, so the
/// assignment check fails on them.
fn secret_value(v: &str) -> bool {
    !v.is_empty() && !matches!(v.to_ascii_lowercase().as_str(), "null" | "none" | "true" | "false" | "changeme")
}

pub fn secret_shape(token: &str) -> bool {
    if token.starts_with("eyJ") {
        // A JWT: three base64url parts.
        return token.split('.').count() == 3 && token.len() > 30;
    }
    SECRET_PREFIXES.iter().any(|p| token.starts_with(p) && token.len() >= p.len() + 12)
}

/// `scheme://user:pass@host` anywhere in the line → `scheme://user:[redacted]@host`.
fn redact_urls(line: &str, mark: &mut dyn FnMut(&str) -> String) -> (String, usize) {
    let mut out = String::with_capacity(line.len());
    let mut count = 0;
    let mut rest = line;
    while let Some(i) = rest.find("://") {
        let scheme_start = rest[..i]
            .char_indices()
            .rfind(|(_, c)| !c.is_ascii_alphanumeric() && *c != '+')
            .map_or(0, |(j, c)| j + c.len_utf8());
        let url_end = rest[i..]
            .find(|c: char| c.is_whitespace() || matches!(c, '"' | '\'' | '<' | '>'))
            .map_or(rest.len(), |e| i + e);
        let url = &rest[scheme_start..url_end];
        out.push_str(&rest[..scheme_start]);
        match redact_url(url, mark) {
            Some(redone) => {
                out.push_str(&redone);
                count += 1;
            }
            None => out.push_str(url),
        }
        rest = &rest[url_end..];
    }
    out.push_str(rest);
    (out, count)
}

fn redact_url(url: &str, mark: &mut dyn FnMut(&str) -> String) -> Option<String> {
    let (scheme, rest) = url.split_once("://")?;
    let (userinfo, host) = rest.split_once('@')?;
    let (user, pass) = userinfo.split_once(':')?;
    (!pass.is_empty() && !host.is_empty() && !userinfo.contains('/') && !pass.starts_with("${"))
        .then(|| format!("{scheme}://{user}:{}@{host}", mark(pass)))
}

fn is_token_char(c: char) -> bool {
    c.is_ascii_alphanumeric() || matches!(c, '_' | '-' | '.' | '+' | '/' | '@' | '~' | '%')
}

fn code_expression(key: &str, sep: &str, value: &str, rest: &str, prefix: &str) -> bool {
    if sep.ends_with(['"', '\'']) {
        return false;
    }
    // A quoted key with a bare value is ambiguous in ordinary text and YAML.
    // Exempt it only when the surrounding source explicitly identifies Rust's
    // `json!` macro; otherwise a scalar such as `"password": hunter2` leaks.
    if sep.starts_with(['"', '\'']) && prefix.contains("json!(") {
        return true;
    }
    let name = |s: &str| s.rsplit('.').next().unwrap_or("").replace(['_', '-'], "").to_ascii_lowercase();
    let after = rest.trim_start();
    let typed_field = sep.trim_end().ends_with(':')
        && is_common_type(value)
        && (after.is_empty() || after.starts_with([',', ';', ')', '=', '>']));
    rest.starts_with(['(', '[', '<'])
        || rest.starts_with("::")
        || name(value) == name(key.trim_start_matches('-'))
        || typed_field
}

fn is_assignment(sep: &str) -> bool {
    let core: String = sep.chars().filter(|c| !c.is_whitespace() && !matches!(c, '"' | '\'')).collect();
    core == "=" || (core == ":" && sep != ":")
}
