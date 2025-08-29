import pygame
import sys
from pygame.locals import *


width = 1080
height = 720
white = (255, 255, 255)
black = (0, 0, 0)
fps = 60

pygame.init()

pygame.display.set_caption("noname")
screen = pygame.display.set_mode((width, height), 0, 32)  # 메인 디스플레이를 설정한다
clock = pygame.time.Clock()

gulimfont = pygame.font.SysFont("굴림", 70)  # 서체 설정

#import images
menuBtn = pygame.image.load("assets/menu.png")
menuBtn = pygame.transform.scale(menuBtn, (50, 50))
bg = pygame.image.load("assets/bg.jpg")
bg = pygame.transform.scale(bg, (width, height))


while True:
    for event in pygame.event.get():
        if event.type == QUIT:  # event의 type이 QUIT에 해당할 경우
            pygame.quit()  # pygame을 종료한다
            sys.exit()  # 창을 닫는다
    screen.fill(white)  # displaysurf를 하얀색으로 채운다
    screen.blit(bg, (0,0))
    screen.blit(menuBtn, (width-60,0))
    pygame.display.update()
    clock.tick(fps)