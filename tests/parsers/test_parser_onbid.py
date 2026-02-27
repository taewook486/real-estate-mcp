"""Unit tests for Onbid XML/JSON parsers.

These tests validate the parsing logic for Onbid API responses.

Requirements:
- REQ-TEST-003: Parser tests for XML/JSON parsing validation
"""

import pytest

from real_estate.mcp_server.parsers.onbid import (
    _as_str_key_dict,
    _get_total_count_onbid,
    _onbid_extract_items,
    _parse_onbid_code_info_xml,
    _parse_onbid_thing_info_list_xml,
    _parse_onbid_xml_items,
)


class TestAsStrKeyDict:
    """Unit tests for _as_str_key_dict helper function."""

    def test_normal_dict_returns_same(self) -> None:
        """Normal dict with string keys returns same dict."""
        result = _as_str_key_dict({"a": 1, "b": 2})
        assert result == {"a": 1, "b": 2}

    def test_non_mapping_returns_empty_dict(self) -> None:
        """Non-mapping value returns empty dict."""
        result = _as_str_key_dict("not a dict")
        assert result == {}

    def test_non_string_keys_filtered(self) -> None:
        """Non-string keys are filtered out."""
        result = _as_str_key_dict({1: "a", "b": 2, None: "c"})
        assert result == {"b": 2}

    def test_none_returns_empty_dict(self) -> None:
        """None value returns empty dict."""
        result = _as_str_key_dict(None)
        assert result == {}


class TestGetTotalCountOnbid:
    """Unit tests for _get_total_count_onbid helper function."""

    def test_total_count_uppercase(self) -> None:
        """TotalCount (uppercase) is parsed correctly."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <body>
    <TotalCount>100</TotalCount>
  </body>
</response>"""
        from defusedxml.ElementTree import fromstring

        root = fromstring(xml_text)
        result = _get_total_count_onbid(root)
        assert result == 100

    def test_total_count_camelcase(self) -> None:
        """totalCount (camelCase) is parsed correctly."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <body>
    <totalCount>50</totalCount>
  </body>
</response>"""
        from defusedxml.ElementTree import fromstring

        root = fromstring(xml_text)
        result = _get_total_count_onbid(root)
        assert result == 50

    def test_total_count_lowercase(self) -> None:
        """totalcount (lowercase) is parsed correctly."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <body>
    <totalcount>25</totalcount>
  </body>
</response>"""
        from defusedxml.ElementTree import fromstring

        root = fromstring(xml_text)
        result = _get_total_count_onbid(root)
        assert result == 25

    def test_missing_total_count_returns_zero(self) -> None:
        """Missing total count returns 0."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <body>
    <items/>
  </body>
</response>"""
        from defusedxml.ElementTree import fromstring

        root = fromstring(xml_text)
        result = _get_total_count_onbid(root)
        assert result == 0

    def test_invalid_total_count_returns_zero(self) -> None:
        """Invalid total count returns 0."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <body>
    <TotalCount>invalid</TotalCount>
  </body>
</response>"""
        from defusedxml.ElementTree import fromstring

        root = fromstring(xml_text)
        result = _get_total_count_onbid(root)
        assert result == 0


class TestOnbidExtractItems:
    """Unit tests for _onbid_extract_items JSON parser."""

    def test_standard_response_structure(self) -> None:
        """Standard response with header/body structure is parsed."""
        payload = {
            "response": {
                "header": {"resultCode": "00"},
                "body": {"items": {"item": [{"id": "1", "name": "Test"}]}},
            }
        }
        result_code, body, items = _onbid_extract_items(payload)
        assert result_code == "00"
        assert len(items) == 1
        assert items[0]["id"] == "1"

    def test_flat_payload_structure(self) -> None:
        """Flat payload (no response wrapper) is parsed."""
        payload = {
            "resultCode": "00",
            "resultMsg": "OK",
            "items": {"item": [{"id": "1"}]},
        }
        result_code, body, items = _onbid_extract_items(payload)
        assert result_code == "00"
        assert len(items) == 1

    def test_single_item_as_dict(self) -> None:
        """Single item returned as dict is converted to list."""
        payload = {
            "response": {
                "header": {"resultCode": "00"},
                "body": {"items": {"item": {"id": "1", "name": "Single"}}},
            }
        }
        result_code, body, items = _onbid_extract_items(payload)
        assert len(items) == 1
        assert items[0]["id"] == "1"

    def test_items_as_list(self) -> None:
        """Items as list is handled correctly."""
        payload = {
            "response": {
                "header": {"resultCode": "00"},
                "body": {"items": [{"id": "1"}, {"id": "2"}]},
            }
        }
        result_code, body, items = _onbid_extract_items(payload)
        assert len(items) == 2

    def test_no_items_returns_empty_list(self) -> None:
        """Missing items returns empty list."""
        payload = {"response": {"header": {"resultCode": "00"}, "body": {}}}
        result_code, body, items = _onbid_extract_items(payload)
        assert items == []

    def test_null_result_code(self) -> None:
        """Null resultCode is converted to empty string."""
        payload = {
            "response": {"header": {"resultCode": None}, "body": {"items": {}}}
        }
        result_code, body, items = _onbid_extract_items(payload)
        assert result_code == ""

    def test_integer_result_code(self) -> None:
        """Integer resultCode is converted to string."""
        payload = {"response": {"header": {"resultCode": 0}, "body": {"items": {}}}}
        result_code, body, items = _onbid_extract_items(payload)
        assert result_code == "0"


