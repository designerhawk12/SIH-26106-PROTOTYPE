"""ReportLab-based PDF generation service."""

import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from .interfaces import ReportingService
from ...schemas import EmailAnalysis


def _safe(text: str | None) -> str:
    """Escape text to prevent ReportLab XML tag injection."""
    if text is None:
        return "Unknown"
    return escape(str(text))


class ReportLabReportingService(ReportingService):
    """Generates PDF reports from EmailAnalysis using ReportLab."""

    async def render_pdf(self, analysis: EmailAnalysis) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
            title=f"Forensic Analysis Report - {analysis.case_id}",
        )

        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        heading_style = styles["Heading2"]
        subheading_style = styles["Heading3"]
        normal_style = styles["Normal"]
        
        # Adjust normal style for table cells if needed
        cell_style = ParagraphStyle(
            "CellStyle",
            parent=normal_style,
            fontSize=9,
            leading=11,
            wordWrap="CJK",
        )

        story = []

        # Title
        story.append(Paragraph("Forensic Analysis Report", title_style))
        story.append(
            Paragraph(
                "Evidence collected and analyzed by the platform.",
                ParagraphStyle("Subtitle", parent=normal_style, alignment=1, spaceAfter=20),
            )
        )

        # 1. Case Overview
        story.append(Paragraph("Case Overview", heading_style))
        case_data = [
            ["Case ID", str(analysis.case_id)],
            ["Analysis Status", analysis.status.value],
            ["Original Filename", _safe(analysis.original_filename)],
            ["Created At", analysis.created_at.isoformat()],
            ["Completed At", analysis.completed_at.isoformat() if analysis.completed_at else "Pending"],
        ]
        story.append(self._build_table(case_data, cell_style, header=False))
        story.append(Spacer(1, 12))

        # 2. Risk Assessment
        if analysis.risk:
            story.append(Paragraph("Deterministic Risk Assessment", heading_style))
            risk_data = [
                ["Risk Score", str(analysis.risk.score)],
                ["Severity", analysis.risk.severity.value],
            ]
            if analysis.risk.formula_version:
                risk_data.append(["Version", analysis.risk.formula_version])
            story.append(self._build_table(risk_data, cell_style, header=False))
            
            if analysis.risk.reasons:
                story.append(Spacer(1, 6))
                story.append(Paragraph("Risk Factors", subheading_style))
                reason_data = [["Code", "Points", "Description"]]
                for reason in analysis.risk.reasons:
                    reason_data.append([
                        reason.code,
                        f"+{reason.points}",
                        _safe(reason.description)
                    ])
                story.append(self._build_table(reason_data, cell_style, header=True))
            story.append(Spacer(1, 12))

        # 3. Email Metadata & Integrity
        if analysis.parsed_email:
            story.append(Paragraph("Email Metadata", heading_style))
            pe = analysis.parsed_email
            
            headers = [
                ["Subject", _safe(pe.subject)],
                ["Sender", _safe(pe.sender.address if pe.sender else None)],
                ["Sender Display", _safe(pe.sender.display_name if pe.sender else None)],
                ["Recipients", _safe(", ".join([r.address for r in pe.to]) if pe.to else "Unknown")],
            ]
            if pe.cc:
                headers.append(["CC", _safe(", ".join([r.address for r in pe.cc]))])
            if pe.bcc:
                headers.append(["BCC", _safe(", ".join([r.address for r in pe.bcc]))])
            headers.append(["Reply-To", _safe(", ".join([r.address for r in pe.reply_to]) if pe.reply_to else None)])
            
            return_path = None
            if "return-path" in pe.headers and pe.headers["return-path"]:
                return_path = pe.headers["return-path"][0]
            headers.append(["Return-Path", _safe(return_path)])
            
            headers.append(["Message-ID", _safe(pe.message_id)])
            headers.append(["Sent Timestamp", _safe(pe.sent_at.isoformat() if pe.sent_at else None)])

            story.append(self._build_table(headers, cell_style, header=False))
            story.append(Spacer(1, 12))

            # Integrity
            story.append(Paragraph("Evidence Integrity", heading_style))
            integrity = [["Email SHA-256", _safe(pe.original_sha256)]]
            story.append(self._build_table(integrity, cell_style, header=False))
            story.append(Spacer(1, 12))

            # Authentication
            if pe.authentication:
                story.append(Paragraph("Authentication", heading_style))
                auth = pe.authentication
                auth_data = [
                    ["SPF", auth.spf.value if auth.spf else "UNKNOWN"],
                    ["DKIM", auth.dkim.value if auth.dkim else "UNKNOWN"],
                    ["DMARC", auth.dmarc.value if auth.dmarc else "UNKNOWN"],
                ]
                story.append(self._build_table(auth_data, cell_style, header=False))
                story.append(Spacer(1, 12))

            # Received Hops
            if pe.received_hops:
                story.append(Paragraph("Received / Routing Observations", heading_style))
                hops_data = [["Hop", "From Host", "By Host", "Protocol", "Timestamp", "IP"]]
                for i, hop in enumerate(pe.received_hops):
                    hops_data.append([
                        str(i + 1),
                        _safe(hop.from_host),
                        _safe(hop.by_host),
                        _safe(hop.protocol),
                        _safe(hop.timestamp),
                        _safe(hop.source_ip),
                    ])
                story.append(self._build_table(hops_data, cell_style, header=True))
                story.append(Spacer(1, 12))

            # Attachments
            if pe.attachments:
                story.append(Paragraph("Attachments", heading_style))
                story.append(Paragraph("Note: Attachments were collected as evidence and not executed.", normal_style))
                story.append(Spacer(1, 6))
                att_data = [["Filename", "Content-Type", "Size", "SHA-256"]]
                for att in pe.attachments:
                    att_data.append([
                        _safe(att.filename),
                        _safe(att.content_type),
                        str(att.size),
                        _safe(att.sha256)
                    ])
                story.append(self._build_table(att_data, cell_style, header=True))
                story.append(Spacer(1, 12))

        # 4. Detection Findings
        if analysis.detection and analysis.detection.findings:
            story.append(Paragraph("Automated Threat Detection Findings", heading_style))
            det_data = [["Category", "Severity", "Title", "Explanation"]]
            for f in analysis.detection.findings:
                det_data.append([
                    f.category.value,
                    f.severity.value,
                    _safe(f.title),
                    _safe(f.explanation)
                ])
            story.append(self._build_table(det_data, cell_style, header=True))
            story.append(Spacer(1, 12))

        # 5. Indicators of Compromise & Threat Intelligence
        if analysis.threat_intel and analysis.threat_intel.findings:
            story.append(Paragraph("Threat-Intelligence Enrichment", heading_style))
            ioc_data = [["Indicator", "Type", "Provider", "Verdict", "Confidence"]]
            for f in analysis.threat_intel.findings:
                ioc_data.append([
                    _safe(f.indicator),
                    f.indicator_type.value,
                    _safe(f.provider),
                    f.verdict.value,
                    _safe(str(f.confidence) if f.confidence is not None else "Unknown")
                ])
            story.append(self._build_table(ioc_data, cell_style, header=True))
            story.append(Spacer(1, 12))

        # 6. Observed Mail-Routing Infrastructure
        if analysis.geolocations:
            story.append(Paragraph("Observed Mail-Routing Infrastructure", heading_style))
            geo_data = [["IP Address", "Country", "Provider", "ASN"]]
            for geo in analysis.geolocations:
                geo_data.append([
                    _safe(geo.ip_address),
                    _safe(geo.country),
                    _safe(geo.provider),
                    _safe(geo.asn)
                ])
            story.append(self._build_table(geo_data, cell_style, header=True))
            story.append(Spacer(1, 12))

        # 7. Timeline / Evidence Events
        if analysis.timeline:
            story.append(Paragraph("Timeline Events", heading_style))
            time_data = [["Seq", "Timestamp", "Event Type", "Title", "Source"]]
            for evt in sorted(analysis.timeline, key=lambda x: x.sequence):
                time_data.append([
                    str(evt.sequence),
                    evt.timestamp.isoformat() if evt.timestamp else "Unknown",
                    evt.event_type.value,
                    _safe(evt.title),
                    _safe(evt.source)
                ])
            story.append(self._build_table(time_data, cell_style, header=True))
            story.append(Spacer(1, 12))

        # 8. Warnings / Errors
        if analysis.warnings or analysis.errors:
            story.append(Paragraph("Warnings and Limitations", heading_style))
            for w in analysis.warnings:
                story.append(Paragraph(f"Warning: {_safe(w)}", normal_style))
            for e in analysis.errors:
                story.append(Paragraph(f"Error: {_safe(e)}", normal_style))
            story.append(Spacer(1, 12))

        # Disclaimer
        story.append(Spacer(1, 24))
        disclaimer_text = (
            "This report summarizes automated forensic analysis and enrichment performed by the platform. "
            "Infrastructure geolocation describes observed network or mail-routing infrastructure and does not establish "
            "the physical location or identity of an attacker. Threat-intelligence and automated detection results "
            "should be interpreted as investigative indicators and not as definitive attribution."
        )
        story.append(Paragraph(disclaimer_text, ParagraphStyle("Disclaimer", parent=normal_style, fontSize=8, textColor=colors.gray)))

        doc.build(story)
        return buffer.getvalue()

    def _build_table(self, data: list[list[str]], cell_style: ParagraphStyle, header: bool = False) -> Table:
        table_data = []
        for row in data:
            new_row = []
            for cell in row:
                new_row.append(Paragraph(str(cell), cell_style))
            table_data.append(new_row)

        t = Table(table_data, repeatRows=1 if header else 0)
        
        table_style = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        
        if header:
            table_style.extend([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                # ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), # handled in Paragraph
            ])
        else:
            table_style.extend([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f9f9f9")),
                # ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ])
            
        t.setStyle(TableStyle(table_style))
        return t
