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
            if not self.check_main():
                return {'type': 'error', 'errors': self.errors}
            statements = []
            while self.current < len(self.tokens) and self.current_token() and self.current_token()[2] != '}':
                stmt = self.statement()
                if stmt:
                    statements.append(stmt)
                # 如果未生成语句（可能因错误），跳到语句边界但不消耗分号
                elif self.current_token():
                    self.skip_to_statement_boundary(consume_semicolon=False)
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
            return {'type': 'error', 'errors': self.errors}

    def check_main(self):
        token = self.current_token()
        if not token or token[2] != 'main':
            self.errors.append("缺少main函数")
            return False
        self.current += 1
        token = self.current_token()
        if not token or token[2] != '(':
            self.errors.append("main函数缺少左括号")
            return False
        self.current += 1
        token = self.current_token()
        if not token or token[2] != ')':
            self.errors.append("main函数缺少右括号")
            return False
        self.current += 1
        token = self.current_token()
        if not token or token[2] != '{':
            self.errors.append("main函数缺少左大括号")
            return False
        self.current += 1
        return True

    def statement(self):
        token = self.current_token()
        if not token:
            return None
        if token[2] == ';':
            self.current += 1
            return {'type': 'empty_statement'}
        elif token[2] == 'if':
            return self.if_statement()
        elif token[2] == 'while':
            return self.while_statement()
        else:
            return self.expression_statement()

    def expression_statement(self):
        start_token = self.current_token()
        if not start_token:
            return None
        expr = self.expression()
        if expr is None:
            self.skip_to_statement_boundary(consume_semicolon=False)
            return None
        token = self.current_token()
        if not token or token[2] == ')':
            self.errors.append(f"第{start_token[3]}行：表达式缺少左括号")
        if not token or token[2] != ';':
            self.errors.append(f"第{start_token[3]}行：表达式缺少分号")
            self.skip_to_statement_boundary(consume_semicolon=False)
            return None
        self.current += 1
        return expr

    def if_statement(self):
        if_token = self.current_token()
        if not if_token:
            return None
        self.current += 1
        token = self.current_token()
        if not token or token[2] != '(':
            self.errors.append(f"第{if_token[3]}行：if后缺少左括号")
            self.skip_to([')', '}'])
            return None
        self.current += 1
        condition = self.condition()
        if not condition:
            self.errors.append(f"第{if_token[3]}行：if条件表达式错误")
            self.skip_to([')', '}'])
            if self.current_token() and self.current_token()[2] == ')':
                self.current += 1
            return None
        token = self.current_token()
        if not token or token[2] != ')':
            self.errors.append(f"第{if_token[3]}行：if条件缺少右括号")
            self.skip_to(['}'])
            return None
        self.current += 1
        token = self.current_token()
        if not token or token[2] != '{':
            self.errors.append(f"第{if_token[3]}行：if后缺少左大括号")
            self.skip_to(['}'])
            return None
        self.current += 1
        body = []
        while self.current < len(self.tokens) and self.current_token() and self.current_token()[2] != '}':
            stmt = self.statement()
            if stmt:
                body.append(stmt)
        token = self.current_token()
        if not token or token[2] != '}':
            self.errors.append(f"第{if_token[3]}行：if后缺少右大括号")
            return None
        self.current += 1
        else_body = None
        if self.current_token() and self.current_token()[2] == 'else':
            self.current += 1
            token = self.current_token()
            if not token or token[2] != '{':
                self.errors.append(f"第{if_token[3]}行：else后缺少左大括号")
                self.skip_to(['}'])
                return None
            self.current += 1
            else_body = []
            while self.current < len(self.tokens) and self.current_token() and self.current_token()[2] != '}':
                stmt = self.statement()
                if stmt:
                    else_body.append(stmt)
            token = self.current_token()
            if not token or token[2] != '}':
                self.errors.append(f"第{if_token[3]}行：else后缺少右大括号")
                return None
            self.current += 1
        return {
            'type': 'if_statement',
            'line': if_token[3],
            'condition': condition,
            'body': body,
            'else': else_body
        }

    def while_statement(self):
        while_token = self.current_token()
        if not while_token:
            return None
        self.current += 1
        token = self.current_token()
        if not token or token[2] != '(':
            self.errors.append(f"第{while_token[3]}行：while后缺少左括号")
            self.skip_to([')', '}'])
            return None
        self.current += 1
        condition = self.condition()
        if not condition:
            self.errors.append(f"第{while_token[3]}行：while条件表达式错误")
            self.skip_to([')', '}'])
            if self.current_token() and self.current_token()[2] == ')':
                self.current += 1
            return None
        token = self.current_token()
        if not token or token[2] != ')':
            self.errors.append(f"第{while_token[3]}行：while条件缺少右括号")
            self.skip_to(['}'])
            return None
        self.current += 1
        token = self.current_token()
        if not token or token[2] != '{':
            self.errors.append(f"第{while_token[3]}行：while后缺少左大括号")
            self.skip_to(['}'])
            return None
        self.current += 1
        body = []
        while self.current < len(self.tokens) and self.current_token() and self.current_token()[2] != '}':
            stmt = self.statement()
            if stmt:
                body.append(stmt)
        token = self.current_token()
        if not token or token[2] != '}':
            self.errors.append(f"第{while_token[3]}行：while后缺少右大括号")
            return None
        self.current += 1
        return {
            'type': 'while_statement',
            'line': while_token[3],
            'condition': condition,
            'body': body
        }
    # 条件表达式
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
                'right': right
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
                'right': right
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
                'right': right
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
                'right': right
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
                'operand': operand
            }
        return self.expression()

    def expression(self):
        """expr -> term rest"""
        token = self.current_token()
        if not token:
            return None
        # 检测孤立的赋值运算符
        if token[2] == '=':
            self.errors.append(f"第{token[3]}行：缺少左操作数 {token[2]}")
            self.current += 1
            self.skip_to_statement_boundary(consume_semicolon=False)
            return None
        # 赋值表达式
        if token[1] == '标识符':
            self.current += 1
            if self.current_token() and self.current_token()[2] == '=':
                self.current += 1
                right = self.expression()
                if not right:
                    self.errors.append(f"第{token[3]}行：赋值表达式缺少右操作数")
                    self.skip_to_statement_boundary(consume_semicolon=False)
                    return None
                return {
                    'type': 'assignment_expression',
                    'left': {'type': 'identifier', 'name': token[2]},
                    'right': right
                }
            self.current -= 1
        # 一元运算符
        if token[2] in ['+', '-']:
            self.current += 1
            operand = self.factor()
            if not operand:
                self.errors.append(f"第{token[3]}行：一元运算符{token[2]}缺少操作数")
                self.skip_to_statement_boundary(consume_semicolon=False)
                return None
            if operand['type'] not in ['number']:
                self.errors.append(f"第{token[3]}行：一元运算符{token[2]}的操作数必须是数字")
                self.skip_to_statement_boundary(consume_semicolon=False)
                return None
            return {
                'type': 'unary_expression',
                'operator': token[2],
                'operand': operand
            }
        # 算术表达式
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
                self.skip_to_statement_boundary(consume_semicolon=False)
                return None
            right = self.term()
            if not right:
                self.errors.append(f"第{op_token[3]}行：运算符{op_token[2]}缺少右操作数")
                self.skip_to_statement_boundary(consume_semicolon=False)
                return None
            left = {
                'type': 'binary_expression',
                'operator': op_token[2],
                'left': left,
                'right': right
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
                self.skip_to_statement_boundary(consume_semicolon=False)
                return None
            right = self.factor()
            if not right:
                self.errors.append(f"第{op_token[3]}行：运算符{op_token[2]}缺少右操作数")
                self.skip_to_statement_boundary(consume_semicolon=False)
                return None
            left = {
                'type': 'binary_expression',
                'operator': op_token[2],
                'left': left,
                'right': right
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
                'value': token[2]
            }
        elif token[1] == '标识符':
            return {
                'type': 'identifier',
                'name': token[2]
            }
        elif token[2] == '(':
            expr = self.expression()
            if not expr:
                self.errors.append(f"第{token[3]}行：括号内的表达式无效")
                self.skip_to([')', ';', '}'])
                return None
            token = self.current_token()
            if not token or token[2] != ')':
                self.errors.append(f"第{token[3] if token else token[3]}行：缺少右括号")
                return None
            self.current += 1
            return expr
        elif token[1] == '符号' and token[2] not in self.valid_operators:
            self.errors.append(f"第{token[3]}行：无效运算符 {token[2]}")
            self.skip_to_statement_boundary(consume_semicolon=False)
            return None
        self.skip_to_statement_boundary(consume_semicolon=False)
        return None

    def current_token(self):
        return self.tokens[self.current] if self.current < len(self.tokens) else None

    def skip_to(self, targets):
        while self.current < len(self.tokens) and self.current_token() and self.current_token()[2] not in targets:
            self.current += 1
        if self.current < len(self.tokens) and self.current_token() and self.current_token()[2] in targets:
            self.current += 1

    def skip_to_statement_boundary(self, consume_semicolon=True):
        while self.current < len(self.tokens) and self.current_token() and self.current_token()[2] not in [';', '}', 'if', 'while', 'else']:
            self.current += 1
        if consume_semicolon and self.current < len(self.tokens) and self.current_token() and self.current_token()[2] == ';':
            self.current += 1


if __name__ == '__main__':
    tokens = [(700, '标识符', 'main', 1), (301, '分隔符', '(', 1), (302, '分隔符', ')', 1), (303, '分隔符', '{', 1), (101, '关键字', 'if', 2), (301, '分隔符', '(', 2), (700, '标识符', 'x', 2), (205, '运算符', '=', 2), (400, '整数', '0', 2), (302, '分隔符', ')', 2), (303, '分隔符', '{', 2), (700, '标识符', 'a', 3), (205, '运算符', '=', 3), (700, '标识符', 'a', 3), (201, '运算符', '+', 3), (400, '整数', '1', 3), (307, '分隔符', ';', 3), (304, '分隔符', '}', 4), (304, '分隔符', '}', 5)]
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