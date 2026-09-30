"""Convert the saved Tennr.html body into React section components.

Usage: python3 tools/html2jsx.py
Writes app/src/components/*.jsx and app/public/svg/inline/*.svg
"""
import hashlib
import json
import os
import re
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'Accept Payments, Build Webstores & Expand Distribution Globally.html')
OUT = os.path.join(ROOT, 'src', 'components')
SVG_OUT = os.path.join(ROOT, 'public', 'svg', 'inline')
IMG_DIR = os.path.join(ROOT, 'public', 'images')
# pages built in this clone (path without trailing slash); everything else becomes an inert "#"
ROUTES = {
    '/product/codapay', '/product/coda-links', '/product/coda-webstore', '/product/distribution',
    '/product/coda-consumer-platforms', '/product/coda-giftcloud',
    '/industries/creator-economy-payments', '/industries/dating-app-payments', '/industries/digital-entertainment',
    '/industries/esim-digital-utility-payments', '/industries/learning-management-system-payments',
    '/industries/online-gaming-payments', '/use-case/merchant-of-record', '/pricing',
}
BIG_SVG = 15000

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}
SVG_TAGS = {t.lower(): t for t in [
    'clipPath', 'linearGradient', 'radialGradient', 'feGaussianBlur', 'feOffset', 'feBlend', 'feColorMatrix',
    'feComposite', 'feFlood', 'feMerge', 'feMergeNode', 'feMorphology', 'feTurbulence', 'feDisplacementMap',
    'feDropShadow', 'foreignObject', 'textPath', 'animateTransform', 'animateMotion']}
ATTR_MAP = {
    'class': 'className', 'classname': 'className', 'for': 'htmlFor', 'tabindex': 'tabIndex', 'srcset': 'srcSet', 'autocomplete': 'autoComplete',
    'crossorigin': 'crossOrigin', 'allowfullscreen': 'allowFullScreen', 'frameborder': 'frameBorder',
    'readonly': 'readOnly', 'maxlength': 'maxLength', 'colspan': 'colSpan', 'rowspan': 'rowSpan',
    'datetime': 'dateTime', 'playsinline': 'playsInline', 'autoplay': 'autoPlay', 'enctype': 'encType',
    'http-equiv': 'httpEquiv', 'fetchpriority': 'fetchPriority', 'referrerpolicy': 'referrerPolicy',
    'contenteditable': 'contentEditable', 'spellcheck': 'spellCheck', 'inputmode': 'inputMode',
    'novalidate': 'noValidate', 'viewbox': 'viewBox', 'preserveaspectratio': 'preserveAspectRatio',
    'gradientunits': 'gradientUnits', 'gradienttransform': 'gradientTransform', 'patternunits': 'patternUnits',
    'patterncontentunits': 'patternContentUnits', 'patterntransform': 'patternTransform',
    'stddeviation': 'stdDeviation', 'filterunits': 'filterUnits', 'maskunits': 'maskUnits',
    'maskcontentunits': 'maskContentUnits', 'clippathunits': 'clipPathUnits', 'primitiveunits': 'primitiveUnits',
    'xlink:href': 'xlinkHref', 'xml:space': 'xmlSpace', 'xmlns:xlink': 'xmlnsXlink', 'value': 'defaultValue',
    'checked': 'defaultChecked', 'srcdoc': 'srcDoc', 'accept-charset': 'acceptCharset', 'itemprop': 'itemProp',
    'itemscope': 'itemScope', 'controlslist': 'controlsList', 'disablepictureinpicture': 'disablePictureInPicture', 'itemtype': 'itemType', 'shadowrootmode': None,
}
BOOL_ATTRS = {'autoPlay', 'loop', 'muted', 'playsInline', 'controls', 'disabled', 'hidden', 'required', 'defaultChecked',
              'readOnly', 'multiple', 'allowFullScreen', 'noValidate', 'async', 'defer', 'open'}
SKIP_TAGS = {'script', 'noscript', 'iframe', 'next-route-announcer', 'template', 'style'}


def camel(name):
    return re.sub(r'-([a-z])', lambda m: m.group(1).upper(), name)


def style_obj(css):
    parts, depth, cur, quote = [], 0, '', None
    for ch in css:
        if quote:
            cur += ch
            if ch == quote:
                quote = None
            continue
        if ch in '"\'':
            quote = ch
        elif ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        elif ch == ';' and depth == 0:
            parts.append(cur)
            cur = ''
            continue
        cur += ch
    parts.append(cur)
    obj = {}
    for p in parts:
        if ':' not in p:
            continue
        k, v = p.split(':', 1)
        k, v = k.strip(), v.strip()
        if not k:
            continue
        if not k.startswith('--'):
            k = k.lower()
            if k.startswith('-ms-'):
                k = 'ms' + camel(k[3:])[0:]
            elif k.startswith('-'):
                k = camel(k[1:])
                k = k[0].upper() + k[1:]
            else:
                k = camel(k)
        obj[k] = v
    return json.dumps(obj, ensure_ascii=False)


SAVED = './Accept Payments, Build Webstores &amp; Expand Distribution Globally_files/'
SAVED2 = './Accept Payments, Build Webstores & Expand Distribution Globally_files/'


