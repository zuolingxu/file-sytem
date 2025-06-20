import os

from PySide6 import QtWidgets
from PySide6.QtCore import Qt, QObject
from PySide6.QtGui import QIcon
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget, QMainWindow, QListWidgetItem, QDialog, QMenu, QLabel, QHBoxLayout, QSpacerItem

from dialog import NewItemDialog
from editor import TextEditor
from file_system_core import FileSystem as FS, load_from_disk


class FileSystemUI(QObject):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.ui = QUiLoader().load('file_system.ui')
        with open("Ubuntu.qss", "r") as f:
            self.ui.setStyleSheet(f.read())
        if os.path.exists("fs.pickle"):
            self.fs = load_from_disk("fs.pickle")
        else:
            self.fs = FS()
        self.files = []   # 用于存储当前目录下的文件
        self.dirs = []    # 用于存储当前目录下的文件夹
        self.text_editor = TextEditor()
        self.text_editor.text_saved.connect(self.save_file)
        self.ui.listWidget.doubleClicked.connect(self.on_double_clicked)
        self.ui.listWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.listWidget.setUniformItemSizes(False)
        self.ui.listWidget.customContextMenuRequested.connect(self.show_menu)

        self.ui.new_dir_button.clicked.connect(self.new_directory_dialog)
        self.ui.new_file_button.clicked.connect(self.new_file_dialog)
        self.ui.return_button.clicked.connect(self.back_to_parent)
        self.ui.return_root_button.clicked.connect(self.back_to_root)
        self.ui.delete_button.clicked.connect(self.delete)
        self.ui.rename_button.clicked.connect(self.rename)
        self.ui.format_button.clicked.connect(self.fformat)

        self.list()
        self.ui.path_label.setText(self.fs.current_directory.name)
        if self.fs.current_directory.name == "/":
            self.ui.return_button.setEnabled(False)
            self.ui.return_root_button.setEnabled(False)

    def show_menu(self, pos):
        # 创建右键菜单
        menu = QMenu(self.ui)

        # 添加菜单项
        new_file_action = menu.addAction("新建文件")
        new_directory_action = menu.addAction("新建文件夹")
        delete_action = menu.addAction("删除")
        open_file_action = menu.addAction("打开文件")
        rename_action = menu.addAction("重命名")
        format_action = menu.addAction("格式化")

        # 显示菜单，并等待用户选择
        action = menu.exec(self.ui.listWidget.mapToGlobal(pos))

        # 根据用户选择执行相应操作
        if action == new_file_action:
            self.new_file_dialog()
        elif action == new_directory_action:
            self.new_directory_dialog()
        elif action == delete_action:
            self.delete()
        elif action == open_file_action:
            item = self.ui.listWidget.currentItem()
            self.open_file(self.ui.listWidget.itemWidget(
                item).layout().itemAt(0).widget().text())
        elif action == rename_action:
            self.rename()
        elif action == format_action:
            self.fformat()

    def new_directory_dialog(self):
        dialog = NewItemDialog(self.ui)
        dialog.setWindowTitle("新建文件夹")

        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.get_input_text()
            if name:
                if self.fs.make_directory(name):
                    self.list()
                else:
                    QtWidgets.QMessageBox.warning(self.ui, "错误", "文件夹已存在")
        else:
            dialog.close()

    def new_file_dialog(self):
        dialog = NewItemDialog(self.ui)
        dialog.setWindowTitle("新建文件")
        if dialog.exec_() == QDialog.DialogCode.Accepted:
            name = dialog.get_input_text()
            if name:
                if self.fs.create_file(name):
                    self.list()
                else:
                    QtWidgets.QMessageBox.warning(self.ui, "错误", "文件已存在")
        else:
            dialog.close()

    def back_to_parent(self):
        if self.fs.current_directory.name != "/":
            self.fs.change_directory(self.fs.current_directory.parent.name)
        self.list()
        self.ui.path_label.setText(self.fs.get_current_path())
        if self.fs.current_directory.name == "/":
            self.ui.return_button.setEnabled(False)
            self.ui.return_root_button.setEnabled(False)

    def back_to_root(self):
        self.fs.change_directory(self.fs.root.name)
        self.list()
        self.ui.path_label.setText("/")
        if self.fs.current_directory.name == "/":
            self.ui.return_button.setEnabled(False)
            self.ui.return_root_button.setEnabled(False)

    def list(self):
        """
        列出当前目录下的文件和文件夹
        """
        self.ui.listWidget.clear()

        for directory in self.fs.current_directory.subdirectories:
            item = QListWidgetItem()
            item.setIcon(QIcon("resources/folder.svg"))
            name_label = QLabel(directory.name+"/")
            num_label = QLabel(str(self.fs.get_dir_item_nums(directory)) + "项")
            layout = QHBoxLayout()
            widget = QWidget()
            layout.addWidget(name_label)
            spacer = QSpacerItem(40, 5, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
            layout.addItem(spacer)
            layout.addWidget(num_label)
            widget.setLayout(layout)
            item.setSizeHint(widget.sizeHint())
            self.ui.listWidget.addItem(item)
            self.ui.listWidget.setItemWidget(item, widget)
            self.dirs.append(directory)

        for file in self.fs.current_directory.files:
            item = QListWidgetItem()
            size_label = QLabel(self.format_size(self.fs.get_file_size(file)))
            time_label = QLabel(self.fs.get_file_mtime(file).strftime("%Y-%m-%d %H:%M:%S"))
            name_label = QLabel(file.name)
            name_label.setMinimumSize(150, 0)
            widget = QWidget()
            layout = QHBoxLayout()
            layout.addWidget(name_label)
            layout.addItem(QSpacerItem(20, 5, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum))
            layout.addWidget(size_label)
            layout.addItem(QSpacerItem(20, 5, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum))
            layout.addWidget(time_label)
            layout.setContentsMargins(0, 0, 0, 0)
            widget.setLayout(layout)
            item.setSizeHint(widget.sizeHint())
            self.ui.listWidget.addItem(item)
            item.setIcon(QIcon("resources/file.svg"))
            self.ui.listWidget.setItemWidget(item, widget)
            self.files.append(file)

        total, used = self.fs.get_total_and_used_space_size()
        self.ui.size_label.setText(
            "已使用空间：" + self.format_size(used) + " / " + self.format_size(total))

        self.ui.listWidget.repaint()
        self.ui.size_label.repaint()

    def on_double_clicked(self, index):
        item = self.ui.listWidget.itemFromIndex(index)
        widget = self.ui.listWidget.itemWidget(item)
        name = widget.layout().itemAt(0).widget().text()
        for file in self.files:
            if file.name == name:
                self.open_file(name)
                return

        for directory in self.dirs:
            if directory.name == name.rstrip("/"):
                self.open_directory(name)
                return

    def open_file(self, name):
        data = self.fs.read_file(name)
        self.text_editor.ui.setWindowTitle(name)
        self.text_editor.file_name = name
        self.text_editor.open_file(data.decode("utf-8"))
        self.text_editor.ui.show()

    def save_file(self, text):
        if self.fs.write_file(self.text_editor.file_name,bytearray(text, "utf-8")):
            self.list()
        else:
            QtWidgets.QMessageBox.warning(self.ui, "错误", "保存失败,空间不足")
        self.fs.save_to_disk("fs.pickle")

    def open_directory(self, name):
        self.ui.return_button.setEnabled(True)
        self.ui.return_root_button.setEnabled(True)
        self.files.clear()
        self.dirs.clear()
        self.fs.change_directory(name.rstrip("/"))
        self.list()
        self.ui.path_label.setText(self.fs.get_current_path())

    def delete(self):
        item = self.ui.listWidget.currentItem()
        name = self.ui.listWidget.itemWidget(
            item).layout().itemAt(0).widget().text()
        if name.endswith("/"):
            self.delete_dir(name.rstrip("/"))
        else:
            self.delete_file(name)
        self.fs.save_to_disk("fs.pickle")

    def delete_file(self, name):
        self.fs.delete_file(name)
        self.list()
        self.fs.save_to_disk("fs.pickle")

    def delete_dir(self, name):
        self.fs.remove_directory(name)
        self.list()
        self.fs.save_to_disk("fs.pickle")

    def format_size(self, size):
        # 格式化文件大小
        if size < 1024:
            return str(size) + " B"
        elif size < 1024 * 1024:
            return "{:.1f} KB".format(size / 1024)
        elif size < 1024 * 1024 * 1024:
            return "{:.1f} MB".format(size / (1024 * 1024))
        else:
            return "{:.1f} GB".format(size / (1024 * 1024 * 1024))

    def rename(self):
        item = self.ui.listWidget.currentItem()
        old_name = self.ui.listWidget.itemWidget(item).layout().itemAt(0).widget().text()
        dialog = NewItemDialog(self.ui, old_name)
        dialog.setWindowTitle("重命名")
        if dialog.exec_() == QDialog.DialogCode.Accepted:
            new_name = dialog.get_input_text()
            if old_name.endswith("/"):
                if new_name:
                    result, err = self.fs.rename_directory(
                        old_name.rstrip("/"), new_name)
                    if result:
                        self.list()
                    else:
                        if err == 1:
                            QtWidgets.QMessageBox.warning(self.ui, "错误", "文件夹不存在")
                        elif err == 2:
                            QtWidgets.QMessageBox.warning(
                                self.ui, "错误", "新文件夹名不能与旧文件夹名相同")
                        elif err == 3:
                            QtWidgets.QMessageBox.warning(
                                self.ui, "错误", "新文件夹名已存在")
                else:
                    QtWidgets.QMessageBox.warning(self.ui, "错误", "名字不能为空")
            else:
                if new_name:
                    result, err = self.fs.rename_file(old_name, new_name)
                    if result:
                        self.list()
                    else:
                        if err == 1:
                            QtWidgets.QMessageBox.warning(self.ui, "错误", "文件不存在")
                        elif err == 2:
                            QtWidgets.QMessageBox.warning(
                                self.ui, "错误", "新文件名不能与旧文件名相同")
                        elif err == 3:
                            QtWidgets.QMessageBox.warning(
                                self.ui, "错误", "新文件名已存在")
                else:
                    QtWidgets.QMessageBox.warning(self.ui, "错误", "名字不能为空")
        else:
            dialog.close()
        self.fs.save_to_disk("fs.pickle")

    def fformat(self):
        self.fs.fformat()
        self.list()

def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = FileSystemUI()
    ui.list()
    ui.ui.show()
    flag = app.exec()
    ui.fs.save_to_disk("fs.pickle")
    sys.exit(flag)


if __name__ == '__main__':
    main()
