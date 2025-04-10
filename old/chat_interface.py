import os  # os モジュールをインポート
import json
import threading
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QLineEdit,
    QMessageBox,
    QApplication,
)
from PyQt6.QtCore import Qt
from deep_translator import GoogleTranslator

# from weather import get_weather
from old.config import load_config, CONVERSATION_HISTORY_FILE, MAX_HISTORY_ENTRIES
from old.error_handling import handle_error
from datetime import datetime  # datetime のインポートを追加
from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration
from deep_translator import GoogleTranslator

# 定数の定義
EXIT_KEYWORDS = ["exit", "bye", "quit", "ばいばい", "さようなら", "またあとで"]
WEATHER_KEYWORDS = ["天気", "weather", "気温"]


class ChatInterface(QWidget):
    def __init__(self, mascot):
        super().__init__()
        self.mascot = mascot
        self.config = load_config()
        self.weather_interval = int(self.config.get("weather_interval", 600))
        self.default_location = self.config.get("default_location", "Tokyo")
        self.last_weather_update = {}
        self.cached_weather_info = {}

        self.initUI()
        self._load_history()
        self._setup_connections()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # 最前面表示を削除
        self.setMinimumSize(400, 500)

        layout = QVBoxLayout()
        self.title_bar = QLabel(" Virtual Mascot Chat ")
        self.title_bar.setStyleSheet("background: rgba(100,100,100,0.5); color: white;")
        self.title_bar.mousePressEvent = self._start_move
        self.title_bar.mouseMoveEvent = self._move_window

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("background: rgba(255,255,255,0.9);")

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("メッセージを入力...")
        self.input_field.returnPressed.connect(self._process_input)

        layout.addWidget(self.title_bar)
        layout.addWidget(self.chat_display)
        layout.addWidget(self.input_field)
        self.setLayout(layout)

    def _setup_connections(self):
        self.mascot.emitter.update_requested.connect(self._handle_updates)

    def _handle_updates(self, msg_type, content):
        if msg_type == "new_message":
            self._append_message(content)
        elif msg_type == "error":
            QMessageBox.critical(self, "エラー", content)

    def _start_move(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.pos()

    def _move_window(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    def _process_input(self):
        user_input = self.input_field.text().strip()
        if not user_input:
            return

        if any(kw in user_input for kw in EXIT_KEYWORDS):
            QApplication.quit()

        self.input_field.clear()
        self.mascot.handle_expression(user_input)

        threading.Thread(target=self._generate_response, args=(user_input,)).start()

    def _generate_response(self, user_input):
        try:
            # 天気キーワード検出
            if any(kw in user_input for kw in WEATHER_KEYWORDS):
                # 入力から地名を抽出
                location = self._extract_location(user_input)
                weather_info = self._get_weather(location)
                self.emitter.update_requested.emit(
                    "new_message", f"[天気情報] {location}: {weather_info}"
                )
                return

            # AI処理
            translated = GoogleTranslator(source="ja", target="en").translate(
                user_input
            )
            inputs = BlenderbotTokenizer.from_pretrained(
                "facebook/blenderbot-400M-distill"
            )(translated, return_tensors="pt")
            response_ids = BlenderbotForConditionalGeneration.from_pretrained(
                "facebook/blenderbot-400M-distill"
            ).generate(**inputs)
            response_en = BlenderbotTokenizer.from_pretrained(
                "facebook/blenderbot-400M-distill"
            ).decode(response_ids[0], skip_special_tokens=True)
            response = GoogleTranslator(source="en", target="ja").translate(response_en)

            self.emitter.update_requested.emit(
                "new_message",
                f"[{datetime.now().strftime('%H:%M')}] あなた\n👹: {user_input}\n"
                f"[{datetime.now().strftime('%H:%M')}] マスコット\n🐱: {response}",
            )
            # 会話履歴保存
            self._save_conversation(user_input, response)

        except Exception as e:
            self.emitter.update_requested.emit("error", str(e))

    def _append_message(self, message):
        current = self.chat_display.toPlainText().split("\n")
        if len(current) >= MAX_HISTORY_ENTRIES:
            current = current[-MAX_HISTORY_ENTRIES // 2 :]
        current.append(message)
        self.chat_display.setPlainText("\n".join(current))
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def _load_history(self):
        try:
            if os.path.exists(CONVERSATION_HISTORY_FILE):  # os.path.exists を使用
                with open(CONVERSATION_HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    self.chat_display.setPlainText(
                        "\n".join(
                            [
                                f"[{entry['time']}] あなた: {entry['input']}\n[{entry['time']}] マスコット: {entry['response']}"
                                for entry in history
                            ]
                        )
                    )
        except Exception as e:
            handle_error(f"履歴読み込みエラー: {e}")

    def _save_conversation(self, user_input, response):
        entry = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "input": user_input,
            "response": response,
        }

        try:
            history = []
            if CONVERSATION_HISTORY_FILE.exists():
                with open(CONVERSATION_HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            history.append(entry)
            if len(history) > MAX_HISTORY_ENTRIES:
                history = history[-MAX_HISTORY_ENTRIES:]
            with open(CONVERSATION_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            handle_error(f"履歴保存エラー: {e}")
