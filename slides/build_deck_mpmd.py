"""Defence deck rendered into the institutional template (texts/devansh_slides.pptx).

Everything is built on the template's own layouts, so the MPMD/HTW logo, the
theme fonts and the date/footer/slide-number placeholders come through natively
rather than being pasted in. Content is the undergraduate-level deck; only the
geometry (10 x 5.625in instead of 13.333 x 7.5in) and palette change.
"""
import os, re, copy, sys
from pptx import Presentation
from pptx.util import Inches as _In, Pt as _Pt, Emu
from pptx.dml.color import RGBColor as C
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, PP_PLACEHOLDER
from PIL import Image

TEMPLATE = "texts/devansh_slides.pptx"
OUT      = "outputs/Defence_CLV_v3_v4.pptx"
FIG, SLD = "outputs/figures/", "outputs/slides/"

# The content below is authored on the original 13.333 x 7.5in grid. Map it into
# the template's 10 x 5.625in frame. X maps exactly (so full-bleed panels still
# reach both edges); Y is compressed a little harder because this template's
# footer band sits at 5.21in and the content must finish above it.
GRID_W, GRID_H = _In(13.333), _In(7.5)
SX   = 0.75                     # 10 / 13.333 — exact, so full-bleed panels still fit
# The layout's logo occupies the top-left down to y = 0.61in, and the footer band
# starts at 5.21in. So the content block has to live between them: map the grid's
# content range (0.42 .. 7.42) onto 0.70 .. 5.15in.
LOGO_BOTTOM, FOOTER_TOP = _In(0.70), _In(5.21)
Y0   = _In(0.42)
SY   = (_In(5.15) - LOGO_BOTTOM) / (_In(7.42) - Y0)
FSC  = 0.66                     # font scale to match the tighter vertical

def In(x):  return _In(x)       # grid units; transformed at draw time
def Pt(x):  return _Pt(x)

def TX(v): return int(round(v * SX))
def TY(v): return int(round(LOGO_BOTTOM + (v - Y0) * SY))   # a position
def TH(v): return int(round(v * SY))                        # a height

# palette taken from the template itself
BRAND  = C(0x76, 0xB9, 0x00)         # the green used 26x across the master
AMBER  = C(0xFB, 0xAE, 0x40)
NAVY   = C(0x33, 0x3F, 0x4C)
ORANGE = BRAND                       # content calls the accent ORANGE
TEAL   = C(0x66, 0x70, 0x7A)         # muted grey for the footnote chips
INK, MUTE, LINE, SOFT = C(0x22,0x22,0x22), C(0x5A,0x5A,0x5A), C(0xD8,0xD8,0xD8), C(0xF2,0xF4,0xEE)
WHITE  = C(0xFF,0xFF,0xFF)
FONT   = "Calibri"
HEAD   = "Calibri Light"

prs = Presentation(TEMPLATE)
W, H = prs.slide_width, prs.slide_height

# drop the template's three example slides, keep every layout and the master
_ids = prs.slides._sldIdLst
for sid in list(_ids):
    rId = sid.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
    prs.part.drop_rel(rId)
    _ids.remove(sid)

L = {l.name: l for l in prs.slide_layouts}
BLANK  = L["Folie pur"]              # carries the logo + footer placeholders
TITLE  = L["Titelfolie"]
CLOSE  = L.get("Abschluss ohne Bild", BLANK)
FOOTER_TEXT = "Devansh Sharma  ·  Customer Lifetime Value Prediction"
_n = {"i": 0}

