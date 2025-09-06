import ply.lex as lex
import ply.yacc as yacc
import re

import pygame

#display
width = 1080
height = 720
fps = 60

#font
def get_font(size: int, style: str = "default" ):
    if style == "default":
        return pygame.font.Font("assets/fonts/NanumGothic.ttf", size)
    return pygame.font.Font(f"assets/fonts/NanumGothic{style}.ttf", size)
font_default = get_font(size=20)
#colors

#player manage
class Player:
    def __init__(self, adv,art, literature, physical):
        pass

#character manage
class Character(Player):
    def __init__(self, ):

#dialogue
class Utterance:
    def __init__(self, speaker, text):
        self.speaker = speaker
        self.text = text

#commands for functions

#commands
class Command:
    def __init__(self, command, args):
        self.command = command
        self.args = args

    def execute(self):
        print(self.command)

#scene
class Scene:
    """structured with command, utterance"""
    def __init__(self, components:list):
        self.components = components

#dialogue render
class DialogueBox:
    def __init__(self, screen, write_interval: int = 20):
        self.screen = screen
        self.dialogue = ""
    def draw(self):
        pass


#button
class Button:
    def __init__(self, screen, img, size):
        self.screen = screen
        self.img = img
        self.size = size

#menu
class MenuRenderer:
    def __init__(self, screen, Buttons):
        self.screen = screen
        self.Buttons = Buttons


