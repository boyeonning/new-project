#!/usr/bin/env python3
"""
간단한 인사말 프로그램
사용자의 이름을 입력받아 개인화된 인사말을 출력합니다.
"""

import datetime


def get_greeting():
    """현재 시간에 따른 적절한 인사말을 반환합니다."""
    current_hour = datetime.datetime.now().hour
    
    if 5 <= current_hour < 12:
        return "좋은 아침입니다"
    elif 12 <= current_hour < 18:
        return "안녕하세요"
    elif 18 <= current_hour < 22:
        return "좋은 저녁입니다"
    else:
        return "안녕하세요"


def main():
    """메인 함수"""
    print("=" * 40)
    print("    환영합니다! 👋")
    print("=" * 40)
    
    # 사용자 이름 입력받기
    name = input("이름을 입력해주세요: ").strip()
    
    if not name:
        name = "익명의 사용자"
    
    # 시간대별 인사말
    greeting = get_greeting()
    current_time = datetime.datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")
    
    print(f"\n{greeting}, {name}님!")
    print(f"현재 시간: {current_time}")
    print("\nPython으로 만든 첫 번째 프로그램입니다! 🐍")
    print("즐거운 코딩 되세요! ✨")


if __name__ == "__main__":
    main()
