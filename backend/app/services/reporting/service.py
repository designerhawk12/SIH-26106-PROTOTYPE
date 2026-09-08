"""Professional, evidence-only ReportLab PDF rendering for Sentinel MX."""

from __future__ import annotations

import io
from datetime import datetime, timezone
from html import unescape
from typing import Iterable, Sequence
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ...schemas import AnalystNote, EmailAnalysis
from .interfaces import ReportingService

NAVY = colors.HexColor("#102235")
CHARCOAL = colors.HexColor("#273443")
LIME = colors.HexColor("#A4C639")
PAPER = colors.HexColor("#FAFBFC")
BORDER = colors.HexColor("#D8DEE5")
MUTED = colors.HexColor("#5B6875")


def _safe(value: object | None) -> str:
    """Render evidence and notes as inert, escaped text."""
    if value is None or value == "":
        return "No data available"
    # Some evidence was already entity-escaped upstream. Normalize it first,
    # then escape once so hostile markup remains visible as inert text.
    return escape(unescape(str(value))).replace("\n", "<br/>")


def _timestamp(value: datetime | None) -> str:
    return value.astimezone(timezone.utc).strftime("%d %b %Y %H:%M UTC") if value else "No data available"


class _NumberedCanvas(canvas.Canvas):
    """Add page X of Y and a case-aware footer after pagination."""

    def __init__(self, *args, case_id: str, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self._case_id = case_id
        self._states: list[dict] = []

    def showPage(self) -> None:  # noqa: N802
        self._states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._states)
        for state in self._states:
            self.__dict__.update(state)
            self.setStrokeColor(BORDER)
            self.setLineWidth(0.5)
            self.line(0.55 * inch, 0.48 * inch, 8.0 * inch, 0.48 * inch)
            self.setFillColor(MUTED)
            self.setFont("Helvetica", 7.5)
            self.drawString(0.55 * inch, 0.3 * inch, "Sentinel MX - Email Threat Investigation Report")
            self.drawRightString(8.0 * inch, 0.3 * inch, f"Case ID: {self._case_id}  |  Page {self._pageNumber} of {total}")
            super().showPage()
        super().save()


