import sys

from PyQt6.QtWidgets import QApplication

from MainWindow import MainWindow
from db import init_db


def main():
    init_db()
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
