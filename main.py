import pygame
import sys
import json
import ply.lex as lex
import ply.yacc as yacc
import random
import os


# ====================================================================
# [1] 기존 컴파일러 클래스: 변경 사항 없음
# ====================================================================
class VnCompiler:
    tokens = (
        'SCENE', 'ID', 'COLON', 'TEXT', 'LPAREN', 'RPAREN', 'ARROW',
        'NARRATOR', 'CHOICE', 'COMMAND'
    )

    def t_SCENE(self, t):
        r'@[a-zA-Z_][a-zA-Z0-9_]*:'
        t.value = t.value[:-1]
        return t

    def t_CHOICE(self, t):
        r'choice:'
        return t

    def t_NARRATOR(self, t):
        r'\$:'
        return t

    def t_COMMAND(self, t):
        r'\b(bg|bgm|locate|stat|goto|place|remove|end)\b'
        return t

    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_./]*'
        return t

    t_COLON = r':'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_ARROW = r'->'

    def t_TEXT(self, t):
        r'.+?(?=(\(.*\))?\n|->|:)'
        t.value = t.value.strip()
        if t.value:
            return t

    t_ignore = ' \t'

    def t_ignore_COMMENT(self, t):
        r'\#.*'
        pass

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        print(f"Illegal character '{t.value[0]}' at line {t.lexer.lineno}")
        t.lexer.skip(1)

    def p_script(self, p):
        'script : scenes'
        p[0] = p[1]

    def p_scenes_multiple(self, p):
        'scenes : scenes scene'
        p[0] = p[1] + [p[2]]

    def p_scenes_single(self, p):
        'scenes : scene'
        p[0] = [p[1]]

    def p_scene(self, p):
        'scene : SCENE components'
        p[0] = {'type': 'scene', 'name': p[1], 'components': p[2]}

    def p_components_multiple(self, p):
        'components : components component'
        p[0] = p[1] + [p[2]]

    def p_components_single(self, p):
        'components : component'
        p[0] = [p[1]]

    def p_component(self, p):
        '''component : dialogue
                     | narration
                     | command
                     | choice'''
        p[0] = p[1]

    def p_dialogue_with_dub(self, p):
        'dialogue : ID COLON TEXT LPAREN ID RPAREN'
        p[0] = {'type': 'utter', 'speaker': p[1], 'utter': p[3], 'dubbing': p[5]}

    def p_dialogue_no_dub(self, p):
        'dialogue : ID COLON TEXT'
        p[0] = {'type': 'utter', 'speaker': p[1], 'utter': p[3], 'dubbing': None}

    def p_narration(self, p):
        'narration : NARRATOR TEXT'
        p[0] = {'type': 'utter', 'speaker': '', 'utter': p[2], 'dubbing': None}

    def p_command_with_args(self, p):
        'command : COMMAND args'
        p[0] = {'type': 'command', 'command': p[1], 'args': p[2]}

    def p_command_goto(self, p):
        'command : COMMAND SCENE'
        p[0] = {'type': 'command', 'command': p[1], 'args': [p[2]]}

    def p_command_place(self, p):
        'command : COMMAND ID ID'
        p[0] = {'type': 'command', 'command': p[1], 'args': [p[2], p[3]]}

    def p_command_place_full(self, p):
        'command : COMMAND ID ID ID ID'
        p[0] = {'type': 'command', 'command': p[1], 'args': [p[2], p[3], p[4], p[5]]}

    def p_args_multiple(self, p):
        'args : args ID'
        p[0] = p[1] + [p[2]]

    def p_args_single(self, p):
        'args : ID'
        p[0] = [p[1]]

    def p_choice(self, p):
        'choice : CHOICE options'
        p[0] = {'type': 'choice', 'options': p[2]}

    def p_options_multiple(self, p):
        'options : options option'
        p[0] = p[1] + [p[2]]

    def p_options_single(self, p):
        'options : option'
        p[0] = [p[1]]

    def p_option_conditional(self, p):
        'option : TEXT LPAREN ID ID RPAREN ARROW SCENE'
        try:
            value = int(p[4])
        except ValueError:
            value = p[4]
        p[0] = {
            'text': p[1],
            'condition': {'stat': p[3], 'value': value},
            'target': p[7]
        }

    def p_option_normal(self, p):
        'option : TEXT ARROW SCENE'
        p[0] = {'text': p[1], 'condition': None, 'target': p[3]}

    def p_error(self, p):
        if p:
            print(f"Syntax error at '{p.value}' (type: {p.type}) on line {p.lineno}")
        else:
            print("Syntax error at EOF")

    def __init__(self):
        self.lexer = lex.lex(module=self)
        self.parser = yacc.yacc(module=self)

    def compile(self, script_text):
        if not script_text.strip():
            return []
        return self.parser.parse(script_text, lexer=self.lexer)


