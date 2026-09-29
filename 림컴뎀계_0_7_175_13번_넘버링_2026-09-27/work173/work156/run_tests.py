#!/usr/bin/env python3
"""Unified test runner for Limbus Company damage calculator.

사용법
  python run_tests.py             전체 테스트 (약 32초)
  python run_tests.py --fast      오래 걸리는 테스트(slow 8개) 제외, 빠른 확인용 (약 3초)
  python run_tests.py --parallel  여러 CPU 코어로 동시 실행 (pytest-xdist 필요, 없으면 자동 설치 시도)
  python run_tests.py --shuffle   실행 순서를 무작위로 (테스트끼리 서로 영향 주는지 검사, pytest-randomly 필요)
그 외 인자는 pytest에 그대로 전달된다. (예: python run_tests.py -k bleed)
"""
from __future__ import annotations
import os, sys, subprocess, compileall, importlib.util

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

argv = sys.argv[1:]
flags = {f for f in ("--fast", "--parallel", "--shuffle") if f in argv}
argv = [a for a in argv if a not in flags]


def ensure(pkg, module):
    if importlib.util.find_spec(module) is None:
        print(f"{pkg}가 없어서 자동 설치를 시도합니다...")
        r = subprocess.run([sys.executable, "-m", "pip", "install", pkg])
        if r.returncode != 0:
            print(f"ERROR: {pkg} 설치 실패. 직접 설치: python -m pip install {pkg}")
            sys.exit(2)


mode = " ".join(sorted(flags))
print("=== 림컴뎀계 통합 테스트 러너 ===" + (f" [{mode}]" if mode else ""))
print(f"Project: {ROOT}")
print()
print("[1/2] Python 문법 검사")
if not compileall.compile_dir(ROOT, quiet=1):
    print("[FAIL] Python 문법 검사 실패")
    sys.exit(1)
print("[PASS] Python 문법 검사 통과")
print()

ensure("pytest", "pytest")
args = [sys.executable, "-m", "pytest", "-q"]
if "--fast" in flags:
    args += ["-m", "not slow"]
if "--parallel" in flags:
    ensure("pytest-xdist", "xdist")
    args += ["-n", "auto"]
if "--shuffle" in flags:
    ensure("pytest-randomly", "pytest_randomly")
else:
    if importlib.util.find_spec("pytest_randomly") is not None:
        args += ["-p", "no:randomly"]   # 설치돼 있어도 기본은 고정 순서
print("[2/2] pytest 테스트 실행")
args += argv
result = subprocess.run(args)
print()
if result.returncode == 0:
    print("[PASS] " + ("빠른 테스트 통과 (전체 확인은 --fast 없이 실행)" if "--fast" in flags else "전체 테스트 통과"))
else:
    print(f"[FAIL] 테스트 실패 (exit code={result.returncode})")
sys.exit(result.returncode)
