#!/usr/bin/env python3
"""Record bounded offline lifecycle scenes after matching QA/native audit gates."""
import argparse
import codecs
import fcntl
import hashlib
import http.server
import json
import os
from pathlib import Path
import pty
import select
import signal
import struct
import tempfile
import termios
import threading
import time
import unittest


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as file:
        for block in iter(lambda: file.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def verify_receipt(receipt, revision, digest, base):
    for key, value in [('source_revision', revision), ('binary_sha256', digest),
                       ('full_qa', 'passed'), ('native_ui', 'passed')]:
        if receipt.get(key) != value:
            raise ValueError(f'audit receipt mismatch or pending gate: {key}')
    evidence = receipt.get('evidence')
    if not isinstance(evidence, list):
        raise ValueError('audit receipt must cite hashed QA/native evidence')
    kinds = set()
    for item in evidence:
        if not isinstance(item, dict) or not all(item.get(k) for k in ['path', 'sha256', 'kind']):
            raise ValueError('each evidence item needs path, sha256 and kind')
        path = Path(base) / item['path']
        if not path.is_file() or sha256_file(path) != item['sha256']:
            raise ValueError(f'audit evidence missing or changed: {item["kind"]}')
        kinds.add(item['kind'])
    if not {'full_qa', 'native_ui'} <= kinds:
        raise ValueError('both full_qa and native_ui evidence are required')


class ReceiptTests(unittest.TestCase):
    def test_pending_wrong_and_missing_artifacts_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); evidence = []
            for kind in ['full_qa', 'native_ui']:
                artifact = root / (kind + '.txt'); artifact.write_text('fixture evidence')
                evidence.append(dict(path=artifact.name, kind=kind, sha256=hashlib.sha256(artifact.read_bytes()).hexdigest()))
            good = dict(source_revision='a' * 40, binary_sha256='b' * 64,
                        full_qa='passed', native_ui='passed', evidence=evidence)
            verify_receipt(good, 'a' * 40, 'b' * 64, root)
            for key in ['source_revision', 'binary_sha256', 'full_qa', 'native_ui', 'evidence']:
                broken = dict(good); broken[key] = None
                with self.assertRaises(ValueError):
                    verify_receipt(broken, 'a' * 40, 'b' * 64, root)
            (root / evidence[0]['path']).write_text('changed bytes')
            with self.assertRaises(ValueError):
                verify_receipt(good, 'a' * 40, 'b' * 64, root)
            (root / evidence[0]['path']).unlink()
            with self.assertRaises(ValueError):
                verify_receipt(good, 'a' * 40, 'b' * 64, root)


class Terminal:
    def __init__(self, name, binary, cwd, env, columns, rows, args=()):
        self.name = name; self.events = []; self.text = ''; self.decoder = codecs.getincrementaldecoder('utf-8')('replace')
        self.start = time.monotonic(); self.reaped = False
        self.columns = columns; self.rows = rows
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.chdir(cwd)
            os.execve(str(binary), [str(binary), '--memory', 'off', '--agents', 'off',
                                    '--mode', 'standard', '--context-tokens', '128000', *args], env)
        self.resize(columns, rows)

    def resize(self, columns, rows):
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack('HHHH', rows, columns, 0, 0))
        os.kill(self.pid, signal.SIGWINCH)
        if self.events:
            self.events.append([round(time.monotonic() - self.start, 4), 'r', f'{columns}x{rows}'])

    def pump(self, seconds=.05):
        if select.select([self.fd], [], [], seconds)[0]:
            try: raw = os.read(self.fd, 65536)
            except OSError: raw = b''
            if raw:
                text = self.decoder.decode(raw)
                self.text += text
                self.events.append([round(time.monotonic() - self.start, 4), 'o', text])

    def wait(self, needle, start=0, timeout=15):
        deadline = time.monotonic() + timeout
        while needle not in self.text[start:]:
            if time.monotonic() >= deadline:
                raise RuntimeError(f'{self.name}: timed out waiting for {needle!r}')
            self.pump()

    def ready(self, start=0):
        self.wait('\x1b[?2004h', start)

    def type(self, text):
        for char in text:
            os.write(self.fd, char.encode()); self.pump(.025)
        deadline = time.monotonic() + .15
        while time.monotonic() < deadline: self.pump(.025)

    def command(self, text, expected):
        start = len(self.text)
        self.type(text); os.write(self.fd, b'\r')
        self.wait(expected, start); self.ready(start)

    def close(self, output, quit=True):
        if self.reaped: return
        try:
            if quit:
                self.type('/exit'); os.write(self.fd, b'\r')
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    self.pump()
                    pid, status = os.waitpid(self.pid, os.WNOHANG)
                    if pid:
                        self.reaped = True
                        if os.waitstatus_to_exitcode(status) != 0:
                            raise RuntimeError(f'{self.name}: unexpected exit status {status}')
                        break
            if not self.reaped:
                os.kill(self.pid, signal.SIGTERM); os.waitpid(self.pid, 0); self.reaped = True
                if quit: raise RuntimeError(f'{self.name}: did not exit cleanly')
            if quit:
                header = dict(version=2, width=self.columns, height=self.rows,
                              title=f'Rusty lifecycle: {self.name} (local mock provider)', env={'TERM': 'xterm-256color'})
                with (output / f'{self.name}.cast').open('w') as file:
                    for event in [header, *self.events]: file.write(json.dumps(event) + '\n')
        finally:
            os.close(self.fd)


