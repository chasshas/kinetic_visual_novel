import pygame
import sys
import json
import ply.lex as lex
import ply.yacc as yacc
import pygame_gui
import random
import os

from game_engine import width


# ====================================================================
# [1] 기존 컴파일러 클래스: 변경 없음
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
        r'\b(bg|bgm|locate|stat|goto|place|remove)\b'
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

# 화면 설정
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("My Pygame Game")
clock = pygame.time.Clock()

# 색상
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


# ====================================================================
# [2] Character, Player, Map 클래스: 변경 없음
# ====================================================================
class Character:
    def __init__(self, name, likability=0, dialogues=None):
        self.name = name
        self.likability = likability
        self.dialogues = dialogues if dialogues else {}

    def get_main_dialogue(self, conditions):
        """메인 대화 조건을 확인하고 대화 스크립트를 반환합니다."""
        # TODO: 조건 충족 여부에 따라 메인 대화 스크립트 반환 로직 구현
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
        # TODO: 호감도 증가 로직도 여기에 포함시킬 수 있습니다.


class Map:
    def __init__(self):
        self.map_data = None
        self.load_map("data/map_data.json")
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
        """JSON 파일에서 맵 데이터를 로드합니다."""
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
                    grid_x.append(structure["pos"][0])
                elif (x, y) == [self.x, self.y]:
                    grid_x.append(1)
                else:
                    grid_x.append(0)
            grid.append(grid_x)






    def move(self, vector):
        for i in vector:
            pass

    def render(self):
        """맵 타일을 화면에 그립니다."""
        # TODO: self.map_data를 사용하여 타일 기반 맵 그리기
        pass

    def check_for_structure(self, x, y):
        """플레이어 위치에 구조물이 있는지 확인합니다."""
        # TODO: 구조물 존재 여부 확인 및 상호작용 로직
        pass


