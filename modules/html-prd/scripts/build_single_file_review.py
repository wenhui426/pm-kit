#!/usr/bin/env python3
"""Build a standalone review HTML for a self-contained, hash-routed prototype.

The page map is supplied by the agent after page-by-page confirmation. This
helper handles packaging and note synchronization; it does not infer PRD text.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "assets" / "PRD评审版模板.html"
FRAME_TAG = '<iframe id="prototype-frame" title="原交互页面" src="{{FIRST_PAGE_SOURCE}}"></iframe>'
PAGE_ID = re.compile(r"P\d{2,}$", re.IGNORECASE)
# stdout 和 stderr 都要加固：argparse 的错误信息走 stderr，
# 只加固 stdout 会让中文错误在 Windows 默认代码页下变成乱码——恰恰在出错时看不懂。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


# data: 已内联，hash 只是页内跳转，mailto:/tel:/sms:/javascript:/about: 不请求资源——
# 这些都不算外部依赖；其余（相对路径、根相对路径、http、blob、file…）都要拦下来。
INERT_REFERENCE = re.compile(r"^(?:data|mailto|tel|sms|javascript|about):", re.IGNORECASE)


def is_dependency(value: str | None) -> bool:
    cleaned = (value or "").strip()
    if not cleaned or cleaned.startswith("#") or INERT_REFERENCE.match(cleaned):
        return False
    return True


class DependencyScanner(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.dependencies: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag in {"script", "img", "iframe", "video", "audio", "source", "embed"}:
            target = values.get("src")
            if is_dependency(target):
                self.dependencies.append(f"<{tag} src={target!r}>")
        if tag in {"img", "source"} and values.get("srcset"):
            self.dependencies.append(f"<{tag} srcset>")
        if tag == "a" and is_dependency(values.get("href")):
            self.dependencies.append(f"<a href={values['href']!r}>")
        if tag == "form" and values.get("action"):
            self.dependencies.append(f"<form action={values['action']!r}>")
        if tag == "link" and is_dependency(values.get("href")):
            self.dependencies.append(f"<link href={values['href']!r}>")
        if tag == "meta" and values.get("http-equiv", "").lower() == "content-security-policy":
            self.dependencies.append("Content-Security-Policy meta")


def inline_md(value: str) -> str:
    value = html.escape(value)
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_table_separator(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells)


def note_html(text: str, page_id: str) -> str:
    """把已确认的单页 Markdown 正文转成说明面板 HTML。

    支持标题、加粗行、无序/有序列表和管道表格——逐页模板本身以加粗行呈现，
    但用户提供的自由正文常带表格，漏掉会渲染成一堆裸竖线。
    """
    lines = text.strip().splitlines()
    if lines and re.fullmatch(rf"###\s+{re.escape(page_id)}\b.*", lines[0].strip(), re.IGNORECASE):
        lines.pop(0)
    parts: list[str] = []
    in_list = False
    list_tag = "ul"
    table: list[list[str]] = []

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            parts.append(f"</{list_tag}>")
            in_list = False

    def flush_table() -> None:
        nonlocal table
        if not table:
            return
        rows, table = table, []
        head, body = rows[0], rows[1:]
        parts.append("<table><thead><tr>" + "".join(f"<th>{inline_md(c)}</th>" for c in head) + "</tr></thead><tbody>")
        for row in body:
            parts.append("<tr>" + "".join(f"<td>{inline_md(c)}</td>" for c in row) + "</tr>")
        parts.append("</tbody></table>")

    for raw in lines:
        line = raw.strip()
        if len(line) > 1 and line.startswith("|") and line.endswith("|"):
            close_list()
            if not is_table_separator(line):
                table.append(split_table_row(line))
            continue
        flush_table()
        if not line:
            close_list()
            continue
        if line.startswith("- "):
            if not in_list or list_tag != "ul":
                close_list()
                parts.append("<ul>")
                in_list, list_tag = True, "ul"
            parts.append(f"<li>{inline_md(line[2:])}</li>")
            continue
        ordered = re.match(r"\d+\.\s+(.*)", line)
        if ordered:
            if not in_list or list_tag != "ol":
                close_list()
                parts.append("<ol>")
                in_list, list_tag = True, "ol"
            parts.append(f"<li>{inline_md(ordered.group(1))}</li>")
            continue
        close_list()
        if re.fullmatch(r"\*\*[^*]+\*\*", line):
            parts.append(f"<h3>{inline_md(line[2:-2])}</h3>")
        elif line.startswith("# ") or line.startswith("## ") or line.startswith("### "):
            parts.append(f"<h3>{inline_md(line.lstrip('# '))}</h3>")
        else:
            parts.append(f"<p>{inline_md(line)}</p>")
    flush_table()
    close_list()
    return "\n".join(parts)


def read_pages(manifest: Path) -> list[dict[str, str]]:
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"无法读取页面映射 {manifest}：{exc}") from exc
    pages = payload.get("pages") if isinstance(payload, dict) else None
    if not isinstance(pages, list) or not pages:
        raise ValueError("页面映射必须包含非空 pages 列表")
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for entry in pages:
        if not isinstance(entry, dict):
            raise ValueError("每个页面映射必须是对象")
        page_id = str(entry.get("id", "")).upper()
        name = str(entry.get("name", "")).strip()
        raw_match = entry.get("match")
        match = "" if raw_match is None else str(raw_match)
        # navigate 显式为 null 时不能落成字符串 "None"，否则报错信息会指向错误原因
        raw_navigate = entry.get("navigate")
        navigate = match if raw_navigate is None else str(raw_navigate)
        status = str(entry.get("status", "已确认"))
        if not PAGE_ID.fullmatch(page_id):
            raise ValueError(f"页面编号必须是 P01 这种形式（字母 P + 至少两位数字）：{page_id!r}")
        if page_id in seen:
            raise ValueError(f"页面编号重复：{page_id}")
        if not name:
            raise ValueError(f"{page_id} 缺少 name")
        if not match.startswith("#") or not navigate.startswith("#"):
            raise ValueError(f"{page_id} 的 match 和 navigate 必须是 hash 路由")
        if status not in {"已确认", "无需说明（已确认）", "跳过（未确认）"}:
            raise ValueError(f"{page_id} 状态不支持：{status}")
        note_path = entry.get("note")
        if status == "已确认":
            if not isinstance(note_path, str):
                raise ValueError(f"{page_id} 缺少 note 路径")
            note_file = (manifest.parent / note_path).resolve()
            root = manifest.parent.resolve()
            # note 必须留在映射文件所在目录之内，否则一个 ../.. 就能读到任意位置
            if note_file != root and root not in note_file.parents:
                raise ValueError(f"{page_id} 的 note 必须位于页面映射所在目录之内：{note_path}")
            if not note_file.is_file():
                raise ValueError(f"{page_id} 页面说明不存在：{note_file}")
            try:
                body = note_html(note_file.read_text(encoding="utf-8-sig"), page_id)
            except (OSError, UnicodeError) as exc:
                raise ValueError(f"{page_id} 页面说明无法按 UTF-8 读取：{exc}") from exc
        else:
            body = "<p>本页无评审说明</p>" if status.startswith("无需说明") else "<p>本页说明未确认</p>"
        result.append({"id": page_id, "name": name, "match": match, "navigate": navigate, "status": status, "body": body})
        seen.add(page_id)
    return result


def pack_source(source: Path) -> str:
    try:
        text = source.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"无法按 UTF-8 读取原型 {source}：{exc}") from exc
    scanner = DependencyScanner()
    scanner.feed(text)
    if scanner.dependencies:
        raise ValueError("原型包含外部资源，请先完成资源内联或按外部引用模式处理：" + ", ".join(scanner.dependencies))
    if re.search(r"\b(?:fetch|XMLHttpRequest|WebSocket|Worker)\s*\(", text):
        raise ValueError("原型包含动态请求或 Worker，不能直接保证单文件运行")
    if re.search(r"url\(\s*['\"]?(?!data:|#)", text, re.IGNORECASE):
        raise ValueError("原型 CSS 包含资源 URL，请先核对并内联")
    if re.search(r"@import\b", text, re.IGNORECASE):
        raise ValueError("原型包含 CSS @import，请先内联样式")
    if not re.search(r"<head(?:\s[^>]*)?>", text, re.IGNORECASE):
        raise ValueError("原型缺少 <head>，无法插入单文件导航适配")
    bridge = """<base href="about:srcdoc"><script>
    for(const method of ['replaceState','pushState']) {
      const original = history[method].bind(history);
      history[method] = function(state,title,url) {
        try { return original(state,title,url); }
        catch(error) {
          if(typeof url === 'string' && url.startsWith('#')) { location.hash=url; return; }
          throw error;
        }
      };
    }
    </script>"""
    return re.sub(r"<head(?:\s[^>]*)?>", lambda m: m.group(0) + bridge, text, count=1, flags=re.IGNORECASE)


SYNC_SCRIPT = r"""
  const layout = document.documentElement.dataset.reviewLayout;
  const frame = document.querySelector('#prototype-frame');
  const pageName = document.querySelector('#current-page-name');
  const unmapped = document.querySelector('#unmapped-note');
  const buttons = [...document.querySelectorAll('.notes nav button[data-page]')];
  const panels = [...document.querySelectorAll('.note-panel[data-page]')];
  const pageMap = __PAGE_MAP__;
  function clearNotes(message) {
    buttons.forEach(button => button.setAttribute('aria-current','false'));
    panels.forEach(panel => panel.classList.remove('active'));
    pageName.textContent='页面未识别';
    unmapped.textContent=message;
    unmapped.classList.add('active');
  }
  function activatePage(id, updateFrame=true) {
    const page = pageMap.find(item => item.id.toLowerCase()===id);
    const panel = panels.find(item => item.dataset.page===id);
    if(!page || !panel) { clearNotes('当前页面未纳入本次评审范围。'); return; }
    buttons.forEach(button => button.setAttribute('aria-current',button.dataset.page===id?'page':'false'));
    panels.forEach(item => item.classList.toggle('active',item===panel));
    pageName.textContent=panel.dataset.name;
    unmapped.classList.remove('active');
    if(updateFrame) {
      try { frame.contentWindow.location.hash=page.navigate; }
      catch(_) { clearNotes('浏览器阻止切换原型页面。'); }
    }
  }
  function syncFromPrototype() {
    try {
      const hash=frame.contentWindow.location.hash;
      const page=pageMap.find(item => item.match.endsWith('/') ? hash.startsWith(item.match) : hash===item.match);
      if(page) activatePage(page.id.toLowerCase(),false);
      else clearNotes('当前原型页面未纳入本次评审范围。');
    } catch(_) { clearNotes('浏览器阻止读取原型页面，无法自动同步说明。'); }
  }
  buttons.forEach(button => button.addEventListener('click',() => activatePage(button.dataset.page)));
  frame.addEventListener('load',() => {
    try { if(!frame.contentWindow.location.hash) frame.contentWindow.location.hash=pageMap[0].navigate; }
    catch(_) { clearNotes('浏览器阻止初始化原型页面。'); return; }
    syncFromPrototype();
    try { frame.contentWindow.addEventListener('hashchange',syncFromPrototype); }
    catch(_) { clearNotes('浏览器阻止读取原型页面，无法自动同步说明。'); }
  });
  setInterval(syncFromPrototype,300);
  if(layout==='parallel') {
    // 宽度选择要落 localStorage：内置模板有这个行为，生成版不能比模板更差
    const widthKey='html-prd-review-note-width';
    try {
      const savedWidth=localStorage.getItem(widthKey);
      if(savedWidth && /^(30%|40%|50%|\d+px)$/.test(savedWidth)) {
        document.documentElement.style.setProperty('--note-width',savedWidth);
      }
    } catch(_) { /* 本地文件可能禁用存储，宽度调节仍可用。 */ }
    const saveWidth=value => {
      document.documentElement.style.setProperty('--note-width',value);
      try { localStorage.setItem(widthKey,value); } catch(_) { /* 忽略存储限制。 */ }
    };
    document.querySelectorAll('.width-preset').forEach(button => button.addEventListener('click',() => saveWidth(button.dataset.noteWidth)));
    const resizer=document.querySelector('#resizer');
    let dragging=false;
    resizer.addEventListener('pointerdown',event => {
      if(matchMedia('(max-width: 900px)').matches) return;
      dragging=true; resizer.setPointerCapture(event.pointerId);
    });
    resizer.addEventListener('pointermove',event => {
      if(!dragging) return;
      const area=document.querySelector('.workspace').getBoundingClientRect();
      saveWidth(Math.max(320,Math.min(area.width-420,area.right-event.clientX-12))+'px');
    });
    resizer.addEventListener('pointerup',() => { dragging=false; });
    resizer.addEventListener('keydown',event => {
      if(!['ArrowLeft','ArrowRight'].includes(event.key)) return;
      event.preventDefault();
      const oldWidth=document.querySelector('.notes').getBoundingClientRect().width;
      const areaWidth=document.querySelector('.workspace').getBoundingClientRect().width;
      saveWidth(Math.max(320,Math.min(areaWidth-420,oldWidth+(event.key==='ArrowLeft'?20:-20)))+'px');
    });
  }
  if(layout==='drawer') {
    const toggle=document.querySelector('#drawer-toggle');
    const setOpen=open => {
      document.documentElement.classList.toggle('drawer-open',open);
      toggle.setAttribute('aria-expanded',String(open));
    };
    toggle.addEventListener('click',() => setOpen(!document.documentElement.classList.contains('drawer-open')));
    document.querySelector('#drawer-close').addEventListener('click',() => setOpen(false));
    document.querySelector('#backdrop').addEventListener('click',() => setOpen(false));
    document.addEventListener('keydown',event => { if(event.key==='Escape') setOpen(false); });
  }
