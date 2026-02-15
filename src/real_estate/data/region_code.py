"""법정동코드 로컬 파일 검색 모듈.

국토교통부 실거래가 API 파라미터(LAWd_CD)에 사용하는
법정동코드 5자리를 사용자 입력 텍스트에서 찾아 반환한다.

파일 내 코드는 10자리(예: 1144000000)이며,
API는 앞 5자리(예: 11440)를 사용한다.
구/군 단위 행은 10자리 중 끝 5자리가 "00000"인 행이다.
"""

from pathlib import Path
from typing import TypedDict

REGION_FILE = Path(__file__).parent.parent / "resources" / "region_codes.txt"


class RegionMatch(TypedDict):
    """단일 매칭 결과."""

    code: str  # 원본 10자리 코드
    name: str


class RegionResult(TypedDict, total=False):
    """search_region_code 반환 타입."""

    region_code: str  # API 파라미터용 5자리 코드
    full_name: str
    matches: list[RegionMatch]
    error: str
    message: str


def _load_region_rows() -> list[tuple[str, str]]:
    """파일에서 (코드, 법정동명) 행을 로드한다.

    Returns:
        폐지되지 않은 (10자리 코드, 이름) 튜플 리스트.
    """
    rows: list[tuple[str, str]] = []
    with REGION_FILE.open(encoding="utf-8") as f:
        next(f)  # 헤더 스킵
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            code, name, status = parts[0], parts[1], parts[2]
            if status == "존재":
                rows.append((code, name))
    return rows


def _to_api_code(ten_digit: str) -> str:
    """10자리 법정동코드에서 API용 5자리 코드를 추출한다.

    Parameters:
        ten_digit: 10자리 법정동코드 (예: "1144000000")

    Returns:
        앞 5자리 문자열 (예: "11440")
    """
    return ten_digit[:5]


def _is_gu_gun(ten_digit: str) -> bool:
    """구/군 단위 행인지 판별한다 (끝 5자리가 "00000").

    Parameters:
        ten_digit: 10자리 법정동코드

    Returns:
        구/군 단위이면 True.
    """
    return ten_digit[5:] == "00000"


def search_region_code(query: str) -> RegionResult:
    """사용자 입력 지역명을 법정동코드로 변환한다.

    Parameters:
        query: 사용자 자유 입력 텍스트 (예: "마포구", "서울 마포구 공덕동")

    Returns:
        region_code: API 파라미터용 5자리 코드 (예: "11440")
        full_name: 대표 매칭 법정동명
        matches: 모든 매칭 결과의 원본 10자리 코드와 이름
        error/message: 매칭 없음 또는 파일 오류 시

    Notes:
        - 구/군 단위 행(끝 5자리 "00000")이 있으면 그것을 대표로 채택한다.
        - 복수 매칭 시 matches 배열을 Claude가 사용자에게 확인하도록 한다.
    """
    query = query.strip()
    if not query:
        return {"error": "invalid_input", "message": "지역명을 입력해 주세요."}

    try:
        rows = _load_region_rows()
    except FileNotFoundError:
        return {"error": "file_not_found", "message": "법정동코드 파일을 찾을 수 없습니다."}

    # 쿼리 토큰 분리: "서울 마포구" → ["서울", "마포구"] 모두 포함하는 행 필터
    tokens = query.split()
    matched = [(code, name) for code, name in rows if all(tok in name for tok in tokens)]

    if not matched:
        return {
            "error": "no_match",
            "message": f"입력한 지역명을 찾을 수 없습니다: {query}",
        }

    # 구/군 단위(끝 5자리 "00000") 우선, 그 다음 코드 오름차순
    matched.sort(key=lambda x: (not _is_gu_gun(x[0]), x[0]))

    matches: list[RegionMatch] = [{"code": c, "name": n} for c, n in matched]

    # 구/군 단위 행이 있으면 우선 채택, 없으면 첫 번째 매칭
    gu_gun = [(c, n) for c, n in matched if _is_gu_gun(c)]
    best_code, best_name = gu_gun[0] if gu_gun else matched[0]

    return {
        "region_code": _to_api_code(best_code),
        "full_name": best_name,
        "matches": matches,
    }
