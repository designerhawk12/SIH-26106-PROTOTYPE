"""Explicit synthetic observed-infrastructure provider for controlled demos."""

from ...schemas import GeoLocationResult, GeoLocationStatus

DEMO_GEOLOCATION_PROVIDER = "DEMO-SYNTHETIC (not live verified)"


class DemoInfrastructureGeoProvider:
    """Return clearly labelled synthetic infrastructure data without network access."""

    name = DEMO_GEOLOCATION_PROVIDER

    async def locate(self, ip_address: str) -> GeoLocationResult:
        return GeoLocationResult(
            ip_address=ip_address,
            status=GeoLocationStatus.FOUND,
            country="Demo Country",
            country_code="ZZ",
            region="Demo Region",
            city="Demo City",
            isp="Synthetic Demo Network",
            asn="AS0",
            organization="Synthetic data - not live verified",
            provider=self.name,
            observed_infrastructure_only=True,
        )
