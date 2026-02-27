"""Integration tests for rent (lease) workflow.

These tests validate the complete end-to-end workflow:
- Input validation
- API call (mocked)
- XML parsing
- Response formatting

Requirements:
- REQ-TEST-002: Integration tests for end-to-end workflow validation
"""

import pytest
import respx
from httpx import Response

from real_estate.mcp_server.tools.rent import (
    get_apartment_rent,
    get_officetel_rent,
    get_single_house_rent,
    get_villa_rent,
)

# ---------------------------------------------------------------------------
# Sample XML responses for integration tests
# ---------------------------------------------------------------------------

_APT_RENT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>000</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <aptNm>래미안푸르지오</aptNm>
        <umdNm>합정동</umdNm>
        <excluUseAr>84.97</excluUseAr>
        <floor>12</floor>
        <deposit>50,000</deposit>
        <monthlyRent>0</monthlyRent>
        <contractType>신규</contractType>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>10</dealDay>
        <buildYear>2014</buildYear>
        <cdealType></cdealType>
      </item>
      <item>
        <aptNm>마포자이</aptNm>
        <umdNm>아현동</umdNm>
        <excluUseAr>59.00</excluUseAr>
        <floor>5</floor>
        <deposit>20,000</deposit>
        <monthlyRent>80</monthlyRent>
        <contractType>신규</contractType>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>15</dealDay>
        <buildYear>2010</buildYear>
        <cdealType></cdealType>
      </item>
    </items>
    <totalCount>2</totalCount>
  </body>
</response>"""

_OFFICETEL_RENT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>000</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <offiNm>래미안오피스텔</offiNm>
        <umdNm>합정동</umdNm>
        <excluUseAr>42.5</excluUseAr>
        <floor>8</floor>
        <deposit>10,000</deposit>
        <monthlyRent>50</monthlyRent>
        <contractType>신규</contractType>
        <dealYear>2025</dealYear>
        <dealMonth>2</dealMonth>
        <dealDay>5</dealDay>
        <buildYear>2018</buildYear>
      </item>
    </items>
    <totalCount>1</totalCount>
  </body>
</response>"""

_VILLA_RENT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>000</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <mhouseNm>현대빌라</mhouseNm>
        <umdNm>연남동</umdNm>
        <houseType>다세대</houseType>
        <excluUseAr>65.0</excluUseAr>
        <floor>3</floor>
        <deposit>15,000</deposit>
        <monthlyRent>30</monthlyRent>
        <contractType>신규</contractType>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>20</dealDay>
        <buildYear>2005</buildYear>
      </item>
    </items>
    <totalCount>1</totalCount>
  </body>
</response>"""

_SINGLE_HOUSE_RENT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>000</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <umdNm>성수동</umdNm>
        <houseType>단독</houseType>
        <totalFloorAr>120.0</totalFloorAr>
        <deposit>80,000</deposit>
        <monthlyRent>0</monthlyRent>
        <contractType>신규</contractType>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>8</dealDay>
        <buildYear>1990</buildYear>
      </item>
    </items>
    <totalCount>1</totalCount>
  </body>
</response>"""

# API URLs
_APT_RENT_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"
_OFFI_RENT_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcOffiRent/getRTMSDataSvcOffiRent"
_VILLA_RENT_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcRHRent/getRTMSDataSvcRHRent"
_SINGLE_RENT_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcSHRent/getRTMSDataSvcSHRent"


