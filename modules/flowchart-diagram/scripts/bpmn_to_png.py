# -*- coding: utf-8 -*-
"""draw.io XML → SVG HTML → PNG。仅依赖标准库与本机 Chromium 浏览器。"""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from render_bpmn_html import render


def find_browser(explicit=None):
    """显式路径、BPMN_BROWSER、PATH、常见安装目录依次查找。"""
    specified = explicit or os.environ.get('BPMN_BROWSER')
    if specified:
        path = Path(specified).expanduser()
        found = str(path) if path.is_file() else shutil.which(specified)
        if not found:
            raise FileNotFoundError(f'指定浏览器不存在：{specified}')
        return found
    for name in ('google-chrome', 'chromium', 'chromium-browser', 'chrome', 'msedge'):
        found = shutil.which(name)
        if found:
            return found
    candidates = [Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
                  Path('/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge')]
    for base in (os.environ.get('PROGRAMFILES'), os.environ.get('PROGRAMFILES(X86)'), os.environ.get('LOCALAPPDATA')):
        if base:
            candidates.extend([Path(base) / 'Google/Chrome/Application/chrome.exe',
                               Path(base) / 'Microsoft/Edge/Application/msedge.exe'])
    return next((str(p) for p in candidates if p.is_file()), None)


def export_png(in_path, out_png, title, scale=2, browser=None):
    out_png = Path(out_png).resolve()
    if out_png.exists():
        raise FileExistsError(f'输出文件已存在，请使用新路径：{out_png}')
    if not 0 < float(scale) <= 4:
        raise ValueError('缩放倍率应大于 0 且不超过 4。')
    executable = find_browser(browser)
    if not executable:
        raise RuntimeError('没有找到 Chrome/Edge/Chromium 浏览器；请通过 --browser 指定路径，或先交付 draw.io 与 HTML。')
    if not out_png.parent.is_dir():
        raise FileNotFoundError(f'输出目录不存在：{out_png.parent}')
    # 每次导出独立目录，保留渲染 HTML 和浏览器资料供复查；不自动清理。
    work = Path(tempfile.mkdtemp(prefix='bpmn-render-', dir=out_png.parent))
    tmp_html = work / 'render.html'
    render(in_path, tmp_html, title)
    h = tmp_html.read_text(encoding='utf-8')
    m = re.search(r'viewBox="0 0 (\d+) (\d+)"', h)
    if not m:
        raise ValueError('生成 HTML 缺少有效 SVG viewBox。')
    w, height = map(int, m.groups())
    # HTML 在与图等宽的视口下展示，不强行截断大图。
    win_w, win_h = max(w + 80, 800), max(height + 240, 400)
    if win_w > 8000 or win_h > 8000:
        raise ValueError('图幅过大，请拆子流程后分别导出 PNG；HTML 已保留。')
    cmd = [executable, '--headless', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
           '--user-data-dir=' + str(work / 'browser-profile'),
           '--screenshot=' + str(out_png), f'--window-size={win_w},{win_h}',
           f'--force-device-scale-factor={scale}', '--default-background-color=FFFFFFFF',
           '--virtual-time-budget=2000', tmp_html.as_uri()]
    kwargs = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
    result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='replace', timeout=60, **kwargs)
    signature = out_png.read_bytes()[:8] if out_png.is_file() else b''
    if result.returncode != 0 or signature != b'\x89PNG\r\n\x1a\n':
        raise RuntimeError(f'PNG 导出失败（退出码 {result.returncode}）：{result.stderr[-1500:]}；工作目录保留在 {work}')
    print(f'OK: {out_png} ({out_png.stat().st_size} bytes); retained work: {work}')
    return out_png


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    parser.add_argument('output')
    parser.add_argument('title')
    parser.add_argument('scale', nargs='?', type=float, default=2)
    parser.add_argument('--browser', help='Chrome/Edge/Chromium 可执行文件路径')
    args = parser.parse_args()
    try:
        export_png(args.input, args.output, args.title, args.scale, args.browser)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, f'FAIL: {exc}\n')


if __name__ == '__main__':
    main()
