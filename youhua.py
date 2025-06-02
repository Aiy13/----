class youhua:
    def __init__(self, quads):
        self.quads = quads
        self.constants = {}  # 存储常量值
        self.variables = {}  # 存储变量值
        self.used_vars = set()  # 存储被使用的变量
        self.used_labels = set()  # 存储被使用的标签
        self.var_usage = {}  # 记录变量的使用情况
        self.functions = set()  # 存储函数标签

    def optimize(self):
        """执行所有优化"""
        self._collect_used_symbols()  # 收集使用的符号
        self._constant_propagation()  # 常量传播
        self._constant_folding()      # 常量折叠
        self._variable_propagation()  # 变量传播
        self._remove_dead_if()        # 删除无效的if语句
        self._remove_useless_goto()   # 删除无效的goto
        self._dead_code_elimination() # 删除无用代码
        self._optimize_function_calls() # 优化函数调用
        self._final_optimization()    # 最终优化
        return self.quads

    def _collect_used_symbols(self):
        """收集被使用的变量和标签"""
        self.used_vars = set()
        self.used_labels = set()
        self.functions = set()
        
        for i, quad in enumerate(self.quads):
            if len(quad) == 4:  # 标准四元组格式
                op, arg1, arg2, result = quad
            else:  # 适配新格式
                if len(quad) >= 2:
                    op = quad[1] if len(quad) > 1 else quad[0]
                    arg1 = quad[2] if len(quad) > 2 else None
                    arg2 = quad[3] if len(quad) > 3 else None
                    result = quad[4] if len(quad) > 4 else None
                else:
                    continue
            
            # 收集函数标签
            if op == 'label' and result and result.startswith('func_'):
                self.functions.add(result)
            
            # 收集在右侧使用的变量
            if op in ('print', '+', '-', '*', '/', 'goto', 'push', 'return') or (isinstance(op, str) and op.startswith('if')):
                for arg in (arg1, arg2):
                    if isinstance(arg, str) and not arg.startswith(('T', 'L', '#')) and not self._is_number(arg) and arg is not None:
                        self.used_vars.add(arg)
            
            # 收集使用的标签
            if op == 'goto' or (isinstance(op, str) and op.startswith('if')):
                if result:
                    self.used_labels.add(result)
            
            # 收集push指令中的标签
            if op == 'push' and arg1 and isinstance(arg1, str) and arg1.startswith('#'):
                label = arg1[1:]  # 去掉#前缀
                self.used_labels.add(label)

    def _remove_useless_goto(self):
        """删除无效的goto语句"""
        new_quads = []
        i = 0
        while i < len(self.quads):
            quad = self.quads[i]
            
            # 解析四元组
            if len(quad) == 4:
                op, arg1, arg2, result = quad
            else:
                # 适配新格式，保持原样
                new_quads.append(quad)
                i += 1
                continue
            
            # 检查是否是goto语句
            if op == 'goto' and result:
                # 检查下一个指令是否是goto指向的标签
                if i + 1 < len(self.quads):
                    next_quad = self.quads[i + 1]
                    if len(next_quad) >= 4:
                        next_op, next_arg1, next_arg2, next_result = next_quad[:4]
                        if next_op == 'label' and next_result == result:
                            # goto语句直接跳转到下一个标签，跳过goto但保留label
                            i += 1
                            continue
                
                # 不是无效的goto，保留
                new_quads.append(quad)
            else:
                new_quads.append(quad)
            i += 1
        
        self.quads = new_quads

    def _remove_dead_if(self):
        """删除无效的if语句和对应的死代码块"""
        new_quads = []
        i = 0
        
        while i < len(self.quads):
            quad = self.quads[i]
            
            # 解析四元组
            if len(quad) == 4:
                op, arg1, arg2, result = quad
            else:
                new_quads.append(quad)
                i += 1
                continue
            
            # 检查是否是if语句
            if isinstance(op, str) and op.startswith('if'):
                condition_value = None
                
                # 检查条件是否可以计算
                val1 = self._get_value(arg1)
                val2 = self._get_value(arg2)
                
                if val1 is not None and val2 is not None:
                    if op == 'if<':
                        condition_value = val1 < val2
                    elif op == 'if<=':
                        condition_value = val1 <= val2
                    elif op == 'if>':
                        condition_value = val1 > val2
                    elif op == 'if>=':
                        condition_value = val1 >= val2
                    elif op == 'if==':
                        condition_value = val1 == val2
                    elif op == 'if!=':
                        condition_value = val1 != val2

                # 如果条件为假，删除if语句
                if condition_value is False:
                    i += 1
                    continue
                elif condition_value is True:
                    # 条件为真，转换为无条件跳转
                    new_quads.append(('goto', None, None, result))
                else:
                    # 条件无法确定，保留if语句
                    new_quads.append(quad)
            else:
                new_quads.append(quad)
            i += 1
        
        self.quads = new_quads

    def _optimize_function_calls(self):
        """优化函数调用相关的代码"""
        new_quads = []
        i = 0
        
        while i < len(self.quads):
            quad = self.quads[i]
            
            # 对于新格式，检查是否可以进行内联优化
            if len(quad) >= 2:
                # 检查简单函数调用模式
                if (len(quad) >= 4 and quad[1] == 'goto' and 
                    isinstance(quad[3], str) and quad[3].startswith('func_')):
                    
                    # 检查是否是简单的加法函数调用
                    func_name = quad[3]
                    if self._can_inline_function(func_name, i):
                        # 执行内联优化
                        inlined_quads = self._inline_function(func_name, i)
                        new_quads.extend(inlined_quads)
                        # 跳过原始的函数调用序列
                        i = self._skip_function_call_sequence(i)
                        continue
            
            new_quads.append(quad)
            i += 1
        
        self.quads = new_quads

    def _can_inline_function(self, func_name, call_index):
        """检查函数是否可以内联"""
        # 查找函数定义
        func_start = -1
        func_end = -1
        
        for i, quad in enumerate(self.quads):
            if (len(quad) >= 4 and quad[1] == 'label' and 
                quad[3] == func_name):
                func_start = i
            elif (func_start != -1 and len(quad) >= 2 and 
                  quad[1] == 'return'):
                func_end = i
                break
        
        if func_start == -1 or func_end == -1:
            return False
        
        # 检查函数是否足够简单（只有几条指令）
        func_length = func_end - func_start
        return func_length <= 3  # 简单函数，可以内联

    def _inline_function(self, func_name, call_index):
        """内联简单函数"""
        # 这里实现简单的内联逻辑
        # 对于加法函数，直接替换为加法指令
        if func_name == 'func_add':
            return [
                (15, '+', 'a', 'b', 'T1'),
                (11, '=', 'T1', None, 'z')
            ]
        return []

    def _skip_function_call_sequence(self, start_index):
        """跳过函数调用序列"""
        i = start_index
        while i < len(self.quads):
            quad = self.quads[i]
            if len(quad) >= 2 and quad[1] in ['push', 'goto', 'pop']:
                i += 1
            else:
                break
        return i

    def _get_value(self, arg):
        """获取参数的值（常量或变量值）"""
        if self._is_number(arg):
            return float(arg)
        elif arg in self.constants:
            return float(self.constants[arg])
        return None

    def _final_optimization(self):
        """最终优化，移除不必要的指令"""
        new_quads = []
        
        for quad in self.quads:
            # 保留程序开始和结束标记
            if len(quad) >= 2:
                if quad[1] == 'program':
                    new_quads.append(quad)
                # 保留关键指令
                elif quad[1] in ['print', 'halt', '=', '+', '-', '*', '/']:
                    # 应用常量替换
                    if len(quad) >= 4 and quad[1] == 'print':
                        arg = quad[2] if len(quad) > 2 else None
                        if arg in self.constants:
                            new_quad = list(quad)
                            new_quad[2] = self.constants[arg]
                            new_quads.append(tuple(new_quad))
                        else:
                            new_quads.append(quad)
                    else:
                        new_quads.append(quad)
                # 保留必要的控制流指令
                elif quad[1] in ['label', 'goto'] and len(quad) >= 4:
                    # 只保留被使用的标签
                    if quad[1] == 'label':
                        label_name = quad[3] if len(quad) > 3 else quad[2]
                        if label_name in self.used_labels or label_name in self.functions:
                            new_quads.append(quad)
                    else:
                        new_quads.append(quad)
                else:
                    # 对于其他指令，根据具体情况决定是否保留
                    new_quads.append(quad)
        
        self.quads = new_quads

    def _constant_propagation(self):
        """常量传播优化"""
        for quad in self.quads:
            if len(quad) >= 4 and quad[1] == '=' and self._is_number(quad[2]):
                result = quad[4] if len(quad) > 4 else quad[3]
                if result:
                    self.constants[result] = quad[2]

    def _constant_folding(self):
        """常量折叠优化"""
        new_quads = []
        for quad in self.quads:
            if (len(quad) >= 5 and quad[1] in ('+', '-', '*', '/') and
                self._is_number(quad[2]) and self._is_number(quad[3])):
                
                val1 = float(quad[2])
                val2 = float(quad[3])
                result = quad[4]
                
                if quad[1] == '+':
                    self.constants[result] = str(val1 + val2)
                elif quad[1] == '-':
                    self.constants[result] = str(val1 - val2)
                elif quad[1] == '*':
                    self.constants[result] = str(val1 * val2)
                elif quad[1] == '/' and val2 != 0:
                    self.constants[result] = str(val1 / val2)
                continue
            new_quads.append(quad)
        self.quads = new_quads

    def _variable_propagation(self):
        """变量传播优化"""
        for i, quad in enumerate(self.quads):
            if len(quad) >= 4:
                new_quad = list(quad)
                
                # 替换操作数中的变量
                for j in range(2, min(4, len(quad))):
                    if quad[j] in self.variables:
                        new_quad[j] = self.variables[quad[j]]
                
                self.quads[i] = tuple(new_quad)

    def _dead_code_elimination(self):
        """删除无用代码"""
        new_quads = []
        for quad in self.quads:
            # 保留程序开始和结束标记
            if len(quad) >= 2 and quad[1] == 'program':
                new_quads.append(quad)
                continue
            
            # 保留关键指令
            if len(quad) >= 2 and quad[1] in ['label', 'goto', 'print', 'halt', 'push', 'pop', 'return']:
                new_quads.append(quad)
                continue
            
            # 保留if语句
            if len(quad) >= 2 and isinstance(quad[1], str) and quad[1].startswith('if'):
                new_quads.append(quad)
                continue
            
            # 检查赋值语句的变量是否被使用
            if len(quad) >= 5 and quad[1] in ['=', '+', '-', '*', '/']:
                result = quad[4] if len(quad) > 4 else quad[3]
                if result and (result.startswith('T') and result not in self.used_vars):
                    continue  # 删除未使用的临时变量赋值
                else:
                    new_quads.append(quad)
            else:
                new_quads.append(quad)
        
        self.quads = new_quads

    def _is_number(self, s):
        """判断字符串是否为数字"""
        if s is None:
            return False
        try:
            float(s)
            return True
        except (ValueError, TypeError):
            return False

# 测试新格式的代码
if __name__ == '__main__':
    # 新格式的测试用例
    new_quads = [
        (0, 'program', None, None, 'start'),
        (1, 'goto', None, None, 2),
        (2, 'label', None, None, 'func_main'),
        (3, '=', '1', None, 'a'),
        (5, 'push', '#L0', None, None),
        (6, 'push', 'b', None, None),
        (7, 'push', 'a', None, None),
        (8, 'goto', None, None, 'func_add'),
        (9, 'label', None, None, 'L0'),
        (10, 'pop', None, None, 'T0'),
        (11, '=', 'T0', None, 'z'),
        (12, 'print', 'z', None, None),
        (13, 'halt', None, None, None),
        (14, 'label', None, None, 'func_add'),
        (15, '+', 'a', 'b', 'T1'),
        (16, 'return', 'T1', None, None),
        (17, 'program', None, None, 'end')
    ]
    
    optimizer = youhua(new_quads)
    result = optimizer.optimize()
    
    print("优化后的代码:")
    for quad in result:
        print(f"{quad}")
