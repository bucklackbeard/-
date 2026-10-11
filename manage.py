#!/usr/bin/env python

# Django 관리 명령 실행파일

import os
import sys


def main():
    # 관리 명령 실행
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings") # 설정파일 경로

    # 오류처리 구문
    try:
        from django.core.management import execute_from_command_line
    except ImportError as error:
        raise ImportError(
            "Django를 불러올 수 없습니다. 설치되어 있는지 확인하세요. "
        ) from error

    #커맨드라인 내용 Django로 전달
    execute_from_command_line(sys.argv)

# 직접 실행했을 때만 main() 구동
if __name__ == "__main__":
    main()
