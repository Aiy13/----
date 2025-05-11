class Yuyi:
    def __init__(self):
        self.symbol_table = {}  # 符号表，存储变量名和类型
        self.errors = []        # 语义错误列表
        self.current_scope = "global"  # 当前作用域

    def analyze(self, ast):
        """
        对语法树进行语义分析
        :param ast: 语法分析生成的抽象语法树
        :return: 包含语义分析结果的字典
        """
        if ast['type'] == 'error':
            return {'type': 'error', 'errors': ast['errors']}
            
        # 清空符号表和错误列表
        self.symbol_table = {}
        self.errors = []
        
        # 分析程序体
        for stmt in ast['body']:
            self.analyze_statement(stmt)
            
        return {
            'type': 'semantic_analysis',
            'symbol_table': self.symbol_table,
            'errors': self.errors
        }
    
    def analyze_statement(self, stmt):
        """分析单个语句"""
        if stmt['type'] == 'variable_declaration':
            self.analyze_variable_declaration(stmt)
        elif stmt['type'] == 'assignment_expression':
            self.analyze_assignment(stmt)
        elif stmt['type'] == 'if_statement':
            self.analyze_if_statement(stmt)
        elif stmt['type'] == 'while_statement':
            self.analyze_while_statement(stmt)
    
    def analyze_variable_declaration(self, stmt):
        """分析变量声明"""
        var_name = stmt['name']
        var_type = stmt['var_type']
        
        # 检查变量是否已声明
        if var_name in self.symbol_table:
            self.errors.append(f"第{stmt['line']}行：变量 '{var_name}' 重复声明")
            return
            
        # 如果有初始化表达式，检查类型是否匹配
        if stmt.get('initializer'):
            init_type = self.get_expression_type(stmt['initializer'])
            if init_type and init_type != var_type:
                self.errors.append(f"第{stmt['line']}行：变量 '{var_name}' 类型不匹配，声明为 {var_type}，但初始化为 {init_type}")
        
        # 将变量添加到符号表
        self.symbol_table[var_name] = var_type
    
    def analyze_assignment(self, stmt):
        """分析赋值语句"""
        var_name = stmt['left']['name']
        
        # 检查变量是否已声明
        if var_name not in self.symbol_table:
            self.errors.append(f"第{stmt.get('line', '?')}行：变量 '{var_name}' 未声明")
            return
            
        # 检查赋值表达式类型是否与变量类型匹配
        var_type = self.symbol_table[var_name]
        expr_type = self.get_expression_type(stmt['right'])
        
        if expr_type and var_type != expr_type:
            self.errors.append(f"第{stmt.get('line', '?')}行：赋值类型不匹配，变量 '{var_name}' 类型为 {var_type}，但表达式类型为 {expr_type}")
    
    def analyze_if_statement(self, stmt):
        """分析if语句"""
        # 检查条件表达式类型
        cond_type = self.get_expression_type(stmt['condition'])
        if cond_type and cond_type != 'bool':
            self.errors.append(f"第{stmt['line']}行：if条件表达式类型错误，应为bool类型，但得到 {cond_type}")
        
        # 分析if语句体
        for body_stmt in stmt['body']:
            self.analyze_statement(body_stmt)
            
        # 分析else语句体
        if stmt.get('else'):
            for else_stmt in stmt['else']:
                self.analyze_statement(else_stmt)
    
    def analyze_while_statement(self, stmt):
        """分析while语句"""
        # 检查条件表达式类型
        cond_type = self.get_expression_type(stmt['condition'])
        if cond_type and cond_type != 'bool':
            self.errors.append(f"第{stmt['line']}行：while条件表达式类型错误，应为bool类型，但得到 {cond_type}")
        
        # 分析while语句体
        for body_stmt in stmt['body']:
            self.analyze_statement(body_stmt)
    
    def get_expression_type(self, expr):
        """获取表达式的类型"""
        if expr['type'] == 'number':
            # 根据数值判断类型
            value = expr['value']
            if '.' in value:
                return 'float'
            else:
                return 'int'
        elif expr['type'] == 'identifier':
            # 从符号表中查找变量类型
            var_name = expr['name']
            if var_name in self.symbol_table:
                return self.symbol_table[var_name]
            else:
                self.errors.append(f"第{expr.get('line', '?')}行：变量 '{var_name}' 未声明")
                return None
        elif expr['type'] == 'binary_expression':
            # 根据运算符和操作数类型判断
            left_type = self.get_expression_type(expr['left'])
            right_type = self.get_expression_type(expr['right'])
            
            if not left_type or not right_type:
                return None
                
            # 比较运算符返回bool类型
            if expr['operator'] in ['==', '!=', '>', '<', '>=', '<=', '&&', '||']:
                return 'bool'
                
            # 算术运算符返回操作数类型
            if expr['operator'] in ['+', '-', '*', '/']:
                # 如果操作数类型不同，返回float
                if left_type != right_type:
                    return 'float'
                return left_type
                
        elif expr['type'] == 'unary_expression':
            # 一元运算符
            operand_type = self.get_expression_type(expr['operand'])
            if expr['operator'] == '!':
                return 'bool'
            return operand_type
            
        return None
