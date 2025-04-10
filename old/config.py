import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
# その他の設定項目
CONVERSATION_HISTORY_FILE = "conversation_history.json"
MAX_HISTORY_ENTRIES = 100  # 履歴の最大エントリ数の定義を追加


def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return {}
