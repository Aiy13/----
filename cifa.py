class Cifa:
    def __init__(self):
        self.token_types = {
            'KEYWORD': 1,    # 关键字
            'IDENTIFIER': 700, # 标识符
            'NUMBER': 400,     # 数字
            'OPERATOR': 4,   # 运算符
            'SEPARATOR': 5,  # 分隔符
            'COMMENT': 600,    # 注释
            'UNKNOWN': 0     # 未识别
        }
        self.keywords = {'if':101, 'else':102, 'while':103, 'for':104, 'return':105, 'int':106, 'float':107, 'printf':108, 'double':109, 'void':110, 'char':111}
        self.operators = {'+':201, '-':202, '*':203, '/':204, '=':205, '==':206, '!=':207, '<':208, '>':209, '<=':210, '>=':211, '!':212, '%':213, '|':214, '&':215, '&&':216}
        self.separators = {'(':301, ')':302, '{':303, '}':304, '[':305, ']':306, ';':307, ',':308, '\'':309, '\"':310, '\\':311}
        
    def cifafenxi(self, data):
        tokens = []
        i = 0
        data = data.strip()
        line_num = 1

        while i < len(data):
            char = data[i]
            
            # 处理换行符和空白字符
            if char == '\n':
                line_num += 1
                i += 1
                continue
            if char.isspace():
                i += 1
                continue

            # 处理注释
            if char == '/' and i + 1 < len(data):
                if data[i+1] == '/':  # 单行注释
                    comment = '//'
                    i += 2
                    while i < len(data) and data[i] != '\n':
                        comment += data[i]
                        i += 1
                    tokens.append((self.token_types['COMMENT'], '注释', comment, line_num))
                    continue
                elif data[i+1] == '*':  # 多行注释
                    comment = '/*'
                    i += 2
                    while i < len(data) - 1:
                        if data[i] == '\n':
                            line_num += 1
                        if data[i] == '*' and data[i+1] == '/':
                            comment += '*/'
                            i += 2
                            break
                        comment += data[i]
                        i += 1
                    tokens.append((self.token_types['COMMENT'], '注释', comment, line_num))
                    continue

            # 处理标识符和关键字
            if char.isalpha() or char == '_':
                identifier = ''
                while i < len(data) and (data[i].isalnum() or data[i] == '_'):
                    identifier += data[i]
                    i += 1
                if identifier in self.keywords:
                    tokens.append((self.keywords[identifier], '关键字', identifier, line_num))
                else:
                    tokens.append((self.token_types['IDENTIFIER'], '标识符', identifier, line_num))
                continue

            # 处理数字（包括整数、浮点数、十六进制、八进制）
            if char.isdigit() or (char == '.' and i + 1 < len(data) and data[i+1].isdigit()):
                number = ''
                is_valid = True
                has_dot = False
                has_e = False
                
                # 处理十六进制
                if char == '0' and i + 1 < len(data) and (data[i+1] == 'x' or data[i+1] == 'X'):
                    number = '0'
                    i += 1
                    number += data[i]
                    i += 1
                    has_hex = False
                    while i < len(data) and (data[i].isdigit() or data[i].lower() in 'abcdef'):
                        has_hex = True
                        number += data[i]
                        i += 1
                    if has_hex and all(c.lower() in '0123456789abcdef' for c in number[2:]):
                        tokens.append((self.token_types['NUMBER'], '十六进制数', number, line_num))
                    else:
                        tokens.append((0, '非法十六进制数', number, line_num))
                    continue

                # 处理八进制
                if char == '0' and i + 1 < len(data) and data[i+1].isdigit():
                    number = '0'
                    i += 1
                    is_valid_octal = True
                    while i < len(data) and data[i].isdigit():
                        if data[i] in '89':
                            is_valid_octal = False
                        number += data[i]
                        i += 1
                    if is_valid_octal and len(number) > 1:
                        tokens.append((self.token_types['NUMBER'], '八进制数', number, line_num))
                    else:
                        tokens.append((0, '非法八进制数', number, line_num))
                    continue

                # 处理浮点数和整数
                while i < len(data):
                    if data[i].isdigit():
                        number += data[i]
                    elif data[i] == '.' and not has_dot and not has_e:
                        if not number and (i + 1 >= len(data) or not data[i+1].isdigit()):
                            tokens.append((0, '非法浮点数', '.', line_num))
                            i += 1
                            break
                        number += data[i]
                        has_dot = True
                    elif (data[i] == 'e' or data[i] == 'E') and not has_e:
                        if i + 1 >= len(data):
                            is_valid = False
                            break
                        number += data[i]
                        has_e = True
                        if i + 1 < len(data) and (data[i+1] == '+' or data[i+1] == '-'):
                            i += 1
                            number += data[i]
                    elif data[i].isalpha() or data[i] == '_':
                        number += data[i]
                        is_valid = False
                    else:
                        break
                    i += 1

                if number.endswith('.'):
                    tokens.append((0, '非法浮点数', number, line_num))
                elif is_valid:
                    try:
                        if 'e' in number.lower() or '.' in number:
                            float(number)
                            tokens.append((self.token_types['NUMBER'], '浮点数', number, line_num))
                        else:
                            tokens.append((self.token_types['NUMBER'], '整数', number, line_num))
                    except ValueError:
                        tokens.append((0, '非法数字', number, line_num))
                else:
                    tokens.append((0, '非法数字', number, line_num))
                continue

            # 处理字符串和字符常量
            if char in ['"', "'"]:
                quote_char = char
                string_content = quote_char
                i += 1
                is_closed = False
                
                while i < len(data):
                    if data[i] == quote_char:
                        string_content += data[i]
                        is_closed = True
                        i += 1
                        break
                    elif data[i] == '\n':
                        break
                    else:
                        string_content += data[i]
                        i += 1

                if is_closed:
                    if quote_char == '"':
                        tokens.append((self.separators[quote_char], '字符串常量', string_content, line_num))
                    else:
                        if len(string_content) == 3:  # 'x'
                            tokens.append((self.separators[quote_char], '字符常量', string_content, line_num))
                        else:
                            tokens.append((0, '非法字符常量', string_content, line_num))
                else:
                    tokens.append((0, '未闭合的引号', string_content, line_num))
                continue

            # 处理运算符
            if char in self.operators:
                op = char
                if i + 1 < len(data) and (char + data[i + 1]) in self.operators:
                    op = char + data[i + 1]
                    i += 2
                else:
                    i += 1
                tokens.append((self.operators[op], '运算符', op, line_num))
                continue

            # 处理分隔符
            if char in self.separators:
                tokens.append((self.separators[char], '分隔符', char, line_num))
                i += 1
                continue

            # 未识别字符
            tokens.append((0, '非法字符', char, line_num))
            i += 1

        return tokens

# 测试代码
if __name__ == "__main__":
    cifa = Cifa()
    test_code = """
    main(){
        if(x = 0){
        a = a + 1;
        }
        }

"""
    tokens = cifa.cifafenxi(test_code)
    print("非法字符列表：")
    print(tokens)