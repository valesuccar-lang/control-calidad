#!/usr/bin/env python3
import sys
from pathlib import Path

# Try to install and use available libraries
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
except ImportError:
    print("Installing reportlab...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab", "-q"])
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

try:
    import markdown
except ImportError:
    print("Installing markdown...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "markdown", "-q"])
    import markdown

def markdown_to_pdf(md_file, pdf_file):
    """Convert markdown file to PDF"""

    # Read markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Create PDF
    doc = SimpleDocTemplate(pdf_file, pagesize=A4,
                           topMargin=0.75*inch,
                           bottomMargin=0.75*inch,
                           leftMargin=0.75*inch,
                           rightMargin=0.75*inch)

    # Get styles
    styles = getSampleStyleSheet()

    # Define custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=8,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )

    code_style = ParagraphStyle(
        'CustomCode',
        parent=styles['BodyText'],
        fontSize=9,
        textColor=colors.HexColor('#555555'),
        fontName='Courier',
        backColor=colors.HexColor('#f5f5f5'),
        leftIndent=10,
        rightIndent=10,
        spaceAfter=8
    )

    # Parse markdown and build content
    story = []
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i]

        # Handle title
        if line.startswith('# ') and not line.startswith('# SEGMENTO'):
            text = line.replace('# ', '').strip()
            story.append(Paragraph(text, title_style))
            story.append(Spacer(1, 0.2*inch))

        # Handle headings
        elif line.startswith('## '):
            text = line.replace('## ', '').replace('{#segmento-', '').replace('}', '').strip()
            story.append(Paragraph(text, heading1_style))
            story.append(Spacer(1, 0.1*inch))

        elif line.startswith('### '):
            text = line.replace('### ', '').strip()
            story.append(Paragraph(text, heading2_style))
            story.append(Spacer(1, 0.08*inch))

        # Handle code blocks
        elif line.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1
            code_text = '\n'.join(code_lines)
            # For code blocks, just add as mono-spaced text
            for code_line in code_lines:
                if code_line.strip():
                    story.append(Paragraph(code_line.replace('<', '&lt;').replace('>', '&gt;'), code_style))
            story.append(Spacer(1, 0.1*inch))

        # Handle horizontal rules
        elif line.strip() == '---':
            story.append(Spacer(1, 0.1*inch))

        # Handle bold text and regular paragraphs
        elif line.strip() and not line.startswith('|'):
            text = line.strip()
            # Convert markdown bold/italic to HTML
            text = text.replace('**', '<b>').replace('**', '</b>')
            text = text.replace('__', '<b>').replace('__', '</b>')
            text = text.replace('*', '<i>').replace('*', '</i>')
            text = text.replace('_', '<i>').replace('_', '</i>')
            # Replace common markdown patterns
            text = text.replace('❌', '[X]').replace('✅', '[OK]').replace('✓', '[OK]')
            text = text.replace('🎯', '[*]').replace('📊', '[*]').replace('🏗️', '[*]')
            text = text.replace('💼', '[*]').replace('⚠️', '[!]').replace('🚨', '[!]')
            text = text.replace('🔴', '[!]').replace('🟡', '[!]').replace('🟢', '[OK]')

            story.append(Paragraph(text, body_style))

        # Handle tables with simple approximation
        elif line.strip().startswith('|'):
            story.append(Spacer(1, 0.05*inch))

        elif line.strip() == '':
            story.append(Spacer(1, 0.05*inch))

        i += 1

    # Build PDF
    doc.build(story)
    print(f"✓ PDF generado: {pdf_file}")

if __name__ == "__main__":
    md_file = r"c:\Users\user\Documents\CURSO30X\PROYECTO\specs\prd.md"
    pdf_file = r"c:\Users\user\Documents\CURSO30X\PROYECTO\specs\prd.pdf"

    try:
        markdown_to_pdf(md_file, pdf_file)
        print(f"Success: {pdf_file}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
