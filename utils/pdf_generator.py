import re
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import os

def generate_pdf_from_html(html_content: str, output_path: str):
    """
    Generates a PDF from HTML content using WeasyPrint.
    """
    font_config = FontConfiguration()
    
    # Basic CSS for a beautiful report
    css = CSS(string="""
        @page {
            size: A4;
            margin: 2.5cm;
            @top-right {
                content: "Kripaa - Automated Exam Generator";
                font-family: 'Helvetica', sans-serif;
                font-size: 9pt;
                color: #888;
            }
            @bottom-center {
                content: counter(page);
                font-family: 'Helvetica', sans-serif;
                font-size: 10pt;
            }
        }
        body {
            font-family: 'Inter', 'Segoe UI', 'Helvetica', sans-serif;
            line-height: 1.7;
            color: #232323;
            font-size: 12pt;
            background: #fff;
            margin: 0;
        }
        h1 {
            font-family: 'Inter', 'Helvetica', sans-serif;
            color: #1a237e;
            border-bottom: 2px solid #e3e6f0;
            padding-bottom: 8px;
            margin-top: 0;
            margin-bottom: 22px;
            font-size: 2.1em;
            font-weight: 700;
            page-break-after: avoid;
        }
        h2 {
            font-family: 'Inter', 'Helvetica', sans-serif;
            color: #283593;
            margin-top: 30px;
            margin-bottom: 16px;
            border-bottom: 1px solid #e3e6f0;
            padding-bottom: 5px;
            font-size: 1.3em;
            font-weight: 600;
            page-break-after: avoid;
        }
        h3 {
            font-family: 'Inter', 'Helvetica', sans-serif;
            color: #424242;
            margin-top: 18px;
            margin-bottom: 10px;
            font-size: 1.1em;
            font-weight: 500;
            page-break-after: avoid;
        }
        p {
            margin-bottom: 14px;
            text-align: left;
            orphans: 3;
            widows: 3;
            font-size: 1em;
        }
        /* Question paper formatting */
        .question-set-intro { margin-bottom: 8px; font-size: 1.05em; color: #333; }
        .question {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 10px 16px;
            margin: 10px 0 16px 0;
            border-left: 4px solid #1976d2;
            background: #f8fafc;
            border-radius: 5px;
            box-shadow: none;
            page-break-inside: avoid;
        }
        .q-number {
            font-weight: 600;
            font-size: 1.1em;
            color: #1976d2;
            min-width: 48px;
        }
        .q-text { line-height: 1.7; font-size: 1em; color: #232323; }
        .multi-part { margin-top: 6px; }
        .sub-parts { margin-top: 6px; padding-left: 18px; }
        .question table { margin-top: 10px; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 18px 0;
            font-size: 0.98em;
            page-break-inside: avoid;
        }
        th, td {
            border: 1px solid #e3e6f0;
            padding: 8px 10px;
            text-align: left;
        }
        th {
            background-color: #f3f6fa;
            font-weight: 600;
            color: #1a237e;
        }
        tr:nth-child(even) {
            background-color: #f7fafd;
        }
        blockquote {
            background: #f3f6fa;
            border-left: 4px solid #1976d2;
            margin: 1.2em 10px;
            padding: 0.7em 15px;
            font-style: italic;
            color: #444;
            page-break-inside: avoid;
        }
        code {
            font-family: 'JetBrains Mono', 'Courier New', monospace;
            background-color: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
            border: 1px solid #e3e6f0;
        }
        ul, ol {
            margin: 12px 0;
            padding-left: 26px;
        }
        li {
            margin-bottom: 6px;
        }
        hr {
            border: none;
            border-top: 1.5px solid #e3e6f0;
            margin: 24px 0;
        }
        .cover-page {
            text-align: center;
            padding-top: 28%;
            page-break-after: always;
        }
        .cover-title {
            font-size: 2.8em;
            font-weight: 700;
            margin-bottom: 18px;
            color: #1a237e;
            letter-spacing: 1.5px;
        }
        .cover-subtitle {
            font-size: 1.3em;
            color: #283593;
            margin-bottom: 38px;
        }
        .section-header {
            background: #1976d2;
            color: #fff;
            padding: 12px;
            margin: 24px 0 16px 0;
            border-radius: 4px;
            font-size: 1.1em;
            font-weight: 600;
            page-break-after: avoid;
        }
        .stat-box {
            background: #f3f6fa;
            border-left: 4px solid #1976d2;
            padding: 12px;
            margin: 16px 0;
            page-break-inside: avoid;
        }
        .data-table-title { margin-top: 32px; font-size: 1.08em; font-weight:600; color:#1a237e; }
        .toc { page-break-after: always; }
        .toc ul { list-style: none; padding-left:0; }
        .toc li { margin:5px 0; }
        .section-label {
            display: inline-block;
            background: #1976d2;
            color: #fff;
            padding: 5px 12px;
            border-radius: 999px;
            font-size: 0.95em;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 7px;
        }
    """)
    
    HTML(string=html_content).write_pdf(output_path, stylesheets=[css], font_config=font_config)
    print(f"PDF generated successfully at: {output_path}")

