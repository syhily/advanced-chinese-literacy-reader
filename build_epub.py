# -*- coding: utf-8 -*-
"""合并稿 Markdown -> EPUB3(带脚注弹注/尾注、三级目录)。纯标准库。"""
import re, os, zipfile, html, shutil
from xml.etree.ElementTree import parse as xmlparse

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '语文素养高级读本.md')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '语文素养高级读本.epub')
BUILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build', 'epub')

text = open(SRC).read()

# --- 切掉印刷版目录(页码对 EPUB 无意义) ---
lines = text.split('\n')
start = next(i for i, l in enumerate(lines) if l.strip() == '## 目录')
end = next(i for i, l in enumerate(lines) if l.strip().startswith('## 上编'))
del lines[start:end]
# 去掉开头两行碎片("七五" 等)
if lines[0].strip() == '七五':
    del lines[0:2]
# 封面页与书名页重复,只保留书名页(第二个「# 语文素养高级读本」起)
title_hits = [i for i, l in enumerate(lines[:40]) if l.strip() == '# 语文素养高级读本']
if len(title_hits) >= 2:
    del lines[:title_hits[1]]
text = '\n'.join(lines)

# --- 分离脚注定义 ---
defs = {}
def_lines = []
body_lines = []
for l in text.split('\n'):
    m = re.match(r'^\[\^(\d+)\]:\s*(.*)$', l)
    if m:
        defs[m.group(1)] = m.group(2).strip()
    elif l.strip() == '' and def_lines:
        continue
    else:
        body_lines.append(l)

UNIT = re.compile(r'^#+\s*(单元[一二三四五六七八九十]+.*)$')
BIAN = re.compile(r'^#+\s*((?:上|中|下)编\s+.*)$')
ART = re.compile(r'^#+\s*(\d+\s*-\s*\d+.*)$')
TIYAO = re.compile(r'（[^（）]{2,8}）\s*$')  # 各篇提要里的「标题（作者）」条目
SEC = re.compile(r'^#+\s*[\[（]?\s*(编读札记|思考与讨论|问题导引|各篇提要|关键词语|要点提炼|争议聚焦|拓展阅读指引|小结)\s*[\]）]?\s*$')
ANYH = re.compile(r'^(#+)\s*(.*)$')
IN_ARTICLE_SUBHEADS = {'汉语的特征', '汉字的特征', '中国语文的优点与缺陷', '解题', '反思', '建议',
    '语言就是内容', '语言的文化积淀', '言外之意', '气盛言宜', '视觉语言', '色、形、音',
    '随时锻炼语言', '训练语感', '惊人与平淡', '方言',
    '一、21 世纪，华语将在全世界华人中普遍推广',
    '二、21 世纪，汉字将成为定形、定量、规范统一的文字',
    '三、21 世纪，拼音将帮助华人在网络上便利流通',
    '汉语的强与弱', '汉语走强的战略与举措'}

ref_place = {}   # fn id -> (chapter href)
chapters = []    # {title, level, html}  level: 1 编 2 单元/前置 3 文章
cur = None       # 当前 chapter 的 html 行列表
cur_title = None
cur_level = 2
toc = []         # (level, title, href, article_children[])

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'\$([^\$]+)\$', r'\1', s)
    def fnref(m):
        n = m.group(1)
        ref_place[n] = cur_href
        return '<sup><a epub:type="noteref" id="fnref-%s" href="notes.xhtml#fn-%s">[%s]</a></sup>' % (n, n, n)
    s = re.sub(r'\[\^(\d+)\]', fnref, s)
    return s

def flush():
    global cur, cur_title
    if cur is not None and (cur or cur_title):
        d = {'title': cur_title, 'level': cur_level, 'lines': cur, 'unit': cur_ch_unit}
        if not cur_nav:
            d['nav'] = False
        chapters.append(d)
    cur = None

def new_chapter(title, level, nav=True):
    global cur, cur_title, cur_level, cur_href, cur_nav, in_keywords, cur_ch_unit
    in_keywords = False
    flush()
    cur_ch_unit = cur_unit  # 新章归属当前单元(在 flush 之后设置,不影响刚写出的上一章)
    idx = len(chapters)
    cur_href = 'chap%02d.xhtml' % idx
    cur_title, cur_level, cur = title, level, []
    cur_nav = nav

para_open = False
in_front = True
cur_nav = True
in_daoyin = False
daoyin_of = {}
in_keywords = False
cur_unit = 0
cur_ch_unit = 0
expect_author = False
def close_para():
    global para_open
    if para_open:
        cur.append('</p>')
        para_open = False

