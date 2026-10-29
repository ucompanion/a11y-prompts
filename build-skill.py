#!/usr/bin/env python3
"""실무 체크리스트 HTML(pages/)을 웹접근성 스킬 참조 파일(web-accessibility/references/)로 변환한다.

원본은 HTML이다. 스킬 파일은 직접 고치지 말고 이 스크립트로 다시 생성한다.
  python3 build-skill.py [스킬 폴더]
"""
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

LEVELS = {
    1: ('lv-l1', 'L1 기본 준수'),
    2: ('lv-l2', 'L2 전문 준수'),
    3: ('lv-l3', 'L3 품질마크'),
}


def read(name):
    with open(os.path.join(ROOT, 'pages', name + '.html'), encoding='utf-8') as f:
        return f.read()


def inline(h):
    """HTML 조각 → 마크다운 인라인 텍스트. <code> 안의 꺾쇠(<button> 등)는 보존한다."""
    stash = []

    def keep(m):
        stash.append('`' + html.unescape(m.group(1)) + '`')
        return '\x00%d\x00' % (len(stash) - 1)

    h = re.sub(r'<code>(.*?)</code>', keep, h, flags=re.S)
    h = re.sub(r'<strong>(.*?)</strong>', r'**\1**', h, flags=re.S)
    h = re.sub(r'<br\s*/?>', ' / ', h)
    h = re.sub(r'<span class="blind">.*?</span>', '', h, flags=re.S)
    h = re.sub(r'<[^>]+>', '', h)
    h = re.sub(r'\s+', ' ', html.unescape(h)).strip()
    return re.sub(r'\x00(\d+)\x00', lambda m: stash[int(m.group(1))], h)


def cell(h):
    return inline(h).replace('|', '\\|')


def plain(text):
    """이미 텍스트인 값(대표 오류): 꺾쇠 태그 모양은 백틱으로 감싼다."""
    return re.sub(r'((?:<[^>]+>)+)', r'`\1`', text).replace('|', '\\|')


def table_md(head, rows):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '|'.join(['---'] * len(head)) + '|']
    out += ['| ' + ' | '.join(cell(c) for c in r) + ' |' for r in rows]
    return '\n'.join(out)


def plain_table(t):
    """th 한 줄 머리글 + td 행으로 된 단순 표."""
    head = [inline(x) for x in re.findall(r'<th[^>]*>(.*?)</th>', t.split('</thead>')[0], re.S)]
    rows = [re.findall(r'<td[^>]*>(.*?)</td>', r, re.S) for r in re.findall(r'<tr>(.*?)</tr>', t.split('</thead>')[1], re.S)]
    return table_md(head, rows)


def errors_from_title(attr):
    """title 속성의 대표 오류를 한 줄 텍스트로."""
    if not attr:
        return ''
    t = html.unescape(attr)
    if t.startswith('대표 오류: '):
        return t[len('대표 오류: '):]
    lines = [x.lstrip('· ').strip() for x in t.split('\n')[1:] if x.strip()]
    return ' / '.join(lines)


def sections(sec):
    """<h3> 기준으로 섹션 이름 → 본문 HTML."""
    parts = re.split(r'(?=<h3>)', sec)
    out = {}
    for p in parts[1:]:
        m = re.match(r'<h3>(.*?)</h3>(.*)', p, re.S)
        out[m.group(1)] = m.group(2)
    return out


def parse_items(body):
    """항목별 규칙 표 → [(제목, 판정 기준, [(유형 td 속성, 유형, 적용, 구현), ...])]"""
    t = re.search(r'<table.*?</table>', body, re.S).group(0)
    items = []
    for r in re.findall(r'<tr>(.*?)</tr>', t.split('</thead>')[1], re.S):
        th = re.search(r'<th scope="rowgroup"[^>]*>(.*?)</th>', r, re.S)
        tds = list(re.finditer(r'<td([^>]*)>(.*?)</td>', r, re.S))
        if th:
            title = inline(re.search(r'<span class="rule-title">(.*?)</span>', th.group(1), re.S).group(1))
            crit = re.search(r'<span class="rule-crit">(.*?)</span>', th.group(1), re.S)
            items.append((title, inline(crit.group(1)) if crit else '', []))
        items[-1][2].append((tds[0].group(1), tds[0].group(2), tds[1].group(2), tds[2].group(2)))
    return items


def err_of(attrs):
    attr = re.search(r'title="([^"]*)"', attrs)
    return plain(errors_from_title(attr.group(1) if attr else ''))


def items_md(body, has_judge):
    lines = []
    for title, crit, rows in parse_items(body):
        if lines:
            lines.append('')
        lines += ['### ' + title, '']
        if crit and has_judge:
            lines += ['판정 기준: ' + crit, '']
        lines += ['| 유형 | 적용 | 구현 | 대표 오류 |', '|---|---|---|---|']
        for attrs, kind, apply_, impl in rows:
            lines.append('| ' + ' | '.join([cell(kind), cell(apply_), cell(impl), err_of(attrs)]) + ' |')
    return '\n'.join(lines)


def items_md_slim(body):
    """L1: data-skill 표시가 있는 유형만. 적용 열은 모두 '준수'라 생략한다."""
    lines = []
    for title, _, rows in parse_items(body):
        rows = [r for r in rows if 'data-skill=' in r[0]]
        if not rows:
            continue
        if lines:
            lines.append('')
        lines += ['### ' + title, '', '| 유형 | 구현 | 대표 오류 |', '|---|---|---|']
        for attrs, kind, apply_, impl in rows:
            assert inline(apply_) == '준수', title
            lines.append('| ' + ' | '.join([cell(kind), cell(impl), err_of(attrs)]) + ' |')
    return '\n'.join(lines)