def record(args):
    binary = Path(args.binary).resolve()
    digest = sha256_file(binary)
    receipt = json.loads(Path(args.audit_receipt).read_text())
    if len(args.source_revision) != 40 or any(c not in '0123456789abcdef' for c in args.source_revision):
        raise ValueError('source revision must be a full lowercase Git SHA')
    verify_receipt(receipt, args.source_revision, digest, Path(args.audit_receipt).resolve().parent)
    output = Path(args.output).resolve(); output.mkdir(parents=True, exist_ok=False)
    requests = []; lock = threading.Lock()

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_): pass
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            with lock: requests.append(body)
            self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
            # Slow enough to demonstrate busy draft input without a paid request.
            for text in ['DEMO_STREAM_START\n', *['local demo progress\n'] * 10, 'DEMO_STREAM_DONE\n']:
                event = {'choices': [{'delta': {'content': text}, 'finish_reason': None}]}
                self.wfile.write(('data: ' + json.dumps(event) + '\n\n').encode()); self.wfile.flush(); time.sleep(.15)
            self.wfile.write(b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n')
            self.wfile.flush()

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    terminals = []; completed = False
    try:
        with tempfile.TemporaryDirectory(prefix='rusty-lifecycle-', dir='/tmp') as scratch:
            root = Path(scratch); project = root / 'project'; project.mkdir()
            env = {'HOME': str(root / 'user'), 'CODEX_HOME': str(root / 'codex'),
                   'RUSTY_HOME': str(root / 'rusty'), 'PATH': '/usr/bin:/bin', 'LANG': 'en_US.UTF-8',
                   'RUSTY_NO_DOTENV': '1', 'RUSTY_INFRA': 'off', 'RUSTY_PROVIDER': 'compatible',
                   'NVIDIA_API_KEY': 'offline-demo-key', 'RUSTY_BASE_URL': f'http://127.0.0.1:{server.server_port}/v1',
                   'TERM': 'xterm-256color', 'COLORTERM': 'truecolor'}
            def launch(name, extra=()):
                t = Terminal(name, binary, project, env, args.columns, args.rows, extra)
                terminals.append(t); t.ready(); return t
            t = launch('configure-use-quit')
            t.command('/theme rust', 'theme'); t.command('/font compact', 'rusty')
            t.command('/settings', 'permissions'); t.command('!pwd', 'exit 0')
            # Exercise completion reflow, retaining raw output for visual review.
            t.type('/the'); t.resize(24, 12)
            for _ in range(8): t.pump(.05)
            t.resize(args.columns, args.rows); os.write(t.fd, b'\x15')
            for _ in range(8): t.pump(.05)
            first = 'First request in this demonstration.'
            start = len(t.text); t.type(first); os.write(t.fd, b'\r'); t.wait('DEMO_STREAM_START', start)
            t.type('Unsent draft kept during work')
            t.wait('DEMO_STREAM_DONE', start); t.ready(start)
            # Busy draft must be present at idle, not submitted as another request.
            idle = t.text.rfind('\x1b[?2004h')
            t.wait('Unsent draft kept during work', idle)
            if len(requests) != 1: raise RuntimeError('unsent draft triggered another model request')
            os.write(t.fd, b'\x15')
            for _ in range(4): t.pump(.05)
            t.close(output)
            before = len(requests); t = launch('reopen-resume', ['-c'])
            if first not in t.text: raise RuntimeError('resume preview missing first request')
            if len(requests) != before: raise RuntimeError('resume made an inference request')
            t.command('Continue this demonstration.', 'DEMO_STREAM_DONE')
            if first not in json.dumps(requests[-1]['messages']): raise RuntimeError('resume lost model context')
            t.close(output)
            t = launch('fresh-session'); t.command('Fresh standalone demonstration.', 'DEMO_STREAM_DONE')
            if first in json.dumps(requests[-1]['messages']): raise RuntimeError('fresh session leaked old context')
            t.command('/new', 'fresh context'); t.close(output)
            completed = True
    finally:
        for t in terminals:
            if not t.reaped: t.close(output, quit=False)
        server.shutdown(); server.server_close(); thread.join(timeout=2)
        manifest = dict(source_revision=args.source_revision, binary_sha256=digest,
                        audit_receipt={k: receipt[k] for k in ['source_revision', 'binary_sha256', 'full_qa', 'native_ui']},
                        audit_evidence=[{'kind': e['kind'], 'sha256': e['sha256']} for e in receipt['evidence']], provider='deterministic local mock; no real authentication',
                        memory='off', terminal={'columns': args.columns, 'rows': args.rows},
                        inference_requests=len(requests), completed=completed,
                        scenes=[t.name for t in terminals if (output / f'{t.name}.cast').exists()],
                        limits=['Not an install test', 'Not native cmux proof', 'Not default daemon cleanup',
                                'Raw resize playback requires human visual inspection'])
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'{output}: completed={completed}, mock requests={len(requests)}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    for name in ['binary', 'source-revision', 'audit-receipt', 'output']: parser.add_argument('--' + name)
    parser.add_argument('--columns', type=int, default=80); parser.add_argument('--rows', type=int, default=24)
    args = parser.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(ReceiptTests)).wasSuccessful() else 1
    if not all([args.binary, args.source_revision, args.audit_receipt, args.output]): parser.error('binary, source-revision, audit-receipt and output are required')
    if args.columns < 24 or args.rows < 12: parser.error('minimum dimensions are 24 columns and 12 rows')
    record(args)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