def _transform_questions(html_body: str) -> str:
    """Detect question patterns in converted HTML and wrap them in styled blocks.

    This is intentionally robust against the Markdown renderer merging
    multiple **Qn.** lines into a single paragraph. We split such
    paragraphs back into individual question blocks.
    """

    def paragraph_repl(match: re.Match) -> str:
        # Inner HTML of the paragraph that contains one or more strong Qn.
        inner = match.group('inner')

        # Split on occurrences of <strong>Qn.</strong>
        parts = re.split(r"(<strong>Q(?P<qnum>\d+)\.</strong>)", inner)
        blocks = []
        current_qnum = None
        current_text_chunks = []

        for part in parts:
            if not part:
                continue

            m = re.match(r"<strong>Q(?P<qnum>\d+)\.</strong>", part)
            if m:
                # Flush previous question if exists
                if current_qnum is not None:
                    text_html = "".join(current_text_chunks).strip()
                    if text_html:
                        blocks.append(
                            f"<div class='question'><div class='q-number'>Q{current_qnum}.</div>"
                            f"<div class='q-text'>{text_html}</div></div>"
                        )
                current_qnum = m.group('qnum')
                current_text_chunks = []
            else:
                current_text_chunks.append(part)

        # Flush the last question
        if current_qnum is not None:
            text_html = "".join(current_text_chunks).strip()
            if text_html:
                blocks.append(
                    f"<div class='question'><div class='q-number'>Q{current_qnum}.</div>"
                    f"<div class='q-text'>{text_html}</div></div>"
                )

        # If for some reason we couldn't split, fall back to original paragraph
        if not blocks:
            return match.group(0)

        return "".join(blocks)

    # First, handle paragraphs that contain one or more strong Qn. markers.
    # This covers cases where several **Qn.** lines were merged into a single
    # <p> by the HTML converter.
    paragraph_pattern = re.compile(
        r"<p>(?P<inner>(?:.*?<strong>Q\d+\.</strong>.*?)+)</p>",
        re.DOTALL,
    )
    transformed = paragraph_pattern.sub(paragraph_repl, html_body)

    return transformed

def markdown_to_pdf(markdown_content: str, output_path: str, title: str = "Report"):
    """Converts Markdown to a styled PDF with cover page and question formatting."""
    html_body = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])
    html_body = _transform_questions(html_body)

    # Optional table of contents generation based on h2 tags
    toc_items = re.findall(r"<h2>(.*?)</h2>", html_body)
    toc_html = "<div class='toc'><h2>Contents</h2><ul>" + "".join(
        f"<li>{i+1}. {item}</li>" for i, item in enumerate(toc_items)
    ) + "</ul></div>"

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
    </head>
    <body>
        <div class="cover-page">
            <div class="cover-title">{title}</div>
            <div class="cover-subtitle">Generated by Kripaa AI</div>
            <p>{os.environ.get('USERNAME', 'User')}</p>
        </div>
        {toc_html}
        {html_body}
    </body>
    </html>
    """
    generate_pdf_from_html(full_html, output_path)
