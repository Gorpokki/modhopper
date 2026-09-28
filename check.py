#!/usr/bin/env python3
"""Offline check: run both implementations against fixtures/ and compare their JSON output.

Serves fixtures/ as fake Modrinth, CurseForge, and Jev endpoints on localhost,
points both implementations at it, and asserts their stdout is byte-identical
to each other and to fixtures/expected.json.
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / 'fixtures'


class Fake(BaseHTTPRequestHandler):
    requests = {}  # Jev request body per mod name, for the run in progress

    def do_GET(self):
        if self.path.startswith('/v2/project/'):
            return self.reply(FIXTURES / 'modrinth' / (self.path.rsplit('/', 1)[1] + '.json'))
        if self.path.startswith('/v1/mods/'):
            if self.headers.get('x-api-key') != 'fixture-key':
                return self.send_error(403, 'x-api-key missing or wrong')
            return self.reply(FIXTURES / 'curseforge' / (self.path.rsplit('/', 1)[1] + '.json'))
        self.send_error(404)

    def do_POST(self):
        if self.path != '/v1/systemone':
            return self.send_error(404)
        request = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        if request['questions']['category']['criteria'] != json.loads((ROOT / 'categories.json').read_text()):
            return self.send_error(500, 'criteria differ from categories.json')
        self.requests[request['state']['name']] = request
        answers = json.loads((FIXTURES / 'jev' / 'answers.json').read_text())
        body = json.dumps(answers[request['state']['name']]).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body)

    def reply(self, path):
        if not path.exists():
            return self.send_error(404, str(path))
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(path.read_bytes())

    def log_message(self, *args):
        pass


def run(command, env, cache):
    """stdout of one run, and the Jev request bodies it sent."""
    Fake.requests = {}
    done = subprocess.run(command + ['--cache', cache, '--file', str(FIXTURES / 'refs.txt')], env=env, capture_output=True)
    if done.returncode:
        sys.exit(f'{command[-1]} exited {done.returncode}:\n{done.stderr.decode()}')
    return done.stdout, Fake.requests


def main():
    server = HTTPServer(('127.0.0.1', 0), Fake)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    env = {**os.environ, 'MODRINTH_BASE_URL': base, 'CURSEFORGE_BASE_URL': base, 'TYPESAFE_BASE_URL': base,
           'CURSEFORGE_API_KEY': 'fixture-key'}
    env.pop('TYPESAFE_API_KEY', None)
    subprocess.run(['cargo', 'build', '-q', '--locked', '--manifest-path', str(ROOT / 'rust' / 'Cargo.toml')], check=True)
    with tempfile.TemporaryDirectory() as tmp:
        python = [sys.executable, str(ROOT / 'python' / 'modhopper.py')]
        rust = [str(ROOT / 'rust' / 'target' / 'debug' / 'modhopper')]
        outputs = {'python': run(python, env, f'{tmp}/py.json'), 'rust': run(rust, env, f'{tmp}/rs.json')}
        # second run of each reads the cache instead of the storefronts
        outputs['python-cached'] = run(python, env, f'{tmp}/py.json')
        outputs['rust-cached'] = run(rust, env, f'{tmp}/rs.json')
        assert Path(f'{tmp}/py.json').read_bytes() == Path(f'{tmp}/rs.json').read_bytes(), 'cache files differ'
    requests = {name: sent for name, (_, sent) in outputs.items()}
    assert len({json.dumps(r, sort_keys=True) for r in requests.values()}) == 1, 'Jev request bodies differ between runs'
    expected = (FIXTURES / 'expected.json').read_bytes()
    for name, (output, _) in outputs.items():
        if output != expected:
            sys.stderr.write(f'{name} output differs from fixtures/expected.json:\n{output.decode()}')
            sys.exit(1)
    print(f'ok: {len(outputs)} runs, byte-identical to fixtures/expected.json')


if __name__ == '__main__':
    main()
