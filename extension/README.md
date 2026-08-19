# 道樞儀表板（VS Code 側欄）

本機 loopback 網頁的側欄殼。**不是市集套件**，也不發佈。

## 先開儀表板

在開源套件根目錄：

```bash
python -m web
```

網址固定 `http://127.0.0.1:8765`。不要用 localhost（有時走 IPv6）。

## 安裝本機套件

VS Code：`Extensions` → `…` → `Install from VSIX…`，或從資料夾載入本目錄。沒有打包 vsix 時，用「Developer: Install Extension from Location」指到 `extension/`。

側欄出現「道樞」。伺服器沒開時 iframe 空白，按「重試」重載 `http://127.0.0.1:8765`。

## 不做

- 不發佈 Marketplace
- 不把 iframe 指到 Type_moon
- 不另開遠端埠
