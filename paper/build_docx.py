"""Builds manuscript_v4.1.docx from manuscript_v4.1.md with academic-paper formatting (formatting only; content unchanged)."""
import subprocess, docx, re
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
subprocess.run(["pandoc","manuscript_v4.1.md","-o","manuscript_v4.1.docx","--resource-path=."],check=True)
d=docx.Document("manuscript_v4.1.docx")
sec=d.sections[0]; sec.page_width=Inches(8.5); sec.page_height=Inches(11)
sec.left_margin=sec.right_margin=Inches(1); sec.top_margin=sec.bottom_margin=Inches(1)
avail=sec.page_width-sec.left_margin-sec.right_margin
SERIF="Times New Roman"; BLACK=RGBColor(0,0,0)
def setfont(style,size=None,bold=None,italic=None,name=SERIF):
    f=style.font; f.name=name; f.color.rgb=BLACK
    if size: f.size=Pt(size)
    if bold is not None: f.bold=bold
    if italic is not None: f.italic=italic
    rpr=style.element.get_or_add_rPr(); rf=rpr.find(qn("w:rFonts"))
    if rf is None: rf=OxmlElement("w:rFonts"); rpr.append(rf)
    for a in list(rf.attrib):
        if "Theme" in a: del rf.attrib[a]
    for a in ("ascii","hAnsi","cs","eastAsia"): rf.set(qn("w:"+a),name)
def para(style,before=0,after=6,line=1.15,align=None,keep=False,left=None,first=None):
    pf=style.paragraph_format; pf.space_before=Pt(before); pf.space_after=Pt(after); pf.line_spacing=line
    if align is not None: pf.alignment=align
    if keep: pf.keep_with_next=True
    if left is not None: pf.left_indent=Inches(left)
    if first is not None: pf.first_line_indent=Inches(first)
_S=d.styles
class _W:
    def __getitem__(self,k):
        for st in _S:
            if st.name.lower()==k.lower(): return st
        raise KeyError(k)
S=_W()
for n in ("Normal","Body Text","First Paragraph"):
    setfont(S[n],11); para(S[n],0,6,1.15,WD_ALIGN_PARAGRAPH.JUSTIFY)
setfont(S["Compact"],10); para(S["Compact"],0,2,1.1,WD_ALIGN_PARAGRAPH.LEFT)
setfont(S["Heading 1"],16,True); para(S["Heading 1"],0,10,1.1,WD_ALIGN_PARAGRAPH.CENTER,True)
setfont(S["Heading 2"],13.5,True); para(S["Heading 2"],16,6,1.1,WD_ALIGN_PARAGRAPH.LEFT,True)
setfont(S["Heading 3"],11.5,True); para(S["Heading 3"],12,4,1.1,WD_ALIGN_PARAGRAPH.LEFT,True)
setfont(S["Heading 4"],11,True,True); para(S["Heading 4"],8,3,1.1,WD_ALIGN_PARAGRAPH.LEFT,True)
for n in ("Image Caption","Table Caption","Caption"):
    setfont(S[n],9.5,False,False); para(S[n],4,10,1.1,WD_ALIGN_PARAGRAPH.LEFT)
setfont(S["Bibliography"],10.5); para(S["Bibliography"],0,4,1.1,WD_ALIGN_PARAGRAPH.LEFT)
setfont(S["Block Text"],10.5); 
for n in ("Source Code",):
    setfont(S[n],9,name="Courier New")
try: setfont(S["Verbatim Char"],9.5,name="Courier New")
except KeyError: pass
# ---- front matter: author block centred on separate lines, date centred
body=d.paragraphs
for i,p in enumerate(body[:8]):
    t=p.text.strip()
    if t.startswith("Quoc Thinh Vo"):
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(4)
        for r in p.runs: r.font.size=Pt(11)
    elif t.startswith("Working Paper"):
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(14)
        for r in p.runs: r.font.size=Pt(10.5)
