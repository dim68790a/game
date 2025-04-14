import pygame
import sys
import os
import math
import random

pygame.font.init()
font = pygame.font.SysFont('Arial', 24)
title_font = pygame.font.SysFont('Arial', 48)


def draw_hud():
    pygame.draw.rect(world, (50, 50, 50), (0, 0, worldx, 40))

    player_hp_text = font.render(f"HP: {player.health}", True, (255, 255, 255))
    player_parry_cd = max(0, player.parry_cooldown / fps)
    player_parry_text = font.render(f"Parry CD: {player_parry_cd:.1f}s", True, (255, 255, 255))

    world.blit(player_hp_text, (10, 10))
    world.blit(player_parry_text, (150, 10))

    if len(enemy_list) > 0:
        enemy = enemy_list.sprites()[0]
        enemy_hp_text = font.render(f"Enemy HP: {enemy.health}", True, (255, 255, 255))
        enemy_attack_cd = max(0, (enemy.attack_delay - enemy.attack_timer) / fps)
        enemy_attack_text = font.render(f"Attack in: {enemy_attack_cd:.1f}s", True, (255, 255, 255))

        world.blit(enemy_hp_text, (worldx - 250, 10))
        world.blit(enemy_attack_text, (worldx - 450, 10))


'''
Variables
'''
worldx = 1280
worldy = 720
fps = 60
ani = 10
ALPHA = (0, 255, 0)

