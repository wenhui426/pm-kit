"""Flowchart import/render/export regression checks; generated directories are retained."""
import importlib.util
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys

BASE = Path(__file__).resolve().parents[1] / 'modules' / 'flowchart-diagram'
sys.path.insert(0, str(BASE / 'scripts'))
import render_bpmn_html as renderer
import bpmn_to_png as png


class FlowchartScriptsTest(unittest.TestCase):
    def setUp(self):
        self.work = Path(tempfile.mkdtemp(prefix='flowchart-test-'))

    def render_xml(self, xml):
        source, target = self.work / 'input.drawio', self.work / 'output.html'
        source.write_text(xml, encoding='utf-8')
        renderer.render(source, target, '流程 <草稿>')
        return target.read_text(encoding='utf-8')

    def test_original_examples_render_and_xml_newlines_are_split(self):
        examples = re.findall(r'```xml\s*\n(.*?)```', (BASE / 'EXAMPLES.md').read_text(encoding='utf-8'), re.S)
        self.assertGreaterEqual(len(examples), 5)
        for i, xml in enumerate(examples):
            source, target = self.work / f'{i}.drawio', self.work / f'{i}.html'
            source.write_text(xml, encoding='utf-8')
            renderer.render(source, target, '示例')
            html = target.read_text(encoding='utf-8')
            self.assertIn('<svg', html)
            self.assertNotIn('src="http', html)
        first = (self.work / '0.html').read_text(encoding='utf-8')
        self.assertIn('>通知申请人</text>', first)
        approved_y = re.search(r'<text[^>]*\sy="([^"]+)"[^>]*>批准</text>', first).group(1)
        rejected_y = re.search(r'<text[^>]*\sy="([^"]+)"[^>]*>拒绝</text>', first).group(1)
        self.assertNotEqual(approved_y, rejected_y, '分支标签不应重叠在共用起点')

    def test_waypoints_and_parent_coordinates_are_preserved(self):
        html = self.render_xml('''<mxfile><diagram><mxGraphModel><root>
          <mxCell id="0"/><mxCell id="1" parent="0"/>
          <mxCell id="a" vertex="1" parent="1"><mxGeometry x="60" y="20" width="80" height="40"/></mxCell>
          <mxCell id="b" vertex="1" parent="1"><mxGeometry x="300" y="20" width="80" height="40"/></mxCell>
          <mxCell id="back" edge="1" parent="1" source="b" target="a" value="退回" style="exitX=0.5;exitY=1;entryX=0.5;entryY=1;strokeColor=#b85450;">
            <mxGeometry relative="1"><Array as="points"><mxPoint x="340" y="90"/><mxPoint x="100" y="90"/></Array></mxGeometry>
          </mxCell></root></mxGraphModel></diagram></mxfile>''')
        self.assertIn('L 310 100 L 70 100', html)
        self.assertIn('流程 &lt;草稿&gt;', html)

    def test_dangling_edge_fails_instead_of_silently_disappearing(self):
        with self.assertRaisesRegex(ValueError, 'source|target|端点'):
            self.render_xml('''<mxfile><diagram><mxGraphModel><root>
              <mxCell id="e" edge="1" source="missing" target="missing2"/>
              </root></mxGraphModel></diagram></mxfile>''')
        self.assertFalse((self.work / 'output.html').exists())

    def test_compressed_diagram_is_rejected_with_an_explanation(self):
        with self.assertRaisesRegex(ValueError, '压缩|未压缩'):
            self.render_xml('<mxfile><diagram>compressed-data</diagram></mxfile>')

    def test_matrix_stage_titles_attached_to_canvas_are_rendered(self):
        html = self.render_xml('''<mxfile><diagram><mxGraphModel><root>
          <mxCell id="header" vertex="1" parent="1" style="text;" value="审批阶段"><mxGeometry x="20" y="10" width="180" height="40"/></mxCell>
          </root></mxGraphModel></diagram></mxfile>''')
        self.assertIn('>审批阶段</text>', html)

    def test_missing_browser_is_an_explicit_failure(self):
        with patch.object(png, 'find_browser', return_value=None):
            with self.assertRaisesRegex(RuntimeError, '浏览器|Chrome|Edge'):
                png.export_png(self.work / 'input.drawio', self.work / 'out.png', '演示')
        self.assertFalse((self.work / 'out.png').exists())

    def test_existing_png_cannot_be_mistaken_for_a_successful_export(self):
        target = self.work / 'out.png'
        target.write_bytes(b'old file')
        with self.assertRaises(FileExistsError):
            png.export_png(self.work / 'input.drawio', target, '演示')
        self.assertEqual(target.read_bytes(), b'old file')


if __name__ == '__main__':
    unittest.main(verbosity=2)
