"""PDF Reporting service for experiments (Phase 4)."""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from rbccps_dashboard.config import get_settings
from rbccps_dashboard.models import Run

def generate_run_report(run_id: int, session: Session) -> io.BytesIO:
    """Generate a PDF report for a completed run."""
    run = session.get(Run, run_id)
    if not run:
        raise KeyError(f"Run not found: {run_id}")
        
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    Story = []
    
    # Title
    Story.append(Paragraph(f"Experiment Report: {run.metadata_json.get('experiment_name', 'Unknown')}", styles["Title"]))
    Story.append(Spacer(1, 12))
    
    # Metadata
    Story.append(Paragraph(f"Run ID: {run.id}", styles["Normal"]))
    Story.append(Paragraph(f"Status: {run.status}", styles["Normal"]))
    if run.started_at:
        Story.append(Paragraph(f"Started At: {run.started_at.strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    if run.finished_at:
        Story.append(Paragraph(f"Finished At: {run.finished_at.strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    Story.append(Spacer(1, 12))
    
    # Configuration Details
    Story.append(Paragraph("Configuration Snapshot", styles["Heading2"]))
    config = run.experiment.config_snapshot if run.experiment else {}
    
    config_data = [["Parameter", "Value"]]
    
    def flatten_config(d: dict, prefix: str = "") -> list:
        items = []
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                items.extend(flatten_config(v, key))
            else:
                items.append([key, str(v)])
        return items
        
    config_data.extend(flatten_config(config))
    
    if len(config_data) > 1:
        t = Table(config_data, colWidths=[200, 200])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        Story.append(t)
    Story.append(Spacer(1, 12))
    
    # Include Artifacts
    Story.append(Paragraph("Visualizations", styles["Heading2"]))
    
    if run.output_dir:
        output_path = Path(run.output_dir)
        if output_path.exists():
            for img_file in output_path.glob("*.png"):
                Story.append(Paragraph(f"Artifact: {img_file.name}", styles["Heading3"]))
                Story.append(Spacer(1, 6))
                try:
                    img = RLImage(str(img_file))
                    # Scale down to fit page width
                    ratio = min(400 / img.drawWidth, 300 / img.drawHeight)
                    img.drawWidth = img.drawWidth * ratio
                    img.drawHeight = img.drawHeight * ratio
                    Story.append(img)
                except Exception:
                    Story.append(Paragraph("(Failed to load image)", styles["Normal"]))
                Story.append(Spacer(1, 12))
                
    doc.build(Story)
    buffer.seek(0)
    return buffer