class TestApartmentRentIntegration:
    """End-to-end integration tests for apartment rent workflow."""

    @pytest.fixture(autouse=True)
    def set_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Set a test API key environment variable."""
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-api-key")

    @respx.mock
    async def test_full_workflow_success(self) -> None:
        """Test complete workflow: request -> API -> parse -> response."""
        respx.get(_APT_RENT_URL).mock(return_value=Response(200, text=_APT_RENT_XML))

        result = await get_apartment_rent("11440", "202501")

        # Verify response structure
        assert "error" not in result
        assert result["total_count"] == 2
        assert len(result["items"]) == 2

        # Verify first item parsing (jeonse - 전세)
        item = result["items"][0]
        assert item["unit_name"] == "래미안푸르지오"
        assert item["dong"] == "합정동"
        assert item["area_sqm"] == 84.97
        assert item["floor"] == 12
        assert item["deposit_10k"] == 50000
        assert item["monthly_rent_10k"] == 0  # 전세 (no monthly rent)
        assert item["contract_type"] == "신규"
        assert item["trade_date"] == "2025-01-10"
        assert item["build_year"] == 2014

        # Verify second item parsing (wolse - 월세)
        item2 = result["items"][1]
        assert item2["monthly_rent_10k"] == 80

        # Verify summary calculation
        summary = result["summary"]
        assert summary["sample_count"] == 2
        assert summary["min_deposit_10k"] == 20000
        assert summary["max_deposit_10k"] == 50000
        assert summary["median_deposit_10k"] == 35000
        assert summary["monthly_rent_avg_10k"] == 40  # (0 + 80) / 2
        assert summary["jeonse_ratio_pct"] is None

    @respx.mock
    async def test_workflow_with_pagination(self) -> None:
        """Test workflow with custom pagination parameters."""
        respx.get(_APT_RENT_URL).mock(return_value=Response(200, text=_APT_RENT_XML))

        result = await get_apartment_rent("11440", "202501", num_of_rows=50)

        assert "error" not in result
        assert result["total_count"] == 2


class TestOfficetelRentIntegration:
    """End-to-end integration tests for officetel rent workflow."""

    @pytest.fixture(autouse=True)
    def set_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Set a test API key environment variable."""
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-api-key")

    @respx.mock
    async def test_full_workflow_success(self) -> None:
        """Test complete officetel rent workflow."""
        respx.get(_OFFI_RENT_URL).mock(
            return_value=Response(200, text=_OFFICETEL_RENT_XML)
        )

        result = await get_officetel_rent("11440", "202502")

        assert "error" not in result
        assert result["total_count"] == 1
        assert len(result["items"]) == 1

        item = result["items"][0]
        assert item["unit_name"] == "래미안오피스텔"
        assert item["dong"] == "합정동"
        assert item["area_sqm"] == 42.5
        assert item["floor"] == 8
        assert item["deposit_10k"] == 10000
        assert item["monthly_rent_10k"] == 50
        assert item["contract_type"] == "신규"
        assert item["trade_date"] == "2025-02-05"
        assert item["build_year"] == 2018


class TestVillaRentIntegration:
    """End-to-end integration tests for villa (row-house/multi-family) rent workflow."""

    @pytest.fixture(autouse=True)
    def set_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Set a test API key environment variable."""
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-api-key")

    @respx.mock
    async def test_full_workflow_success(self) -> None:
        """Test complete villa rent workflow."""
        respx.get(_VILLA_RENT_URL).mock(return_value=Response(200, text=_VILLA_RENT_XML))

        result = await get_villa_rent("11440", "202501")

        assert "error" not in result
        assert result["total_count"] == 1
        assert len(result["items"]) == 1

        item = result["items"][0]
        assert item["unit_name"] == "현대빌라"
        assert item["dong"] == "연남동"
        assert item["house_type"] == "다세대"
        assert item["area_sqm"] == 65.0
        assert item["floor"] == 3
        assert item["deposit_10k"] == 15000
        assert item["monthly_rent_10k"] == 30
        assert item["contract_type"] == "신규"
        assert item["trade_date"] == "2025-01-20"
        assert item["build_year"] == 2005


class TestSingleHouseRentIntegration:
    """End-to-end integration tests for single/detached house rent workflow."""

    @pytest.fixture(autouse=True)
    def set_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Set a test API key environment variable."""
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-api-key")

    @respx.mock
    async def test_full_workflow_success(self) -> None:
        """Test complete single house rent workflow."""
        respx.get(_SINGLE_RENT_URL).mock(
            return_value=Response(200, text=_SINGLE_HOUSE_RENT_XML)
        )

        result = await get_single_house_rent("11440", "202501")

        assert "error" not in result
        assert result["total_count"] == 1
        assert len(result["items"]) == 1

        item = result["items"][0]
        assert item["unit_name"] == ""  # Not provided by API
        assert item["dong"] == "성수동"
        assert item["house_type"] == "단독"
        assert item["area_sqm"] == 120.0
        assert item["deposit_10k"] == 80000
        assert item["monthly_rent_10k"] == 0  # 전세
        assert item["contract_type"] == "신규"
        assert item["trade_date"] == "2025-01-08"
        assert item["build_year"] == 1990


class TestRentWorkflowErrorHandling:
    """Integration tests for error handling in rent workflows."""

    @pytest.fixture(autouse=True)
    def set_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Set a test API key environment variable."""
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-api-key")

    async def test_missing_api_key_returns_config_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing API key returns config_error."""
        monkeypatch.delenv("DATA_GO_KR_API_KEY", raising=False)

        result = await get_apartment_rent("11440", "202501")

        assert result["error"] == "config_error"

    @respx.mock
    async def test_timeout_returns_network_error(self) -> None:
        """Network timeout returns network_error."""
        import httpx

        respx.get(_APT_RENT_URL).mock(side_effect=httpx.TimeoutException("timeout"))

        result = await get_apartment_rent("11440", "202501")

        assert result["error"] == "network_error"

