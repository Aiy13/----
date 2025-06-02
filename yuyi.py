import json

from cifa import Cifa
from yufa import Yufa


class Yuyi:
    def __init__(self):
        self.symbol_table = []  # 符号表，存储 [{name, type, scope, value}, ...]
        self.function_table = {}  # 函数表，存储函数名、参数类型和返回类型
        self.errors = []  # 语义错误列表
        self.scopes = [[]]  # 初始化时添加全局作用域
        self.current_scope = 0  # 当前作用域索引
        self.functions = {}  # 存储函数信息
        self.current_function = None  # 当前正在分析的函数名

    def enter_scope(self):
        """进入新的作用域"""
        self.scopes.append([])  # 添加新的作用域列表
        self.current_scope = len(self.scopes) - 1

    def exit_scope(self):
        """退出当前作用域"""
        if self.current_scope > 0:  # 保持全局作用域
            self.scopes.pop()
            self.current_scope = len(self.scopes) - 1

    def add_symbol(self, name, type, value=None):
        """添加符号到当前作用域"""
        # 只检查当前作用域内的重复声明
        for symbol in self.scopes[self.current_scope]:
            if symbol['name'] == name:
                self.error(f"变量 {name} 重复声明")
                return False
                    
        # 创建符号信息
        symbol_info = {
            'name': name,
            'type': type,
            'value': value,
            'is_initialized': value is not None,
            'scope': self.current_scope  # 添加scope字段
        }
        
        # 添加到当前作用域
        self.scopes[self.current_scope].append(symbol_info)
        self.symbol_table.append(symbol_info)
        return True

    def find_symbol(self, name):
        """查找符号"""
        for scope in reversed(self.scopes):  # 从内层作用域向外查找
            for symbol in scope:
                if symbol['name'] == name:
                    return symbol
        return None

    def analyze(self, ast):
        """分析语法树"""
        if ast['type'] != 'program':
            self.error("语法树根节点必须是program类型")
            return
        
        # 处理程序中的所有函数声明和定义
        for stmt in ast['body']:
            if stmt['type'] != 'function_declaration':
                self.error("顶层语句必须是函数声明或定义")
                return
            self.analyze_function_declaration(stmt)
        
        # 检查是否有main函数
        if 'main' not in self.functions:
            self.error("缺少main函数")
            return

        return {
            'type': 'semantic_analysis',
            'symbol_table': self.symbol_table,
            'function_table': self.functions,  # 使用 self.functions 而不是 self.function_table
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
        elif t == 'printf_statement':
            self.analyze_printf_statement(stmt)

    def analyze_printf_statement(self, stmt):
        """分析printf语句"""
        # 检查参数类型
        for arg in stmt.get('arguments', []):
            arg_type = self.get_expression_type(arg)
            # printf可以接受各种类型的参数，这里只检查变量是否已声明
            pass

    def analyze_variable_declaration(self, stmt):
        var_name = stmt['name']
        var_type = stmt['var_type']

        # 检查当前作用域内的重复声明
        for symbol in self.scopes[self.current_scope]:
            if symbol['name'] == var_name:
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
        symbol = self.find_symbol(var_name)
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
        symbol['value'] = expr_value
        symbol['is_initialized'] = True

    def analyze_if_statement(self, stmt):
        cond_type = self.get_expression_type(stmt['condition'])
        if cond_type and cond_type != 'bool':
            self.errors.append(f"第{stmt['line']}行：if条件表达式类型错误，应为bool类型，但得到 {cond_type}")

        # if 分支新作用域
        self.enter_scope()
        for body_stmt in stmt.get('body', []):
            self.analyze_statement(body_stmt)
        self.exit_scope()

        # else 分支新作用域
        if stmt.get('else'):
            self.enter_scope()
            for else_stmt in stmt['else']:
                self.analyze_statement(else_stmt)
            self.exit_scope()

    def analyze_while_statement(self, stmt):
        cond_type = self.get_expression_type(stmt['condition'])
        if cond_type and cond_type != 'bool':
            self.errors.append(f"第{stmt['line']}行：while条件表达式类型错误，应为bool类型，但得到 {cond_type}")

        # while 分支新作用域
        self.enter_scope()
        for body_stmt in stmt.get('body', []):
            self.analyze_statement(body_stmt)
        self.exit_scope()

    def analyze_function_declaration(self, node):
        """分析函数声明或定义"""
        func_name = node['name']
        return_type = node['return_type']
        is_declaration = node.get('is_declaration', False)
        
        # 检查函数是否已存在
        if func_name in self.functions:
            existing_func = self.functions[func_name]
            
            # 如果已存在的是声明，当前也是声明 -> 允许（可以有多个声明）
            # 如果已存在的是声明，当前是定义 -> 允许（声明后定义）
            # 如果已存在的是定义，当前是声明 -> 允许（定义后声明，虽然少见但合法）
            # 如果已存在的是定义，当前也是定义 -> 错误（重复定义）
            
            if not existing_func['is_declaration'] and not is_declaration:
                self.error(f"函数 {func_name} 重复定义")
                return
            
            # 检查函数签名是否匹配（返回类型和参数类型）
            if (existing_func['return_type'] != return_type or 
                len(existing_func['param_types']) != len(node['params']) or
                existing_func['param_types'] != [param['type'] for param in node['params']]):
                self.error(f"函数 {func_name} 的声明和定义签名不匹配")
                return
            
            # 如果当前是定义，更新函数信息
            if not is_declaration:
                self.functions[func_name]['is_declaration'] = False
        else:
            # 检查参数
            param_types = []
            param_names = []
            for param in node['params']:
                param_type = param['type']
                param_name = param['name']
                
                # 检查参数类型
                if param_type not in ['int', 'float', 'char']:
                    self.error(f"不支持的参数类型: {param_type}")
                    return
                
                # 检查参数名是否重复
                if param_name in param_names:
                    self.error(f"参数 {param_name} 重复声明")
                    return
                
                param_types.append(param_type)
                param_names.append(param_name)
            
            # 记录函数信息
            self.functions[func_name] = {
                'return_type': return_type,
                'param_types': param_types,
                'param_names': param_names,
                'is_declaration': is_declaration
            }
            
            # 更新 function_table 以保持兼容性
            self.function_table[func_name] = {
                'return_type': return_type,
                'params': [(name, ptype) for name, ptype in zip(param_names, param_types)]
            }
        
        # 如果是函数定义（不是声明），分析函数体
        if not is_declaration and node.get('body'):
            self.current_function = func_name
            self.enter_scope()  # 进入函数作用域
            
            # 获取参数信息（可能是新函数或已存在函数）
            func_info = self.functions[func_name]
            param_names = func_info['param_names']
            param_types = func_info['param_types']
            
            # 将参数添加到作用域
            for param_name, param_type in zip(param_names, param_types):
                self.add_symbol(param_name, param_type)
            
            # 分析函数体
            for stmt in node['body']:
                self.analyze_statement(stmt)
                
            self.exit_scope()  # 退出函数作用域
            self.current_function = None

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
        if self.current_scope == 0:
            self.errors.append(f"第{stmt['line']}行：返回语句不能在全局作用域")
            return

        # 使用 current_function 来获取当前函数信息
        if not self.current_function:
            return
            
        func_info = self.functions.get(self.current_function)
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
            symbol = self.find_symbol(expr['name'])
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
            sym = self.find_symbol(expr['name'])
            return sym.get('value') if sym else None
        return None

    def error(self, message):
        self.errors.append(message)


if __name__ == '__main__':
    cifa = Cifa()
    yufa = Yufa()
    yuyi = Yuyi()
    test_code = """
    int add(int a, int b);
int main() 
{ 
    int a = 1; 
    int b = 2; 
    int z = add(a, b);
    printf(z);
}

int add(int a, int b)
{
    return a + b;
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
        print("错误列表：")
        for error in yuyi.errors:
            print(error)
