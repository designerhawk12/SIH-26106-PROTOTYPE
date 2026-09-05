"""Geolocator reads persisted evidence and cannot initiate enrichment."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from backend.app.api.dependencies import get_case_repository
from backend.app.core import Settings
from backend.app.db import (
    SqlAlchemyCaseRepository, create_database_engine, create_session_factory,
    initialize_database,
)
from backend.app.schemas import (
    AnalysisStatus, EmailAnalysis, EnrichmentStatus, GeoLocationResult,
    GeoLocationStatus, IOCType, ParsedEmail, ReceivedHop, ReputationVerdict,
    RiskLevel, RiskResult, ThreatFinding, ThreatIntelResult,
)
from backend.app.services.orchestrator.infrastructure import (
    _mappable, aggregate_persisted_infrastructure,
)
from backend.main import create_app
from backend.tests.auth_helpers import AUTH_HEADERS, FakeIdentityVerifier

NOW = datetime(2026, 9, 5, tzinfo=timezone.utc)


def location(ip="8.8.8.8", **kwargs):
    return GeoLocationResult(
        ip_address=ip, **{
            "status": GeoLocationStatus.FOUND, "latitude": 37.4,
            "longitude": -122.1, "provider": "ipwho.is", "country": "United States",
            "city": "Mountain View", "asn": "AS15169", "organization": "Example network",
            **kwargs,
        },
    )


def analysis(number=1, *, locations=(), ips=(), hops=(), findings=()):
    return EmailAnalysis(
        case_id=UUID(int=number), status=AnalysisStatus.PARTIAL,
        created_at=NOW + timedelta(days=number),
        parsed_email=ParsedEmail(
            original_sha256="a" * 64, subject="Persisted evidence",
            originating_public_ips=ips, received_hops=hops,
        ),
        geolocations=locations,
        threat_intel=ThreatIntelResult(status=EnrichmentStatus.UNAVAILABLE, findings=findings),
        risk=RiskResult(score=6, severity=RiskLevel.LOW, formula_version="test"),
    )


def test_infrastructure_preserves_multiple_cases_and_provider_observations():
    result = aggregate_persisted_infrastructure((
        analysis(locations=(location(),)),
        analysis(2, locations=(location(latitude=51.5, longitude=-0.1,
                                        provider="DEMO-SYNTHETIC (not live verified)"),)),
    ))
    assert result.cases_scanned == 2
    first, second = result.observations
    assert first.ip_address == second.ip_address
    assert first.case.case_id != second.case.case_id
    assert first.location.latitude == 37.4
    assert second.location.latitude == 51.5
    assert first.location.asn == "AS15169"
    assert first.case.status is AnalysisStatus.PARTIAL
    assert first.case.risk_severity is RiskLevel.LOW
    assert first.verdict is ReputationVerdict.UNKNOWN
    assert first.threat_intel_status is EnrichmentStatus.UNAVAILABLE
    assert not first.demo and second.demo
    assert "does not establish" in result.disclaimer


@pytest.mark.parametrize("ip", ["10.0.0.1", "127.0.0.1", "169.254.1.1", "224.0.0.1",
    "192.0.2.1", "100.64.0.1", "240.0.0.1", "::1", "fe80::1", "fc00::1", "ff02::1",
    "2001:db8::1", "bad-ip", "8.8.8.8%eth0"])
def test_infrastructure_excludes_invalid_nonpublic_ips_even_if_persisted(ip):
    result = aggregate_persisted_infrastructure((analysis(locations=(location(ip),), ips=(ip,)),))
    assert result.observations == ()


def test_infrastructure_public_ipv6_normalized_and_reputation_preserved():
    ip = "2606:4700:4700::1111"
    result = aggregate_persisted_infrastructure((analysis(
        locations=(location(ip),), ips=("2606:4700:4700:0:0:0:0:1111",),
        findings=(ThreatFinding(indicator_type=IOCType.IP_ADDRESS, indicator=ip,
            provider="AbuseIPDB", verdict=ReputationVerdict.SUSPICIOUS),),
    ),))
    assert len(result.observations) == 1
    assert result.observations[0].verdict is ReputationVerdict.SUSPICIOUS
    assert result.observations[0].threat_providers == ("AbuseIPDB",)


@pytest.mark.parametrize("changes", [
    {"latitude": None}, {"longitude": None}, {"latitude": 0.0, "longitude": 0.0},
    {"status": GeoLocationStatus.PROVIDER_ERROR}, {"status": GeoLocationStatus.NOT_FOUND},
])
def test_infrastructure_missing_coordinates_never_mappable(changes):
    record = aggregate_persisted_infrastructure((analysis(locations=(location(**changes),)),)).observations[0]
    assert not _mappable(record)
    assert record.location == location(**changes)


def test_infrastructure_empty_and_absent_geolocation_stays_missing():
    assert aggregate_persisted_infrastructure(()).observations == ()
    result = aggregate_persisted_infrastructure((analysis(ips=("8.8.8.8",)),))
    assert result.observations[0].location is None
    assert not _mappable(result.observations[0])


def hop(position, ip):
    return ReceivedHop(position=position, raw_header="Synthetic routing evidence",
        source_ip=ip, timestamp=NOW - timedelta(minutes=position))


def test_infrastructure_routes_use_adjacent_chronological_persisted_hops_only():
    locations = (location("8.8.8.8"), location("1.1.1.1"), location("9.9.9.9"))
    hops = (hop(0, "8.8.8.8"), hop(1, "1.1.1.1"), hop(2, "9.9.9.9"))
    result = aggregate_persisted_infrastructure((analysis(locations=locations, hops=hops),))
    assert len(result.route_segments) == 2
    assert all(segment.from_timestamp <= segment.to_timestamp for segment in result.route_segments)
    gap = aggregate_persisted_infrastructure((analysis(locations=(locations[0], locations[2]), hops=hops),))
    assert gap.route_segments == ()
    unknown_time = hops[1].model_copy(update={"timestamp": None})
    assert aggregate_persisted_infrastructure((analysis(locations=locations,
        hops=(hops[0], unknown_time, hops[2])),)).route_segments == ()
    reverse_time = hops[1].model_copy(update={"timestamp": NOW + timedelta(days=1)})
    result = aggregate_persisted_infrastructure((analysis(locations=locations,
        hops=(hops[0], reverse_time)),))
    assert result.route_segments == ()


def test_infrastructure_authenticated_reads_repeat_without_provider_calls(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Infrastructure viewing must never construct analysis providers")
    monkeypatch.setattr("backend.app.api.dependencies.build_default_analysis_orchestrator", forbidden)
    engine = create_database_engine("sqlite://")
    initialize_database(engine)
    with create_session_factory(engine)() as session:
        repository = SqlAlchemyCaseRepository(session)
        repository.create(analysis(locations=(location(),)))
        repository.create(analysis(2, ips=("1.1.1.1",)))
    app = create_app(settings=Settings(database_url="sqlite://"), database_engine=engine,
                     identity_verifier=FakeIdentityVerifier())
    with TestClient(app) as client:
        assert client.get("/api/v1/infrastructure").status_code == 401
        assert client.get("/api/v1/infrastructure", headers={"Authorization": "Bearer invalid"}).status_code == 401
        responses = [client.get("/api/v1/infrastructure", headers=AUTH_HEADERS) for _ in range(3)]
        assert all(response.status_code == 200 for response in responses)
        assert responses[0].json() == responses[1].json() == responses[2].json()
        assert len(responses[0].json()["observations"]) == 2
        assert responses[0].json()["observations"][1]["location"]["city"] == "Mountain View"


def test_infrastructure_database_failure_is_controlled():
    class FailedRepository:
        def list_analyses(self):
            raise RuntimeError("private database exception")
    app = create_app(settings=Settings(database_url="sqlite://"), identity_verifier=FakeIdentityVerifier())
    app.dependency_overrides[get_case_repository] = lambda: FailedRepository()
    with TestClient(app, headers=AUTH_HEADERS) as client:
        response = client.get("/api/v1/infrastructure")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert "private database exception" not in response.text
