from PyQt5.QtWidgets import (QMainWindow, QApplication, QTextEdit, QTableWidget, QTableWidgetItem,
                             QFileDialog, QMessageBox, QAction, QStyleFactory, QVBoxLayout, QWidget,
                             QDialog, QLabel, QPushButton, QHBoxLayout, QScrollArea)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt
import sys
import pandas as pd
from cifa import Cifa
from yufa import Yufa
from graphviz import Digraph
import tempfile
import os
from yuyi import Yuyi


class SyntaxTreeDialog(QDialog):
    """语法树显示对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('语法树可视化')
        self.setModal(True)
        self.scale_factor = 1.0  # 缩放因子

        # 设置对话框大小
        self.resize(1000, 800)

        # 创建布局
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        self.setLayout(layout)

        # 创建工具栏
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar.setLayout(toolbar_layout)

        # 添加缩放按钮
        zoom_in_btn = QPushButton('放大')
        zoom_out_btn = QPushButton('缩小')
        reset_btn = QPushButton('重置')
        
        # 设置按钮样式
        button_style = """
            QPushButton {
                background-color: #353535;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #007acc;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #005f99;
            }
        """
        zoom_in_btn.setStyleSheet(button_style)
        zoom_out_btn.setStyleSheet(button_style)
        reset_btn.setStyleSheet(button_style)

        # 连接按钮信号
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_out_btn.clicked.connect(self.zoom_out)
        reset_btn.clicked.connect(self.reset_zoom)

        # 添加按钮到工具栏
        toolbar_layout.addWidget(zoom_in_btn)
        toolbar_layout.addWidget(zoom_out_btn)
        toolbar_layout.addWidget(reset_btn)
        toolbar_layout.addStretch()

        layout.addWidget(toolbar)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #2b2b2b;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
            }
            QScrollBar:vertical {
                border: none;
                background: #2b2b2b;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #4a4a4a;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                border: none;
                background: #2b2b2b;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #4a4a4a;
                border-radius: 6px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)

        # 创建图片标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        # 将图片标签添加到滚动区域
        scroll_area.setWidget(self.image_label)
        layout.addWidget(scroll_area)

        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #252525;
            }
        """)

    def show_tree(self, image_path):
        """显示语法树图片"""
        self.original_pixmap = QPixmap(image_path)
        self.update_image()

    def update_image(self):
        """更新图片显示"""
        if hasattr(self, 'original_pixmap'):
            # 将浮点数转换为整数
            new_width = int(self.original_pixmap.width() * self.scale_factor)
            new_height = int(self.original_pixmap.height() * self.scale_factor)
            
            scaled_pixmap = self.original_pixmap.scaled(
                new_width,
                new_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def zoom_in(self):
        """放大图片"""
        self.scale_factor *= 1.2
        self.update_image()

    def zoom_out(self):
        """缩小图片"""
        self.scale_factor /= 1.2
        self.update_image()

    def reset_zoom(self):
        """重置缩放"""
        self.scale_factor = 1.0
        self.update_image()


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
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(12, 12, 12, 12)

        # 输入文本编辑区
        self.textEdit = QTextEdit()
        self.textEdit.setFont(QFont('Consolas', 12))
        self.textEdit.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
                padding: 10px;
                selection-background-color: #007acc;
                selection-color: #ffffff;
            }
            QTextEdit:focus {
                border: 1px solid #007acc;
            }
            QScrollBar:vertical {
                border: none;
                background: #2b2b2b;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #4a4a4a;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        self.layout.addWidget(self.textEdit)

        # 结果展示表格
        self.tableWidget = QTableWidget()
        self.tableWidget.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
                gridline-color: #3c3c3c;
                selection-background-color: #007acc;
                selection-color: #ffffff;
            }
            QHeaderView::section {
                background-color: #353535;
                color: #d4d4d4;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #3c3c3c;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #007acc;
            }
            QScrollBar:vertical {
                border: none;
                background: #2b2b2b;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #4a4a4a;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        self.layout.addWidget(self.tableWidget)

        # 菜单栏
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #353535;
                color: #d4d4d4;
                padding: 6px;
                border-bottom: 1px solid #3c3c3c;
            }
            QMenuBar::item {
                padding: 6px 12px;
                background: transparent;
            }
            QMenuBar::item:selected {
                background-color: #007acc;
                color: #ffffff;
                border-radius: 4px;
            }
            QMenu {
                background-color: #353535;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                background: transparent;
            }
            QMenu::item:selected {
                background-color: #007acc;
                color: #ffffff;
                border-radius: 4px;
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

        yuyiFenxi = QAction('语义分析', self)
        yuyiFenxi.triggered.connect(self.yuyi_fenxi)

        fileMenu.addAction(newFile)
        fileMenu.addAction(openFile)
        FenxiMenu.addAction(cifaFenxi)
        FenxiMenu.addAction(yufaFenxi)
        FenxiMenu.addAction(yuyiFenxi)

        # 工具栏
        toolbar = self.addToolBar('工具栏')
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #353535;
                border-bottom: 1px solid #3c3c3c;
                padding: 6px;
                spacing: 8px;
            }
            QToolButton {
                background-color: transparent;
                border: none;
                padding: 8px;
                color: #d4d4d4;
                border-radius: 6px;
            }
            QToolButton:hover {
                background-color: #007acc;
                color: #ffffff;
            }
            QToolButton:pressed {
                background-color: #005f99;
            }
        """)

        # 窗口设置
        self.setGeometry(100, 100, 900, 700)
        self.setWindowTitle('小小编译器')
        self.setStyleSheet("""
            QMainWindow {
                background-color: #252525;
            }
            QMessageBox {
                background-color: #2b2b2b;
                color: #d4d4d4;
            }
            QMessageBox QPushButton {
                background-color: #353535;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QMessageBox QPushButton:hover {
                background-color: #007acc;
                color: #ffffff;
            }
        """)
        self.show()

    def generate_ast_graph(self, ast):
        """使用 graphviz 生成语法树图形并返回图片路径"""
        try:
            from graphviz import Digraph
        except ImportError:
            QMessageBox.critical(self, '错误', '请安装 graphviz 库：pip install graphviz\n并确保安装 Graphviz 软件：https://graphviz.org/download/')
            return None

        # 创建 DOT 图
        dot = Digraph(
            comment='Syntax Tree',
            format='png',
            graph_attr={'rankdir': 'TB', 'bgcolor': '#252525'},
            node_attr={'shape': 'box', 'style': 'filled', 'fillcolor': '#ADD8E6', 'color': '#000000', 'fontcolor': '#000000', 'fontname': 'Consolas', 'fontsize': '10'},
            edge_attr={'color': '#555555', 'arrowsize': '1.0'}
        )

        def add_node_and_edges(node, parent=None, description=''):
            if not node or not isinstance(node, dict):
                return

            # 创建当前节点的标签
            node_id = str(id(node))
            node_type = node.get('type', '')
            label = node_type

            if node_type == 'binary_expression':
                label = node.get('operator', '')
            elif node_type == 'number':
                label = node.get('value', '')
            elif node_type == 'identifier':
                label = node.get('name', '')
            elif node_type == 'assignment_expression':
                label = '='
            elif node_type == 'variable_declaration':
                label = f"{node.get('var_type', '')} {node.get('name', '')}"
            elif node_type in ['if_statement', 'while_statement', 'program']:
                label = node_type

            # 添加节点
            dot.node(node_id, label)

            # 如果有父节点，添加边
            if parent is not None:
                dot.edge(parent, node_id, label=description if description else '')

            # 递归处理子节点
            if node_type == 'binary_expression':
                add_node_and_edges(node.get('left'), node_id, 'left')
                add_node_and_edges(node.get('right'), node_id, 'right')
            elif node_type == 'assignment_expression':
                add_node_and_edges(node.get('left'), node_id, 'left')
                add_node_and_edges(node.get('right'), node_id, 'right')
            elif node_type == 'variable_declaration':
                add_node_and_edges(node.get('initializer'), node_id, 'initializer')
            elif node_type == 'if_statement':
                add_node_and_edges(node.get('condition'), node_id, 'condition')
                for stmt in node.get('body', []):
                    add_node_and_edges(stmt, node_id, 'body')
                if node.get('else'):
                    for stmt in node['else']:
                        add_node_and_edges(stmt, node_id, 'else')
            elif node_type == 'while_statement':
                add_node_and_edges(node.get('condition'), node_id, 'condition')
                for stmt in node.get('body', []):
                    add_node_and_edges(stmt, node_id, 'body')
            elif node_type == 'program':
                for stmt in node.get('body', []):
                    add_node_and_edges(stmt, node_id, 'body')

        # 从根节点开始构建图
        add_node_and_edges(ast)

        # 保存图形到用户主目录下的特定文件夹
        output_dir = os.path.expanduser("~/syntax_tree_output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 创建唯一的临时文件
        temp_file = os.path.join(output_dir, f"syntax_tree_{str(id(ast))}.png")
        try:
            dot.render(filename=temp_file[:-4], format='png', cleanup=True)
            return temp_file
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法生成语法树图片: {str(e)}')
            return None

    def yufa_fenxi(self):
        if not hasattr(self, 'tokens') or not self.tokens:
            QMessageBox.warning(self, '警告', '请先进行词法分析！')
            return

        yufa = Yufa()
        ast = yufa.parse(self.tokens)

        # 显示语法分析结果（表格）
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
                elif node['type'] == 'identifier':
                    self.tableWidget.setItem(row, 0, QTableWidgetItem('标识符'))
                    self.tableWidget.setItem(row, 1, QTableWidgetItem(node['name']))
                    self.tableWidget.setItem(row, 2, QTableWidgetItem(description))
                elif node['type'] == 'assignment_expression':
                    self.tableWidget.setItem(row, 0, QTableWidgetItem('赋值表达式'))
                    self.tableWidget.setItem(row, 1, QTableWidgetItem('='))
                    self.tableWidget.setItem(row, 2, QTableWidgetItem(description))
                    show_ast(node.get('left'), '左操作数')
                    show_ast(node.get('right'), '右操作数')
                elif node['type'] == 'variable_declaration':
                    self.tableWidget.setItem(row, 0, QTableWidgetItem('变量声明'))
                    self.tableWidget.setItem(row, 1, QTableWidgetItem(f"{node['var_type']} {node['name']}"))
                    self.tableWidget.setItem(row, 2, QTableWidgetItem(description))
                    show_ast(node.get('initializer'), '初始化表达式')
                elif node['type'] == 'if_statement':
                    self.tableWidget.setItem(row, 0, QTableWidgetItem('if语句'))
                    self.tableWidget.setItem(row, 1, QTableWidgetItem('if'))
                    self.tableWidget.setItem(row, 2, QTableWidgetItem(description))
                    show_ast(node.get('condition'), '条件')
                    for stmt in node.get('body', []):
                        show_ast(stmt, '语句体')
                    if node.get('else'):
                        for stmt in node['else']:
                            show_ast(stmt, 'else语句体')
                elif node['type'] == 'while_statement':
                    self.tableWidget.setItem(row, 0, QTableWidgetItem('while语句'))
                    self.tableWidget.setItem(row, 1, QTableWidgetItem('while'))
                    self.tableWidget.setItem(row, 2, QTableWidgetItem(description))
                    show_ast(node.get('condition'), '条件')
                    for stmt in node.get('body', []):
                        show_ast(stmt, '语句体')
                elif node['type'] == 'program':
                    self.tableWidget.setItem(row, 0, QTableWidgetItem('程序'))
                    self.tableWidget.setItem(row, 1, QTableWidgetItem(''))
                    self.tableWidget.setItem(row, 2, QTableWidgetItem(description))
                    for stmt in node.get('body', []):
                        show_ast(stmt, '语句')

            show_ast(ast)
            self.tableWidget.resizeColumnsToContents()

        # 绘制语法树
        if ast and ast['type'] != 'error':
            image_path = self.generate_ast_graph(ast)
            if image_path:
                dialog = SyntaxTreeDialog(self)
                try:
                    dialog.show_tree(image_path)
                    dialog.exec_()
                finally:
                    if os.path.exists(image_path):
                        os.remove(image_path)

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
                QMessageBox.critical(self, '错误', f'无法打开文件: {str(e)}')

    def yuyi_fenxi(self):
        if not hasattr(self, 'tokens') or not self.tokens:
            QMessageBox.warning(self, '警告', '请先进行词法分析！')
            return

        # 先进行语法分析
        yufa = Yufa()
        ast = yufa.parse(self.tokens)
        
        if ast['type'] == 'error':
            QMessageBox.warning(self, '语法错误', '\n'.join(ast['errors']))
            return
        
        # 进行语义分析
        yuyi = Yuyi()
        result = yuyi.analyze(ast)
        
        # 显示语义分析结果
        if result['type'] == 'error':
            QMessageBox.warning(self, '语义错误', '\n'.join(result['errors']))
        else:
            # 显示符号表
            self.tableWidget.clear()
            self.tableWidget.setRowCount(0)
            self.tableWidget.setColumnCount(2)
            self.tableWidget.setHorizontalHeaderLabels(['变量名', '类型'])
            
            for var_name, var_type in result['symbol_table'].items():
                row = self.tableWidget.rowCount()
                self.tableWidget.insertRow(row)
                self.tableWidget.setItem(row, 0, QTableWidgetItem(var_name))
                self.tableWidget.setItem(row, 1, QTableWidgetItem(var_type))
            
            self.tableWidget.resizeColumnsToContents()
            
            # 显示语义错误
            if result['errors']:
                QMessageBox.warning(self, '语义错误', '\n'.join(result['errors']))
            else:
                QMessageBox.information(self, '语义分析', '语义分析通过，未发现错误！')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = TextEditor()
    sys.exit(app.exec_())