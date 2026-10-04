import copy
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from bshl.share import render_svg, write_share
from test_workspace import card


class ShareTests(unittest.TestCase):
    def test_labels_provenance_and_html_escape_survive_export(self):
        value = card()
        value["source"]["url"] = 'https://example.invalid/?q=<script>&x="hello"'
        svg = render_svg(value)
        root = ET.fromstring(svg)
        content = " ".join(root.itertext())
        for expected in ("MOCK / SYNTHETIC", value["analysis_id"], value["as_of"], value["rule_version"], "Invalidation", "No orders"):
            self.assertIn(expected, content)
        self.assertNotIn("<script>", svg)
        self.assertEqual(len(root.findall(".//{http://www.w3.org/2000/svg}script")), 0)

    def test_share_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "share.svg"
            write_share(card(), path)
            write_share(card(), path)
            changed = card({"target_price": 150})
            with self.assertRaises(ValueError):
                write_share(changed, path)
