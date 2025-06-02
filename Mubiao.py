class Mubiao:
    def __init__(self, quads):
        self.quads = quads
        self.vars = set()
        self.temp_vars = set()
        self.labels = set()
        self.functions = set()
        self._collect_vars()

    def _collect_vars(self):
        """收集程序中使用的变量、临时变量和标签"""
        for quad in self.quads:
            if len(quad) == 4:
                op, arg1, arg2, result = quad
            else:
                continue
            
            if op == 'label':
                self.labels.add(result)
                continue
            if op in ('goto', 'halt', 'program'):
                continue
                
            for operand in (arg1, arg2, result):
                if isinstance(operand, str) and operand is not None and not self._is_number(operand):
                    if operand.startswith('T'):  # 临时变量
                        self.temp_vars.add(operand)
                    elif operand.startswith('L'):  # 标签
                        self.labels.add(operand)
                    elif operand.startswith('func_'):  # 函数名
                        self.functions.add(operand)
                        self.labels.add(operand)
                    elif operand not in ('start', 'end'):  # 普通变量
                        self.vars.add(operand)

    def _is_number(self, s):
        """判断字符串是否为数字"""
        if s is None:
            return False
        try:
            float(s)
            return True
        except (ValueError, TypeError):
            return False

    def _get_var_name(self, var):
        """处理变量名，避免使用与汇编指令冲突的名称"""
        if var is None:
            return None
        
        # 需要避免的汇编指令和关键字
        reserved_words = {
            'add', 'sub', 'mul', 'div', 'mov', 'jmp', 'je', 'jne', 'jg', 'jl',
            'jge', 'jle', 'push', 'pop', 'call', 'ret', 'int', 'cmp', 'and',
            'or', 'xor', 'not', 'shl', 'shr', 'rol', 'ror', 'inc', 'dec'
        }
        
        # 如果变量名是单个字母，添加var_前缀
        if len(var) == 1 and var.isalpha():
            return f'var_{var}'
        
        # 如果变量名是保留字，添加var_前缀
        if var.lower() in reserved_words:
            return f'var_{var}'
        
        return var

    def generate(self):
        """生成8086汇编代码"""
        lines = []

        # 数据段
        lines.append('DATA SEGMENT')
        # 声明普通变量
        for v in sorted(self.vars):
            lines.append(f'    {self._get_var_name(v)} DW 0')
        # 声明临时变量
        for v in sorted(self.temp_vars):
            lines.append(f'    {v} DW 0')
        # 栈指针（用于模拟函数调用栈）
        lines.append('    STACK_PTR DW 0')
        lines.append('    CALL_STACK DW 100 DUP(0)  ; 函数调用栈')
        lines.append('DATA ENDS')
        lines.append('')
        lines.append('STACK SEGMENT')
        lines.append('    DW 128 DUP(0)')
        lines.append('STACK ENDS')
        lines.append('')
        lines.append('CODE SEGMENT')
        lines.append('    ASSUME CS:CODE, DS:DATA, SS:STACK')
        lines.append('START:')
        lines.append('    MOV AX, DATA')
        lines.append('    MOV DS, AX')
        lines.append('    MOV AX, STACK')
        lines.append('    MOV SS, AX')
        lines.append('    JMP func_main')
        lines.append('')

        # 遍历四元式生成代码
        for quad in self.quads:
            op, arg1, arg2, result = quad

            if op == 'program':
                if result == 'end':
                    # 程序结束标记
                    lines.append('    MOV AH, 4CH')
                    lines.append('    INT 21H')
                continue

            elif op == 'label':
                # 标签定义
                if result.startswith('func_'):
                    # 函数开始，需要保存返回地址
                    lines.append(f'{result}:')
                    lines.append('    PUSH BP')  # 保存BP
                    lines.append('    MOV BP, SP')  # 设置新的BP
                else:
                    lines.append(f'{result}:')
                continue

            elif op == '=':
                # 赋值操作
                if self._is_number(arg1):
                    lines.append(f'    MOV AX, {arg1}')
                else:
                    lines.append(f'    MOV AX, DS:[{self._get_var_name(arg1)}]')
                lines.append(f'    MOV DS:[{self._get_var_name(result)}], AX')

            elif op in ('+', '-', '*', '/'):
                # 算术运算
                if self._is_number(arg1):
                    lines.append(f'    MOV AX, {arg1}')
                else:
                    lines.append(f'    MOV AX, DS:[{self._get_var_name(arg1)}]')

                if op == '+':
                    if self._is_number(arg2):
                        lines.append(f'    ADD AX, {arg2}')
                    else:
                        lines.append(f'    ADD AX, DS:[{self._get_var_name(arg2)}]')
                elif op == '-':
                    if self._is_number(arg2):
                        lines.append(f'    SUB AX, {arg2}')
                    else:
                        lines.append(f'    SUB AX, DS:[{self._get_var_name(arg2)}]')
                elif op == '*':
                    if self._is_number(arg2):
                        lines.append(f'    MOV BX, {arg2}')
                    else:
                        lines.append(f'    MOV BX, DS:[{self._get_var_name(arg2)}]')
                    lines.append('    MUL BX')
                elif op == '/':
                    if self._is_number(arg2):
                        lines.append(f'    MOV BX, {arg2}')
                    else:
                        lines.append(f'    MOV BX, DS:[{self._get_var_name(arg2)}]')
                    lines.append('    XOR DX, DX  ; 清除高位')
                    lines.append('    DIV BX')

                lines.append(f'    MOV DS:[{self._get_var_name(result)}], AX')

            elif op == 'param':
                # 参数压栈
                if self._is_number(arg1):
                    lines.append(f'    MOV AX, {arg1}')
                else:
                    lines.append(f'    MOV AX, DS:[{self._get_var_name(arg1)}]')
                lines.append('    MOV BX, DS:[STACK_PTR]')
                lines.append('    MOV DS:[CALL_STACK + BX], AX')
                lines.append('    ADD DS:[STACK_PTR], 2')

            elif op == 'call':
                # 函数调用
                func_name = f'func_{arg1}'
                lines.append(f'    CALL {func_name}')
                # 获取返回值
                lines.append('    SUB DS:[STACK_PTR], 2')
                lines.append('    MOV BX, DS:[STACK_PTR]')
                lines.append('    MOV AX, DS:[CALL_STACK + BX]')
                if result:
                    lines.append(f'    MOV DS:[{self._get_var_name(result)}], AX')

            elif op == 'return':
                # 函数返回
                if arg1:
                    # 有返回值
                    if self._is_number(arg1):
                        lines.append(f'    MOV AX, {arg1}')
                    else:
                        lines.append(f'    MOV AX, DS:[{self._get_var_name(arg1)}]')
                    # 将返回值压栈
                    lines.append('    MOV BX, DS:[STACK_PTR]')
                    lines.append('    MOV DS:[CALL_STACK + BX], AX')
                    lines.append('    ADD DS:[STACK_PTR], 2')
                
                # 恢复BP并返回
                lines.append('    MOV SP, BP')
                lines.append('    POP BP')
                lines.append('    RET')

            elif op == 'print':
                # 打印操作
                if self._is_number(arg1):
                    lines.append(f'    MOV AX, {arg1}')
                else:
                    lines.append(f'    MOV AX, DS:[{self._get_var_name(arg1)}]')
                
                # 将数字转换为ASCII字符
                lines.append('    ADD AX, 30H')
                
                # 显示字符
                lines.append('    MOV AH, 2')
                lines.append('    MOV DL, AL')
                lines.append('    INT 21H')
                
                # 添加换行
                lines.append('    MOV AH, 2')
                lines.append('    MOV DL, 0DH')
                lines.append('    INT 21H')
                lines.append('    MOV DL, 0AH')
                lines.append('    INT 21H')

            elif op == 'goto':
                # 无条件跳转
                lines.append(f'    JMP {result}')

            elif op.startswith('if'):
                # 条件跳转
                cond = op[2:]  # 提取条件操作符
                if self._is_number(arg1):
                    lines.append(f'    MOV AX, {arg1}')
                else:
                    lines.append(f'    MOV AX, DS:[{self._get_var_name(arg1)}]')

                if self._is_number(arg2):
                    lines.append(f'    MOV BX, {arg2}')
                else:
                    lines.append(f'    MOV BX, DS:[{self._get_var_name(arg2)}]')

                lines.append('    CMP AX, BX')
                
                if cond == '>':
                    lines.append(f'    JG {result}')
                elif cond == '<':
                    lines.append(f'    JL {result}')
                elif cond == '>=':
                    lines.append(f'    JGE {result}')
                elif cond == '<=':
                    lines.append(f'    JLE {result}')
                elif cond == '==':
                    lines.append(f'    JE {result}')
                elif cond == '!=':
                    lines.append(f'    JNE {result}')

            elif op == 'halt':
                # 程序终止
                lines.append('    MOV AH, 4CH')
                lines.append('    INT 21H')

        lines.append('')
        lines.append('CODE ENDS')
        lines.append('END START')

        return '\n'.join(lines)


# 测试代码
if __name__ == '__main__':
    # 修正后的四元式
    test_quads = [
        ('program', None, None, 'start'),
        ('label', None, None, 'func_add'),
        ('+', 'a', 'b', 'T0'),
        ('return', 'T0', None, None),
        ('label', None, None, 'func_main'),
        ('=', '1', None, 'a'),
        ('=', '2', None, 'b'),
        ('param', 'a', None, None),
        ('param', 'b', None, None),
        ('call', 'add', None, 'T1'),
        ('=', 'T1', None, 'z'),
        ('print', 'z', None, None),
        ('program', None, None, 'end')
    ]

    mubiao = Mubiao(test_quads)
    asm_code = mubiao.generate()
    print("修复后的8086汇编代码：")
    print(asm_code)
