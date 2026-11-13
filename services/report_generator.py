import io
import datetime
import pandas as pd
from typing import Dict, Any

def build_report_data(state: dict, selections: dict) -> dict:
    data = {}
    if selections.get("profiling"):
        data["profiling"] = state.get("profiling_summary", "Profiling completed.")
    if selections.get("cleaning"):
        data["cleaning"] = state.get("cleaning_log", [])
    if selections.get("kpis"):
        data["kpis"] = state.get("kpis", [])
    if selections.get("charts"):
        data["charts"] = state.get("charts", [])
    if selections.get("insights"):
        data["executive_summary"] = state.get("executive_summary", "")
        data["insights"] = state.get("insights_findings", [])
        data["risks"] = state.get("insights_risks", [])
        data["opportunities"] = state.get("insights_opps", [])
        data["recommendations"] = state.get("insights_recs", [])
    if selections.get("chat"):
        data["chat_history"] = state.get("chat_history", [])
    
    # Dataset metadata
    data["dataset_type"] = state.get("dataset_type", "General")
    data["confidence"] = state.get("dataset_confidence", 0)
    data["entities"] = state.get("dataset_entities", [])
    metadata = state.get("metadata", {})
    if metadata:
        data["filename"] = metadata.get("filename", "dataset")
        data["rows"] = metadata.get("rows", "N/A")
        data["columns"] = metadata.get("columns", "N/A")
    
    return data

