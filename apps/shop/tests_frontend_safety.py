
from pathlib import Path

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parents[2]


class FrontendSafetyRegressionTests(SimpleTestCase):
    def read_project_file(self, relative_path):
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def extract_js_function(self, text, signature):
        start = text.index(signature)
        open_brace = text.index("{", start)
        depth = 0
        quote = None
        escape = False

        for index in range(open_brace, len(text)):
            char = text[index]

            if quote:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == quote:
                    quote = None
                continue

            if char in ("'", '"', "`"):
                quote = char
                continue

            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : index + 1]

        self.fail(f"Could not extract JS function: {signature}")

    def test_live_search_builds_results_with_dom_nodes(self):
        for relative_path in (
            "apps/shop/static/js/header.js",
            "static/main.js",
        ):
            with self.subTest(path=relative_path):
                text = self.read_project_file(relative_path)
                block = self.extract_js_function(text, "function renderResults")

                self.assertIn("document.createElement", block)
                self.assertIn("textContent", block)
                self.assertIn("safeSameOriginUrl", block)
                self.assertNotIn("htmlContent", block)
                self.assertNotIn("innerHTML = htmlContent", block)

    def test_live_search_blocks_cross_origin_urls(self):
        for relative_path in (
            "apps/shop/static/js/header.js",
            "static/main.js",
        ):
            with self.subTest(path=relative_path):
                text = self.read_project_file(relative_path)
                block = self.extract_js_function(text, "function renderResults")

                self.assertIn("url.origin !== window.location.origin", block)
                self.assertIn('return "#"', block)

    def test_toast_message_uses_text_content(self):
        text = self.read_project_file("static/main.js")
        block = self.extract_js_function(text, "window.showToast")

        self.assertIn("document.createElement", block)
        self.assertIn("messageElement.textContent", block)
        self.assertNotIn("innerHTML", block)

    def test_admin_chart_json_is_escaped_before_parsing(self):
        text = self.read_project_file("templates/admin/index.html")

        self.assertIn("chart|escapejs", text)
        self.assertNotIn("JSON.parse('{{ chart|safe }}')", text)
