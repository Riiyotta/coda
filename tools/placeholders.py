"""List (or fill) the placeholder text slots in page components.

  python3 tools/placeholders.py extract OUT_DIR   -> OUT_DIR/<Page>.json with, per slot: index, length,
                                                    section block and the nearby real headings/labels
  python3 tools/placeholders.py apply IN_DIR      -> replaces slots with IN_DIR/<Page>.copy.json {index: text}

A literal is a placeholder slot when it differs from the corresponding literal of the generated
source (tools/live2jsx.py replaced every 9+ word text). Only slot positions and lengths are exported;
the new copy is written from the page's own headings, not from the source text.
"""
import difflib
import json
import os
import re
import sys

from _lib import ROOT, externalize_svgs, to_jsx
from html2jsx import Spans

PAGES = {
    'ProductCodapayPage': 'product_codapay',
    'ProductCodaWebstorePage': 'product_coda-webstore',
    'IndustriesCreatorEconomyPaymentsPage': 'industries_creator-economy-payments',
    'IndustriesDatingAppPaymentsPage': 'industries_dating-app-payments',
    'IndustriesDigitalEntertainmentPage': 'industries_digital-entertainment',
    'IndustriesEsimDigitalUtilityPaymentsPage': 'industries_esim-digital-utility-payments',
    'IndustriesLearningManagementSystemPaymentsPage': 'industries_learning-management-system-payments',
    'IndustriesOnlineGamingPaymentsPage': 'industries_online-gaming-payments',
    'UseCaseMerchantOfRecordPage': 'use-case_merchant-of-record',
}
LIT = re.compile(r'\{("(?:[^"\\]|\\.)*")\}')
BLOCK = re.compile(r'className="(?:transition-all )?(?:opacity-0 )?(?:translate-y-7 )?'
                   r'(hero|benefits-stack|highlighted-mega|impact-figures|feature-callout|section-bridge|metrics|'
                   r'card-carousel|faq|pre-footer|features-stack|feature-grid|isolated-callout|page-tiles|'
                   r'integration-comparison|price-stack|products-hightlight)\b')


def source_lengths(crawl_name):
    h = open(os.path.join(ROOT, 'crawl', crawl_name + '.html'), encoding='utf-8').read()
    body = h[h.find('<body'):]
    for tag in ('script', 'noscript', 'iframe', 'style'):
        body = re.sub(rf'<{tag}\b.*?</{tag}>', '', body, flags=re.S)
    body = re.sub(r'<!--.*?-->', '', body, flags=re.S)
    p = Spans(body)
    p.feed(body)
    mw = min((s for s in p.spans if 'mt-navBarInnerTopBase' in (s[1].get('class') or '')), key=lambda s: s[2])
    jsx = to_jsx(externalize_svgs(body[mw[2]:mw[3]], set()), set())
    return [json.loads(m.group(1)) for m in LIT.finditer(jsx)]


def slots(comp):
    jsx = open(os.path.join(ROOT, 'src', 'pages', comp + '.jsx'), encoding='utf-8').read()
    lits = list(LIT.finditer(jsx))
    cur = [json.loads(m.group(1)) for m in lits]
    src = source_lengths(PAGES[comp])
    key = lambda s: s if len(s.split()) < 9 else '\0long'
    sm = difflib.SequenceMatcher(None, [key(s) for s in cur], [key(s) for s in src], autojunk=False)
    idx = set()
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal' or (op == 'replace' and i2 - i1 == j2 - j1):
            for a, b in zip(range(i1, i2), range(j1, j2)):
                if cur[a] != src[b] and len(src[b].split()) >= 9:
                    idx.add(a)
    return jsx, lits, cur, sorted(idx)


def extract(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for comp in PAGES:
        jsx, lits, cur, idx = slots(comp)
        items = []
        for a in idx:
            pos = lits[a].start()
            blocks = BLOCK.findall(jsx[:pos])
            before = [t for t in cur[max(0, a - 6):a] if t.strip() and a - 6 >= 0 or True][-6:]
            ctx = [t for t in cur[max(0, a - 8):a] if t.strip() and len(t.split()) < 9][-4:]
            after = [t for t in cur[a + 1:a + 6] if t.strip() and len(t.split()) < 9][:2]
            items.append({'index': a, 'length': len(cur[a]), 'block': blocks[-1] if blocks else '',
                          'ends_with': cur[a].rstrip()[-1:] if cur[a].rstrip()[-1:] in '.?!:' else '',
                          'labels_before': ctx, 'labels_after': after})
        with open(os.path.join(out_dir, comp + '.json'), 'w') as f:
            json.dump({'page': comp, 'route': '/' + PAGES[comp].replace('_', '/', 1) + '/', 'slots': items}, f, indent=1)
        print(f'{comp:48} slots {len(items)}')


def apply(in_dir):
    for comp in PAGES:
        cf = os.path.join(in_dir, comp + '.copy.json')
        if not os.path.exists(cf):
            print(f'{comp:48} no copy file, skipped')
            continue
        copy = {int(k): v for k, v in json.load(open(cf)).items()}
        jsx, lits, cur, idx = slots(comp)
        bad = [a for a in copy if a not in idx or abs(len(copy[a]) - len(cur[a])) > max(12, 0.2 * len(cur[a]))]
        missing = [a for a in idx if a not in copy]
        out, last = [], 0
        for a, m in enumerate(lits):
            if a in copy and a not in bad:
                out.append(jsx[last:m.start()] + '{' + json.dumps(copy[a], ensure_ascii=False) + '}')
                last = m.end()
        out.append(jsx[last:])
        open(os.path.join(ROOT, 'src', 'pages', comp + '.jsx'), 'w', encoding='utf-8').write(''.join(out))
        print(f'{comp:48} applied {len(copy) - len(bad)}  rejected {bad}  missing {missing}')


if __name__ == '__main__':
    {'extract': extract, 'apply': apply}[sys.argv[1]](sys.argv[2])