def _fill_placeholders(s):
    """Use the template's own date / footer / number placeholders."""
    for ph in list(s.placeholders):
        t = ph.placeholder_format.type
        if t == PP_PLACEHOLDER.DATE:
            ph.text_frame.text = "Thesis defence"
        elif t == PP_PLACEHOLDER.FOOTER:
            ph.text_frame.text = FOOTER_TEXT
        elif t == PP_PLACEHOLDER.SLIDE_NUMBER:
            pass                      # PowerPoint fills this itself
        else:
            ph._element.getparent().remove(ph._element)   # unused body placeholders
    for ph in s.placeholders:
        for p in ph.text_frame.paragraphs:
            for r in p.runs:
                r.font.size, r.font.name, r.font.color.rgb = _Pt(8), FONT, C(0x9A,0x9A,0x9A)

def tb(slide, l, t, w, h, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(TX(l), TY(t), TX(w), TH(h)); tf = box.text_frame
    tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.paragraphs[0].alignment = align
    return tf

def put(tf, text, size=18, bold=False, color=INK, space_after=8, first=False,
        align=None, italic=False, bullet=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    if align: p.alignment = align
    p.space_after = Pt(space_after)
    r = p.add_run(); r.text = ("•  " if bullet else "") + text
    r.font.size, r.font.bold, r.font.italic = _Pt(size * FSC), bold, italic
    r.font.color.rgb, r.font.name = color, FONT
    return p

def rect(slide, l, t, w, h, fill, line=None):
    if l <= 0 and t <= 0 and ((w >= GRID_W*0.95 and h >= GRID_H*0.95) or (w >= W*0.95 and h >= H*0.95)):
        l, t, w, h = 0, 0, W, H                      # full-bleed panel: use the real slide
    else:
        l, t, w, h = TX(l), TY(t), TX(w), TH(h)
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = fill
    if line: s.line.color.rgb = line; s.line.width = Pt(1)
    else: s.line.fill.background()
    s.shadow.inherit = False
    return s

def table(s, headers, rows, top, left=In(0.85), width=In(11.6), row_h=In(0.40), size=12):
    """A plain academic table: brand rule under the header, hairline rows, no grid."""
    from pptx.util import Pt as _P
    nr, nc = len(rows) + 1, len(headers)
    shp = s.shapes.add_table(nr, nc, TX(left), TY(top), TX(width), TH(row_h) * nr)
    tbl = shp.table
    tbl.first_row = False; tbl.horz_banding = False
    for j, h in enumerate(headers):
        c = tbl.cell(0, j); c.text = h
        p = c.text_frame.paragraphs[0]
        for r in p.runs:
            r.font.size, r.font.bold, r.font.name, r.font.color.rgb = _P(size*FSC), True, FONT, BRAND
        c.fill.background(); c.margin_left = c.margin_right = TX(In(0.10))
        c.margin_top = c.margin_bottom = TH(In(0.04))
    for i, row in enumerate(rows, start=1):
        for j, v in enumerate(row):
            c = tbl.cell(i, j); c.text = str(v)
            p = c.text_frame.paragraphs[0]
            for r in p.runs:
                r.font.size, r.font.name = _P(size*FSC), FONT
                r.font.color.rgb = NAVY if j == 0 else INK
                r.font.bold = (j == 0)
            c.fill.background(); c.margin_left = c.margin_right = TX(In(0.10))
            c.margin_top = c.margin_bottom = TH(In(0.04))
    for i in range(nr):
        tbl.rows[i].height = TH(row_h)
    return tbl

def slide(title, kicker=None, notes=None, number=True):
    s = prs.slides.add_slide(BLANK); _n["i"] += 1
    _fill_placeholders(s)
    if kicker:
        t = tb(s, In(0.85), In(0.42), In(11.6), In(0.3))
        put(t, kicker.upper(), 12.5, True, BRAND, 2, first=True)
    t = tb(s, In(0.85), In(0.70) if kicker else In(0.60), In(11.6), In(0.8))
    p = put(t, title, 28, True, NAVY, 0, first=True)
    for r in p.runs: r.font.name = HEAD
    rect(s, In(0.85), In(1.52), In(1.5), Pt(3.2), BRAND)
    if notes: s.notes_slide.notes_text_frame.text = notes
    return s

def section(title, sub, notes=None):
    s = prs.slides.add_slide(BLANK); _n["i"] += 1
    _fill_placeholders(s)
    rect(s, 0, 0, W, H, NAVY)
    t = tb(s, In(1.4), In(3.0), In(10.5), In(1.6))
    p = put(t, title, 36, True, WHITE, 6, first=True)
    for r in p.runs: r.font.name = HEAD
    put(t, sub, 17, False, C(0xC8,0xD2,0xBC), 0)
    rect(s, In(1.4), In(2.6), In(1.6), Pt(3.5), BRAND)
    if notes: s.notes_slide.notes_text_frame.text = notes
    return s

def picture(s, path, top, max_w=In(11.0), max_h=In(4.1), left=None):
    mw, mh = TX(max_w), TH(max_h)
    iw, ih = Image.open(path).size
    w, h = mw, Emu(int(mw * ih / iw))
    if h > mh: h = mh; w = Emu(int(mh * iw / ih))
    l = TX(left) if left is not None else Emu(int((W - w) / 2))
    return s.shapes.add_picture(path, l, TY(top), width=w, height=h)

def takeaway(s, text, top=In(6.05)):
    rect(s, In(0.85), top, In(11.6), In(0.62), SOFT)
    rect(s, In(0.85), top, Pt(4), In(0.62), BRAND)
    t = tb(s, In(1.08), top + In(0.10), In(11.2), In(0.45), anchor=MSO_ANCHOR.MIDDLE)
    put(t, text, 15, True, NAVY, 0, first=True)

def bullets(s, items, top=In(1.95), left=In(0.95), width=In(11.4), size=18, gap=11):
    avail = max(In(0.5), H - top - In(0.15))
    tf = tb(s, left, top, width, min(In(4.0), avail))
    for i, it in enumerate(items):
        if isinstance(it, tuple):
            head, sub = it
            put(tf, head, size, True, NAVY, 2, first=(i == 0))
            put(tf, sub, size-3, False, MUTE, gap+2)
        else:
            put(tf, it, size, False, INK, gap, first=(i == 0), bullet=True)
    return tf

def chip(s, proper, top=In(6.78)):
    if TY(top) + TH(In(0.34)) > FOOTER_TOP - _In(0.04):
        top = Y0 + int(((FOOTER_TOP - _In(0.04) - TH(In(0.34))) - LOGO_BOTTOM) / SY)
    t = tb(s, In(0.85), top, In(11.6), In(0.34))
    p = t.paragraphs[0]; p.space_after = Pt(0)
    r = p.add_run(); r.text = "The proper name for this:  "
    r.font.size, r.font.color.rgb, r.font.name = Pt(11), C(0x9A,0x9A,0x9A), FONT
    r2 = p.add_run(); r2.text = proper
    r2.font.size, r2.font.bold, r2.font.color.rgb, r2.font.name = Pt(11), True, TEAL, FONT

def question(s, q, top=In(1.80)):          # retained for compatibility
    claim(s, q, top)

def claim(s, text, top=In(1.78)):
    """One declarative sentence stating what the slide establishes."""
    t = tb(s, In(0.85), top, In(11.6), In(0.62))
    put(t, text, 16, False, MUTE, 0, first=True)

def stat_row(s, items, top=In(2.1), h=In(1.35)):
    n = len(items); gap = In(0.25)
    w = Emu(int((In(11.6) - gap*(n-1)) / n))
    for i,(k,v,c) in enumerate(items):
        l = In(0.85) + Emu(int(i*(w+gap)))
        rect(s, l, top, w, h, SOFT); rect(s, l, top, w, Pt(3.5), c)
        t = tb(s, l+In(0.18), top+In(0.22), w-In(0.36), h-In(0.3))
        put(t, k, 25, True, c, 2, first=True)
        for ln in v.split("\n"): put(t, ln, 12, False, MUTE, 0)

def box(s, lines, top, h=In(1.0), accent=BRAND):
    rect(s, In(0.85), top, In(11.6), h, SOFT)
    rect(s, In(0.85), top, Pt(4), h, accent)
    t = tb(s, In(1.10), top+In(0.13), In(11.1), h-In(0.2))
    for i,(txt,sz,bold,col) in enumerate(lines):
        put(t, txt, sz, bold, col, 4, first=(i==0))

# ── title slide, on the template's own Titelfolie ──
s = prs.slides.add_slide(TITLE); _n["i"] += 1
for ph in list(s.placeholders):
    ph._element.getparent().remove(ph._element)
t = tb(s, In(0.85), In(1.35), In(11.4), In(2.0))
p = put(t, "How much is a customer worth,", 32, True, NAVY, 3, first=True)
for r in p.runs: r.font.name = HEAD
p = put(t, "when you can't tell who has left?", 32, True, NAVY, 12)
for r in p.runs: r.font.name = HEAD
put(t, "Customer Lifetime Value Prediction Using Bayesian Methods", 15, False, MUTE, 0, italic=True)
rect(s, In(0.85), In(3.70), In(2.0), Pt(3), BRAND)
t = tb(s, In(0.85), In(3.95), In(11.0), In(1.5))
put(t, "Devansh Sharma", 17, True, INK, 6, first=True)
put(t, "Master's Thesis  ·  M.Sc.", 13, False, MUTE, 4)
put(t, "First Supervisor: Professor Dr. Tilo Wendler    ·    Second Supervisor: Dr. Guido Möser",
    12, False, MUTE, 0)
s.notes_slide.notes_text_frame.text = (
 "~40 s. Good morning. I'll keep the vocabulary plain and put the technical names in small print at "
 "the bottom of each slide, so the argument is followable whether or not you work in this area.")

# ── body: reuse the undergraduate deck's content verbatim ──
body = open("slides/deck_body_v3.py", encoding="utf-8").read()
exec(compile(body, "deck_body_v3.py", "exec"))

# ── closing slide ──
s = prs.slides.add_slide(BLANK); _n["i"] += 1
_fill_placeholders(s)
rect(s, 0, 0, W, H, NAVY)
t = tb(s, In(1.4), In(2.6), In(10.5), In(2.0))
p = put(t, "Thank you", 40, True, WHITE, 8, first=True)
for r in p.runs: r.font.name = HEAD
put(t, "I welcome your questions.", 18, False, C(0xC8,0xD2,0xBC), 14)
put(t, "Devansh Sharma   ·   Customer Lifetime Value Prediction Using Bayesian Methods",
    13, False, C(0x9A,0xA8,0x90), 0)
rect(s, In(1.4), In(2.2), In(1.6), Pt(3.5), BRAND)

# append the short definitional prompts to the speaker notes
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
FOOTNOTES = {}
_added = 0
for _i, _s in enumerate(prs.slides, 1):
    _fn = FOOTNOTES.get(_i)
    if not _fn: continue
    _tf = _s.notes_slide.notes_text_frame
    if "IF ASKED" in _tf.text: continue
    _tf.text = (_tf.text.rstrip() + "\n\n" + _fn) if _tf.text.strip() else _fn
    _added += 1
print("definitional footnotes added to %d slides" % _added)

dest = None
for cand in [OUT] + [OUT.replace(".pptx", "_v%d.pptx" % k) for k in range(2, 12)]:
    try:
        prs.save(cand); dest = cand; break
    except PermissionError:
        continue                       # that file is open in PowerPoint
if dest is None:
    raise SystemExit("every candidate filename is locked — close PowerPoint and re-run")
if dest != OUT:
    print("NOTE: %s is open in PowerPoint — wrote %s instead" % (OUT, dest))
print("saved %s · %d slides · %.0f x %.2f in" %
      (dest, len(prs.slides._sldIdLst), W/914400, H/914400))
