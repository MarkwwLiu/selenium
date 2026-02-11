"""
背景測試執行器

在獨立 subprocess 中執行 pytest，即時回傳輸出。
"""

import os
import sys
import json
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TestResult:
    """單一測試結果。"""
    nodeid: str = ''
    name: str = ''
    outcome: str = ''  # passed / failed / error / skipped
    duration: float = 0.0
    message: str = ''
    longrepr: str = ''


@dataclass
class RunSession:
    """一次測試執行的完整紀錄。"""
    run_id: str = ''
    started_at: str = ''
    finished_at: str = ''
    status: str = 'idle'  # idle / running / finished / error
    test_path: str = ''
    browser: str = 'chrome'
    headless: bool = True
    env: str = 'dev'
    markers: str = ''
    extra_args: str = ''
    total: int = 0
    passed: int = 0
    failed: int = 0
    error: int = 0
    skipped: int = 0
    results: list = field(default_factory=list)
    output_lines: list = field(default_factory=list)
    exit_code: int = -1


# === 全域狀態 ===
_current_session: RunSession | None = None
_history: list[RunSession] = []
_lock = threading.Lock()

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def get_current_session() -> RunSession | None:
    return _current_session


def get_history() -> list[RunSession]:
    return list(_history)


def is_running() -> bool:
    return _current_session is not None and _current_session.status == 'running'


def _build_pytest_args(session: RunSession) -> list[str]:
    """根據 RunSession 組合 pytest 命令列參數。"""
    args = [
        sys.executable, '-m', 'pytest',
        session.test_path,
        '-v', '--tb=short', '--no-header',
        f'--browser={session.browser}',
    ]

    if session.headless:
        args.append('--headless-mode')

    if session.env:
        args.extend(['--env', session.env])

    if session.markers:
        args.extend(['-m', session.markers])

    # JSON 結果輸出（需安裝 pytest-json-report）
    try:
        import pytest_jsonreport  # noqa: F401
        _has_json_report = True
    except ImportError:
        _has_json_report = False

    if _has_json_report:
        json_path = os.path.join(ROOT_DIR, 'reports', '.last_run.json')
        args.extend([
            '--json-report',
            f'--json-report-file={json_path}',
        ])

    if session.extra_args:
        args.extend(session.extra_args.split())

    return args


def _parse_json_report(session: RunSession):
    """解析 pytest-json-report 產生的結果。"""
    json_path = os.path.join(ROOT_DIR, 'reports', '.last_run.json')
    if not os.path.exists(json_path):
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        summary = data.get('summary', {})
        session.passed = summary.get('passed', 0)
        session.failed = summary.get('failed', 0)
        session.error = summary.get('error', 0)
        session.skipped = summary.get('skipped', 0)
        session.total = summary.get('total', 0)

        for t in data.get('tests', []):
            r = TestResult(
                nodeid=t.get('nodeid', ''),
                name=t.get('nodeid', '').split('::')[-1],
                outcome=t.get('outcome', ''),
                duration=t.get('duration', 0.0),
            )
            call_info = t.get('call', {})
            if call_info.get('longrepr'):
                r.longrepr = call_info['longrepr']
            if call_info.get('crash', {}).get('message'):
                r.message = call_info['crash']['message']
            session.results.append(r)

    except Exception as e:
        session.output_lines.append(f'[解析報告失敗] {e}')


def _run_in_thread(session: RunSession, on_update=None):
    """在子執行緒中跑 pytest subprocess。"""
    global _current_session
    session.status = 'running'
    session.started_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        args = _build_pytest_args(session)
        session.output_lines.append(f'$ {" ".join(args)}')
        if on_update:
            on_update()

        proc = subprocess.Popen(
            args,
            cwd=ROOT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        for line in proc.stdout:
            line = line.rstrip('\n')
            with _lock:
                session.output_lines.append(line)

                # 即時統計 PASSED / FAILED
                if ' PASSED' in line:
                    session.passed += 1
                    session.total += 1
                elif ' FAILED' in line:
                    session.failed += 1
                    session.total += 1
                elif ' ERROR' in line:
                    session.error += 1
                    session.total += 1
                elif ' SKIPPED' in line:
                    session.skipped += 1
                    session.total += 1

            if on_update:
                on_update()

        proc.wait()
        session.exit_code = proc.returncode

        # 嘗試從 JSON 報告取得精確結果（覆寫即時統計）
        _parse_json_report(session)

    except Exception as e:
        session.output_lines.append(f'[錯誤] {e}')
        session.status = 'error'
    else:
        session.status = 'finished'
    finally:
        session.finished_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with _lock:
            _history.append(session)
        if on_update:
            on_update()


def start_run(
    test_path: str = 'tests/',
    browser: str = 'chrome',
    headless: bool = True,
    env: str = 'dev',
    markers: str = '',
    extra_args: str = '',
    on_update=None,
) -> RunSession:
    """
    啟動一次測試執行。

    Args:
        test_path: 測試路徑
        browser: 瀏覽器
        headless: 是否無頭
        env: 環境
        markers: pytest 標記
        extra_args: 額外參數
        on_update: 有新輸出時的回呼函式

    Returns:
        RunSession 物件
    """
    global _current_session

    if is_running():
        raise RuntimeError('已有測試正在執行中')

    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    session = RunSession(
        run_id=run_id,
        test_path=test_path,
        browser=browser,
        headless=headless,
        env=env,
        markers=markers,
        extra_args=extra_args,
    )
    _current_session = session

    os.makedirs(os.path.join(ROOT_DIR, 'reports'), exist_ok=True)

    t = threading.Thread(target=_run_in_thread, args=(session, on_update), daemon=True)
    t.start()

    return session


def discover_tests(test_path: str = 'tests/') -> list[str]:
    """
    用 pytest --collect-only 列出所有測試項目。

    Returns:
        list of test nodeids
    """
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', test_path, '--collect-only', '-q', '--no-header'],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        items = []
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if '::' in line and not line.startswith(('=', '-', 'no tests')):
                items.append(line)
        return items
    except Exception:
        return []


def discover_scenarios() -> list[dict]:
    """
    掃描 scenarios/ 目錄，回傳所有情境資訊。

    Returns:
        [{'name': '...', 'path': '...', 'url': '...', 'has_tests': bool}, ...]
    """
    scenarios_dir = os.path.join(ROOT_DIR, 'scenarios')
    results = []

    if not os.path.isdir(scenarios_dir):
        return results

    for name in sorted(os.listdir(scenarios_dir)):
        if name.startswith(('_', '.')):
            continue
        scenario_path = os.path.join(scenarios_dir, name)
        if not os.path.isdir(scenario_path):
            continue

        info = {
            'name': name,
            'path': scenario_path,
            'url': '',
            'has_tests': os.path.isdir(os.path.join(scenario_path, 'tests')),
        }

        # 嘗試讀取 SCENARIO_URL
        conftest = os.path.join(scenario_path, 'conftest.py')
        if os.path.exists(conftest):
            try:
                with open(conftest, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip().startswith('SCENARIO_URL'):
                            url_val = line.split('=', 1)[1].strip().strip("'\"")
                            info['url'] = url_val
                            break
            except Exception:
                pass

        results.append(info)

    return results
