import os
import csv
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional

import pygame

# --------------------------- Config --------------------------- #
TITLE = "Snake: Korean Vocab Edition"
CELL = 32                     # pixel size of one grid cell
GRID_W, GRID_H = 20, 15       # grid size in cells -> 640x480 window
WIDTH, HEIGHT = GRID_W * CELL, GRID_H * CELL
FPS_BASE = 3                  # base speed (frames per second for snake moves) -- slowed down
FONT_NAME = None              # use default; you can set to a .ttf path
HUD_HEIGHT = 48               # top HUD padding (drawn within game area, not extra)
LIVES_START = 3
SCORE_CORRECT = 10
SCORE_WRONG = -5
MAX_DISTRACTORS_PER_LEVEL = 6 # cap the number of distractors

# Colors
BG = (91, 15, 113)
GRID_DARK = (18, 15, 113)
SNAKE_HEAD = (15, 3, 9)
SNAKE_BODY = (125, 218, 88)
ITEM_KR = (255, 222, 89)
ITEM_EN = (93, 226, 231)
HUD_TEXT = (239, 195, 202)
ITEM_BG = (25, 65, 100)
SHADOW = (0, 0, 0)

# --------------------------- Data --------------------------- #

@dataclass
class Vocab:
    korean: str
    english: str

@dataclass
class Item:
    text: str
    lang: str            # "korean" or "english"
    is_correct: bool     # True only for the target korean item
    pos: Tuple[int, int] # grid coordinate (col,row)
    rect: Optional[pygame.Rect] = None  # pixel rect after render (set each frame)

# Built-in fallback vocab
BUILTIN_VOCAB: List[Vocab] = [
    Vocab("mul", "water"),
    Vocab("annyeong", "hello"),
    Vocab("gamsahamnida", "thank you"),
    Vocab("bap", "rice"),
    Vocab("sarang", "love"),
    Vocab("mianhae", "sorry"),
    Vocab("nae", "yes"),
    Vocab("ani", "no"),
    Vocab("juseyo", "please"),
    Vocab("eolmayo", "how much"),
    Vocab("jip", "house"),
    Vocab("sigan", "time"),
    Vocab("saram","person"),
    Vocab("chingu","friend"),
    Vocab("gajok","family"),
    Vocab("hakgyo","school"),
    Vocab("hoesa","office"),
    Vocab("byeongwon","hospital"),
    Vocab("sijang","market"),
    Vocab("eumsik","food"),
    Vocab("oneul","today"),
    Vocab("naeil","tomorrow"),
    Vocab("eoje","yesterday"),
    Vocab("nalssi","weather"),
    Vocab("hana","one"),
    Vocab("dul","two"),
    Vocab("set","three"),
    Vocab("yeol","ten"),
    Vocab("baek","hundred"),
    Vocab("sarang","love"),
    Vocab("haengbok","happiness"),
    Vocab("seulpeum","sadness"),
    Vocab("hwa","anger"),
    Vocab("utda","smile"),
    Vocab("meokda","to_eat"),
    Vocab("masida","to_drink"),
    Vocab("gada","to_go"),
    Vocab("oda","to_come"),
    Vocab("jada","to sleep"),
    Vocab("gi=ongwon","park"),
    Vocab("doseogwan","library"),
    Vocab("gyohoe","church"),
    Vocab("gage","store"),
    Vocab("eunhaeng","bank"),
    Vocab("ucheguk","post office"),
    Vocab("sikdang","restaurant"),
    Vocab("kape","cafe"),
    Vocab("gonghang","airport"),
    Vocab("bada","sea"),
    Vocab("chaek","book"),
]

# --------------------------- Helpers --------------------------- #

def load_vocab_csv(path: str = "vocab.csv") -> List[Vocab]:
    if not os.path.exists(path):
        return []
    out: List[Vocab] = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            k = (row.get('korean') or '').strip()
            e = (row.get('english') or '').strip()
            if k and e:
                out.append(Vocab(k, e))
    return out


def grid_to_px(col: int, row: int) -> Tuple[int, int]:
    return col * CELL, row * CELL


def random_free_cell(occupied: set) -> Tuple[int, int]:
    while True:
        p = (random.randrange(GRID_W), random.randrange(GRID_H))
        if p not in occupied:
            return p


