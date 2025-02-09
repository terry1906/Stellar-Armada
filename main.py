import pygame
import sys
import random
import math

# ============ ИНИЦИАЛИЗАЦИЯ ================
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shooter Game")
clock = pygame.time.Clock()

# --- Фоновая музыка ---
current_music = None  


def update_music():
       Если уровень боссовой (level % 5 == 0), нормальная музыка ставится на паузу,
       и запускается музыка для босса, иначе – воспроизводится нормальная музыка.
    """
    global current_music
    try:
        if level % 5 == 0:
            if current_music != "boss":
                pygame.mixer.music.pause()  # Приостанавливаем текущую музыку
                pygame.mixer.music.load("61b96400fd1fd08.mp3")
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
                current_music = "boss"
        else:
            if current_music != "normal":
                pygame.mixer.music.pause()
                pygame.mixer.music.load("a31df44c3944ea6.mp3")
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
                current_music = "normal"
    except Exception as e:
        print("Ошибка обновления музыки:", e)


# ================= ГЛОБАЛЬНЫЕ СОСТОЯНИЯ =================
STATE_MENU = "menu"
STATE_GAME = "game"
STATE_GAMEOVER = "game_over"
STATE_TOP10 = "top10"
current_state = STATE_MENU

game_mode = "single"  # "single" или "multi"
difficulty_multiplier = 1

# ================= НАСТРОЙКИ ИГРЫ ====================
bg_color = (30, 30, 30)
FONT_SMALL = pygame.font.SysFont('Arial', 20)
FONT_MEDIUM = pygame.font.SysFont('Arial', 28)
FONT_LARGE = pygame.font.SysFont('Arial', 48)

PLAYER_SIZE = 30
PLAYER_SPEED = 8
PLAYER_MAX_HEALTH = 5
PLAYER_SHOOT_DELAY = 200  # мс между выстрелами
PLAYER_RECOIL = 3

BULLET_WIDTH = 6
BULLET_HEIGHT = 20
BULLET_SPEED = 12

START_LEVEL = 1
level = START_LEVEL
score = 0
score_multiplier = 1

regen_threshold = 20  # Каждые 20 очков +1 сердце

highscore = 0
top10_scores = []
try:
    with open("highscore.txt", "r") as f:
        highscore = int(f.read())
except FileNotFoundError:
    highscore = 0
try:
    with open("top10.txt", "r") as f:
        for line in f:
            top10_scores.append(int(line.strip()))
    top10_scores.sort(reverse=True)
except FileNotFoundError:
    top10_scores = []

# ========== ЗАГРУЗКА СПРАЙТОВ ==========
# Анимированный спрайт игрока (кадры "player_1.png" ... "player_4.png")
player_frames = []
for i in range(1, 5):
    try:
        frame = pygame.image.load(f"player_{i}.png").convert_alpha()
        frame = pygame.transform.scale(frame, (PLAYER_SIZE, PLAYER_SIZE))
        player_frames.append(frame)
    except Exception as e:
        print(f"Ошибка загрузки player_{i}.png:", e)
if not player_frames:
    player_frames = [None]

try:
    enemy_sprite = pygame.image.load('enemy_sprite.png').convert_alpha()
except Exception as e:
    print("Ошибка загрузки enemy_sprite.png:", e)
    enemy_sprite = None

try:
    boss_sprite = pygame.image.load('boss.png').convert_alpha()
except Exception as e:
    print("Ошибка загрузки boss.png:", e)
    boss_sprite = None

try:
    defender_sprite = pygame.image.load('defender.png').convert_alpha()
except Exception as e:
    print("Ошибка загрузки defender.png:", e)
    defender_sprite = None

try:
    tank_sprite = pygame.image.load('tank.png').convert_alpha()
except Exception as e:
    print("Ошибка загрузки tank.png:", e)
    tank_sprite = None

try:
    heart_sprite = pygame.image.load('Heart.jpg').convert()
    heart_sprite.set_colorkey((0, 0, 0))
    heart_sprite = pygame.transform.scale(heart_sprite, (35, 35))
except Exception as e:
    print("Ошибка загрузки Heart.jpg:", e)
    heart_sprite = None

# Фоны для игровых уровней (bg1.png, bg2.png, bg3.png, bg4.png)
background_files = ['bg1.png', 'bg2.png', 'bg3.png', 'bg4.png']
backgrounds = []
for fname in background_files:
    try:
        bg = pygame.image.load(fname).convert()
        bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
        backgrounds.append(bg)
    except Exception as e:
        print(f"Ошибка загрузки {fname}:", e)
if backgrounds:
    current_background_index = 0
    bg_surface = backgrounds[current_background_index]
else:
    bg_surface = None

# Анимированный фон для меню – 12 кадров, имена файлов: "1.png", "2.png", …, "12.png"
menu_bg_frames = []
for i in range(1, 13):
    try:
        frame = pygame.image.load(f"{i}.png").convert()
        frame = pygame.transform.scale(frame, (WIDTH, HEIGHT))
        menu_bg_frames.append(frame)
    except Exception as e:
        print(f"Ошибка загрузки {i}.png:", e)

menu_bg_frame_index = 0
menu_bg_last_update = pygame.time.get_ticks()
menu_bg_frame_duration = 100  # мс между кадрами меню

# Фон для экрана смерти
try:
    gameover_bg = pygame.image.load("gameover_bg.png").convert()
    gameover_bg = pygame.transform.scale(gameover_bg, (WIDTH, HEIGHT))
except Exception as e:
    print("Ошибка загрузки gameover_bg.png:", e)
    gameover_bg = None

is_paused = False
defender_shoot_index = 0


# ============= КЛАССЫ ================

class Player:
    def __init__(self, x, y, color, controls):
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.color = color
        self.speed = PLAYER_SPEED
        self.health = float(PLAYER_MAX_HEALTH)
        self.last_shot = 0
        self.controls = controls
        self.invulnerable_until = 0
        self.sprite_frames = player_frames
        self.frame_index = 0
        self.last_frame_update = pygame.time.get_ticks()
        self.frame_duration = 200

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_frame_update > self.frame_duration:
            self.frame_index = (self.frame_index + 1) % len(self.sprite_frames)
            self.last_frame_update = now

    def move(self, keys_pressed):
        if keys_pressed[self.controls['left']] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys_pressed[self.controls['right']] and self.rect.right < WIDTH:
            self.rect.x += self.speed
        if keys_pressed[self.controls['up']] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys_pressed[self.controls['down']] and self.rect.bottom < HEIGHT:
            self.rect.y += self.speed

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > PLAYER_SHOOT_DELAY:
            bullet = pygame.Rect(self.rect.centerx - BULLET_WIDTH // 2, self.rect.top, BULLET_WIDTH, BULLET_HEIGHT)
            self.last_shot = now
            self.rect.y = min(self.rect.y + PLAYER_RECOIL, HEIGHT - self.rect.height)
            return bullet
        return None

    def draw(self, surface):
        current_frame = self.sprite_frames[self.frame_index]
        if current_frame:
            surface.blit(current_frame, self.rect)
        else:
            pygame.draw.rect(surface, self.color, self.rect)

    def draw_health(self, surface, pos):
        if heart_sprite:
            x, y = pos
            full_hearts = int(self.health)
            for i in range(full_hearts):
                surface.blit(heart_sprite, (x - i * 40, y))
            if self.health - int(self.health) >= 0.5:
                half_heart = pygame.transform.scale(heart_sprite,
                                                    (int(heart_sprite.get_width() // 2), heart_sprite.get_height()))
                surface.blit(half_heart, (x - int(self.health) * 40, y))
        else:
            x, y = pos
            for i in range(int(self.health)):
                pygame.draw.circle(surface, (255, 0, 0), (x - i * 40, y + 15), 15)


class Enemy:
    def __init__(self, level):
        self.size = max(20, 50 - level)
        self.speed = (2 + level * 0.2) * difficulty_multiplier
        self.health = (50 + level * 5) * difficulty_multiplier
        self.rect = self.generate_position(self.size)
        self.color = (0, 200, 0)

    def generate_position(self, size):
        for _ in range(100):
            x = random.randint(0, WIDTH - size)
            y = random.randint(-150, -size)
            new_rect = pygame.Rect(x, y, size, size)
            if not any(new_rect.colliderect(e.rect) for e in enemies):
                return new_rect
        return pygame.Rect(x, y, size, size)

    def move(self):
        self.rect.y += int(self.speed)

    def draw(self, surface):
        if enemy_sprite:
            sprite = pygame.transform.scale(enemy_sprite, (self.rect.width, self.rect.height))
            surface.blit(sprite, self.rect)
        else:
            pygame.draw.rect(surface, self.color, self.rect)
        max_health = (50 + level * 5) * difficulty_multiplier
        health_ratio = self.health / max_health
        health_bar = pygame.Rect(self.rect.x, self.rect.y - 7, int(self.rect.width * health_ratio), 5)
        pygame.draw.rect(surface, (255, 0, 0), health_bar)


class Boss:
    def __init__(self, level):
        self.size = 150
        self.speed = (1 + level * 0.1) * difficulty_multiplier
        self.health = (500 + level * 100) * difficulty_multiplier
        self.rect = pygame.Rect(WIDTH // 2 - self.size // 2, -self.size, self.size, self.size // 2)
        self.color = (200, 0, 200)
        self.phase = 1
        self.move_direction = 1
        self.last_shot = pygame.time.get_ticks()
        self.shot_delay = 1500
        self.last_tank_spawn = pygame.time.get_ticks()
        self.tank_spawn_delay = 3000

    def move(self):
        if self.rect.y < 50:
            self.rect.y += int(self.speed)
        else:
            self.rect.x += int(self.speed * self.move_direction)
            if self.rect.right >= WIDTH or self.rect.left <= 0:
                self.move_direction *= -1

    def shoot(self, target_list):
        now = pygame.time.get_ticks()
        boss_bullets = []
        if now - self.last_shot > self.shot_delay:
            self.last_shot = now
            for target in target_list:
                dx = target.rect.centerx - self.rect.centerx
                dy = target.rect.centery - self.rect.centery
                dist = max(1, math.hypot(dx, dy))
                velx = dx / dist * 8
                vely = dy / dist * 8
                bullet = {"rect": pygame.Rect(self.rect.centerx, self.rect.centery, 8, 16),
                          "vel": (velx, vely)}
                boss_bullets.append(bullet)
        return boss_bullets

    def spawn_tank(self, target_list):
        now = pygame.time.get_ticks()
        if now - self.last_tank_spawn > self.tank_spawn_delay:
            self.last_tank_spawn = now
            tank = TankEnemy(self.rect.centerx, self.rect.centery, level, target_list)
            return tank
        return None

    def draw(self, surface):
        if boss_sprite:
            sprite = pygame.transform.scale(boss_sprite, (self.rect.width, self.rect.height))
            surface.blit(sprite, self.rect)
        else:
            pygame.draw.rect(surface, self.color, self.rect)
        max_health = (500 + level * 100) * difficulty_multiplier
        health_ratio = self.health / max_health
        health_bar = pygame.Rect(self.rect.x, self.rect.y - 10, int(self.rect.width * health_ratio), 8)
        pygame.draw.rect(surface, (255, 0, 0), health_bar)
        phase_text = FONT_SMALL.render(f'Phase: {self.phase}', True, (255, 255, 255))
        surface.blit(phase_text, (self.rect.x, self.rect.y - 30))


class OrbitingEnemy(Enemy):
    def __init__(self, boss, level):
        self.size = 20
        self.speed = 0
        self.health = 30 * difficulty_multiplier
        self.orbit_center = boss
        self.orbit_radius = random.randint(boss.rect.width // 2 + 20, boss.rect.width // 2 + 50)
        self.angle = random.uniform(0, 2 * math.pi)
        self.angular_speed = 0.02 * difficulty_multiplier
        self.last_shot = pygame.time.get_ticks()
        self.shot_delay = 2000
        cx = boss.rect.centerx
        cy = boss.rect.centery
        x = cx + self.orbit_radius * math.cos(self.angle) - self.size // 2
        y = cy + self.orbit_radius * math.sin(self.angle) - self.size // 2
        self.rect = pygame.Rect(int(x), int(y), self.size, self.size)
        self.color = (0, 150, 150)

    def move(self):
        self.angle += self.angular_speed
        cx = self.orbit_center.rect.centerx
        cy = self.orbit_center.rect.centery
        x = cx + self.orbit_radius * math.cos(self.angle) - self.size / 2
        y = cy + self.orbit_radius * math.sin(self.angle) - self.size / 2
        self.rect.x = int(x)
        self.rect.y = int(y)

    def shoot(self, target_list):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shot_delay:
            self.last_shot = now
            target = min(target_list, key=lambda p: math.hypot(p.rect.centerx - self.rect.centerx,
                                                               p.rect.centery - self.rect.centery))
            dx = target.rect.centerx - self.rect.centerx
            dy = target.rect.centery - self.rect.centery
            dist = max(1, math.hypot(dx, dy))
            velx = dx / dist * 6
            vely = dy / dist * 6
            bullet = {"rect": pygame.Rect(self.rect.centerx, self.rect.centery, 6, 12),
                      "vel": (velx, vely)}
            return [bullet]
        return []

    def draw(self, surface):
        if defender_sprite:
            sprite = pygame.transform.scale(defender_sprite, (self.rect.width, self.rect.height))
            surface.blit(sprite, self.rect)
        else:
            pygame.draw.rect(surface, self.color, self.rect)
        max_health = 30 * difficulty_multiplier
        health_ratio = self.health / max_health
        health_bar = pygame.Rect(self.rect.x, self.rect.y - 5, int(self.rect.width * health_ratio), 3)
        pygame.draw.rect(surface, (255, 0, 0), health_bar)


class TankEnemy(Enemy):
    def __init__(self, x, y, level, target_list):
        self.size = 30
        self.speed = (2.5 + level * 0.3) * difficulty_multiplier
        self.health = 1
        self.rect = pygame.Rect(x, y, self.size, self.size)
        self.color = (150, 0, 0)
        self.target_list = target_list

    def move(self):
        if self.target_list:
            target = min(self.target_list, key=lambda p: math.hypot(p.rect.centerx - self.rect.centerx,
                                                                    p.rect.centery - self.rect.centery))
            dx = target.rect.centerx - self.rect.centerx
            dy = target.rect.centery - self.rect.centery
            dist = max(1, math.hypot(dx, dy))
            vx = dx / dist * self.speed
            vy = dy / dist * self.speed
            self.rect.x += int(vx)
            self.rect.y += int(vy)

    def draw(self, surface):
        if tank_sprite:
            sprite = pygame.transform.scale(tank_sprite, (self.rect.width, self.rect.height))
            surface.blit(sprite, self.rect)
        else:
            pygame.draw.rect(surface, self.color, self.rect)
        max_health = 1
        health_ratio = self.health / max_health
        health_bar = pygame.Rect(self.rect.x, self.rect.y - 7, int(self.rect.width * health_ratio), 5)
        pygame.draw.rect(surface, (255, 0, 0), health_bar)


# ============= ГЛОБАЛЬНЫЕ списки объектов =============
players = []
player_bullets = []
enemies = []
boss_bullets = []
orbit_bullets = []

enemy_spawn_enabled = True
defender_shoot_index = 0


# ============= ФУНКЦИИ СПАВНА =============
def spawn_wave():
    global enemies, level, bg_surface, current_background_index
    update_music()  # Обновляем музыку в зависимости от уровня
    if level < 5:
        num = random.randint(3, 5)
    elif level < 10:
        num = random.randint(5, 10)
    else:
        num = random.randint(10, 15)
    if level % 5 == 0:
        boss_count = level // 5
        defenders_count = 3 + max(0, boss_count - 1)
        boss = Boss(level)
        enemies.append(boss)
        for _ in range(defenders_count):
            mini = generate_orbiting_enemy(boss, level)
            enemies.append(mini)
        if boss_count <= 4 and backgrounds:
            current_background_index = (boss_count - 1) % len(backgrounds)
            bg_surface = backgrounds[current_background_index]
        else:
            bg_surface = backgrounds[-1]
    else:
        for _ in range(num):
            enemies.append(generate_enemy(level))


def generate_enemy(level):
    new_enemy = Enemy(level)
    attempts = 0
    while any(new_enemy.rect.colliderect(e.rect) for e in enemies) and attempts < 100:
        new_enemy.rect = new_enemy.generate_position(new_enemy.size)
        attempts += 1
    return new_enemy


def generate_orbiting_enemy(boss, level):
    new_enemy = OrbitingEnemy(boss, level)
    attempts = 0
    while any(new_enemy.rect.colliderect(e.rect) for e in enemies) and attempts < 100:
        new_enemy = OrbitingEnemy(boss, level)
        attempts += 1
    return new_enemy


def update_enemies():
    global enemies
    for enemy in enemies[:]:
        enemy.move()
        if not isinstance(enemy, (OrbitingEnemy, Boss)) and enemy.rect.y > HEIGHT:
            try:
                enemies.remove(enemy)
            except ValueError:
                pass


def update_boss_shooting():
    global boss_bullets
    for enemy in enemies:
        if isinstance(enemy, Boss):
            new_bullets = enemy.shoot(players)
            boss_bullets.extend(new_bullets)
            tank = enemy.spawn_tank(players)
            if tank:
                enemies.append(tank)


def update_orbiting_shooting():
    global orbit_bullets, defender_shoot_index
    orbiters = [e for e in enemies if isinstance(e, OrbitingEnemy)]
    if orbiters:
        orbiters.sort(key=lambda e: e.rect.x)
        index = defender_shoot_index % len(orbiters)
        shooter = orbiters[index]
        now = pygame.time.get_ticks()
        if now - shooter.last_shot > shooter.shot_delay:
            new_bullets = shooter.shoot(players)
            orbit_bullets.extend(new_bullets)
            defender_shoot_index += 1


def update_boss_bullets():
    global boss_bullets, players
    for bullet in boss_bullets[:]:
        bullet["rect"].x += int(bullet["vel"][0])
        bullet["rect"].y += int(bullet["vel"][1])
        if (bullet["rect"].x < 0 or bullet["rect"].x > WIDTH or
                bullet["rect"].y < 0 or bullet["rect"].y > HEIGHT):
            try:
                boss_bullets.remove(bullet)
            except ValueError:
                pass
        else:
            for p in players:
                if bullet["rect"].colliderect(p.rect):
                    if pygame.time.get_ticks() > p.invulnerable_until:
                        p.health -= 1 * difficulty_multiplier
                        p.invulnerable_until = pygame.time.get_ticks() + 1000
                    try:
                        boss_bullets.remove(bullet)
                    except ValueError:
                        pass


def update_orbit_bullets():
    global orbit_bullets, players
    for bullet in orbit_bullets[:]:
        bullet["rect"].x += int(bullet["vel"][0])
        bullet["rect"].y += int(bullet["vel"][1])
        if (bullet["rect"].x < 0 or bullet["rect"].x > WIDTH or
                bullet["rect"].y < 0 or bullet["rect"].y > HEIGHT):
            try:
                orbit_bullets.remove(bullet)
            except ValueError:
                pass
        else:
            for p in players:
                if bullet["rect"].colliderect(p.rect):
                    if pygame.time.get_ticks() > p.invulnerable_until:
                        p.health -= 0.5 * difficulty_multiplier
                        p.invulnerable_until = pygame.time.get_ticks() + 1000
                    try:
                        orbit_bullets.remove(bullet)
                    except ValueError:
                        pass


# ============= ПАУЗА =============
def handle_pause():
    pause_font = FONT_LARGE.render("PAUSED", True, (255, 255, 255))
    screen.blit(pause_font, (WIDTH // 2 - pause_font.get_width() // 2, HEIGHT // 2 - pause_font.get_height() // 2))
    pygame.display.flip()
    paused = True
    while paused:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                paused = False
            elif event.type == pygame.QUIT:
                save_and_quit()
        clock.tick(60)


# ============= АНИМАЦИЯ ФОНА В МЕНЮ =============
menu_bg_frame_index = 0
menu_bg_last_update = pygame.time.get_ticks()
menu_bg_frame_duration = 100  # мс между кадрами меню


def update_menu_bg_animation():
    global menu_bg_frame_index, menu_bg_last_update
    now = pygame.time.get_ticks()
    if not menu_bg_frames:  # если список пуст, ничего не делаем
        return
    if now - menu_bg_last_update > menu_bg_frame_duration:
        menu_bg_frame_index = (menu_bg_frame_index + 1) % len(menu_bg_frames)
        menu_bg_last_update = now



# ============= РИСОВАНИЕ ИНТЕРФЕЙСА =============
def draw_game_interface():
    if bg_surface:
        screen.blit(bg_surface, (0, 0))
    else:
        screen.fill(bg_color)
    for p in players:
        p.draw(screen)
    for b in player_bullets:
        pygame.draw.rect(screen, (255, 50, 50), b)
    for enemy in enemies:
        enemy.draw(screen)
    for bullet in boss_bullets:
        pygame.draw.rect(screen, (255, 255, 0), bullet["rect"])
    for bullet in orbit_bullets:
        pygame.draw.rect(screen, (200, 200, 50), bullet["rect"])
    info = FONT_MEDIUM.render(f"Score: {score}   Level: {level}", True, (255, 255, 255))
    screen.blit(info, (5, 5))
    if game_mode == "single":
        players[0].draw_health(screen, (WIDTH - 150, 5))
    else:
        players[0].draw_health(screen, (WIDTH - 150, 5))
        players[1].draw_health(screen, (WIDTH - 150, 50))
    pygame.display.flip()


# ============= ЛОГИКА СТОЛКНОВЕНИЙ =============
def check_collisions():
    global player_bullets, enemies, score
    for bullet in player_bullets[:]:
        for enemy in enemies[:]:
            if bullet.colliderect(enemy.rect):
                enemy.health -= 40 * score_multiplier
                if enemy.health <= 0:
                    if isinstance(enemy, Boss):
                        score += 10 * score_multiplier
                        for p in players:
                            if p.health < PLAYER_MAX_HEALTH:
                                p.health = min(p.health + 1, PLAYER_MAX_HEALTH)
                        try:
                            enemies.remove(enemy)
                        except ValueError:
                            pass
                    else:
                        score += 1 * score_multiplier
                        try:
                            enemies.remove(enemy)
                        except ValueError:
                            pass
                try:
                    player_bullets.remove(bullet)
                except ValueError:
                    pass
                break
    for enemy in enemies[:]:
        for p in players:
            if enemy.rect.colliderect(p.rect):
                if isinstance(enemy, Boss):
                    if pygame.time.get_ticks() > p.invulnerable_until:
                        p.health -= 1 * difficulty_multiplier
                        p.invulnerable_until = pygame.time.get_ticks() + 1000
                else:
                    if pygame.time.get_ticks() > p.invulnerable_until:
                        p.health -= 1 * difficulty_multiplier
                        p.invulnerable_until = pygame.time.get_ticks() + 1000
                    try:
                        if not isinstance(enemy, Boss):
                            enemies.remove(enemy)
                    except ValueError:
                        pass
    if game_mode == "single":
        if players[0].health < 1:
            end_game()
    else:
        if players[0].health < 1 or players[1].health < 1:
            end_game()


# ============= ЭКРАН МЕНЮ =============
menu_bg_frames = []
for i in range(1, 13):
    try:
        frame = pygame.image.load(f"{i}.png").convert()
        frame = pygame.transform.scale(frame, (WIDTH, HEIGHT))
        menu_bg_frames.append(frame)
    except Exception as e:
        print(f"Ошибка загрузки {i}.png:", e)
if not menu_bg_frames:
    try:
        menu_bg = pygame.image.load("menu_bg.png").convert()
        menu_bg = pygame.transform.scale(menu_bg, (WIDTH, HEIGHT))
        menu_bg_frames = [menu_bg]
    except Exception as e:
        print("Ошибка загрузки menu_bg.png:", e)
        menu_bg_frames = []
menu_bg_frame_index = 0
menu_bg_last_update = pygame.time.get_ticks()
menu_bg_frame_duration = 100


def draw_main_menu():
    update_menu_bg_animation()
    if menu_bg_frames:
        screen.blit(menu_bg_frames[menu_bg_frame_index], (0, 0))
    else:
        screen.fill((10, 10, 50))
    title = FONT_LARGE.render("Shooter Game", True, (255, 255, 255))
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
    btn_single = FONT_MEDIUM.render("Одиночная игра", True, (255, 255, 255))
    btn_multi = FONT_MEDIUM.render("Игра с другом", True, (255, 255, 255))
    btn_top10 = FONT_MEDIUM.render("Топ 10", True, (255, 255, 255))
    btn_quit = FONT_MEDIUM.render("Выход", True, (255, 255, 255))
    screen.blit(btn_single, (WIDTH // 2 - btn_single.get_width() // 2, 200))
    screen.blit(btn_multi, (WIDTH // 2 - btn_multi.get_width() // 2, 260))
    screen.blit(btn_top10, (WIDTH // 2 - btn_top10.get_width() // 2, 320))
    screen.blit(btn_quit, (WIDTH // 2 - btn_quit.get_width() // 2, 380))
    instructions = [
        "Управление (Одиночная игра): стрелки для движения, пробел для выстрела.",
        "Управление (Игра с другом): игрок 1 – стрелки и пробел, игрок 2 – WASD и F.",
        "ESC для выхода, P для паузы."
    ]
    y = 450
    for line in instructions:
        instr = FONT_SMALL.render(line, True, (200, 200, 200))
        screen.blit(instr, (WIDTH // 2 - instr.get_width() // 2, y))
        y += 25
    pygame.display.flip()


def handle_main_menu_events():
    global current_state, game_mode
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_and_quit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            if WIDTH // 2 - 150 < x < WIDTH // 2 + 150:
                if 200 < y < 230:
                    game_mode = "single"
                    current_state = STATE_GAME
                    start_game()
                elif 260 < y < 290:
                    game_mode = "multi"
                    current_state = STATE_GAME
                    start_game()
                elif 320 < y < 350:
                    current_state = STATE_TOP10
                elif 380 < y < 410:
                    save_and_quit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                save_and_quit()


def draw_top10_screen():
    screen.fill((20, 20, 70))
    title = FONT_LARGE.render("Топ 10", True, (255, 255, 255))
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
    y = 150
    if top10_scores:
        for i, scr in enumerate(top10_scores[:10], start=1):
            line = FONT_MEDIUM.render(f"{i}. {scr}", True, (255, 255, 0))
            screen.blit(line, (WIDTH // 2 - line.get_width() // 2, y))
            y += 40
    else:
        line = FONT_MEDIUM.render("Нет записей", True, (255, 255, 255))
        screen.blit(line, (WIDTH // 2 - line.get_width() // 2, y))
    btn_back = FONT_MEDIUM.render("Назад", True, (255, 255, 255))
    screen.blit(btn_back, (WIDTH // 2 - btn_back.get_width() // 2, 500))
    pygame.display.flip()


def handle_top10_events():
    global current_state
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_and_quit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            if WIDTH // 2 - 150 < x < WIDTH // 2 + 150 and 500 < y < 540:
                current_state = STATE_MENU
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                current_state = STATE_MENU


def start_game():
    global players, player_bullets, enemies, boss_bullets, orbit_bullets, level, score, difficulty_multiplier, regen_threshold, defender_shoot_index, bg_surface, current_background_index
    players = []
    player_bullets = []
    enemies = []
    boss_bullets = []
    orbit_bullets = []
    level = START_LEVEL
    score = 0
    regen_threshold = 20
    difficulty_multiplier = 2 if game_mode == "multi" else 1
    defender_shoot_index = 0
    # При запуске новой игры сбрасываем фон игровых уровней на первый (bg1.png)
    if backgrounds:
        current_background_index = 0
        bg_surface = backgrounds[0]
    if game_mode == "single":
        controls = {
            'left': pygame.K_LEFT,
            'right': pygame.K_RIGHT,
            'up': pygame.K_UP,
            'down': pygame.K_DOWN,
            'shoot': pygame.K_SPACE
        }
        p = Player(WIDTH // 2 - PLAYER_SIZE // 2, HEIGHT - PLAYER_SIZE - 10, (50, 150, 255), controls)
        players.append(p)
    else:
        controls1 = {
            'left': pygame.K_LEFT,
            'right': pygame.K_RIGHT,
            'up': pygame.K_UP,
            'down': pygame.K_DOWN,
            'shoot': pygame.K_SPACE
        }
        controls2 = {
            'left': pygame.K_a,
            'right': pygame.K_d,
            'up': pygame.K_w,
            'down': pygame.K_s,
            'shoot': pygame.K_f
        }
        p1 = Player(WIDTH // 4 - PLAYER_SIZE // 2, HEIGHT - PLAYER_SIZE - 10, (50, 150, 255), controls1)
        p2 = Player(WIDTH * 3 // 4 - PLAYER_SIZE // 2, HEIGHT - PLAYER_SIZE - 10, (255, 100, 100), controls2)
        players.extend([p1, p2])
    spawn_wave()


def game_loop():
    global current_state, player_bullets, score, level, regen_threshold, is_paused
    while current_state == STATE_GAME:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_and_quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    current_state = STATE_MENU
                if event.key == pygame.K_p:
                    handle_pause()
                for p in players:
                    if event.key == p.controls['shoot']:
                        bullet = p.shoot()
                        if bullet:
                            player_bullets.append(bullet)
        for p in players:
            p.move(pygame.key.get_pressed())
            p.update()
        for bullet in player_bullets[:]:
            bullet.y -= BULLET_SPEED
            if bullet.y < 0:
                try:
                    player_bullets.remove(bullet)
                except ValueError:
                    pass
        update_enemies()
        update_boss_shooting()
        update_boss_bullets()
        update_orbiting_shooting()
        update_orbit_bullets()
        check_collisions()
        if score >= regen_threshold:
            for p in players:
                if p.health < PLAYER_MAX_HEALTH:
                    p.health = min(p.health + 1, PLAYER_MAX_HEALTH)
            regen_threshold += 20
        if enemy_spawn_enabled and not enemies:
            level += 1
            spawn_wave()
        draw_game_interface()
        clock.tick(60)
    if current_state == STATE_GAMEOVER:
        game_over_screen()


def end_game():
    global current_state, score, top10_scores, highscore
    if score > highscore:
        highscore = score
        with open("highscore.txt", "w") as f:
            f.write(str(highscore))
    top10_scores.append(score)
    top10_scores.sort(reverse=True)
    with open("top10.txt", "w") as f:
        for s in top10_scores[:10]:
            f.write(f"{s}\n")
    current_state = STATE_GAMEOVER


def game_over_screen():
    global current_state
    while current_state == STATE_GAMEOVER:
        if gameover_bg:
            screen.blit(gameover_bg, (0, 0))
        else:
            screen.fill((50, 0, 0))
        over_text = FONT_LARGE.render("GAME OVER", True, (255, 255, 255))
        score_text = FONT_MEDIUM.render(f"Ваш счёт: {score}", True, (255, 255, 0))
        btn_restart = FONT_MEDIUM.render("Начать заново", True, (255, 255, 255))
        btn_menu = FONT_MEDIUM.render("Главное меню", True, (255, 255, 255))
        screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, 100))
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 180))
        screen.blit(btn_restart, (WIDTH // 2 - btn_restart.get_width() // 2, 300))
        screen.blit(btn_menu, (WIDTH // 2 - btn_menu.get_width() // 2, 360))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_and_quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if WIDTH // 2 - 150 < x < WIDTH // 2 + 150:
                    if 300 < y < 340:
                        start_game()
                        current_state = STATE_GAME
                        game_loop()
                    elif 360 < y < 400:
                        current_state = STATE_MENU
        clock.tick(60)


def save_and_quit():
    pygame.quit()
    sys.exit()


def main():
    global current_state
    while True:
        if current_state == STATE_MENU:
            try:
                pygame.mixer.music.load("a31df44c3944ea6.mp3")
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
                current_music = "normal"
            except Exception as e:
                print("Ошибка загрузки музыки в меню:", e)
            update_menu_bg_animation()
            if menu_bg_frames:
                screen.blit(menu_bg_frames[menu_bg_frame_index], (0, 0))
            else:
                screen.fill((10, 10, 50))
            draw_main_menu()
            handle_main_menu_events()
        elif current_state == STATE_TOP10:
            draw_top10_screen()
            handle_top10_events()
        elif current_state == STATE_GAME:
            start_game()
            game_loop()
        clock.tick(60)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main()