MENU = 0
PLAYING = 1
GAME_OVER = 2
game_state = MENU

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
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.movex = 0
        self.movey = 0
        self.frame = 0
        self.health = 2
        self.max_health = 2
        self.images = []
        self.attack_images = []
        self.facing_right = True
        self.is_attacking = False
        self.attack_cooldown = 0
        self.parry_cooldown = 0
        self.is_parrying = False
        self.parry_frames = 0
        self.parry_window = 10
        self.parry_range = 120

        for i in range(1, 5):
            img = pygame.image.load(os.path.join('images', 'hero' + str(i) + '.png')).convert()
            img.convert_alpha()
            img.set_colorkey(ALPHA)
            self.images.append(img)

        for i in range(1, 5):
            img = pygame.image.load(os.path.join('images', 'hero_attack' + str(i) + '.png')).convert()
            img.convert_alpha()
            img.set_colorkey(ALPHA)
            self.attack_images.append(img)

        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.gravity = 0.5
        self.jump_power = -12
        self.is_on_ground = False
        self.attack_range = 100
        self.attack_damage = 1

    def control(self, x, y):
        self.movex += x
        self.movey += y

    def jump(self):
        if self.is_on_ground:
            self.movey = self.jump_power
            self.is_on_ground = False

    def attack(self):
        if self.attack_cooldown == 0:
            self.is_attacking = True
            self.attack_cooldown = 20
            self.frame = 0

            for enemy in enemy_list:
                attack_rect = pygame.Rect(0, 0, self.attack_range, self.rect.height)
                if self.facing_right:
                    attack_rect.left = self.rect.right
                else:
                    attack_rect.right = self.rect.left
                attack_rect.top = self.rect.top

                if attack_rect.colliderect(enemy.rect):
                    enemy.take_damage(self.attack_damage)

    def parry(self):
        if self.parry_cooldown == 0:
            self.is_parrying = True
            self.parry_frames = self.parry_window
            self.parry_cooldown = 30

            for enemy in enemy_list:
                if enemy.is_attacking and enemy.attack_frame <= enemy.attack_startup:
                    enemy_attack_rect = pygame.Rect(0, 0, enemy.attack_range, enemy.rect.height)
                    if not enemy.facing_right:
                        enemy_attack_rect.left = enemy.rect.right
                    else:
                        enemy_attack_rect.right = enemy.rect.left
                    enemy_attack_rect.top = enemy.rect.top

                    parry_rect = pygame.Rect(0, 0, self.parry_range, self.rect.height)
                    if self.facing_right:
                        parry_rect.left = self.rect.right
                    else:
                        parry_rect.right = self.rect.left
                    parry_rect.top = self.rect.top

                    if parry_rect.colliderect(enemy_attack_rect):
                        enemy.stun(200)
                        return True
        return False

    def take_damage(self, damage):
        if not self.is_parrying:
            self.health -= damage
            if self.health <= 0:
                global game_state
                game_state = GAME_OVER

    def stun(self, frames):
        pass

    def update(self):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.parry_cooldown > 0:
            self.parry_cooldown -= 1

        if self.is_parrying:
            self.parry_frames -= 1
            if self.parry_frames <= 0:
                self.is_parrying = False

        self.rect.x += self.movex

        if self.movex > 0:
            self.facing_right = True
        elif self.movex < 0:
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

        if self.is_attacking:
            self.frame += 1
            if self.frame >= 3 * ani:
                self.frame = 0
                self.is_attacking = False
            attack_frame = self.frame // ani
            if not self.facing_right:
                self.image = pygame.transform.flip(self.attack_images[attack_frame], True, False)
            else:
                self.image = self.attack_images[attack_frame]
        elif self.movex != 0:
            self.frame += 1
            if self.frame > 3 * ani:
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

    def check_out_of_bounds(self):
        if self.rect.top > worldy:
            global game_state
            game_state = GAME_OVER
            return True
        return False

    def reset(self):
        self.health = self.max_health
        self.rect.x = 0
        self.rect.y = 505
        self.movex = 0
        self.movey = 0
        self.is_attacking = False
        self.is_parrying = False
        self.attack_cooldown = 0
        self.parry_cooldown = 0


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, img):
        pygame.sprite.Sprite.__init__(self)
        self.frame = 0
        self.images = []
        self.attack_images = []
        self.facing_right = False
        self.is_attacking = False
        self.attack_cooldown = 0
        self.attack_frame = 0
        self.attack_startup = 10
        self.attack_active = False
        self.stun_frames = 0
        self.attack_delay = 120
        self.attack_timer = random.randint(0, self.attack_delay)

        for i in range(1, 5):
            img = pygame.image.load(os.path.join('images', 'y' + str(i) + '.png')).convert()
            img.convert_alpha()
            img.set_colorkey(ALPHA)
            self.images.append(img)

        for i in range(1, 5):
            img = pygame.image.load(os.path.join('images', 'y' + str(i) + '.png')).convert()
            img.convert_alpha()
            img.set_colorkey(ALPHA)
            self.attack_images.append(img)

        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.counter = 0
        self.movey = 0
        self.movex = 0
        self.gravity = 0.5
        self.health = 3
        self.is_alive = True
        self.attack_range = 80
        self.attack_damage = 1
        self.attack_timer = 0
        self.attack_delay = 120

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.is_alive = False
            enemy_list.remove(self)

    def stun(self, frames):
        self.stun_frames = frames

    def attack_player(self):
        if self.attack_cooldown == 0 and self.stun_frames == 0:
            self.is_attacking = True
            self.attack_frame = 0
            self.attack_cooldown = 60
            self.attack_active = False

            if player.rect.centerx > self.rect.centerx:
                self.facing_right = True
            else:
                self.facing_right = False

    def move(self):
        if not self.is_alive or self.stun_frames > 0:
            self.stun_frames = max(0, self.stun_frames - 1)
            return

        self.attack_timer += 1
        if self.attack_timer >= self.attack_delay:
            self.attack_timer = 0
            self.attack_player()

        distance = 80
        speed = 2

        if self.counter >= 0 and self.counter <= distance:
            self.movex = speed
            self.frame += 1
            if self.frame > 3 * ani:
                self.frame = 0
            self.image = self.images[self.frame // ani]
        elif self.counter >= distance and self.counter <= distance * 2:
            self.movex = -speed
            self.frame += 1
            if self.frame > 3 * ani:
                self.frame = 0
            self.image = pygame.transform.flip(self.images[self.frame // ani], True, False)
        else:
            self.counter = 0

        self.counter += 1

        if self.is_attacking:
            self.attack_frame += 1

            if self.attack_frame < 3 * ani:
                attack_frame = self.attack_frame // ani
                if not self.facing_right:
                    self.image = pygame.transform.flip(self.attack_images[attack_frame], True, False)
                else:
                    self.image = self.attack_images[attack_frame]
            else:
                self.is_attacking = False
                self.attack_frame = 0

            if self.attack_frame == self.attack_startup and not self.attack_active:
                self.attack_active = True

                attack_rect = pygame.Rect(0, 0, self.attack_range, self.rect.height)
                if self.facing_right:
                    attack_rect.left = self.rect.right
                else:
                    attack_rect.right = self.rect.left
                attack_rect.top = self.rect.top

                if attack_rect.colliderect(player.rect):
                    player.take_damage(self.attack_damage)

            if self.attack_frame > self.attack_startup:
                self.attack_active = False

        if not self.is_attacking:
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

        hit_list = pygame.sprite.spritecollide(self, ground_list, False)
        hit_list.extend(pygame.sprite.spritecollide(self, plat_list, False))
        for hit in hit_list:
            if self.movey > 0:
                self.rect.bottom = hit.rect.top
                self.movey = 0
            elif self.movey < 0:
                self.rect.top = hit.rect.bottom
                self.movey = 0

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1


class Level():
    def bad(lvl, eloc):
        if lvl == 1:
            enemy = Enemy(eloc[0], eloc[1], 'y1.png')
            enemy_list = pygame.sprite.Group()
            enemy_list.add(enemy)
        if lvl == 2:
            print("Level " + str(lvl))

        return enemy_list

    def ground(lvl, x, y, w, h):
        ground_list = pygame.sprite.Group()
        if lvl == 1:
            ground = Platform(x, y, w, h, 'block-ground.png')
            ground_list.add(ground)

        if lvl == 2:
            print("Level " + str(lvl))

        return ground_list

    def platform(lvl):
        plat_list = pygame.sprite.Group()
        if lvl == 1:
            plat = Platform(200, worldy - 97 - 128, 285, 67, 'block-big.png')
            plat_list.add(plat)
            plat = Platform(500, worldy - 97 - 320, 197, 54, 'block-small.png')
            plat_list.add(plat)
        if lvl == 2:
            print("Level " + str(lvl))

        return plat_list

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def apply_rect(self, rect):
        return rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.x + int(worldx / 2)
        y = -target.rect.y + int(worldy / 2)

        self.camera.x += (x - self.camera.x) * 0.1
        self.camera.y += (y - self.camera.y) * 0.1

        self.camera.x = min(0, self.camera.x)
        self.camera.y = min(0, self.camera.y)
        self.camera.x = max(-(self.width - worldx), self.camera.x)
        self.camera.y = max(-(self.height - worldy), self.camera.y)

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
Setup
'''


def init_game():
    global player, player_list, enemy_list, ground_list, plat_list, camera

    player = Player()
    player.rect.x = 0
    player.rect.y = 505
    player_list = pygame.sprite.Group()
    player_list.add(player)

    eloc = [300, 0]
    enemy_list = Level.bad(1, eloc)
    ground_list = Level.ground(1, 0, worldy - 97, 1080, 97)
    plat_list = Level.platform(1)

    camera = Camera(2000, worldy)


clock = pygame.time.Clock()
pygame.init()
world = pygame.display.set_mode([worldx, worldy])
backdrop = pygame.image.load(os.path.join('images', 'stage.jpg'))
backdropbox = world.get_rect()
player = Player()
player.rect.x = 0
player.rect.y = 505
player_list = pygame.sprite.Group()
player_list.add(player)
steps = 10

eloc = [300, 0]
enemy_list = Level.bad(1, eloc)
ground_list = Level.ground(1, 0, worldy - 97, 1080, 97)
plat_list = Level.platform(1)

start_button = Button(worldx // 2 - 100, worldy // 2 - 50, 200, 50, "Start", (70, 70, 70), (100, 100, 100))
exit_button = Button(worldx // 2 - 100, worldy // 2 + 50, 200, 50, "Exit", (70, 70, 70), (100, 100, 100))
restart_button = Button(worldx // 2 - 100, worldy // 2 - 50, 200, 50, "Restart", (70, 70, 70), (100, 100, 100))
menu_button = Button(worldx // 2 - 100, worldy // 2 + 50, 200, 50, "Menu", (70, 70, 70), (100, 100, 100))

init_game()

'''
Main Loop
'''
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == MENU:
            start_button.check_hover(mouse_pos)
            exit_button.check_hover(mouse_pos)

            if start_button.is_clicked(mouse_pos, event):
                game_state = PLAYING
                init_game()
            elif exit_button.is_clicked(mouse_pos, event):
                running = False

        elif game_state == PLAYING:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == ord('a'):
                    player.control(-steps, 0)
                if event.key == pygame.K_RIGHT or event.key == ord('d'):
                    player.control(steps, 0)
                if event.key == pygame.K_UP or event.key == ord('w'):
                    player.jump()
                if event.key == pygame.K_SPACE:
                    player.attack()
                if event.key == ord('f'):
                    if player.parry():
                        print("Успешное парирование!")

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == ord('a'):
                    player.control(steps, 0)
                if event.key == pygame.K_RIGHT or event.key == ord('d'):
                    player.control(-steps, 0)

        elif game_state == GAME_OVER:
            restart_button.check_hover(mouse_pos)
            menu_button.check_hover(mouse_pos)

            if restart_button.is_clicked(mouse_pos, event):
                game_state = PLAYING
                init_game()
            elif menu_button.is_clicked(mouse_pos, event):
                game_state = MENU

    if game_state == PLAYING:
        camera.update(player)

        player.update()
        for e in enemy_list:
            e.move()

        player.check_out_of_bounds()

    world.blit(backdrop, backdropbox)

    if game_state == MENU:
        title_text = title_font.render("Platform Fighter", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(worldx // 2, worldy // 3))
        world.blit(title_text, title_rect)

        start_button.draw(world)
        exit_button.draw(world)

    elif game_state == PLAYING:
        for entity in ground_list:
            world.blit(entity.image, camera.apply(entity))
        for entity in plat_list:
            world.blit(entity.image, camera.apply(entity))

        for entity in enemy_list:
            if entity.is_alive:
                world.blit(entity.image, camera.apply(entity))

        world.blit(player.image, camera.apply(player))
        draw_hud()

    elif game_state == GAME_OVER:
        overlay = pygame.Surface((worldx, worldy), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        world.blit(overlay, (0, 0))

        game_over_text = title_font.render("Game Over", True, (255, 255, 255))
        game_over_rect = game_over_text.get_rect(center=(worldx // 2, worldy // 3))
        world.blit(game_over_text, game_over_rect)

        restart_button.draw(world)
        menu_button.draw(world)

    pygame.display.flip()
    clock.tick(fps)

pygame.quit()
sys.exit()