"""Unit tests for trade XML parsers.

These tests validate the XML parsing logic for trade (sale) API responses.

Requirements:
- REQ-TEST-003: Parser tests for XML parsing validation
"""

import pytest

from real_estate.mcp_server.parsers.trade import (
    _parse_apt_trades,
    _parse_commercial_trade,
    _parse_officetel_trades,
    _parse_single_house_trades,
    _parse_villa_trades,
)


class TestParseAptTrades:
    """Unit tests for apartment trade XML parsing."""

    def test_normal_response_returns_items(self) -> None:
        """Normal XML returns items correctly parsed."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>000</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <aptNm>테스트아파트</aptNm>
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
    </items>
    <totalCount>1</totalCount>
  </body>
</response>"""
        items, error_code = _parse_apt_trades(xml_text)
        assert error_code is None
        assert len(items) == 1
        assert items[0]["apt_name"] == "테스트아파트"
        assert items[0]["dong"] == "합정동"
        assert items[0]["area_sqm"] == 84.97
        assert items[0]["floor"] == 12
        assert items[0]["price_10k"] == 135000
        assert items[0]["trade_date"] == "2025-01-15"
        assert items[0]["build_year"] == 2014
        assert items[0]["deal_type"] == "중개거래"

    def test_cancelled_deal_excluded(self) -> None:
        """Items with cdealType=O are excluded."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>000</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <aptNm>정상거래</aptNm>
        <umdNm>합정동</umdNm>
        <excluUseAr>84.0</excluUseAr>
        <floor>10</floor>
        <dealAmount>100,000</dealAmount>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>10</dealDay>
        <buildYear>2010</buildYear>
        <dealingGbn>중개거래</dealingGbn>
        <cdealType></cdealType>
      </item>
      <item>
        <aptNm>취소거래</aptNm>
        <umdNm>공덕동</umdNm>
        <excluUseAr>84.0</excluUseAr>
        <floor>5</floor>
        <dealAmount>90,000</dealAmount>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>5</dealDay>
        <buildYear>2015</buildYear>
        <dealingGbn>중개거래</dealingGbn>
        <cdealType>O</cdealType>
      </item>
    </items>
    <totalCount>2</totalCount>
  </body>
</response>"""
        items, _ = _parse_apt_trades(xml_text)
        assert len(items) == 1
        assert items[0]["apt_name"] == "정상거래"

    def test_missing_price_excluded(self) -> None:
        """Items with missing or invalid dealAmount are excluded."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>000</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <aptNm>가격있음</aptNm>
        <umdNm>합정동</umdNm>
        <excluUseAr>84.0</excluUseAr>
        <floor>10</floor>
        <dealAmount>100,000</dealAmount>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>10</dealDay>
        <buildYear>2010</buildYear>
        <dealingGbn>중개거래</dealingGbn>
        <cdealType></cdealType>
      </item>
      <item>
        <aptNm>가격없음</aptNm>
        <umdNm>공덕동</umdNm>
        <excluUseAr>84.0</excluUseAr>
        <floor>5</floor>
        <dealAmount></dealAmount>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>5</dealDay>
        <buildYear>2015</buildYear>
        <dealingGbn>중개거래</dealingGbn>
        <cdealType></cdealType>
      </item>
    </items>
    <totalCount>2</totalCount>
  </body>
</response>"""
        items, _ = _parse_apt_trades(xml_text)
        assert len(items) == 1
        assert items[0]["apt_name"] == "가격있음"

    def test_error_code_returned_on_api_error(self) -> None:
        """Non-000 resultCode returns error code."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
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
        items, error_code = _parse_apt_trades(xml_text)
        assert error_code == "03"
        assert items == []

    def test_date_formatting_with_single_digit_month_day(self) -> None:
        """Month and day are zero-padded in date."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>000</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <aptNm>테스트</aptNm>
        <umdNm>합정동</umdNm>
        <excluUseAr>84.0</excluUseAr>
        <floor>10</floor>
        <dealAmount>100,000</dealAmount>
        <dealYear>2025</dealYear>
        <dealMonth>3</dealMonth>
        <dealDay>5</dealDay>
        <buildYear>2010</buildYear>
        <dealingGbn>중개거래</dealingGbn>
        <cdealType></cdealType>
      </item>
    </items>
    <totalCount>1</totalCount>
  </body>
