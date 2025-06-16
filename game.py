import pygame
import sys
import os
import math
import random

pygame.mixer.init()
pygame.font.init()
font = pygame.font.SysFont('Arial', 24)
title_font = pygame.font.SysFont('Arial', 48)

hit_sound = pygame.mixer.Sound(os.path.join('sounds', 'hit.wav'))
hit_sound.set_volume(0.1)
walk_sound = pygame.mixer.Sound(os.path.join('sounds', 'walk.wav'))
walk_sound.set_volume(0.3)
attack_sound = pygame.mixer.Sound(os.path.join('sounds', 'attack.wav'))
attack_sound.set_volume(1)
heavy_attack_sound = pygame.mixer.Sound(os.path.join('sounds', 'heavy_attack.wav'))
heavy_attack_sound.set_volume(0.6)
dash_sound = pygame.mixer.Sound(os.path.join('sounds', 'dash.wav'))
dash_sound.set_volume(0.6)
parry_sound = pygame.mixer.Sound(os.path.join('sounds', 'parry.wav'))
parry_sound.set_volume(0.6)


def draw_hud():
    pygame.draw.rect(world, (50, 50, 50), (0, 0, worldx, 40))

    # player1
    player_hp_text = font.render(f"HP: {player.health}", True, (255, 255, 255))
    player_parry_cd = max(0, player.parry_cooldown / fps)
    player_parry_text = font.render(f"Parry CD: {player_parry_cd:.1f}s", True, (255, 255, 255))
    player_stun = max(0, player.stun_frames / fps)
    player_stun_text = font.render(f"Stun: {player_stun:.1f}s", True,
                                   (255, 0, 0) if player.stun_frames > 0 else (255, 255, 255))
    player_dash_cd = max(0, player.dash_cooldown / fps)
    player_dash_text = font.render(f"Dash CD: {player_dash_cd:.1f}s", True, (255, 255, 255))

    world.blit(player_hp_text, (10, 10))
    world.blit(player_parry_text, (150, 10))
    world.blit(player_stun_text, (300, 10))
    world.blit(player_dash_text, (450, 10))

    # bot
    if game_mode == "PVE" and len(enemy_list) > 0:
        enemy = next(iter(enemy_list))  # Берем первого врага
        enemy_hp_text = font.render(f"Enemy HP: {enemy.health}", True, (255, 255, 255))
        world.blit(enemy_hp_text, (worldx - 200, 10))

    # player2
    if game_mode == "PVP" and player2 is not None:
        player2_hp_text = font.render(f"P2 HP: {player2.health}", True, (255, 255, 255))
        player2_parry_cd = max(0, player2.parry_cooldown / fps)
        player2_parry_text = font.render(f"P2 Parry CD: {player2_parry_cd:.1f}s", True, (255, 255, 255))
        player2_stun = max(0, player2.stun_frames / fps)
        player2_stun_text = font.render(f"P2 Stun: {player2_stun:.1f}s", True,
                                        (255, 0, 0) if player2.stun_frames > 0 else (255, 255, 255))
        player2_dash_cd = max(0, player2.dash_cooldown / fps)
        player2_dash_text = font.render(f"P2 Dash CD: {player2_dash_cd:.1f}s", True, (255, 255, 255))

        world.blit(player2_hp_text, (worldx - 250, 10))
        world.blit(player2_parry_text, (worldx - 450, 10))
        world.blit(player2_stun_text, (worldx - 650, 10))
        world.blit(player2_dash_text, (worldx - 850, 10))


'''
Variables
'''

worldx = 1920
worldy = 1200
fps = 60
ani = 10
main = True
ALPHA = (0, 255, 0)
MENU = 0
MODE_SELECT = 1
PLAYING = 2
GAME_OVER = 3
PAUSED = 4
game_state = MENU
game_mode = "PVE"
MAP_SELECT = 5
current_map = 1

'''
Objects
'''

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=10)

        text_surface = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False