# Pygame 초기화
pygame.init()
pygame.font.init()

# 화면 설정
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("My Pygame Game")
clock = pygame.time.Clock()

# 색상
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (50, 50, 50)
LIGHT_GRAY = (100, 100, 100)


def scale_image(image, max_width, max_height):
    original_width, original_height = image.get_size()
    width_ratio = max_width / original_width
    height_ratio = max_height / original_height
    scale_ratio = min(width_ratio, height_ratio)
    new_width = int(original_width * scale_ratio)
    new_height = int(original_height * scale_ratio)
    return pygame.transform.smoothscale(image, (new_width, new_height))


def render_text_to_surf(text, surf, font):
    text_surf = font.render(text, True, WHITE)
    text_rect = text_surf.get_rect(center=surf.get_rect().center)
    surf.blit(text_surf, text_rect)

# ====================================================================
# [2] Character, Player, Map 클래스: 변경 없음
# ====================================================================
class Character:
    def __init__(self, name, likability=0, dialogues=None):
        self.name = name
        self.likability = likability
        self.dialogues = dialogues if dialogues else {}

    def get_main_dialogue(self, conditions):
        pass


class Player(Character):
    def __init__(self, name="주인공"):
        super().__init__(name)
        self.stats = {
            "예술": 0,
            "문학": 0,
            "체육": 0,
            "운": 0,
            "눈치": 0,
        }
        self.activities_today = 0
        self.day = 1

    def increase_stat(self, stat_name, value):
        if stat_name in self.stats:
            self.stats[stat_name] += value


