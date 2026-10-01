"""Converte o .md da entrega em .docx no mesmo padrão visual dos documentos do projeto."""
import re, sys, os, copy
import docx
from docx.shared import Pt, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

TEMPLATE, SRC, DST, FOOTER = sys.argv[1:5]
BASE = os.path.dirname(SRC)

doc = docx.Document(TEMPLATE)
body = doc.element.body
for el in list(body):
    if el.tag != qn("w:sectPr"):
        body.remove(el)
sec = doc.sections[0]
TEXT_W = sec.page_width - sec.left_margin - sec.right_margin
TW_DXA = int(TEXT_W / 635)  # EMU -> twips


def el(tag, **attrs):
    e = OxmlElement(tag)
    for k, v in attrs.items():
        e.set(qn(k), str(v))
    return e


def add_runs(p, text, size=None, color=None, bold=False):
    tokens = re.split(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)", text)
    for t in tokens:
        if not t:
            continue
        b, i, code = bold, False, False
        if t.startswith("**") and t.endswith("**"):
            t, b = t[2:-2], True
        elif t.startswith("`") and t.endswith("`"):
            t, code = t[1:-1], True
        elif t.startswith("*") and t.endswith("*") and len(t) > 2:
            t, i = t[1:-1], True
        r = p.add_run(t)
        r.bold = b or None
        r.italic = i or None
        if code:
            r.font.name = "Consolas"
            r._r.get_or_add_rPr().append(el("w:shd", **{"w:val": "clear", "w:color": "auto", "w:fill": "F2F4F7"}))
        if size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = docx.shared.RGBColor.from_string(color)


def spacing(p, before=None, after=None):
    pf = p.paragraph_format
    if before is not None:
        pf.space_before = Pt(before)
    if after is not None:
        pf.space_after = Pt(after)


def p_border(p, side, color, sz, space):
    pPr = p._p.get_or_add_pPr()
    bdr = pPr.find(qn("w:pBdr"))
    if bdr is None:
        bdr = el("w:pBdr")
        pPr.append(bdr)
    bdr.append(el(f"w:{side}", **{"w:val": "single", "w:color": color, "w:sz": sz, "w:space": space}))


def p_shade(p, fill):
    p._p.get_or_add_pPr().append(el("w:shd", **{"w:val": "clear", "w:color": "auto", "w:fill": fill}))


def cell_fmt(cell, fill=None, w=None, head=False):
    tcPr = cell._tc.get_or_add_tcPr()
    if w:
        tcPr.append(el("w:tcW", **{"w:type": "dxa", "w:w": w}))
    b = el("w:tcBorders")
    for s in ("top", "left", "bottom", "right"):
        b.append(el(f"w:{s}", **{"w:val": "single", "w:color": "BFC7D5", "w:sz": 4}))
    tcPr.append(b)
    if fill:
        tcPr.append(el("w:shd", **{"w:val": "clear", "w:color": "auto", "w:fill": fill}))
    m = el("w:tcMar")
    v = 60 if head else 50
    for s, val in (("top", v), ("left", 90), ("bottom", v), ("right", 90)):
        m.append(el(f"w:{s}", **{"w:type": "dxa", "w:w": val}))
    tcPr.append(m)