# L1은 기준(전체 표)과 별개로, 스킬에는 아래 지시와 표시된 유형만 싣는다. 근거는 pages/lv-overview.html "L1 스킬 반영 기준".
L1_DIRECTIVES = [
    '아래 기준에 못 미치는 것만 고치고, 이미 충족한 것은 그대로 둔다. 기존 구조와 디자인은 바꾸지 않는다.',
    '대체 텍스트, 레이블, 제목은 시안 문구를 근거로 쓴다.',
]


def build_level1_inline():
    """SKILL.md에 내장할 L1 섹션(별도 참조 파일 없음)."""
    sec = re.search(r'<section.*?</section>', read('lv-l1'), re.S).group(0)
    s = sections(sec)
    md = ['**작업 지시**', '']
    md += ['%d. %s' % (i, d) for i, d in enumerate(L1_DIRECTIVES, 1)]
    md += ['', '**항목별 규칙**: 클로드가 따로 지시받지 않으면 놓치거나 팀 규약과 달라지기 쉬운 유형만 싣는다.', '']
    md += [items_md_slim(s['항목별 규칙']), '']
    md += ['**완료 점검**', '']
    for li in re.findall(r'<label[^>]*>(.*?)</label>', s['완료 점검'], re.S):
        md.append('- [ ] ' + inline(li))
    return '\n'.join(md) + '\n'


def build_level(n):
    page, name = LEVELS[n]
    sec = re.search(r'<section.*?</section>', read(page), re.S).group(0)
    s = sections(sec)
    md = ['# ' + name + ' 기준', '', '이 파일은 **' + name + '** 기준이다. 다른 수준의 파일과 섞어 쓰지 않는다.', '']
    md += ['## 적용 기준', '', inline(re.search(r'<p>(.*?)</p>', s['적용 기준'], re.S).group(1)), '']
    md += ['## 작업 지시', '']
    for i, li in enumerate(re.findall(r'<li>(.*?)</li>', s['작업 지시'], re.S), 1):
        md.append('%d. %s' % (i, inline(li)))
    md += ['', '## 항목별 규칙', '']
    if n >= 2:
        md += ['항목별로 판정 기준과 유형별 적용·구현을 정리했다. "적용"이 "조건부"이면 구현 칸의 조건을 따른다.', '']
    else:
        md += ['핵심 항목만 다룬다. 표에 없는 항목은 검토하거나 언급하지 않는다. "조건부"는 구현 칸의 조건을 따른다.', '']
    md += [items_md(s['항목별 규칙'], n >= 2), '']
    if n >= 2:
        md += ['## 컴포넌트 패턴', '', '탭, 모달 같은 커스텀 컴포넌트를 만들 때는 `components.md`의 필수 마크업과 키보드·초점 동작을 따른다.', '']
    if '놓치기 쉬운 영역' in s:
        t = re.search(r'<table.*?</table>', s['놓치기 쉬운 영역'], re.S).group(0)
        md += ['## 놓치기 쉬운 영역', '', plain_table(t), '']
    md += ['## 완료 점검', '']
    for li in re.findall(r'<label[^>]*>(.*?)</label>', s['완료 점검'], re.S):
        md.append('- [ ] ' + inline(li))
    return '\n'.join(md) + '\n'


def build_components():
    sec = re.search(r'<section.*?</section>', read('base-components'), re.S).group(0)
    t = re.search(r'<table.*?</table>', sec, re.S).group(0)
    md = ['# 컴포넌트별 체크리스트', '',
          '자주 만드는 UI 컴포넌트마다 꼭 들어가야 할 마크업과 키보드·초점 동작이다. L2·L3 작업에서 탭, 모달 같은 커스텀 컴포넌트를 만들 때 따른다. L1에서는 기준으로 지정하지 않으며 직접 판단해 처리한다.', '',
          plain_table(t)]
    return '\n'.join(md) + '\n'


L1_START, L1_END = '<!-- L1:start -->', '<!-- L1:end -->'


def main(skill_dir):
    out = os.path.join(skill_dir, 'references')
    os.makedirs(out, exist_ok=True)
    # L1은 SKILL.md에 내장하므로 level-1.md를 만들지 않는다.
    files = {'level-%d.md' % n: build_level(n) for n in LEVELS if n > 1}
    files['components.md'] = build_components()
    for name, text in files.items():
        with open(os.path.join(out, name), 'w', encoding='utf-8') as f:
            f.write(text)
        print(name, len(text.splitlines()), 'lines', len(text), 'chars')
    path = os.path.join(skill_dir, 'SKILL.md')
    with open(path, encoding='utf-8') as f:
        md = f.read()
    if L1_START not in md or L1_END not in md:
        print('SKILL.md에 L1 표식(%s ... %s)이 없어 L1 섹션은 건너뜀' % (L1_START, L1_END))
        return
    head, rest = md.split(L1_START, 1)
    tail = rest.split(L1_END, 1)[1]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(head + L1_START + '\n' + build_level1_inline() + L1_END + tail)
    print('SKILL.md L1 섹션', len(build_level1_inline()), 'chars')


if __name__ == '__main__':
    # 인자: 스킬 폴더(기본 web-accessibility). 점검용으로 다른 폴더를 줄 수 있다.
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'web-accessibility'))