"""


def build(template: str, source_html: str, pages: list[dict[str, str]], layout: str) -> str:
    nav = "\n".join(
        f'<button type="button" data-page="{p["id"].lower()}" aria-current="{("page" if i == 0 else "false")}">{html.escape(p["id"] + " " + p["name"])}</button>'
        for i, p in enumerate(pages)
    )
    articles = "\n".join(
        f'<article class="note-panel{(" active" if i == 0 else "")}" data-page="{p["id"].lower()}" data-name="{html.escape(p["id"] + " " + p["name"], quote=True)}"><h2>{html.escape(p["id"] + " " + p["name"])}</h2>{p["body"]}</article>'
        for i, p in enumerate(pages)
    )
    values = {
        "REVIEW_LAYOUT": layout,
        "DOCUMENT_TITLE": "PRD评审版｜" + ("并列可调" if layout == "parallel" else "聚焦抽屉"),
        "CONFIRMED_COUNT": str(sum(p["status"] in {"已确认", "无需说明（已确认）"} for p in pages)),
        "PENDING_COUNT": str(sum(p["status"] == "跳过（未确认）" for p in pages)),
        "FIRST_PAGE_NAME": html.escape(pages[0]["id"] + " " + pages[0]["name"]),
        "PAGE_NAV_ITEMS": nav,
        "PAGE_ARTICLES": articles,
    }
    output = template
    for key, value in values.items():
        output = output.replace("{{" + key + "}}", value)
    if FRAME_TAG not in output:
        raise ValueError("HTML 模板缺少预期的 prototype-frame；此工具仅支持内置模板")
    output = output.replace(FRAME_TAG, '<iframe id="prototype-frame" title="原交互页面" srcdoc="' + html.escape(source_html, quote=True) + '"></iframe>')
    mapping = [{key: p[key] for key in ("id", "match", "navigate")} for p in pages]
    script = SYNC_SCRIPT.replace("__PAGE_MAP__", json.dumps(mapping, ensure_ascii=False).replace("</", "<\\/"))
    output, count = re.subn(r"  <script>[\s\S]*?</script>\s*</body>", lambda _: "  <script>" + script + "</script>\n</body>", output, count=1)
    if count != 1 or "{{FIRST_PAGE_SOURCE}}" in output:
        raise ValueError("HTML 模板脚本适配失败")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="生成可独立打开的 hash 路由原型评审版")
    parser.add_argument("--source", required=True, type=Path, help="自包含 HTML 原型")
    parser.add_argument("--pages", required=True, type=Path, help="逐页确认后的页面映射 JSON")
    parser.add_argument("--output-dir", required=True, type=Path, help="开工时指定的输出目录")
    parser.add_argument("--layout", choices=("parallel", "drawer", "both"), required=True)
    parser.add_argument("--force", action="store_true", help="仅对本次任务已记录的同名产物使用")
    args = parser.parse_args()
    if not args.source.is_file() or not args.pages.is_file() or not args.output_dir.is_dir():
        parser.error("source、pages 必须是现有文件；output-dir 必须是已确认的现有目录")
    try:
        pages = read_pages(args.pages.resolve())
        source_html = pack_source(args.source.resolve())
    except ValueError as exc:
        parser.error(str(exc))
    try:
        template = TEMPLATE.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        parser.error(f"无法读取内置模板 {TEMPLATE}：{exc}；scripts 目录不能脱离模块单独复制")
    layouts = ("parallel", "drawer") if args.layout == "both" else (args.layout,)
    targets = [
        args.output_dir / ("PRD评审版.html" if len(layouts) == 1 else "PRD评审版-" + ("并列可调" if layout == "parallel" else "聚焦抽屉") + ".html")
        for layout in layouts
    ]
    for target in targets:
        if target.exists() and not args.force:
            parser.error(f"产物已存在，未覆盖：{target}")
        if target.resolve() == args.source.resolve():
            parser.error("产物路径不能覆盖输入 HTML")
    for layout, target in zip(layouts, targets):
        target.write_text(build(template, source_html, pages, layout), encoding="utf-8")
        print(f"已生成：{target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
