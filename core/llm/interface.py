"""
core/llm/interface.py
LLM 추상화 인터페이스
ARCHITECTURE.md의 'LLM 인터페이스 추상화' 구현
"""

from abc import ABC, abstractmethod
from core.schema import SlideSchema


class LLMInterface(ABC):
    """
    모든 LLM 어댑터가 구현해야 하는 인터페이스.
    이 인터페이스를 통해 Claude API → 온프레미스 LLM 교체가 가능하다.
    """

    @abstractmethod
    def plan_slides(
        self,
        user_request: str,
        template: str,
        data: dict | None = None,
    ) -> SlideSchema:
        """
        사용자 요청을 받아 슬라이드 스키마를 생성한다.

        Args:
            user_request: 사용자가 입력한 장표 내용
            template: 선택된 템플릿 이름
            data: 데이터 파일 업로드 시 파싱된 데이터 (선택)

        Returns:
            SlideSchema: 검증된 슬라이드 구조
        """
        ...