class TestParseOnbidXmlItems:
    """Unit tests for _parse_onbid_xml_items XML parser."""

    def test_normal_response_returns_items(self) -> None:
        """Normal XML returns items correctly parsed."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>00</resultCode>
    <resultMsg>NORMAL SERVICE</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <CTGR_ID>10101</CTGR_ID>
        <CTGR_NM>아파트</CTGR_NM>
      </item>
      <item>
        <CTGR_ID>10102</CTGR_ID>
        <CTGR_NM>오피스텔</CTGR_NM>
      </item>
    </items>
    <TotalCount>2</TotalCount>
  </body>
</response>"""
        items, total_count, error_code, error_msg = _parse_onbid_xml_items(xml_text)
        assert error_code is None
        assert error_msg is None
        assert total_count == 2
        assert len(items) == 2
        assert items[0]["CTGR_ID"] == "10101"
        assert items[0]["CTGR_NM"] == "아파트"

    def test_error_response_returns_error_code(self) -> None:
        """Non-00 resultCode returns error code and message."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>99</resultCode>
    <resultMsg>SYSTEM ERROR</resultMsg>
  </header>
  <body>
    <items/>
  </body>
</response>"""
        items, total_count, error_code, error_msg = _parse_onbid_xml_items(xml_text)
        assert error_code == "99"
        assert error_msg == "SYSTEM ERROR"
        assert items == []

    def test_empty_items_returns_empty_list(self) -> None:
        """Empty items returns empty list."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>00</resultCode>
    <resultMsg>NORMAL SERVICE</resultMsg>
  </header>
  <body>
    <items/>
    <TotalCount>0</TotalCount>
  </body>
</response>"""
        items, total_count, error_code, error_msg = _parse_onbid_xml_items(xml_text)
        assert items == []
        assert total_count == 0

    def test_empty_text_elements_handled(self) -> None:
        """Empty text in XML elements is handled gracefully."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>00</resultCode>
    <resultMsg>NORMAL SERVICE</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <CTGR_ID></CTGR_ID>
        <CTGR_NM></CTGR_NM>
      </item>
    </items>
    <TotalCount>1</TotalCount>
  </body>
</response>"""
        items, total_count, error_code, error_msg = _parse_onbid_xml_items(xml_text)
        assert len(items) == 1
        assert items[0]["CTGR_ID"] == ""
        assert items[0]["CTGR_NM"] == ""


class TestParseOnbidThingInfoListXml:
    """Unit tests for _parse_onbid_thing_info_list_xml function."""

    def test_normal_response(self) -> None:
        """Normal ThingInfoInquireSvc XML is parsed."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>00</resultCode>
    <resultMsg>NORMAL SERVICE</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <CLTR_NO>12345</CLTR_NO>
        <CLTR_NM>테스트물건</CLTR_NM>
        <FST_REG_DT>2025-01-01</FST_REG_DT>
      </item>
    </items>
    <TotalCount>1</TotalCount>
  </body>
</response>"""
        items, total_count, error_code, error_msg = _parse_onbid_thing_info_list_xml(
            xml_text
        )
        assert error_code is None
        assert len(items) == 1
        assert items[0]["CLTR_NO"] == "12345"


class TestParseOnbidCodeInfoXml:
    """Unit tests for _parse_onbid_code_info_xml function."""

    def test_normal_response(self) -> None:
        """Normal OnbidCodeInfoInquireSvc XML is parsed."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>00</resultCode>
    <resultMsg>NORMAL SERVICE</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <CTGR_ID>10101</CTGR_ID>
        <CTGR_NM>아파트</CTGR_NM>
        <UPR_CTGR_ID>10100</UPR_CTGR_ID>
      </item>
    </items>
    <TotalCount>1</TotalCount>
  </body>
</response>"""
        items, total_count, error_code, error_msg = _parse_onbid_code_info_xml(xml_text)
        assert error_code is None
        assert len(items) == 1
        assert items[0]["CTGR_ID"] == "10101"
        assert items[0]["CTGR_NM"] == "아파트"