def local_asset(u):
    u = u.replace(SAVED, '/images/').replace(SAVED2, '/images/')
    if u.startswith('/images/'):
        return u
    m = re.match(r'https://www\.coda\.co/wp-content/uploads/\d+/\d+/(.+)$', u)
    if m:
        name = m.group(1)
        if name.endswith('.mp4'):
            return '/video/' + name
        if os.path.exists(os.path.join(IMG_DIR, name)):
            return '/images/' + name
    return None


def fix_srcset(v):
    keep = []
    for cand in v.split(','):
        parts = cand.strip().split()
        if not parts:
            continue
        loc = local_asset(parts[0])
        if loc:
            keep.append(' '.join([loc] + parts[1:]))
    return ', '.join(keep)


def fix_url(v, name='src'):
    if name == 'srcSet':
        return fix_srcset(v)
    loc = local_asset(v)
    if loc:
        return loc
    if name == 'href':
        if re.match(r'^https://www\.coda\.co/?(\?ref=saaspo\.com)?$', v):
            return '/'
        m = re.match(r'^https://www\.coda\.co(/[^?#]*?)/?(?:[?#].*)?$', v)
        if m and m.group(1) in ROUTES:
            return m.group(1) + '/'
        # every other destination is a page that is not part of this clone
        return '#'
    return v


def attr_jsx(tag, name, value, in_svg):
    if name.startswith('on'):
        return None
    mapped = ATTR_MAP.get(name, name) if name in ATTR_MAP else name
    if mapped is None:
        return None
    if in_svg and '-' in mapped and not mapped.startswith(('data-', 'aria-')):
        mapped = camel(mapped)
    if value is None or (value == '' and mapped in BOOL_ATTRS):
        return mapped
    if mapped == 'style':
        return 'style={' + style_obj(value) + '}'
    if mapped in ('src', 'href', 'srcSet', 'poster', 'xlinkHref'):
        value = fix_url(value, mapped)
    return f'{mapped}={json.dumps(value, ensure_ascii=False)}' if ('"' in value or '\\' in value or '\n' in value) \
        else f'{mapped}="{value}"'


class Conv(HTMLParser):
    def __init__(self, svg_files):
        super().__init__(convert_charrefs=True)
        self.out, self.stack, self.skip = [], [], 0
        self.svg_files = svg_files

    def in_svg(self):
        return 'svg' in self.stack

    def handle_starttag(self, tag, attrs):
        if self.skip or (tag in SKIP_TAGS and not (tag == 'style' and self.in_svg())):
            if tag not in VOID:
                self.skip += 1
            return
        real = SVG_TAGS.get(tag, tag) if self.in_svg() or tag == 'svg' else tag
        in_svg = self.in_svg() or tag == 'svg'
        a = [x for x in (attr_jsx(tag, n, v, in_svg) for n, v in attrs) if x]
        self.out.append('<' + real + (' ' + ' '.join(a) if a else '') + (' />' if tag in VOID else '>'))
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        if self.skip or tag in SKIP_TAGS:
            return
        in_svg = self.in_svg() or tag == 'svg'
        real = SVG_TAGS.get(tag, tag) if in_svg else tag
        a = [x for x in (attr_jsx(tag, n, v, in_svg) for n, v in attrs) if x]
        self.out.append('<' + real + (' ' + ' '.join(a) if a else '') + ' />')

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.skip:
            if tag in SKIP_TAGS or self.skip:
                self.skip -= 1
            return
        # pop to matching tag
        while self.stack:
            t = self.stack.pop()
            real = SVG_TAGS.get(t, t) if (self.in_svg() or t == 'svg') else t
            self.out.append(f'</{real}>')
            if t == tag:
                break

    def handle_data(self, data):
        if self.skip:
            return
        if self.in_svg():
            if data.strip():
                self.out.append('{' + json.dumps(data, ensure_ascii=False) + '}')
            return
        if not data.strip():
            if self.stack and self.stack[-1] in ('table', 'tbody', 'thead', 'tr', 'colgroup'):
                return
            self.out.append('{" "}')
            return
        self.out.append('{' + json.dumps(data, ensure_ascii=False) + '}')

    def handle_comment(self, data):
        pass


def externalize_svgs(html, svg_files):
    def repl(m):
        svg = m.group(0)
        if len(svg) <= BIG_SVG or 'currentColor' in svg:
            return svg
        h = hashlib.md5(svg.encode()).hexdigest()[:12]
        path = os.path.join(SVG_OUT, h + '.svg')
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                f.write(svg if 'xmlns=' in svg else svg.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"', 1))
        svg_files.add(h)
        head = re.match(r'<svg\b([^>]*)>', svg).group(1)
        keep = ' '.join(re.findall(r'\b(?:width|height|class|style)="[^"]*"', head))
        return f'<img src="/svg/inline/{h}.svg" alt="" {keep}>'
    return re.sub(r'<svg\b.*?</svg>', repl, html, flags=re.S)


def to_jsx(html, svg_files):
    c = Conv(svg_files)
    c.feed(html)
    c.close()
    return ''.join(c.out)


def component(name, jsx):
    return f'export default function {name}() {{\n  return (\n    <>\n{jsx}\n    </>\n  )\n}}\n'


