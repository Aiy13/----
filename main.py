from PyQt5.QtWidgets import (QMainWindow, QApplication, QTextEdit, QTableWidget, QTableWidgetItem,
                           QFileDialog, QMessageBox, QAction, QStyleFactory, QVBoxLayout, QWidget,
                           QDialog, QLabel)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt
import sys
import pandas as pd
from cifa import Cifa
from yufa import Yufa
# import graphviz
import tempfile
import os

class SyntaxTreeDialog(QDialog):
    """语法树显示对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('语法树可视化')
        self.setModal(True)
        
        # 设置对话框大小
        self.resize(800, 600)
        
        # 创建布局
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 创建图片标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #252525;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)

    def show_tree(self, dot):
        """显示语法树图片"""
        # 创建临时文件
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, 'syntax_tree')
        
        # 渲染图片
        dot.render(temp_path, format='png', cleanup=True)
        
        # 加载并显示图片
        pixmap = QPixmap(temp_path + '.png')
        scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)

class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data = ""
        self.tokens = []
        self.initUI()

    def initUI(self):
        # 设置应用样式
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        
        # 创建主布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setSpacing(10)  # 控件间距
        self.layout.setContentsMargins(10, 10, 10, 10)  # 外边距

        # 输入文本编辑区
        self.textEdit = QTextEdit()
        self.textEdit.setFont(QFont('Consolas', 12))
        self.textEdit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 8px;
                selection-background-color: #4a90e2;
                selection-color: #ffffff;
            }
            QTextEdit:focus {
                border: 1px solid #4a90e2;
            }
        """)
        self.layout.addWidget(self.textEdit)

        # 结果展示表格
        self.tableWidget = QTableWidget()
        self.tableWidget.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #404040;
                border-radius: 6px;
                gridline-color: #404040;
                selection-background-color: #4a90e2;
                selection-color: #ffffff;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #e0e0e0;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #404040;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #4a90e2;
            }
        """)
        self.layout.addWidget(self.tableWidget)

        # 菜单栏
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #2d2d2d;
                color: #e0e0e0;
                padding: 4px;
            }
            QMenuBar::item {
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #4a90e2;
                color: #ffffff;
            }
            QMenu {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #404040;
                border-radius: 4px;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #4a90e2;
                color: #ffffff;
            }
        """)
        
        fileMenu = menubar.addMenu('文件')
        FenxiMenu = menubar.addMenu('分析')
        
        newFile = QAction('新建', self)
        newFile.setShortcut('Ctrl+N')
        newFile.triggered.connect(self.newFile)
        
        openFile = QAction('打开', self)
        openFile.setShortcut('Ctrl+O')
        openFile.triggered.connect(self.openFile)
        
        cifaFenxi = QAction('词法分析', self)
        cifaFenxi.triggered.connect(self.cifa_fenxi)
        
        yufaFenxi = QAction('语法分析', self)
        yufaFenxi.triggered.connect(self.yufa_fenxi)
        
        # 工具栏
        toolbar = self.addToolBar('工具栏')
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #2d2d2d;
                border-bottom: 1px solid #404040;
                padding: 4px;
                spacing: 6px;
            }
            QToolButton {
                background-color: transparent;
                border: none;
                padding: 6px;
                color: #e0e0e0;
            }
            QToolButton:hover {
                background-color: #4a90e2;
                border-radius: 4px;
            }
        """)
        
        fileMenu.addAction(newFile)
        fileMenu.addAction(openFile)
        FenxiMenu.addAction(cifaFenxi)
        FenxiMenu.addAction(yufaFenxi)
        
        # 窗口设置
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('小小编译器')
        self.setStyleSheet("""
            QMainWindow {
                background-color: #252525;
            }
        """)
        self.show()

    def yufa_fenxi(self):
        if not hasattr(self, 'tokens') or not self.tokens:
            QMessageBox.warning(self, '警告', '请先进行词法分析！')
            return
        
        yufa = Yufa()
        ast = yufa.parse(self.tokens)
        
        # 显示语法分析结果
        if ast:
            # 创建结果表格
            self.tableWidget.clear()
            self.tableWidget.setRowCount(0)
            self.tableWidget.setColumnCount(3)
            self.tableWidget.setHorizontalHeaderLabels(['类型', '运算符/值', '说明'])
            
            # 递归显示语法树结果
            def show_ast(node, description=''):
                if not node or not isinstance(node, dict):
                    return
                
                row = self.tableWidget.rowCount()
                self.tableWidget.insertRow(row)
                
                if node['type'] == 'binary_expression':
                    self.tableWidget.setItem(row, 0, QTableWidgetItem('运算符'))
                    self.tableWidget.setItem(row, 1, QTableWidgetItem(node['operator']))
                    self.tableWidget.setItem(row, 2, QTableWidgetItem(description))
                    
                    show_ast(node.get('left'), '左操作数')
                    show_ast(node.get('right'), '右操作数')
                    
                elif node['type'] == 'number':
                    self.tableWidget.setItem(row, 0, QTableWidgetItem('数值'))
                    self.tableWidget.setItem(row, 1, QTableWidgetItem(node['value']))
                    self.tableWidget.setItem(row, 2, QTableWidgetItem(description))
            
            show_ast(ast)
            self.tableWidget.resizeColumnsToContents()
        
        # 显示错误信息
        if ast and ast.get('errors'):
            error_msg = '\n'.join(ast['errors'])
            QMessageBox.warning(self, '语法错误', error_msg)

   
    def cifa_fenxi(self):
        if not self.textEdit.toPlainText():
            QMessageBox.warning(self, '警告', '请先输入或打开文件！')
            return
        
        cifa = Cifa()
        self.data = self.textEdit.toPlainText()
        self.tokens = cifa.cifafenxi(self.data)
        
        # 收集非法字符信息
        illegal_tokens = []
        for token in self.tokens:
            if token[0] == 0:  # 种别码为0的token
                illegal_tokens.append(f"第{token[3]}行: {token[2]} \t类型: {token[1]}")
        
        # 如果有非法字符，显示弹窗
        if illegal_tokens:
            error_message = "发现非法字符：\n\n" + "\n".join(illegal_tokens)
            QMessageBox.warning(self, '非法字符提示', error_message)
        
        # 显示词法分析结果
        df = pd.DataFrame(self.tokens, columns=['种别码', '类型', '值', '行数'])
        self.tableWidget.setRowCount(df.shape[0])
        self.tableWidget.setColumnCount(df.shape[1])
        self.tableWidget.setHorizontalHeaderLabels(df.columns)
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))
        self.tableWidget.resizeColumnsToContents()

    def newFile(self):
        self.textEdit.clear()
        self.data = ""
        self.tokens = []
        self.tableWidget.clear()
        self.tableWidget.setRowCount(0)

    def openFile(self):
        fname = QFileDialog.getOpenFileName(self, '打开文件')
        if fname[0]:
            try:
                with open(fname[0], 'r', encoding='utf-8') as f:
                    self.data = f.read()
                    self.textEdit.setText(self.data)
            except Exception as e:
                QMessageBox.warning(self, '错误', f'无法打开文件: {str(e)}')


app = QApplication(sys.argv)
editor = TextEditor()
sys.exit(app.exec_())