"""ZIP-based evidence export implementation."""

import io
import json
import zipfile
from datetime import datetime, timezone

from .interfaces import EvidenceExportService
from ...schemas import EmailAnalysis


class ZipEvidenceExportService(EvidenceExportService):
    """Generates a ZIP archive containing structured evidence derived from EmailAnalysis."""

    async def export_case(self, analysis: EmailAnalysis) -> bytes:
        buffer = io.BytesIO()
        
        # Use ZIP_DEFLATED for compression
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            
            # 1. analysis.json (Full payload)
            analysis_data = analysis.model_dump(mode="json")
            zf.writestr("analysis.json", json.dumps(analysis_data, indent=2))
            
            # 2. Extract specific segments for ease of investigation
            if analysis.parsed_email:
                if analysis.parsed_email.authentication:
                    auth_data = analysis.parsed_email.authentication.model_dump(mode="json")
                    zf.writestr("authentication.json", json.dumps(auth_data, indent=2))
                
                if analysis.parsed_email.iocs:
                    ioc_data = [ioc.model_dump(mode="json") for ioc in analysis.parsed_email.iocs]
                    zf.writestr("iocs.json", json.dumps(ioc_data, indent=2))
                
                if analysis.parsed_email.attachments:
                    att_data = [att.model_dump(mode="json") for att in analysis.parsed_email.attachments]
                    zf.writestr("attachments.json", json.dumps(att_data, indent=2))
            
            if analysis.threat_intel and analysis.threat_intel.findings:
                ti_data = [f.model_dump(mode="json") for f in analysis.threat_intel.findings]
                zf.writestr("threat-intel.json", json.dumps(ti_data, indent=2))
            
            if analysis.geolocations:
                geo_data = [g.model_dump(mode="json") for g in analysis.geolocations]
                zf.writestr("geolocation.json", json.dumps(geo_data, indent=2))
                
            if analysis.timeline:
                time_data = [t.model_dump(mode="json") for t in analysis.timeline]
                zf.writestr("timeline.json", json.dumps(time_data, indent=2))
                
            # 3. Hashes
            hashes_lines = []
            if analysis.parsed_email:
                hashes_lines.append(f"Original Email SHA-256: {analysis.parsed_email.original_sha256}")
                
                if analysis.parsed_email.attachments:
                    hashes_lines.append("\nAttachment hashes:")
                    for att in analysis.parsed_email.attachments:
                        name = att.filename or att.attachment_id
                        hashes_lines.append(f"{name}  {att.sha256}")
                        
            if hashes_lines:
                zf.writestr("hashes.txt", "\n".join(hashes_lines) + "\n")
                
            # 4. Manifest
            manifest = {
                "title": "Forensic Evidence Export",
                "disclaimer": "Evidence collected and derived by the Sentinel MX analysis platform.",
                "case_id": str(analysis.case_id),
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "schema_version": analysis.schema_version,
                "analysis_status": analysis.status.value,
                "original_filename": analysis.original_filename,
                "original_email_stored": False,
                "notes": [
                    "Original raw email bytes (.eml) are not persisted in the database by design, and are therefore omitted from this export."
                ],
                "files_included": zf.namelist(),
            }
            
            # Record missing optional evidence
            missing = []
            if not analysis.threat_intel or not analysis.threat_intel.findings:
                missing.append("threat-intel.json")
            if not analysis.geolocations:
                missing.append("geolocation.json")
            if not analysis.parsed_email or not analysis.parsed_email.attachments:
                missing.append("attachments.json")
                
            if missing:
                manifest["files_unavailable"] = missing
                
            if analysis.parsed_email:
                manifest["original_email_sha256"] = analysis.parsed_email.original_sha256

            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            
        return buffer.getvalue()