class Player(pygame.sprite.Sprite):
    def __init__(self, is_player2=False):
        pygame.sprite.Sprite.__init__(self)
        self.movex = 0
        self.movey = 0
        self.frame = 0
        self.health = 10
        self.images = []
        self.attack_images = []
        self.facing_right = True if not is_player2 else False
        self.is_attacking = False
        self.attack_cooldown = 0
        self.parry_cooldown = 0
        self.is_parrying = False
        self.parry_frames = 50
        self.parry_window = 10
        self.parry_range = 120
        self.heavy_attack_images = []
        self.is_heavy_attacking = False
        self.heavy_attack_cooldown = 0
        self.heavy_attack_damage = 2
        self.heavy_attack_range = 120
        self.is_player2 = is_player2
        self.stun_frames = 20
        self.attack_startup = 10
        self.attack_active_frames = 10
        self.heavy_attack_startup = 15
        self.heavy_attack_active_frames = 25
        self.has_hit = False
        self.has_heavy_hit = False
        self.is_in_attack_animation = False
        self.is_dashing = False
        self.dash_frames = 0
        self.dash_cooldown = 0
        self.dash_speed = 30
        self.dash_duration = 10
        self.dash_distance = 150
        self.dash_cooldown_time = 60
        self.keys_pressed = {'left': False, 'right': False}
        self.walk_sound_timer = 0
        self.walk_sound_delay = 15
        self.dash_images = []
        self.parry_images = []
        self.player = 1

        if is_player2:
            self.player = 2

        for i in range(1, 3):
            img = pygame.image.load(os.path.join(f'images/player{self.player}', f'dash{i}.png')).convert()
            img.set_colorkey(ALPHA)
            self.dash_images.append(img)

        for i in range(1, 3):
            img = pygame.image.load(os.path.join(f'images/player{self.player}', f'parry{i}.png')).convert()
            img.set_colorkey(ALPHA)
            self.parry_images.append(img)

        for i in range(1, 5):
            img = pygame.image.load(os.path.join(f'images/player{self.player}', 'hero' + str(i) + '.png')).convert()
            img.convert_alpha()
            img.set_colorkey(ALPHA)
            self.images.append(img)

        for i in range(1, 5):
            img = pygame.image.load(os.path.join(f'images/player{self.player}', 'attack_2' + str(i) + '.png')).convert()
            img.convert_alpha()
            img.set_colorkey(ALPHA)
            self.attack_images.append(img)

        for i in range(1, 7):
            img = pygame.image.load(os.path.join(f'images/player{self.player}', 'attack_1' + str(i) + '.png')).convert()
            img.convert_alpha()
            img.set_colorkey(ALPHA)
            self.heavy_attack_images.append(img)

        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.gravity = 0.5
        self.jump_power = -15
        self.is_on_ground = False
        self.attack_range = 100
        self.attack_damage = 1

    # передвижение
    def control(self, x, y):
        if self.stun_frames > 0 or self.is_dashing:
            return
        self.movex += x
        self.movey += y

        if x > 0:
            self.keys_pressed['right'] = True
        elif x < 0:
            self.keys_pressed['left'] = True

    def jump(self):
        if self.stun_frames > 0 or self.is_dashing:
            return
        if self.is_on_ground:
            self.movey = self.jump_power
            self.is_on_ground = False

    # рывок
    def dash(self):
        if self.stun_frames > 0 or self.dash_cooldown > 0 or self.is_dashing:
            return False

        self.pre_dash_movex = self.movex
        self.is_dashing = True
        self.dash_frames = self.dash_duration
        self.dash_cooldown = self.dash_cooldown_time
        self.dash_frame = 0
        dash_sound.play()

        if self.facing_right:
            self.movex = self.dash_speed
        else:
            self.movex = -self.dash_speed

        return True

    def attack(self):
        if self.stun_frames > 0 or self.attack_cooldown != 0 or self.is_dashing:
            return

        self.is_attacking = True
        self.is_in_attack_animation = True
        self.attack_cooldown = 30
        self.attack_frame = 0
        self.has_hit = False
        self.attack_active = False
        attack_sound.play()

    def heavy_attack(self):
        if self.stun_frames > 0 or self.heavy_attack_cooldown != 0 or self.is_attacking or self.is_dashing:
            return

        self.is_heavy_attacking = True
        self.is_in_attack_animation = True
        self.heavy_attack_cooldown = 80
        self.heavy_attack_frame = 0
        self.has_heavy_hit = False
        self.heavy_attack_active = False
        heavy_attack_sound.play()

    def parry(self):
        if self.stun_frames > 0 or self.parry_cooldown != 0 or self.is_dashing:
            return False

        self.is_parrying = True
        self.parry_frames = self.parry_window
        self.parry_cooldown = 30
        self.parry_frame = 0
        self.movex = 0
        self.movey = 0

        if game_mode == "PVE":
            targets = enemy_list
        else:
            targets = [player2] if self != player2 else [player]

        parry_success = False
        for target in targets:
            if target.is_in_attack_animation and not target.is_heavy_attacking:
                parry_rect = pygame.Rect(0, 0, self.parry_range, self.rect.height)
                if self.facing_right:
                    parry_rect.left = self.rect.right
                else:
                    parry_rect.right = self.rect.left
                parry_rect.top = self.rect.top

                if parry_rect.colliderect(target.rect):
                    target.stun(60)
                    target.is_attacking = False
                    target.is_heavy_attacking = False
                    target.is_in_attack_animation = False
                    target.attack_cooldown = 60
                    parry_success = True
                    parry_sound.play()

        return parry_success

    # получение урона
    def take_damage(self, damage):
        if not self.is_parrying or damage > 1:
            self.health -= damage
            hit_sound.play()
            if self.health <= 0:
                global game_state
                game_state = GAME_OVER

    def stun(self, frames):
        self.stun_frames = frames
        self.movex = 0
        self.movey = 0

    def update(self):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.heavy_attack_cooldown > 0:
            self.heavy_attack_cooldown -= 1

        if self.parry_cooldown > 0:
            self.parry_cooldown -= 1

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        if self.is_parrying:
            self.parry_frames -= 1
            if self.parry_frames <= 0:
                self.is_parrying = False

        if self.stun_frames > 0:
            self.stun_frames -= 1
            return

        if self.is_dashing:
            self.dash_frames -= 1
            if self.dash_frames <= 0:
                self.is_dashing = False
                self.movex = 0

        if self.is_attacking:
            self.attack_frame += 1

            if self.attack_frame >= self.attack_startup and not self.attack_active:
                self.attack_active = True
                self.has_hit = False

            if self.attack_active and not self.has_hit:
                self.has_hit = True

                if game_mode == "PVE":
                    targets = enemy_list
                else:
                    targets = [player2] if self != player2 else [player]

                for target in targets:
                    attack_rect = pygame.Rect(0, 0, self.attack_range, self.rect.height)
                    if self.facing_right:
                        attack_rect.left = self.rect.right
                    else:
                        attack_rect.right = self.rect.left
                    attack_rect.top = self.rect.top

                    if attack_rect.colliderect(target.rect):
                        target.take_damage(self.attack_damage)

            if self.attack_frame >= self.attack_startup + self.attack_active_frames:
                self.is_attacking = False
                self.is_in_attack_animation = False
                self.attack_active = False

            attack_progress = min(self.attack_frame / (self.attack_startup + self.attack_active_frames), 1)
            attack_frame = int(attack_progress * 3)
            if not self.facing_right:
                self.image = pygame.transform.flip(self.attack_images[attack_frame], True, False)
            else:
                self.image = self.attack_images[attack_frame]

        elif self.is_heavy_attacking:
            self.heavy_attack_frame += 1

            if self.heavy_attack_frame >= self.heavy_attack_startup and not self.heavy_attack_active:
                self.heavy_attack_active = True
                self.has_heavy_hit = False

            if self.heavy_attack_active and not self.has_heavy_hit:
                self.has_heavy_hit = True

                if game_mode == "PVE":
                    targets = enemy_list
                else:
                    targets = [player2] if self != player2 else [player]

                for target in targets:
                    attack_rect = pygame.Rect(0, 0, self.heavy_attack_range, self.rect.height)
                    if self.facing_right:
                        attack_rect.left = self.rect.right
                    else:
                        attack_rect.right = self.rect.left
                    attack_rect.top = self.rect.top

                    if attack_rect.colliderect(target.rect):
                        target.take_damage(self.heavy_attack_damage)

            if self.heavy_attack_frame >= self.heavy_attack_startup + self.heavy_attack_active_frames:
                self.is_heavy_attacking = False
                self.is_in_attack_animation = False
                self.heavy_attack_active = False

            attack_progress = min(
                self.heavy_attack_frame / (self.heavy_attack_startup + self.heavy_attack_active_frames), 1)
            attack_frame = int(attack_progress * (len(self.heavy_attack_images) - 1))

            if not self.facing_right:
                self.image = pygame.transform.flip(self.heavy_attack_images[attack_frame], True, False)
            else:
                self.image = self.heavy_attack_images[attack_frame]

        elif self.movex != 0 and not self.is_dashing:
            self.frame += 1
            if self.frame >= len(self.images) * ani:
                self.frame = 0
            if self.movex < 0:
                self.image = pygame.transform.flip(self.images[self.frame // ani], True, False)
            else:
                self.image = self.images[self.frame // ani]
        else:
            if self.facing_right:
                self.image = self.images[0]
            else:
                self.image = pygame.transform.flip(self.images[0], True, False)

        self.rect.x += self.movex

        if self.movex > 0 and not self.is_dashing:
            self.facing_right = True
        elif self.movex < 0 and not self.is_dashing:
            self.facing_right = False

        hit_list = pygame.sprite.spritecollide(self, ground_list, False)
        hit_list.extend(pygame.sprite.spritecollide(self, plat_list, False))
        for hit in hit_list:
            if self.movex > 0:
                self.rect.right = hit.rect.left
            elif self.movex < 0:
                self.rect.left = hit.rect.right

        self.movey += self.gravity
        self.rect.y += self.movey

        self.is_on_ground = False
        hit_list = pygame.sprite.spritecollide(self, ground_list, False)
        hit_list.extend(pygame.sprite.spritecollide(self, plat_list, False))
        for hit in hit_list:
            if self.movey > 0:
                self.rect.bottom = hit.rect.top
                self.movey = 0
                self.is_on_ground = True
            elif self.movey < 0:
                self.rect.top = hit.rect.bottom
                self.movey = 0
        if self.is_dashing:
            self.dash_frames -= 1
            if self.dash_frames <= 0:
                self.is_dashing = False
                if hasattr(self, 'pre_dash_movex'):
                    if (self.pre_dash_movex > 0 and self.keys_pressed['right']) or \
                            (self.pre_dash_movex < 0 and self.keys_pressed['left']):
                        self.movex = self.pre_dash_movex
                    else:
                        self.movex = 0
                    del self.pre_dash_movex
                else:
                    self.movex = 0
        if (
                self.movex != 0 or self.movey != 0) and self.is_on_ground and not self.is_attacking and not self.is_heavy_attacking and not self.is_dashing:
            self.walk_sound_timer += 1
            if self.walk_sound_timer >= self.walk_sound_delay:
                walk_sound.play()
                self.walk_sound_timer = 0
        else:
            self.walk_sound_timer = 0

        if self.is_dashing:
            self.dash_frame += 1
            dash_progress = min(self.dash_frame / self.dash_duration, 1)
            dash_frame = int(dash_progress * (len(self.dash_images) - 1))

            if not self.facing_right:
                self.image = pygame.transform.flip(self.dash_images[dash_frame], True, False)
            else:
                self.image = self.dash_images[dash_frame]

        elif self.is_parrying:
            self.parry_frame += 1
            parry_progress = min(self.parry_frame / self.parry_window, 1)
            parry_frame = int(parry_progress * (len(self.parry_images) - 1))

            if not self.facing_right:
                self.image = pygame.transform.flip(self.parry_images[parry_frame], True, False)
            else:
                self.image = self.parry_images[parry_frame]

    # проверка на падение
    def check_out_of_bounds(self):
        if self.rect.top > worldy:
            return True
        return False


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.is_alive = True
        self.images = []
        self.attack_images = []
        self.heavy_attack_images = []
        self.dash_images = []
        self.parry_images = []
        self.movex = 0
        self.movey = 0
        self.frame = 0
        self.health = 10
        self.facing_right = False
        self.is_attacking = False
        self.attack_cooldown = 0
        self.parry_cooldown = 0
        self.is_parrying = False
        self.parry_frames = 50
        self.parry_window = 10
        self.parry_range = 120
        self.is_heavy_attacking = False
        self.heavy_attack_cooldown = 0
        self.heavy_attack_damage = 2
        self.heavy_attack_range = 120
        self.stun_frames = 0
        self.attack_startup = 10
        self.attack_active_frames = 10
        self.heavy_attack_startup = 15
        self.heavy_attack_active_frames = 25
        self.has_hit = False
        self.has_heavy_hit = False
        self.is_in_attack_animation = False
        self.is_dashing = False
        self.dash_frames = 0
        self.dash_cooldown = 0
        self.dash_speed = 30
        self.dash_duration = 10
        self.dash_cooldown_time = 60
        self.decision_timer = 0
        self.decision_delay = 0
        self.aggression = 0.7
        self.player = 2

        for i in range(1, 3):
            img = pygame.image.load(os.path.join(f'images/player{self.player}', f'dash{i}.png')).convert()
            img.set_colorkey(ALPHA)
            self.dash_images.append(img)

        for i in range(1, 3):
            img = pygame.image.load(os.path.join(f'images/player{self.player}', f'parry{i}.png')).convert()
            img.set_colorkey(ALPHA)
            self.parry_images.append(img)

        for i in range(1, 5):
            img = pygame.image.load(os.path.join(f'images/player{self.player}', 'hero' + str(i) + '.png')).convert()
            img.convert_alpha()
            img.set_colorkey(ALPHA)
            self.images.append(img)

        for i in range(1, 5):
            img = pygame.image.load(os.path.join(f'images/player{self.player}', 'attack_2' + str(i) + '.png')).convert()
            img.convert_alpha()
            img.set_colorkey(ALPHA)
            self.attack_images.append(img)

        for i in range(1, 7):
            img = pygame.image.load(os.path.join(f'images/player{self.player}', 'attack_1' + str(i) + '.png')).convert()
            img.convert_alpha()
            img.set_colorkey(ALPHA)
            self.heavy_attack_images.append(img)

        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.gravity = 0.5
        self.jump_power = -15
        self.is_on_ground = False
        self.attack_range = 100
        self.attack_damage = 1
        self.platform_jump_threshold = 150

    # получение урона
    def take_damage(self, damage):
        if not self.is_parrying or damage > 1:
            self.health -= damage
            hit_sound.play()
            if self.health <= 0:
                self.is_alive = False
                self.kill()
                global game_state
                game_state = GAME_OVER

    def stun(self, frames):
        self.stun_frames = frames
        self.movex = 0
        self.movey = 0

    def jump(self):
        if self.stun_frames > 0 or self.is_dashing:
            return
        if self.is_on_ground:
            self.movey = self.jump_power
            self.is_on_ground = False

    # рывок
    def dash(self):
        if self.stun_frames > 0 or self.dash_cooldown > 0 or self.is_dashing:
            return False

        self.is_dashing = True
        self.dash_frames = self.dash_duration
        self.dash_cooldown = self.dash_cooldown_time
        self.dash_frame = 0
        dash_sound.play()

        if self.facing_right:
            self.movex = self.dash_speed
        else:
            self.movex = -self.dash_speed

        return True

    def attack(self):
        if self.stun_frames > 0 or self.attack_cooldown != 0 or self.is_dashing:
            return

        self.is_attacking = True
        self.is_in_attack_animation = True
        self.attack_cooldown = 40
        self.attack_frame = 0
        self.has_hit = False
        self.attack_active = False
        attack_sound.play()

    def heavy_attack(self):
        if self.stun_frames > 0 or self.heavy_attack_cooldown != 0 or self.is_attacking or self.is_dashing:
            return

        self.is_heavy_attacking = True
        self.is_in_attack_animation = True
        self.heavy_attack_cooldown = 90
        self.heavy_attack_frame = 0
        self.has_heavy_hit = False
        self.heavy_attack_active = False
        heavy_attack_sound.play()

    def parry(self):
        if self.stun_frames > 0 or self.parry_cooldown != 0 or self.is_dashing:
            return False

        self.is_parrying = True
        self.parry_frames = self.parry_window
        self.parry_cooldown = 30
        self.parry_frame = 0
        self.movex = 0
        self.movey = 0

        if player.is_in_attack_animation and not player.is_heavy_attacking:
            parry_rect = pygame.Rect(0, 0, self.parry_range, self.rect.height)
            if self.facing_right:
                parry_rect.left = self.rect.right
            else:
                parry_rect.right = self.rect.left
            parry_rect.top = self.rect.top

            if parry_rect.colliderect(player.rect):
                player.stun(60)
                player.is_attacking = False
                player.is_heavy_attacking = False
                player.is_in_attack_animation = False
                player.attack_cooldown = 60
                parry_sound.play()
                return True
        return False

    # решения бота
    def make_decision(self):
        if self.stun_frames > 0:
            return

        self.decision_timer += 1
        if self.decision_timer < self.decision_delay:
            return
        self.decision_timer = 0

        ground_ahead = self.check_ground_ahead()
        player_above = self.check_player_above()
        player_below = self.check_player_below()
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)

        self.facing_right = dx > 0

        if not ground_ahead and self.is_on_ground:
            if random.random() < 0.7:
                self.movex = -steps if self.facing_right else steps
            else:
                self.jump()
            return

        if player_above and self.is_on_ground:
            if random.random() < 0.8:
                self.jump()
                if abs(dx) < 200 and random.random() < 0.5:
                    self.dash()
            return

        if player_below and not ground_ahead:
            self.movex = 0
            if random.random() < 0.3:
                self.movex = steps if self.facing_right else -steps
            return

        if distance > 200:
            if dx > 0:
                self.movex = steps
            else:
                self.movex = -steps

            if distance > 6000 and self.dash_cooldown == 0:
                self.dash()

        elif 150 < distance <= 200:
            if random.random() < self.aggression:
                if self.heavy_attack_cooldown == 0 and random.random() < 0.4:
                    self.heavy_attack()
                elif self.attack_cooldown == 0:
                    self.attack()
            else:
                if player.is_in_attack_animation and self.parry_cooldown == 0:
                    self.parry()
                elif self.dash_cooldown == 0:
                    self.dash()

        else:
            if player.is_in_attack_animation and self.parry_cooldown == 0:
                self.parry()
            elif self.attack_cooldown == 0:
                self.attack()
            elif self.dash_cooldown == 0 and random.random() < 0.5:
                self.dash()

    # проверка на наличие платформы спереди
    def check_ground_ahead(self):
        check_distance = 50
        future_rect = pygame.Rect(
            self.rect.x + (check_distance if self.facing_right else -check_distance),
            self.rect.y + 10,
            self.rect.width,
            self.rect.height
        )

        for ground in ground_list:
            if future_rect.colliderect(ground.rect):
                return True

        for platform in plat_list:
            if future_rect.colliderect(platform.rect):
                return True
        return False

    # проверка на падение
    def check_out_of_bounds(self):
        if self.rect.top > worldy:
            return True
        return False

    # проверка выше ли игрок
    def check_player_above(self):
        return (abs(player.rect.centerx - self.rect.centerx) < 200 and
                player.rect.bottom < self.rect.top)

    # проверка ниже ли игрок
    def check_player_below(self):
        return (abs(player.rect.centerx - self.rect.centerx) < 200 and
                player.rect.top > self.rect.bottom)

    def update(self):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.heavy_attack_cooldown > 0:
            self.heavy_attack_cooldown -= 1

        if self.parry_cooldown > 0:
            self.parry_cooldown -= 1

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        if self.is_parrying:
            self.parry_frames -= 1
            if self.parry_frames <= 0:
                self.is_parrying = False

        if self.stun_frames > 0:
            self.stun_frames -= 1
            return

        self.make_decision()

        if self.is_dashing:
            self.dash_frames -= 1
            if self.dash_frames <= 0:
                self.is_dashing = False
                self.movex = 0

        if self.is_attacking:
            self.attack_frame += 1

            if self.attack_frame >= self.attack_startup and not self.attack_active:
                self.attack_active = True
                self.has_hit = False

            if self.attack_active and not self.has_hit:
                self.has_hit = True
                attack_rect = pygame.Rect(0, 0, self.attack_range, self.rect.height)
                if self.facing_right:
                    attack_rect.left = self.rect.right
                else:
                    attack_rect.right = self.rect.left
                attack_rect.top = self.rect.top

                if attack_rect.colliderect(player.rect):
                    player.take_damage(self.attack_damage)

            if self.attack_frame >= self.attack_startup + self.attack_active_frames:
                self.is_attacking = False
                self.is_in_attack_animation = False
                self.attack_active = False

            attack_progress = min(self.attack_frame / (self.attack_startup + self.attack_active_frames), 1)
            attack_frame = int(attack_progress * 3)
            if not self.facing_right:
                self.image = pygame.transform.flip(self.attack_images[attack_frame], True, False)
            else:
                self.image = self.attack_images[attack_frame]

        elif self.is_heavy_attacking:
            self.heavy_attack_frame += 1

            if self.heavy_attack_frame >= self.heavy_attack_startup and not self.heavy_attack_active:
                self.heavy_attack_active = True
                self.has_heavy_hit = False

            if self.heavy_attack_active and not self.has_heavy_hit:
                self.has_heavy_hit = True
                attack_rect = pygame.Rect(0, 0, self.heavy_attack_range, self.rect.height)
                if self.facing_right:
                    attack_rect.left = self.rect.right
                else:
                    attack_rect.right = self.rect.left
                attack_rect.top = self.rect.top

                if attack_rect.colliderect(player.rect):
                    player.take_damage(self.heavy_attack_damage)

            if self.heavy_attack_frame >= self.heavy_attack_startup + self.heavy_attack_active_frames:
                self.is_heavy_attacking = False
                self.is_in_attack_animation = False
                self.heavy_attack_active = False

            attack_progress = min(
                self.heavy_attack_frame / (self.heavy_attack_startup + self.heavy_attack_active_frames), 1)
            attack_frame = int(attack_progress * (len(self.heavy_attack_images) - 1))
            if not self.facing_right:
                self.image = pygame.transform.flip(self.heavy_attack_images[attack_frame], True, False)
            else:
                self.image = self.heavy_attack_images[attack_frame]

        elif self.movex != 0 and not self.is_dashing:
            self.frame += 1
            if self.frame >= len(self.images) * ani:
                self.frame = 0
            if self.movex < 0:
                self.image = pygame.transform.flip(self.images[self.frame // ani], True, False)
            else:
                self.image = self.images[self.frame // ani]
        else:
            if self.facing_right:
                self.image = self.images[0]
            else:
                self.image = pygame.transform.flip(self.images[0], True, False)

        self.rect.x += self.movex

        hit_list = pygame.sprite.spritecollide(self, ground_list, False)
        hit_list.extend(pygame.sprite.spritecollide(self, plat_list, False))
        for hit in hit_list:
            if self.movex > 0:
                self.rect.right = hit.rect.left
            elif self.movex < 0:
                self.rect.left = hit.rect.right

        self.movey += self.gravity
        self.rect.y += self.movey

        self.is_on_ground = False
        hit_list = pygame.sprite.spritecollide(self, ground_list, False)
        hit_list.extend(pygame.sprite.spritecollide(self, plat_list, False))
        for hit in hit_list:
            if self.movey > 0:
                self.rect.bottom = hit.rect.top
                self.movey = 0
                self.is_on_ground = True
            elif self.movey < 0:
                self.rect.top = hit.rect.bottom
                self.movey = 0

        if self.is_dashing:
            self.dash_frame += 1
            dash_progress = min(self.dash_frame / self.dash_duration, 1)
            dash_frame = int(dash_progress * (len(self.dash_images) - 1))
            if not self.facing_right:
                self.image = pygame.transform.flip(self.dash_images[dash_frame], True, False)
            else:
                self.image = self.dash_images[dash_frame]

        elif self.is_parrying:
            self.parry_frame += 1
            parry_progress = min(self.parry_frame / self.parry_window, 1)
            parry_frame = int(parry_progress * (len(self.parry_images) - 1))
            if not self.facing_right:
                self.image = pygame.transform.flip(self.parry_images[parry_frame], True, False)
            else:
                self.image = self.parry_images[parry_frame]


class Level():
    @staticmethod
    def bad(lvl):
        if lvl == 1:
            enemy = Enemy(1400, 500)
            enemy_list = pygame.sprite.Group()
            enemy_list.add(enemy)
        elif lvl == 2:
            enemy = Enemy(1400, 500)
            enemy_list = pygame.sprite.Group()
            enemy_list.add(enemy)
        return enemy_list

    @staticmethod
    def ground(lvl, x, y, w, h):
        ground_list = pygame.sprite.Group()
        return ground_list

    @staticmethod
    def platform(lvl):
        plat_list = pygame.sprite.Group()
        if lvl == 1:
            plat = Platform(100, worldy - 97 - 128, 285, 67, 'blockm22.png')
            plat_list.add(plat)
            plat = Platform(500, worldy - 97 - 320, 197, 54, 'blockm21.png')
            plat_list.add(plat)
            plat = Platform(1300, worldy - 97 - 320, 197, 54, 'blockm21.png')
            plat_list.add(plat)
        elif lvl == 2:
            plat = Platform(870, worldy - 97 - 180, 285, 67, 'blockm11.png')
            plat_list.add(plat)
            plat = Platform(1625, worldy - 97 - 700, 197, 54, 'blockm12.png')
            plat_list.add(plat)
            plat = Platform(100, worldy - 97 - 700, 285, 67, 'blockm12.png')
            plat_list.add(plat)
            plat = Platform(450, worldy - 97 - 370, 197, 54, 'blockm11.png')
            plat_list.add(plat)
            plat = Platform(800, worldy - 97 - 550, 285, 67, 'blockm13.png')
            plat_list.add(plat)
            plat = Platform(1300, worldy - 97 - 370, 197, 54, 'blockm11.png')
            plat_list.add(plat)
        return plat_list

    @staticmethod
    def get_background(lvl):
        if lvl == 1:
            return 'stage4.jpg'
        elif lvl == 2:
            return 'stage4.jpg'


class Platform(pygame.sprite.Sprite):
    def __init__(self, xloc, yloc, imgw, imgh, img):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(os.path.join('images', img)).convert()
        self.image.convert_alpha()
        self.image.set_colorkey(ALPHA)
        self.rect = self.image.get_rect()
        self.rect.y = yloc
        self.rect.x = xloc


'''
Camera
'''

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.lerp_speed = 0.1
        self.margin = 200
        self.min_zoom = 1.5
        self.max_zoom = 2

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def apply_rect(self, rect):
        return rect.move(self.camera.topleft)

    def update(self, target1, target2=None):
        if target2 is None:
            target2 = type('', (), {'rect': pygame.Rect(target1.rect.x + 300, target1.rect.y, 50, 50)})

        mid_x = (target1.rect.centerx + target2.rect.centerx) / 2
        mid_y = (target1.rect.centery + target2.rect.centery) / 2

        distance_x = abs(target1.rect.centerx - target2.rect.centerx)
        distance_y = abs(target1.rect.centery - target2.rect.centery)

        x = -mid_x + worldx / 2
        y = -mid_y + worldy / 2

        required_zoom_x = min(self.max_zoom, max(self.min_zoom, distance_x / (worldx - 2 * self.margin)))
        required_zoom_y = min(self.max_zoom, max(self.min_zoom, distance_y / (worldy - 2 * self.margin)))
        zoom_factor = max(required_zoom_x, required_zoom_y)

        self.camera.x += (x - self.camera.x) * self.lerp_speed
        self.camera.y += (y - self.camera.y) * self.lerp_speed

        self.camera.x = min(0, self.camera.x)
        self.camera.y = min(0, self.camera.y)
        self.camera.x = max(-(self.width * zoom_factor - worldx), self.camera.x)
        self.camera.y = max(-(self.height * zoom_factor - worldy), self.camera.y)

camera = Camera(4000, worldy)

'''
Setup
'''

def init_game():
    global player, player2, player_list, enemy_list, ground_list, plat_list, camera, backdrop, backdropbox

    # Загружаем выбранную карту
    backdrop = pygame.image.load(os.path.join('images', Level.get_background(current_map)))
    backdropbox = world.get_rect()

    player = Player()
    player.rect.x = 580
    player.rect.y = 500
    player_list = pygame.sprite.Group()
    player_list.add(player)

    if game_mode == "PVE":
        enemy_list = Level.bad(current_map)
        for enemy in enemy_list:
            if difficulty == "easy":
                enemy.decision_delay = 20
                enemy.aggression = 0.5
            elif difficulty == "medium":
                enemy.decision_delay = 10
                enemy.aggression = 0.7
            elif difficulty == "hard":
                enemy.decision_delay = 0
                enemy.aggression = 0.9
    else:
        player2 = Player(is_player2=True)
        player2.rect.x = 1400
        player2.rect.y = 500
        player_list.add(player2)
        enemy_list = pygame.sprite.Group()

    ground_list = Level.ground(current_map, 0, worldy - 97, 1080, 97)
    plat_list = Level.platform(current_map)

    camera = Camera(4000, worldy)


clock = pygame.time.Clock()
pygame.init()
world = pygame.display.set_mode([worldx, worldy])
backdrop = pygame.image.load(os.path.join('images', 'stage4.jpg'))
backdropbox = world.get_rect()
player = Player()
player.rect.x = 0
player.rect.y = 505
player_list = pygame.sprite.Group()
player_list.add(player)
player2 = None
steps = 10
DIFFICULTY_SELECT = 6
difficulty = "medium"

enemy_list = Level.bad(1)
ground_list = Level.ground(1, 0, worldy - 97, 1080, 97)
plat_list = Level.platform(1)

# кнопки меню
start_button = Button(worldx // 2 - 100, worldy // 2 - 50, 200, 50, "Start", (70, 70, 70), (100, 100, 100))
exit_button = Button(worldx // 2 - 100, worldy // 2 + 50, 200, 50, "Exit", (70, 70, 70), (100, 100, 100))
restart_button = Button(worldx // 2 - 100, worldy // 2 - 50, 200, 50, "Restart", (70, 70, 70), (100, 100, 100))
menu_button = Button(worldx // 2 - 100, worldy // 2 + 50, 200, 50, "Menu", (70, 70, 70), (100, 100, 100))
resume_button = Button(worldx // 2 - 100, worldy // 2 - 50, 200, 50, "Resume", (70, 70, 70), (100, 100, 100))

# кнопки выбора режима
pve_button = Button(worldx // 2 - 220, worldy // 2 - 50, 200, 50, "PVE", (70, 70, 70), (100, 100, 100))
pvp_button = Button(worldx // 2 + 20, worldy // 2 - 50, 200, 50, "PVP", (70, 70, 70), (100, 100, 100))
back_button = Button(worldx // 2 - 100, worldy // 2 + 50, 200, 50, "Back", (70, 70, 70), (100, 100, 100))

# кнопки выбора карты
map1_button = Button(worldx // 2 - 220, worldy // 2 - 50, 200, 50, "Map 1", (70, 70, 70), (100, 100, 100))
map2_button = Button(worldx // 2 + 20, worldy // 2 - 50, 200, 50, "Map 2", (70, 70, 70), (100, 100, 100))
map_back_button = Button(worldx // 2 - 100, worldy // 2 + 50, 200, 50, "Back", (70, 70, 70), (100, 100, 100))

# кнопки выбора сложности
easy_button = Button(worldx // 2 - 220, worldy // 2 - 50, 200, 50, "Easy", (70, 70, 70), (100, 100, 100))
medium_button = Button(worldx // 2 + 20, worldy // 2 - 50, 200, 50, "Medium", (70, 70, 70), (100, 100, 100))
hard_button = Button(worldx // 2 - 100, worldy // 2 + 50, 200, 50, "Hard", (70, 70, 70), (100, 100, 100))
difficulty_back_button = Button(worldx // 2 - 100, worldy // 2 + 150, 200, 50, "Back", (70, 70, 70), (100, 100, 100))

init_game()

'''
Main Loop
'''

while main:
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            main = False

        # кнопки
        if game_state == MENU:
            start_button.check_hover(mouse_pos)
            exit_button.check_hover(mouse_pos)

            if start_button.is_clicked(mouse_pos, event):
                game_state = MODE_SELECT
            elif exit_button.is_clicked(mouse_pos, event):
                main = False

        elif game_state == MODE_SELECT:
            pve_button.check_hover(mouse_pos)
            pvp_button.check_hover(mouse_pos)
            back_button.check_hover(mouse_pos)

            if pve_button.is_clicked(mouse_pos, event):
                game_mode = "PVE"
                game_state = MAP_SELECT
            elif pvp_button.is_clicked(mouse_pos, event):
                game_mode = "PVP"
                game_state = MAP_SELECT  # Переходим к выбору карты
            elif back_button.is_clicked(mouse_pos, event):
                game_state = MENU

        elif game_state == MAP_SELECT:
            map1_button.check_hover(mouse_pos)
            map2_button.check_hover(mouse_pos)
            map_back_button.check_hover(mouse_pos)

            if map1_button.is_clicked(mouse_pos, event):
                current_map = 1

                if game_mode == "PVE":
                    game_state = DIFFICULTY_SELECT

                else:
                    game_state = PLAYING
                    init_game()

            elif map2_button.is_clicked(mouse_pos, event):
                current_map = 2

                if game_mode == "PVE":
                    game_state = DIFFICULTY_SELECT

                else:
                    game_state = PLAYING
                    init_game()

            elif map_back_button.is_clicked(mouse_pos, event):
                game_state = MODE_SELECT

        # управление
        elif game_state == PLAYING:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = PAUSED

                if event.key == pygame.K_a:
                    player.control(-steps, 0)
                if event.key == pygame.K_d:
                    player.control(steps, 0)
                if event.key == pygame.K_w:
                    player.jump()
                if event.key == pygame.K_r:
                    player.attack()
                if event.key == pygame.K_t:
                    player.heavy_attack()
                if event.key == pygame.K_f:
                    if player.parry():
                        print("Успешное парирование!")
                if event.key == pygame.K_g:
                    player.dash()

                if game_mode == "PVP" and player2 is not None:
                    if event.key == pygame.K_LEFT:
                        player2.control(-steps, 0)
                    if event.key == pygame.K_RIGHT:
                        player2.control(steps, 0)
                    if event.key == pygame.K_UP:
                        player2.jump()
                    if event.key == pygame.K_KP1:
                        player2.attack()
                    if event.key == pygame.K_KP2:
                        player2.heavy_attack()
                    if event.key == pygame.K_KP3:
                        if player2.parry():
                            print("Успешное парирование P2!")
                    if event.key == pygame.K_KP4:
                        player2.dash()

        # сложность
        elif game_state == DIFFICULTY_SELECT:
            easy_button.check_hover(mouse_pos)
            medium_button.check_hover(mouse_pos)
            hard_button.check_hover(mouse_pos)
            difficulty_back_button.check_hover(mouse_pos)

            if easy_button.is_clicked(mouse_pos, event):
                difficulty = "easy"
                game_state = PLAYING
                init_game()
            elif medium_button.is_clicked(mouse_pos, event):
                difficulty = "medium"
                game_state = PLAYING
                init_game()
            elif hard_button.is_clicked(mouse_pos, event):
                difficulty = "hard"
                game_state = PLAYING
                init_game()
            elif difficulty_back_button.is_clicked(mouse_pos, event):
                game_state = MAP_SELECT

        # плавная ходьба
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                player.keys_pressed['left'] = False
                if not player.keys_pressed['right']:
                    player.movex = 0
                else:
                    player.control(steps, 0)
            if event.key == pygame.K_d:
                player.keys_pressed['right'] = False
                if not player.keys_pressed['left']:
                    player.movex = 0
                else:
                    player.control(-steps, 0)

            if game_mode == "PVP" and player2 is not None:
                if event.key == pygame.K_LEFT:
                    player2.keys_pressed['left'] = False
                    if not player2.keys_pressed['right']:
                        player2.movex = 0
                    else:
                        player2.control(steps, 0)
                if event.key == pygame.K_RIGHT:
                    player2.keys_pressed['right'] = False
                    if not player2.keys_pressed['left']:
                        player2.movex = 0
                    else:
                        player2.control(-steps, 0)

        elif game_state == PAUSED:
            resume_button.check_hover(mouse_pos)
            menu_button.check_hover(mouse_pos)

            if resume_button.is_clicked(mouse_pos, event):
                game_state = PLAYING
            elif menu_button.is_clicked(mouse_pos, event):
                game_state = MENU

        elif game_state == GAME_OVER:
            restart_button.check_hover(mouse_pos)
            menu_button.check_hover(mouse_pos)

            if restart_button.is_clicked(mouse_pos, event):
                game_state = PLAYING
                init_game()
            elif menu_button.is_clicked(mouse_pos, event):
                game_state = MENU

    if game_state == PLAYING:
        if game_mode == "PVP" and player2 is not None:
            camera.update(player, player2)
        else:
            virtual_target = type('', (), {'rect': pygame.Rect(player.rect.x + 300, player.rect.y, 50, 50)})
            camera.update(player, virtual_target)

        player.update()
        if game_mode == "PVP" and player2 is not None:
            player2.update()

        if player.check_out_of_bounds() or (player2 is not None and player2.check_out_of_bounds()):
            game_state = GAME_OVER

        if game_mode == "PVE":
            for e in enemy_list:
                e.update()
                if e.check_out_of_bounds():
                    game_state = GAME_OVER
                    break

    # oтрисовка
    world.blit(backdrop, backdropbox)
    if game_state == MENU:
        title_text = title_font.render("fighting", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(worldx // 2, worldy // 3))
        world.blit(title_text, title_rect)

        start_button.draw(world)
        exit_button.draw(world)

    elif game_state == MODE_SELECT:
        title_text = title_font.render("Select Game Mode", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(worldx // 2, worldy // 3))
        world.blit(title_text, title_rect)

        pve_button.draw(world)
        pvp_button.draw(world)
        back_button.draw(world)

    elif game_state == MAP_SELECT:
        title_text = title_font.render("Select Map", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(worldx // 2, worldy // 3))
        world.blit(title_text, title_rect)

        map1_button.draw(world)
        map2_button.draw(world)
        map_back_button.draw(world)

    elif game_state == PLAYING:
        for entity in ground_list:
            world.blit(entity.image, camera.apply(entity))
        for entity in plat_list:
            world.blit(entity.image, camera.apply(entity))

        for entity in enemy_list:
            if entity.is_alive:
                world.blit(entity.image, camera.apply(entity))

        for player_entity in player_list:
            world.blit(player_entity.image, camera.apply(player_entity))
        draw_hud()

    elif game_state == PAUSED:
        for entity in ground_list:
            world.blit(entity.image, camera.apply(entity))
        for entity in plat_list:
            world.blit(entity.image, camera.apply(entity))

        for entity in enemy_list:
            if entity.is_alive:
                world.blit(entity.image, camera.apply(entity))

        for player_entity in player_list:
            world.blit(player_entity.image, camera.apply(player_entity))

        overlay = pygame.Surface((worldx, worldy), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        world.blit(overlay, (0, 0))

        pause_text = title_font.render("Paused", True, (255, 255, 255))
        pause_rect = pause_text.get_rect(center=(worldx // 2, worldy // 3))
        world.blit(pause_text, pause_rect)

        resume_button.draw(world)
        menu_button.draw(world)

    elif game_state == DIFFICULTY_SELECT:
        title_text = title_font.render("Select Difficulty", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(worldx // 2, worldy // 3))
        world.blit(title_text, title_rect)

        easy_button.draw(world)
        medium_button.draw(world)
        hard_button.draw(world)
        difficulty_back_button.draw(world)

    elif game_state == GAME_OVER:
        overlay = pygame.Surface((worldx, worldy), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        world.blit(overlay, (0, 0))

        if game_mode == "PVP":
            if player.health <= 0 or player.check_out_of_bounds():
                winner_text = title_font.render("Player 2 Wins!", True, (255, 255, 255))

            else:
                winner_text = title_font.render("Player 1 Wins!", True, (255, 255, 255))

        else:  # PVE
            enemy_alive = any(e.is_alive and not e.check_out_of_bounds() for e in enemy_list)

            if player.health <= 0 or player.check_out_of_bounds():
                winner_text = title_font.render("Enemy Wins!", True, (255, 0, 0))

            elif not enemy_alive:
                winner_text = title_font.render("You Win!", True, (0, 255, 0))

            else:
                winner_text = title_font.render("You Win!", True, (0, 255, 0))

        winner_rect = winner_text.get_rect(center=(worldx // 2, worldy // 3))
        world.blit(winner_text, winner_rect)

        restart_button.draw(world)
        menu_button.draw(world)

    pygame.display.flip()
    clock.tick(fps)

pygame.quit()
sys.exit()