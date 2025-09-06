import pygame
import json
import os
import sys
from enum import Enum
from typing import Dict, List, Optional, Any

# Initialize pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TILE_SIZE = 32
ACTIONS_PER_DAY = 2

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 200)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
GREEN = (0, 200, 0)


class GameState(Enum):
    TITLE_SCREEN = 0
    VISUAL_NOVEL = 1
    MAP = 2


class CharacterType(Enum):
    haram = "유하람"
    eunyu = "최은유"
    yuah = "한유아"
    shihyun = "백시현"


class GameData:
    def __init__(self):
        # 플레이어 스탯
        self.stats = {
            "art": 0,
            "literature": 0,
            "physical": 0,
            "luck": 0,
            "sense": 0
        }

        # 히로인 호감도
        self.affection = {
            "eunyu": 0,
            "yuah": 0,
            "shihyun": 0
        }

        # 게임 진행 상태
        self.day = 1
        self.actions_today = 0
        self.current_scene = ""
        self.current_dialogue_file = ""


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Visual Novel RPG")
        self.clock = pygame.time.Clock()
        self.running = True

        # 게임 상태
        self.game_state = GameState.TITLE_SCREEN
        self.game_data = GameData()

        # 타이틀 메뉴
        self.title_selected = 0

        # 대화 시스템
        self.dialogue_scenes = {}  # scene_id: scene_data
        self.current_scene_data = None
        self.current_line = 0

        # 맵 시스템
        self.map_data = {
            "width": 20,
            "height": 15,
            "tiles": [],
            "structures": [],  # {"name": str, "x": int, "y": int, "stats": dict, "text": str}
            "characters": []  # {"name": str, "type": CharacterType, "x": int, "y": int, "daily": str, "main": str}
        }
        self.player_x = 5
        self.player_y = 5

        # 폰트
        self.font = pygame.font.Font("assets/fonts/NanumGothic.ttf", 36)
        self.small_font = pygame.font.Font("assets/fonts/NanumGothic.ttf", 24)
        self.large_font = pygame.font.Font("assets/fonts/NanumGothic.ttf", 48)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if self.game_state == GameState.TITLE_SCREEN:
                self.handle_title_input(event)
            elif self.game_state == GameState.VISUAL_NOVEL:
                self.handle_dialogue_input(event)
            elif self.game_state == GameState.MAP:
                self.handle_map_input(event)

    def handle_title_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.title_selected = (self.title_selected - 1) % 3
            elif event.key == pygame.K_DOWN:
                self.title_selected = (self.title_selected + 1) % 3
            elif event.key == pygame.K_RETURN:
                if self.title_selected == 0:  # 새 게임
                    self.start_new_game()
                elif self.title_selected == 1:  # 불러오기
                    self.load_game()
                elif self.title_selected == 2:  # 게임 종료
                    self.running = False

    def handle_dialogue_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                if self.current_scene_data and "choices" in self.current_scene_data:
                    pass  # 선택지가 있으면 숫자키로 선택
                else:
                    self.advance_dialogue()

            # 선택지 선택 (1-9)
            elif pygame.K_1 <= event.key <= pygame.K_9:
                choice_index = event.key - pygame.K_1
                if self.current_scene_data and "choices" in self.current_scene_data:
                    if choice_index < len(self.current_scene_data["choices"]):
                        self.select_choice(choice_index)

    def handle_map_input(self, event):
        if event.type == pygame.KEYDOWN:
            # 이동
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                self.move_player(0, -1)
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                self.move_player(0, 1)
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                self.move_player(-1, 0)
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                self.move_player(1, 0)
            elif event.key == pygame.K_SPACE:
                self.interact()

    def start_new_game(self):
        self.game_data = GameData()
        self.load_initial_map()
        self.game_state = GameState.MAP

    def load_game(self):
        # 세이브 파일 로드 - to be implemented
        pass

    def save_game(self):
        # 게임 저장 - to be implemented
        pass

    def load_initial_map(self):
        # 초기 맵 데이터 설정 - to be implemented
        pass

    def load_dialogue_file(self, filename):
        # 대화 파일 로드 - to be implemented
        # JSON 형태로 된 대화 데이터를 로드하여 self.dialogue_scenes에 저장
        pass

    def start_dialogue(self, filename, scene_id="start"):
        self.load_dialogue_file(filename)
        self.current_scene_data = self.dialogue_scenes.get(scene_id)
        self.current_line = 0
        self.game_state = GameState.VISUAL_NOVEL

    def advance_dialogue(self):
        if not self.current_scene_data or "lines" not in self.current_scene_data:
            return

        self.current_line += 1

        # 씬의 모든 대사를 읽었으면
        if self.current_line >= len(self.current_scene_data["lines"]):
            if "next_scene" in self.current_scene_data:
                # 다음 씬으로
                next_scene = self.current_scene_data["next_scene"]
                self.current_scene_data = self.dialogue_scenes.get(next_scene)
                self.current_line = 0
            elif "choices" not in self.current_scene_data:
                # 선택지도 없으면 대화 종료
                self.end_dialogue()

    def select_choice(self, choice_index):
        if not self.current_scene_data or "choices" not in self.current_scene_data:
            return

        choices = self.current_scene_data["choices"]
        if choice_index >= len(choices):
            return

        choice = choices[choice_index]

        # 스탯 조건 확인
        if "required_stats" in choice:
            for stat_name, required_amount in choice["required_stats"].items():
                if self.game_data.stats.get(stat_name, 0) < required_amount:
                    return  # 조건 불충족시 선택 불가

        # 선택지 효과 처리
        if "effects" in choice:
            self.process_choice_effects(choice["effects"])

        # 다음 씬으로 이동
        if "target_scene" in choice:
            target_scene = choice["target_scene"]
            self.current_scene_data = self.dialogue_scenes.get(target_scene)
            self.current_line = 0
        else:
            self.end_dialogue()

    def process_choice_effects(self, effects):
        # 스탯 변경
        if "stats" in effects:
            for stat_name, amount in effects["stats"].items():
                self.game_data.stats[stat_name] = self.game_data.stats.get(stat_name, 0) + amount

        # 호감도 변경
        if "affection" in effects:
            for character, amount in effects["affection"].items():
                self.game_data.affection[character] = self.game_data.affection.get(character, 0) + amount

    def end_dialogue(self):
        self.current_scene_data = None
        self.current_line = 0
        self.game_state = GameState.MAP

    def move_player(self, dx, dy):
        new_x = self.player_x + dx
        new_y = self.player_y + dy

        # 맵 경계 체크
        if 0 <= new_x < self.map_data["width"] and 0 <= new_y < self.map_data["height"]:
            self.player_x = new_x
            self.player_y = new_y

    def interact(self):
        # 구조물과 상호작용
        for structure in self.map_data["structures"]:
            if structure["x"] == self.player_x and structure["y"] == self.player_y:
                self.interact_with_structure(structure)
                return

        # 캐릭터와 상호작용
        for character in self.map_data["characters"]:
            if character["x"] == self.player_x and character["y"] == self.player_y:
                self.interact_with_character(character)
                return

    def interact_with_structure(self, structure):
        # 스탯 증가
        if "stats" in structure:
            for stat_name, amount in structure["stats"].items():
                self.game_data.stats[stat_name] = self.game_data.stats.get(stat_name, 0) + amount

        self.consume_action()

    def interact_with_character(self, character):
        # 대화 선택 (일상 or 메인)
        dialogue_file = self.choose_dialogue_for_character(character)
        self.start_dialogue(dialogue_file)
        self.consume_action()

    def choose_dialogue_for_character(self, character):
        # 메인 대화 조건 확인 - to be implemented
        # 기본적으로 일상 대화 반환
        return character["daily"]

    def consume_action(self):
        self.game_data.actions_today += 1

        if self.game_data.actions_today >= ACTIONS_PER_DAY:
            self.end_day()

    def end_day(self):
        self.game_data.day += 1
        self.game_data.actions_today = 0

        # 하루 종료 대화 시작
        self.start_dialogue("end_of_day.json")

    def render(self):
        if self.game_state == GameState.TITLE_SCREEN:
            self.render_title_screen()
        elif self.game_state == GameState.VISUAL_NOVEL:
            self.render_dialogue()
        elif self.game_state == GameState.MAP:
            self.render_map()

        pygame.display.flip()

    def render_title_screen(self):
        self.screen.fill(BLACK)

        # 타이틀
        title_text = self.large_font.render("게임 타이틀", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title_text, title_rect)

        # 메뉴 옵션
        options = ["새 게임", "불러오기", "게임 종료"]
        for i, option in enumerate(options):
            color = GREEN if i == self.title_selected else WHITE
            option_text = self.font.render(option, True, color)
            option_rect = option_text.get_rect(center=(SCREEN_WIDTH // 2, 350 + i * 60))
            self.screen.blit(option_text, option_rect)

    def render_dialogue(self):
        self.screen.fill(BLACK)

        if not self.current_scene_data or "lines" not in self.current_scene_data:
            return

        lines = self.current_scene_data["lines"]
        if self.current_line >= len(lines):
            return

        current_line_data = lines[self.current_line]

        # 배경 렌더링 - to be implemented

        # 대화창
        dialogue_box = pygame.Rect(50, SCREEN_HEIGHT - 200, SCREEN_WIDTH - 100, 150)
        pygame.draw.rect(self.screen, (50, 50, 50), dialogue_box)
        pygame.draw.rect(self.screen, WHITE, dialogue_box, 3)

        # 발화자 이름
        speaker = current_line_data.get("speaker", "")
        speaker_text = self.font.render(f"{speaker}:", True, WHITE)
        self.screen.blit(speaker_text, (70, SCREEN_HEIGHT - 190))

        # 대화 내용
        text = current_line_data.get("text", "")
        text_lines = self.wrap_text(text, dialogue_box.width - 40)
        for i, line in enumerate(text_lines):
            text_surface = self.font.render(line, True, WHITE)
            self.screen.blit(text_surface, (70, SCREEN_HEIGHT - 150 + i * 30))

        # 선택지 렌더링
        if "choices" in self.current_scene_data:
            self.render_choices()
        else:
            # 진행 안내
            continue_text = self.small_font.render("ENTER: 계속", True, LIGHT_GRAY)
            self.screen.blit(continue_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 30))

    def render_choices(self):
        if not self.current_scene_data or "choices" not in self.current_scene_data:
            return

        choices = self.current_scene_data["choices"]
        start_y = SCREEN_HEIGHT - 350

        for i, choice in enumerate(choices):
            # 선택 가능 여부 확인
            can_select = True
            if "required_stats" in choice:
                for stat_name, required_amount in choice["required_stats"].items():
                    if self.game_data.stats.get(stat_name, 0) < required_amount:
                        can_select = False
                        break

            color = WHITE if can_select else GRAY
            choice_text = f"{i + 1}. {choice['text']}"

            # 필요 스탯 표시
            if not can_select and "required_stats" in choice:
                req_stats = []
                for stat, amount in choice["required_stats"].items():
                    req_stats.append(f"{stat}:{amount}")
                choice_text += f" (필요: {', '.join(req_stats)})"

            choice_surface = self.font.render(choice_text, True, color)
            self.screen.blit(choice_surface, (100, start_y + i * 40))

    def wrap_text(self, text, max_width):
        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            test_surface = self.font.render(test_line, True, WHITE)

            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "

        if current_line:
            lines.append(current_line.strip())

        return lines

    def render_map(self):
        self.screen.fill(GREEN)

        # 간단한 맵 렌더링 - to be implemented

        # 플레이어 렌더링
        player_rect = pygame.Rect(
            self.player_x * TILE_SIZE,
            self.player_y * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE
        )
        pygame.draw.rect(self.screen, BLUE, player_rect)

        # UI 렌더링
        self.render_ui()

    def render_ui(self):
        ui_texts = [
            f"Day: {self.game_data.day}",
            f"Actions: {self.game_data.actions_today}/{ACTIONS_PER_DAY}",
            f"art: {self.game_data.stats['art']}",
            f"literature: {self.game_data.stats['literature']}",
            f"physical: {self.game_data.stats['physical']}",
            f"luck: {self.game_data.stats['luck']}",
            f"sense: {self.game_data.stats['sense']}"
        ]

        for i, text in enumerate(ui_texts):
            text_surface = self.small_font.render(text, True, WHITE)
            self.screen.blit(text_surface, (10, 10 + i * 25))

    def run(self):
        while self.running:
            self.handle_events()
            self.render()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()