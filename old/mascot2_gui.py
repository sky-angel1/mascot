import sys
import os
import time
import json
import requests
import random
from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration
from deep_translator import GoogleTranslator

try:
    from PyQt6.QtWidgets import (
        QApplication,
        QLabel,
        QWidget,
        QTextEdit,
        QVBoxLayout,
        QLineEdit,
    )
    from PyQt6.QtGui import QPixmap
    from PyQt6.QtCore import Qt, QPoint, QTimer

    PYQT_AVAILABLE = True
except ModuleNotFoundError:
    print("Error: PyQt6 module is not installed.")
    PYQT_AVAILABLE = False

CONFIG_FILE = "config.json"
CONVERSATION_HISTORY_FILE = "conversation_history.json"

# 設定ファイル読み込み
try:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
except Exception as e:
    print(f"設定ファイルの読み込みに失敗しました: {e}")
    config = {}

MAX_HISTORY_ENTRIES = config.get("MAX_HISTORY_ENTRIES", 100)
conversation_history = []
EXIT_KEYWORDS = ["exit", "bye", "quit", "ばいばい", "さようなら", "またあとで"]

# Hugging Face のモデルをロード
tokenizer = BlenderbotTokenizer.from_pretrained("facebook/blenderbot-400M-distill")
model = BlenderbotForConditionalGeneration.from_pretrained(
    "facebook/blenderbot-400M-distill"
)


# Deep Translator を使用した翻訳関数
def translate_to_english(text):
    try:
        translated = GoogleTranslator(source="ja", target="en").translate(text)
        return translated if translated else text  # 空文字列対策
    except Exception as e:
        print(f"翻訳エラー: {e}")
        return text[:500]  # 長文入力対策


def translate_to_japanese(text):
    try:
        translated = GoogleTranslator(source="en", target="ja").translate(text)
        return translated if translated else text  # 空文字列対策
    except Exception as e:
        print(f"翻訳エラー: {e}")
        return text[:500]  # 長文入力対策


