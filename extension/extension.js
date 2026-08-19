const vscode = require("vscode");

const DASHBOARD = "http://127.0.0.1:8765";

function sidebarHtml() {
  return `<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; frame-src http://127.0.0.1:8765; style-src 'unsafe-inline'; script-src 'unsafe-inline';">
  <style>
    html, body { margin: 0; height: 100%; background: #0a120e; color: #d8e4dc; font-family: "Microsoft JhengHei", sans-serif; }
    #bar { padding: .6rem .8rem; font-size: .78rem; border-bottom: 1px solid #3a4a3f; }
    #bar button { background: #121c18; color: #8fbfa8; border: 1px solid #3a4a3f; padding: .2rem .5rem; }
    iframe { width: 100%; height: calc(100% - 2.4rem); border: 0; background: #0a120e; }
  </style>
</head>
<body>
  <div id="bar">儀表板未開時，在套件根目錄執行 python -m web。 <button id="retry" type="button">重試</button></div>
  <iframe id="frame" title="道樞" src="${DASHBOARD}"></iframe>
  <script>
    const frame = document.getElementById("frame");
    document.getElementById("retry").addEventListener("click", () => {
      frame.src = "${DASHBOARD}";
    });
  </script>
</body>
</html>`;
}

class SidebarProvider {
  resolveWebviewView(webviewView) {
    webviewView.webview.options = {
      enableScripts: true,
    };
    webviewView.webview.html = sidebarHtml();
  }
}

function activate(context) {
  const provider = new SidebarProvider();
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("daozhu.sidebar", provider, {
      webviewOptions: { retainContextWhenHidden: true },
    })
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
