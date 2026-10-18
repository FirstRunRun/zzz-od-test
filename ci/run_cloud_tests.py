"""运行独立于游戏窗口的 33 项测试，保存版本和真实结果。"""

import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def git_sha(directory: Path) -> str:
    """读取实际检出提交，不用分支名称代替版本。"""
    return subprocess.check_output(
        ['git', '-C', str(directory), 'rev-parse', 'HEAD'], text=True
    ).strip()


def main() -> int:
    """执行全部指定测试；失败、跳过或数量异常均返回失败。"""
    test_root = Path(__file__).resolve().parents[1]
    project_root = test_root.parent
    report_dir = project_root / '.debug' / 'cloud-unit-tests'
    report_dir.mkdir(parents=True, exist_ok=True)
    versions = {
        'main_repository': 'FirstRunRun/ZenlessZoneZero-OneDragon',
        'main_sha': git_sha(project_root),
        'test_repository': 'FirstRunRun/zzz-od-test',
        'test_sha': git_sha(test_root),
        'python': platform.python_version(),
        'platform': platform.platform(),
        'dependencies': {
            name: importlib.metadata.version(name)
            for name in ('pytest', 'numpy', 'opencv-python', 'PyYAML', 'ruff')
        },
    }
    version_text = json.dumps(versions, ensure_ascii=False, indent=2)
    (report_dir / 'versions.json').write_text(version_text, encoding='utf-8')
    print(version_text, flush=True)
    for variable, key in (
        ('MAIN_SHA', 'main_sha'),
        ('EXPECTED_TEST_SHA', 'test_sha'),
    ):
        expected = os.environ.get(variable)
        if expected and versions[key] != expected:
            print(f'版本不匹配：{variable}={expected}，实际为 {versions[key]}')
            return 1

    suites = (
        ('repo-config', 'test/one_dragon/envs/test_repo_config.py', 12),
        ('restore-charge', 'test/zzz_od/operation/test_restore_charge.py', 15),
        ('cv2-utils', 'test/one_dragon/utils/test_cv2_utils.py', 6),
    )
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root / 'src')
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
    lines = [
        '# 云端单元测试',
        '',
        f"主项目 SHA：`{versions['main_sha']}`",
        f"测试项目 SHA：`{versions['test_sha']}`",
        '',
        '| 测试组 | 预期数量 | 实际数量 | 结果 |',
        '|---|---:|---:|---|',
    ]
    all_passed = True
    for name, relative_path, expected_count in suites:
        test_file = test_root / relative_path
        report = report_dir / f'{name}.xml'
        report.unlink(missing_ok=True)
        # 这些测试不使用全局游戏 fixture；限定配置搜索范围，不过滤测试或断言。
        result = subprocess.run(
            [
                sys.executable, '-m', 'pytest', '-p', 'no:cacheprovider',
                f'--confcutdir={test_file.parent}', str(test_file),
                '-q', '--tb=short', f'--junitxml={report}',
            ],
            cwd=project_root,
            env=env,
            check=False,
        )
        actual_count = 0
        passed = False
        if report.exists():
            root = ET.parse(report).getroot()
            cases = root.findall('.//testcase')
            actual_count = len(cases)
            passed = (
                result.returncode == 0
                and actual_count == expected_count
                and not any(
                    case.find(tag) is not None
                    for case in cases
                    for tag in ('failure', 'error', 'skipped')
                )
            )
        all_passed = all_passed and passed
        status = '通过' if passed else '失败'
        lines.append(f'| {name} | {expected_count} | {actual_count} | {status} |')

    summary = '\n'.join(lines) + '\n'
    (report_dir / 'summary.md').write_text(summary, encoding='utf-8')
    if summary_file := os.environ.get('GITHUB_STEP_SUMMARY'):
        with Path(summary_file).open('a', encoding='utf-8') as stream:
            stream.write(summary)
    print(summary, flush=True)
    return 0 if all_passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
