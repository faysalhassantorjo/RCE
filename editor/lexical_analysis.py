import re

class Token:
    def __init__(self, type, value, line, column):
        self.type = type
        self.value = value
        self.line = line
        self.column = column
    
    def __str__(self):
        return f"Token(type='{self.type}', value='{self.value}', line={self.line}, column={self.column})"
    
    def __repr__(self):
        return self.__str__()

class CLexer:
    def __init__(self, code):
        self.code = code
        self.pos = 0
        self.line = 1
        self.column = 1
        self.current_char = self.code[self.pos] if len(self.code) > 0 else None
        
        self.token_specification = [
            ('LINE_COMMENT', r'//.*'),
            ('BLOCK_COMMENT', r'/\*.*?\*/', re.DOTALL),
            
            ('WHITESPACE', r'\s+'),
            
            ('PREPROCESSOR', r'#\s*(include|define|ifdef|ifndef|endif|elif|else|pragma)\b'),
            
            ('TYPE', r'\b(int|float|double|char|short|long|void|signed|unsigned|struct|union|enum|typedef)\b'),
            
            ('STORAGE_CLASS', r'\b(auto|register|static|extern)\b'),
            
            ('CONTROL', r'\b(if|else|switch|case|default|while|do|for|break|continue|return|goto)\b'),
            
            ('PLUSPLUS', r'\+\+'),
            ('MINUSMINUS', r'--'),
            ('ARROW', r'->'),
            ('DOT', r'\.'),
            ('PLUS', r'\+'),
            ('MINUS', r'-'),
            ('MULTIPLY', r'\*'),
            ('DIVIDE', r'/'),
            ('MODULO', r'%'),
            ('ASSIGN', r'='),
            ('PLUS_ASSIGN', r'\+='),
            ('MINUS_ASSIGN', r'-='),
            ('MULTIPLY_ASSIGN', r'\*='),
            ('DIVIDE_ASSIGN', r'/='),
            ('MODULO_ASSIGN', r'%='),
            ('EQ', r'=='),
            ('NEQ', r'!='),
            ('LT', r'<'),
            ('GT', r'>'),
            ('LTE', r'<='),
            ('GTE', r'>='),
            ('AND', r'&&'),
            ('OR', r'\|\|'),
            ('NOT', r'!'),
            ('BITAND', r'&'),
            ('BITOR', r'\|'),
            ('BITXOR', r'\^'),
            ('BITNOT', r'~'),
            ('LSHIFT', r'<<'),
            ('RSHIFT', r'>>'),
            
            ('LPAREN', r'\('),
            ('RPAREN', r'\)'),
            ('LBRACE', r'\{'),
            ('RBRACE', r'\}'),
            ('LBRACKET', r'\['),
            ('RBRACKET', r'\]'),
            ('COMMA', r','),
            ('SEMICOLON', r';'),
            ('COLON', r':'),
            ('QUESTION', r'\?'),
            
            ('INTEGER', r'\b(0[xX][0-9a-fA-F]+|0[0-7]*|\d+)\b'),
            ('FLOAT', r'\b\d+\.\d*([eE][+-]?\d+)?\b'),
            ('CHAR', r"'([^'\\]|\\.)'"),
            ('STRING', r'"([^"\\]|\\.)*"'),
            
            ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),
            
            ('MISMATCH', r'.')
        ]
        
        self.token_regex = '|'.join('(?P<%s>%s)' % (pair[0], pair[1]) for pair in self.token_specification)
        self.compiled_re = re.compile(self.token_regex)
    
    def error(self, message):
        raise Exception(f"Lexer error at line {self.line}, column {self.column}: {message}")
    
    def get_tokens(self):
        tokens = []
        for mo in self.compiled_re.finditer(self.code):
            kind = mo.lastgroup
            value = mo.group()
            column = mo.start() - self.code.rfind('\n', 0, mo.start()) - 1
            line = self.code.count('\n', 0, mo.start()) + 1
            
            if kind == 'WHITESPACE':
                continue
            elif kind in ('LINE_COMMENT', 'BLOCK_COMMENT'):
                continue
            elif kind == 'MISMATCH':
                self.line = line
                self.column = column
                self.error(f"Unexpected character: '{value}'")
            else:
                if kind == 'INTEGER':
                    if value.startswith('0x') or value.startswith('0X'):
                        value = int(value[2:], 16)
                    elif value.startswith('0'):
                        value = int(value, 8)
                    else:
                        value = int(value)
                elif kind == 'FLOAT':
                    value = float(value)
                elif kind == 'CHAR':
                    value = value[1:-1]
                    if len(value) == 1:
                        value = ord(value)
                    else: 
                        escape_seq = {
                            '\\n': '\n',
                            '\\t': '\t',
                            '\\r': '\r',
                            '\\\'': '\'',
                            '\\"': '"',
                            '\\\\': '\\',
                            '\\0': '\0',
                            '\\a': '\a',
                            '\\b': '\b',
                            '\\f': '\f',
                            '\\v': '\v'
                        }.get(value, value)
                        value = ord(escape_seq)
                elif kind == 'STRING':
                    value = value[1:-1]
                    value = bytes(value, 'utf-8').decode('unicode_escape')
                
                tokens.append(Token(kind, value, line, column))
        
        tokens.append(Token('EOF', None, self.line, self.column))
        return tokens

def lex_c_code(code):
    lexer = CLexer(code)
    try:
        tokens = lexer.get_tokens()
        return tokens
    except Exception as e:
        print(e)
        return None

def main(c_code):

    
    tokens = lex_c_code(c_code)
    return tokens