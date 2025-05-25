import json

from cifa import Cifa
from yufa import Yufa


class Yuyi:
    def __init__(self):
        self.symbol_table = []  # 符号表，存储 [{name, type, scope, value}, ...]
        self.function_table = {}  # 函数表，存储函数名、参数类型和返回类型
        self.errors = []  # 语义错误列表
        self.scopes = [{"global": []}]  # 作用域栈，初始只有全局作用域
        self.current_scope = "global"  # 当前作用域

    def enter_scope(self, scope_name):
        """进入新的作用域"""
        self.scopes.append({scope_name: []})
        self.current_scope = scope_name

    def exit_scope(self):
        """退出当前作用域"""
        if len(self.scopes) > 1:
            self.scopes.pop()
            self.current_scope = list(self.scopes[-1].keys())[0]

    def add_symbol(self, name, type_info, value=None):
        """添加符号到当前作用域"""
        symbol_info = {
            'name': name,
            'type': type_info,
            'scope': self.current_scope,
            'value': value
        }
        self.scopes[-1][self.current_scope].append(symbol_info)
        self.symbol_table.append(symbol_info)

    def lookup_symbol(self, name):
        """查找符号，从内层作用域向外层查找"""
        for scope in reversed(self.scopes):
            for _, symbols in scope.items():
                for symbol in symbols:
                    if symbol['name'] == name:
                        return symbol
        return None

    def analyze(self, ast):
        """对语法树进行语义分析"""
        if ast.get('type') == 'error':
            return {'type': 'error', 'errors': ast.get('errors', [])}

        # 重置表和状态
        self.symbol_table.clear()
        self.function_table.clear()
        self.errors.clear()
        self.scopes = [{"global": []}]
        self.current_scope = "global"

        # 分析顶层语句
        for stmt in ast.get('body', []):
            self.analyze_statement(stmt)

        return {
            'type': 'semantic_analysis',
            'symbol_table': self.symbol_table,
            'function_table': self.function_table,
            'errors': self.errors
        }

    def analyze_statement(self, stmt):
        """通过类型分发调用对应分析方法"""
        t = stmt.get('type')
        if t == 'variable_declaration':
            self.analyze_variable_declaration(stmt)
        elif t == 'assignment_expression':
            self.analyze_assignment(stmt)
        elif t == 'if_statement':
            self.analyze_if_statement(stmt)
        elif t == 'while_statement':
            self.analyze_while_statement(stmt)
        elif t == 'function_declaration':
            self.analyze_function_declaration(stmt)
        elif t == 'function_call':
            self.analyze_function_call(stmt)
        elif t == 'return_statement':
            self.analyze_return_statement(stmt)

    def analyze_variable_declaration(self, stmt):
        var_name = stmt['name']
        var_type = stmt['var_type']

        # 重复声明检测
        if self.lookup_symbol(var_name):
            self.errors.append(f"第{stmt['line']}行：变量 '{var_name}' 重复声明")
            return

        initializer_value = None
        # 初始化表达式类型检查
        if stmt.get('initializer'):
            init_type = self.get_expression_type(stmt['initializer'])
            initializer_value = self.get_expression_value(stmt['initializer'])
            if init_type and init_type != var_type:
                self.errors.append(
                    f"第{stmt['line']}行：变量 '{var_name}' 类型不匹配，声明为 {var_type}，但初始化为 {init_type}")

        # 添加符号
        self.add_symbol(var_name, var_type, initializer_value)

    def analyze_assignment(self, stmt):
        var_name = stmt['left']['name']
        symbol = self.lookup_symbol(var_name)
        if not symbol:
            self.errors.append(f"第{stmt.get('line', '?')}行：变量 '{var_name}' 未声明")
            return

        var_type = symbol['type']
        expr_type = self.get_expression_type(stmt['right'])
        expr_value = self.get_expression_value(stmt['right'])

        if expr_type and expr_type != var_type:
            self.errors.append(
                f"第{stmt.get('line', '?')}行：赋值类型不匹配，变量 '{var_name}' 类型为 {var_type}，但表达式类型为 {expr_type}")

        # 更新符号表中值
        for sym in self.symbol_table:
            if sym['name'] == var_name and sym['scope'] == symbol['scope']:
                sym['value'] = expr_value
                break

    def analyze_if_statement(self, stmt):
        cond_type = self.get_expression_type(stmt['condition'])
        if cond_type and cond_type != 'bool':
            self.errors.append(f"第{stmt['line']}行：if条件表达式类型错误，应为bool类型，但得到 {cond_type}")

        # if 分支新作用域
        self.enter_scope(f"if_{stmt['line']}")
        for body_stmt in stmt.get('body', []):
            self.analyze_statement(body_stmt)
        self.exit_scope()

        # else 分支新作用域
        if stmt.get('else'):
            self.enter_scope(f"else_{stmt['line']}")
            for else_stmt in stmt['else']:
                self.analyze_statement(else_stmt)
            self.exit_scope()

    def analyze_while_statement(self, stmt):
        cond_type = self.get_expression_type(stmt['condition'])
        if cond_type and cond_type != 'bool':
            self.errors.append(f"第{stmt['line']}行：while条件表达式类型错误，应为bool类型，但得到 {cond_type}")

        # while 分支新作用域
        self.enter_scope(f"while_{stmt['line']}")
        for body_stmt in stmt.get('body', []):
            self.analyze_statement(body_stmt)
        self.exit_scope()

    def analyze_function_declaration(self, stmt):
        func_name = stmt['name']
        return_type = stmt['return_type']
        params = stmt.get('params', [])

        if func_name in self.function_table:
            self.errors.append(f"第{stmt['line']}行：函数 '{func_name}' 重复声明")
            return

        # 记录函数签名
        self.function_table[func_name] = {
            'return_type': return_type,
            'params': [(p['name'], p['type']) for p in params],
            'line': stmt['line']
        }

        # 进入函数新作用域
        self.enter_scope(func_name)
        # 添加参数
        for p in params:
            self.add_symbol(p['name'], p['type'], None)
        # 分析函数体
        for body_stmt in stmt.get('body', []):
            self.analyze_statement(body_stmt)

        # 检查返回
        if return_type != 'void' and not self.has_return_statement(stmt.get('body', [])):
            self.errors.append(f"第{stmt['line']}行：函数 '{func_name}' 缺少返回语句")

        self.exit_scope()

    def analyze_function_call(self, expr):
        func_name = expr['name']
        args = expr.get('arguments', [])
        line = expr.get('line', '?')

        if func_name not in self.function_table:
            self.errors.append(f"第{line}行：函数 '{func_name}' 未声明")
            return None

        info = self.function_table[func_name]
        if len(args) != len(info['params']):
            self.errors.append(f"第{line}行：函数 '{func_name}' 参数数量不匹配")
            return None

        for i, (arg, (_, ptype)) in enumerate(zip(args, info['params'])):
            atype = self.get_expression_type(arg)
            if atype and atype != ptype:
                self.errors.append(
                    f"第{line}行：函数 '{func_name}' 第{i+1}个参数类型不匹配，期望 {ptype}，得到 {atype}")

        return info['return_type']

    def has_return_statement(self, body):
        for s in body:
            if s.get('type') == 'return_statement':
                return True
            if s.get('type') in ('if_statement', 'while_statement'):
                if self.has_return_statement(s.get('body', [])):
                    return True
                if s.get('else') and self.has_return_statement(s['else']):
                    return True
        return False

    def analyze_return_statement(self, stmt):
        if self.current_scope == 'global':
            self.errors.append(f"第{stmt['line']}行：返回语句不能在全局作用域")
            return

        func_info = self.function_table.get(self.current_scope)
        if not func_info:
            return
        ret_type = func_info['return_type']
        val = stmt.get('value')

        if ret_type == 'void':
            if val is not None:
                self.errors.append(f"第{stmt['line']}行：void函数不能返回值")
        else:
            if val is None:
                self.errors.append(f"第{stmt['line']}行：非void函数必须返回值")
            else:
                vtype = self.get_expression_type(val)
                if vtype and vtype != ret_type:
                    self.errors.append(
                        f"第{stmt['line']}行：返回类型不匹配，期望 {ret_type}，得到 {vtype}")

    def get_expression_type(self, expr):
        t = expr.get('type')
        if t == 'function_call':
            return self.analyze_function_call(expr)
        if t == 'number':
            return 'float' if '.' in str(expr.get('value')) else 'int'
        if t == 'identifier':
            symbol = self.lookup_symbol(expr['name'])
            if symbol:
                return symbol['type']
            self.errors.append(f"第{expr.get('line','?')}行：变量 '{expr['name']}' 未声明")
            return None
        if t == 'binary_expression':
            lt = self.get_expression_type(expr['left'])
            rt = self.get_expression_type(expr['right'])
            if lt and rt:
                op = expr.get('operator')
                if op in ('==','!=','>','<','>=','<=','&&','||'):
                    return 'bool'
                if op in ('+','-','*','/'):
                    return lt if lt == rt else 'float'
            return None
        if t == 'unary_expression':
            op = expr.get('operator')
            if op == '!':
                return 'bool'
            return self.get_expression_type(expr.get('operand'))
        return None

    def get_expression_value(self, expr):
        t = expr.get('type')
        if t == 'number':
            return expr.get('value')
        if t == 'identifier':
            sym = self.lookup_symbol(expr['name'])
            return sym.get('value') if sym else None
        return None


if __name__ == '__main__':
    cifa = Cifa()
    yufa = Yufa()
    yuyi = Yuyi()
    test_code = """
    main()
    {
        int a = 1;
        int b = 2;
        if((a + b) > 0)
        {
            int x = 7;
            a = 7;
            b = 1;
        }
        x = 10;
    }
    """
    tokens = cifa.cifafenxi(test_code)
    result = yufa.parse(tokens)
    if result.get('type') == 'error':
        print("语法错误：")
        for err in result.get('errors', []):
            print(err)
    else:
        yuyi_result = yuyi.analyze(result)
        print("符号表：")
        print(json.dumps(yuyi_result['symbol_table'], indent=2, ensure_ascii=False))
