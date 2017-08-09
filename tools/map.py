#!/usr/bin/env python3
import sys

from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()
    ctx = engine.rootContext()
    ctx.setContextProperty('main', engine)

    engine.load('main.qml')

    win = engine.rootObjects()[0]
    win.show()
    sys.exit(app.exec_())