</response>"""
        items, _ = _parse_apt_trades(xml_text)
        assert items[0]["trade_date"] == "2025-03-05"


class TestParseOfficetelTrades:
    """Unit tests for officetel trade XML parsing."""

    def test_normal_response_returns_items(self) -> None:
        """Normal XML returns items correctly parsed."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>000</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <offiNm>테스트오피스텔</offiNm>
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
        items, error_code = _parse_officetel_trades(xml_text)
        assert error_code is None
        assert len(items) == 1
        assert items[0]["unit_name"] == "테스트오피스텔"
        assert items[0]["area_sqm"] == 42.5
        assert items[0]["price_10k"] == 35000


class TestParseVillaTrades:
    """Unit tests for villa (row-house/multi-family) trade XML parsing."""

    def test_normal_response_returns_items(self) -> None:
        """Normal XML returns items with house_type."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>000</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <mhouseNm>테스트빌라</mhouseNm>
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
        items, error_code = _parse_villa_trades(xml_text)
        assert error_code is None
        assert len(items) == 1
        assert items[0]["unit_name"] == "테스트빌라"
        assert items[0]["house_type"] == "다세대"
        assert items[0]["price_10k"] == 55000


class TestParseSingleHouseTrades:
    """Unit tests for single/detached house trade XML parsing."""

    def test_normal_response_returns_items(self) -> None:
        """Normal XML returns items with totalFloorAr as area."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
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
        items, error_code = _parse_single_house_trades(xml_text)
        assert error_code is None
        assert len(items) == 1
        assert items[0]["unit_name"] == ""  # Not provided
        assert items[0]["house_type"] == "단독"
        assert items[0]["area_sqm"] == 120.0
        assert items[0]["floor"] == 0  # Not applicable
        assert items[0]["price_10k"] == 180000


class TestParseCommercialTrade:
    """Unit tests for commercial building trade XML parsing."""

    def test_normal_response_returns_items(self) -> None:
        """Normal XML returns items with commercial-specific fields."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
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
        items, error_code = _parse_commercial_trade(xml_text)
        assert error_code is None
        assert len(items) == 1
        assert items[0]["building_type"] == "근린생활시설"
        assert items[0]["building_use"] == "상가"
        assert items[0]["land_use"] == "상업지역"
        assert items[0]["building_ar"] == 150.0
        assert items[0]["price_10k"] == 500000

    def test_cancelled_deal_with_lowercase_tag_excluded(self) -> None:
        """Items with cdealtype=O (lowercase) are excluded."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
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
        <cdealtype>O</cdealtype>
        <shareDealingType></shareDealingType>
      </item>
    </items>
    <totalCount>1</totalCount>
  </body>
</response>"""
        items, _ = _parse_commercial_trade(xml_text)
        assert len(items) == 0


class TestTradeParserEdgeCases:
    """Edge case tests for trade parsers."""

    def test_empty_items_list(self) -> None:
        """Empty items list returns empty result."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>000</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items/>
    <totalCount>0</totalCount>
  </body>
</response>"""
        items, error_code = _parse_apt_trades(xml_text)
        assert error_code is None
        assert items == []

    def test_comma_in_price_removed(self) -> None:
        """Commas in dealAmount are stripped."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>000</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <aptNm>테스트</aptNm>
        <umdNm>합정동</umdNm>
        <excluUseAr>84.0</excluUseAr>
        <floor>10</floor>
        <dealAmount>1,234,567</dealAmount>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>10</dealDay>
        <buildYear>2010</buildYear>
        <dealingGbn>중개거래</dealingGbn>
        <cdealType></cdealType>
      </item>
    </items>
    <totalCount>1</totalCount>
  </body>
</response>"""
        items, _ = _parse_apt_trades(xml_text)
        assert items[0]["price_10k"] == 1234567

    def test_missing_optional_fields_default_values(self) -> None:
        """Missing optional fields get default values."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>000</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <aptNm>테스트</aptNm>
        <umdNm></umdNm>
        <excluUseAr></excluUseAr>
        <floor></floor>
        <dealAmount>100,000</dealAmount>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>10</dealDay>
        <buildYear></buildYear>
        <dealingGbn></dealingGbn>
        <cdealType></cdealType>
      </item>
    </items>
    <totalCount>1</totalCount>
  </body>
</response>"""
        items, _ = _parse_apt_trades(xml_text)
        assert len(items) == 1
        assert items[0]["dong"] == ""
        assert items[0]["area_sqm"] == 0.0
        assert items[0]["floor"] == 0
        assert items[0]["build_year"] == 0
        assert items[0]["deal_type"] == ""