cur_href = 'chap00.xhtml'
# 版权页(CIP)信息按用户要求整体略去
skip_cip = False
for raw in body_lines:
    line = raw.rstrip()
    if not line.strip():
        close_para()
        continue
    if line.strip() == '图书在版编目（CIP）数据':
        skip_cip = True
        continue
    if skip_cip:
        if line.strip().startswith('物料号'):
            skip_cip = False
        continue
    m = BIAN.match(line)
    if m:
        in_front = False
        new_chapter(m.group(1), 1)
        cur.append('<h1>%s</h1>' % html.escape(m.group(1)))
        continue
    m = UNIT.match(line)
    if m:
        cur_unit += 1
        new_chapter(m.group(1), 2)
        cur.append('<h1>%s</h1>' % inline(m.group(1)))
        continue
    m = ART.match(line)
    if m:
        close_para()
        if in_daoyin:
            cur.append('</div>')
            in_daoyin = False
        t = re.sub(r'\s+', ' ', m.group(1)).strip()
        if '[^' not in t:  # 无脚注引用的不是正式文章标题 -> 提要样式,不入目录
            cur.append('<h3 class="tiyao">%s</h3>' % inline(t))
        else:
            aid = 's' + re.match(r'(\d+)\s*-\s*(\d+)', t).expand(r'\1-\2')  # 锚点 s<x>-<y>
            new_chapter(re.sub(r'\[\^\d+\]', '', t).strip(), 3)  # 每篇文章独立文件,保证分页
            cur.append('<h2 id="%s">%s</h2>' % (aid, inline(t)))
            expect_author = True  # 下一短行带脚注的为作者行,居中
        continue
    if expect_author and line.strip():
        t2 = line.strip().lstrip('#').strip()
        if t2.startswith('——'):  # 副题(原书居中)
            close_para()
            cur.append('<p class="subtitle">%s</p>' % inline(t2))
            continue
        if '[^' in t2 and len(t2) < 25:  # 选文作者(原书居中)
            close_para()
            cur.append('<p class="author">%s</p>' % inline(t2))
            expect_author = False
            continue
        expect_author = False
    if line.strip().startswith(('（以上', '（此则')) and cur_level == 3:
        close_para()
        cur.append('<p class="right">%s</p>' % inline(line.strip()))  # 选篇出处注,居右
        continue
    if re.match(r'^(19|20)\d{2}\s*年(\s*\d{1,2}\s*月)?(\s*\d{1,2}\s*日)?$', line.strip()) \
            or re.match(r'^(19|20)\d{2}-\d{1,2}-\d{1,2}$', line.strip()):
        if cur_level == 3 and cur_title != '小结':
            close_para()
            cur.append('<p class="right">%s</p>' % inline(line.strip()))  # 文末写作日期,居右
            continue
    m = SEC.match(line)
    if m:
        close_para()
        if in_daoyin and m.group(1) != '问题导引':
            cur.append('</div>')
            in_daoyin = False
        name = m.group(1)
        if name == '小结' and cur_level == 3:
            new_chapter(name, 3)  # 小结与文章并列,独立分页且入目录
            cur.append('<h2>%s</h2>' % html.escape(name))
            continue
        if cur_title == '小结':
            # 小结之后的栏目(关键词语/要点提炼/争议聚焦/拓展阅读指引)是小结的子标题,同页连续
            cur.append('<h4>%s</h4>' % html.escape(name))
            in_keywords = (name == '关键词语')
            continue
        if name == '问题导引':
            cur.append('<h2 class="center" id="daoyin">%s</h2>' % html.escape(name))
            cur.append('<div class="daoyin">')
            in_daoyin = True
            daoyin_of[cur_href] = True
            continue
        cur.append('<h3>%s</h3>' % html.escape(name))
        continue
    m = ANYH.match(line)
    if m:
        close_para()
        t = m.group(2).strip()
        if in_front:  # 前置部分(书名页/作者名录/内容简介/前言等)
            new_chapter(t, 2)
            cur.append('<h1>%s</h1>' % inline(t))
        elif t.startswith('——'):  # 文章副题
            cur.append('<p class="subtitle">%s</p>' % inline(t))
        elif t.rstrip('：:') == '注释':  # 文内注释小标题(居左,无缩进)
            cur.append('<h3>%s</h3>' % html.escape(t.rstrip('：:')))
        elif t in IN_ARTICLE_SUBHEADS:  # 文内小标题(居中)
            cur.append('<h3 class="center">%s</h3>' % inline(t))
        else:  # OCR 误判为标题的正文行
            cur.append('<p>%s</p>' % inline(t))
        continue
    if in_keywords and line.strip():
        close_para()
        toks = line.strip().split()
        cur.append('<p class="keywords">' + ''.join('<span>%s</span>' % html.escape(t) for t in toks) + '</p>')
        continue
    # 引文: ">> " 前缀 -> blockquote 样式段落
    if line.strip().startswith('>>'):
        close_para()
        qt = line.strip().lstrip('>').strip()
        if qt:
            cur.append('<p class="quote">%s</p>' % inline(qt))
        continue
    # 诗行: "> " 前缀的连续行合成一个 verse 段落,行内换行保留为 <br/>
    if line.strip().startswith('>'):
        t = inline(line.strip().lstrip('>').strip())
        if para_open == 'verse':
            cur.append('<br/>' + t)
        else:
            close_para()
            cur.append('<p class="verse">' + t)
            para_open = 'verse'
        continue
    if para_open == 'verse':
        close_para()
    # 普通正文行
    if cur is None:
        new_chapter('语文素养高级读本', 2)
    stripped = line.strip()
    expect_author = False
    if cur_title == '前言' and re.match(r'^(编撰者|\d{4}\s*年\s*\d{1,2}\s*月)$', stripped):
        close_para()
        cur.append('<p class="right">%s</p>' % inline(stripped))  # 落款居右
        continue
    if cur_title == '本书所选文章作者名录':
        # 仿原书: 每行人名一栏均分;两个字的名原书为字间空,先合并单字
        close_para()
        if stripped.startswith('(') or stripped.startswith('（'):
            cur.append('<p class="note">%s</p>' % inline(stripped))
        elif stripped.startswith('谨向'):
            cur.append('<p class="thanks">%s</p>' % inline(stripped))
        else:
            toks = stripped.split()
            names = []
            k = 0
            while k < len(toks):
                if len(toks[k]) == 1 and k + 1 < len(toks):
                    names.append(toks[k] + toks[k + 1])
                    k += 2
                else:
                    names.append(toks[k])
                    k += 1
            cur.append('<p class="namerow">' + ''.join('<span>%s</span>' % html.escape(x) for x in names) + '</p>')
        continue
    if not para_open:
        cur.append('<p>')
        para_open = True
        cur.append(inline(stripped))
    else:
        # 中文排版: 源文件换行不渲染。两侧都是 ASCII 字母数字时补一个空格(断词),否则直接相连
        prev = ''
        for k in range(len(cur) - 1, -1, -1):
            t = re.sub(r'<[^>]+>', '', cur[k])
            if t.strip():
                prev = t.rstrip()[-1]
                break
        cjk = lambda c: '一' <= c <= '鿿'
        alnum = lambda c: c.isascii() and c.isalnum()  # 英文字母或数字
        sep = ' ' if (alnum(prev) and alnum(stripped[:1])) \
              or (cjk(prev) and alnum(stripped[:1])) \
              or (alnum(prev) and cjk(stripped[:1])) else ''
        cur.append(sep + inline(stripped))
