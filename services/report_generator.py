import io
import datetime
import pandas as pd
import json

def build_report_data(state: dict, selections: dict) -> dict:
    data = {}
    if selections.get("profiling"):
        data["profiling"] = state.get("profiling_summary", "No profiling data generated.")
    if selections.get("cleaning"):
        data["cleaning"] = state.get("cleaning_logs", [])
    if selections.get("kpis"):
        data["kpis"] = state.get("kpis", [])
    if selections.get("insights"):
        data["executive_summary"] = state.get("executive_summary", "")
        data["insights"] = state.get("insights_findings", [])
        data["risks"] = state.get("insights_risks", [])
        data["opportunities"] = state.get("insights_opps", [])
        data["recommendations"] = state.get("insights_recs", [])
    if selections.get("chat"):
        data["chat_history"] = state.get("chat_history", [])
    
    # We always pull dataset intelligence if available
    data["dataset_type"] = state.get("dataset_type", "General")
    data["confidence"] = state.get("dataset_confidence", 0)
    data["entities"] = state.get("dataset_entities", [])
    
    return data

def generate_html_report(report_data: dict, branding: dict) -> str:
    html = f"""
    <html>
    <head>
        <title>{branding['title']}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; color: #333; line-height: 1.6; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #2980b9; margin-top: 40px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
            h3 {{ color: #16a085; }}
            .kpi-container {{ display: flex; flex-wrap: wrap; gap: 20px; }}
            .kpi-card {{ border: 1px solid #ddd; padding: 20px; border-radius: 8px; width: calc(33% - 20px); background: #fdfefe; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); box-sizing: border-box; }}
            .kpi-title {{ margin: 0; color: #7f8c8d; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }}
            .kpi-val {{ font-size: 28px; color: #2c3e50; font-weight: bold; margin: 10px 0; }}
            .kpi-desc {{ font-size: 12px; color: #95a5a6; margin: 0; }}
            .insight-card {{ border-left: 4px solid #3498db; padding: 15px 20px; margin: 15px 0; background: #f4f6f7; border-radius: 0 5px 5px 0; }}
            .insight-card h4 {{ margin: 0 0 10px 0; color: #2c3e50; }}
            .insight-card p {{ margin: 0; }}
            .risk-card {{ border-left-color: #e74c3c; background: #fdf2e9; }}
            .rec-card {{ border-left-color: #27ae60; background: #e9f7ef; }}
            .chat-msg {{ margin: 15px 0; padding: 15px; border-radius: 8px; box-shadow: 1px 1px 5px rgba(0,0,0,0.05); }}
            .chat-user {{ background: #ebf5fb; border: 1px solid #d6eaf8; }}
            .chat-ai {{ background: #fdfefe; border: 1px solid #eaeded; }}
            .header {{ text-align: center; margin-bottom: 50px; background: #2c3e50; color: white; padding: 40px; border-radius: 8px; }}
            .header h1 {{ color: white; border: none; margin: 0 0 10px 0; }}
            .header p {{ margin: 5px 0; color: #bdc3c7; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{branding['title']}</h1>
            <h3>Prepared for: {branding['company']}</h3>
            <p><strong>Analyst:</strong> {branding['analyst']}</p>
            <p><strong>Date:</strong> {datetime.datetime.now().strftime('%Y-%m-%d')}</p>
            <p><strong>Dataset Profile:</strong> {report_data.get('dataset_type', 'N/A')} Dataset</p>
        </div>
    """
    
    if "executive_summary" in report_data and report_data["executive_summary"]:
        html += f"<h2>Executive Summary</h2><p>{report_data['executive_summary']}</p>"
        
    if "kpis" in report_data and report_data["kpis"]:
        html += "<h2>Key Performance Indicators (KPIs)</h2><div class='kpi-container'>"
        for kpi in report_data["kpis"]:
            html += f"<div class='kpi-card'><p class='kpi-title'>{kpi['name']}</p><div class='kpi-val'>{kpi['value']}</div><p class='kpi-desc'>{kpi['description']}</p></div>"
        html += "</div>"
        
    if "insights" in report_data and report_data["insights"]:
        html += "<h2>Key Findings</h2>"
        for ins in report_data["insights"]:
            html += f"<div class='insight-card'><h4>{ins['title']}</h4><p>{ins['description']}</p></div>"
            
    if "risks" in report_data and report_data["risks"]:
        html += "<h2>Business Risks</h2>"
        for r in report_data["risks"]:
            html += f"<div class='insight-card risk-card'><h4>{r['title']}</h4><p>{r['description']}</p></div>"
            
    if "recommendations" in report_data and report_data["recommendations"]:
        html += "<h2>Actionable Recommendations</h2>"
        for r in report_data["recommendations"]:
            html += f"<div class='insight-card rec-card'><h4>{r['title']}</h4><p>{r['description']}</p></div>"

    if "chat_history" in report_data and report_data["chat_history"]:
        html += "<h2>Analytics Chat Log</h2>"
        for msg in report_data["chat_history"]:
            cls = "chat-user" if msg['role'] == 'user' else "chat-ai"
            role_name = "Analyst" if msg['role'] == 'user' else "InsightFlow AI"
            content = str(msg['content']).replace('\n', '<br>')
            html += f"<div class='chat-msg {cls}'><strong>{role_name}:</strong><br><br>{content}</div>"

    html += "</body></html>"
    return html

