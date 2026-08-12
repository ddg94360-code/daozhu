"""道樞設定載入：讀取可選的 config.yaml，提供全模組共用設定。

支援欄位（對應道樞建置文件第四章 CONFIG.yaml 規格）：
- timezone:            "Asia/Taipei"   # 顯示時區（預設本機）
- currency:            "TWD"           # 記帳貨幣，用於週報/摘要顯示符號
- review_weekday:      6               # 週報日（0=週一 ... 6=週日）
- review_time:         "21:00"         # 週報輸出時間
- energy_analysis_days: 7              # 精力分析所需累積天數
- high_speed_threshold: 80             # 精簡模式觸發門檻（字/分鐘，供 skill 層用）

yaml 為可選依賴：未安裝 pyyaml 時靜默使用預設值，不影響其他功能。
"""
import os

DEFAULTS: dict = {
    "timezone": "Asia/Taipei",
    "currency": "",
    "review_weekday": 6,
    "review_time": "21:00",
    "energy_analysis_days": 7,
    "high_speed_threshold": 80,
}

_CURRENCY_SYMBOLS: dict = {
    "TWD": "NT$", "HKD": "HK$", "USD": "$", "JPY": "¥",
    "CNY": "¥", "EUR": "€", "GBP": "£", "KRW": "₩",
}

_config: dict | None = None


def _config_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")


def load(path: str | None = None) -> dict:
    """載入設定（只載入一次；顯式傳 path 可強制重載）。回傳合併後的 dict。"""
    global _config
    cfg = dict(DEFAULTS)
    p = path or _config_path()
    if os.path.exists(p):
        try:
            import yaml  # 可選依賴
            with open(p, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            # 支援頂層 daozhu: 命名空間或直接頂層
            merged = data.get("daozhu", data)
            if isinstance(merged, dict):
                cfg.update({k: v for k, v in merged.items() if k in DEFAULTS})
        except (ImportError, OSError, ValueError):
            pass  # 無 pyyaml 或格式錯誤 → 用預設
    _config = cfg
    return cfg


def get(key: str, default=None):
    """讀取單一設定（惰性載入）。"""
    if _config is None:
        load()
    return _config.get(key, default) if _config else default


def currency_symbol() -> str:
    """貨幣符號（如 NT$）。未設定 currency 時回傳空字串。"""
    code = get("currency", "")
    if not code:
        return ""
    return _CURRENCY_SYMBOLS.get(code, f"{code} ")
