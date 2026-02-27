"""Integration tests for trade (sale) workflow.

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

from real_estate.mcp_server.tools.trade import (
    get_apartment_trades,
    get_commercial_trade,
    get_officetel_trades,
    get_single_house_trades,
    get_villa_trades,
)

# ---------------------------------------------------------------------------
# Sample XML responses for integration tests
# ---------------------------------------------------------------------------

_APT_TRADE_XML = """<?xml version="1.0" encoding="UTF-8"?>
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
        <dealAmount>135,000</dealAmount>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>15</dealDay>
        <buildYear>2014</buildYear>
        <dealingGbn>중개거래</dealingGbn>
        <cdealType></cdealType>
      </item>
      <item>
        <aptNm>마포자이</aptNm>
        <umdNm>아현동</umdNm>
        <excluUseAr>59.00</excluUseAr>
        <floor>5</floor>
        <dealAmount>90,000</dealAmount>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>20</dealDay>
        <buildYear>2010</buildYear>
        <dealingGbn>직거래</dealingGbn>
        <cdealType></cdealType>
      </item>
    </items>
    <totalCount>2</totalCount>
  </body>
</response>"""

_OFFICETEL_TRADE_XML = """<?xml version="1.0" encoding="UTF-8"?>
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
        <dealAmount>35,000</dealAmount>
        <dealYear>2025</dealYear>
        <dealMonth>2</dealMonth>
        <dealDay>10</dealDay>
        <buildYear>2018</buildYear>
        <dealingGbn>중개거래</dealingGbn>
        <cdealType></cdealType>
      </item>
    </items>
    <totalCount>1</totalCount>
  </body>
</response>"""

_VILLA_TRADE_XML = """<?xml version="1.0" encoding="UTF-8"?>
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
        <dealAmount>55,000</dealAmount>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>5</dealDay>
        <buildYear>2005</buildYear>
        <dealingGbn>직거래</dealingGbn>
        <cdealType></cdealType>
      </item>
    </items>
    <totalCount>1</totalCount>
  </body>
</response>"""

_SINGLE_HOUSE_TRADE_XML = """<?xml version="1.0" encoding="UTF-8"?>
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
        <dealAmount>180,000</dealAmount>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>25</dealDay>
        <buildYear>1990</buildYear>
        <dealingGbn>중개거래</dealingGbn>
        <cdealType></cdealType>
      </item>
    </items>
    <totalCount>1</totalCount>
  </body>
</response>"""

_COMMERCIAL_TRADE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>000</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <buildingType>근린생활시설</buildingType>
        <buildingUse>상가</buildingUse>
        <landUse>상업지역</landUse>
        <umdNm>역삼동</umdNm>
        <buildingAr>150.0</buildingAr>
        <floor>1</floor>
        <dealAmount>500,000</dealAmount>
        <dealYear>2025</dealYear>
        <dealMonth>2</dealMonth>
        <dealDay>1</dealDay>
        <buildYear>2015</buildYear>
        <dealingGbn>중개거래</dealingGbn>
        <cdealtype></cdealtype>
        <shareDealingType></shareDealingType>
      </item>
    </items>
    <totalCount>1</totalCount>
  </body>
</response>"""

# API URLs
_APT_TRADE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
_OFFI_TRADE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcOffiTrade/getRTMSDataSvcOffiTrade"
_VILLA_TRADE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcRHTrade/getRTMSDataSvcRHTrade"
_SINGLE_TRADE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcSHTrade/getRTMSDataSvcSHTrade"
_COMMERCIAL_TRADE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcNrgTrade/getRTMSDataSvcNrgTrade"


class TestApartmentTradeIntegration:
    """End-to-end integration tests for apartment trade workflow."""

    @pytest.fixture(autouse=True)
    def set_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Set a test API key environment variable."""
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-api-key")

    @respx.mock
    async def test_full_workflow_success(self) -> None:
        """Test complete workflow: request -> API -> parse -> response."""
        respx.get(_APT_TRADE_URL).mock(return_value=Response(200, text=_APT_TRADE_XML))

        result = await get_apartment_trades("11440", "202501")

        # Verify response structure
        assert "error" not in result
        assert result["total_count"] == 2
        assert len(result["items"]) == 2

        # Verify first item parsing
        item = result["items"][0]
        assert item["apt_name"] == "래미안푸르지오"
        assert item["dong"] == "합정동"
        assert item["area_sqm"] == 84.97
        assert item["floor"] == 12
        assert item["price_10k"] == 135000
        assert item["trade_date"] == "2025-01-15"
        assert item["build_year"] == 2014
        assert item["deal_type"] == "중개거래"

        # Verify summary calculation
        summary = result["summary"]
        assert summary["sample_count"] == 2
        assert summary["min_price_10k"] == 90000
        assert summary["max_price_10k"] == 135000
        assert summary["median_price_10k"] == 112500

    @respx.mock
    async def test_workflow_with_pagination(self) -> None:
        """Test workflow with custom pagination parameters."""
        respx.get(_APT_TRADE_URL).mock(return_value=Response(200, text=_APT_TRADE_XML))

        result = await get_apartment_trades("11440", "202501", num_of_rows=50)

        assert "error" not in result
        assert result["total_count"] == 2


class TestOfficetelTradeIntegration:
    """End-to-end integration tests for officetel trade workflow."""

    @pytest.fixture(autouse=True)
    def set_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Set a test API key environment variable."""
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-api-key")

    @respx.mock
    async def test_full_workflow_success(self) -> None:
        """Test complete officetel trade workflow."""
        respx.get(_OFFI_TRADE_URL).mock(
            return_value=Response(200, text=_OFFICETEL_TRADE_XML)
        )

        result = await get_officetel_trades("11440", "202502")

        assert "error" not in result
        assert result["total_count"] == 1
        assert len(result["items"]) == 1

        item = result["items"][0]
        assert item["unit_name"] == "래미안오피스텔"
        assert item["dong"] == "합정동"
        assert item["area_sqm"] == 42.5
        assert item["floor"] == 8
        assert item["price_10k"] == 35000
        assert item["trade_date"] == "2025-02-10"
        assert item["build_year"] == 2018