# author name bold only (first run) already bold by markdown
# ---- headings: keep black, abstract/keywords styling, rules
in_refs=False
for p in d.paragraphs:
    sn=p.style.name; t=p.text.strip()
    if sn.startswith("Heading"):
        in_refs = (t=="References")
        for r in p.runs: r.font.color.rgb=BLACK; r.font.name=SERIF
        if t in ("Abstract",): p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(6)
        if t.startswith("Appendix"): in_refs=False
        continue
    if re.match(r"^(Table \d|Figure \d)",t) or re.match(r"^(Table|Figure) [A-Z0-9.]+\.",t):
        if t.startswith("Table"): p.paragraph_format.keep_with_next=True; p.alignment=WD_ALIGN_PARAGRAPH.LEFT; p.paragraph_format.space_before=Pt(8); p.paragraph_format.space_after=Pt(3)
    if in_refs and t:
        p.paragraph_format.left_indent=Inches(0.35); p.paragraph_format.first_line_indent=Inches(-0.35)
        p.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.LEFT; p.paragraph_format.space_after=Pt(4)
        for r in p.runs: r.font.size=Pt(10.5)
    for r in p.runs:
        if r.font.color is not None and r.font.color.rgb not in (None,BLACK) and r.font.name is None: pass
# figure paragraphs centred, keep with caption
for p in d.paragraphs:
    if p._p.xpath(".//w:drawing"):
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next=True; p.paragraph_format.space_before=Pt(8); p.paragraph_format.space_after=Pt(3)
# ---- tables: three-rule academic style, bold header, repeat header row
def set_cell_border(cell,**kw):
    tcPr=cell._tc.get_or_add_tcPr(); b=tcPr.find(qn("w:tcBorders"))
    if b is None: b=OxmlElement("w:tcBorders"); tcPr.append(b)
    for edge,(sz,val) in kw.items():
        e=OxmlElement(f"w:{edge}"); e.set(qn("w:val"),val); e.set(qn("w:sz"),str(sz)); e.set(qn("w:color"),"000000"); b.append(e)
for t in d.tables:
    ncol=len(t.columns); t.autofit=False
    tblPr=t._tbl.tblPr
    for old in tblPr.findall(qn("w:tblBorders")): tblPr.remove(old)
    big=ncol>=8
    size=Pt(7.5) if big else (Pt(9) if ncol>=5 else Pt(9.5))
    tot=avail/914400
    if big: w=[1.95,0.45]+[(tot-2.4)/(ncol-2)]*(ncol-2)
    elif ncol==4: w=[0.9,1.2,2.4,2.2]; w=[x*tot/sum(w) for x in w]
    else: w=[tot/ncol]*ncol
    rows=t.rows
    trPr=rows[0]._tr.get_or_add_trPr(); h=OxmlElement("w:tblHeader"); h.set(qn("w:val"),"true"); trPr.append(h)
    for ri,r in enumerate(rows):
        cs=OxmlElement("w:cantSplit"); r._tr.get_or_add_trPr().append(cs)
        for ci,c in enumerate(r.cells):
            c.width=Inches(w[ci])
            if ri==0: set_cell_border(c,top=(10,"single"),bottom=(6,"single"))
            if ri==len(rows)-1: set_cell_border(c,bottom=(10,"single"))
            for p in c.paragraphs:
                p.paragraph_format.space_after=Pt(1.5); p.paragraph_format.space_before=Pt(1.5); p.paragraph_format.line_spacing=1.05
                ref=rows[1].cells[ci].text.strip() if len(rows)>1 else ""
                numcol=bool(re.match(r"^[-+−0-9.,±†\s()%$–]+$",ref or "x"))
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER if (ci>0 and numcol) else WD_ALIGN_PARAGRAPH.LEFT
                for run in p.runs:
                    run.font.size=size; run.font.name=SERIF
                    if ri==0: run.font.bold=True
# keep small tables on one page; add space after every table
from docx.text.paragraph import Paragraph
for t in d.tables:
    rows=t.rows
    if len(rows)<=18:
        for r in rows[:-1]:
            for c in r.cells:
                for p in c.paragraphs: p.paragraph_format.keep_with_next=True
    nxt=t._tbl.getnext()
    if nxt is not None and nxt.tag==qn("w:p"):
        Paragraph(nxt,t._parent).paragraph_format.space_before=Pt(10)
for s in d.inline_shapes:
    if s.width>avail: r=avail/s.width; s.width=int(s.width*r); s.height=int(s.height*r)
# ---- page number footer
f=sec.footer; fp=f.paragraphs[0]; fp.alignment=WD_ALIGN_PARAGRAPH.CENTER
def fld(par,instr):
    r=par.add_run(); r.font.size=Pt(9); r.font.name=SERIF
    for typ,txt in (("begin",None),(None,instr),("end",None)):
        if typ: e=OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"),typ); r._r.append(e)
        else: e=OxmlElement("w:instrText"); e.set(qn("xml:space"),"preserve"); e.text=txt; r._r.append(e)
fld(fp,"PAGE")
d.save("manuscript_v4.1.docx")