class Map:
    def __init__(self):
        self.map_data = None
        self.load_map("data/map.json")
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.structures = []
        self.structure_place = []
        self.grid = []
        self.place_structure()
        self.get_grid()

    def load_map(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.map_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: Map data file not found at {filename}")
            self.map_data = {}
        data = self.map_data
        try:
            data["structures"] = self.structures
            data["width"] = self.width
            data["height"] = self.height
            self.x = random.choice(range(self.width))
            self.y = random.choice(range(self.height))
        except:
            print(f"Error: Map data file not found at {filename}")

    def place_structure(self):
        positions = []
        structure_places = []
        for structure in self.structures:
            is_set = False
            while not is_set:
                pos_x = random.choice(range(self.width))
                pos_y = random.choice(range(self.height))
                if [pos_x, pos_y] in positions:
                    pass
                else:
                    if [pos_x, pos_y] != [self.x, self.y]:
                        positions.append([pos_x, pos_y])
                        is_set = True
            structure["pos"] = [pos_x, pos_y]
            structure_places.append(structure)
        self.structure_place = structure_places

    def get_grid(self):
        structures = self.structure_place
        grid = []
        pos_list = []
        for structure in structures:
            pos_list.append([structure["pos"][0], structure["pos"][1]])

        for x in range(self.width):
            grid_x = []
            for y in range(self.height):
                if (x, y) in pos_list:
                    for i in structures:
                        if i["pos"][0] == x and i["pos"][1] == y:
                            grid_x.append(i)
                elif (x, y) == [self.x, self.y]:
                    grid_x.append(1)
                else:
                    grid_x.append(0)
            grid.append(grid_x)

        self.grid = grid

    def move(self, vector):
        self.x += vector[0]
        if self.x < 0:
            self.x = 0
        elif self.x > self.width:
            self.x = self.width - 1
        self.y += vector[1]
        if self.y < 0:
            self.y = 0
        elif self.y > self.height:
            self.y = self.height - 1
        st = self.check_for_structure()
        if not st:
            self.sudden_dialogue()

    def render(self):
        pass

    def check_for_structure(self):
        x = self.x
        y = self.y
        structures = self.structure_place
        for structure in structures:
            if structure["pos"][0] == x and structure["pos"][1] == y:
                exec(structure["code"])
                return 1
        return 0

    def sudden_dialogue(self):
        if random.random() < 0.1:
            return []


# ====================================================================
# [3] Game 클래스: pygame-gui 통합 및 UI 관리 로직 전면 개편
# ====================================================================

class Button:
    def __init__(self, rect, image, callback=None):
        self.rect = rect
        self.image = image
        self.callback = callback

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
                return True
        return False

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Game:
    def __init__(self):
        self.game_running = True
        self.state = "TITLE"
        self.placed_objects = {}
        self.player = Player()
        self.map_data = Map()
        self.completed_conversation = []

        try:
            self.main_font = pygame.font.SysFont("Malgun Gothic", 24)
            self.title_font = pygame.font.SysFont("Malgun Gothic", 48)
        except:
            self.main_font = pygame.font.SysFont(pygame.font.get_default_font(), 24)
            self.title_font = pygame.font.SysFont(pygame.font.get_default_font(), 48)

        # 버튼 인스턴스를 저장할 리스트를 초기화만 합니다.
        self.buttons = []

    def start_new_game(self):
        self.state = "MAP"
        print("새 게임 시작!")

    def load_game(self):
        self.state = "MAP"
        print("게임 불러오기!")

    def end_game(self):
        self.game_running = False

    def next_day(self):
        self.player.activities_today = 0
        self.player.day += 1

    def run_dialogue_command(self, command):
        cmd = command['command']
        args = command['args']
        if cmd == 'bg':
            pass
        elif cmd == 'bgm':
            pass
        elif cmd == 'locate':
            pass
        elif cmd == 'stat':
            stat_name, value = args[0], int(args[1])
            self.player.increase_stat(stat_name, value)
        elif cmd == 'goto':
            target_scene = args[0]
            pass
        elif cmd == 'place':
            objname, filename = args[0], args[1]
            try:
                image = pygame.image.load(filename).convert_alpha()
                if len(args) == 4:
                    x_pos, y_pos = int(args[2]), int(args[3])
                else:
                    default_x = (SCREEN_WIDTH - image.get_width()) // 2
                    default_y = SCREEN_HEIGHT - image.get_height()
                    x_pos, y_pos = default_x, default_y

                rect = image.get_rect(x=x_pos, y=y_pos)
                self.placed_objects[objname] = {'image': image, 'rect': rect}
            except pygame.error as e:
                print(f"Error loading image '{filename}': {e}")
        elif cmd == 'remove':
            objname = args[0]
            if objname in self.placed_objects:
                del self.placed_objects[objname]
            else:
                print(f"Warning: Object '{objname}' not found for removal.")
        elif cmd == 'end':
            self.state = "MAP"

    def process_dialogue(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pass
        pass

    def process_map(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                self.map_data.move([0, -1])
                self.player.activities_today += 1
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                self.map_data.move([0, 1])
                self.player.activities_today += 1
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                self.map_data.move([-1, 0])
                self.player.activities_today += 1
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                self.map_data.move([1, 0])
                self.player.activities_today += 1

    def render_title_screen(self):
        screen.fill(BLACK)
        title_text = self.title_font.render("My Pygame Game", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 200))

        self.buttons.clear()  # 매 프레임마다 버튼 리스트 초기화

        button_width, button_height = 200, 50

        # 텍스트 렌더링을 위한 임시 함수



        # 새 게임 버튼 동적 생성
        normal_surf = pygame.Surface((button_width, button_height))
        normal_surf.fill(GRAY)
        render_text_to_surf("새 게임", normal_surf, self.main_font)
        self.buttons.append(
            Button(
                pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, SCREEN_HEIGHT // 2 - 50, button_width,
                            button_height),
                normal_surf, self.start_new_game
            )
        )

        # 불러오기 버튼 동적 생성
        normal_surf_load = pygame.Surface((button_width, button_height))
        normal_surf_load.fill(GRAY)
        render_text_to_surf("불러오기", normal_surf_load, self.main_font)
        self.buttons.append(
            Button(
                pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, SCREEN_HEIGHT // 2 + 10, button_width,
                            button_height),
                normal_surf_load, self.load_game
            )
        )

        # 게임 종료 버튼 동적 생성
        normal_surf_quit = pygame.Surface((button_width, button_height))
        normal_surf_quit.fill(GRAY)
        render_text_to_surf("게임 종료", normal_surf_quit, self.main_font)
        self.buttons.append(
            Button(
                pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, SCREEN_HEIGHT // 2 + 70, button_width,
                            button_height),
                normal_surf_quit, self.end_game
            )
        )

    def render_dialogue(self):
        for obj in self.placed_objects.values():
            screen.blit(obj['image'], obj['rect'])

    def render_map(self):
        self.map_data.render()

    def render_status(self):
        stat_data = self.player.stats

    def render_menu(self):
        pass

    def run(self):
        while self.game_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.end_game()
                # Button 클래스의 handle_event() 메서드를 호출하여 이벤트 처리
                if self.buttons:
                    for button in self.buttons:
                        if button.handle_event(event):
                            break  # 버튼이 클릭되면 더 이상 다른 버튼을 확인할 필요 없음

                if self.state == "VISUAL_NOVEL":
                    self.process_dialogue(event)
                elif self.state == "MAP":
                    self.process_map(event)

            # 렌더링 파트
            if self.state == "TITLE":
                self.render_title_screen()
            elif self.state == "VISUAL_NOVEL":
                self.render_dialogue()
            elif self.state == "MAP":
                self.render_map()

            pygame.display.flip()
            clock.tick(60)


# ====================================================================
# [4] 실행
# ====================================================================
if __name__ == "__main__":
    game = Game()
    game.run()