close_para()
flush()

# --- 脚注按单元拆分: 每单元的注释附在该单元小结章末尾 ---
unit_notes = {}   # unit -> [fn id ...] 按出现顺序
for ch in chapters:
    u = ch.get('unit', 0)
    if not u:
        continue
    for ln in ch['lines']:
        for m in re.finditer(r'id="fnref-(\d+)"', ln):
            if m.group(1) not in unit_notes.setdefault(u, []):
                unit_notes[u].append(m.group(1))
xj_file = {}      # unit -> 小结章文件名
for idx, ch in enumerate(chapters):
    if ch['title'] == '小结' and ch.get('unit'):
        xj_file[ch['unit']] = 'chap%02d.xhtml' % idx
        notes_sec = ['<section epub:type="endnotes">', '<h3>注释</h3>']
        for n in unit_notes.get(ch['unit'], []):
            back = ref_place.get(n, 'chap00.xhtml')
            notes_sec.append('<aside epub:type="footnote" id="fn-%s"><p><a href="%s#fnref-%s">[%s]</a> %s</p></aside>'
                             % (n, back, n, n, inline(defs[n])))
        notes_sec.append('</section>')
        ch['lines'].extend(notes_sec)
# 正文引用链接改指本单元小结章
for ch in chapters:
    u = ch.get('unit', 0)
    if u and u in xj_file:
        ch['lines'] = [ln.replace('href="notes.xhtml#', 'href="%s#' % xj_file[u]) for ln in ch['lines']]

