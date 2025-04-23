""" 
第二版修改预计修改以下内容
1 声明语句
2 赋值语句
3 bool运算符
暂定分支为第二版
"""
class Yufa:
    def __init__(self):
        self.keywords = {'if', 'else', 'while'}

    def parse(self, tokens):
        self.tokens = tokens
        self.current = 0
        self.errors = []
        try:
            # 检查main函数结构
            if not self.check_main():
                return {
                    'type': 'error',
                    'errors': self.errors
                }
            # 进入main函数体
            statements = []
            while self.current < len(self.tokens) and self.current_token()[2] != '}':
                stmt = self.statement()
                if stmt:
                    statements.append(stmt)
            # 检查main右大括号
            if not self.current_token() or self.current_token()[2] != '}':
                self.errors.append("main函数缺少右大括号")
            else:
                self.current += 1
            return {
                'type': 'program',
                'body': statements,
                'errors': self.errors
            }
        except Exception as e:
            self.errors.append(f"语法错误：{str(e)}")
            return {
                'type': 'error',
                'errors': self.errors
            }
    def check_main(self):
        # main ( ) {
        if not self.current_token() or self.current_token()[2] != 'main':
            self.errors.append("缺少main函数")
            return False
        self.current += 1
        if not self.current_token() or self.current_token()[2] != '(':
            self.errors.append("main函数缺少左括号")
            return False
        self.current += 1
        if not self.current_token() or self.current_token()[2] != ')':
            self.errors.append("main函数缺少右括号")
            return False
        self.current += 1
        if not self.current_token() or self.current_token()[2] != '{':
            self.errors.append("main函数缺少左大括号")
            return False
        self.current += 1
        return True
    
    def statement(self):
        """语句分析"""
        token = self.current_token()
        if not token:
            return None

        # 处理if和while语句
        if token[2] == 'if':
            return self.if_statement()
        elif token[2] == 'while':
            return self.while_statement()
        # 处理其他语句（表达式语句，必须以分号结尾）
        else:
            return self.expression_statement()

    def expression_statement(self):
        start_token = self.current_token()
        expr = self.expression()
        if expr is None:
            # 语法错误已在expression中记录
            # 跳到下一个分号或右大括号
            while self.current < len(self.tokens) and self.current_token()[2] not in [';', '}']:
                self.current += 1
            if self.current_token() and self.current_token()[2] == ';':
                self.current += 1
            return None
        # 检查分号
        if not self.current_token() or self.current_token()[2] != ';':
            self.errors.append(f"第{start_token[3]}行：表达式缺少分号")
            # 跳到下一个分号或右大括号
            while self.current < len(self.tokens) and self.current_token()[2] not in [';', '}']:
                self.current += 1
            if self.current_token() and self.current_token()[2] == ';':
                self.current += 1
            return None
        self.current += 1
        return expr
    def expression(self):
        token = self.current_token()
        if token and token[2] in ['+', '-']:
            op = token[2]
            self.current += 1
            right = self.term()
            if right is None:
                self.errors.append(f"第{token[3]}行：一元运算符{op}缺少操作数")
                return None
            node = {'type': 'unary_expression', 'operator': op, 'operand': right}
            return self.rest(node)
        else:
            left = self.term()
            if left is None:
                if token:
                    self.errors.append(f"第{token[3]}行：表达式缺少左操作数")
                return None
            return self.rest(left)
        
    def if_statement(self):
        """if语句分析"""
        if_token = self.current_token()
        self.current += 1

        # 检查左括号
        if not self.current_token() or self.current_token()[2] != '(':
            self.errors.append(f"第{if_token[3]}行：if后缺少左括号")
            return None
        self.current += 1

        # 检查条件表达式
        condition = self.condition()
        if not condition:
            self.errors.append(f"第{if_token[3]}行：if条件表达式错误")
            return None

        # 检查右括号
        if not self.current_token() or self.current_token()[2] != ')':
            self.errors.append(f"第{if_token[3]}行：if条件缺少右括号")
            return None
        self.current += 1

        # 检查左大括号
        if not self.current_token() or self.current_token()[2] != '{':
            self.errors.append(f"第{if_token[3]}行：缺少左大括号")
            return None
        self.current += 1

        # 检查语句体中的分号
        self.current += 1  # 跳过左大括号
        while self.current < len(self.tokens) and self.current_token()[2] != '}':
            stmt = self.expression_statement()
            if not stmt:
                self.errors.append(f"第{self.current_token()[3]}行：语句缺少分号")
            
        # 检查右大括号
        if not self.current_token() or self.current_token()[2] != '}':
            self.errors.append(f"第{if_token[3]}行：缺少右大括号")
            return None
        self.current += 1

        # 检查是否有else
        else_part = None
        if self.current_token() and self.current_token()[2] == 'else':
            self.current += 1
            # 检查else的左大括号
            if not self.current_token() or self.current_token()[2] != '{':
                self.errors.append(f"第{if_token[3]}行：else后缺少左大括号")
                return None
            self.current += 1

            # 检查语句体中的分号
            self.current += 1  # 跳过左大括号
            while self.current < len(self.tokens) and self.current_token()[2] != '}':
                stmt = self.expression_statement()
                if not stmt:
                    self.errors.append(f"第{self.current_token()[3]}行：语句缺少分号")
            
            # 检查else的右大括号
            if not self.current_token() or self.current_token()[2] != '}':
                self.errors.append(f"第{if_token[3]}行：else后缺少右大括号")
                return None
            self.current += 1
            else_part = True

        return {
            'type': 'if_statement',
            'line': if_token[3],
            'has_else': else_part is not None
        }

    def while_statement(self):
        """while语句分析"""
        while_token = self.current_token()
        self.current += 1

        # 检查左括号
        if not self.current_token() or self.current_token()[2] != '(':
            self.errors.append(f"第{while_token[3]}行：while后缺少左括号")
            return None
        self.current += 1

        # 检查条件表达式
        condition = self.condition()
        if not condition:
            self.errors.append(f"第{while_token[3]}行：while条件表达式错误")
            return None

        # 检查右括号
        if not self.current_token() or self.current_token()[2] != ')':
            self.errors.append(f"第{while_token[3]}行：while条件缺少右括号")
            return None
        self.current += 1

        # 检查左大括号
        if not self.current_token() or self.current_token()[2] != '{':
            self.errors.append(f"第{while_token[3]}行：缺少左大括号")
            return None
        self.current += 1

        # 检查语句体中的分号
        self.current += 1  # 跳过左大括号
        while self.current < len(self.tokens) and self.current_token()[2] != '}':
            stmt = self.expression_statement()
            if not stmt:
                self.errors.append(f"第{self.current_token()[3]}行：语句缺少分号")
            
        # 检查右大括号
        if not self.current_token() or self.current_token()[2] != '}':
            self.errors.append(f"第{while_token[3]}行：缺少右大括号")
            return None
        self.current += 1

        return {
            'type': 'while_statement',
            'line': while_token[3],
            'condition': condition
        }

    def condition(self):
        """条件表达式分析，现在支持布尔运算"""
        return self.bool_or()

    def bool_or(self):
        """或运算：bool_or -> bool_and (|| bool_and)*"""
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
                'right': right
            }
            
        return left
    
    def bool_and(self):
        """与运算：bool_and -> bool_equality (&& bool_equality)*"""
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
                'right': right
            }
            
        return left
    def bool_equality(self):
        """等于运算：bool_equality -> bool_relation ((== | !=) bool_relation)*"""
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
                'right': right
            }
            
        return left
    def bool_relation(self):
        """关系比较：bool_relation -> bool_not ((> | < | >= | <=) bool_not)*"""
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
                'right': right
            }
            
        return left
    
    def bool_not(self):
        """逻辑非运算：bool_not -> !bool_not | expression"""
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
                'operand': operand
            }
        else:
            return self.expression()
    def expression(self):
        """expr -> term rest"""
        term_val = self.term()
        if term_val is None:
            return None
        return self.rest(term_val)

    def rest(self, left):
        """rest -> + term rest | - term rest | ε"""
        if not self.current_token():
            return left
            
        token = self.current_token()
        if token[2] in ['+', '-']:
            self.current += 1
            term_val = self.term()
            if term_val is None:
                return None
            return self.rest({
                'type': 'binary_expression',
                'operator': token[2],
                'left': left,
                'right': term_val
            })
        return left

    def term(self):
        """term -> factor rest2"""
        factor_val = self.factor()
        if factor_val is None:
            return None
        return self.rest2(factor_val)

    def rest2(self, left):
        """rest2 -> * factor rest2 | / factor rest2 | ε"""
        if not self.current_token():
            return left
            
        token = self.current_token()
        if token[2] in ['*', '/']:
            self.current += 1
            factor_val = self.factor()
            if factor_val is None:
                return None
            return self.rest2({
                'type': 'binary_expression',
                'operator': token[2],
                'left': left,
                'right': factor_val
            })
        return left

    def factor(self):
        """factor -> number | identifier | (expr)"""
        if not self.current_token():
            return None
            
        token = self.current_token()
        self.current += 1
        
        if token[1] in ['整数', '浮点数']:
            return {
                'type': 'number',
                'value': token[2]
            }
        elif token[1] == '标识符':
            return {
                'type': 'identifier',
                'name': token[2]
            }
        elif token[2] == '(':
            expr_val = self.expression()
            if expr_val is None:
                return None
                
            if not self.current_token() or self.current_token()[2] != ')':
                self.errors.append(f"第{token[3]}行：缺少右括号")
                return None
                
            self.current += 1
            return expr_val
        
        self.current -= 1  # 回退一个token
        return None

    def current_token(self):
        if self.current < len(self.tokens):
            return self.tokens[self.current]
        return None