def generate_html_report(report_data: dict, branding: dict) -> str:
    charts_html = ""
    if "charts" in report_data and report_data["charts"]:
        charts_html += "<h2>Analytical Visualizations</h2><div class='charts-container'>"
        for ch in report_data["charts"][:6]:  # Limit to top 6 charts for clean document layout
            fig = ch.get("fig")
            if fig is not None:
                try:
                    c_div = fig.to_html(full_html=False, include_plotlyjs='cdn')
                    charts_html += f"<div class='chart-card'><h3>{ch.get('title', 'Chart')}</h3>{c_div}</div>"
                except Exception:
                    pass
        charts_html += "</div>"

    html = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>{branding['title']}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 40px; color: #2c3e50; background: #fafbfc; line-height: 1.6; }}
            .container {{ max-width: 1000px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }}
            h1 {{ color: #1a252f; margin: 0 0 8px 0; font-size: 28px; }}
            h2 {{ color: #2c3e50; margin-top: 36px; padding-bottom: 8px; border-bottom: 2px solid #eaedf0; font-size: 20px; }}
            h3 {{ color: #34495e; font-size: 16px; margin: 16px 0 8px 0; }}
            .header {{ text-align: left; margin-bottom: 36px; padding-bottom: 24px; border-bottom: 3px solid #1a73e8; }}
            .meta-bar {{ display: flex; flex-wrap: wrap; gap: 20px; font-size: 14px; color: #5f6368; margin-top: 12px; }}
            .meta-item {{ background: #f1f3f4; padding: 4px 12px; border-radius: 16px; font-weight: 500; }}
            .kpi-container {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; margin-top: 16px; }}
            .kpi-card {{ border: 1px solid #e1e4e8; padding: 18px; border-radius: 8px; background: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.03); }}
            .kpi-title {{ margin: 0; color: #586069; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }}
            .kpi-val {{ font-size: 26px; color: #1a73e8; font-weight: bold; margin: 8px 0; }}
            .kpi-desc {{ font-size: 12px; color: #6a737d; margin: 0; }}
            .card {{ border-left: 4px solid #1a73e8; padding: 14px 18px; margin: 12px 0; background: #f8f9fa; border-radius: 0 6px 6px 0; }}
            .card h4 {{ margin: 0 0 6px 0; color: #24292e; font-size: 15px; }}
            .card p {{ margin: 0; font-size: 14px; color: #444d56; }}
            .card-risk {{ border-left-color: #d73a49; background: #ffeef0; }}
            .card-rec {{ border-left-color: #28a745; background: #f0fff4; }}
            .charts-container {{ display: grid; grid-template-columns: 1fr; gap: 24px; margin-top: 16px; }}
            .chart-card {{ border: 1px solid #e1e4e8; padding: 16px; border-radius: 8px; background: #fff; }}
            .chat-msg {{ margin: 12px 0; padding: 12px 16px; border-radius: 8px; font-size: 14px; }}
            .chat-user {{ background: #e8f0fe; border-left: 3px solid #1a73e8; }}
            .chat-ai {{ background: #f8f9fa; border-left: 3px solid #34a853; }}
            .footer {{ margin-top: 48px; text-align: center; font-size: 12px; color: #9aa0a6; border-top: 1px solid #eee; padding-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{branding['title']}</h1>
                <div class="meta-bar">
                    <span class="meta-item">Organization: <strong>{branding['company']}</strong></span>
                    <span class="meta-item">Analyst: <strong>{branding['analyst']}</strong></span>
                    <span class="meta-item">Generated: <strong>{datetime.datetime.now().strftime('%Y-%m-%d')}</strong></span>
                    <span class="meta-item">Domain: <strong>{report_data.get('dataset_type', 'General')}</strong></span>
                </div>
            </div>
    """
    
    if report_data.get("executive_summary"):
        html += f"<h2>Executive Summary</h2><p style='font-size: 15px; line-height: 1.6;'>{report_data['executive_summary']}</p>"
        
    if report_data.get("kpis"):
        html += "<h2>Key Performance Indicators (KPIs)</h2><div class='kpi-container'>"
        for kpi in report_data["kpis"]:
            html += f"<div class='kpi-card'><p class='kpi-title'>{kpi['name']}</p><div class='kpi-val'>{kpi['value']}</div><p class='kpi-desc'>{kpi.get('description', '')}</p></div>"
        html += "</div>"
        
    if report_data.get("insights"):
        html += "<h2>Key Observations</h2>"
        for ins in report_data["insights"]:
            html += f"<div class='card'><h4>{ins.get('title', '')}</h4><p>{ins.get('description', '')}</p></div>"
            
    if report_data.get("risks"):
        html += "<h2>Operational & Strategic Risks</h2>"
        for r in report_data["risks"]:
            html += f"<div class='card card-risk'><h4>{r.get('title', '')}</h4><p>{r.get('description', '')}</p></div>"
            
    if report_data.get("recommendations"):
        html += "<h2>Actionable Recommendations</h2>"
        for r in report_data["recommendations"]:
            html += f"<div class='card card-rec'><h4>{r.get('title', '')}</h4><p>{r.get('description', '')}</p></div>"

    html += charts_html

    if report_data.get("chat_history"):
        html += "<h2>Conversational Analytics Transcript</h2>"
        for msg in report_data["chat_history"]:
            cls = "chat-user" if msg['role'] == 'user' else "chat-ai"
            role_name = "User Query" if msg['role'] == 'user' else "InsightFlow AI"
            content = str(msg['content']).replace('\n', '<br>')
            html += f"<div class='chat-msg {cls}'><strong>{role_name}:</strong><br>{content}</div>"

    html += """
            <div class="footer">
                Compiled automatically via InsightFlow AI Universal Analytics Platform.
            </div>
        </div>
    </body>
    </html>
    """
    return html

def generate_pdf_report(report_data: dict, branding: dict) -> io.BytesIO:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        raise ImportError("ReportLab is not installed. Please install reportlab to generate PDF exports.")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=54, 
        leftMargin=54, 
        topMargin=54, 
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Safe style additions without duplicates
    if 'ReportTitle' not in styles:
        styles.add(ParagraphStyle(name='ReportTitle', parent=styles['Title'], alignment=TA_LEFT, fontSize=22, leading=26, textColor=colors.HexColor('#1a252f')))
    if 'ReportSubTitle' not in styles:
        styles.add(ParagraphStyle(name='ReportSubTitle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#5f6368')))
    if 'ReportH2' not in styles:
        styles.add(ParagraphStyle(name='ReportH2', parent=styles['Heading2'], fontSize=14, leading=18, textColor=colors.HexColor('#1a73e8'), spaceBefore=14, spaceAfter=8))
    if 'ReportBody' not in styles:
        styles.add(ParagraphStyle(name='ReportBody', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#2c3e50')))
    if 'CardTitle' not in styles:
        styles.add(ParagraphStyle(name='CardTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=12, textColor=colors.HexColor('#1a252f')))
    if 'CardDesc' not in styles:
        styles.add(ParagraphStyle(name='CardDesc', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#444d56')))

    story = []
    
    # Header Banner
    story.append(Paragraph(branding['title'], styles['ReportTitle']))
    meta_line = f"Organization: <b>{branding['company']}</b> | Analyst: <b>{branding['analyst']}</b> | Date: <b>{datetime.datetime.now().strftime('%Y-%m-%d')}</b> | Domain: <b>{report_data.get('dataset_type', 'General')}</b>"
    story.append(Spacer(1, 4))
    story.append(Paragraph(meta_line, styles['ReportSubTitle']))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a73e8'), spaceAfter=14))
    
    # Executive Summary
    if report_data.get("executive_summary"):
        story.append(Paragraph("Executive Summary", styles['ReportH2']))
        story.append(Paragraph(report_data["executive_summary"], styles['ReportBody']))
        story.append(Spacer(1, 12))
        
    # KPIs as a clean Table
    if report_data.get("kpis"):
        story.append(Paragraph("Key Performance Indicators (KPIs)", styles['ReportH2']))
        table_data = [["Metric Name", "Calculated Value", "Description / Formula"]]
        for k in report_data["kpis"][:8]:
            table_data.append([
                Paragraph(f"<b>{k['name']}</b>", styles['CardTitle']),
                Paragraph(f"<font color='#1a73e8'><b>{k['value']}</b></font>", styles['CardTitle']),
                Paragraph(k.get('description', k.get('formula', '')), styles['CardDesc'])
            ])
            
        kpi_table = Table(table_data, colWidths=[130, 110, 260])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f3f4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a252f')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 14))
        
    # Observations
    if report_data.get("insights"):
        story.append(Paragraph("Key Observations", styles['ReportH2']))
        for ins in report_data["insights"][:5]:
            p_text = f"• <b>{ins.get('title', '')}:</b> {ins.get('description', '')}"
            story.append(Paragraph(p_text, styles['ReportBody']))
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 8))
        
    # Risks & Recommendations
    if report_data.get("risks"):
        story.append(Paragraph("Operational & Strategic Risks", styles['ReportH2']))
        for r in report_data["risks"][:4]:
            p_text = f"• <font color='#d73a49'><b>[{r.get('priority', 'Risk').upper()}] {r.get('title', '')}:</b></font> {r.get('description', '')}"
            story.append(Paragraph(p_text, styles['ReportBody']))
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 8))

    if report_data.get("recommendations"):
        story.append(Paragraph("Prescriptive Recommendations", styles['ReportH2']))
        for rec in report_data["recommendations"][:4]:
            p_text = f"• <font color='#28a745'><b>{rec.get('title', '')}:</b></font> {rec.get('description', '')}"
            story.append(Paragraph(p_text, styles['ReportBody']))
            story.append(Spacer(1, 4))
            
    # Footer notice
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc'), spaceAfter=8))
    story.append(Paragraph("InsightFlow AI — Verified Automated Analytics Report", styles['ReportSubTitle']))

    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_docx_report(report_data: dict, branding: dict) -> io.BytesIO:
    try:
        import docx
    except ImportError:
        raise ImportError("python-docx is not installed. Please install python-docx to generate DOCX exports.")
        
    doc = docx.Document()
    
    # Document Title & Metadata
    title_p = doc.add_heading(branding['title'], 0)
    meta_p = doc.add_paragraph()
    meta_p.add_run(f"Organization: {branding['company']}  |  Analyst: {branding['analyst']}  |  Date: {datetime.datetime.now().strftime('%Y-%m-%d')}  |  Domain: {report_data.get('dataset_type', 'General')}\n").italic = True
    
    if report_data.get("executive_summary"):
        doc.add_heading("Executive Summary", level=1)
        doc.add_paragraph(report_data["executive_summary"])
        
    if report_data.get("kpis"):
        doc.add_heading("Key Performance Indicators (KPIs)", level=1)
        table = doc.add_table(rows=1, cols=3)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "Metric Name"
        hdr_cells[1].text = "Value"
        hdr_cells[2].text = "Description"
        
        for k in report_data["kpis"]:
            row_cells = table.add_row().cells
            row_cells[0].text = k.get("name", "")
            row_cells[1].text = str(k.get("value", ""))
            row_cells[2].text = k.get("description", k.get("formula", ""))
            
    if report_data.get("insights"):
        doc.add_heading("Key Observations", level=1)
        for ins in report_data["insights"]:
            p = doc.add_paragraph(style='List Bullet')
            p.add_run(f"{ins.get('title', '')}: ").bold = True
            p.add_run(ins.get('description', ''))
            
    if report_data.get("risks"):
        doc.add_heading("Strategic Risks", level=1)
        for r in report_data["risks"]:
            p = doc.add_paragraph(style='List Bullet')
            p.add_run(f"[{r.get('priority', 'Risk')}] {r.get('title', '')}: ").bold = True
            p.add_run(r.get('description', ''))
            
    if report_data.get("recommendations"):
        doc.add_heading("Recommendations", level=1)
        for r in report_data["recommendations"]:
            p = doc.add_paragraph(style='List Bullet')
            p.add_run(f"{r.get('title', '')}: ").bold = True
            p.add_run(r.get('description', ''))
            
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