# 脚注编号按单元重排: 每单元从 1 开始(显示编号与锚点 id 一并替换)
for u, fnids in unit_notes.items():
    for i, fnid in sorted(enumerate(fnids, 1), key=lambda x: -int(x[1])):  # 长 id 先替换防碰撞
        for ch in chapters:
            ch['lines'] = [
                ln.replace('id="fnref-%s"' % fnid, 'id="fnref-%d-%d"' % (u, i))
                  .replace('#fnref-%s"' % fnid, '#fnref-%d-%d"' % (u, i))
                  .replace('id="fn-%s"' % fnid, 'id="fn-%d-%d"' % (u, i))
                  .replace('#fn-%s"' % fnid, '#fn-%d-%d"' % (u, i))
                  .replace('>[%s]</a>' % fnid, '>[%d]</a>' % i)
                for ln in ch['lines']]

# --- 目录层级整理 ---
# 目录从上编开始: 编 > 单元 > 文章 三级;前置章节与单元尾部栏目(nav=False)不入目录
nav_tree = []  # [(title, href, [children])]
cur_bian = None
cur_unit = None
for ch in chapters:
    href = 'chap%02d.xhtml' % chapters.index(ch)
    if not ch.get('nav', True):
        continue
    if ch['level'] == 1:
        cur_bian = (ch['title'], href, [])
        nav_tree.append(cur_bian)
        cur_unit = None
    elif ch['level'] == 2 and cur_bian is not None:
        cur_unit = (ch['title'], href, [])
        cur_bian[2].append(cur_unit)
        if daoyin_of.get(href):
            cur_unit[2].append(('问题导引', href + '#daoyin', []))
    elif ch['level'] == 3 and cur_unit is not None:
        cur_unit[2].append((ch['title'], href, []))

def render_nav(nodes):
    out = ['<ol>']
    for t, h, ch in nodes:
        out.append('<li><a href="%s">%s</a>' % (h, html.escape(t)))
        if ch:
            out.append(render_nav(ch))
        out.append('</li>')
    out.append('</ol>')
    return '\n'.join(out)

# --- 写文件 ---
if os.path.exists(BUILD):
    shutil.rmtree(BUILD)
os.makedirs(BUILD + '/META-INF')
os.makedirs(BUILD + '/OEBPS')

XHTML_HEAD = ('<?xml version="1.0" encoding="utf-8"?>\n'
    '<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-CN">\n'
    '<head><meta charset="utf-8"/><title>%s</title><link rel="stylesheet" type="text/css" href="style.css"/></head>\n<body>\n')

for i, ch in enumerate(chapters):
    body = '\n'.join(ch['lines'])
    open('%s/OEBPS/chap%02d.xhtml' % (BUILD, i), 'w').write(
        XHTML_HEAD % html.escape(ch['title']) + body + '\n</body>\n</html>\n')

# nav.xhtml
nav_doc = (XHTML_HEAD % '目录' + '<nav epub:type="toc"><h1>目录</h1>\n' + render_nav(nav_tree)
           + '\n</nav>\n</body>\n</html>\n')
open(BUILD + '/OEBPS/nav.xhtml', 'w').write(nav_doc)

# toc.ncx(兼容旧阅读器),与 nav 同样的两级嵌套
pn = [0]
def ncx_nodes(nodes):
    out = []
    for t, h, ch in nodes:
        pn[0] += 1
        inner = ncx_nodes(ch) if ch else ''
        out.append('<navPoint id="np%d" playOrder="%d"><navLabel><text>%s</text></navLabel><content src="%s"/>%s</navPoint>'
                   % (pn[0], pn[0], html.escape(t), h, inner))
    return '\n'.join(out)
ncx = ('<?xml version="1.0" encoding="utf-8"?>\n'
       '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
       '<head><meta name="dtb:uid" content="yuwensuyang-2006"/></head>\n'
       '<docTitle><text>语文素养高级读本</text></docTitle>\n<navMap>\n' + ncx_nodes(nav_tree) + '\n</navMap>\n</ncx>\n')
open(BUILD + '/OEBPS/toc.ncx', 'w').write(ncx)

# content.opf
manifest = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
            '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
            '<item id="css" href="style.css" media-type="text/css"/>',
            '<item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>',
            '<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>']
spine = ['<itemref idref="cover"/>']
for i in range(len(chapters)):
    manifest.append('<item id="chap%02d" href="chap%02d.xhtml" media-type="application/xhtml+xml"/>' % (i, i))
    spine.append('<itemref idref="chap%02d"/>' % i)
