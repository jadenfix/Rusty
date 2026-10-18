#!/usr/bin/env python3
"""Check handbook navigation and source-area documentation maintenance (stdlib)."""
import argparse
import pathlib
import re
import subprocess
import sys
import unittest
from urllib.parse import unquote, urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]
GUIDES = ['README', 'install', 'configure', 'terminal', 'work', 'integrations', 'sessions', 'data', 'troubleshooting', 'reference', 'audit']
AREAS = {
    'install': ['Cargo.toml', 'Dockerfile'],
    'configure': ['src/config.rs', 'src/codex.rs', 'src/doctor.rs', 'src/llm.rs', 'src/anthropic.rs'],
    'terminal': ['src/ui.rs', 'src/slash.rs', 'src/footer.rs', 'src/display.rs', 'src/signal.rs', 'src/markdown.rs', 'src/tips.rs', 'src/sse.rs'],
    'work': ['src/agent.rs', 'src/execution.rs', 'src/permissions.rs', 'src/tools.rs', 'src/verification.rs', 'src/budget.rs', 'src/skills.rs', 'src/side.rs', 'src/aside.rs', 'src/swarm.rs', 'src/activity.rs', 'src/infra.rs', 'src/snapshot.rs', 'src/cloud', 'src/bin/rusty-cloud.rs'],
    'integrations': ['src/integrations.rs', 'src/mcp.rs'],
    'sessions': ['src/session.rs', 'src/backend.rs', 'src/inbox.rs'],
    'data': ['src/advisor.rs', 'src/privacy.rs', 'src/memory', 'src/bin/rusty-memoryd.rs', 'src/recall.rs', 'src/context.rs'],
}

DEEP_AREAS = {
    'docs/INTEGRATIONS.md': ['src/integrations.rs', 'src/mcp.rs'],
    'docs/CLOUD.md': ['src/cloud', 'src/bin/rusty-cloud.rs'],
    'docs/MEMORY.md': ['src/advisor.rs', 'src/recall.rs', 'src/bin/rusty-memoryd.rs'],
    'docs/VERIFICATION.md': ['src/verification.rs'],
    'docs/INFRA.md': ['src/infra.rs'],
}


def matches(path, source):
    return path == source or path.startswith(source + '/')


def classification_errors(root):
    sources = [source for area in AREAS.values() for source in area]
    return [f'{p.relative_to(root)}: assign this module to its user guide in scripts/check-docs.py'
            for p in sorted((root / 'src').rglob('*.rs'))
            if str(p.relative_to(root)) not in ['src/main.rs', 'src/lib.rs']
            and not any(matches(str(p.relative_to(root)), source) for source in sources)]


def maintenance_errors(changed):
    changed = set(changed)
    errors = []
    targets = {f'docs/guide/{guide}.md': sources for guide, sources in AREAS.items()}
    targets.update(DEEP_AREAS)
    for guide, sources in targets.items():
        affected = sorted(p for p in changed if any(matches(p, source) for source in sources))
        if affected and guide not in changed:
            errors.append(f'{", ".join(affected)}: update {guide} with its executable example/demo evidence')
    if changed & {'src/main.rs', 'src/lib.rs'} and not any(p.startswith('docs/guide/') for p in changed):
        errors.append('CLI/lifecycle entry point: update the affected lifecycle guide with its example/demo evidence')
    return errors


def anchors(path):
    result = set()
    for heading in re.findall(r'^#{1,6} +(.+)$', path.read_text(), re.MULTILINE):
        slug = re.sub(r'[^\w -]', '', heading.lower()).replace(' ', '-')
        unique = slug; number = 0
        while unique in result:
            number += 1; unique = f'{slug}-{number}'
        result.add(unique)
    return result


