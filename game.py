import pygame
import sys
import os
import math
import random

pygame.font.init()
font = pygame.font.SysFont('Arial', 24)


def draw_hud():
    # Фон для HUD
    pygame.draw.rect(world, (50, 50, 50), (0, 0, worldx, 40))

    # Статистика игрока (слева)
    player_hp_text = font.render(f"HP: {player.health}", True, (255, 255, 255))
    player_parry_cd = max(0, player.parry_cooldown / fps)
    player_parry_text = font.render(f"Parry CD: {player_parry_cd:.1f}s", True, (255, 255, 255))

    world.blit(player_hp_text, (10, 10))
    world.blit(player_parry_text, (150, 10))

    # Статистика врагов (справа)
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
main = True
ALPHA = (0, 255, 0)

'''
Objects
'''


class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.movex = 0
        self.movey = 0
        self.frame = 0
        self.health = 2
        self.images = []
        self.attack_images = []
        self.facing_right = True
        self.is_attacking = False
        self.attack_cooldown = 0
        self.parry_cooldown = 0
        self.is_parrying = False
        self.parry_frames = 0
        self.parry_window = 10  # Количество кадров для парирования
        self.parry_range = 120  # Дистанция парирования

        # Загрузка анимаций
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

    def strong_attack(self):
        pass

    def parry(self):
        if self.parry_cooldown == 0:
            self.is_parrying = True
            self.parry_frames = self.parry_window
            self.parry_cooldown = 30

            # Проверяем парирование атак врагов
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
                        enemy.stun(200)  #стан
                        return True
        return False

    def take_damage(self, damage):
        if not self.is_parrying:
            self.health -= damage
            if self.health <= 0:
                pygame.quit()
                sys.exit()

    def stun(self, frames):
        pass

    def update(self):
        # Обновление кд
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.parry_cooldown > 0:
            self.parry_cooldown -= 1

        if self.is_parrying:
            self.parry_frames -= 1
            if self.parry_frames <= 0:
                self.is_parrying = False

        # Движение и столкновения
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

        # Анимации
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
            return True
        return False


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
            img = pygame.image.load(os.path.join('images', 'y' + str(i) + '.png')).convert() # ПОТОМ ПОМЕНЯЙ
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
        print('dfgf')

    def attack_player(self):
        if self.attack_cooldown == 0 and self.stun_frames == 0:
            self.is_attacking = True
            self.attack_frame = 0
            self.attack_cooldown = 60
            self.attack_active = False

            # Определяем направление к игроку
            if player.rect.centerx > self.rect.centerx:
                self.facing_right = True
            else:
                self.facing_right = False

    def move(self):
        if not self.is_alive or self.stun_frames > 0:
            self.stun_frames = max(0, self.stun_frames - 1)
            return

        # Атака каждые 2 секунды
        self.attack_timer += 1
        if self.attack_timer >= self.attack_delay:
            self.attack_timer = 0
            self.attack_player()

        # Движение
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

        # Обновление атаки
        if self.is_attacking:
            self.attack_frame += 1

            # Анимация атаки
            if self.attack_frame < 3 * ani:
                attack_frame = self.attack_frame // ani
                if not self.facing_right:
                    self.image = pygame.transform.flip(self.attack_images[attack_frame], True, False)
                else:
                    self.image = self.attack_images[attack_frame]
            else:
                self.is_attacking = False
                self.attack_frame = 0

            # Нанесение урона в определенный момент анимации
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

        # Горизонтальное движение
        if not self.is_attacking:
            self.rect.x += self.movex
            hit_list = pygame.sprite.spritecollide(self, ground_list, False)
            hit_list.extend(pygame.sprite.spritecollide(self, plat_list, False))
            for hit in hit_list:
                if self.movex > 0:
                    self.rect.right = hit.rect.left
                elif self.movex < 0:
                    self.rect.left = hit.rect.right

        # Гравитация
        self.movey += self.gravity
        self.rect.y += self.movey

        # Столкновения по вертикали
        hit_list = pygame.sprite.spritecollide(self, ground_list, False)
        hit_list.extend(pygame.sprite.spritecollide(self, plat_list, False))
        for hit in hit_list:
            if self.movey > 0:
                self.rect.bottom = hit.rect.top
                self.movey = 0
            elif self.movey < 0:
                self.rect.top = hit.rect.bottom
                self.movey = 0

        # Обновление кд атаки
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

class Level():
    def bad(lvl, eloc):
        if lvl == 1:
            enemy = Enemy(eloc[0], eloc[1], 'y1.png')  # спавн врага
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

'''
Camera
'''

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

        # Плавное движение камеры (LERP)
        self.camera.x += (x - self.camera.x) * 0.1
        self.camera.y += (y - self.camera.y) * 0.1

        # Ограничение камеры в пределах уровня
        self.camera.x = min(0, self.camera.x)
        self.camera.y = min(0, self.camera.y)
        self.camera.x = max(-(self.width - worldx), self.camera.x)
        self.camera.y = max(-(self.height - worldy), self.camera.y)


camera = Camera(2000, worldy)

'''
Main Loop
'''
while main:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            main = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == ord('a'):
                player.control(-steps, 0)
            if event.key == pygame.K_RIGHT or event.key == ord('d'):
                player.control(steps, 0)
            if event.key == pygame.K_UP or event.key == ord('w'):
                player.jump()
            if event.key == pygame.K_SPACE:  # атака
                player.attack()
            if event.key == ord('f'):  # парирование
                if player.parry():
                    print("Успешное парирование!")

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == ord('a'):
                player.control(steps, 0)
            if event.key == pygame.K_RIGHT or event.key == ord('d'):
                player.control(-steps, 0)
            if event.key == ord('q'):
                pygame.quit()
                sys.exit()
                main = False

    # Обновление камеры
    camera.update(player)

    # Обновление игрока и врагов
    player.update()
    for e in enemy_list:
        e.move()

    if player.check_out_of_bounds():
        print("Игрок упал за пределы карты!")
        main = False

    # Отрисовка
    world.blit(backdrop, backdropbox)

    # Отрисовка земли и платформ
    for entity in ground_list:
        world.blit(entity.image, camera.apply(entity))
    for entity in plat_list:
        world.blit(entity.image, camera.apply(entity))

    # Отрисовка врагов
    for entity in enemy_list:
        if entity.is_alive:
            world.blit(entity.image, camera.apply(entity))

    # Отрисовка игрока
    world.blit(player.image, camera.apply(player))
    draw_hud()
    pygame.display.flip()
    clock.tick(fps)

pygame.quit()
sys.exit()