def add_table(rows, aligns):
    ncol = len(rows[0])
    lens = [max(len(re.sub(r"[*`]", "", r[c])) for r in rows) for c in range(ncol)]
    words = [max(len(w) for r in rows for w in re.sub(r"[*`]", "", r[c]).split() or [""]) for c in range(ncol)]
    lens = [min(max(l, 6), 60) for l in lens]
    total = sum(lens)
    lens = [max(l, (w + 3) * total / 72) for l, w in zip(lens, words)]
    widths = [int(TW_DXA * l / sum(lens)) for l in lens]
    t = doc.add_table(rows=len(rows), cols=ncol)
    tblPr = t._tbl.tblPr
    tblPr.append(el("w:tblW", **{"w:type": "dxa", "w:w": TW_DXA}))
    tblPr.append(el("w:tblLayout", **{"w:type": "fixed"}))
    grid = t._tbl.tblGrid
    for gc, w in zip(grid.findall(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(w))
    for ri, row in enumerate(rows):
        tr = t.rows[ri]._tr
        trPr = tr.get_or_add_trPr()
        trPr.append(el("w:tblHeader") if ri == 0 else el("w:cantSplit"))
        for ci, txt in enumerate(row):
            c = t.cell(ri, ci)
            head = ri == 0
            cell_fmt(c, "1F3864" if head else ("F5F7FB" if ri % 2 == 0 else None), widths[ci], head)
            p = c.paragraphs[0]
            spacing(p, 1, 1)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if aligns[ci] == "c" else WD_ALIGN_PARAGRAPH.LEFT
            add_runs(p, txt, size=9.5, color="FFFFFF" if head else None, bold=head)
    sp = doc.add_paragraph()
    spacing(sp, 0, 3)


def add_image(path):
    from PIL import Image
    w, h = Image.open(path).size
    width = int(TEXT_W)
    max_h = Emu(int(TEXT_W * 1.05))
    if width * h / w > max_h:
        width = int(max_h * w / h)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = False
    spacing(p, 4, 8)
    p.add_run().add_picture(path, width=width)


STY = {st.style_id: st for st in doc.styles if st.type == 1}
lines = open(SRC, encoding="utf8").read().splitlines()
i = 0
first_title = True
meta_buf = []


def flush_meta():
    global meta_buf
    if meta_buf:
        p = doc.add_paragraph()
        spacing(p, 0, 6)
        for k, m in enumerate(meta_buf):
            if k:
                p.add_run().add_break()
            add_runs(p, m)
        meta_buf = []


while i < len(lines):
    ln = lines[i]
    s = ln.strip()
    if s.startswith("**") and ":**" in s and not s.startswith("**Gravidade") and i < 12:
        meta_buf.append(s)
        i += 1
        continue
    flush_meta()
    if not s:
        i += 1
        continue
    if s.startswith("# "):
        p = doc.add_paragraph(style=STY["Title"])
        p_border(p, "bottom", "1F3864", 12, 4)
        spacing(p, 0, 6)
        add_runs(p, s[2:], size=18, color="1F3864", bold=True)
    elif s.startswith("## "):
        p = doc.add_paragraph(style=STY["Heading1"])
        p.paragraph_format.keep_with_next = True
        add_runs(p, s[3:])
    elif s.startswith("### "):
        p = doc.add_paragraph(style=STY["Heading2"])
        p.paragraph_format.keep_with_next = True
        add_runs(p, s[4:])
    elif s == "---":
        p = doc.add_paragraph()
        p_border(p, "bottom", "BFC7D5", 4, 1)
        spacing(p, 3, 6)
    elif s.startswith(">"):
        txt = []
        while i < len(lines) and lines[i].strip().startswith(">"):
            txt.append(lines[i].strip().lstrip(">").strip())
            i += 1
        p = doc.add_paragraph()
        p_border(p, "left", "4472C4", 24, 8)
        p_shade(p, "EEF3FB")
        spacing(p, 4, 8)
        add_runs(p, " ".join(txt))
        continue
    elif s.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
            i += 1
        sep = rows.pop(1)
        aligns = ["c" if c.startswith(":") and c.endswith(":") else "l" for c in sep]
        add_table(rows, aligns)
        continue
    elif s.startswith("```"):
        i += 1
        code = []
        while not lines[i].strip().startswith("```"):
            code.append(lines[i])
            i += 1
        p = doc.add_paragraph()
        p_shade(p, "F2F4F7")
        p_border(p, "left", "BFC7D5", 12, 6)
        spacing(p, 4, 8)
        for k, c in enumerate(code):
            if k:
                p.add_run().add_break()
            r = p.add_run(c)
            r.font.name = "Consolas"
            r.font.size = Pt(8.5)
    elif s.startswith("!["):
        path = re.search(r"\(([^)]+)\)", s).group(1)
        add_image(os.path.join(BASE, path))
    elif s.startswith("- "):
        p = doc.add_paragraph(style=STY["ListParagraph"])
        numPr = el("w:numPr")
        numPr.append(el("w:ilvl", **{"w:val": 0}))
        numPr.append(el("w:numId", **{"w:val": 2}))
        p._p.get_or_add_pPr().append(numPr)
        spacing(p, 0, 3)
        add_runs(p, s[2:])
    else:
        p = doc.add_paragraph()
        spacing(p, 0, 6)
        add_runs(p, s)
    i += 1

for f in sec.footer.paragraphs:
    for r in f.runs:
        if "Desafio" in r.text:
            r.text = r.text.replace("Desafio", FOOTER)
doc.save(DST)
print("ok")
