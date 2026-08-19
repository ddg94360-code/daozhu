"""第六期 I+J：左軌殼、桌面真視窗旗標、vsix 不入庫。"""
import inspect
import os

from web import desktop


def _root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_three_pages_have_left_rail(client):
    for path in ("/", "/cabinet", "/xinjing"):
        html = client.get(path).text
        assert 'id="rail"' in html
        assert 'id="rail-status"' in html
        assert 'id="theme-select"' in html
        assert "127.0.0.1:8765" in html
        assert 'href="/"' in html
        assert 'href="/cabinet"' in html
        assert 'href="/xinjing"' in html
        assert 'class="nav"' not in html


def test_css_collapses_rail_under_720(client):
    css = client.get("/static/app.css").text
    assert "id=\"rail\"" not in css
    assert ".rail" in css
    assert "720px" in css
    assert "48px" in css


def test_theme_select_still_on_three_pages(client):
    keys = ("daoist", "confucian", "legalist", "strategist", "taiji")
    for path in ("/", "/cabinet", "/xinjing"):
        html = client.get(path).text
        assert 'id="theme-select"' in html
        for key in keys:
            assert f'value="{key}"' in html


def test_desktop_default_stays_browser_shell():
    src = inspect.getsource(desktop)
    assert "webbrowser" in src
    assert "--window" in src
    assert "第四期不內嵌視窗" in src
    assert "localhost" not in src
    assert "127.0.0.1" in src


def test_desktop_window_flag_imports_webview():
    src = inspect.getsource(desktop)
    assert "import webview" in src
    assert "1100" in src
    assert "800" in src
    assert "未裝 pywebview" in src
    assert "只開視窗" in src or "埠已被占用" in src


def test_extension_package_has_license():
    pkg_path = os.path.join(_root(), "extension", "package.json")
    import json

    pkg = json.loads(open(pkg_path, encoding="utf-8").read())
    assert pkg["version"] == "0.4.0"
    assert pkg.get("license")
    js = open(os.path.join(_root(), "extension", "extension.js"), encoding="utf-8").read()
    assert "127.0.0.1:8765" in js
    assert "localhost" not in js


def test_gitignore_excludes_vsix():
    text = open(os.path.join(_root(), ".gitignore"), encoding="utf-8").read()
    assert "*.vsix" in text


def test_cabinet_page_is_workspace_layout(client):
    html = client.get("/cabinet").text
    assert 'class="workspace"' in html
    assert 'id="cabinet-compose"' in html
    assert 'id="cabinet-stage-pane"' in html
    css = client.get("/static/app.css").text
    assert ".workspace" in css
    assert "minmax(0, 1.6fr)" in css or "1.6fr" in css


def test_xinjing_page_is_workspace_layout(client):
    html = client.get("/xinjing").text
    assert 'class="workspace"' in html
    assert 'id="xinjing-compose"' in html
    assert 'id="xinjing-stage"' in html
    css = client.get("/static/app.css").text
    assert "#xinjing-stage" in css
    assert "flex: 1" in css


def test_requirements_web_lists_pywebview():
    text = open(os.path.join(_root(), "mcp", "requirements-web.txt"), encoding="utf-8").read()
    assert "pywebview" in text
    mcp_req = open(os.path.join(_root(), "mcp", "requirements.txt"), encoding="utf-8").read()
    assert "pywebview" not in mcp_req