def navigation_errors(root):
    errors = []
    pages = [root / 'docs/guide' / (name + '.md') for name in GUIDES]
    for optional in ['README.md', 'docs/demo/README.md']:
        if (root / optional).is_file(): pages.append(root / optional)
    for path in pages:
        if not path.is_file():
            errors.append(f'missing guide: {path.relative_to(root)}')
            continue
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', path.read_text()):
            target = target.strip('<>')
            if urlsplit(target).scheme:
                continue
            file, separator, anchor = target.partition('#')
            linked = path.parent / unquote(file) if file else path
            if not linked.exists():
                errors.append(f'{path.relative_to(root)}: broken link {target}')
            elif separator and linked.is_file() and linked.suffix == '.md' and unquote(anchor) not in anchors(linked):
                errors.append(f'{path.relative_to(root)}: missing heading {target}')
    readme = root / 'README.md'
    if readme.is_file() and 'docs/guide/README.md' not in readme.read_text():
        errors.append('README.md must link to the ordered lifecycle guide')
    return errors


class Checks(unittest.TestCase):
    def test_runtime_change_needs_its_guide(self):
        self.assertTrue(maintenance_errors(['src/integrations.rs', 'docs/guide/integrations.md']))
        self.assertFalse(maintenance_errors(['src/integrations.rs', 'docs/guide/integrations.md', 'docs/INTEGRATIONS.md']))
        self.assertTrue(maintenance_errors(['src/ui.rs']))
        self.assertFalse(maintenance_errors(['src/ui.rs', 'docs/guide/terminal.md']))
        self.assertTrue(maintenance_errors(['src/session.rs', 'docs/guide/terminal.md']))

    def test_evidence_cannot_bypass_the_affected_guide(self):
        self.assertTrue(maintenance_errors(['src/agent.rs', 'docs/examples/contract.json']))
        self.assertFalse(maintenance_errors(['src/agent.rs', 'docs/guide/work.md', 'docs/examples/contract.json']))
        self.assertFalse(maintenance_errors(['src/main.rs', 'docs/guide/sessions.md']))
        self.assertFalse(maintenance_errors(['tests/documentation.rs']))
        self.assertTrue(maintenance_errors(['src/cloud/api.rs', 'docs/guide/work.md']))
        self.assertFalse(maintenance_errors(['src/cloud/api.rs', 'docs/guide/work.md', 'docs/CLOUD.md']))

    def test_new_source_modules_need_a_guide_mapping(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp); (root / 'src').mkdir()
            (root / 'src/new_feature.rs').write_text('// new feature')
            self.assertTrue(classification_errors(root))
            (root / 'src/new_feature.rs').unlink()
            (root / 'src/ui.rs').write_text('// known area')
            self.assertFalse(classification_errors(root))

    def test_missing_or_broken_pages_are_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'docs/guide').mkdir(parents=True)
            for name in GUIDES:
                (root / 'docs/guide' / (name + '.md')).write_text('# Guide\n')
            self.assertFalse(navigation_errors(root))
            (root / 'docs/guide/install.md').write_text('[bad](#not-a-heading)')
            self.assertTrue(navigation_errors(root))
            (root / 'docs/guide/install.md').write_text('[broken](missing.md)')
            self.assertTrue(navigation_errors(root))
            (root / 'docs/guide/install.md').unlink()
            self.assertTrue(navigation_errors(root))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', help='git ref for same-PR source/documentation coverage')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks)).wasSuccessful() else 1
    errors = navigation_errors(ROOT) + classification_errors(ROOT)
    if args.base:
        # Use merge-base, so unrelated base-branch updates are not attributed to this PR.
        merge_base = subprocess.check_output(['git', 'merge-base', args.base, 'HEAD'], cwd=ROOT, text=True).strip()
        changed = subprocess.check_output(['git', 'diff', '--name-only', merge_base, '--'], cwd=ROOT, text=True).splitlines()
        errors += maintenance_errors(changed)
    for error in errors:
        print(error, file=sys.stderr)
    if not errors:
        print('documentation navigation and requested source coverage passed')
    return bool(errors)


if __name__ == '__main__':
    sys.exit(main())