#interpreter
class VisualNovelInterpreter:
    def __init__(self):
        self.scenes = {}
        self.variables = {}
        self.stats = {}
        self.indent_stack = [0]  # For tracking indentation levels

        # Build lexer and parser
        self.lexer = lex.lex(module=self)
        self.parser = yacc.yacc(module=self)

    # Token definitions
    tokens = (
        'CHARACTER',
        'TEXT',
        'SCENE_DEF',
        'SCENE_REF',
        'CHOICE',
        'IF',
        'ELSE',
        'SET',
        'ARROW',
        'OPTION',
        'CONDITION',
        'COMMAND',
        'IDENTIFIER',
        'NUMBER',
        'FLOAT',
        'STRING',
        'FORMATTED_STRING',
        'COMPARISON',
        'PLUS',
        'MINUS',
        'TIMES',
        'DIVIDE',
        'LPAREN',
        'RPAREN',
        'ESCAPED_LPAREN',
        'ESCAPED_RPAREN',
        'LBRACE',
        'RBRACE',
        'COLON',
        'NEWLINE',
        'INDENT',
        'DEDENT',
        'TRUE',
        'FALSE',
    )

    # Reserved words
    reserved = {
        'choice': 'CHOICE',
        'if': 'IF',
        'else': 'ELSE',
        'set': 'SET',
        'sound': 'COMMAND',
        'bgm': 'COMMAND',
        'bg': 'COMMAND',
        'show': 'COMMAND',
        'goto': 'COMMAND',
        'move': 'COMMAND',
        'stat': 'COMMAND',
        'var': 'COMMAND',
        'end': 'COMMAND',
        'true': 'TRUE',
        'false': 'FALSE',
    }

    # Token rules
    t_ARROW = r'->'
    t_COLON = r':'
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_ESCAPED_LPAREN = r'\\\('
    t_ESCAPED_RPAREN = r'\\\)'
    t_COMPARISON = r'>=|<=|==|!=|>|<'

    # Ignore spaces and tabs (but not newlines)
    t_ignore = ' \t'

    def t_SCENE_DEF(self, t):
        r'@[a-zA-Z_][a-zA-Z0-9_]*:'
        t.value = t.value[1:-1]  # Remove @ and :
        return t

    def t_SCENE_REF(self, t):
        r'@[a-zA-Z_][a-zA-Z0-9_]*'
        t.value = t.value[1:]  # Remove @
        return t

    def t_CHARACTER(self, t):
        r'^[a-zA-Z_][a-zA-Z0-9_]*:'
        t.value = t.value[:-1]  # Remove colon
        return t

    def t_FLOAT(self, t):
        r'\d+\.\d+'
        t.value = float(t.value)
        return t

    def t_NUMBER(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    def t_STRING(self, t):
        r'"[^"]*"'
        t.value = t.value[1:-1]  # Remove quotes
        return t

    def t_FORMATTED_STRING(self, t):
        r'[^:\n]*\{[^}]*\}[^:\n]*'
        return t

    def t_CONDITION(self, t):
        r'\([^)]+\)'
        content = t.value[1:-1]  # Remove parentheses
        t.value = content
        return t

    def t_OPTION(self, t):
        r'[^->\n\(]+(?=\s*(?:\([^)]*\))?\s*->)'
        t.value = t.value.strip()
        return t

    def t_IDENTIFIER(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        t.type = self.reserved.get(t.value, 'IDENTIFIER')
        return t

    def t_TEXT(self, t):
        r'[^\n\{]+'
        return t

    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
        return t

    def t_error(self, t):
        print(f"Illegal character '{t.value[0]}'")
        t.lexer.skip(1)

    # Indentation handling (simplified)
    def handle_indentation(self, text):
        """Handle indentation and generate INDENT/DEDENT tokens"""
        lines = text.split('\n')
        tokens = []

        for line in lines:
            if line.strip() == '':
                continue

            indent = len(line) - len(line.lstrip())
            content = line.strip()

            if indent > self.indent_stack[-1]:
                self.indent_stack.append(indent)
                tokens.append(('INDENT', indent))
            elif indent < self.indent_stack[-1]:
                while self.indent_stack[-1] > indent:
                    self.indent_stack.pop()
                    tokens.append(('DEDENT', indent))

            # Tokenize the content
            tokens.append(('CONTENT', content))

        return tokens

    # Grammar rules
    def p_script(self, p):
        '''script : statements'''
        p[0] = p[1]

    def p_statements(self, p):
        '''statements : statements statement
                     | statement'''
        if len(p) == 2:
            p[0] = [p[1]] if p[1] else []
        else:
            p[0] = (p[1] or []) + ([p[2]] if p[2] else [])

    def p_statement(self, p):
        '''statement : scene_def
                    | dialogue
                    | choice_block
                    | if_block
                    | command
                    | NEWLINE'''
        if p[1] != '\n' and p[1] is not None:
            p[0] = p[1]

    def p_scene_def(self, p):
        '''scene_def : SCENE_DEF NEWLINE'''
        p[0] = ('scene_def', p[1])

    def p_dialogue(self, p):
        '''dialogue : CHARACTER TEXT NEWLINE
                   | CHARACTER FORMATTED_STRING NEWLINE'''
        p[0] = ('dialogue', p[1], p[2])

    def p_choice_block(self, p):
        '''choice_block : CHOICE COLON NEWLINE choice_options'''
        p[0] = ('choice', p[4])

    def p_choice_options(self, p):
        '''choice_options : choice_options choice_option
                         | choice_option'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    def p_choice_option(self, p):
        '''choice_option : OPTION ARROW SCENE_REF NEWLINE
                        | OPTION CONDITION ARROW SCENE_REF NEWLINE'''
        if len(p) == 5:
            p[0] = ('option', p[1], None, p[3])
        else:
            p[0] = ('option', p[1], p[2], p[4])

    def p_if_block(self, p):
        '''if_block : IF condition COLON NEWLINE statements
                   | IF condition COLON NEWLINE statements ELSE COLON NEWLINE statements'''
        if len(p) == 6:
            p[0] = ('if', p[2], p[5], None)
        else:
            p[0] = ('if', p[2], p[5], p[9])

    def p_condition(self, p):
        '''condition : expression COMPARISON expression
                    | IDENTIFIER'''
        if len(p) == 2:
            p[0] = ('bool_check', p[1])
        else:
            p[0] = ('comparison', p[1], p[2], p[3])

    def p_expression(self, p):
        '''expression : expression PLUS term
                     | expression MINUS term
                     | term'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = ('binop', p[1], p[2], p[3])

    def p_term(self, p):
        '''term : term TIMES factor
               | term DIVIDE factor
               | factor'''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = ('binop', p[1], p[2], p[3])

    def p_factor(self, p):
        '''factor : NUMBER
                 | FLOAT
                 | STRING
                 | IDENTIFIER
                 | TRUE
                 | FALSE
                 | LPAREN expression RPAREN'''
        if len(p) == 2:
            if p[1] == 'true':
                p[0] = True
            elif p[1] == 'false':
                p[0] = False
            else:
                p[0] = p[1]
        else:
            p[0] = p[2]

    def p_command(self, p):
        '''command : media_command
                  | game_command
                  | var_command
                  | set_command'''
        p[0] = p[1]

    def p_media_command(self, p):
        '''media_command : COMMAND STRING NEWLINE
                        | COMMAND IDENTIFIER NEWLINE'''
        if p[1] in ['sound', 'bgm', 'bg', 'show']:
            p[0] = ('media_command', p[1], p[2])

    def p_game_command(self, p):
        '''game_command : COMMAND SCENE_REF NEWLINE
                       | COMMAND STRING NEWLINE
                       | COMMAND IDENTIFIER expression NEWLINE
                       | COMMAND NEWLINE'''
        if len(p) == 3:
            if p[1] == 'end':
                p[0] = ('end_command',)
        elif len(p) == 4:
            if p[1] == 'goto':
                p[0] = ('goto_command', p[2])
            elif p[1] == 'move':
                p[0] = ('move_command', p[2])
        elif len(p) == 5:
            if p[1] == 'stat':
                p[0] = ('stat_command', p[2], p[3])

    def p_var_command(self, p):
        '''var_command : COMMAND IDENTIFIER expression NEWLINE'''
        if p[1] == 'var':
            p[0] = ('var_command', p[2], p[3])

    def p_set_command(self, p):
        '''set_command : SET IDENTIFIER expression NEWLINE'''
        p[0] = ('set_command', p[2], p[3])

    def p_error(self, p):
        if p:
            print(f"Syntax error at token {p.type} ('{p.value}') at line {p.lineno}")
        else:
            print("Syntax error at EOF")

    # Expression evaluation
    def evaluate_expression(self, expr):
        """Evaluate expressions recursively"""
        if isinstance(expr, (int, float, str, bool)):
            return expr

        if isinstance(expr, str):  # Variable reference
            return self.variables.get(expr, self.stats.get(expr, 0))

        if expr[0] == 'binop':
            left = self.evaluate_expression(expr[1])
            op = expr[2]
            right = self.evaluate_expression(expr[3])

            if op == '+':
                return left + right
            elif op == '-':
                return left - right
            elif op == '*':
                return left * right
            elif op == '/':
                return left / right if right != 0 else 0

        return 0

    def evaluate_condition(self, condition):
        """Evaluate condition"""
        if condition[0] == 'bool_check':
            var_name = condition[1]
            return bool(self.variables.get(var_name, False))

        elif condition[0] == 'comparison':
            left = self.evaluate_expression(condition[1])
            op = condition[2]
            right = self.evaluate_expression(condition[3])

            if op == '>=':
                return left >= right
            elif op == '<=':
                return left <= right
            elif op == '==':
                return left == right
            elif op == '!=':
                return left != right
            elif op == '>':
                return left > right
            elif op == '<':
                return left < right

        return False

    def format_string(self, text):
        """Handle f-string style formatting"""
        if '{' not in text:
            return text

        # Simple replacement - in real implementation, use proper parsing
        result = text
        import re

        def replace_var(match):
            var_name = match.group(1)
            value = self.variables.get(var_name, self.stats.get(var_name, ''))
            return str(value)

        result = re.sub(r'\{([^}]+)\}', replace_var, result)
        return result

    # Execution methods
    def execute_dialogue(self, character, text):
        """Display dialogue with variable interpolation"""
        formatted_text = self.format_string(text)
        print(f"{character}: {formatted_text}")
        self.display_dialogue(character, formatted_text)

    def execute_choice(self, options):
        """Present choices to player"""
        print("Choices:")
        valid_options = []
        for i, option in enumerate(options):
            text, condition, scene = option[1], option[2], option[3]
            if condition and not self.evaluate_old_condition(condition):
                continue
            valid_options.append((text, scene))
            print(f"{i + 1}. {text}")
        return valid_options

    def execute_if(self, condition, then_stmts, else_stmts):
        """Execute if statement"""
        if self.evaluate_condition(condition):
            if then_stmts:
                self.execute_ast(then_stmts)
        elif else_stmts:
            self.execute_ast(else_stmts)

    def execute_media_command(self, command, filename):
        """Execute media commands"""
        print(f"Executing {command}: {filename}")
        if command == 'sound':
            self.play_sound(filename)
        elif command == 'bgm':
            self.play_bgm(filename)
        elif command == 'bg':
            self.show_background(filename)
        elif command == 'show':
            self.show_image(filename)

    def execute_goto(self, scene):
        """Jump to scene"""
        print(f"Going to scene: {scene}")
        self.goto_scene(scene)

    def execute_move(self, location):
        """Move to location"""
        print(f"Moving to: {location}")
        self.move_to_location(location)

    def execute_stat(self, stat_name, value_expr):
        """Modify stat"""
        value = self.evaluate_expression(value_expr)
        self.stats[stat_name] = self.stats.get(stat_name, 0) + value
        print(f"Stat {stat_name} changed by {value}, now: {self.stats[stat_name]}")

    def execute_var(self, var_name, value_expr):
        """Set variable"""
        value = self.evaluate_expression(value_expr)
        self.variables[var_name] = value
        print(f"Variable {var_name} = {value}")

    def execute_set(self, var_name, value_expr):
        """Set variable (alternative syntax)"""
        value = self.evaluate_expression(value_expr)
        self.variables[var_name] = value
        print(f"Set {var_name} = {value}")

    def evaluate_old_condition(self, condition):
        """Legacy condition evaluation"""
        tokens = condition.split()
        if len(tokens) >= 3:
            stat_name = tokens[0]
            operator = tokens[1]
            value = float(tokens[2]) if '.' in tokens[2] else int(tokens[2])
            stat_value = self.stats.get(stat_name, 0)

            if operator == '>=':
                return stat_value >= value
            elif operator == '<=':
                return stat_value <= value
            elif operator == '==':
                return stat_value == value
            elif operator == '!=':
                return stat_value != value
            elif operator == '>':
                return stat_value > value
            elif operator == '<':
                return stat_value < value
        return True

    # Placeholder functions
    def display_dialogue(self, character, text):
        pass

    def play_sound(self, filename):
        print(f"[SOUND] {filename}")

    def play_bgm(self, filename):
        print(f"[BGM] {filename}")

    def show_background(self, filename):
        print(f"[BACKGROUND] {filename}")

    def show_image(self, filename):
        print(f"[IMAGE] {filename}")

    def goto_scene(self, scene):
        print(f"[GOTO] {scene}")

    def move_to_location(self, location):
        print(f"[MOVE] {location}")

    def close_dialogue(self):
        print("[DIALOGUE CLOSED]")

    def parse(self, text):
        """Parse script"""
        result = self.parser.parse(text, lexer=self.lexer)
        return result

    def run_script(self, script_text):
        """Run complete script"""
        try:
            ast = self.parse(script_text)
            if ast:
                self.execute_ast(ast)
        except Exception as e:
            print(f"Error running script: {e}")
            import traceback
            traceback.print_exc()

    def execute_ast(self, statements):
        """Execute parsed AST"""
        if not statements:
            return

        for stmt in statements:
            if not stmt:
                continue

            stmt_type = stmt[0]

            if stmt_type == 'dialogue':
                self.execute_dialogue(stmt[1], stmt[2])
            elif stmt_type == 'choice':
                self.execute_choice(stmt[1])
            elif stmt_type == 'if':
                self.execute_if(stmt[1], stmt[2], stmt[3])
            elif stmt_type == 'media_command':
                self.execute_media_command(stmt[1], stmt[2])
            elif stmt_type == 'goto_command':
                self.execute_goto(stmt[1])
            elif stmt_type == 'move_command':
                self.execute_move(stmt[1])
            elif stmt_type == 'stat_command':
                self.execute_stat(stmt[1], stmt[2])
            elif stmt_type == 'var_command':
                self.execute_var(stmt[1], stmt[2])
            elif stmt_type == 'set_command':
                self.execute_set(stmt[1], stmt[2])
            elif stmt_type == 'scene_def':
                self.scenes[stmt[1]] = True
                print(f"Scene defined: {stmt[1]}")
            elif stmt_type == 'end_command':
                self.close_dialogue()
                break

#visual novel form management
class VisualNovelManager:
    def __init__(self, file):
        pass

#
# Example usage
if __name__ == "__main__":
    interpreter = VisualNovelInterpreter()

    # Updated test script
    test_script = """
@start:
var user "Player"
set knowledge 3

maria: Hello, {user}! Welcome to our story.
john: Your knowledge level is {knowledge}.

if knowledge >= 5:
    maria: Impressive knowledge!
    stat wisdom 10
else:
    maria: You could learn more.
    stat wisdom 1

choice:
    Hello?\(knowledge >= 5\) -> @greetings  
    Who are you? -> @wonder

@greetings:
maria: Great to see a knowledgeable person!
stat knowledge 2
goto @end

@wonder:  
john: I'm just a character in this story.
set met_john true
goto @end

@end:
sound "victory.wav" 
move "town_square"
end
"""

    print("=== Running Visual Novel Script ===")
    interpreter.run_script(test_script)


