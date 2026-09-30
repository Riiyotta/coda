"""Swap placeholder text in page components for the real text from the user's own saved copies.

Usage: python3 tools/restore_text.py [--dry]
The page JSX has hand edits (hooks, React ports), so it isn't regenerated. Instead the ordered
text literals of the current JSX are aligned with those of the saved page; runs that differ
(the placeholders) are replaced one-for-one.
"""
import difflib
import json
import os
import re
import sys

from _lib import ROOT, externalize_svgs, to_jsx
from html2jsx import Spans

# saved file (in the project root) -> page component, matched by page content, not by the
# file's title/"saved from" line (the browser records the URL of the first page in the tab)
SAVED = {
    'Create Payment Links for Global Out-of-App Sales.html': 'ProductCodaLinksPage',
    'Automate Instant Incentives_ B2B Digital Rewards Platform.html': 'ProductCodaGiftcloudPage',
    'Own Your Branded Storefront_ AI-Powered & Fully Managed.html': 'ProductDistributionPage',
    'Sell Globally_ Instant Distribution to 800M+ Active Users.html': 'ProductCodaConsumerPlatformsPage',
    'Coda Pricing_ Codapay Fees, Webstore & Distribution Rates.html': 'PricingPage',
}
LIT = re.compile(r'\{("(?:[^"\\]|\\.)*")\}')


def saved_texts(path):
    h = open(path, encoding='utf-8').read()
    body = h[h.find('<body'):]
    for tag in ('script', 'noscript', 'iframe', 'style'):
        body = re.sub(rf'<{tag}\b.*?</{tag}>', '', body, flags=re.S)
    body = re.sub(r'<!--.*?-->', '', body, flags=re.S)
    p = Spans(body)
    p.feed(body)
    mw = min((s for s in p.spans if 'mt-navBarInnerTopBase' in (s[1].get('class') or '')), key=lambda s: s[2])
    jsx = to_jsx(externalize_svgs(body[mw[2]:mw[3]], set()), set())
    return [json.loads(m.group(1)) for m in LIT.finditer(jsx)]


def words(s):
    return len(s.split())


def main():
    dry = '--dry' in sys.argv
    for fname, comp in SAVED.items():
        src = saved_texts(os.path.join(ROOT, fname))
        path = os.path.join(ROOT, 'src', 'pages', comp + '.jsx')
        jsx = open(path, encoding='utf-8').read()
        lits = list(LIT.finditer(jsx))
        cur = [json.loads(m.group(1)) for m in lits]
        key = lambda s: s if words(s) < 9 else '\0long'   # placeholders only ever replaced 9+ word text
        sm = difflib.SequenceMatcher(None, [key(s) for s in cur], [key(s) for s in src], autojunk=False)
        repl, skipped = {}, 0
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == 'equal':
                for a, b in zip(range(i1, i2), range(j1, j2)):
                    if cur[a] != src[b] and words(cur[a]) >= 9:
                        repl[a] = src[b]
            elif op == 'replace' and i2 - i1 == j2 - j1:
                for a, b in zip(range(i1, i2), range(j1, j2)):
                    if cur[a] != src[b]:
                        repl[a] = src[b]
            elif op != 'equal':
                skipped += max(i2 - i1, j2 - j1)
        # length sanity check: placeholders were generated at the original length
        bad = [a for a, t in repl.items() if abs(len(t) - len(cur[a])) > max(12, len(t) * 0.25)]
        for a in bad:
            del repl[a]
        out, last = [], 0
        for idx, m in enumerate(lits):
            if idx in repl:
                out.append(jsx[last:m.start()] + '{' + json.dumps(repl[idx], ensure_ascii=False) + '}')
                last = m.end()
        out.append(jsx[last:])
        print(f'{comp:36} literals {len(cur):4}  saved {len(src):4}  replaced {len(repl):3}  '
              f'rejected(length) {len(bad)}  unaligned {skipped}')
        if not dry:
            open(path, 'w', encoding='utf-8').write(''.join(out))


if __name__ == '__main__':
    main()
