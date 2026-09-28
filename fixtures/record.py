#!/usr/bin/env python3
"""Record the Modrinth fixtures and their Jev answers, then regenerate refs.txt and expected.json.

Picks well-known Modrinth mods across several storefront categories with the search API,
downloads them with the bulk projects endpoint, and writes one file per project to
fixtures/modrinth/. Then runs python/modhopper.py against those files with Jev answers
recorded through a local proxy, so fixtures/jev/answers.json and fixtures/expected.json
hold exactly what one real run produced. CurseForge fixtures stay as they are.

Needs network access to Modrinth and Jev (TYPESAFE_API_KEY, or TYPESAFE_BASE_URL pointing at
a gateway that holds the key). Usage: python3 fixtures/record.py [--per-bucket 15]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import urllib.parse
import urllib.request
from http.server import HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import check  # noqa: E402  (the fixture server; only its Jev endpoint is replaced below)

FIXTURES = ROOT / 'fixtures'
MODRINTH = 'https://api.modrinth.com'
TYPESAFE = os.environ.get('TYPESAFE_BASE_URL', 'https://api.typesafe.ai')
USER_AGENT = 'modhopper fixture recorder (github.com/gorpokki/modhopper)'
FIELDS = ('id', 'slug', 'project_type', 'title', 'description', 'body', 'categories', 'additional_categories')
# Buckets to draw from: a Modrinth category facet, or a free-text query where no facet exists.
BUCKETS = [('performance', 'optimization', None), ('visuals', 'decoration', None), ('animations', None, 'animation'),
           ('tools', 'utility', None), ('gameplay', 'game-mechanics', None), ('gameplay', 'equipment', None),
           ('gameplay', 'magic', None), ('gameplay', 'mobs', None), ('gameplay', 'adventure', None),
           ('gameplay', 'technology', None), ('gameplay', 'food', None), ('gameplay', 'storage', None),
           ('libraries', 'library', None), ('world generation', 'worldgen', None),
           ('server utilities', 'management', None), ('server utilities', None, 'server')]
# Skipped on purpose: their storefront text carries words that must stay out of this repository.
SKIP = {'aquamirae', 'crash-assistant', 'create', 'create-fabric'}
SECRET = re.compile(r'(?i)(bearer\s+\S+|api[_-]?key\s*[:=]\s*\S+|sk-[A-Za-z0-9]{16,})')


def get(path, **query):
    url = f'{MODRINTH}{path}?{urllib.parse.urlencode(query)}'
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': USER_AGENT}), timeout=60) as r:
        return json.load(r)


def pick(per_bucket):
    """Project ids, spread across BUCKETS, most downloaded first, no duplicate ids or titles."""
    ids, titles = [], set()
    for label, category, query in BUCKETS:
        facets = [['project_type:mod']] + ([[f'categories:{category}']] if category else [])
        hits = get('/v2/search', query=query or '', facets=json.dumps(facets), index='downloads', limit=per_bucket)
        new = [h for h in hits['hits'] if h['project_id'] not in ids and h['title'] not in titles and h['slug'] not in SKIP]
        ids += [h['project_id'] for h in new]
        titles |= {h['title'] for h in new}
        print(f'{label}: {len(new)} new projects', file=sys.stderr)
    return ids


def scrub(value):
    """Replace anything that looks like a credential in recorded text."""
    if isinstance(value, str):
        return SECRET.sub('[redacted]', value)
    if isinstance(value, list):
        return [scrub(v) for v in value]
    if isinstance(value, dict):
        return {k: scrub(v) for k, v in value.items()}
    return value


def record_modrinth(ids):
    for path in (FIXTURES / 'modrinth').glob('*.json'):
        path.unlink()
    projects = []
    for start in range(0, len(ids), 50):
        projects += get('/v2/projects', ids=json.dumps(ids[start:start + 50]))
    projects.sort(key=lambda p: p['slug'])
    for project in projects:
        trimmed = scrub({field: project.get(field) for field in FIELDS})
        (FIXTURES / 'modrinth' / f'{project["slug"]}.json').write_text(
            json.dumps(trimmed, indent=2, ensure_ascii=False) + '\n')
    return [f'modrinth:{p["slug"]}' for p in projects]


class Recorder(check.Fake):
    """check.py's fixture server, with Jev calls forwarded to the real endpoint and recorded."""
    answers = {}

    def do_POST(self):
        request = self.rfile.read(int(self.headers['Content-Length']))
        name = json.loads(request)['state']['name']
        headers = {'Content-Type': 'application/json', 'User-Agent': USER_AGENT}
        if os.environ.get('TYPESAFE_API_KEY'):
            headers['Authorization'] = 'Bearer ' + os.environ['TYPESAFE_API_KEY']
        with urllib.request.urlopen(urllib.request.Request(f'{TYPESAFE}/v1/systemone', data=request, headers=headers),
                                    timeout=120) as r:
            answer = json.load(r)
        self.answers[name] = scrub(answer)
        body = json.dumps(answer).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body)


def record_answers():
    server = HTTPServer(('127.0.0.1', 0), Recorder)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    env = {**os.environ, 'MODRINTH_BASE_URL': base, 'CURSEFORGE_BASE_URL': base, 'TYPESAFE_BASE_URL': base,
           'CURSEFORGE_API_KEY': 'fixture-key'}
    with tempfile.TemporaryDirectory() as tmp:
        run = subprocess.run([sys.executable, str(ROOT / 'python' / 'modhopper.py'), '--cache', f'{tmp}/cache.json',
                              '--file', str(FIXTURES / 'refs.txt')], env=env, capture_output=True)
    if run.returncode:
        sys.exit(f'modhopper.py failed:\n{run.stderr.decode()}')
    (FIXTURES / 'jev' / 'answers.json').write_text(
        json.dumps(Recorder.answers, indent=2, sort_keys=True, ensure_ascii=False) + '\n')
    (FIXTURES / 'expected.json').write_bytes(run.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--per-bucket', type=int, default=15, help='search hits to take per category bucket')
    args = parser.parse_args()
    refs = record_modrinth(pick(args.per_bucket))
    refs += [f'curseforge:{p.stem}' for p in sorted((FIXTURES / 'curseforge').glob('*.json'))]
    (FIXTURES / 'refs.txt').write_text('\n'.join(refs) + '\n')
    record_answers()
    print(f'recorded {len(refs)} projects', file=sys.stderr)


if __name__ == '__main__':
    main()
