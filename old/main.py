import sys
from PyQt6.QtWidgets import QApplication
from old.mascot import Mascot
from old.chat_interface import ChatInterface

if __name__ == "__main__":
    app = QApplication(sys.argv)

    mascot = Mascot()
    mascot.show()

    chat_ui = ChatInterface(mascot)
    chat_ui.show()

    sys.exit(app.exec())