# 测试代码
if __name__ == '__main__':
    tokens = [
        # int x = 5;
        (106, '关键字', 'int', 1),
        (700, '标识符', 'x', 1),
        (205, '运算符', '=', 1),
        (400, '整数', '5', 1),
        (307, '分隔符', ';', 1),
        
        # float y;
        (107, '关键字', 'float', 2),
        (700, '标识符', 'y', 2),
        (307, '分隔符', ';', 2),
        
        # if (x > 0)
        (101, '关键字', 'if', 4),
        (301, '分隔符', '(', 4),
        (700, '标识符', 'x', 4),
        (209, '运算符', '>', 4),
        (400, '整数', '0', 4),
        (302, '分隔符', ')', 4),
        (303, '分隔符', '{', 4),
        
        # y = x + 1;
        (700, '标识符', 'y', 5),
        (205, '运算符', '=', 5),
        (700, '标识符', 'x', 5),
        (201, '运算符', '+', 5),
        (400, '整数', '1', 5),
        (307, '分隔符', ';', 5),
        
        (304, '分隔符', '}', 6),
        
        # else
        (102, '关键字', 'else', 6),
        (303, '分隔符', '{', 6),
        
        # y = 0;
        (700, '标识符', 'y', 7),
        (205, '运算符', '=', 7),
        (400, '整数', '0', 7),
        (307, '分隔符', ';', 7),
        
        (304, '分隔符', '}', 8),
        
        # while (x > 0)
        (103, '关键字', 'while', 10),
        (301, '分隔符', '(', 10),
        (700, '标识符', 'x', 10),
        (209, '运算符', '>', 10),
        (400, '整数', '0', 10),
        (302, '分隔符', ')', 10),
        (303, '分隔符', '{', 10),
        
        # x = x - 1;
        (700, '标识符', 'x', 11),
        (205, '运算符', '=', 11),
        (700, '标识符', 'x', 11),
        (202, '运算符', '-', 11),
        (400, '整数', '1', 11),
        (307, '分隔符', ';', 11),
        # }
        (304, '分隔符', '}', 12)
    ]

    yufa = Yufa()
    result = yufa.parse(tokens)
    if result['type'] == 'error':
        print("语法错误：")
        for error in result['errors']:
            print(error)
    else:
        print("语法分析成功！")
        print("语法树：")
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))