"""get_apartment_trades 도구 단위 테스트.

httpx 호출은 respx로 mock 처리하여 실제 API를 호출하지 않는다.
"""

import pytest
import respx
from httpx import Response

from real_estate.mcp_server.server import (
    _build_summary,
    _parse_trades,
    get_apartment_trades,
)

# ---------------------------------------------------------------------------
# 테스트 픽스처: XML 응답 샘플
# ---------------------------------------------------------------------------

_XML_OK = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>000</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <aptNm>마포래미안푸르지오</aptNm>
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
      <item>
        <aptNm>취소단지</aptNm>
        <umdNm>공덕동</umdNm>
        <excluUseAr>84.00</excluUseAr>
        <floor>3</floor>
        <dealAmount>100,000</dealAmount>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>10</dealDay>
        <buildYear>2015</buildYear>
        <dealingGbn>중개거래</dealingGbn>
        <cdealType>O</cdealType>
      </item>
    </items>
    <totalCount>2</totalCount>
  </body>
</response>"""

_XML_NO_DATA = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>03</resultCode>
    <resultMsg>No Data</resultMsg>
  </header>
  <body>
    <items/>
    <totalCount>0</totalCount>
  </body>
</response>"""

_API_URL = (
    "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
)


# ---------------------------------------------------------------------------
# _parse_trades 단위 테스트
# ---------------------------------------------------------------------------


class TestParseTrades:
    """XML 파싱 로직 단위 테스트."""

    def test_normal_response_returns_items(self) -> None:
        """정상 XML에서 해제 건 제외 후 2건 반환."""
        items, error_code = _parse_trades(_XML_OK)
        assert error_code is None
        assert len(items) == 2  # 해제 건(cdealType=O) 제외

    def test_deal_amount_comma_removed(self) -> None:
        """dealAmount 콤마가 제거되어 int로 변환."""
        items, _ = _parse_trades(_XML_OK)
        assert items[0]["price_10k"] == 135000

    def test_trade_date_formatted(self) -> None:
        """날짜가 YYYY-MM-DD 형식으로 조합."""
        items, _ = _parse_trades(_XML_OK)
        assert items[0]["trade_date"] == "2025-01-15"

    def test_cancelled_deal_excluded(self) -> None:
        """cdealType=O 건은 결과에 포함되지 않음."""
        items, _ = _parse_trades(_XML_OK)
        names = [it["apt_name"] for it in items]
        assert "취소단지" not in names

    def test_error_code_returned_on_no_data(self) -> None:
        """resultCode가 000이 아니면 error_code 반환."""
        items, error_code = _parse_trades(_XML_NO_DATA)
        assert error_code == "03"
        assert items == []


# ---------------------------------------------------------------------------
# _build_summary 단위 테스트
# ---------------------------------------------------------------------------


class TestBuildSummary:
    """통계 요약 계산 단위 테스트."""

    def test_summary_values(self) -> None:
        """중앙값·최소·최대·건수 정확히 계산."""
        items = [{"price_10k": 90000}, {"price_10k": 135000}]
        summary = _build_summary(items)
        assert summary["median_price_10k"] == 112500
        assert summary["min_price_10k"] == 90000
        assert summary["max_price_10k"] == 135000
        assert summary["sample_count"] == 2

    def test_empty_items_returns_zeros(self) -> None:
        """빈 목록이면 모든 값 0."""
        summary = _build_summary([])
        assert summary["sample_count"] == 0
        assert summary["median_price_10k"] == 0


# ---------------------------------------------------------------------------
# get_apartment_trades 통합 테스트 (respx mock)
# ---------------------------------------------------------------------------


class TestGetApartmentTrades:
    """get_apartment_trades 도구 통합 테스트."""

    @pytest.fixture(autouse=True)
    def set_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """테스트용 API 키 환경변수 설정."""
        monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-key")

    @respx.mock
    async def test_success_returns_items_and_summary(self) -> None:
        """정상 응답 시 items + summary 반환."""
        respx.get(_API_URL).mock(return_value=Response(200, text=_XML_OK))

        result = await get_apartment_trades("11440", "202501")

        assert "error" not in result
        assert result["total_count"] == 2
        assert len(result["items"]) == 2
        assert result["summary"]["sample_count"] == 2

    @respx.mock
    async def test_no_data_returns_api_error(self) -> None:
        """데이터 없음(코드 03) 시 error dict 반환."""
        respx.get(_API_URL).mock(return_value=Response(200, text=_XML_NO_DATA))

        result = await get_apartment_trades("11440", "200001")

        assert result["error"] == "api_error"
        assert result["code"] == "03"

    @respx.mock
    async def test_timeout_returns_network_error(self) -> None:
        """타임아웃 시 network_error 반환."""
        import httpx as _httpx

        respx.get(_API_URL).mock(side_effect=_httpx.TimeoutException("timeout"))

        result = await get_apartment_trades("11440", "202501")

        assert result["error"] == "network_error"

    async def test_missing_api_key_returns_config_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """API 키 미설정 시 config_error 반환."""
        monkeypatch.delenv("DATA_GO_KR_API_KEY", raising=False)

        result = await get_apartment_trades("11440", "202501")

        assert result["error"] == "config_error"
