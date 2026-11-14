"""Find the translatable Korean units in the built dashboard page.
units(html_text) -> list of (start, end, kind, text): kind 'h' html run, 'a' attribute value, 'j' js string literal body (outermost)."""
import re
HG = re.compile(r'[가-힣]')
INLINE = {'b', 'strong', 'em', 'i', 'code', 'a', 'sup', 'sub', 'u', 'mark', 'br'}


def js_units(s, base):
    out, i, n = [], 0, len(s)
    prev_sig = ''                      # last significant char, to tell a regex from a division

    def skip_tpl(j):                   # j just after the opening backtick; returns index after the closing one
        while j < n:
            c = s[j]
            if c == '\\': j += 2; continue
            if c == '`': return j + 1
            if c == '$' and s[j + 1:j + 2] == '{':
                j = skip_expr(j + 2); continue
            j += 1
        raise ValueError('open template')

    def skip_str(j, q):
        while j < n:
            c = s[j]
            if c == '\\': j += 2; continue
            if c == q: return j + 1
            j += 1
        raise ValueError('open string')

    def skip_expr(j):                  # inside ${ ... }: returns index after the matching }
        d = 0
        while j < n:
            c = s[j]
            if c in '\'"': j = skip_str(j + 1, c); continue
            if c == '`': j = skip_tpl(j + 1); continue
            if c == '{': d += 1
            elif c == '}':
                if d == 0: return j + 1
                d -= 1
            j += 1
        raise ValueError('open ${')

    while i < n:
        c = s[i]
        if c == '/' and s[i + 1:i + 2] == '/':
            j = s.find('\n', i); i = n if j < 0 else j; continue
        if c == '/' and s[i + 1:i + 2] == '*':
            i = s.index('*/', i) + 2; continue
        if c == '/' and (prev_sig in '(,=:[!&|?{};\n' or prev_sig == ''):      # regex literal
            j, cls = i + 1, False
            while j < n and (s[j] != '/' or cls):
                if s[j] == '\\': j += 1
                elif s[j] == '[': cls = True
                elif s[j] == ']': cls = False
                elif s[j] == '\n': break
                j += 1
            if j < n and s[j] == '/':
                i = j + 1; prev_sig = '/'; continue
        if c in '\'"':
            j = skip_str(i + 1, c)
            if HG.search(s[i + 1:j - 1]): out.append((base + i + 1, base + j - 1, 'j' + c, s[i + 1:j - 1]))
            i = j; prev_sig = c; continue
        if c == '`':
            j = skip_tpl(i + 1)
            if HG.search(s[i + 1:j - 1]): out.append((base + i + 1, base + j - 1, 'j`', s[i + 1:j - 1]))
            i = j; prev_sig = c; continue
        if not c.isspace(): prev_sig = c
        elif c == '\n' and prev_sig not in ')]}' and False: prev_sig = '\n'
        i += 1
    return out


def html_units(s, a, b):
    out = []
    toks = [(m.start() + a, m.end() + a, m.group(0)) for m in re.finditer(r'<!--.*?-->|<[^>]+>|[^<]+', s[a:b], re.S)]
    run = []

    def flush():
        while run and (run[0][2].startswith('<') or not run[0][2].strip()): run.pop(0)
        while run and (run[-1][2].startswith('<') or not run[-1][2].strip()): run.pop()
        if run:
            x0 = run[0][0] + len(run[0][2]) - len(run[0][2].lstrip()); x1 = run[-1][1] - (len(run[-1][2]) - len(run[-1][2].rstrip()))
            t = s[x0:x1]
            if HG.search(re.sub(r'<[^>]+>', '', t)): out.append((x0, x1, 'h', t))
        run.clear()
    for x0, x1, t in toks:
        if t.startswith('<'):
            for m in re.finditer(r'\b(content|title|aria-label|placeholder|alt)="([^"]*[가-힣][^"]*)"', t):
                out.append((x0 + m.start(2), x0 + m.end(2), 'a', m.group(2)))
            name = re.match(r'</?\s*([a-zA-Z0-9]+)', t)
            if name and name.group(1).lower() in INLINE and run: run.append((x0, x1, t))
            else: flush()
        else: run.append((x0, x1, t))
    flush()
    return out


def units(s):
    out, pos = [], 0
    for m in re.finditer(r'<(script|style)\b[^>]*>(.*?)</\1>', s, re.S):
        out += html_units(s, pos, m.start(2))
        if m.group(1) == 'script': out += js_units(m.group(2), m.start(2))
        pos = m.end(2)
    out += html_units(s, pos, len(s))
    return sorted(out)
