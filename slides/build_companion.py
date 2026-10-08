# -*- coding: utf-8 -*-
"""Render the defence companion to HTML (artifact body: no html/head/body)."""
import sys, os, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from defence_qa import SLIDES

KIND = {
 "clarify":  ("Clarify",   "k-clarify",  "They want it explained simply"),
 "method":   ("Method",    "k-method",   "How exactly did you do it"),
 "challenge":("Challenge", "k-challenge","Pushback on a choice"),
 "hostile":  ("Hardest",   "k-hostile",  "The one you least want"),
 "extend":   ("Extend",    "k-extend",   "Where would you take it"),
}
E = html.escape

CSS = """
:root{
 --ground:#F2F1ED;--ground-2:#EAE8E2;--card:#FBFAF7;--ink:#2E4057;--ink-strong:#1E2B3B;
 --muted:#6B7685;--faint:#9AA2AE;--rule:#D9D6CE;--accent:#E76F51;--accent-soft:#F6E2DB;
 --verify:#1D7A5F;--verify-soft:#DCEBE4;--hot:#A8323A;--hot-soft:#F3DEDF;
 --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
 --serif:ui-serif,Georgia,"Palatino Linotype",Palatino,"Times New Roman",serif;
 --mono:ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
 --measure:72ch;--s1:.4rem;--s2:.75rem;--s3:1.1rem;--s4:1.75rem;--s5:2.75rem;--s6:4.25rem;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
 color-scheme:dark;
 --ground:#14181F;--ground-2:#1A1F28;--card:#1B212B;--ink:#DFE4EA;--ink-strong:#F2F5F8;
 --muted:#9AA5B4;--faint:#6B7686;--rule:#2C343F;--accent:#F0866A;--accent-soft:#3A2520;
 --verify:#4FB38C;--verify-soft:#17312A;--hot:#E4868C;--hot-soft:#3A2022;}}
:root[data-theme="dark"]{
 color-scheme:dark;
 --ground:#14181F;--ground-2:#1A1F28;--card:#1B212B;--ink:#DFE4EA;--ink-strong:#F2F5F8;
 --muted:#9AA5B4;--faint:#6B7686;--rule:#2C343F;--accent:#F0866A;--accent-soft:#3A2520;
 --verify:#4FB38C;--verify-soft:#17312A;--hot:#E4868C;--hot-soft:#3A2022;}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--serif);
 font-size:17px;line-height:1.65;-webkit-font-smoothing:antialiased}
.wrap{max-width:1000px;margin:0 auto;padding:0 var(--s4)}
.mast{padding:var(--s6) 0 var(--s4)}
.eyebrow{font-family:var(--mono);font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;
 color:var(--accent);margin:0 0 var(--s3)}
h1{font-family:var(--sans);font-weight:760;letter-spacing:-.028em;font-size:clamp(2rem,5vw,3.1rem);
 line-height:1.05;margin:0 0 var(--s3);color:var(--ink-strong);text-wrap:balance}
.standfirst{font-size:1.1rem;color:var(--muted);margin:0;max-width:60ch}
.tally{display:flex;gap:var(--s4);flex-wrap:wrap;margin:var(--s4) 0 0;padding-top:var(--s3);
 border-top:1px solid var(--rule)}
.tally div{font-family:var(--mono);font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--faint)}
.tally b{display:block;font-family:var(--sans);font-size:1.9rem;color:var(--ink-strong);letter-spacing:-.02em}
.bar{position:sticky;top:env(safe-area-inset-top,0px);z-index:20;background:var(--ground);
 border-bottom:1px solid var(--rule);margin-top:var(--s5)}
.bar .row{display:flex;gap:var(--s2);align-items:center;flex-wrap:wrap;padding:var(--s2) 0}
.bar button{font-family:var(--mono);font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;
 background:var(--ground-2);color:var(--muted);border:1px solid var(--rule);padding:.45rem .7rem;cursor:pointer}
.bar button[aria-pressed="true"]{background:var(--ink);color:var(--ground);border-color:var(--ink)}
.bar button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.bar .lbl{font-family:var(--mono);font-size:.66rem;letter-spacing:.12em;text-transform:uppercase;color:var(--faint);margin-right:.2rem}
.slide{background:var(--card);border:1px solid var(--rule);padding:var(--s4);margin:var(--s3) 0}
.slide-head{display:flex;gap:var(--s3);align-items:baseline;flex-wrap:wrap}
.num{font-family:var(--mono);font-size:1.5rem;color:var(--accent);font-weight:600;line-height:1}
.kick{font-family:var(--mono);font-size:.64rem;letter-spacing:.14em;text-transform:uppercase;color:var(--faint)}
.slide h2{font-family:var(--sans);font-weight:700;letter-spacing:-.02em;font-size:1.3rem;
 margin:.2rem 0 0;color:var(--ink-strong);flex:1 1 100%;text-wrap:balance}
.says{margin:var(--s2) 0 0;color:var(--muted);font-size:.98rem;max-width:var(--measure)}
.concepts{margin:var(--s3) 0 0;padding:var(--s3);background:var(--ground-2);border-left:2px solid var(--verify)}
.concepts h3{font-family:var(--mono);font-size:.64rem;letter-spacing:.12em;text-transform:uppercase;
 color:var(--verify);margin:0 0 var(--s2);font-weight:500}
.concepts dl{margin:0}
.concepts dt{font-family:var(--sans);font-weight:650;color:var(--ink-strong);font-size:.96rem;margin-top:.55rem}
.concepts dt:first-child{margin-top:0}
.concepts dd{margin:.1rem 0 0;font-size:.94rem;color:var(--ink);max-width:var(--measure)}
.qs{margin:var(--s3) 0 0}
.qs h3{font-family:var(--mono);font-size:.64rem;letter-spacing:.12em;text-transform:uppercase;
 color:var(--accent);margin:0 0 var(--s2);font-weight:500}
details.q{border-top:1px solid var(--rule);padding:var(--s2) 0}
details.q[hidden]{display:none}
summary{cursor:pointer;list-style:none;display:flex;gap:var(--s2);align-items:flex-start}
summary::-webkit-details-marker{display:none}
summary:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
.tag{flex:0 0 auto;font-family:var(--mono);font-size:.58rem;letter-spacing:.1em;text-transform:uppercase;
 padding:.22rem .45rem;margin-top:.22rem;border-radius:2px;white-space:nowrap}
.k-clarify{background:var(--verify-soft);color:var(--verify)}
.k-method{background:var(--ground-2);color:var(--ink-strong)}
.k-challenge{background:var(--accent-soft);color:var(--accent)}
.k-hostile{background:var(--hot-soft);color:var(--hot)}
.k-extend{background:var(--ground-2);color:var(--muted)}
.qtext{font-family:var(--sans);font-weight:620;color:var(--ink-strong);font-size:1rem;line-height:1.45}
summary .qtext::after{content:" \\2193";color:var(--faint);font-weight:400}
details[open] summary .qtext::after{content:" \\2191"}
.ans{margin:var(--s2) 0 var(--s1) calc(.58rem + 1.4rem);font-size:.98rem;max-width:var(--measure)}
.ans p{margin:0}
footer{margin-top:var(--s6);padding:var(--s4) 0 var(--s6);border-top:1px solid var(--rule);
 color:var(--faint);font-size:.9rem}
footer p{margin:0 0 var(--s2);max-width:var(--measure)}
@media (max-width:640px){body{font-size:16px}.slide{padding:var(--s3)}
 .ans{margin-left:0}.tally{gap:var(--s3)}}
"""