def load_conversation_history():
    try:
        if os.path.exists(CONVERSATION_HISTORY_FILE):
            with open(CONVERSATION_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading history: {e}")
    return []


def save_conversation_history(history):
    try:
        with open(CONVERSATION_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving history: {e}")


def generate_ai_response(user_input):
    # 日本語→英語 翻訳
    english_input = translate_to_english(user_input)
    inputs = tokenizer(english_input, return_tensors="pt")
    reply_ids = model.generate(**inputs)
    response = tokenizer.decode(reply_ids[0], skip_special_tokens=True)

    # 英語→日本語 翻訳
    return translate_to_japanese(response)


def fetch_weather():
    url = "https://wttr.in/?format=%C+%t"  # 天気と気温を取得
    try:
        response = requests.get(url, timeout=5)  # タイムアウト5秒を設定
        return f"現在の天気: {response.text}"
    except requests.RequestException as e:
        return f"天気情報の取得に失敗しました: {e}"


if PYQT_AVAILABLE:
    from PyQt6.QtWidgets import QLabel


class Mascot(QWidget):
    def initUI(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # キャラ画像をセット
        self.label = QLabel(self)
        self.pixmap_normal = QPixmap("mascot.png")  # 通常の画像
        self.pixmap_happy = QPixmap("mascot_happy.png")  # 反応した時の画像
        self.pixmap_angry = QPixmap("mascot_angry.png")  # 怒った時の画像
        self.pixmap_blink = QPixmap("mascot_blink.png")  # 瞬き画像
        self.label.setPixmap(self.pixmap_normal)
        self.resize(self.pixmap_normal.size())

    def process_input(self):
        user_input = self.input_box.text().strip()
        if not user_input:
            return

    def speak_console(self, user_input):
        
        # 表情変化ロジック
        original_pixmap = self.label.pixmap()

        if "怒" in user_input:
            self.label.setPixmap(self.pixmap_angry)
            QTimer.singleShot(1500, lambda: self.label.setPixmap(original_pixmap))
        elif any(kw in user_input for kw in ["笑", "楽"]):
            self.label.setPixmap(self.pixmap_happy)
            QTimer.singleShot(1500, lambda: self.label.setPixmap(original_pixmap))
        elif "驚" in user_input or "びっくり" in user_input:
            self.label.setPixmap(self.pixmap_blink)
            QTimer.singleShot(800, lambda: self.label.setPixmap(original_pixmap))

        # 即時反映のために必要
        QApplication.processEvents()

        # 以下の2行を削除
        # time.sleep(1.5)
        # self.label.setPixmap(self.pixmap_normal)

    def __init__(self):
        super().__init__()
        self.initUI()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.random_move)
        self.timer.start(30000)  # 30秒ごとに移動

        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.blink)
        self.blink_timer.start(15000)  # 15秒ごとに瞬き

    def random_move(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        max_x = screen_geometry.width() - self.width()
        max_y = screen_geometry.height() - self.height()
        new_x = random.randint(0, max_x)
        new_y = random.randint(0, max_y)
        self.move(new_x, new_y)

    def blink(self):
        self.label.setPixmap(self.pixmap_blink)
        QApplication.processEvents()
        time.sleep(1.0)
        self.label.setPixmap(self.pixmap_normal)


class Mascot2(QWidget):
    def __init__(self):
        super().__init__()
        self.drag_position = QPoint()
        self.initUI()

    def initUI(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(300, 400)

        self.layout = QVBoxLayout()
        # 透明なタイトルバー風のラベルを追加
        self.title_bar = QLabel("")
        self.title_bar.setFixedHeight(30)
        # 視認性が必要なら背景色などを設定します
        self.title_bar.setStyleSheet("background-color: rgba(0, 0, 0, 50);")
        # タイトルバーに対してマウスイベントをオーバーライド
        self.title_bar.mousePressEvent = self.titleBarMousePressEvent
        self.title_bar.mouseMoveEvent = self.titleBarMouseMoveEvent

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setMinimumHeight(300)

        self.input_box = QLineEdit()
        self.input_box.returnPressed.connect(self.process_input)

        self.layout.addWidget(self.title_bar)
        self.layout.addWidget(self.chat_history)
        self.layout.addWidget(self.input_box)
        self.setLayout(self.layout)

    def titleBarMousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def titleBarMouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def speak_console(self, user_input):
        responses = {
            "こんにちは": "こんにちは！今日も頑張ろうね！",
            "元気？": "もちろん！あなたはどう？",
            "何してるの？": "お話ししてるよ！",
            "Pythonって楽しい？": "もちろん！Python最高だよ！",
            "怒る": "そんなこと言われると、怒っちゃうよ！",
            "笑う": "ふふふ、楽しいね！",
            "びっくり": "わぁ！びっくりした！",
            "天気": fetch_weather(),
        }

        # AIの返答を取得
        if user_input == "天気":
            response = fetch_weather()
        else:
            response = responses.get(user_input, generate_ai_response(user_input))

        # self.update_chat_history(f"あなた: {user_input}\n🐱: {response}")
        text = generate_ai_response(user_input)
        self.update_chat_history(f"あなた: {user_input}\n🐱: {text}")

        # チャット履歴を更新
        conversation_history.append(
            {
                "timestamp": time.time(),
                "user_input": user_input,
                "mascot_response": text,
            }
        )
        save_conversation_history(conversation_history)

    def process_input(self):
        user_input = self.input_box.text().strip()
        if not user_input:
            return

        # 終了キーワードチェック（部分一致）
        if any(keyword in user_input for keyword in EXIT_KEYWORDS):
            save_conversation_history(conversation_history)
            sys.exit("終了キーワードを検知しました")

        self.speak_console(user_input)
        self.input_box.clear()

    def update_chat_history(self, new_message):
        current_text = self.chat_history.toPlainText().split("\n")
        if len(current_text) >= 10:
            current_text = current_text[-9:]
        current_text.append(new_message)
        self.chat_history.setPlainText("\n".join(current_text))


if __name__ == "__main__":
    conversation_history = load_conversation_history()
    if PYQT_AVAILABLE:
        app = QApplication(sys.argv)
        mascot = Mascot()
        mascot.show()  # テキストBOX表示
        mascot2 = Mascot2()
        mascot2.show()  # キャラクターを表示
        sys.exit(app.exec())
    else:
        print("PyQt6 is required. Exiting...")
