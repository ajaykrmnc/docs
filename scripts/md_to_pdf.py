#!/usr/bin/env python3
"""Convert markdown file to PDF with proper monospace font for ASCII diagrams."""

import sys
import markdown
from weasyprint import HTML, CSS

def convert_md_to_pdf(input_path: str, output_path: str):
    # Read markdown content
    with open(input_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(
        md_content,
        extensions=['fenced_code', 'tables', 'toc']
    )
    
    # Wrap in full HTML with CSS styling optimized for ASCII diagrams
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4;
                margin: 1.5cm;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.5;
                color: #333;
            }}
            h1 {{
                font-size: 22pt;
                color: #1a1a1a;
                border-bottom: 2px solid #333;
                padding-bottom: 8px;
                margin-top: 24pt;
            }}
            h2 {{
                font-size: 16pt;
                color: #2a2a2a;
                margin-top: 20pt;
                border-bottom: 1px solid #ccc;
                padding-bottom: 4px;
            }}
            h3 {{
                font-size: 13pt;
                color: #3a3a3a;
                margin-top: 16pt;
            }}
            /* Critical for ASCII diagrams - use monospace and preserve spacing */
            pre, code {{
                font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
                font-size: 8pt;
                line-height: 1.2;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            pre {{
                padding: 12px;
                overflow-x: auto;
                white-space: pre;
                page-break-inside: avoid;
            }}
            code {{
                padding: 2px 4px;
            }}
            pre code {{
                padding: 0;
                border: none;
                background: none;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 12pt 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f0f0f0;
            }}
            ul, ol {{
                margin-left: 20px;
            }}
            li {{
                margin: 4px 0;
            }}
            hr {{
                border: none;
                border-top: 1px solid #ccc;
                margin: 20pt 0;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Convert to PDF
    HTML(string=full_html).write_pdf(output_path)
    print(f"✓ Successfully created: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python md_to_pdf.py <input.md> [output.pdf]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        output_file = input_file.rsplit('.', 1)[0] + '.pdf'
    
    convert_md_to_pdf(input_file, output_file)

