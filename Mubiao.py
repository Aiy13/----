class Mubiao:
    def __init__(self, quads):
        self.quads = quads
        self.vars = set()
        self._collect_vars()

    def _collect_vars(self):
        for op, arg1, arg2, result in self.quads:
            if op in ('label', 'goto'):
                continue
            for operand in (arg1, arg2, result):
                if isinstance(operand, str) and operand is not None and not self._is_number(operand):
                    # 修复逻辑：排除标签(L开头)和临时变量(T开头)
                    if not (operand.startswith('L') or operand.startswith('T')):
                        self.vars.add(operand)

    def _is_number(self, s):
        if s is None:
            return False
        try:
            float(s)
            return True
        except (ValueError, TypeError):
            return False

    def _gen_cond(self, cond, a, b, label):
        lines = []
        # 加载第一个操作数
        if self._is_number(a):
            lines.append(f'    li $t0, {a}')
        else:
            lines.append(f'    lw $t0, {a}')

        # 加载第二个操作数
        if self._is_number(b):
            lines.append(f'    li $t1, {b}')
        else:
            lines.append(f'    lw $t1, {b}')

        # 使用基本的比较和跳转指令组合
        if cond == '>':
            lines.append(f'    slt $t2, $t1, $t0')  # t2 = (b < a)
            lines.append(f'    bne $t2, $zero, {label}')
        elif cond == '<':
            lines.append(f'    slt $t2, $t0, $t1')  # t2 = (a < b)
            lines.append(f'    bne $t2, $zero, {label}')
        elif cond == '>=':
            lines.append(f'    slt $t2, $t0, $t1')  # t2 = (a < b)
            lines.append(f'    beq $t2, $zero, {label}')  # 如果不小于则跳转
        elif cond == '<=':
            lines.append(f'    slt $t2, $t1, $t0')  # t2 = (b < a)
            lines.append(f'    beq $t2, $zero, {label}')  # 如果不大于则跳转
        elif cond == '==':
            lines.append(f'    beq $t0, $t1, {label}')
        elif cond == '!=':
            lines.append(f'    bne $t0, $t1, {label}')
        else:
            # 默认情况，使用相等比较
            lines.append(f'    beq $t0, $t1, {label}')

        return lines

    def generate(self):
        """Generate the full assembly code as a string."""
        lines = []

        # 数据段
        lines.append('.data')
        for v in sorted(self.vars):
            lines.append(f'{v}: .word 0')
        lines.append('')

        # 代码段
        lines.append('.text')
        lines.append('.globl main')
        lines.append('main:')

        for op, arg1, arg2, result in self.quads:
            if op == '=':
                # 赋值操作
                if self._is_number(arg1):
                    lines.append(f'    li $t0, {arg1}')
                else:
                    lines.append(f'    lw $t0, {arg1}')
                lines.append(f'    sw $t0, {result}')

            elif op in ('+', '-', '*', '/'):
                # 算术运算
                if self._is_number(arg1):
                    lines.append(f'    li $t0, {arg1}')
                else:
                    lines.append(f'    lw $t0, {arg1}')

                if self._is_number(arg2):
                    lines.append(f'    li $t1, {arg2}')
                else:
                    lines.append(f'    lw $t1, {arg2}')

                if op == '+':
                    lines.append('    add $t2, $t0, $t1')
                elif op == '-':
                    lines.append('    sub $t2, $t0, $t1')
                elif op == '*':
                    lines.append('    mult $t0, $t1')
                    lines.append('    mflo $t2')
                elif op == '/':
                    lines.append('    div $t0, $t1')
                    lines.append('    mflo $t2')

                lines.append(f'    sw $t2, {result}')

            elif op == 'label':
                # 标签定义
                lines.append(f'{result}:')

            elif op == 'goto':
                # 无条件跳转
                lines.append(f'    j {result}')

            elif op.startswith('if'):
                # 条件跳转
                cond = op[2:]  # 提取条件操作符
                lines.extend(self._gen_cond(cond, arg1, arg2, result))

            elif op == 'program':
                if result == 'start':
                    # 程序开始标记
                    pass
                elif result == 'end':
                    # 程序结束
                    lines.append('    li $v0, 10')  # 系统调用：退出程序
                    lines.append('    syscall')

        return '\n'.join(lines)


# 测试代码
if __name__ == '__main__':
    # 模拟中间代码四元组
    test_quads = [
        ('program', None, None, 'start'),
        ('=', '5', None, 'a'),
        ('>', 'a', '0', 'L1'),
        ('goto', None, None, 'L2'),
        ('label', None, None, 'L1'),
        ('+', 'a', '1', 'T1'),
        ('=', 'T1', None, 'a'),
        ('goto', None, None, 'L3'),
        ('label', None, None, 'L2'),
        ('-', 'a', '1', 'T2'),
        ('=', 'T2', None, 'a'),
        ('label', None, None, 'L3'),
        ('program', None, None, 'end')
    ]

    mubiao = Mubiao(test_quads)
    asm_code = mubiao.generate()
    print("生成的MIPS汇编代码：")
    print(asm_code)
