class Yuyi:
    def __init__(self):
        self.symbol_table = {}  # 符号表，存储变量名和类型
        self.function_table = {}  # 函数表，存储函数名、参数类型和返回类型
        self.errors = []        # 语义错误列表
        self.scopes = [{"global": {}}]  # 作用域栈，初始只有全局作用域
        self.current_scope = "global"  # 当前作用域

    def enter_scope(self, scope_name):
        """进入新的作用域"""
        self.scopes.append({scope_name: {}})
        self.current_scope = scope_name

    def exit_scope(self):
        """退出当前作用域"""
        if len(self.scopes) > 1:  # 保持至少有一个全局作用域
            self.scopes.pop()
            self.current_scope = list(self.scopes[-1].keys())[0]

    def add_symbol(self, name, type_info):
        """添加符号到当前作用域"""
        self.scopes[-1][self.current_scope][name] = type_info

    def lookup_symbol(self, name):
        """查找符号，从内层作用域向外层查找"""
        for scope in reversed(self.scopes):
            for scope_name, symbols in scope.items():
                if name in symbols:
                    return symbols[name]
        return None

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
        self.function_table = {}
        self.errors = []
        self.scopes = [{"global": {}}]
        self.current_scope = "global"
        
        # 分析程序体
        for stmt in ast['body']:
            self.analyze_statement(stmt)
            
        return {
            'type': 'semantic_analysis',
            'symbol_table': self.symbol_table,
            'function_table': self.function_table,
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
        elif stmt['type'] == 'function_declaration':
            self.analyze_function_declaration(stmt)
        elif stmt['type'] == 'function_call':
            self.analyze_function_call(stmt)
        elif stmt['type'] == 'return_statement':
            self.analyze_return_statement(stmt)
    
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
    
    def analyze_function_declaration(self, stmt):
        """分析函数声明"""
        func_name = stmt['name']
        return_type = stmt['return_type']
        params = stmt['params']

        # 检查函数是否已声明
        if func_name in self.function_table:
            self.errors.append(f"第{stmt['line']}行：函数 '{func_name}' 重复声明")
            return

        # 创建函数信息
        func_info = {
            'return_type': return_type,
            'params': [(param['name'], param['type']) for param in params],
            'line': stmt['line']
        }
        self.function_table[func_name] = func_info

        # 进入函数作用域
        self.enter_scope(func_name)

        # 添加参数到函数作用域
        for param in params:
            self.add_symbol(param['name'], param['type'])

        # 分析函数体
        for body_stmt in stmt['body']:
            self.analyze_statement(body_stmt)

        # 检查返回语句
        if not self.has_return_statement(stmt['body']):
            if return_type != 'void':
                self.errors.append(f"第{stmt['line']}行：函数 '{func_name}' 缺少返回语句")

        # 退出函数作用域
        self.exit_scope()

    def analyze_function_call(self, expr):
        """分析函数调用"""
        func_name = expr['name']
        args = expr['arguments']

        # 检查函数是否已声明
        if func_name not in self.function_table:
            self.errors.append(f"第{expr['line']}行：函数 '{func_name}' 未声明")
            return None

        func_info = self.function_table[func_name]
        
        # 检查参数数量
        if len(args) != len(func_info['params']):
            self.errors.append(f"第{expr['line']}行：函数 '{func_name}' 参数数量不匹配")
            return None

        # 检查参数类型
        for i, (arg, (param_name, param_type)) in enumerate(zip(args, func_info['params'])):
            arg_type = self.get_expression_type(arg)
            if arg_type != param_type:
                self.errors.append(f"第{expr['line']}行：函数 '{func_name}' 第{i+1}个参数类型不匹配，期望 {param_type}，得到 {arg_type}")

        return func_info['return_type']

    def has_return_statement(self, body):
        """检查函数体是否包含返回语句"""
        for stmt in body:
            if stmt['type'] == 'return_statement':
                return True
            elif stmt['type'] in ['if_statement', 'while_statement']:
                if self.has_return_statement(stmt['body']):
                    return True
                if stmt.get('else') and self.has_return_statement(stmt['else']):
                    return True
        return False

    def analyze_return_statement(self, stmt):
        """分析返回语句"""
        if self.current_scope == "global":
            self.errors.append(f"第{stmt['line']}行：返回语句不能在全局作用域")
            return

        func_info = self.function_table[self.current_scope]
        if func_info['return_type'] == 'void':
            if stmt.get('value'):
                self.errors.append(f"第{stmt['line']}行：void函数不能返回值")
        else:
            if not stmt.get('value'):
                self.errors.append(f"第{stmt['line']}行：非void函数必须返回值")
            else:
                return_type = self.get_expression_type(stmt['value'])
                if return_type != func_info['return_type']:
                    self.errors.append(f"第{stmt['line']}行：返回类型不匹配，期望 {func_info['return_type']}，得到 {return_type}")

    def get_expression_type(self, expr):
        """获取表达式的类型"""
        if expr['type'] == 'function_call':
            return self.analyze_function_call(expr)
        elif expr['type'] == 'number':
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
