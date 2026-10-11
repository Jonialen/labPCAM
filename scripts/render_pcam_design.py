"""Render the editable PCAM design and annotated pseudocode for submission."""

from html import escape
from pathlib import Path
from shutil import copy2

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "diseno_pcam_previo.md"
PDF = ROOT / "diseno_pcam_previo.pdf"
FONTS = Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("DesignArial", str(FONTS / "arial.ttf")))
pdfmetrics.registerFont(TTFont("DesignArialBold", str(FONTS / "arialbd.ttf")))
pdfmetrics.registerFont(TTFont("DesignConsolas", str(FONTS / "consola.ttf")))

title_style = ParagraphStyle(
    "DesignTitle", fontName="DesignArialBold", fontSize=17, leading=22,
    textColor=colors.HexColor("#173c55"), spaceAfter=11,
)
heading_style = ParagraphStyle(
    "DesignHeading", fontName="DesignArialBold", fontSize=11.2, leading=15,
    textColor=colors.HexColor("#17618a"), spaceBefore=7, spaceAfter=4,
    keepWithNext=True,
)
body_style = ParagraphStyle(
    "DesignBody", fontName="DesignArial", fontSize=9, leading=12.7,
    spaceAfter=6,
)
bullet_style = ParagraphStyle(
    "DesignBullet", parent=body_style, leftIndent=13, firstLineIndent=-11,
    spaceAfter=4,
)
code_style = ParagraphStyle(
    "DesignCode", fontName="DesignConsolas", fontSize=7.45, leading=10,
)


def add_paragraph(story: list, lines: list[str]) -> None:
    if lines:
        story.append(Paragraph(escape(" ".join(lines)).replace("`", ""), body_style))
        lines.clear()


story: list = []
paragraph: list[str] = []
code: list[str] | None = None
for raw in SOURCE.read_text(encoding="utf-8").splitlines():
    line = raw.rstrip()
    if code is not None:
        if line == "```":
            block = Preformatted("\n".join(code), code_style)
            table = Table([[block]], colWidths=[17.2 * cm])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef4f7")),
                ("BOX", (0, 0), (-1, -1), .35, colors.HexColor("#d3e0e7")),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.extend([table, Spacer(1, .22 * cm)])
            code = None
        else:
            code.append(line)
        continue
    if not line:
        add_paragraph(story, paragraph)
    elif line == "<!-- pagebreak -->":
        add_paragraph(story, paragraph)
        story.append(PageBreak())
    elif line.startswith("# "):
        add_paragraph(story, paragraph)
        story.append(Paragraph(escape(line[2:]), title_style))
    elif line.startswith("## "):
        add_paragraph(story, paragraph)
        story.append(Paragraph(escape(line[3:]), heading_style))
    elif line.startswith("Repositorio: "):
        add_paragraph(story, paragraph)
        url = line.removeprefix("Repositorio: ")
        story.append(Paragraph(
            f'Repositorio: <link href="{escape(url, quote=True)}" color="#17618a">'
            f'{escape(url)}</link>', body_style,
        ))
    elif line == "```text":
        add_paragraph(story, paragraph)
        code = []
    elif line.startswith("- "):
        add_paragraph(story, paragraph)
        story.append(Paragraph("• " + escape(line[2:]).replace("`", ""), bullet_style))
    else:
        paragraph.append(line)
add_paragraph(story, paragraph)
if code is not None:
    raise SystemExit("Unclosed pseudocode block")

document = SimpleDocTemplate(
    str(PDF), pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
    topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    title="Diseño PCAM previo al código: N-Body 2D",
    author="David Domínguez, Jonathan Diaz, Luis Padilla",
)
document.build(story)
copy2(PDF, ROOT / "entrega_canvas" / PDF.name)
print(f"Generated {PDF.name} and the Canvas copy")
