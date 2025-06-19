import sys

from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QKeySequence
from PySide6.QtGui import QShortcut
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QMessageBox


class TextEditor(QObject):
    text_saved = Signal(str)

    def __init__(self):
        super().__init__()
        self.ui = QUiLoader().load('editor.ui')
        with open("Ubuntu.qss", "r") as f:
            self.ui.setStyleSheet(f.read())
        self.ui.textEdit.setText("")
        self.ui.save_button.clicked.connect(self.save_file)
        self.ui.textEdit.textChanged.connect(self.modified)
        self.is_saved = True
        self.file_name = ""
        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.activated.connect(self.save_file)

    def modified(self):
        self.is_saved = False
        self.ui.setWindowTitle(f"{self.file_name} *")

    def open_file(self, text):
        self.ui.textEdit.setText(text)
        self.ui.setWindowTitle(self.file_name)

    def save_file(self):
        if self.is_saved:
            return
        self.text_saved.emit(self.ui.textEdit.toPlainText())
        self.is_saved = True
        self.ui.setWindowTitle(self.file_name)

    def closeEvent(self, event):
        if self.ui.textEdit.document().isModified() and not self.is_saved:
            reply = QMessageBox.question(
                self.ui, "保存文件", "是否保存文件？",
                QMessageBox.StandardButton.Yes |
                QMessageBox.StandardButton.No |
                QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.save_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = TextEditor()
    editor.ui.show()
    sys.exit(app.exec())
