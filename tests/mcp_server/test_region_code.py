"""법정동코드 검색 함수 단위 테스트."""

from real_estate.data.region_code import search_region_code


class TestSearchRegionCode:
    """search_region_code 정상 케이스."""

    def test_gu_name_returns_five_digit_api_code(self) -> None:
        """구 이름 입력 시 API용 5자리 코드 반환.

        파일 내 코드는 10자리(1144000000)이며,
        region_code는 앞 5자리(11440)를 반환해야 한다.
        """
        result = search_region_code("마포구")
        assert "region_code" in result
        assert result["region_code"] == "11440"
        assert "full_name" in result
        assert "마포구" in result["full_name"]

    def test_full_path_returns_gu_code(self) -> None:
        """시+구 조합 입력 시 구 단위 5자리 코드 반환."""
        result = search_region_code("서울 마포구")
        assert "region_code" in result
        assert result["region_code"] == "11440"

    def test_dong_name_returns_matches(self) -> None:
        """동 이름 입력 시 matches에 동 단위 행 포함."""
        result = search_region_code("공덕동")
        assert "matches" in result
        assert any("공덕동" in m["name"] for m in result["matches"])

    def test_multiple_tokens_all_must_match(self) -> None:
        """복수 토큰은 법정동명에 모두 포함된 행만 반환."""
        result = search_region_code("마포구 공덕동")
        assert "matches" in result
        for m in result["matches"]:
            assert "마포구" in m["name"]
            assert "공덕동" in m["name"]

    def test_gu_gun_row_is_first_in_matches(self) -> None:
        """구/군 단위 행(끝 5자리 00000)이 matches 첫 번째에 위치."""
        result = search_region_code("마포구")
        assert "matches" in result
        first = result["matches"][0]
        # 10자리 원본 코드 끝 5자리가 "00000"이어야 함
        assert first["code"][5:] == "00000"


class TestSearchRegionCodeEdgeCases:
    """search_region_code 엣지케이스."""

    def test_empty_string_returns_error(self) -> None:
        """빈 문자열 입력 시 error 반환."""
        result = search_region_code("")
        assert "error" in result
        assert result["error"] == "invalid_input"

    def test_whitespace_only_returns_error(self) -> None:
        """공백만 입력 시 error 반환."""
        result = search_region_code("   ")
        assert "error" in result
        assert result["error"] == "invalid_input"

    def test_unknown_region_returns_no_match(self) -> None:
        """존재하지 않는 지역명 입력 시 no_match 반환."""
        result = search_region_code("없는지역XYZ")
        assert "error" in result
        assert result["error"] == "no_match"
        assert "message" in result
        assert "없는지역XYZ" in result["message"]
