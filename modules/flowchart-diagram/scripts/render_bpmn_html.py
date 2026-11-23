# -*- coding: utf-8 -*-
"""
mxfile (draw.io XML) 子集渲染器：把流程图 XML 渲染为内嵌 SVG 的自包含 HTML。
支持元素：ellipse(事件)、rounded rect(任务)、rhombus(网关)、text(标记)、orthogonal edge(连线)。
用法：python render_bpmn_html.py <输入.drawio/.xml> <输出.html> <标题>
"""
import sys, io, html
from pathlib import Path
import xml.etree.ElementTree as ET

def parse_style(style):
    d = {}
    for kv in (style or '').split(';'):
        if '=' in kv:
            k, v = kv.split('=', 1)
            d[k.strip()] = v.strip()
        elif kv.strip():
            d[kv.strip()] = True
    return d

def esc(t):
    return html.escape(str(t), quote=True)

def render(in_path, out_path, title):
    if Path(out_path).exists():
        raise FileExistsError(f'输出文件已存在，请使用新路径：{out_path}')
    tree = ET.parse(in_path)
    root_mx = tree.getroot()
    diagrams = root_mx.findall('diagram')
    if len(diagrams) != 1:
        raise ValueError('一次仅渲染一个 diagram；多页文件请先拆成单页。')
    diagram = diagrams[0]
    model = diagram.find('mxGraphModel')
    if model is None:
        raise ValueError('需要未压缩的 draw.io XML（包含 mxGraphModel）；压缩文件请先导出未压缩 XML。')
    cells_root = model.find('root')
    if cells_root is None:
        raise ValueError('mxGraphModel 缺少 root。')

    vertices, edges = {}, []
    for cell in cells_root.findall('mxCell'):
        cid = cell.get('id')
        geo = cell.find('mxGeometry')
        g = None
        if geo is not None:
            g = {'x': float(geo.get('x', 0)), 'y': float(geo.get('y', 0)),
                 'w': float(geo.get('width', 0)), 'h': float(geo.get('height', 0))}
        if cell.get('vertex') == '1':
            vertices[cid] = {'style': parse_style(cell.get('style')), 'value': cell.get('value') or '',
                             'geo': g, 'parent': cell.get('parent')}
        elif cell.get('edge') == '1':
            points = geo.findall('./Array[@as="points"]/mxPoint') if geo is not None else []
            edges.append({'id': cid, 'style': parse_style(cell.get('style')),
                          'value': cell.get('value') or '',
                          'source': cell.get('source'), 'target': cell.get('target'),
                          'parent': cell.get('parent'),
                          'points': [(float(p.get('x', 0)), float(p.get('y', 0))) for p in points]})

    for e in edges:
        if e['source'] not in vertices or e['target'] not in vertices:
            raise ValueError(f"连线 {e['id']} 的 source/target 端点不存在。")

    def abs_geo(cid):
        """累加父容器偏移得到绝对坐标"""
        x, y = 0.0, 0.0
        cur = vertices.get(cid)
        g = dict(cur['geo']) if cur and cur['geo'] else {'x': 0, 'y': 0, 'w': 0, 'h': 0}
        visited = {cid}
        while cur and cur['parent'] not in (None, '0', '1'):
            if cur['parent'] in visited:
                raise ValueError(f'容器 parent 存在循环：{cid}')
            visited.add(cur['parent'])
            p = vertices.get(cur['parent'])
            if not p or not p['geo']:
                break
            x += p['geo']['x']; y += p['geo']['y']
            cur = p
        g['x'] += x; g['y'] += y
        return g

    # 计算 bounds
    minx = miny = float('inf'); maxx = maxy = float('-inf')
    for cid, v in vertices.items():
        if not v['geo']:
            continue
        g = abs_geo(cid)
        minx = min(minx, g['x']); miny = min(miny, g['y'])
        maxx = max(maxx, g['x'] + g['w']); maxy = max(maxy, g['y'] + g['h'])
    if minx == float('inf'):
        raise ValueError('没有可渲染的顶点。')
    for e in edges:
        pg = abs_geo(e['parent']) if e['parent'] in vertices else {'x': 0, 'y': 0}
        e['points'] = [(px + pg['x'], py + pg['y']) for px, py in e['points']]
        for px, py in e['points']:
            minx, miny = min(minx, px), min(miny, py)
            maxx, maxy = max(maxx, px), max(maxy, py)
    pad = 30
    W = maxx - minx + pad * 2; H = maxy - miny + pad * 2

    svg = []
    containers = []   # 泳道/池容器(最底层)
    edges_svg = []    # 连线(容器之上、元素之下)
    # defs: 箭头 marker
    svg.append('<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
               'markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
               '<path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/></marker>'
               '<marker id="open-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10" fill="none" stroke="context-stroke"/></marker>'
               '<marker id="start-circle" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6"><circle cx="5" cy="5" r="4" fill="white" stroke="context-stroke"/></marker></defs>')

    # ---- 连线(画在容器上、元素下) ----
    for e in edges:
        s, t = vertices.get(e['source']), vertices.get(e['target'])
        if not s or not t:
            continue
        sg, tg = abs_geo(e['source']), abs_geo(e['target'])
        sx1, sy1 = sg['x'] - minx + pad, sg['y'] - miny + pad
        tx1, ty1 = tg['x'] - minx + pad, tg['y'] - miny + pad
        sx2, sy2 = sx1 + sg['w'], sy1 + sg['h']
        tx2, ty2 = tx1 + tg['w'], ty1 + tg['h']
        scy, tcy = (sy1 + sy2) / 2, (ty1 + ty2) / 2
        stroke = e['style'].get('strokeColor', '#666666')
        dashed = ' stroke-dasharray="6 4"' if 'dashed=1' in (e['style'].get('dashed') and 'dashed=1' or '') or e['style'].get('dashed') == '1' else ''
        st = e['style']
        start = (sx1 + sg['w'] * float(st.get('exitX', 1)), sy1 + sg['h'] * float(st.get('exitY', .5)))
        end = (tx1 + tg['w'] * float(st.get('entryX', 0)), ty1 + tg['h'] * float(st.get('entryY', .5)))
        if e['points']:
            pts = [start] + [(px-minx+pad, py-miny+pad) for px, py in e['points']] + [end]
        elif tx1 < sx2:
            # 回退流绕到元素下方，避免从节点内部穿过。
            low = max(sy2, ty2) + 25
            pts = [(sx1, scy), (sx1-20, scy), (sx1-20, low), (tx2+20, low), (tx2+20, tcy), (tx2, tcy)]
        elif abs(scy - tcy) < 2:
            pts = [start, end]
        else:
            midx = (sx2 + tx1) / 2
            pts = [start, (midx, start[1]), (midx, end[1]), end]
        H = max(H, max(py for _, py in pts) + pad)
        W = max(W, max(px for px, _ in pts) + pad)
        d = ' '.join(f'{"M" if i == 0 else "L"} {px:.0f} {py:.0f}' for i, (px, py) in enumerate(pts))
        # 等长分支选择靠近目标的线段，避免通过/拒绝标签叠在共用起点。
        a, b = max(reversed(list(zip(pts, pts[1:]))), key=lambda pair: abs(pair[0][0]-pair[1][0]))
        lx, ly = (a[0]+b[0])/2, (a[1]+b[1])/2-8
        label_anchor = 'middle'
        if abs(a[0]-b[0]) < len(e['value']) * 12 + 8:
            vertical = [(p, q) for p, q in zip(pts, pts[1:]) if abs(p[0]-q[0]) < 1 and abs(p[1]-q[1]) >= 25]
            if vertical:
                p, q = max(vertical, key=lambda pair: abs(pair[0][1]-pair[1][1]))
                lx, ly, label_anchor = p[0]-8, (p[1]+q[1])/2+4, 'end'
        arrow = st.get('endArrow', 'block')
        marker = '' if arrow == 'none' else f' marker-end="url(#{"open-arrow" if arrow == "open" else "arrow"})"'
        if st.get('startArrow') == 'oval':
            marker += ' marker-start="url(#start-circle)"'
        edges_svg.append(f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="1.5" '
                   f'{marker}{dashed}/>')
        if e['value']:
            edges_svg.append(f'<text x="{lx:.0f}" y="{ly:.0f}" font-size="12" fill="#444" '
                       f'text-anchor="{label_anchor}" font-family="Microsoft YaHei,sans-serif">{esc(e["value"])}</text>')

    # ---- 顶点 ----
    for cid, v in vertices.items():
        st = v['style']
        g = abs_geo(cid)
        x, y = g['x'] - minx + pad, g['y'] - miny + pad
        w, h = g['w'], g['h']
        fill = st.get('fillColor', '#ffffff')
        stroke = st.get('strokeColor', '#666666')
        sw = st.get('strokeWidth', '2')
        if st.get('swimlane'):
            # 泳道容器: 画矩形 + 左侧标题栏竖排文字
            containers.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" '
                       f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
            if v['value']:
                strip = float(st.get('startSize', 30))
                cx, cy = x + strip/2, y + h/2
                containers.append(f'<text x="{cx:.0f}" y="{cy:.0f}" font-size="14" font-weight="bold" fill="#333" '
                           f'text-anchor="middle" font-family="Microsoft YaHei,sans-serif" '
                           f'transform="rotate(-90 {cx:.0f} {cy:.0f})">{esc(v["value"])}</text>')
                # 标题栏分隔线
                containers.append(f'<line x1="{x+strip:.0f}" y1="{y:.0f}" x2="{x+strip:.0f}" y2="{y+h:.0f}" '
                           f'stroke="{stroke}" stroke-width="1"/>')
            continue
        if st.get('ellipse'):
            svg.append(f'<ellipse cx="{x+w/2:.0f}" cy="{y+h/2:.0f}" rx="{w/2:.0f}" ry="{h/2:.0f}" '
                       f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
            if st.get('double') == '1':
                svg.append(f'<ellipse cx="{x+w/2:.0f}" cy="{y+h/2:.0f}" rx="{max(w/2-4,1):.0f}" ry="{max(h/2-4,1):.0f}" fill="none" stroke="{stroke}" stroke-width="1"/>')
        elif st.get('rhombus'):
            cx, cy = x + w/2, y + h/2
            pts = f'{x:.0f},{cy:.0f} {cx:.0f},{y:.0f} {x+w:.0f},{cy:.0f} {cx:.0f},{y+h:.0f}'
            svg.append(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
        elif st.get('text'):
            # 同时支持网关子标记与画布上的矩阵阶段标题。
            fs = float(st.get('fontSize', 14))
            fw = 'bold' if st.get('fontStyle') in ('1', '3', '5', '7') else 'normal'
            lines = v['value'].replace('&#xa;', '\n').splitlines() or ['']
            for i, line in enumerate(lines):
                cy = y + h/2 - (len(lines)-1)*9 + i*18 + fs/3
                svg.append(f'<text x="{x+w/2:.0f}" y="{cy:.0f}" font-size="{fs}" font-weight="{fw}" fill="#333" text-anchor="middle" font-family="Microsoft YaHei,sans-serif">{esc(line)}</text>')
            continue
        else:
            rx = 10 if st.get('rounded') else 0
            svg.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{rx}" '
                       f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
        # 顶点自身文字(&#xa; 换行)
        if v['value']:
            lines = v['value'].replace('&#xa;', '\n').splitlines() or ['']
            fs = 13
            cx, cy = x + w/2, y + h/2
            dy0 = cy - (len(lines) - 1) * 9 + 4
            for i, ln in enumerate(lines):
                svg.append(f'<text x="{cx:.0f}" y="{dy0 + i*18:.0f}" font-size="{fs}" fill="#333" '
                           f'text-anchor="middle" font-family="Microsoft YaHei,sans-serif">{esc(ln)}</text>')

    # 渲染层级: defs + 泳道容器(底) + 连线(中) + 元素(顶)
    svg_body = '\n'.join([svg[0]] + containers + edges_svg + svg[1:])
    html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} - BPMN</title>
<style>
  body{{margin:0;background:#f5f6f8;font-family:"Microsoft YaHei",sans-serif}}
  .bar{{background:#1a2b4a;color:#fff;padding:12px 20px;font-size:14px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px}}
  .bar span{{opacity:.8;font-size:12px}}
  .graph{{background:#fff;margin:16px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,.08);overflow-x:auto}}
  .legend{{margin:0 16px 16px;padding:10px 16px;background:#fff;border-radius:6px;font-size:12px;color:#555;box-shadow:0 2px 8px rgba(0,0,0,.06)}}
  .legend b{{display:inline-block;width:12px;height:12px;border-radius:50%;margin:0 4px -1px 12px;border:1.5px solid}}
</style>
</head>
<body>
<div class="bar"><b>{esc(title)}（BPMN 风格流程图）</b><span>自包含 HTML · 内嵌 SVG 矢量渲染 · 离线可用 · 可编辑源文件为 .drawio</span></div>
<div class="graph">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" style="width:100%;height:auto;max-width:{W:.0f}px">
{svg_body}
</svg>
</div>
<div class="legend">图例：<b style="background:#d5e8d4;border-color:#82b366"></b>开始事件
<b style="background:#dae8fc;border-color:#6c8ebf;border-radius:3px"></b>任务
<b style="background:#fff2cc;border-color:#d6b656;transform:rotate(45deg)"></b>排他网关
<b style="background:#f8cecc;border-color:#b85450"></b>结束/拒绝</div>
</body>
</html>'''
    with io.open(out_path, 'x', encoding='utf-8', newline='\n') as stream:
        stream.write(html)
    print(f'OK: {out_path}  (SVG {W:.0f}x{H:.0f})')

if __name__ == '__main__':
    render(sys.argv[1], sys.argv[2], sys.argv[3])