def generate_pdf_report(report_data: dict, branding: dict) -> io.BytesIO:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
    except ImportError:
        raise ImportError("ReportLab is not installed. Run `pip install reportlab` or download the HTML version.")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterTitle', parent=styles['Heading1'], alignment=TA_CENTER))
    
    Story = []
    
    # Title Page
    Story.append(Paragraph(branding['title'], styles["CenterTitle"]))
    Story.append(Spacer(1, 12))
    Story.append(Paragraph(f"Company: {branding['company']}", styles["Normal"]))
    Story.append(Paragraph(f"Analyst: {branding['analyst']}", styles["Normal"]))
    Story.append(Paragraph(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}", styles["Normal"]))
    Story.append(Spacer(1, 48))
    
    if "executive_summary" in report_data and report_data["executive_summary"]:
        Story.append(Paragraph("Executive Summary", styles["Heading2"]))
        Story.append(Paragraph(report_data["executive_summary"], styles["Normal"]))
        Story.append(Spacer(1, 12))
        
    if "kpis" in report_data and report_data["kpis"]:
        Story.append(Paragraph("Key Performance Indicators (KPIs)", styles["Heading2"]))
        for kpi in report_data["kpis"]:
            text = f"<b>{kpi['name']}:</b> {kpi['value']} - <i>{kpi['description']}</i>"
            Story.append(Paragraph(text, styles["Normal"]))
        Story.append(Spacer(1, 12))
        
    if "insights" in report_data and report_data["insights"]:
        Story.append(Paragraph("Key Findings", styles["Heading2"]))
        for ins in report_data["insights"]:
            Story.append(Paragraph(f"<b>{ins['title']}:</b> {ins['description']}", styles["Normal"]))
        Story.append(Spacer(1, 12))
        
    if "recommendations" in report_data and report_data["recommendations"]:
        Story.append(Paragraph("Recommendations", styles["Heading2"]))
        for r in report_data["recommendations"]:
            Story.append(Paragraph(f"<b>{r['title']}:</b> {r['description']}", styles["Normal"]))
        Story.append(Spacer(1, 12))
        
    if "chat_history" in report_data and report_data["chat_history"]:
        Story.append(Paragraph("Chat Log Snippets", styles["Heading2"]))
        for msg in report_data["chat_history"][-10:]:
            clean_text = str(msg['content']).replace("*", "")
            Story.append(Paragraph(f"<b>{msg['role'].upper()}:</b> {clean_text}", styles["Normal"]))
            Story.append(Spacer(1, 6))

    doc.build(Story)
    buffer.seek(0)
    return buffer

def generate_docx_report(report_data: dict, branding: dict) -> io.BytesIO:
    try:
        import docx
    except ImportError:
        raise ImportError("python-docx is not installed. Run `pip install python-docx` or download the HTML version.")
        
    doc = docx.Document()
    
    doc.add_heading(branding['title'], 0)
    doc.add_paragraph(f"Company: {branding['company']}")
    doc.add_paragraph(f"Analyst: {branding['analyst']}")
    doc.add_paragraph(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}")
    doc.add_paragraph(f"Dataset Type: {report_data.get('dataset_type', 'N/A')}")
    
    if "executive_summary" in report_data and report_data["executive_summary"]:
        doc.add_heading("Executive Summary", level=1)
        doc.add_paragraph(report_data["executive_summary"])
        
    if "kpis" in report_data and report_data["kpis"]:
        doc.add_heading("Key Performance Indicators (KPIs)", level=1)
        for kpi in report_data["kpis"]:
            p = doc.add_paragraph()
            p.add_run(f"{kpi['name']}: ").bold = True
            p.add_run(f"{kpi['value']} - ")
            p.add_run(f"{kpi['description']}").italic = True
            
    if "insights" in report_data and report_data["insights"]:
        doc.add_heading("Key Findings", level=1)
        for ins in report_data["insights"]:
            p = doc.add_paragraph(style='List Bullet')
            p.add_run(f"{ins['title']}: ").bold = True
            p.add_run(ins['description'])
            
    if "recommendations" in report_data and report_data["recommendations"]:
        doc.add_heading("Recommendations", level=1)
        for r in report_data["recommendations"]:
            p = doc.add_paragraph(style='List Bullet')
            p.add_run(f"{r['title']}: ").bold = True
            p.add_run(r['description'])
            
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
