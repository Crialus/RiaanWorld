import pygame
from tiles import Tile, StaticTile, Crate, Coin, Palm
from settings import tile_size, screen_width, screen_height
from player import Player
from particles import ParticleEffect
from support import import_csv_layout, import_cut_graphics
from random import randint
from enemy import Enemy
from decoration import Sky, Water, Clouds
from game_data import levels

class Level:
    def __init__(self, current_level, surface, create_overworld, change_coins, change_health):
        # Level Setup
        self.display_surface = surface
        self.world_shift = 0
        self.current_x = 0

        # Audio
        self.coin_sound = pygame.mixer.Sound('../resources/audio/effects/coin.wav')
        self.coin_sound.set_volume(0.5)
        self.stomp_sound = pygame.mixer.Sound('../resources/audio/effects/stomp.wav')
        self.stomp_sound.set_volume(0.8)

        # overworld connection
        self.create_overworld = create_overworld
        self.current_level = current_level
        level_data = levels[self.current_level]
        self.new_max_level = level_data['unlock']

        # player setup
        player_layout = import_csv_layout(level_data['player'])
        self.player = pygame.sprite.GroupSingle()
        self.goal = pygame.sprite.GroupSingle()
        self.player_setup(player_layout, change_health)
        self.dust_sprite = pygame.sprite.GroupSingle()
        self.player_on_ground = False
        self.explosion_sprite = pygame.sprite.Group()

        # UI elements
        self.change_coins = change_coins
        self.change_health = change_health
        
        # terrain data
        terrain_layout = import_csv_layout(level_data['terrain'])
        self.terrain_sprites = self.create_tile_group(terrain_layout, 'terrain')

        # grass data
        grass_layout = import_csv_layout(level_data['grass'])
        self.grass_sprites = self.create_tile_group(grass_layout, 'grass')

        # crates data
        crate_layout = import_csv_layout(level_data['crates'])
        self.crate_sprites = self.create_tile_group(crate_layout, 'crates')

        # coins data
        coins_layout = import_csv_layout(level_data['coins'])
        self.coins_sprites = self.create_tile_group(coins_layout, 'coins')

        # foreground palms
        fg_palm_layout = import_csv_layout(level_data['fg_palms'])
        self.fg_palm_sprites = self.create_tile_group(fg_palm_layout, 'fg_palms')

        # background palms
        bg_palm_layout = import_csv_layout(level_data['bg_palms'])
        self.bg_palm_sprites = self.create_tile_group(bg_palm_layout, 'bg_palms')

        # enemy
        enemy_layout = import_csv_layout(level_data['enemies'])
        self.enemy_sprites = self.create_tile_group(enemy_layout, 'enemies')

        # constraints
        constraint_layout = import_csv_layout(level_data['constraints'])
        self.constraint_sprites = self.create_tile_group(constraint_layout, 'constraint')

        # decoration
        self.sky = Sky(8)
        level_width = len(terrain_layout[0]) * tile_size
        self.water = Water(screen_height - 20, level_width)
        self.clouds = Clouds(400, level_width, 30)

    def create_tile_group(self, layout, type):
        sprite_group = pygame.sprite.Group()
        for row_index, row in enumerate(layout):
            for col_index, col in enumerate(row):
                if col != '-1':
                    x = col_index * tile_size
                    y = row_index * tile_size
                
                    if type == 'terrain':
                        terrain_tile_list = import_cut_graphics('../resources/graphics/terrain/terrain_tiles.png')
                        tile_surface = terrain_tile_list[int(col)]
                        sprite = StaticTile(tile_size, x, y, tile_surface)
                    if type == 'grass':
                        grass_tile_list = import_cut_graphics('../resources/graphics/decoration/grass/grass.png')
                        tile_surface = grass_tile_list[int(col)]
                        sprite = StaticTile(tile_size, x, y, tile_surface)
                    if type == 'crates':
                        sprite = Crate(tile_size, x, y)
                    if type == 'coins':
                        if col == '0': sprite = Coin(tile_size, x, y, '../resources/graphics/coins/gold', 5)
                        if col == '1': sprite = Coin(tile_size, x, y, '../resources/graphics/coins/silver', 1)
                    if type == 'fg_palms':
                        if col == '0': sprite = Palm(tile_size, x, y, '../resources/graphics/terrain/palm_small', randint(30, 45))
                        if col == '1': sprite = Palm(tile_size, x, y, '../resources/graphics/terrain/palm_large', randint(15, 30))
                    if type == 'bg_palms':
                        sprite = Palm(tile_size, x, y, '../resources/graphics/terrain/palm_bg', randint(25, 33))
                    if type == 'enemies':
                        sprite = Enemy(tile_size, x, y, 5)
                    if type == 'constraint':
                        sprite = Tile(tile_size, x, y)

                    sprite_group.add(sprite)
        return sprite_group

    def player_setup(self, layout, change_health):
        for row_index, row in enumerate(layout):
            for col_index, col in enumerate(row):
                x = col_index * tile_size
                y = row_index * tile_size
                if col == '0':
                   sprite = Player((x, y), self.display_surface, self.create_jump_particles, change_health)
                   self.player.add(sprite)
                if col == '1':
                    hat_surface = pygame.image.load('../resources/graphics/character/hat.png').convert_alpha()
                    sprite = StaticTile(tile_size, x, y, hat_surface)
                    self.goal.add(sprite)

    def enemy_reverse(self):
        for enemy in self.enemy_sprites.sprites():
            if pygame.sprite.spritecollide(enemy, self.constraint_sprites, False):
                enemy.reverse()

    def create_jump_particles(self, pos):
        jump_particle_sprite = ParticleEffect(pos, 'jump')
        self.dust_sprite.add(jump_particle_sprite)
        if self.player.sprite.facing_right:
            pos -= pygame.math.Vector2(10, 5)
        else:
            pos += pygame.math.Vector2(10, -5)

    def get_player_on_ground(self):
        if self.player.sprite.on_ground:
            self.player_on_ground = True
        else:
            self.player_on_ground = False

    def create_landing_particles(self):
        if not self.player_on_ground and self.player.sprite.on_ground and not self.dust_sprite.sprites():
            if self.player.sprite.facing_right:
                offset = pygame.math.Vector2(10, 15)
            else:
                offset = pygame.math.Vector2(-10, 15)
            fall_dust = ParticleEffect(self.player.sprite.rect.midbottom - offset, 'land')
            self.dust_sprite.add(fall_dust)

    def scroll_x(self):
        player = self.player.sprite
        player_x = player.rect.centerx
        direction_x = player.direction.x

        if player_x < screen_width / 4 and direction_x < 0:
            self.world_shift = 8
            player.speed = 0
        elif player_x > screen_width - (screen_width / 4) and direction_x > 0:
            self.world_shift = -8
            player.speed = 0
        else:
            self.world_shift = 0
            player.speed = 8

    def horizontal_movement_collision(self):
        player = self.player.sprite
        player.collision_rect.x += player.direction.x * player.speed
        collidable_sprites = self.terrain_sprites.sprites() + self.crate_sprites.sprites() + self.fg_palm_sprites.sprites()
        for sprite in collidable_sprites:
            if sprite.rect.colliderect(player.collision_rect):
                if player.direction.x < 0:
                    player.collision_rect.left = sprite.rect.right
                    player.on_left = True
                elif player.direction.x > 0:
                    player.collision_rect.right = sprite.rect.left
                    player.on_right = True

    def vertical_movement_collision(self):
        player = self.player.sprite
        player.apply_gravity()
        collidable_sprites = self.terrain_sprites.sprites() + self.crate_sprites.sprites() + self.fg_palm_sprites.sprites()
        for sprite in collidable_sprites:
            if sprite.rect.colliderect(player.collision_rect):
                if player.direction.y > 0:
                    player.collision_rect.bottom = sprite.rect.top
                    player.direction.y = 0
                    player.on_ground = True
                elif player.direction.y < 0:
                    player.collision_rect.top = sprite.rect.bottom
                    player.direction.y = 0
                    player.on_ceiling = True

        if player.on_ground and (player.direction.y < 0 or player.direction.y > 1):
            player.on_ground = False
        if player.on_ceiling and player.direction.y > 0:
            player.on_ceiling = False

    def check_death(self):
        if self.player.sprite.rect.top > screen_height:
            self.player.sprite.get_damage(100)

    def check_win(self):
        if pygame.sprite.spritecollide(self.player.sprite, self.goal, False):
            self.create_overworld(self.current_level, self.new_max_level)

    def check_coin_collisions(self):
        collided_coins = pygame.sprite.spritecollide(self.player.sprite, self.coins_sprites, True)
        if collided_coins:
            self.coin_sound.play()
            for coin in collided_coins:
                self.change_coins(coin.value)
                
    def check_enemy_collisions(self):
        collided_enemies = pygame.sprite.spritecollide(self.player.sprite, self.enemy_sprites, False)
        if collided_enemies:
            self.stomp_sound.play()
            for enemy in collided_enemies:
                enemy_center = enemy.rect.centery
                enemy_top = enemy.rect.top
                player_bottom = self.player.sprite.rect.bottom
                if enemy_top < player_bottom < enemy_center and self.player.sprite.direction.y >= 0:
                    self.player.sprite.direction.y = -15
                    explosion = ParticleEffect((enemy.rect.center), 'explosion')
                    self.explosion_sprite.add(explosion)
                    enemy.kill()
                else:
                    self.player.sprite.get_damage(enemy.value)

    def run(self):

        # level tiles
        self.sky.draw(self.display_surface)
        self.clouds.draw(self.display_surface, self.world_shift)

        self.bg_palm_sprites.update(self.world_shift)
        self.bg_palm_sprites.draw(self.display_surface)

        # dust particles
        self.dust_sprite.update(self.world_shift)
        self.dust_sprite.draw(self.display_surface)

        self.terrain_sprites.update(self.world_shift)
        self.terrain_sprites.draw(self.display_surface)
        
        self.enemy_sprites.update(self.world_shift)
        self.enemy_sprites.draw(self.display_surface)
        self.constraint_sprites.update(self.world_shift)
        self.enemy_reverse()
        self.explosion_sprite.update(self.world_shift)
        self.explosion_sprite.draw(self.display_surface)

        self.crate_sprites.update(self.world_shift)
        self.crate_sprites.draw(self.display_surface)

        self.grass_sprites.update(self.world_shift)
        self.grass_sprites.draw(self.display_surface)

        self.coins_sprites.update(self.world_shift)
        self.coins_sprites.draw(self.display_surface)

        self.fg_palm_sprites.update(self.world_shift)
        self.fg_palm_sprites.draw(self.display_surface)

        self.goal.update(self.world_shift)
        self.goal.draw(self.display_surface)
        self.player.update()
        self.player.draw(self.display_surface)
        

        self.water.draw(self.display_surface, self.world_shift)

        self.scroll_x()

        # player
        self.player.update()
        self.horizontal_movement_collision()
        self.get_player_on_ground()
        self.vertical_movement_collision()
        self.create_landing_particles()
        self.player.draw(self.display_surface)

        self.check_death()
        self.check_win()
        self.check_coin_collisions()
        self.check_enemy_collisions()
