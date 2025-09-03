import pygame
#display
width = 1080
height = 720
fps = 60

#font
def get_font(size, style: str = "default" ):
    if style == "default":
        return pygame.font.Font("assets/fonts/NanumGothic.ttf", size)
    return pygame.font.Font(f"assets/fonts/NanumGothic{style}.ttf", size)
font_default = pygame.font.Font("assets/fonts/NanumGothic.ttf", 20)
#colors