def level_from_score(score: int) -> int:
    # Every 50 points, level up (1-based)
    return max(1, score // 50 + 1)


def speed_from_level(level: int) -> int:
    # Increase speed modestly with level
    return FPS_BASE + (level - 1) * 2


def distractor_count_from_level(level: int) -> int:
    return min(2 + level, MAX_DISTRACTORS_PER_LEVEL)


# --------------------------- Game --------------------------- #

class SnakeGame:
    def __init__(self, screen: pygame.Surface, vocab: List[Vocab]):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(FONT_NAME, 20)
        self.font_small = pygame.font.Font(FONT_NAME, 16)
        self.title_font = pygame.font.Font(FONT_NAME, 24)
        self.reset(vocab)

    def reset(self, vocab: List[Vocab]):
        self.vocab = vocab[:] if vocab else BUILTIN_VOCAB[:]
        random.shuffle(self.vocab)
        # Snake starts center
        start = (GRID_W // 2, GRID_H // 2)
        self.snake: List[Tuple[int, int]] = [start, (start[0]-1, start[1]), (start[0]-2, start[1])]
        self.direction = (1, 0)  # moving right
        self.pending_dir: Optional[Tuple[int, int]] = None
        self.move_timer = 0.0
        self.score = 0
        self.lives = LIVES_START
        self.game_over = False
        self.paused = False

        self.target: Optional[Vocab] = None
        self.items: List[Item] = []
        self.spawn_new_round()

    # --------------- Round/Items --------------- #
    def spawn_new_round(self):
        # Choose a new target different from previous if possible
        prev = self.target
        choices = [v for v in self.vocab if v != prev] or self.vocab
        self.target = random.choice(choices)
        self.items.clear()

        occupied = set(self.snake)
        # Correct Korean item for the target
        pos_correct = random_free_cell(occupied)
        occupied.add(pos_correct)
        self.items.append(Item(text=self.target.korean, lang='korean', is_correct=True, pos=pos_correct))

        # Distractors: mix of wrong korean + some english words
        level = level_from_score(self.score)
        n_distractors = distractor_count_from_level(level)

        pool_wrong_kr = [v.korean for v in self.vocab if v.korean != self.target.korean]
        pool_en = [v.english for v in self.vocab]
        random.shuffle(pool_wrong_kr)
        random.shuffle(pool_en)

        for i in range(n_distractors):
            if i % 2 == 0 and pool_wrong_kr:
                text = pool_wrong_kr.pop()
                lang = 'korean'
            else:
                text = pool_en.pop() if pool_en else random.choice(pool_wrong_kr or [self.target.korean])
                lang = 'english'
            pos = random_free_cell(occupied)
            occupied.add(pos)
            self.items.append(Item(text=text, lang=lang, is_correct=False, pos=pos))

    # --------------- Update/Draw --------------- #
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE,):
                    pygame.quit()
                    raise SystemExit
                if event.key in (pygame.K_p,):
                    self.paused = not self.paused
                if self.game_over and event.key in (pygame.K_r,):
                    self.reset(self.vocab)
                    return

                # Movement
                if not self.game_over and not self.paused:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.set_pending_dir((0, -1))
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.set_pending_dir((0, 1))
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        self.set_pending_dir((-1, 0))
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.set_pending_dir((1, 0))

    def set_pending_dir(self, d: Tuple[int, int]):
        # Prevent reversing into itself
        if len(self.snake) >= 2:
            head = self.snake[0]
            neck = self.snake[1]
            cur = (head[0]-neck[0], head[1]-neck[1])
            if (d[0] == -cur[0] and d[1] == -cur[1]):
                return
        self.pending_dir = d

    def step(self, dt: float):
        if self.game_over or self.paused:
            return
        level = level_from_score(self.score)
        speed = speed_from_level(level)
        self.move_timer += dt
        step_time = 1.0 / float(speed)
        while self.move_timer >= step_time:
            self.move_timer -= step_time
            self.move_snake()

    def move_snake(self):
        if self.pending_dir:
            self.direction = self.pending_dir
            self.pending_dir = None
        head = self.snake[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])

        # Wall collision
        if not (0 <= new_head[0] < GRID_W and 0 <= new_head[1] < GRID_H):
            self.game_over = True
            return
        # Self collision
        if new_head in self.snake:
            self.game_over = True
            return

        self.snake.insert(0, new_head)

        # Check item collisions (pixel rect collision using approximate rect for head)
        head_px = pygame.Rect(*grid_to_px(*new_head), CELL, CELL)
        ate_any = False
        to_remove = None
        for item in self.items:
            # Create/update item's pixel rect from its text render size around its cell center
            # We'll compute rect later in draw; for collision during logic we create a similar rect
            ipx, ipy = grid_to_px(*item.pos)
            text_surf = self.font.render(item.text, True, ITEM_KR if item.lang == 'korean' else ITEM_EN)
            rect = text_surf.get_rect()
            rect.center = (ipx + CELL // 2, ipy + CELL // 2)
            if head_px.colliderect(rect):
                ate_any = True
                to_remove = item
                if item.is_correct and item.lang == 'korean' and item.text == self.target.korean:
                    self.score += SCORE_CORRECT
                    # Grow: keep tail
                    self.spawn_new_round()
                else:
                    # Wrong item penalty: lose life and shrink if possible
                    self.score = max(0, self.score + SCORE_WRONG)
                    self.lives -= 1
                    if len(self.snake) > 3:
                        self.snake.pop()
                    if self.lives < 0:
                        self.game_over = True
                break

        if not ate_any:
            # Move normally: remove tail
            self.snake.pop()

    def draw_grid(self):
        self.screen.fill(BG)
        # Subtle grid
        for x in range(0, WIDTH, CELL):
            pygame.draw.line(self.screen, GRID_DARK, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, CELL):
            pygame.draw.line(self.screen, GRID_DARK, (0, y), (WIDTH, y))

    def draw_snake(self):
        for i, (cx, cy) in enumerate(self.snake):
            x, y = grid_to_px(cx, cy)
            rect = pygame.Rect(x+2, y+2, CELL-4, CELL-4)
            color = SNAKE_HEAD if i == 0 else SNAKE_BODY
            pygame.draw.rect(self.screen, color, rect, border_radius=6)

    def draw_items(self):
        for item in self.items:
            col = ITEM_KR if item.lang == 'korean' else ITEM_EN
            ipx, ipy = grid_to_px(*item.pos)
            # Render text & a subtle background pill
            text = self.font.render(item.text, True, col)
            pad_x, pad_y = 8, 4
            bg_rect = text.get_rect()
            bg_rect.center = (ipx + CELL // 2, ipy + CELL // 2)
            bg_rect.inflate_ip(pad_x*2, pad_y*2)
            # Shadow
            shadow = bg_rect.copy(); shadow.move_ip(2, 2)
            pygame.draw.rect(self.screen, SHADOW, shadow, border_radius=10)
            pygame.draw.rect(self.screen, ITEM_BG, bg_rect, border_radius=10)
            # Text on top
            self.screen.blit(text, text.get_rect(center=bg_rect.center))
            # Store rect for potential external use
            item.rect = bg_rect

    def draw_hud(self):
        # Top HUD: Target English, score, lives, level
        level = level_from_score(self.score)
        target_text = f"Find: {self.target.english}" if self.target else "Find: —"
        info_text = f"Score: {self.score}   Lives: {self.lives}   Level: {level}"

        left = self.title_font.render(target_text, True, HUD_TEXT)
        right = self.font_small.render(info_text, True, HUD_TEXT)
        self.screen.blit(left, (12, 8))
        self.screen.blit(right, (12, 12 + left.get_height()))

    def draw_overlay(self):
        if self.paused:
            self.draw_center_message("Paused — Press P to resume")
        if self.game_over:
            self.draw_center_message("Game Over — Press R to restart")

    def draw_center_message(self, text: str):
        surf = self.title_font.render(text, True, HUD_TEXT)
        rect = surf.get_rect(center=(WIDTH//2, HEIGHT//2))
        # backdrop
        back = rect.inflate(20, 20)
        pygame.draw.rect(self.screen, (0,0,0), back, border_radius=12)
        pygame.draw.rect(self.screen, (70,70,90), back, 2, border_radius=12)
        self.screen.blit(surf, rect)

    def draw(self):
        self.draw_grid()
        self.draw_snake()
        self.draw_items()
        self.draw_hud()
        self.draw_overlay()
        pygame.display.flip()

    # --------------- Main loop --------------- #
    def run(self):
        # Use a fixed-timestep mover driven by dt
        while True:
            dt = self.clock.tick(60) / 1000.0
            self.handle_input()
            self.step(dt)
            self.draw()


# --------------------------- Main --------------------------- #

def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    vocab = load_vocab_csv()
    if not vocab:
        vocab = BUILTIN_VOCAB

    game = SnakeGame(screen, vocab)
    game.run()


if __name__ == '__main__':
    main()

