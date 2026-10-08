# -*- coding: utf-8 -*-
"""Printable defence handout: one page per slide, plus a metric reference.
Reads the built deck so nothing can drift. Print-first: A4, ink-economical."""
import sys, os, html
from pptx import Presentation
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck_notes import METRICS, ANNOT, FOOTNOTES

DECK = sys.argv[1] if len(sys.argv) > 1 else "outputs/Defence_CLV_MPMD.pptx"
OUT  = sys.argv[2] if len(sys.argv) > 2 else "/tmp/handout.html"
E = html.escape

prs = Presentation(DECK)
slides = []
for i, s in enumerate(prs.slides, 1):
    texts, tables = [], []
    for sh in s.shapes:
        if sh.has_table:
            tables.append([[c.text for c in r.cells] for r in sh.table.rows])
        elif sh.has_text_frame and sh.text_frame.text.strip() and not sh.is_placeholder:
            for p in sh.text_frame.paragraphs:
                t = "".join(r.text for r in p.runs).strip()
                if t: texts.append(t)
    notes = s.notes_slide.notes_text_frame.text.strip() if s.has_notes_slide else ""
    slides.append({"n": i, "texts": texts, "tables": tables, "notes": notes,
                   "divider": s.slide_layout.name != "Folie pur" or not texts})

CSS = """
@page { size: A4; margin: 16mm 15mm 14mm 15mm; }
*{box-sizing:border-box}
html{-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{margin:0;font-family:ui-serif,Georgia,"Palatino Linotype",Palatino,"Times New Roman",serif;
 font-size:10.5pt;line-height:1.45;color:#15161A;background:#fff}
.mono{font-family:ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace}
.sheet{page-break-after:always;break-after:page;padding:0 0 6mm}
.sheet:last-child{page-break-after:auto;break-after:auto}
.cover{text-align:left;padding-top:28mm}
.cover h1{font-size:30pt;line-height:1.08;margin:0 0 6mm;letter-spacing:-.4pt}
.cover .sub{font-size:12pt;color:#44464E;margin:0 0 14mm}
.cover .meta{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:9pt;color:#5C5F68;line-height:1.9}
.rule{height:3pt;background:#76B900;width:38mm;margin:0 0 7mm}
.toc{margin-top:12mm;column-count:2;column-gap:10mm;font-size:9.5pt}
.toc div{break-inside:avoid;margin-bottom:1.1mm;color:#2C2E35}
.toc b{font-family:ui-monospace,Menlo,monospace;color:#76B900;margin-right:2.5mm}
h2.sec{font-size:17pt;margin:0 0 4mm;letter-spacing:-.2pt}
.head{display:flex;justify-content:space-between;align-items:baseline;
 border-bottom:1.2pt solid #15161A;padding-bottom:2mm;margin-bottom:4mm}
.head .n{font-family:ui-monospace,Menlo,monospace;font-size:9pt;color:#76B900;font-weight:700}
.head .kick{font-family:ui-monospace,Menlo,monospace;font-size:7.5pt;letter-spacing:.9pt;
 text-transform:uppercase;color:#6B6E77}
h3.title{font-size:15pt;margin:0 0 3mm;letter-spacing:-.2pt;line-height:1.2}
.claim{font-size:10.5pt;color:#33353D;margin:0 0 5mm;font-style:italic;
 border-left:2.5pt solid #D5D7D2;padding-left:4mm}
.blk{margin-bottom:5mm;break-inside:avoid}
.blk h4{font-family:ui-monospace,Menlo,monospace;font-size:7.5pt;letter-spacing:.9pt;
 text-transform:uppercase;color:#6B6E77;margin:0 0 1.8mm;font-weight:600}
.blk ul{margin:0;padding-left:5mm}
.blk li{margin-bottom:1.2mm;font-size:9.8pt}
.blk p{margin:0 0 2mm;font-size:10pt}
.deliver{background:#F4F5F1;border-left:2.5pt solid #76B900;padding:3mm 4mm;font-size:10pt}
.line{margin-top:2.5mm;padding-top:2mm;border-top:.5pt solid #DDDEDA;break-inside:avoid}
.line .w{font-family:ui-monospace,Menlo,monospace;font-size:8pt;color:#3D4E8C;margin:0 0 .8mm}
.line p{margin:0;font-size:9.8pt}
.ask{background:#FBF6EC;border-left:2.5pt solid #9A5B12;padding:3mm 4mm;font-size:9.6pt;margin-top:4mm}
.ask b{font-family:ui-monospace,Menlo,monospace;font-size:7.5pt;letter-spacing:.9pt;
 text-transform:uppercase;color:#9A5B12;display:block;margin-bottom:1.2mm}
.notes{font-size:9.3pt;color:#2C2E35;white-space:pre-wrap;background:#FAFAF8;
 border:.5pt solid #E2E3DF;padding:3mm 4mm}
table.t{width:100%;border-collapse:collapse;font-size:8.8pt;margin-top:2mm}
table.t td{border-bottom:.5pt solid #DDDEDA;padding:1.3mm 2mm;vertical-align:top}
table.t tr:first-child td{font-family:ui-monospace,Menlo,monospace;font-size:7.6pt;
 color:#76B900;font-weight:700;border-bottom:1pt solid #15161A}
.metric{break-inside:avoid;margin-bottom:6mm;border-bottom:.5pt solid #DDDEDA;padding-bottom:4mm}
.metric h4{font-size:11.5pt;margin:0 0 1mm}
.metric .where{font-family:ui-monospace,Menlo,monospace;font-size:7.5pt;color:#6B6E77;margin:0 0 2mm}
.metric dl{display:grid;grid-template-columns:26mm 1fr;gap:.8mm 3mm;margin:0 0 2.5mm}
.metric dt{font-family:ui-monospace,Menlo,monospace;font-size:7.4pt;letter-spacing:.5pt;
 text-transform:uppercase;color:#6B6E77;padding-top:.6mm}
.metric dd{margin:0;font-size:9.6pt}
.say{background:#FBF6EC;border-left:2.5pt solid #9A5B12;padding:2.5mm 3.5mm;font-size:9.8pt;margin-bottom:2mm}
.press{background:#F2F4F9;border-left:2.5pt solid #3D4E8C;padding:2.5mm 3.5mm;font-size:9.4pt}
.press i{color:#33353D}
"""