opf = ('<?xml version="1.0" encoding="utf-8"?>\n'
    '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="zh-CN">\n'
    '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
    '<dc:identifier id="uid">urn:isbn:7040198290</dc:identifier>\n'
    '<dc:title>语文素养高级读本</dc:title>\n'
    '<dc:creator>李瑞山 编撰</dc:creator>\n'
    '<dc:language>zh-CN</dc:language>\n'
    '<dc:publisher>高等教育出版社</dc:publisher>\n'
    '<dc:date>2006-08</dc:date>\n'
    '<meta property="dcterms:modified">2026-10-10T00:00:00Z</meta>\n'
    '<meta name="cover" content="cover-image"/>\n'
    '</metadata>\n<manifest>\n' + '\n'.join(manifest) + '\n</manifest>\n'
    '<spine toc="ncx">\n' + '\n'.join(spine) + '\n</spine>\n'
    '<guide><reference type="cover" title="封面" href="cover.xhtml"/></guide>\n</package>\n')
open(BUILD + '/OEBPS/content.opf', 'w').write(opf)

# 封面页
os.makedirs(BUILD + '/OEBPS/images')
shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cover.jpg'), BUILD + '/OEBPS/images/cover.jpg')
open(BUILD + '/OEBPS/cover.xhtml', 'w').write(
    XHTML_HEAD % '封面' +
    '<section style="text-align:center;margin:0;padding:0;">'
    '<img src="images/cover.jpg" alt="封面" style="max-width:100%;max-height:100%;"/></section>\n</body>\n</html>\n')

open(BUILD + '/META-INF/container.xml', 'w').write(
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
    '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>\n</container>\n')
open(BUILD + '/mimetype', 'w').write('application/epub+zip')
open(BUILD + '/OEBPS/style.css', 'w').write(
    'body{font-family:serif;line-height:1.6;margin:5%;}\n'
    'h1{font-size:1.5em;font-weight:bold;margin:1em 0 1.5em;}\n'
    'h2{font-family:"Heiti SC","SimHei","Microsoft YaHei",sans-serif;font-size:1.25em;font-weight:bold;text-align:center;margin:1.5em 0 0.6em;}\n'
    'h3{font-size:1.1em;font-weight:bold;margin-top:1em;}h3.center{text-align:center;}\n'
    'h4{font-size:1.05em;font-weight:bold;margin-top:0.9em;}\n'
    'h2.center{text-align:center;}\n'
    '.daoyin{background:#f6f6f6;border-left:3px solid #bbb;padding:0.4em 0.9em;margin:0.6em 0;}\n'
    'p{text-indent:2em;margin:0.4em 0;}\n'
    'p.subtitle{text-indent:0;text-align:center;}\n'
    'p.author{font-family:"Kaiti SC","STKaiti","KaiTi",serif;text-align:center;text-indent:0;margin:0.2em 0 1.2em;}\n'
    'p.right{text-align:right;text-indent:0;}\n'
    'p.verse{text-indent:0;margin:0.3em 0 0.3em 2em;line-height:1.5;}\n'
    'p.quote{font-family:"Kaiti SC","STKaiti","KaiTi",serif;margin:0.5em 2em;font-size:0.95em;}\n'
    'p.keywords{text-indent:0;line-height:2;margin:0.5em 0;}\n'
    'p.keywords span{display:inline-block;background:#f2f2f2;border:1px solid #ddd;border-radius:4px;padding:0.05em 0.6em;margin:0.15em 0.35em;}\n'
    'p.note{text-indent:0;font-size:0.9em;}\n'
    'p.namerow{display:flex;justify-content:space-between;text-indent:0;margin:0.25em 0;}\n'
    'p.namerow span{white-space:nowrap;}\n'
    'p.thanks{text-align:center;font-weight:bold;text-indent:0;margin-top:1.5em;}\n'
    'sup{font-size:0.75em;}\naside p{text-indent:0;}\n')

# 打包
if os.path.exists(OUT):
    os.remove(OUT)
with zipfile.ZipFile(OUT, 'w') as z:
    z.write(BUILD + '/mimetype', 'mimetype', zipfile.ZIP_STORED)
    for root, _, files in os.walk(BUILD):
        for f in files:
            if f == 'mimetype':
                continue
            full = os.path.join(root, f)
            z.write(full, os.path.relpath(full, BUILD), zipfile.ZIP_DEFLATED)

# 校验: 所有 xhtml 均可解析
nfiles = 0
for root, _, files in os.walk(BUILD):
    for f in files:
        if f.endswith(('.xhtml', '.opf', '.ncx', '.xml')):
            xmlparse(os.path.join(root, f))
            nfiles += 1
print('chapters:', len(chapters), 'notes:', len(defs), 'xml files ok:', nfiles)
print('epub:', OUT, os.path.getsize(OUT), 'bytes')