# ====================================================================
# [3] Game 클래스: pygame-gui 통합 및 UI 관리 로직 전면 개편
# ====================================================================
class Game:
    def __init__(self):
        # Pygame GUI 매니저 초기화
        self.ui_manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT), 'data/themes/theme.json')

        # ===> 오류 해결을 위해 추가된 변수들 <===
        self.game_running = True  # 게임 루프를 제어하는 변수
        self.state = "TITLE"       # 게임의 현재 상태를 나타내는 변수
        self.placed_objects = {}   # 'place' 커맨드로 배치된 객체를 저장할 딕셔너리

        # UI 그룹 초기화
        self.title_ui_panel = None
        self.settings_popup = None
        self.credits_popup = None

        # 타이틀 화면 UI 생성
        self.create_title_screen_ui()

    def create_title_screen_ui(self):
        """타이틀 화면의 UI 요소들을 패널에 담아 생성합니다."""
        # 타이틀 UI를 담을 패널 생성
        self.title_ui_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((0, 0), (SCREEN_WIDTH, SCREEN_HEIGHT)),
            starting_height=0,
            manager=self.ui_manager,
            visible=True
        )

        button_width, button_height = 200, 50

        new_game_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((SCREEN_WIDTH // 2 - button_width // 2, SCREEN_HEIGHT // 2 - 50),
                                      (button_width, button_height)),
            text='새 게임',
            manager=self.ui_manager,
            container=self.title_ui_panel,
            object_id='#new_game_button'
        )
        load_game_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((SCREEN_WIDTH // 2 - button_width // 2, SCREEN_HEIGHT // 2 + 10),
                                      (button_width, button_height)),
            text='불러오기',
            manager=self.ui_manager,
            container=self.title_ui_panel,
            object_id='#load_game_button'
        )
        settings_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((SCREEN_WIDTH // 2 - button_width // 2, SCREEN_HEIGHT // 2 + 70),
                                      (button_width, button_height)),
            text='환경설정',
            manager=self.ui_manager,
            container=self.title_ui_panel,
            object_id='#settings_button'
        )
        credits_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((SCREEN_WIDTH // 2 - button_width // 2, SCREEN_HEIGHT // 2 + 130),
                                      (button_width, button_height)),
            text='크레딧',
            manager=self.ui_manager,
            container=self.title_ui_panel,
            object_id='#credits_button'
        )
        quit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((SCREEN_WIDTH // 2 - button_width // 2, SCREEN_HEIGHT // 2 + 190),
                                      (button_width, button_height)),
            text='게임 종료',
            manager=self.ui_manager,
            container=self.title_ui_panel,
            object_id='#quit_button'
        )

    def hide_title_ui(self):
        """타이틀 화면의 모든 UI를 숨깁니다."""
        self.title_ui_panel.hide()

    def show_title_ui(self):
        """타이틀 화면의 모든 UI를 표시합니다."""
        self.title_ui_panel.show()

    def start_new_game(self):
        self.state = "MAP"
        self.hide_title_ui()
        # TODO: 게임 초기 상태 설정 (스탯, 호감도 등)

    def load_game(self):
        self.state = "MAP"
        self.hide_title_ui()
        # TODO: 저장된 게임 상태를 로드하는 로직 구현

    def end_game(self):
        self.game_running = False

    def next_day(self):
        self.player.activities_today = 0
        self.player.day += 1
        # TODO: 다음 날 시작 대화 등 추가 로직 구현

    def take_activity(self, activity_type, target=None):
        if self.player.activities_today < 2:
            self.player.activities_today += 1
            if activity_type == "dialogue":
                # TODO: 캐릭터와의 대화 시작 로직
                pass
            elif activity_type == "map":
                # TODO: 맵 활동 (구조물 상호작용 등) 로직
                pass

            if self.player.activities_today >= 2:
                self.state = "VISUAL_NOVEL"
                # TODO: 하루를 마치는 대화 스크립트 로드 및 시작
                pass
        else:
            print("오늘 할 수 있는 활동 횟수를 모두 소진했습니다.")

    def run_dialogue_command(self, command):
        cmd = command['command']
        args = command['args']
        if cmd == 'bg':
            # TODO: 배경 이미지 변경 로직 (args[0]은 파일명)
            pass
        elif cmd == 'bgm':
            # TODO: BGM 변경 로직 (args[0]은 파일명)
            pass
        elif cmd == 'locate':
            # self.current_location 변수가 없으므로 주석 처리
            # self.current_location = args[0]
            pass
        elif cmd == 'stat':
            # self.player 변수가 없으므로 주석 처리
            # stat_name, value = args[0], int(args[1])
            # self.player.increase_stat(stat_name, value)
            pass
        elif cmd == 'goto':
            target_scene = args[0]
            # TODO: 특정 씬으로 이동하는 로직
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

    def process_dialogue(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # TODO: 다음 대사로 진행하는 로직
            pass
        # TODO: 기타 선택지 처리 로직
        pass

    def process_map(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                # TODO: 상방향 이동 로직
                pass
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                # TODO: 하방향 이동 로직
                pass
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                # TODO: 좌방향 이동 로직
                pass
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                # TODO: 우방향 이동 로직
                pass

            # TODO: 맵 상호작용 (캐릭터 만남, 구조물 접근 등) 로직
            pass

    def render_title_screen(self):
        screen.fill(BLACK)
        title_font = pygame.font.Font(None, 48)
        title_text = title_font.render("My Pygame Game", True, WHITE)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 200))
        # UI 요소는 UIManager가 그립니다.

    def render_dialogue(self):
        # TODO: 배경 이미지, 텍스트 박스, 대사, 이름 등 그리기 로직
        for obj in self.placed_objects.values():
            screen.blit(obj['image'], obj['rect'])

    def render_map(self):
        # TODO: 맵 타일, 구조물, 플레이어 캐릭터 그리기 로직
        pass

    def run(self):
        while self.game_running:
            time_delta = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.end_game()

                # UIManager에 모든 이벤트를 전달
                self.ui_manager.process_events(event)

                # pygame-gui 위젯 이벤트 처리
                if event.type == pygame.USEREVENT:
                    if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                        # 오브젝트 ID를 사용하여 버튼 구분
                        button_id = event.ui_element.get_object_ids()[0]
                        if button_id == '#new_game_button':
                            self.start_new_game()
                        elif button_id == '#load_game_button':
                            self.load_game()
                        # settings와 credits 팝업에 대한 메서드가 없으므로 주석 처리
                        # elif button_id == '#settings_button':
                        #     self.show_settings_popup()
                        # elif button_id == '#credits_button':
                        #     self.show_credits_popup()
                        elif button_id == '#quit_button':
                            self.end_game()
                        elif button_id == '#close_button':
                            event.ui_element.get_container().hide()

                # 기존의 수동 이벤트 처리 로직 (필요시 사용)
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

            # UIManager 업데이트 및 UI 그리기
            self.ui_manager.update(time_delta)
            self.ui_manager.draw_ui(screen)

            pygame.display.flip()


# ====================================================================
# [4] 실행
# ====================================================================
if __name__ == "__main__":

    # 테마 폴더 생성


    if not os.path.exists('data/themes'):
        os.makedirs('data/themes')
        with open('data/themes/theme.json', 'w', encoding='utf-8') as f:
            f.write(
                '{"defaults": {"font": {"name": "nanumgothic", "size": "20", "regular_path": "assets/fonts/Nanumgothic.ttf", "bold_path": "assets/fonts/NanumgothicBold.ttf"}}}')

    game = Game()
    game.run()