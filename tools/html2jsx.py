"""Convert the saved Coda homepage body into React section components.

Usage: python3 tools/html2jsx.py
Writes src/components/*.jsx and public/svg/inline/*.svg
"""
import os
import re
from html.parser import HTMLParser

from _lib import OUT, SRC, SVG_OUT, externalize_svgs, to_jsx, component

SECTIONS = [
    ('hero', 'Hero'),
    ('products-hightlight', 'ProductsHighlight'),
    ('benefits-stack', 'BenefitsStack'),
    ('metrics', 'Metrics'),
    ('awards', 'Awards'),
    ('card-carousel', 'CardCarousel'),
    ('press-carousel', 'PressCarousel'),
    ('pre-footer', 'PreFooter'),
]
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}


class Spans(HTMLParser):
    """Record [start, end) character offsets of every element."""

    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text = text
        self.line_off = [0]
        # HTMLParser counts lines by "\n" only; str.splitlines() would also split on U+2028 etc.
        for line in text.split('\n'):
            self.line_off.append(self.line_off[-1] + len(line) + 1)
        self.stack, self.spans = [], []

    def off(self):
        ln, col = self.getpos()
        return self.line_off[ln - 1] + col

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        self.stack.append((tag, dict(attrs), self.off(), len(self.stack)))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        while self.stack:
            t, a, s, d = self.stack.pop()
            end = self.text.find('>', self.off()) + 1
            self.spans.append((t, a, s, end, d))
            if t == tag:
                break


SLIDE = ('w-full h-full relative overflow-hidden', 'inline-media ')


def mark_reveal(html):
    # Coda's reveal wrapper (component M3 in client-*.js) renders "opacity-0 [translate-y-7]" plus
    # an inline transition-duration; class order varies between blocks. The saved/crawled copies
    # froze some of them mid/after reveal; reset all to the pre-reveal state and give them a hook
    # for src/lib/reveal.js. SVG <line> hover arrows share the classes but have no inline duration.
    def repl(m):
        toks = m.group(1).split()
        revealed = {'opacity-100', 'translate-y-0', 'scale-100'} <= set(toks)
        if 'opacity-0' not in toks and not revealed:
            return m.group(0)
        rest = ' '.join(t for t in toks if t not in ('opacity-0', 'opacity-100', 'translate-y-0', 'scale-100'))
        slide = 'translate-y-7' in toks or any(rest.startswith('transition-all ' + k) for k in SLIDE)
        toks = [t for t in toks if t not in ('opacity-100', 'translate-y-0', 'scale-100', 'translate-y-7')]
        if 'opacity-0' not in toks:
            toks.insert(toks.index('transition-all') + 1 if 'transition-all' in toks else 0, 'opacity-0')
        if slide:
            toks.insert(toks.index('opacity-0') + 1, 'translate-y-7')
        return f'<div data-reveal="" class="{" ".join(toks)}" style="{m.group(2)}"'
    return re.sub(r'<div class="([^"]*)" style="([^"]*transition-duration:500ms[^"]*)"', repl, html)


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SVG_OUT, exist_ok=True)
    h = open(SRC, encoding='utf-8').read()
    body = h[h.find('<body'):h.find('<aside id="usercentrics-cmp-ui"')]
    body = re.sub(r'<script\b.*?</script>', '', body, flags=re.S)
    body = re.sub(r'<noscript\b.*?</noscript>', '', body, flags=re.S)
    body = re.sub(r'<iframe\b.*?</iframe>', '', body, flags=re.S)
    body = re.sub(r'<!--.*?-->', '', body, flags=re.S)

    p = Spans(body)
    p.feed(body)
    spans = p.spans

    def first(pred):
        return min((s for s in spans if pred(s)), key=lambda s: s[2])

    root = first(lambda s: s[1].get('id') == 'root')
    locale = first(lambda s: s[1].get('data-locale') == 'en')
    kids = sorted((s for s in spans if s[4] == locale[4] + 1 and locale[2] < s[2] < locale[3]), key=lambda s: s[2])
    main_wrap = next(k for k in kids if 'mt-navBarInnerTopBase' in (k[1].get('class') or ''))
    header_parts = [k for k in kids if k[2] < main_wrap[2]]
    footer = next(k for k in kids if k[2] > main_wrap[2])

    header_html = ''.join(body[k[2]:k[3]] for k in header_parts)
    footer_html = body[footer[2]:footer[3]]
    wrap_open = body[main_wrap[2]:body.find('>', main_wrap[2]) + 1]
    wrap_cls = re.search(r'class="([^"]*)"', wrap_open).group(1)

    sec_spans = sorted((s for s in spans if s[4] == main_wrap[4] + 1 and main_wrap[2] < s[2] < main_wrap[3]),
                       key=lambda s: s[2])
    parts = [('Header', header_html)]
    names = []
    for s in sec_spans:
        cls = s[1].get('class') or ''
        name = next(n for key, n in SECTIONS if re.search(r'(^|\s)' + re.escape(key) + r'(\s|$)', cls))
        names.append(name)
        parts.append((name, body[s[2]:s[3]]))
    assert names == [n for _, n in SECTIONS], names
    parts.append(('Footer', footer_html))

    svg_files = set()
    for n, frag in parts:
        frag = mark_reveal(externalize_svgs(frag, svg_files))
        jsx = to_jsx(frag, svg_files)
        with open(os.path.join(OUT, n + '.jsx'), 'w', encoding='utf-8') as f:
            f.write(component(n, jsx))
        print(f'{n}.jsx {len(jsx):>9,} bytes')

    imports = ''.join(f"import {n} from './{n}.jsx'\n" for n in names)
    inner = '\n'.join(f'      <{n} />' for n in names)
    with open(os.path.join(OUT, 'Main.jsx'), 'w', encoding='utf-8') as f:
        f.write(imports + f'\nexport default function Main() {{\n  return (\n    <div className="{wrap_cls}">\n{inner}\n    </div>\n  )\n}}\n')
    print('externalized svgs:', len(svg_files))


if __name__ == '__main__':
    main()
