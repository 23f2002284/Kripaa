import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

def generate_simple_exam_pdf(markdown_path: str, output_path: str):
    """
    Generate a simple, clean PDF from markdown - looks like a plain exam paper.
    """
    # Read markdown
    with open(markdown_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert to HTML
    html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    
    # Simple, clean CSS - looks like a printed document
    simple_css = CSS(string="""
        @page {
            size: A4;
            margin: 2.5cm;
            @bottom-center {
                content: counter(page);
                font-size: 10pt;
            }
        }
        body {
            font-family: 'Times New Roman', serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #000;
        }
        h1 {
            font-size: 18pt;
            font-weight: bold;
            text-align: center;
            margin-bottom: 0.5em;
        }
        h2 {
            font-size: 14pt;
            font-weight: bold;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }
        p {
            margin-bottom: 1em;
        }
        strong {
            font-weight: bold;
        }
        hr {
            border: none;
            border-top: 1px solid #000;
            margin: 1em 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1em 0;
        }
        th, td {
            border: 1px solid #000;
            padding: 0.5em;
        }
    """)
    
    # Wrap in HTML
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Exam Paper</title>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """
    
    font_config = FontConfiguration()
    HTML(string=full_html).write_pdf(output_path, stylesheets=[simple_css], font_config=font_config)
    print(f"Simple PDF generated: {output_path}")

if __name__ == "__main__":
    generate_simple_exam_pdf("generated_paper.md", "generated_paper_simple.pdf")