o = ['<title>Defence Handout</title>', '<style>%s</style>' % CSS]

# ── cover ──
o.append('<div class="sheet cover"><div class="rule"></div>'
 '<h1>Defence handout</h1>'
 '<p class="sub">Customer Lifetime Value Prediction Using Bayesian Methods</p>'
 '<p class="meta">Devansh Sharma &middot; M.Sc. thesis defence<br>'
 'First Supervisor: Professor Dr. Tilo Wendler<br>'
 'Second Supervisor: Dr. Guido M&ouml;ser<br><br>'
 'One page per slide: what is shown, how to deliver it, the full speaker note,<br>'
 'and the definitions to have ready. A metric reference follows at the end.</p>')
o.append('<div class="toc">')
for sl in slides:
    t = next((x for x in sl["texts"] if x.upper() != x and len(x) > 4), "")
    if t: o.append('<div><b>%02d</b>%s</div>' % (sl["n"], E(t[:52])))
o.append('</div></div>')

# ── one sheet per slide ──
for sl in slides:
    n = sl["n"]; txts = sl["texts"]
    kick = next((x for x in txts if x.upper() == x and 2 < len(x) < 42), "")
    title = next((x for x in txts if x.upper() != x and len(x) > 4), "Slide %d" % n)
    rest = [x for x in txts if x not in (kick, title)]
    claim = rest[0] if rest and len(rest[0]) > 60 else ""
    body = [x for x in rest if x != claim]
    deliver, lines = ANNOT.get(n, ("", []))
    o.append('<div class="sheet"><div class="head"><span class="n">SLIDE %02d / %d</span>'
             '<span class="kick">%s</span></div>' % (n, len(slides), E(kick)))
    o.append('<h3 class="title">%s</h3>' % E(title))
    if claim: o.append('<p class="claim">%s</p>' % E(claim))
    if body:
        o.append('<div class="blk"><h4>On the slide</h4><ul>')
        for b in body[:12]: o.append('<li>%s</li>' % E(b))
        o.append('</ul></div>')
    for tb in sl["tables"]:
        o.append('<div class="blk"><h4>Table</h4><table class="t">')
        for r in tb: o.append('<tr>' + "".join('<td>%s</td>' % E(c) for c in r) + '</tr>')
        o.append('</table></div>')
    if deliver or lines:
        o.append('<div class="blk"><h4>Delivery</h4>')
        if deliver: o.append('<div class="deliver">%s</div>' % E(deliver))
        for w, h in lines:
            o.append('<div class="line"><p class="w">%s</p><p>%s</p></div>' % (E(w), E(h)))
        o.append('</div>')
    note = sl["notes"]; fn = FOOTNOTES.get(n, "")
    if fn and fn in note: note = note.replace(fn, "").strip()
    if note:
        o.append('<div class="blk"><h4>Speaker note</h4><div class="notes">%s</div></div>' % E(note))
    if fn:
        o.append('<div class="ask"><b>Definitions to have ready</b>%s</div>'
                 % E(fn.replace("IF ASKED — ", "")))
    o.append('</div>')

# ── metric reference ──
o.append('<div class="sheet"><h2 class="sec">Metric reference</h2>'
 '<p style="font-size:10pt;color:#44464E;margin:0 0 6mm">Every metric appearing in the deck: what it '
 'measures, the value in these results, the line to deliver, and the question most likely to follow.</p>')
for i, (slug, name, where, what, how, val, bad, say, press) in enumerate(METRICS):
    if i and i % 4 == 0: o.append('</div><div class="sheet">')
    q, a = press
    o.append('<div class="metric"><h4>%s</h4><p class="where">%s</p><dl>'
             '<dt>Measures</dt><dd>%s</dd><dt>Computed</dt><dd>%s</dd>'
             '<dt>Your value</dt><dd>%s</dd><dt>Poor would be</dt><dd>%s</dd></dl>'
             '<div class="say">%s</div>'
             '<div class="press"><i>&ldquo;%s&rdquo;</i><br>%s</div></div>'
             % (E(name), E(where), E(what), E(how), E(val), E(bad), E(say), E(q), E(a)))
o.append('</div>')

open(OUT, "w", encoding="utf-8").write("\n".join(o))
print("wrote %s — %d sheets, %d metrics" % (OUT, len(slides) + 1, len(METRICS)))
