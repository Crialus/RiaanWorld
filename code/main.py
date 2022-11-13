import pygame
import sys
import os
from settings import *
from level import Level
from overworld import Overworld
from ui import UI

class Game:
    def __init__(self):
        # Game Atributes
        self.max_level = 5
        self.max_health = 100
        self.cur_health = 100
        self.coins = 0

        # UI
        self.ui = UI(screen)
        self.level_bg = pygame.mixer.Sound('../resources/audio/level_music.wav')
        self.overworld_bg = pygame.mixer.Sound('../resources/audio/overworld_music.wav')

        # Overworld Creation
        self.overworld = Overworld(0, self.max_level, screen, self.create_level)
        self.status = 'overworld'
        self.level_bg.stop()
        self.overworld_bg.play(loops = -1)

    def create_level(self, current_level):
        self.level = Level(current_level, screen, self.create_overworld, self.change_coins, self.change_health)
        self.status = 'level'
        self.overworld_bg.stop()
        self.level_bg.play(loops = -1)
    
    def create_overworld(self, current_level, new_max_level):
        if new_max_level > self.max_level:
            self.max_level = new_max_level
        self.overworld = Overworld(current_level, self.max_level, screen, self.create_level)
        self.status = 'overworld'
        self.level_bg.stop()
        self.overworld_bg.play(loops = -1)

    def change_coins(self, amount):
        self.coins += amount

    def change_health(self, amount):
        self.cur_health -= amount

    def check_game_over(self):
        if self.cur_health <=0:
            self.cur_health = 100
            self.coins = 0
            self.overworld = Overworld(0, self.max_level, screen, self.create_level)
            self.status = 'overworld'
            self.level_bg.stop()
            self.overworld_bg.play(loops = -1)

    def run(self):
        if self.status == 'overworld':
            self.overworld.run()
        elif self.status == 'level':
            self.level.run()
            self.ui.show_health(self.cur_health, self.max_health)
            self.ui.show_coins(self.coins)
            self.check_game_over()

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((screen_width, screen_height))
clock = pygame.time.Clock()
game = Game()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()       
    game.run()
    
    pygame.display.update()
    clock.tick(60)
