from cifa import Cifa
import json


class Yufa:
    def __init__(self):
        self.keywords = {'if', 'else', 'while', 'int', 'float', 'printf', 'return'}
        self.tokens = []
        self.current = 0
        self.errors = []
        self.valid_operators = {'+', '-', '*', '/', '=', '||', '&&', '!', '==', '!=', '>', '<', '>=', '<='}

    def delete_comment(self, tokens):
        return [token for token in tokens if token[0] != 600]

    def parse(self, tokens):
        self.tokens = self.delete_comment(tokens)
        self.current = 0
        self.errors = []
        try:
            functions = []
            
            # 解析所有函数定义
            while self.current < len(self.tokens):
                func = self.function_declaration()
                if func:
                    functions.append(func)
                else:
                    break
            
            if not functions:
                self.errors.append("没有找到任何函数定义")
                return {'type': 'error', 'errors': self.errors}
            
            # 检查是否有main函数
            main_func = None
            for func in functions:
                if func['name'] == 'main':
                    main_func = func
                    break
            
            if not main_func:
                self.errors.append("缺少main函数")
            
            return {
                'type': 'program',
                'body': functions,
                'line': functions[0]['line'] if functions else 0,
                'errors': self.errors
            }
        except Exception as e:
            self.errors.append(f"语法错误：{str(e)}")
            return {'type': 'error', 'errors': self.errors}

    def function_declaration(self):
        """解析函数声明"""
        # 解析返回类型
        return_type = 'int'  # 默认返回类型
        token = self.current_token()
        if not token:
            return None
            
        if token[2] in ['int', 'float', 'void']:
            return_type = token[2]
            self.current += 1
            token = self.current_token()
        
        # 解析函数名
        if not token or token[1] != '标识符':
            if token:
                self.errors.append(f"第{token[3]}行：期望函数名")
            return None
        
        func_name = token[2]
        func_line = token[3]
        self.current += 1
        
        # 解析参数列表
        token = self.current_token()
        if not token or token[2] != '(':
            self.errors.append(f"第{func_line}行：函数{func_name}缺少左括号")
            return None
        self.current += 1
        
        params = []
        while True:
            token = self.current_token()
            if not token:
                self.errors.append(f"第{func_line}行：函数{func_name}参数列表不完整")
                return None
            
            if token[2] == ')':
                self.current += 1
                break
            
            # 解析参数类型
            if token[2] not in ['int', 'float']:
                self.errors.append(f"第{token[3]}行：无效的参数类型")
                return None
            
            param_type = token[2]
            self.current += 1
            
            # 解析参数名
            token = self.current_token()
            if not token or token[1] != '标识符':
                self.errors.append(f"第{func_line}行：参数缺少标识符")
                return None
            
            param_name = token[2]
            self.current += 1
            
            params.append({
                'type': param_type,
                'name': param_name
            })
            
            # 检查是否有更多参数
            token = self.current_token()
            if token and token[2] == ',':
                self.current += 1
                continue
            elif token and token[2] == ')':
                continue
            else:
                self.errors.append(f"第{func_line}行：参数之间缺少逗号")
                return None
        
        # 检查是否有函数体
        token = self.current_token()
        if not token:
            self.errors.append(f"第{func_line}行：函数声明不完整")
            return None
        
        # 如果是分号，说明是函数声明
        if token[2] == ';':
            self.current += 1
            return {
                'type': 'function_declaration',
                'return_type': return_type,
                'name': func_name,
                'params': params,
                'body': None,  # 函数声明没有函数体
                'line': func_line,
                'is_declaration': True  # 标记这是一个函数声明
            }
        
        # 如果是左大括号，说明是函数定义
        if token[2] != '{':
            self.errors.append(f"第{func_line}行：函数定义缺少左大括号")
            return None
        
        self.current += 1
        
        # 解析函数体
        statements = []
        while self.current < len(self.tokens) and self.current_token() and self.current_token()[2] != '}':
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
        
        token = self.current_token()
        if not token or token[2] != '}':
            self.errors.append(f"第{func_line}行：函数定义缺少右大括号")
        else:
            self.current += 1
        
        return {
            'type': 'function_declaration',
            'return_type': return_type,
            'name': func_name,
            'params': params,
            'body': statements,
            'line': func_line,
            'is_declaration': False  # 标记这是一个函数定义
        }

    def statement(self):
        token = self.current_token()
        if not token:
            return None
        if token[2] == ';':
            self.current += 1
            return {'type': 'empty_statement', 'line': token[3]}
        elif token[2] in ['int', 'float']:
            return self.variable_declaration()
        elif token[2] == 'if':
            return self.if_statement()
        elif token[2] == 'while':
            return self.while_statement()
        elif token[2] == 'printf':
            return self.printf_statement()
        elif token[2] == 'return':
            return self.return_statement()
        else:
            return self.expression_statement()

    def return_statement(self):
        return_token = self.current_token()
        if not return_token:
            return None
        self.current += 1
        
        result = {
            'type': 'return_statement',
            'line': return_token[3],
            'value': None
        }
        
        # 检查是否有返回值
        token = self.current_token()
        if token and token[2] != ';':
            value = self.expression()
            if value:
                result['value'] = value
        
        token = self.current_token()
        if not token or token[2] != ';':
            self.errors.append(f"第{return_token[3]}行：return语句缺少分号")
            return None
        self.current += 1
        
        return result

    def variable_declaration(self):
        type_token = self.current_token()
        if not type_token or type_token[2] not in ['int', 'float']:
            return None
        var_type = type_token[2]
        self.current += 1
        token = self.current_token()
        if not token or token[1] != '标识符':
            self.errors.append(f"第{type_token[3]}行：变量声明缺少标识符")
            self.skip_to_nextline()
            return None
        var_name = token[2]
        self.current += 1
        initializer = None
        if self.current_token() and self.current_token()[2] == '=':
            self.current += 1
            initializer = self.expression()
            if not initializer:
                self.errors.append(f"第{type_token[3]}行：变量初始化表达式无效")
                self.skip_to_nextline()
                return None
        token = self.current_token()
        if not token or token[2] != ';':
            self.errors.append(f"第{type_token[3]}行：变量声明缺少分号")
            self.skip_to_nextline()
            return None
        self.current += 1
        return {
            'type': 'variable_declaration',
            'var_type': var_type,
            'name': var_name,
            'initializer': initializer,
            'line': type_token[3]
        }

    def expression_statement(self):
        start_token = self.current_token()
        if not start_token:
            return None
        expr = self.expression()
        if expr is None:
            return None
        token = self.current_token()
        if not token or token[2] != ';':
            self.errors.append(f"第{start_token[3]}行：表达式缺少分号")
            self.skip_to_nextline()
            return None
        self.current += 1
        return expr

    def if_statement(self):
        if_token = self.current_token()
        if not if_token:
            return None
        self.current += 1
        result = {
            'type': 'if_statement',
            'line': if_token[3],
            'condition': None,
            'body': [],
            'else': None
        }
        token = self.current_token()
        if not token or token[2] != '(':
            self.errors.append(f"第{if_token[3]}行：if后缺少左括号")
        else:
            self.current += 1
        condition = self.condition()
        if not condition:
            self.errors.append(f"第{if_token[3]}行：if条件表达式错误")
        else:
            result['condition'] = condition
            if condition.get('type') == 'assignment_expression':
                self.errors.append(f"第{if_token[3]}行：if条件错误")
        token = self.current_token()
        if not token or token[2] != ')':
            self.errors.append(f"第{if_token[3]}行：if条件缺少右括号")
        else:
            self.current += 1
        token = self.current_token()
        if not token or token[2] != '{':
            self.errors.append(f"第{if_token[3]}行：if后缺少左大括号")
        else:
            self.current += 1
        while self.current < len(self.tokens) and self.current_token() and self.current_token()[2] != '}':
            stmt = self.statement()
            if stmt:
                result['body'].append(stmt)
        token = self.current_token()
        if not token or token[2] != '}':
            self.errors.append(f"第{if_token[3]}行：if后缺少右大括号")
        else:
            self.current += 1
        if self.current_token() and self.current_token()[2] == 'else':
            self.current += 1
            token = self.current_token()
            if not token or token[2] != '{':
                self.errors.append(f"第{if_token[3]}行：else后缺少左大括号")
            else:
                self.current += 1
                result['else'] = []
                while self.current < len(self.tokens) and self.current_token() and self.current_token()[2] != '}':
                    stmt = self.statement()
                    if stmt:
                        result['else'].append(stmt)
                token = self.current_token()
                if not token or token[2] != '}':
                    self.errors.append(f"第{if_token[3]}行：else后缺少右大括号")
                else:
                    self.current += 1
        return result

    def while_statement(self):
        while_token = self.current_token()
        if not while_token:
            return None
        self.current += 1
        result = {
            'type': 'while_statement',
            'line': while_token[3],
            'condition': None,
            'body': []
        }
        token = self.current_token()
        if not token or token[2] != '(':
            self.errors.append(f"第{while_token[3]}行：while后缺少左括号")
        else:
            self.current += 1
        condition = self.condition()
        if not condition:
            self.errors.append(f"第{while_token[3]}行：while条件表达式错误")
        else:
            result['condition'] = condition
            if condition.get('type') == 'assignment_expression':
                self.errors.append(f"第{while_token[3]}行：while条件中不能使用赋值表达式")
        token = self.current_token()
        if not token or token[2] != ')':
            self.errors.append(f"第{while_token[3]}行：while条件缺少右括号")
        else:
            self.current += 1
        token = self.current_token()
        if not token or token[2] != '{':
            self.errors.append(f"第{while_token[3]}行：while后缺少左大括号")
        else:
            self.current += 1
        while self.current < len(self.tokens) and self.current_token() and self.current_token()[2] != '}':
            stmt = self.statement()
            if stmt:
                result['body'].append(stmt)
        token = self.current_token()
        if not token or token[2] != '}':
            self.errors.append(f"第{while_token[3]}行：while后缺少右大括号")
        else:
            self.current += 1
        return result

    def condition(self):
        return self.bool_or()

    def bool_or(self):
        left = self.bool_and()
        if not left:
            return None
        while self.current_token() and self.current_token()[2] == '||':
            op_token = self.current_token()
            self.current += 1
            right = self.bool_and()
            if not right:
                self.errors.append(f"第{op_token[3]}行：逻辑或运算符||缺少右操作数")
                return None
            left = {
                'type': 'binary_expression',
                'operator': '||',
                'left': left,
                'right': right,
                'line': op_token[3]
            }
        return left

    def bool_and(self):
        left = self.bool_equality()
        if not left:
            return None
        while self.current_token() and self.current_token()[2] == '&&':
            op_token = self.current_token()
            self.current += 1
            right = self.bool_equality()
            if not right:
                self.errors.append(f"第{op_token[3]}行：逻辑与运算符&&缺少右操作数")
                return None
            left = {
                'type': 'binary_expression',
                'operator': '&&',
                'left': left,
                'right': right,
                'line': op_token[3]
            }
        return left

    def bool_equality(self):
        left = self.bool_relation()
        if not left:
            return None
        while self.current_token() and self.current_token()[2] in ['==', '!=']:
            op_token = self.current_token()
            op = op_token[2]
            self.current += 1
            right = self.bool_relation()
            if not right:
                self.errors.append(f"第{op_token[3]}行：比较运算符{op}缺少右操作数")
                return None
            left = {
                'type': 'binary_expression',
                'operator': op,
                'left': left,
                'right': right,
                'line': op_token[3]
            }
        return left

    def bool_relation(self):
        left = self.bool_not()
        if not left:
            return None
        while self.current_token() and self.current_token()[2] in ['>', '<', '>=', '<=']:
            op_token = self.current_token()
            op = op_token[2]
            self.current += 1
            right = self.bool_not()
            if not right:
                self.errors.append(f"第{op_token[3]}行：比较运算符{op}缺少右操作数")
                return None
            left = {
                'type': 'binary_expression',
                'operator': op,
                'left': left,
                'right': right,
                'line': op_token[3]
            }
        return left

    def bool_not(self):
        token = self.current_token()
        if token and token[2] == '!':
            self.current += 1
            operand = self.bool_not()
            if not operand:
                self.errors.append(f"第{token[3]}行：逻辑非运算符!缺少操作数")
                return None
            return {
                'type': 'unary_expression',
                'operator': '!',
                'operand': operand,
                'line': token[3]
            }
        return self.expression()

    def expression(self):
        token = self.current_token()
        if not token:
            return None
        if token[2] in ['=', '+', '-']:
            self.errors.append(f"第{token[3]}行：一元运算符{token[2]}缺少左操作数")
            self.skip_to_nextline()
            return None
        if token[1] == '标识符':
            self.current += 1
            if self.current_token() and self.current_token()[2] == '=':
                self.current += 1
                right = self.expression()
                if not right:
                    self.errors.append(f"第{token[3]}行：赋值表达式缺少右操作数")
                    self.skip_to_nextline()
                    return None
                return {
                    'type': 'assignment_expression',
                    'left': {'type': 'identifier', 'name': token[2], 'line': token[3]},
                    'right': right,
                    'line': token[3]
                }
            self.current -= 1
        if token[2] in ['+', '-']:
            self.current += 1
            operand = self.factor()
            if not operand:
                self.errors.append(f"第{token[3]}行：一元运算符{token[2]}缺少操作数")
                self.skip_to_nextline()
                return None
            if operand['type'] not in ['number']:
                self.errors.append(f"第{token[3]}行：一元运算符{token[2]}缺少右操作数")
                self.skip_to_nextline()
                return None
            return {
                'type': 'unary_expression',
                'operator': token[2],
                'operand': operand,
                'line': token[3]
            }
        return self.arithmetic_expression()

    def arithmetic_expression(self):
        left = self.term()
        if not left:
            return None
        while self.current_token() and self.current_token()[2] in ['+', '-']:
            op_token = self.current_token()
            self.current += 1
            next_token = self.current_token()
            if next_token and next_token[2] in ['+', '-']:
                self.errors.append(f"第{next_token[3]}行：无效的运算符序列 {next_token[2]}")
                self.skip_to_nextline()
                return None
            right = self.term()
            if not right:
                self.errors.append(f"第{op_token[3]}行：运算符{op_token[2]}缺少右操作数")
                self.skip_to_nextline()
                return None
            left = {
                'type': 'binary_expression',
                'operator': op_token[2],
                'left': left,
                'right': right,
                'line': op_token[3]
            }
        return left

    def term(self):
        left = self.factor()
        if not left:
            return None
        while self.current_token() and self.current_token()[2] in ['*', '/']:
            op_token = self.current_token()
            self.current += 1
            next_token = self.current_token()
            if not next_token or next_token[2] in ['*', '/', ';']:
                self.errors.append(f"第{op_token[3]}行：运算符{op_token[2]}缺少右操作数")
                self.skip_to_nextline()
                return None
            right = self.factor()
            if not right:
                self.errors.append(f"第{op_token[3]}行：运算符{op_token[2]}缺少右操作数")
                self.skip_to_nextline()
                return None
            left = {
                'type': 'binary_expression',
                'operator': op_token[2],
                'left': left,
                'right': right,
                'line': op_token[3]
            }
        return left

    def factor(self):
        token = self.current_token()
        if not token:
            return None
        if token[2] == ';':
            return None
        self.current += 1
        if token[1] in ['整数', '浮点数']:
            return {
                'type': 'number',
                'value': token[2],
                'line': token[3]
            }
        elif token[1] == '标识符':
            # 检查是否是函数调用
            if self.current_token() and self.current_token()[2] == '(':
                self.current += 1  # 跳过 '('
                func_name = token[2]
                func_line = token[3]
                
                arguments = []
                while True:
                    current_token = self.current_token()
                    if not current_token:
                        self.errors.append(f"第{func_line}行：函数调用{func_name}参数列表不完整")
                        return None
                    
                    if current_token[2] == ')':
                        self.current += 1
                        break
                    
                    arg = self.expression()
                    if not arg:
                        self.errors.append(f"第{func_line}行：函数调用{func_name}参数无效")
                        return None
                    arguments.append(arg)
                    
                    current_token = self.current_token()
                    if current_token and current_token[2] == ',':
                        self.current += 1
                        continue
                    elif current_token and current_token[2] == ')':
                        continue
                    else:
                        self.errors.append(f"第{func_line}行：函数调用{func_name}参数之间缺少逗号")
                        return None
                
                return {
                    'type': 'function_call',
                    'name': func_name,
                    'arguments': arguments,
                    'line': func_line
                }
            else:
                return {
                    'type': 'identifier',
                    'name': token[2],
                    'line': token[3]
                }
        elif token[2] == '(':
            expr = self.expression()
            if not expr:
                self.errors.append(f"第{token[3]}行：括号内的表达式无效")
                self.skip_to_nextline()
                return None
            token = self.current_token()
            if not token or token[2] != ')':
                self.errors.append(f"第{token[3] if token else token[3]}行：缺少右括号")
                return None
            self.current += 1
            expr['line'] = token[3]
            return expr
        elif token[1] == '符号' and token[2] not in self.valid_operators:
            self.errors.append(f"第{token[3]}行：无效运算符 {token[2]}")
            self.skip_to_nextline()
            return None
        self.skip_to_nextline()
        return None

    def current_token(self):
        return self.tokens[self.current] if self.current < len(self.tokens) else None

    def skip_to_nextline(self):
        if not self.current_token():
            return
        line = self.current_token()[3]
        while self.current < len(self.tokens) and self.current_token() and self.current_token()[3] == line:
            self.current += 1

    def printf_statement(self):
        printf_token = self.current_token()
        if not printf_token:
            return None
        self.current += 1
        result = {
            'type': 'printf_statement',
            'line': printf_token[3],
            'arguments': []
        }
        
        token = self.current_token()
        if not token or token[2] != '(':
            self.errors.append(f"第{printf_token[3]}行：printf后缺少左括号")
            return None
        self.current += 1
        
        while True:
            token = self.current_token()
            if not token:
                self.errors.append(f"第{printf_token[3]}行：printf语句不完整")
                return None
                
            if token[2] == ')':
                self.current += 1
                break
                
            arg = self.expression()
            if not arg:
                self.errors.append(f"第{printf_token[3]}行：printf参数无效")
                return None
            result['arguments'].append(arg)
            
            token = self.current_token()
            if token and token[2] == ',':
                self.current += 1
                continue
            elif token and token[2] == ')':
                continue
            else:
                self.errors.append(f"第{printf_token[3]}行：printf参数之间缺少逗号")
                return None
        
        token = self.current_token()
        if not token or token[2] != ';':
            self.errors.append(f"第{printf_token[3]}行：printf语句缺少分号")
            return None
        self.current += 1
        
        return result


if __name__ == '__main__':
    cifa = Cifa()
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
    yufa = Yufa()
    result = yufa.parse(tokens)
    
    if result['type'] == 'error':
        print("语法错误：")
        for error in result['errors']:
            print(error)
    else:
        print("语法分析成功！")
        print("语法树：")
        print(json.dumps(result, indent=2, ensure_ascii=False))
