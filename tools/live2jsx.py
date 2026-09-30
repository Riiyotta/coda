"""Convert crawled coda.co pages (crawl/*.html) into page components.

Usage: python3 tools/live2jsx.py [--no-download]
Writes src/pages/*.jsx, src/pages/routes.js and downloads page images/videos into public/.

Unlike the homepage (from the user's own saved copy), these pages were fetched live, so any
body text of 9+ words is replaced with placeholder text of the same length. Headings, labels,
buttons and figures (short strings) are kept.
"""
import os
import re
import subprocess
import sys

from _lib import ROOT, ROUTES, IMG_DIR, externalize_svgs, to_jsx
from html2jsx import Spans, mark_reveal

CRAWL = os.path.join(ROOT, 'crawl')
PAGES = os.path.join(ROOT, 'src', 'pages')
VID_DIR = os.path.join(ROOT, 'public', 'video')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36'
MIN_WORDS = 9
LOREM = ('lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore '
         'et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut '
         'aliquip ex ea commodo consequat duis aute irure dolor in reprehenderit in voluptate velit esse cillum '
         'dolore eu fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt in culpa qui '
         'officia deserunt mollit anim id est laborum').split()


def placeholder(text, seed):
    """Same-length placeholder that keeps leading/trailing whitespace, capitalisation and final punctuation."""
    lead = text[:len(text) - len(text.lstrip())]
    trail = text[len(text.rstrip()):]
    core = text.strip()
    end = core[-1] if core[-1] in '.!?:' else ''
    target = len(core) - len(end)
    words, i = [], seed % len(LOREM)
    while len(' '.join(words)) < target:
        words.append(LOREM[i % len(LOREM)])
        i += 1
    out = ' '.join(words)[:target].rstrip()
    out = out + 'x' * (target - len(out))
    if core[0].isupper():
        out = out[0].upper() + out[1:]
    return lead + out + end + trail


def scrub_text(html):
    """Replace long text nodes (outside tags, svg and style) with placeholder."""
    n = [0]

    def repl(m):
        text = m.group(0)
        plain = re.sub(r'&[a-z#0-9]+;', 'x', text)
        if len(plain.split()) < MIN_WORDS:
            return text
        n[0] += 1
        return placeholder(plain, n[0] * 7)
    parts = re.split(r'(<svg\b.*?</svg>|<style\b.*?</style>|<[^>]+>)', html, flags=re.S)
    return ''.join(p if (i % 2 or not p.strip()) else re.sub(r'[^<]+', repl, p) for i, p in enumerate(parts))


def asset_urls(html):
    return set(re.findall(r'https://www\.coda\.co/wp-content/uploads/[^"\s,)]+\.(?:avif|webp|png|jpe?g|svg|gif|mp4|webm)',
                          html))


def download(urls):
    todo = []
    for u in sorted(urls):
        name = u.rsplit('/', 1)[1]
        dest = os.path.join(VID_DIR if name.endswith(('.mp4', '.webm')) else IMG_DIR, name)
        if not os.path.exists(dest):
            todo.append((u, dest))
    print(f'downloading {len(todo)} assets')
    for u, dest in todo:
        r = subprocess.run(['curl', '-sfL', '-A', UA, '-o', dest, u])
        if r.returncode:
            print('  FAIL', u)


def comp_name(route):
    return ''.join(w.capitalize() for w in re.split(r'[/-]', route) if w) + 'Page'


def main():
    os.makedirs(PAGES, exist_ok=True)
    os.makedirs(VID_DIR, exist_ok=True)
    pages = []
    for route in sorted(ROUTES):
        f = os.path.join(CRAWL, route.strip('/').replace('/', '_') + '.html')
        h = open(f, encoding='utf-8').read()
        body = h[h.find('<body'):]
        body = re.sub(r'<script\b.*?</script>', '', body, flags=re.S)
        body = re.sub(r'<noscript\b.*?</noscript>', '', body, flags=re.S)
        body = re.sub(r'<iframe\b.*?</iframe>', '', body, flags=re.S)
        body = re.sub(r'<!--.*?-->', '', body, flags=re.S)
        p = Spans(body)
        p.feed(body)
        mw = min((s for s in p.spans if 'mt-navBarInnerTopBase' in (s[1].get('class') or '')), key=lambda s: s[2])
        wrap_cls = mw[1].get('class')
        inner = body[body.find('>', mw[2]) + 1:body.rfind('</', 0, mw[3])]
        pages.append((route, wrap_cls, inner))

    if '--no-download' not in sys.argv:
        urls = set()
        for _, _, inner in pages:
            urls |= asset_urls(inner)
        names = {}
        for u in urls:
            names.setdefault(u.rsplit('/', 1)[1], set()).add(u)
        clash = {k: v for k, v in names.items() if len(v) > 1}
        assert not clash, clash
        download(urls)

    svg_files = set()
    routes_js = []
    for route, wrap_cls, inner in pages:
        name = comp_name(route)
        frag = mark_reveal(externalize_svgs(scrub_text(inner), svg_files))
        jsx = to_jsx(frag, svg_files)
        with open(os.path.join(PAGES, name + '.jsx'), 'w', encoding='utf-8') as fh:
            fh.write(f'export default function {name}() {{\n  return (\n    <div className="{wrap_cls}">\n{jsx}\n    </div>\n  )\n}}\n')
        routes_js.append(f"  '{route}/': () => import('./{name}.jsx'),")
        print(f'{route:52} {name}.jsx {len(jsx):>9,} bytes')
    with open(os.path.join(PAGES, 'routes.js'), 'w', encoding='utf-8') as fh:
        fh.write('// generated by tools/live2jsx.py\nexport const routes = {\n' + '\n'.join(routes_js) + '\n}\n')


if __name__ == '__main__':
    main()