class ReportLabReportingService(ReportingService):
    """Render persisted analysis and notes without network, provider, or AI calls."""

    async def render_pdf(
        self,
        analysis: EmailAnalysis,
        *,
        analyst_notes: Sequence[AnalystNote] = (),
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.55 * inch,
            leftMargin=0.55 * inch,
            topMargin=0.55 * inch,
            bottomMargin=0.72 * inch,
            title=f"Sentinel MX Investigation Report - {analysis.case_id}",
            author="Sentinel MX",
        )
        styles = self._styles()
        story: list[object] = []
        story.extend(self._cover(analysis, styles))
        story.extend(self._executive_summary(analysis, styles))
        story.extend(self._email_overview(analysis, styles))
        story.extend(self._authentication(analysis, styles))
        story.extend(self._findings(analysis, styles))
        story.extend(self._indicators(analysis, styles))
        story.extend(self._threat_intelligence(analysis, styles))
        story.extend(self._infrastructure(analysis, styles))
        story.extend(self._timeline(analysis, styles))
        story.extend(self._notes(analyst_notes, styles))
        story.extend(self._integrity(analysis, styles))
        if analysis.warnings or analysis.errors:
            story.extend(self._limitations(analysis, styles))
        story.extend([
            Spacer(1, 12),
            Paragraph(
                "Forensic limitation: observed infrastructure geolocation describes mail-routing infrastructure and does not establish the physical location or identity of an attacker. This report summarizes platform-collected evidence and is not a legal or regulatory certification.",
                styles["disclaimer"],
            ),
        ])
        doc.build(story, canvasmaker=lambda *args, **kwargs: _NumberedCanvas(*args, case_id=str(analysis.case_id), **kwargs))
        return buffer.getvalue()

    def _styles(self) -> dict[str, ParagraphStyle]:
        base = getSampleStyleSheet()["BodyText"]
        return {
            "title": ParagraphStyle("ReportTitle", parent=base, fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=colors.white),
            "subtitle": ParagraphStyle("ReportSubtitle", parent=base, fontName="Helvetica", fontSize=9, leading=12, textColor=colors.HexColor("#D8E0E8")),
            "eyebrow": ParagraphStyle("Eyebrow", parent=base, fontName="Helvetica-Bold", fontSize=7.5, leading=9, textColor=LIME, spaceAfter=4),
            "section": ParagraphStyle("Section", parent=base, fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=NAVY, spaceBefore=14, spaceAfter=7, keepWithNext=True),
            "subsection": ParagraphStyle("Subsection", parent=base, fontName="Helvetica-Bold", fontSize=9.5, leading=12, textColor=CHARCOAL, spaceBefore=7, spaceAfter=4, keepWithNext=True),
            "body": ParagraphStyle("Body", parent=base, fontName="Helvetica", fontSize=8.8, leading=12, textColor=CHARCOAL),
            "cell": ParagraphStyle("Cell", parent=base, fontName="Helvetica", fontSize=7.7, leading=9.5, textColor=CHARCOAL, wordWrap="CJK"),
            "cell_bold": ParagraphStyle("CellBold", parent=base, fontName="Helvetica-Bold", fontSize=7.7, leading=9.5, textColor=NAVY, wordWrap="CJK"),
            "table_header": ParagraphStyle("TableHeader", parent=base, fontName="Helvetica-Bold", fontSize=7.2, leading=8.5, textColor=colors.white, wordWrap="CJK"),
            "risk_score": ParagraphStyle("RiskScore", parent=base, fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=NAVY, alignment=TA_CENTER),
            "disclaimer": ParagraphStyle("Disclaimer", parent=base, fontName="Helvetica-Oblique", fontSize=7.3, leading=9.5, textColor=MUTED),
        }

    def _cover(self, analysis: EmailAnalysis, styles: dict[str, ParagraphStyle]) -> list[object]:
        score = f"{analysis.risk.score} / 100" if analysis.risk else "--"
        severity = analysis.risk.severity.value if analysis.risk else "UNKNOWN"
        header = Table([[ [Paragraph("SENTINEL MX", styles["eyebrow"]), Paragraph("Email Threat Investigation Report", styles["title"]), Spacer(1, 5), Paragraph("AI-Powered Email Threat Detection &amp; Forensic Intelligence", styles["subtitle"])], [Paragraph("CLASSIFICATION: INTERNAL SECURITY ANALYSIS", styles["subtitle"]), Spacer(1, 9), Paragraph(f"<b>Case ID</b><br/>{_safe(analysis.case_id)}", styles["subtitle"]), Paragraph(f"<b>Generated</b><br/>{_timestamp(datetime.now(timezone.utc))}", styles["subtitle"])]]], colWidths=[4.55 * inch, 2.9 * inch])
        header.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 18), ("RIGHTPADDING", (0, 0), (-1, -1), 18), ("TOPPADDING", (0, 0), (-1, -1), 16), ("BOTTOMPADDING", (0, 0), (-1, -1), 16)]))
        assessment = Table([[Paragraph("RISK ASSESSMENT", styles["eyebrow"]), Paragraph("CASE STATUS", styles["eyebrow"]), Paragraph("RISK SEVERITY", styles["eyebrow"])], [Paragraph(score, styles["risk_score"]), Paragraph(_safe(analysis.status.value), styles["risk_score"]), Paragraph(_safe(severity), styles["risk_score"])]], colWidths=[2.48 * inch, 2.48 * inch, 2.49 * inch])
        assessment.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PAPER), ("BOX", (0, 0), (-1, -1), 0.8, BORDER), ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
        return [header, Spacer(1, 12), assessment]

    def _section(self, number: int, title: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
        return Paragraph(f"{number}. {title}", styles["section"])

    def _executive_summary(self, analysis: EmailAnalysis, styles: dict[str, ParagraphStyle]) -> list[object]:
        parsed = analysis.parsed_email
        rows = [["Risk Score", f"{analysis.risk.score} / 100" if analysis.risk else "No deterministic risk available"], ["Severity", analysis.risk.severity.value if analysis.risk else "UNKNOWN"], ["Risk Authority", "Persisted deterministic risk engine result; AI interpretation cannot alter this value."], ["Case Status", analysis.status.value], ["Sender", parsed.sender.address if parsed and parsed.sender else None], ["Recipient", ", ".join(item.address for item in parsed.to) if parsed and parsed.to else None], ["Subject", parsed.subject if parsed else None], ["Analysis Timestamp", _timestamp(analysis.completed_at or analysis.created_at)]]
        result: list[object] = [self._section(1, "Executive Summary", styles), self._key_value_table(rows, styles)]
        if analysis.risk and analysis.risk.reasons:
            result.extend([Spacer(1, 7), Paragraph("KEY RISK FACTORS", styles["subsection"])])
            result.extend(Paragraph(f"&#8226; {_safe(reason.description)} (+{reason.points})", styles["body"]) for reason in analysis.risk.reasons[:8])
        return result

    def _email_overview(self, analysis: EmailAnalysis, styles: dict[str, ParagraphStyle]) -> list[object]:
        parsed = analysis.parsed_email
        if parsed is None:
            return []
        rows = [["From", parsed.sender.address if parsed.sender else None], ["Reply-To", ", ".join(item.address for item in parsed.reply_to) if parsed.reply_to else None], ["To", ", ".join(item.address for item in parsed.to) if parsed.to else None], ["Subject", parsed.subject], ["Message-ID", parsed.message_id], ["Date", _timestamp(parsed.sent_at)], ["Return-Path", (parsed.headers.get("return-path") or [None])[0]], ["Original Email SHA-256", parsed.original_sha256]]
        return [self._section(2, "Email Overview", styles), self._key_value_table(rows, styles)]

    def _authentication(self, analysis: EmailAnalysis, styles: dict[str, ParagraphStyle]) -> list[object]:
        auth = analysis.parsed_email.authentication if analysis.parsed_email else None
        if auth is None:
            return []
        return [self._section(3, "Authentication Analysis", styles), self._table(["Control", "Declared Result"], [["SPF", auth.spf.value], ["DKIM", auth.dkim.value], ["DMARC", auth.dmarc.value]], [2.2 * inch, 5.25 * inch], styles)]

    def _findings(self, analysis: EmailAnalysis, styles: dict[str, ParagraphStyle]) -> list[object]:
        findings = analysis.detection.findings if analysis.detection else ()
        if not findings:
            return []
        rows = [
            [
                item.title,
                item.severity.value,
                item.explanation,
                "\n".join(item.evidence[:3]) or "No evidence text",
            ]
            for item in findings
        ]
        return [self._section(4, "Deterministic Findings", styles), self._table(["Finding", "Severity", "Description", "Evidence"], rows, [1.35 * inch, 0.7 * inch, 2.55 * inch, 2.85 * inch], styles)]

    def _indicators(self, analysis: EmailAnalysis, styles: dict[str, ParagraphStyle]) -> list[object]:
        parsed = analysis.parsed_email
        if parsed is None:
            return []
        allowed = {"IP_ADDRESS", "DOMAIN", "URL", "ATTACHMENT_SHA256"}
        iocs = [ioc for ioc in parsed.iocs if ioc.type.value in allowed]
        if not iocs:
            return []
        findings = {(item.indicator_type.value, item.indicator): item for item in (analysis.threat_intel.findings if analysis.threat_intel else ())}
        rows = []
        for ioc in iocs:
            finding = findings.get((ioc.type.value, ioc.normalized_value))
            rows.append([ioc.type.value, ioc.normalized_value, finding.verdict.value if finding else "UNKNOWN", finding.provider if finding else "No persisted provider result"])
        return [self._section(5, "Indicators of Compromise", styles), self._table(["Type", "Indicator", "Verdict", "Provider"], rows, [1.2 * inch, 3.5 * inch, 1.0 * inch, 1.75 * inch], styles)]

    def _threat_intelligence(self, analysis: EmailAnalysis, styles: dict[str, ParagraphStyle]) -> list[object]:
        result = analysis.threat_intel
        if result is None:
            return []
        rows = [[item.indicator_type.value, item.indicator, item.provider, item.verdict.value, f"{item.confidence:.0%}" if item.confidence is not None else "Unknown"] for item in result.findings] or [["No persisted result", "", "", result.status.value, ""]]
        return [self._section(6, "Threat Intelligence", styles), Paragraph("Provider intelligence shown here was persisted during analysis; no provider was queried while rendering this report.", styles["body"]), Spacer(1, 5), self._table(["Type", "Indicator", "Provider", "Verdict", "Confidence"], rows, [1.0 * inch, 2.85 * inch, 1.2 * inch, 1.0 * inch, 1.4 * inch], styles)]

    def _infrastructure(self, analysis: EmailAnalysis, styles: dict[str, ParagraphStyle]) -> list[object]:
        parsed = analysis.parsed_email
        result: list[object] = [
            self._section(7, "Observed Mail-Routing Infrastructure", styles),
            Paragraph(
                "Observed infrastructure describes mail-routing systems and does not establish attacker identity or physical location.",
                styles["disclaimer"],
            ),
        ]
        if parsed and parsed.received_hops:
            routing_rows = [
                [
                    hop.position,
                    hop.from_host or "Unknown",
                    hop.by_host or "Unknown",
                    hop.source_ip or "No public IP extracted",
                    _timestamp(hop.timestamp),
                ]
                for hop in parsed.received_hops
            ]
            result.extend(
                [
                    Spacer(1, 5),
                    Paragraph("RECEIVED-HEADER OBSERVATIONS", styles["subsection"]),
                    self._table(
                        ["Order", "From Host", "By Host", "Observed IP", "Timestamp"],
                        routing_rows,
                        [0.45 * inch, 1.75 * inch, 1.75 * inch, 1.35 * inch, 2.15 * inch],
                        styles,
                    ),
                ]
            )
        if analysis.geolocations:
            rows = [
                [
                    geo.ip_address,
                    geo.city or "Unknown",
                    geo.region or "Unknown",
                    geo.country or "Unknown",
                    geo.asn or geo.network or "Unknown",
                    geo.organization or geo.isp or "Unknown",
                ]
                for geo in analysis.geolocations
            ]
            result.extend(
                [
                    Spacer(1, 7),
                    Paragraph("PERSISTED INFRASTRUCTURE GEOLOCATION", styles["subsection"]),
                    self._table(
                        ["IP", "City", "Region", "Country", "ASN / Network", "Organization"],
                        rows,
                        [1.1 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch, 1.3 * inch, 2.35 * inch],
                        styles,
                    ),
                ]
            )
        if not (parsed and parsed.received_hops) and not analysis.geolocations:
            result.extend([Spacer(1, 5), Paragraph("No routing or geolocation observations are available for this case.", styles["body"])])
        return result

    def _timeline(self, analysis: EmailAnalysis, styles: dict[str, ParagraphStyle]) -> list[object]:
        body: list[object] = [self._section(8, "Timeline and Evidence Events", styles)]
        if not analysis.timeline:
            return body + [Paragraph("No persisted timeline events are available for this case.", styles["body"])]
        rows = [
            [
                event.sequence,
                _timestamp(event.timestamp),
                event.event_type.value,
                event.title,
                event.source,
                ", ".join(event.evidence_refs) or "None",
            ]
            for event in analysis.timeline
        ]
        return body + [
            self._table(
                ["#", "Timestamp", "Event", "Description", "Source", "Evidence Refs"],
                rows,
                [0.35 * inch, 1.25 * inch, 1.0 * inch, 2.0 * inch, 1.05 * inch, 1.8 * inch],
                styles,
            )
        ]

    def _notes(self, notes: Sequence[AnalystNote], styles: dict[str, ParagraphStyle]) -> list[object]:
        heading = self._section(9, "Analyst Notes", styles)
        disclaimer = Paragraph(
            "Analyst commentary - not part of original forensic evidence.",
            styles["disclaimer"],
        )
        if not notes:
            return [
                KeepTogether(
                    [
                        heading,
                        disclaimer,
                        Spacer(1, 4),
                        Paragraph(
                            "No analyst notes have been added to this case.",
                            styles["body"],
                        ),
                    ]
                )
            ]

        cards: list[Table] = []
        for note in sorted(notes, key=lambda item: item.created_at):
            meta = f"<b>{_safe(note.author_display_name)}</b><br/>{_timestamp(note.created_at)}"
            if note.updated_at != note.created_at:
                meta += f"<br/>Updated {_timestamp(note.updated_at)}"
            card = Table([[Paragraph(meta, styles["cell_bold"]), Paragraph(_safe(note.content), styles["body"])]], colWidths=[1.55 * inch, 5.9 * inch])
            card.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F6F8")), ("BOX", (0, 0), (-1, -1), 0.6, BORDER), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
            cards.append(card)
        body: list[object] = [KeepTogether([heading, disclaimer, Spacer(1, 6), cards[0]])]
        for card in cards[1:]:
            body.extend([Spacer(1, 6), card])
        return body

    def _integrity(self, analysis: EmailAnalysis, styles: dict[str, ParagraphStyle]) -> list[object]:
        parsed = analysis.parsed_email
        rows: list[list[object]] = [
            ["Case ID", analysis.case_id],
            ["Case Status", analysis.status.value],
            ["Analysis Completeness", analysis.status.value],
            ["Analysis Timestamp", _timestamp(analysis.completed_at or analysis.created_at)],
            ["Original Email SHA-256", parsed.original_sha256 if parsed else None],
        ]
        if parsed:
            rows.extend(
                [
                    [
                        f"Attachment SHA-256 - {attachment.filename or 'Unnamed'}",
                        attachment.sha256,
                    ]
                    for attachment in parsed.attachments
                ]
            )
        body: list[object] = [
            self._section(10, "Evidence Integrity / Case Metadata", styles),
            self._key_value_table(rows, styles),
        ]
        if parsed and parsed.attachments:
            attachment_rows = [
                [
                    attachment.filename or "Unnamed attachment",
                    attachment.content_type,
                    attachment.content_disposition or "Unknown",
                    attachment.size_bytes,
                    attachment.sha256,
                ]
                for attachment in parsed.attachments
            ]
            body.extend(
                [
                    Spacer(1, 7),
                    Paragraph("ATTACHMENT EVIDENCE (NOT EXECUTED)", styles["subsection"]),
                    self._table(
                        ["Filename", "MIME Type", "Disposition", "Size (bytes)", "SHA-256"],
                        attachment_rows,
                        [1.35 * inch, 1.3 * inch, 1.0 * inch, 0.75 * inch, 3.05 * inch],
                        styles,
                    ),
                ]
            )
        return body

    def _limitations(self, analysis: EmailAnalysis, styles: dict[str, ParagraphStyle]) -> list[object]:
        body: list[object] = [self._section(11, "Warnings and Limitations", styles)]
        body.extend(Paragraph(f"&#8226; {_safe(value)}", styles["body"]) for value in (*analysis.warnings, *analysis.errors))
        return body

    def _key_value_table(self, rows: Iterable[Sequence[object]], styles: dict[str, ParagraphStyle]) -> Table:
        content = [[Paragraph(_safe(label), styles["cell_bold"]), Paragraph(_safe(value), styles["cell"])] for label, value in rows]
        table = Table(content, colWidths=[1.65 * inch, 5.8 * inch], hAlign="LEFT")
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF2F5")), ("GRID", (0, 0), (-1, -1), 0.35, BORDER), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        return table

    def _table(self, headers: Sequence[str], rows: Sequence[Sequence[object]], widths: Sequence[float], styles: dict[str, ParagraphStyle]) -> Table:
        content = [[Paragraph(_safe(header), styles["table_header"]) for header in headers]]
        content.extend([[Paragraph(_safe(value), styles["cell"]) for value in row] for row in rows])
        table = Table(content, colWidths=list(widths), repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.35, BORDER), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PAPER])]))
        return table
