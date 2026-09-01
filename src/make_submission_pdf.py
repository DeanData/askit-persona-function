#!/usr/bin/env python3
"""Build the submission PDF: repo link, REPORT.md, the visual, the
CLAUDE_CODE_WAS_WRONG.md paragraph, a METRIC.md link, Part 3 status, and the
required audience/persona descriptions.
"""
import json
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, HRFlowable, ListFlowable, ListItem,
)

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "AskIt_Submission.pdf"
REPO_URL = "https://github.com/DeanData/askit-persona-function"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, spaceAfter=10, spaceBefore=4))
styles.add(ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceAfter=8, spaceBefore=12,
                           textColor=colors.HexColor("#2b4c7e")))
styles.add(ParagraphStyle("Body", parent=styles["BodyText"], fontSize=9.5, leading=13.5, spaceAfter=8))
styles.add(ParagraphStyle("Small", parent=styles["BodyText"], fontSize=8.5, leading=12, textColor=colors.gray))
styles.add(ParagraphStyle("LinkLine", parent=styles["BodyText"], fontSize=10, leading=14, spaceAfter=6))


def md_inline_to_reportlab(text):
    """Very small subset: **bold**, `code`, *italic*."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r'<font face="Courier">\1</font>', text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
    return text


def render_markdown_body(md_text, story, skip_first_h1=False):
    """Minimal markdown -> reportlab flowables: #/## headers, blank-line-separated
    paragraphs, everything else treated as body text."""
    lines = md_text.strip("\n").split("\n")
    para_buf = []
    first_h1_seen = False

    def flush():
        if para_buf:
            joined = " ".join(para_buf).strip()
            if joined:
                story.append(Paragraph(md_inline_to_reportlab(joined), styles["Body"]))
            para_buf.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith("# "):
            flush()
            if skip_first_h1 and not first_h1_seen:
                first_h1_seen = True
                continue
            story.append(Paragraph(md_inline_to_reportlab(stripped[2:]), styles["H1"]))
        elif stripped.startswith("## "):
            flush()
            story.append(Paragraph(md_inline_to_reportlab(stripped[3:]), styles["H2"]))
        elif stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**"):
            flush()
            story.append(Paragraph(md_inline_to_reportlab(stripped), styles["Small"]))
        else:
            para_buf.append(stripped)
    flush()


def main():
    story = []

    # --- Title / header ---
    story.append(Paragraph("AskIt Research Lab — Home Assignment Submission", styles["H1"]))
    story.append(Paragraph(
        f'Repository (code, data, full logs, commit history): '
        f'<link href="{REPO_URL}" color="blue">{REPO_URL}</link>',
        styles["LinkLine"]))
    story.append(Paragraph(
        f'Metric, committed before any text was generated: '
        f'<link href="{REPO_URL}/blob/main/METRIC.md" color="blue">{REPO_URL}/blob/main/METRIC.md</link>',
        styles["LinkLine"]))
    story.append(Paragraph(
        "<b>Part 3 (slow research) status:</b> not yet completed at the time of this "
        "submission. See REPORT.md's Part 3 section below for the current status; if "
        "completed later in the 5-hour budget, the repository's REPORT.md will reflect "
        "the finished version even if this PDF was generated earlier.",
        styles["Body"]))
    story.append(HRFlowable(width="100%", color=colors.lightgrey, spaceBefore=6, spaceAfter=12))

    # --- REPORT.md ---
    report_md = (ROOT / "REPORT.md").read_text()
    render_markdown_body(report_md, story, skip_first_h1=True)

    # --- Visual ---
    story.append(Paragraph("Required visual", styles["H2"]))
    img_path = ROOT / "artifacts" / "baseline_vs_fewshot.png"
    story.append(Image(str(img_path), width=6.8 * inch, height=6.8 * inch * (5.5 / 13)))
    story.append(Spacer(1, 12))

    # --- Claude Code was wrong ---
    story.append(HRFlowable(width="100%", color=colors.lightgrey, spaceBefore=6, spaceAfter=12))
    wrong_md = (ROOT / "CLAUDE_CODE_WAS_WRONG.md").read_text()
    render_markdown_body(wrong_md, story)

    # --- Audience descriptions (required deliverable) ---
    story.append(HRFlowable(width="100%", color=colors.lightgrey, spaceBefore=6, spaceAfter=12))
    story.append(Paragraph("Audience descriptions", styles["H1"]))
    story.append(Paragraph(
        "Population-level descriptions fed to f() as one of its two inputs. "
        f'Full file: <link href="{REPO_URL}/blob/main/data/audiences.json" color="blue">'
        f'data/audiences.json</link>.', styles["Body"]))
    audiences = json.loads((ROOT / "data" / "audiences.json").read_text())
    for name, aud in audiences.items():
        story.append(Paragraph(f"{name} <font size=8 color='gray'>({aud['role']})</font>", styles["H2"]))
        story.append(Paragraph(md_inline_to_reportlab(aud["description"]), styles["Body"]))

    # --- Persona descriptions (required deliverable) ---
    story.append(HRFlowable(width="100%", color=colors.lightgrey, spaceBefore=6, spaceAfter=12))
    story.append(Paragraph("Persona descriptions (sample)", styles["H1"]))
    story.append(Paragraph(
        "One individual drawn from an audience, the other of f()'s two inputs. Structured "
        "schema (age, age-conditioned occupation, region, family status, one open-ended "
        "detail) rendered through a fixed template — full design rationale in WORKLOG.md. "
        "40 personas per audience, 200 total, fixed seed, shared roster across every "
        f'condition. Full roster: <link href="{REPO_URL}/tree/main/data/personas" '
        f'color="blue">data/personas/</link>. Two samples below, one per risk-orientation:',
        styles["Body"]))
    samples = [
        ("personalfinance",
         "57, engaged, lives in Seattle, Washington, works as a nurse practitioner. "
         "Recently adopted a rescue dog."),
        ("wallstreetbets",
         "31, divorced, shares custody of one child, lives in a small town in rural "
         "Minnesota, works as a physical therapist. Started taking pottery classes recently."),
    ]
    items = [ListItem(Paragraph(f"<b>{a}</b>: {t}", styles["Body"])) for a, t in samples]
    story.append(ListFlowable(items, bulletType="bullet"))

    doc = SimpleDocTemplate(str(OUT_PATH), pagesize=LETTER,
                             topMargin=0.7 * inch, bottomMargin=0.7 * inch,
                             leftMargin=0.75 * inch, rightMargin=0.75 * inch)
    doc.build(story)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
