import json
import numpy as np
import pygame as pg



class textBox():
    def __init__(self, text: str = "", name: str = "") -> None:
        self.text = text
        self.name = name

    def draw(self, screen):
        pass

    def update(self, screen):
        pass

    def add_text(self, text: str):
        self.text += text
        return self.text

    def clear(self):
        self.text = ""

    def set_name(self, name: str):
        self.name = name


class character():
    def __init__(self, name: str, img: pg.image):
        self.name = name
        self.img = img