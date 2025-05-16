class Zhongjian:
    def __init__(self):
        self.quads = []  # Store quadruples
        self.temp_count = 0  # Counter for temporary variables
        self.label_count = 0  # Counter for labels
        self.next_quad = 0  # Next quadruple index

    def new_temp(self):
        """Generate a new temporary variable name."""
        temp = f"T{self.temp_count}"
        self.temp_count += 1
        return temp

    def new_label(self):
        """Generate a new label name."""
        label = f"L{self.label_count}"
        self.label_count += 1
        return label

    def emit(self, op, arg1, arg2, result):
        """Generate a quadruple and add it to the list."""
        self.quads.append((op, arg1, arg2, result))
        self.next_quad += 1

    def merge(self, list1, list2):
        """Merge two lists of quad indices (true/false chains)."""
        return list1 + list2

    def backpatch(self, quad_indices, label):
        """Backpatch quadruples with the given label."""
        for idx in quad_indices:
            op, arg1, arg2, _ = self.quads[idx]
            self.quads[idx] = (op, arg1, arg2, label)

    def generate(self, syntax_tree):
        """Generate intermediate code from the syntax tree."""
        if syntax_tree['type'] == 'program':
            self.gen_program(syntax_tree)
        return self.quads

    def gen_program(self, program):
        """Process the program node."""
        self.emit('program', None, None, 'start')
        for stmt in program.get('body', []):
            self.gen_statement(stmt)
        self.emit('program', None, None, 'end')

    def gen_statement(self, stmt):
        """Process a statement node."""
        if stmt['type'] == 'if_statement':
            self.gen_if_statement(stmt)
        elif stmt['type'] == 'while_statement':
            self.gen_while_statement(stmt)
        elif stmt['type'] == 'variable_declaration':
            self.gen_variable_declaration(stmt)
        elif stmt['type'] == 'assignment_expression':
            self.gen_assignment_expression(stmt)
        elif stmt['type'] == 'empty_statement':
            pass  # No code for empty statements

    def gen_variable_declaration(self, decl):
        """Generate code for variable declaration."""
        if decl.get('initializer'):
            result = self.gen_expression(decl['initializer'])
            self.emit('=', result, None, decl['name'])

    def gen_assignment_expression(self, expr):
        """Generate code for assignment expression."""
        result = self.gen_expression(expr['right'])
        self.emit('=', result, None, expr['left']['name'])

    def gen_if_statement(self, stmt):
        """Generate code for if statement."""
        # Generate condition code
        true_list, false_list = self.gen_condition(stmt['condition'])

        # Create labels
        true_label = self.new_label()
        false_label = self.new_label() if stmt.get('else') else None
        end_label = self.new_label()

        # Backpatch true list
        self.backpatch(true_list, true_label)
        self.emit('label', None, None, true_label)

        # Generate code for if body
        for s in stmt.get('body', []):
            self.gen_statement(s)

        if stmt.get('else'):
            # Jump to end after true branch
            self.emit('goto', None, None, end_label)
            # Backpatch false list
            self.backpatch(false_list, false_label)
            self.emit('label', None, None, false_label)
            # Generate code for else body
            for s in stmt.get('else', []):
                self.gen_statement(s)
        else:
            # Backpatch false list to end
            self.backpatch(false_list, end_label)

        # Emit end label
        self.emit('label', None, None, end_label)

    def gen_while_statement(self, stmt):
        """Generate code for while statement."""
        # Create labels
        begin_label = self.new_label()
        true_label = self.new_label()
        end_label = self.new_label()

        # Emit begin label
        self.emit('label', None, None, begin_label)

        # Generate condition code
        true_list, false_list = self.gen_condition(stmt['condition'])

        # Backpatch true list
        self.backpatch(true_list, true_label)
        self.emit('label', None, None, true_label)

        # Generate code for while body
        for s in stmt.get('body', []):
            self.gen_statement(s)

        # Jump back to condition
        self.emit('goto', None, None, begin_label)

        # Backpatch false list to end
        self.backpatch(false_list, end_label)
        self.emit('label', None, None, end_label)

    def gen_condition(self, condition):
        """Generate code for condition expressions."""
        if condition['type'] == 'binary_expression':
            return self.gen_binary_condition(condition)
        elif condition['type'] == 'unary_expression':
            return self.gen_unary_condition(condition)
        elif condition['type'] == 'identifier':
            temp = self.new_temp()
            self.emit('=', condition['name'], None, temp)
            true_list = [self.next_quad]
            self.emit('if', temp, None, None)  # Placeholder for backpatching
            false_list = [self.next_quad]
            self.emit('goto', None, None, None)  # Placeholder for backpatching
            return true_list, false_list
        elif condition['type'] == 'number':
            true_list = [self.next_quad] if float(condition['value']) != 0 else []
            false_list = [self.next_quad] if float(condition['value']) == 0 else []
            self.emit('if', condition['value'], None, None)  # Placeholder
            self.emit('goto', None, None, None)  # Placeholder
            return true_list, false_list
        return [], []

    def gen_binary_condition(self, expr):
        """Generate code for binary condition expressions."""
        op = expr['operator']
        if op in ['&&', '||']:
            left_true, left_false = self.gen_condition(expr['left'])
            if op == '&&':
                # For AND, backpatch left true to evaluate right
                right_label = self.new_label()
                self.backpatch(left_true, right_label)
                self.emit('label', None, None, right_label)
                right_true, right_false = self.gen_condition(expr['right'])
                return right_true, self.merge(left_false, right_false)
            else:
                # For OR, backpatch left false to evaluate right
                right_label = self.new_label()
                self.backpatch(left_false, right_label)
                self.emit('label', None, None, right_label)
                right_true, right_false = self.gen_condition(expr['right'])
                return self.merge(left_true, right_true), right_false
        else:
            # Relational operators
            left = self.gen_expression(expr['left'])
            right = self.gen_expression(expr['right'])
            true_list = [self.next_quad]
            self.emit(f'if{op}', left, right, None)  # Placeholder for backpatching
            false_list = [self.next_quad]
            self.emit('goto', None, None, None)  # Placeholder for backpatching
            return true_list, false_list

    def gen_unary_condition(self, expr):
        """Generate code for unary condition expressions."""
        if expr['operator'] == '!':
            true_list, false_list = self.gen_condition(expr['operand'])
            return false_list, true_list  # Swap true and false for NOT
        return [], []

    def gen_expression(self, expr):
        """Generate code for expressions and return the result variable."""
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
            return expr['value']
        elif expr['type'] == 'identifier':
            return expr['name']
        elif expr['type'] == 'assignment_expression':
            result = self.gen_expression(expr['right'])
            self.emit('=', result, None, expr['left']['name'])
            return expr['left']['name']
        return None

    def get_quads(self):
        """Return the list of quadruples."""
        return self.quads


if __name__ == '__main__':
    from cifa import Cifa

    cifa = Cifa()
    test_code = """
        main()
        {
            int a = 5;
            if (a > 0) {
                a = a + 1;
            } else {
                a = a - 1;
            }
            while (a < 10) {
                a = a + 1;
            }
        }
    """
    tokens = cifa.cifafenxi(test_code)
    from yufa import Yufa

    yufa = Yufa()
    syntax_tree = yufa.parse(tokens)

    if syntax_tree['type'] == 'error':
        print("语法错误：")
        for error in syntax_tree['errors']:
            print(error)
    else:
        zhongjian = Zhongjian()
        quads = zhongjian.generate(syntax_tree)
        print("中间代码（四元式）：")
        for i, quad in enumerate(quads):
            print(f"{i}: {quad}")