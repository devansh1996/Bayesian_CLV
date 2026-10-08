"""Build the thesis defence deck (16:9, 25 min)."""
from pptx import Presentation
from pptx.util import Inches as In, Pt, Emu
from pptx.dml.color import RGBColor as C
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image
import os

NAVY, ORANGE, TEAL = C(0x2E,0x40,0x57), C(0xE7,0x6F,0x51), C(0x1D,0x7A,0x5F)
INK, MUTE, LINE, SOFT = C(0x22,0x22,0x22), C(0x5A,0x5A,0x5A), C(0xD8,0xD8,0xD8), C(0xF1,0xEF,0xE8)
WHITE = C(0xFF,0xFF,0xFF)
FONT = "Calibri"
W, H = In(13.333), In(7.5)
OUT = "outputs/Defence_CLV_Story.pptx"
FIG, SLD = "outputs/figures/", "outputs/slides/"

prs = Presentation(); prs.slide_width, prs.slide_height = W, H
BLANK = prs.slide_layouts[6]
_n = {"i": 0}

def tb(slide, l, t, w, h, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(l, t, w, h); tf = box.text_frame
    tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.paragraphs[0].alignment = align
    return tf

def put(tf, text, size=18, bold=False, color=INK, space_after=8, first=False,
        align=None, italic=False, bullet=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    if align: p.alignment = align
    p.space_after = Pt(space_after)
    r = p.add_run(); r.text = ("•  " if bullet else "") + text
    r.font.size, r.font.bold, r.font.italic = Pt(size), bold, italic
    r.font.color.rgb, r.font.name = color, FONT
    return p

def rect(slide, l, t, w, h, fill, line=None):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = fill
    if line: s.line.color.rgb = line; s.line.width = Pt(1)
    else: s.line.fill.background()
    s.shadow.inherit = False
    return s

def slide(title, kicker=None, notes=None, number=True):
    s = prs.slides.add_slide(BLANK)
    _n["i"] += 1
    if kicker:
        t = tb(s, In(0.85), In(0.42), In(11.6), In(0.3))
        put(t, kicker.upper(), 12.5, True, ORANGE, 2, first=True)
    t = tb(s, In(0.85), In(0.70) if kicker else In(0.60), In(11.6), In(0.8))
    put(t, title, 30, True, NAVY, 0, first=True)
    rect(s, In(0.85), In(1.52), In(1.5), Pt(3.2), ORANGE)
    if number:
        f = tb(s, In(11.9), In(6.92), In(0.6), In(0.3), align=PP_ALIGN.RIGHT)
        put(f, str(_n["i"]), 11, False, C(0x9A,0x9A,0x9A), 0, first=True)
        g = tb(s, In(0.85), In(6.92), In(8.0), In(0.3))
        put(g, "Bayesian CLV in non-contractual e-commerce", 10, False, C(0xAA,0xAA,0xAA), 0, first=True)
    if notes: s.notes_slide.notes_text_frame.text = notes
    return s

def section(title, sub, notes=None):
    s = prs.slides.add_slide(BLANK); _n["i"] += 1
    rect(s, 0, 0, W, H, NAVY)
    t = tb(s, In(1.4), In(3.0), In(10.5), In(1.6))
    put(t, title, 40, True, WHITE, 6, first=True)
    put(t, sub, 18, False, C(0xBF,0xC9,0xD4), 0)
    rect(s, In(1.4), In(2.6), In(1.6), Pt(3.5), ORANGE)
    if notes: s.notes_slide.notes_text_frame.text = notes
    return s

def picture(s, path, top, max_w=In(11.0), max_h=In(4.1), left=None):
    iw, ih = Image.open(path).size
    w, h = max_w, Emu(int(max_w * ih / iw))
    if h > max_h: h = max_h; w = Emu(int(max_h * iw / ih))
    l = left if left is not None else Emu(int((W - w)/2))
    return s.shapes.add_picture(path, l, top, width=w, height=h)

def takeaway(s, text, top=In(6.05)):
    rect(s, In(0.85), top, In(11.6), In(0.62), SOFT)
    rect(s, In(0.85), top, Pt(4), In(0.62), ORANGE)
    t = tb(s, In(1.08), top + In(0.10), In(11.2), In(0.45), anchor=MSO_ANCHOR.MIDDLE)
    put(t, text, 15, True, NAVY, 0, first=True)

def bullets(s, items, top=In(1.95), left=In(0.95), width=In(11.4), size=18, gap=11):
    avail = max(In(0.5), H - top - In(0.15))      # never declare a box past the slide edge
    tf = tb(s, left, top, width, min(In(4.0), avail))
    for i, it in enumerate(items):
        if isinstance(it, tuple):
            head, sub = it
            put(tf, head, size, True, NAVY, 2, first=(i == 0))
            put(tf, sub, size-3, False, MUTE, gap+2)
        else:
            put(tf, it, size, False, INK, gap, first=(i == 0), bullet=True)
    return tf