class TestVillaTradeIntegration:
    """End-to-end integration tests for villa (row-house/multi-family) trade workflow."""

    @pytest.fixture(autouse=True)
    def set_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Set a test API key environment variable."""
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-api-key")

    @respx.mock
    async def test_full_workflow_success(self) -> None:
        """Test complete villa trade workflow."""
        respx.get(_VILLA_TRADE_URL).mock(
            return_value=Response(200, text=_VILLA_TRADE_XML)
        )

        result = await get_villa_trades("11440", "202501")

        assert "error" not in result
        assert result["total_count"] == 1
        assert len(result["items"]) == 1

        item = result["items"][0]
        assert item["unit_name"] == "현대빌라"
        assert item["dong"] == "연남동"
        assert item["house_type"] == "다세대"
        assert item["area_sqm"] == 65.0
        assert item["floor"] == 3
        assert item["price_10k"] == 55000
        assert item["trade_date"] == "2025-01-05"
        assert item["build_year"] == 2005


class TestSingleHouseTradeIntegration:
    """End-to-end integration tests for single/detached house trade workflow."""

    @pytest.fixture(autouse=True)
    def set_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Set a test API key environment variable."""
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-api-key")

    @respx.mock
    async def test_full_workflow_success(self) -> None:
        """Test complete single house trade workflow."""
        respx.get(_SINGLE_TRADE_URL).mock(
            return_value=Response(200, text=_SINGLE_HOUSE_TRADE_XML)
        )

        result = await get_single_house_trades("11440", "202501")

        assert "error" not in result
        assert result["total_count"] == 1
        assert len(result["items"]) == 1

        item = result["items"][0]
        assert item["unit_name"] == ""  # Not provided by API
        assert item["dong"] == "성수동"
        assert item["house_type"] == "단독"
        assert item["area_sqm"] == 120.0
        assert item["floor"] == 0  # Not applicable for detached houses
        assert item["price_10k"] == 180000
        assert item["trade_date"] == "2025-01-25"
        assert item["build_year"] == 1990


class TestCommercialTradeIntegration:
    """End-to-end integration tests for commercial building trade workflow."""

    @pytest.fixture(autouse=True)
    def set_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Set a test API key environment variable."""
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-api-key")

    @respx.mock
    async def test_full_workflow_success(self) -> None:
        """Test complete commercial trade workflow."""
        respx.get(_COMMERCIAL_TRADE_URL).mock(
            return_value=Response(200, text=_COMMERCIAL_TRADE_XML)
        )

        result = await get_commercial_trade("11650", "202502")

        assert "error" not in result
        assert result["total_count"] == 1
        assert len(result["items"]) == 1

        item = result["items"][0]
        assert item["building_type"] == "근린생활시설"
        assert item["building_use"] == "상가"
        assert item["land_use"] == "상업지역"
        assert item["dong"] == "역삼동"
        assert item["building_ar"] == 150.0
        assert item["floor"] == 1
        assert item["price_10k"] == 500000
        assert item["trade_date"] == "2025-02-01"
        assert item["build_year"] == 2015


class TestTradeWorkflowErrorHandling:
    """Integration tests for error handling in trade workflows."""

    @pytest.fixture(autouse=True)
    def set_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Set a test API key environment variable."""
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-api-key")

    async def test_missing_api_key_returns_config_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing API key returns config_error."""
        monkeypatch.delenv("DATA_GO_KR_API_KEY", raising=False)

        result = await get_apartment_trades("11440", "202501")

        assert result["error"] == "config_error"

    @respx.mock
    async def test_timeout_returns_network_error(self) -> None:
        """Network timeout returns network_error."""
        import httpx

        respx.get(_APT_TRADE_URL).mock(side_effect=httpx.TimeoutException("timeout"))

        result = await get_apartment_trades("11440", "202501")

        assert result["error"] == "network_error"