def render():
    nq = sum(len(s["qs"]) for s in SLIDES)
    nh = sum(1 for s in SLIDES for k,_,_ in s["qs"] if k == "hostile")
    out = ['<title>Defence Companion</title>', '<style>%s</style>' % CSS, '<div class="wrap">',
     '<header class="mast">',
     '<p class="eyebrow">Thesis defence &middot; slide-by-slide preparation</p>',
     '<h1>Every slide, every concept, every question</h1>',
     '<p class="standfirst">For each slide of the defence deck: what it claims, the concepts an examiner '
     'may probe, and the questions that can be asked from it &mdash; with an answer you can actually say out loud. '
     'Answers are hidden by default, so you can test yourself before revealing.</p>',
     '<div class="tally"><div><b>%d</b>slides</div><div><b>%d</b>questions</div>'
     '<div><b>%d</b>concepts</div><div><b>%d</b>hardest</div></div>' %
       (len(SLIDES), nq, sum(len(s["concepts"]) for s in SLIDES), nh),
     '</header></div>',
     '<div class="bar"><div class="wrap"><div class="row">',
     '<span class="lbl">Answers</span>',
     '<button type="button" id="all" aria-pressed="false">Reveal all</button>',
     '<span class="lbl" style="margin-left:.6rem">Filter</span>',
     '<button type="button" class="f" data-k="" aria-pressed="true">All</button>']
    for k,(lab,_,_) in KIND.items():
        out.append('<button type="button" class="f" data-k="%s" aria-pressed="false">%s</button>' % (k, lab))
    out.append('</div></div></div><div class="wrap">')

    for s in SLIDES:
        out.append('<article class="slide">')
        out.append('<div class="slide-head"><span class="num">%02d</span>'
                   '<span class="kick">%s</span><h2>%s</h2></div>' % (s["n"], E(s["kicker"]), E(s["title"])))
        out.append('<p class="says">%s</p>' % E(s["says"]))
        if s["concepts"]:
            out.append('<div class="concepts"><h3>Concepts on this slide</h3><dl>')
            for t, d in s["concepts"]:
                out.append('<dt>%s</dt><dd>%s</dd>' % (E(t), E(d)))
            out.append('</dl></div>')
        out.append('<div class="qs"><h3>Questions you could be asked</h3>')
        for kind, q, a in s["qs"]:
            lab, cls, _ = KIND[kind]
            out.append('<details class="q" data-k="%s"><summary><span class="tag %s">%s</span>'
                       '<span class="qtext">%s</span></summary><div class="ans"><p>%s</p></div></details>'
                       % (kind, cls, lab, E(q), E(a)))
        out.append('</div></article>')

    out.append('<footer><p>Answers are written to be spoken, not read &mdash; roughly 20 to 40 seconds each. '
               'Where a question attacks a real weakness, the answer concedes it first and then bounds it. '
               'That is almost always stronger than defending ground you do not hold.</p>'
               '<p>Generated from <code>outputs/Defence_CLV_Bayesian.pptx</code>.</p></footer></div>')
    out.append("""<script>
(function(){
 var all=document.getElementById('all'), ds=[].slice.call(document.querySelectorAll('details.q'));
 all.addEventListener('click',function(){
   var on=all.getAttribute('aria-pressed')!=='true';
   all.setAttribute('aria-pressed',on?'true':'false');
   all.textContent=on?'Hide all':'Reveal all';
   ds.forEach(function(d){ if(!d.hidden) d.open=on; });
 });
 [].forEach.call(document.querySelectorAll('.f'),function(b){
   b.addEventListener('click',function(){
     var k=b.getAttribute('data-k');
     [].forEach.call(document.querySelectorAll('.f'),function(o){
       o.setAttribute('aria-pressed', o===b?'true':'false'); });
     ds.forEach(function(d){ d.hidden = !!k && d.getAttribute('data-k')!==k; });
     [].forEach.call(document.querySelectorAll('.slide'),function(sl){
       var vis=sl.querySelectorAll('details.q:not([hidden])').length;
       sl.hidden = !!k && vis===0;
     });
   });
 });
})();
</script>""")
    return "\n".join(out)

if __name__ == "__main__":
    body = render()
    open("/tmp/claude-1000/-mnt-c-Users-devan-bayesCLV/01ab1f48-ef3b-4cb7-9ffc-552c36f08dd3/scratchpad/defence-companion.html","w",encoding="utf-8").write(body)
    print("rendered %d bytes" % len(body))
