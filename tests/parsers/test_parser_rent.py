"""Unit tests for rent XML parsers.

These tests validate the XML parsing logic for rent (lease) API responses.

Requirements:
- REQ-TEST-003: Parser tests for XML parsing validation
"""

import pytest

from real_estate.mcp_server.parsers.rent import (
    _parse_apt_rent,
    _parse_officetel_rent,
    _parse_single_house_rent,
    _parse_villa_rent,
)


class TestParseAptRent:
    """Unit tests for apartment rent XML parsing."""

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
        <deposit>50,000</deposit>
        <monthlyRent>0</monthlyRent>
        <contractType>신규</contractType>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>10</dealDay>
        <buildYear>2014</buildYear>
        <cdealType></cdealType>
      </item>
    </items>
    <totalCount>1</totalCount>
  </body>
</response>"""
        items, error_code = _parse_apt_rent(xml_text)
        assert error_code is None
        assert len(items) == 1
        assert items[0]["unit_name"] == "테스트아파트"
        assert items[0]["dong"] == "합정동"
        assert items[0]["area_sqm"] == 84.97
        assert items[0]["floor"] == 12
        assert items[0]["deposit_10k"] == 50000
        assert items[0]["monthly_rent_10k"] == 0  # 전세
        assert items[0]["contract_type"] == "신규"
        assert items[0]["trade_date"] == "2025-01-10"
        assert items[0]["build_year"] == 2014

    def test_monthly_rent_parsed_correctly(self) -> None:
        """Non-zero monthlyRent (월세) is parsed correctly."""
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
        <excluUseAr>59.0</excluUseAr>
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
    <totalCount>1</totalCount>
  </body>
</response>"""
        items, _ = _parse_apt_rent(xml_text)
        assert items[0]["deposit_10k"] == 20000
        assert items[0]["monthly_rent_10k"] == 80

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
        <deposit>50,000</deposit>
        <monthlyRent>0</monthlyRent>
        <contractType>신규</contractType>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>10</dealDay>
        <buildYear>2010</buildYear>
        <cdealType></cdealType>
      </item>
      <item>
        <aptNm>취소거래</aptNm>
        <umdNm>공덕동</umdNm>
        <excluUseAr>84.0</excluUseAr>
        <floor>5</floor>
        <deposit>40,000</deposit>
        <monthlyRent>0</monthlyRent>
        <contractType>신규</contractType>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>5</dealDay>
        <buildYear>2015</buildYear>
        <cdealType>O</cdealType>
      </item>
    </items>
    <totalCount>2</totalCount>
  </body>
</response>"""
        items, _ = _parse_apt_rent(xml_text)
        assert len(items) == 1
        assert items[0]["unit_name"] == "정상거래"

    def test_missing_deposit_excluded(self) -> None:
        """Items with missing or invalid deposit are excluded."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>000</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <aptNm>보증금있음</aptNm>
        <umdNm>합정동</umdNm>
        <excluUseAr>84.0</excluUseAr>
        <floor>10</floor>
        <deposit>50,000</deposit>
        <monthlyRent>0</monthlyRent>
        <contractType>신규</contractType>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>10</dealDay>
        <buildYear>2010</buildYear>
        <cdealType></cdealType>
      </item>
      <item>
        <aptNm>보증금없음</aptNm>
        <umdNm>공덕동</umdNm>
        <excluUseAr>84.0</excluUseAr>
        <floor>5</floor>
        <deposit></deposit>
        <monthlyRent>0</monthlyRent>
        <contractType>신규</contractType>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>5</dealDay>
        <buildYear>2015</buildYear>
        <cdealType></cdealType>
      </item>
    </items>
    <totalCount>2</totalCount>
  </body>
</response>"""
        items, _ = _parse_apt_rent(xml_text)
        assert len(items) == 1
        assert items[0]["unit_name"] == "보증금있음"

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
        items, error_code = _parse_apt_rent(xml_text)
        assert error_code == "03"
        assert items == []


class TestParseOfficetelRent:
    """Unit tests for officetel rent XML parsing."""

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
        items, error_code = _parse_officetel_rent(xml_text)
        assert error_code is None
        assert len(items) == 1
        assert items[0]["unit_name"] == "테스트오피스텔"
        assert items[0]["deposit_10k"] == 10000
        assert items[0]["monthly_rent_10k"] == 50


class TestParseVillaRent:
    """Unit tests for villa (row-house/multi-family) rent XML parsing."""

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
        items, error_code = _parse_villa_rent(xml_text)
        assert error_code is None
        assert len(items) == 1
        assert items[0]["unit_name"] == "테스트빌라"
        assert items[0]["house_type"] == "다세대"
        assert items[0]["deposit_10k"] == 15000
        assert items[0]["monthly_rent_10k"] == 30


class TestParseSingleHouseRent:
    """Unit tests for single/detached house rent XML parsing."""

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
        items, error_code = _parse_single_house_rent(xml_text)
        assert error_code is None
        assert len(items) == 1
        assert items[0]["unit_name"] == ""  # Not provided
        assert items[0]["house_type"] == "단독"
        assert items[0]["area_sqm"] == 120.0
        assert items[0]["deposit_10k"] == 80000
        assert items[0]["monthly_rent_10k"] == 0


class TestRentParserEdgeCases:
    """Edge case tests for rent parsers."""

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
        items, error_code = _parse_apt_rent(xml_text)
        assert error_code is None
        assert items == []

    def test_comma_in_deposit_removed(self) -> None:
        """Commas in deposit are stripped."""
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
        <deposit>1,234,567</deposit>
        <monthlyRent>0</monthlyRent>
        <contractType>신규</contractType>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>10</dealDay>
        <buildYear>2010</buildYear>
        <cdealType></cdealType>
      </item>
    </items>
    <totalCount>1</totalCount>
  </body>
</response>"""
        items, _ = _parse_apt_rent(xml_text)
        assert items[0]["deposit_10k"] == 1234567

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
        <deposit>50,000</deposit>
        <monthlyRent></monthlyRent>
        <contractType></contractType>
        <dealYear>2025</dealYear>
        <dealMonth>1</dealMonth>
        <dealDay>10</dealDay>
        <buildYear></buildYear>
        <cdealType></cdealType>
      </item>
    </items>
    <totalCount>1</totalCount>
  </body>
</response>"""
        items, _ = _parse_apt_rent(xml_text)
        assert len(items) == 1
        assert items[0]["dong"] == ""
        assert items[0]["area_sqm"] == 0.0
        assert items[0]["floor"] == 0
        assert items[0]["monthly_rent_10k"] == 0
        assert items[0]["build_year"] == 0
        assert items[0]["contract_type"] == ""
