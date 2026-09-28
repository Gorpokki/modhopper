#!/usr/bin/env python3
"""Sort Minecraft mods from Modrinth and CurseForge into categories with Jev.

Usage: modhopper.py [--file refs.txt] [--cache metadata-cache.json] [--refresh] [REF ...]
A REF is modrinth:<slug-or-id> or curseforge:<numeric-id>.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

MODRINTH = os.environ.get('MODRINTH_BASE_URL', 'https://api.modrinth.com')
CURSEFORGE = os.environ.get('CURSEFORGE_BASE_URL', 'https://api.curseforge.com')
TYPESAFE = os.environ.get('TYPESAFE_BASE_URL', 'https://api.typesafe.ai')
CATEGORIES = Path(__file__).resolve().parent.parent / 'categories.json'
DESCRIPTION_LIMIT = 2000
USER_AGENT = 'modhopper (github.com/gorpokki/modhopper)'


def http_json(url, headers, body=None):
    request = urllib.request.Request(url, data=body, headers={'User-Agent': USER_AGENT, **headers})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'{url} returned HTTP {error.code}') from None


def fetch(reference):
    """Return storefront evidence for one reference: name, summary, description, categories."""
    source, _, identifier = reference.partition(':')
    if source == 'modrinth' and identifier:
        d = http_json(f'{MODRINTH}/v2/project/{identifier}', {})
        return {'name': d['title'], 'summary': d['description'], 'description': d.get('body') or '',
                'categories': d['categories'] + d.get('additional_categories', [])}
    if source == 'curseforge' and identifier.isdecimal():
        key = os.environ.get('CURSEFORGE_API_KEY')
        if not key:
            raise RuntimeError('CURSEFORGE_API_KEY is not set; CurseForge references need it')
        d = http_json(f'{CURSEFORGE}/v1/mods/{identifier}', {'x-api-key': key})['data']
        # ponytail: CurseForge's full description is a second HTML endpoint; summary alone until it proves too thin.
        return {'name': d['name'], 'summary': d['summary'], 'description': '',
                'categories': [c['name'] for c in d['categories']]}
    raise RuntimeError(f'Bad reference {reference!r}: expected modrinth:<slug-or-id> or curseforge:<numeric-id>')


def classify(evidence, categories):
    """Ask Jev for one category. Returns (category, one-line reason)."""
    state = {'name': evidence['name'], 'summary': evidence['summary'],
             'description': evidence['description'][:DESCRIPTION_LIMIT],
             'storefront_categories': evidence['categories']}
    question = {'type': 'choice',
                'instructions': 'Which category fits this Minecraft mod best? Judge from `name`, `summary`, '
                                '`description`, and `storefront_categories`.',
                'criteria': categories}
    body = json.dumps({'model': 'jev-latest', 'state': state, 'questions': {'category': question}}).encode()
    headers = {'Content-Type': 'application/json'}
    key = os.environ.get('TYPESAFE_API_KEY')
    if key:
        headers['Authorization'] = 'Bearer ' + key
    answer = http_json(f'{TYPESAFE}/v1/systemone', headers, body)['answers']['category']
    choice = answer['choice']
    if choice not in categories:
        raise RuntimeError(f'Jev answered {choice!r}, which is not in categories.json')
    ranked = sorted(answer['probabilities'].items(), key=lambda item: (-item[1], item[0]))
    runner = next((name, p) for name, p in ranked if name != choice)
    return choice, (f'Jev chose {choice} with {percent(answer["probabilities"][choice])}% probability; '
                    f'runner-up {runner[0]} at {percent(runner[1])}%.')


def percent(probability):
    return int(probability * 100 + 0.5)


def load_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def save_json(path, value):
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('refs', nargs='*', metavar='REF', help='modrinth:<slug-or-id> or curseforge:<numeric-id>')
    parser.add_argument('--file', type=Path, help='file with one REF per line')
    parser.add_argument('--cache', type=Path, default=Path('metadata-cache.json'), help='storefront metadata cache')
    parser.add_argument('--refresh', action='store_true', help='refetch storefront metadata')
    args = parser.parse_args()
    refs = args.refs + ([line.strip() for line in args.file.read_text().splitlines() if line.strip()] if args.file else [])
    if not refs:
        parser.error('no references given')
    categories = json.loads(CATEGORIES.read_text())
    cache = {} if args.refresh else load_json(args.cache, {})
    results, failed = [], 0
    for reference in refs:
        try:
            if reference not in cache:
                print(f'fetching {reference}', file=sys.stderr)
                cache[reference] = fetch(reference)
                save_json(args.cache, cache)
            evidence = cache[reference]
            print(f'classifying {evidence["name"]}', file=sys.stderr)
            category, reason = classify(evidence, categories)
            results.append({'reference': reference, 'name': evidence['name'], 'source': reference.partition(':')[0],
                            'category': category, 'reason': reason, 'categories': evidence['categories']})
        except Exception as error:  # one bad project must not hide the others
            failed += 1
            print(f'error: {reference}: {error}', file=sys.stderr)
    print(json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
