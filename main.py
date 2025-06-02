from PyQt5.QtWidgets import (QMainWindow, QApplication, QTextEdit, QTableWidget, QTableWidgetItem,
                             QFileDialog, QAction, QStyleFactory, QVBoxLayout, QWidget,
                             QDialog, QLabel, QPushButton, QHBoxLayout, QScrollArea)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt
import sys
import pandas as pd
from cifa import Cifa
from yufa import Yufa
from graphviz import Digraph
import os
from yuyi import Yuyi
from zhongjian import Zhongjian
from Mubiao import Mubiao  # 新增导入目标代码生成模块


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


class AssemblyCodeDialog(QDialog):
    """汇编代码显示对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('目标代码 - MIPS汇编')
        self.setModal(True)

        # 设置对话框大小
        self.resize(800, 600)

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

        # 添加保存按钮
        save_btn = QPushButton('保存汇编代码')

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
        save_btn.setStyleSheet(button_style)
        save_btn.clicked.connect(self.save_code)

        toolbar_layout.addWidget(save_btn)
        toolbar_layout.addStretch()

        layout.addWidget(toolbar)

        # 创建文本编辑器显示汇编代码
        self.code_editor = QTextEdit()
        self.code_editor.setReadOnly(True)
        self.code_editor.setFont(QFont('Consolas', 11))
        self.code_editor.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
                padding: 10px;
                selection-background-color: #007acc;
                selection-color: #ffffff;
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

        layout.addWidget(self.code_editor)

        # 设置对话框样式
        self.setStyleSheet("""
            QDialog {
                background-color: #252525;
            }
        """)

    def show_code(self, assembly_code):
        """显示汇编代码"""
        self.assembly_code = assembly_code
        self.code_editor.setText(assembly_code)

    def save_code(self):
        """保存汇编代码到文件"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                '保存汇编代码',
                'output.asm',
                'Assembly Files (*.asm);;All Files (*)'
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.assembly_code)
                # 这里可以添加成功保存的提示
        except Exception as e:
            # 这里可以添加错误处理
            pass


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data = ""
        self.tokens = []
        self.ast = None  # 添加 ast 属性存储语法树
        self.quads = []  # 新增四元式存储
        self.initUI()

    def initUI(self):
        QApplication.setStyle(QStyleFactory.create('Fusion'))

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
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
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
                background: #f0f0f0;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #cccccc;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        self.layout.addWidget(self.textEdit)

        # 结果展示表格
        self.tableWidget = QTableWidget()
        self.tableWidget.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 8px;
                gridline-color: #cccccc;
                selection-background-color: #007acc;
                selection-color: #ffffff;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                color: #333333;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #cccccc;
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
                background: #f0f0f0;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #cccccc;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        self.layout.addWidget(self.tableWidget)

        # 错误输出框
        self.errorOutput = QTextEdit()
        self.errorOutput.setReadOnly(True)
        self.errorOutput.setFont(QFont('Consolas', 10))
        self.errorOutput.setStyleSheet("""
            QTextEdit {
                background-color: #fff5f5;
                color: #a94442;
                border: 1px solid #ebccd1;
                border-radius: 8px;
                padding: 10px;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #cccccc;
                border-radius: 6px;
            }
        """)
        self.errorOutput.setMaximumHeight(100)
        self.layout.addWidget(self.errorOutput)

        # 菜单栏
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #e0e0e0;
                color: #333333;
                padding: 6px;
                border-bottom: 1px solid #cccccc;
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
                background-color: #e0e0e0;
                color: #333333;
                border: 1px solid #cccccc;
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

        zhongjianFenxi = QAction('生成中间代码', self)
        zhongjianFenxi.triggered.connect(self.zhongjian_fenxi)

        # 新增目标代码生成菜单项
        mubiaoFenxi = QAction('生成目标代码', self)
        mubiaoFenxi.triggered.connect(self.mubiao_fenxi)

        fileMenu.addAction(newFile)
        fileMenu.addAction(openFile)
        FenxiMenu.addAction(cifaFenxi)
        FenxiMenu.addAction(yufaFenxi)
        FenxiMenu.addAction(yuyiFenxi)
        FenxiMenu.addAction(zhongjianFenxi)
        FenxiMenu.addAction(mubiaoFenxi)  # 添加到分析菜单

        toolbar = self.addToolBar('工具栏')
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #e0e0e0;
                border-bottom: 1px solid #cccccc;
                padding: 6px;
                spacing: 8px;
            }
            QToolButton {
                background-color: transparent;
                border: none;
                padding: 8px;
                color: #333333;
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

        self.setGeometry(100, 100, 900, 700)
        self.setWindowTitle('小小编译器')
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
        """)
        self.show()

    def show_error(self, message):
        """显示错误信息到错误输出框"""
        self.errorOutput.setText(message)

    def clear_error(self):
        """清空错误输出框"""
        self.errorOutput.clear()

    def generate_ast_graph(self, ast):
        """生成语法树图形"""
        dot = Digraph(comment='AST')
        dot.attr(rankdir='TB')
        
        def add_node_and_edges(node, parent_id=None, edge_label=None):
            if node is None:
                return
            
            # 生成节点ID
            node_id = str(id(node))
            
            # 设置节点标签
            if node['type'] == 'program':
                label = 'program'
            elif node['type'] == 'function_declaration':
                # 区分函数声明和函数定义
                if node.get('is_declaration', False):
                    label = f"function_declaration\n{node['return_type']} {node['name']}"
                else:
                    label = f"function_definition\n{node['return_type']} {node['name']}"
            elif node['type'] == 'variable_declaration':
                label = f"variable_declaration\n{node['var_type']} {node['name']}"
            elif node['type'] == 'binary_expression':
                label = f"binary_expression\n{node['operator']}"
            elif node['type'] == 'unary_expression':
                label = f"unary_expression\n{node['operator']}"
            elif node['type'] == 'identifier':
                label = f"identifier\n{node['name']}"
            elif node['type'] == 'number':
                label = f"number\n{node['value']}"
            elif node['type'] == 'if_statement':
                label = 'if_statement'
            elif node['type'] == 'while_statement':
                label = 'while_statement'
            elif node['type'] == 'printf_statement':
                label = 'printf_statement'
            elif node['type'] == 'return_statement':
                label = 'return_statement'
            elif node['type'] == 'function_call':
                label = f"function_call\n{node['name']}"
            else:
                label = node['type']
            
            # 添加节点
            dot.node(node_id, label)
            
            # 如果有父节点，添加边
            if parent_id is not None:
                dot.edge(parent_id, node_id, edge_label)
            
            # 处理子节点
            if node['type'] == 'program':
                for stmt in node.get('body', []):
                    add_node_and_edges(stmt, node_id, 'body')
            elif node['type'] == 'function_declaration':
                # 处理参数
                for param in node.get('params', []):
                    param_label = f"param\n{param['type']} {param['name']}"
                    param_id = str(id(param))
                    dot.node(param_id, param_label)
                    dot.edge(node_id, param_id, 'param')
                # 处理函数体（如果不是函数声明）
                if not node.get('is_declaration', False) and node.get('body'):
                    for stmt in node['body']:
                        add_node_and_edges(stmt, node_id, 'body')
            elif node['type'] == 'binary_expression':
                add_node_and_edges(node['left'], node_id, 'left')
                add_node_and_edges(node['right'], node_id, 'right')
            elif node['type'] == 'unary_expression':
                add_node_and_edges(node['operand'], node_id, 'operand')
            elif node['type'] == 'if_statement':
                add_node_and_edges(node['condition'], node_id, 'condition')
                if node.get('body'):
                    for stmt in node['body']:
                        add_node_and_edges(stmt, node_id, 'body')
                if node.get('else'):
                    for stmt in node['else']:
                        add_node_and_edges(stmt, node_id, 'else')
            elif node['type'] == 'while_statement':
                add_node_and_edges(node['condition'], node_id, 'condition')
                if node.get('body'):
                    for stmt in node['body']:
                        add_node_and_edges(stmt, node_id, 'body')
            elif node['type'] == 'printf_statement':
                for arg in node.get('arguments', []):
                    add_node_and_edges(arg, node_id, 'arg')
            elif node['type'] == 'function_call':
                for arg in node.get('arguments', []):
                    add_node_and_edges(arg, node_id, 'arg')
            elif node['type'] == 'return_statement':
                if node.get('value'):
                    add_node_and_edges(node['value'], node_id, 'value')
        
        # 开始生成图形
        add_node_and_edges(ast)
        
        output_dir = os.path.expanduser("~/syntax_tree_output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        temp_file = os.path.join(output_dir, f"syntax_tree_{str(id(ast))}.png")
        try:
            dot.render(filename=temp_file[:-4], format='png', cleanup=True)
            return temp_file
        except Exception as e:
            self.show_error(f'无法生成语法树图片: {str(e)}')
            return None

    def yufa_fenxi(self):
        self.clear_error()
        if not hasattr(self, 'tokens') or not self.tokens:
            self.show_error('请先进行词法分析！')
            return

        yufa = Yufa()
        self.ast = yufa.parse(self.tokens)

        if self.ast:
            self.tableWidget.clear()
            self.tableWidget.setRowCount(0)
            self.tableWidget.setColumnCount(3)
            self.tableWidget.setHorizontalHeaderLabels(['类型', '运算符/值', '说明'])

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

            show_ast(self.ast)
            self.tableWidget.resizeColumnsToContents()

        if self.ast and self.ast['type'] != 'error':
            image_path = self.generate_ast_graph(self.ast)
            if image_path:
                dialog = SyntaxTreeDialog(self)
                try:
                    dialog.show_tree(image_path)
                    dialog.exec_()
                finally:
                    if os.path.exists(image_path):
                        os.remove(image_path)

        if self.ast and self.ast.get('errors'):
            self.show_error('\n'.join(self.ast['errors']))

    def cifa_fenxi(self):
        self.clear_error()
        if not self.textEdit.toPlainText():
            self.show_error('请先输入或打开文件！')
            return

        cifa = Cifa()
        self.data = self.textEdit.toPlainText()
        self.tokens = cifa.cifafenxi(self.data)

        illegal_tokens = []
        for token in self.tokens:
            if token[0] == 0:
                illegal_tokens.append(f"第{token[3]}行: {token[2]} \t类型: {token[1]}")

        if illegal_tokens:
            self.show_error("发现非法字符：\n" + "\n".join(illegal_tokens))

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
        self.ast = None
        self.quads = []  # 清空四元式
        self.tableWidget.clear()
        self.tableWidget.setRowCount(0)
        self.clear_error()

    def openFile(self):
        self.clear_error()
        fname = QFileDialog.getOpenFileName(self, '打开文件')
        if fname[0]:
            try:
                with open(fname[0], 'r', encoding='utf-8') as f:
                    self.data = f.read()
                    self.textEdit.setText(self.data)
            except Exception as e:
                self.show_error(f'无法打开文件: {str(e)}')

    def yuyi_fenxi(self):
        self.clear_error()
        if not hasattr(self, 'tokens') or not self.tokens:
            self.show_error('请先进行词法分析！')
            return
        ast = self.ast

        if ast['type'] == 'error':
            self.show_error('\n'.join(ast['errors']))
            return

        yuyi = Yuyi()
        result = yuyi.analyze(ast)

        if result:
            # 显示符号表和函数表
            self.tableWidget.clear()
            self.tableWidget.setRowCount(0)
            self.tableWidget.setColumnCount(5)
            self.tableWidget.setHorizontalHeaderLabels(['类别', '符号名', '类型', '作用域', '值/参数'])

            # 添加变量（符号表）
            for var_info in result['symbol_table']:
                row = self.tableWidget.rowCount()
                self.tableWidget.insertRow(row)
                self.tableWidget.setItem(row, 0, QTableWidgetItem('变量'))
                self.tableWidget.setItem(row, 1, QTableWidgetItem(var_info['name']))
                self.tableWidget.setItem(row, 2, QTableWidgetItem(var_info['type']))
                self.tableWidget.setItem(row, 3, QTableWidgetItem(str(var_info['scope'])))
                value_str = str(var_info['value']) if var_info['value'] is not None else ''
                self.tableWidget.setItem(row, 4, QTableWidgetItem(value_str))

            # 添加函数（函数表）
            for func_name, func_info in result['function_table'].items():
                row = self.tableWidget.rowCount()
                self.tableWidget.insertRow(row)
                self.tableWidget.setItem(row, 0, QTableWidgetItem('函数'))
                self.tableWidget.setItem(row, 1, QTableWidgetItem(func_name))
                self.tableWidget.setItem(row, 2, QTableWidgetItem(func_info['return_type']))
                self.tableWidget.setItem(row, 3, QTableWidgetItem('global'))
                
                # 格式化参数信息
                params = []
                for name, type in zip(func_info['param_names'], func_info['param_types']):
                    params.append(f"{name}:{type}")
                params_str = ', '.join(params)
                self.tableWidget.setItem(row, 4, QTableWidgetItem(params_str))

            self.tableWidget.resizeColumnsToContents()

            # 显示语义错误或成功信息
            if result['errors']:
                self.show_error('\n'.join(result['errors']))
            else:
                self.show_error('语义分析通过，未发现错误！')

    def zhongjian_fenxi(self):
        """生成中间代码（四元式）并显示"""
        self.clear_error()

        # 检查是否已进行词法分析
        if not hasattr(self, 'tokens') or not self.tokens:
            self.show_error('请先进行词法分析！')
            return

        # 检查是否已进行语法分析
        if not hasattr(self, 'ast') or not self.ast:
            self.show_error('请先进行语法分析！')
            return

        # 检查语法分析是否成功
        if self.ast['type'] == 'error':
            self.show_error('语法分析失败，无法生成中间代码！\n' + '\n'.join(self.ast['errors']))
            return

        try:
            # 生成四元式
            zhongjian = Zhongjian()
            print("开始生成中间代码...")  # 调试信息
            print("AST结构:", self.ast)  # 调试信息
            
            self.quads = zhongjian.generate(self.ast)
            print("生成的四元式:", self.quads)  # 调试信息
            
            # 检查四元式是否生成成功
            if not self.quads:
                self.show_error('中间代码生成失败：未生成任何四元式')
                return
            
            # 创建水平布局来放置两个表格
            h_layout = QHBoxLayout()
            
            # 左侧表格显示优化前的代码
            left_table = QTableWidget()
            left_table.setRowCount(len(self.quads))
            left_table.setColumnCount(5)
            left_table.setHorizontalHeaderLabels(['索引', '操作符', '参数1', '参数2', '结果'])

            # 填充优化前的四元式到左侧表格
            for i, quad in enumerate(self.quads):
                try:
                    left_table.setItem(i, 0, QTableWidgetItem(str(i)))
                    left_table.setItem(i, 1, QTableWidgetItem(str(quad[0])))
                    left_table.setItem(i, 2, QTableWidgetItem(str(quad[1]) if quad[1] is not None else ''))
                    left_table.setItem(i, 3, QTableWidgetItem(str(quad[2]) if quad[2] is not None else ''))
                    left_table.setItem(i, 4, QTableWidgetItem(str(quad[3]) if quad[3] is not None else ''))
                except Exception as e:
                    print(f"处理四元式 {i} 时出错:", e)  # 调试信息
                    print("四元式内容:", quad)  # 调试信息
                    raise

            left_table.resizeColumnsToContents()
            h_layout.addWidget(left_table)

            # 进行代码优化
            from youhua import youhua
            optimizer = youhua(self.quads)
            optimized_quads = optimizer.optimize()
            print("优化后的四元式:", optimized_quads)  # 调试信息

            # 检查优化后的四元式
            if not optimized_quads:
                self.show_error('代码优化失败：未生成任何优化后的四元式')
                return

            # 右侧表格显示优化后的代码
            right_table = QTableWidget()
            right_table.setRowCount(len(optimized_quads))
            right_table.setColumnCount(5)
            right_table.setHorizontalHeaderLabels(['索引', '操作符', '参数1', '参数2', '结果'])

            # 填充优化后的四元式到右侧表格
            for i, quad in enumerate(optimized_quads):
                try:
                    right_table.setItem(i, 0, QTableWidgetItem(str(i)))
                    right_table.setItem(i, 1, QTableWidgetItem(str(quad[0])))
                    right_table.setItem(i, 2, QTableWidgetItem(str(quad[1]) if quad[1] is not None else ''))
                    right_table.setItem(i, 3, QTableWidgetItem(str(quad[2]) if quad[2] is not None else ''))
                    right_table.setItem(i, 4, QTableWidgetItem(str(quad[3]) if quad[3] is not None else ''))
                except Exception as e:
                    print(f"处理优化后的四元式 {i} 时出错:", e)  # 调试信息
                    print("四元式内容:", quad)  # 调试信息
                    raise

            right_table.resizeColumnsToContents()
            h_layout.addWidget(right_table)

            # 清空主布局并添加水平布局
            for i in reversed(range(self.layout.count())): 
                widget = self.layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            self.layout.addLayout(h_layout)

            # 更新主窗口的四元式为优化后的结果
            self.quads = optimized_quads

        except Exception as e:
            import traceback
            error_msg = f'中间代码生成失败: {str(e)}\n{traceback.format_exc()}'
            print(error_msg)  # 打印完整错误信息到控制台
            self.show_error(error_msg)

    def mubiao_fenxi(self):
        """生成目标代码并显示"""
        self.clear_error()

        # 检查是否已进行词法分析
        if not hasattr(self, 'tokens') or not self.tokens:
            self.show_error('请先进行词法分析！')
            return

        # 检查是否已进行语法分析
        if not hasattr(self, 'ast') or not self.ast:
            self.show_error('请先进行语法分析！')
            return

        # 检查是否已生成中间代码
        if not hasattr(self, 'quads') or not self.quads:
            self.show_error('请先生成中间代码！')
            return

        try:
            # 创建Mubiao实例并生成汇编代码
            mubiao = Mubiao(self.quads)
            asm_code = mubiao.generate()

            # 显示汇编代码
            dialog = AssemblyCodeDialog(self)
            dialog.show_code(asm_code)
            dialog.exec_()

        except Exception as e:
            self.show_error(f'目标代码生成失败: {str(e)}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = TextEditor()
    sys.exit(app.exec_())
