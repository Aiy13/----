from youhua import youhua

class Zhongjian:
    def __init__(self):
        self.quads = []  # 存储四元式
        self.temp_count = 0  # 临时变量计数器
        self.label_count = 0  # 标签计数器
        self.next_quad = 0  # 下一个四元式索引
        self.function_table = {}  # 存储函数信息

    def new_temp(self):
        """生成新的临时变量名称"""
        temp = f"T{self.temp_count}"
        self.temp_count += 1
        return temp

    def new_label(self):
        """生成新的标签名称"""
        label = f"L{self.label_count}"
        self.label_count += 1
        return label

    def emit(self, op, arg1, arg2, result):
        """生成四元式并添加到列表中"""
        self.quads.append((op, arg1, arg2, result))
        self.next_quad += 1

    def merge(self, list1, list2):
        """合并两个四元式索引列表（真假链）"""
        return list1 + list2

    def backpatch(self, quad_indices, label):
        """回填四元式的标签"""
        for idx in quad_indices:
            op, arg1, arg2, _ = self.quads[idx]
            self.quads[idx] = (op, arg1, arg2, label)

    def generate(self, syntax_tree):
        """生成中间代码"""
        if not syntax_tree or syntax_tree['type'] != 'program':
            return []
        
        self.quads = []  # 重置四元式列表
        self.temp_count = 0  # 重置临时变量计数
        self.label_count = 0  # 重置标签计数
        self.next_quad = 0  # 重置四元式索引
        
        # 生成程序开始标记
        self.emit('program', None, None, 'start')
        
        # 处理程序体
        for stmt in syntax_tree.get('body', []):
            if stmt['type'] == 'function_declaration' and not stmt.get('is_declaration', False):
                # 只处理函数定义，忽略函数声明
                self.gen_function_declaration(stmt)
        
        # 生成程序结束标记
        self.emit('program', None, None, 'end')
        
        return self.quads  # 返回生成的四元式列表

    def gen_function_declaration(self, func):
        """生成函数定义的代码"""
        func_name = func['name']
        params = func.get('params', [])
        body = func.get('body', [])
        
        # 生成函数标签 - 适配Mubiao的func_前缀格式
        self.emit('label', None, None, f"func_{func_name}")
        
        # 处理函数体
        for stmt in body:
            self.gen_statement(stmt)

    def gen_statement(self, stmt):
        """处理语句节点"""
        if stmt['type'] == 'if_statement':
            self.gen_if_statement(stmt)
        elif stmt['type'] == 'while_statement':
            self.gen_while_statement(stmt)
        elif stmt['type'] == 'variable_declaration':
            self.gen_variable_declaration(stmt)
        elif stmt['type'] == 'assignment_expression':
            self.gen_assignment_expression(stmt)
        elif stmt['type'] == 'printf_statement':
            self.gen_printf_statement(stmt)
        elif stmt['type'] == 'return_statement':
            self.gen_return_statement(stmt)
        elif stmt['type'] == 'empty_statement':
            pass

    def gen_variable_declaration(self, decl):
        """生成变量声明的代码"""
        if decl.get('initializer'):
            if decl['initializer']['type'] == 'function_call':
                # 处理函数调用赋值
                result = self.gen_function_call(decl['initializer'])
                self.emit('=', result, None, decl['name'])
            else:
                result = self.gen_expression(decl['initializer'])
                self.emit('=', result, None, decl['name'])
        else:
            # 没有初始化值的变量声明，不生成四元式（只是声明）
            pass

    def gen_assignment_expression(self, expr):
        """生成赋值表达式的代码"""
        result = self.gen_expression(expr['right'])
        # 处理左值
        if isinstance(expr['left'], dict) and expr['left']['type'] == 'identifier':
            var_name = expr['left']['name']
        else:
            var_name = expr['left']
        self.emit('=', result, None, var_name)

    def gen_if_statement(self, stmt):
        """生成if语句的代码"""
        # 生成条件代码
        true_list, false_list = self.gen_condition(stmt['condition'])

        # 记录当前四元式序号作为true分支的起始位置
        true_start = self.next_quad

        # 生成if体的代码
        for s in stmt.get('body', []):
            self.gen_statement(s)

        if stmt.get('else'):
            # 记录else分支的起始位置
            else_start = self.next_quad
            # 生成else体的代码
            for s in stmt.get('else', []):
                self.gen_statement(s)
            # 记录结束位置
            end_pos = self.next_quad
            # 回填false分支跳转到else分支
            self.backpatch(false_list, else_start)
            # 在if体结束后添加跳转到结束位置的指令
            self.emit('goto', None, None, end_pos)
        else:
            # 记录结束位置
            end_pos = self.next_quad
            # 回填false分支跳转到结束位置
            self.backpatch(false_list, end_pos)

        # 回填true分支跳转到if体开始位置
        self.backpatch(true_list, true_start)

    def gen_while_statement(self, stmt):
        """生成while语句的代码"""
        # 记录循环开始位置
        begin_pos = self.next_quad

        # 生成条件代码
        true_list, false_list = self.gen_condition(stmt['condition'])

        # 记录循环体开始位置
        body_start = self.next_quad

        # 生成while体的代码
        for s in stmt.get('body', []):
            self.gen_statement(s)

        # 跳回循环开始位置
        self.emit('goto', None, None, begin_pos)

        # 记录结束位置
        end_pos = self.next_quad

        # 回填true分支跳转到循环体开始位置
        self.backpatch(true_list, body_start)
        # 回填false分支跳转到结束位置
        self.backpatch(false_list, end_pos)

    def gen_condition(self, condition):
        """生成条件表达式的代码"""
        if condition['type'] == 'binary_expression':
            return self.gen_binary_condition(condition)
        elif condition['type'] == 'unary_expression':
            return self.gen_unary_condition(condition)
        elif condition['type'] == 'identifier':
            temp = self.new_temp()
            self.emit('=', condition['name'], None, temp)
            true_list = [self.next_quad]
            self.emit('if!=', temp, '0', None)  # 非零为真
            false_list = [self.next_quad]
            self.emit('goto', None, None, None)  # 回填占位符
            return true_list, false_list
        elif condition['type'] == 'number':
            if float(condition['value']) != 0:
                true_list = [self.next_quad]
                self.emit('goto', None, None, None)  # 无条件跳转（真）
                false_list = []
            else:
                true_list = []
                false_list = [self.next_quad]
                self.emit('goto', None, None, None)  # 无条件跳转（假）
            return true_list, false_list
        return [], []

    def gen_binary_condition(self, expr):
        """生成二元条件表达式的代码"""
        op = expr['operator']
        if op in ['&&', '||']:
            left_true, left_false = self.gen_condition(expr['left'])
            if op == '&&':
                # 对于AND，左真链回填到计算右边
                right_label = self.new_label()
                self.backpatch(left_true, right_label)
                self.emit('label', None, None, right_label)
                right_true, right_false = self.gen_condition(expr['right'])
                return right_true, self.merge(left_false, right_false)
            else:
                # 对于OR，左假链回填到计算右边
                right_label = self.new_label()
                self.backpatch(left_false, right_label)
                self.emit('label', None, None, right_label)
                right_true, right_false = self.gen_condition(expr['right'])
                return self.merge(left_true, right_true), right_false
        else:
            # 关系运算符
            left = self.gen_expression(expr['left'])
            right = self.gen_expression(expr['right'])
            true_list = [self.next_quad]
            self.emit(f'if{op}', left, right, None)  # 回填占位符
            false_list = [self.next_quad]
            self.emit('goto', None, None, None)  # 回填占位符
            return true_list, false_list

    def gen_unary_condition(self, expr):
        """生成一元条件表达式的代码"""
        if expr['operator'] == '!':
            true_list, false_list = self.gen_condition(expr['operand'])
            return false_list, true_list  # NOT操作交换真假
        return [], []

    def gen_printf_statement(self, stmt):
        """生成printf语句的代码"""
        for arg in stmt['arguments']:
            result = self.gen_expression(arg)
            self.emit('print', result, None, None)

    def gen_return_statement(self, stmt):
        """生成return语句的代码"""
        if stmt.get('value'):
            result = self.gen_expression(stmt['value'])
            self.emit('return', result, None, None)
        else:
            self.emit('return', None, None, None)

    def gen_expression(self, expr):
        """生成表达式的代码并返回结果变量"""
        if expr['type'] == 'binary_expression':
            left = self.gen_expression(expr['left'])
            right = self.gen_expression(expr['right'])
            result = self.new_temp()
            self.emit(expr['operator'], left, right, result)
            return result
        elif expr['type'] == 'unary_expression':
            operand = self.gen_expression(expr['operand'])
            result = self.new_temp()
            self.emit(expr['operator'], operand, None, result)
            return result
        elif expr['type'] == 'number':
            return str(expr['value'])  # 确保数字以字符串形式返回
        elif expr['type'] == 'identifier':
            return expr['name']
        elif expr['type'] == 'assignment_expression':
            result = self.gen_expression(expr['right'])
            # 处理左值
            if isinstance(expr['left'], dict) and expr['left']['type'] == 'identifier':
                var_name = expr['left']['name']
            else:
                var_name = expr['left']
            self.emit('=', result, None, var_name)
            return var_name
        elif expr['type'] == 'function_call':
            return self.gen_function_call(expr)
        return None

    def gen_function_call(self, expr):
    
        func_name = expr['name']
        args = expr.get('arguments', [])
        
        # 生成参数传递代码
        for arg in args:
            if arg['type'] == 'identifier':
                # 直接使用变量名
                result = arg['name']
            else:
                # 对于表达式，先计算结果
                result = self.gen_expression(arg)
            self.emit('param', result, None, None)
        
        # 调用函数 - 适配Mubiao的格式：('call', 函数名, None, 结果变量)
        result_temp = self.new_temp()
        self.emit('call', func_name, None, result_temp)
        
        return result_temp

    def get_quads(self):
        """返回四元式列表"""
        return self.quads


# 测试代码
if __name__ == '__main__':
    from yufa import Yufa
    from cifa import Cifa
    test_code = """
int main() {
    int a = 1;
    int b = 2;
    int c = 3;
    int d = (a + b) * c;
    printf(d);
}
    """
    cifa = Cifa()
    tokens = cifa.cifafenxi(test_code)
    yufa = Yufa()
    result = yufa.parse(tokens)
    syntax_tree = result

    zhongjian = Zhongjian()
    result = zhongjian.generate(syntax_tree)
    print("生成的四元式:")
    for i, quad in enumerate(result):
        print(f"{i}: {quad}")
    # from Mubiao import Mubiao
    # mubiao = Mubiao(result)
    # asm_code = mubiao.generate()
    # print(asm_code)
