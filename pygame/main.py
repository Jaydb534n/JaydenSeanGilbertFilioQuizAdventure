import pygame
import sys
import os
import random
from data import questions

# --- CONFIGURATION ---
pygame.init()
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Quiz Adventure: Global Edition")

# --- MODERN COLOR PALETTE ---
# Slate / Dark Theme
BG_COLOR = (15, 23, 42)      # Slate 900
PANEL_COLOR = (30, 41, 59)   # Slate 800
TEXT_WHITE = (248, 250, 252) # Slate 50
TEXT_GRAY = (148, 163, 184)  # Slate 400

# Accents
ACCENT_BLUE = (59, 130, 246) # Blue 500
ACCENT_PURPLE = (147, 51, 234) # Purple 600
ACCENT_GREEN = (16, 185, 129) # Emerald 500
ACCENT_RED = (239, 68, 68)    # Red 500
ACCENT_YELLOW = (234, 179, 8) # Yellow 500

# --- FONTS ---
try:
    font_xs = pygame.font.SysFont("segoeui", 16)
    font_sm = pygame.font.SysFont("segoeui", 20)
    font_md = pygame.font.SysFont("segoeui", 28, bold=True)
    font_lg = pygame.font.SysFont("segoeui", 48, bold=True)
    font_xl = pygame.font.SysFont("segoeui", 72, bold=True)
except:
    font_xs = pygame.font.Font(None, 20)
    font_sm = pygame.font.Font(None, 24)
    font_md = pygame.font.Font(None, 32)
    font_lg = pygame.font.Font(None, 60)
    font_xl = pygame.font.Font(None, 80)

# --- ASSET LOADER ---
def load_image(filename, scale_size=None):
    path = os.path.join("assets", filename)
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            if scale_size:
                img = pygame.transform.scale(img, scale_size)
            return img
        except:
            return None
    return None

player_img = load_image("player.png", (60, 60))
bg_img = load_image("bg.png", (WIDTH, HEIGHT))

# --- UTILS ---
def draw_rounded_rect(surface, color, rect, radius=10):
    pygame.draw.rect(surface, color, rect, border_radius=radius)

def draw_text_centered(text, font, color, surface, x, y):
    text_obj = font.render(text, True, color)
    rect = text_obj.get_rect(center=(x, y))
    surface.blit(text_obj, rect)

def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        if font.size(test_line)[0] < max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))
    return lines

# --- GAME CLASS ---
class Game:
    def __init__(self):
        self.state = "MENU" # MENU, RUNNING, QUIZ, GAMEOVER
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.reset_game()

    def reset_game(self):
        self.score = 0
        self.health = 3
        self.streak = 0
        self.level = 1
        
        # Player Position
        self.player_x = 100
        self.player_y = 400
        self.ground_y = 460
        
        # Scrolling (Parallax)
        self.scroll_x = 0
        self.scroll_speed = 3
        
        # Quiz System
        self.current_q_index = 0
        self.distance_to_next_quiz = 0
        self.quiz_timer = 15
        self.quiz_active = None
        self.feedback = "" # "CORRECT" or "WRONG"
        self.feedback_timer = 0
        
        # Powerups
        self.powerups = {"50:50": 1, "freeze": 1}
        self.disabled_options = []
        self.is_frozen = False

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.fps)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if self.state == "MENU":
                    if event.key == pygame.K_RETURN:
                        self.reset_game()
                        self.state = "RUNNING"
                
                elif self.state == "GAMEOVER":
                    if event.key == pygame.K_RETURN:
                        self.state = "MENU"

                elif self.state == "QUIZ":
                    if self.feedback == "": # Only accept input if not showing feedback
                        # Answer Options 1-4
                        if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                            idx = event.key - pygame.K_1
                            if idx not in self.disabled_options:
                                self.check_answer(idx)
                        
                        # Powerups
                        if event.key == pygame.K_f: # F for Fifty-Fifty
                            self.use_fifty_fifty()
                        if event.key == pygame.K_t: # T for Time Freeze
                            self.use_time_freeze()

    def check_answer(self, selected_idx):
        correct_idx = self.quiz_active['answer']
        
        if selected_idx == correct_idx:
            # Correct logic
            bonus = int(self.quiz_timer * 10) + (self.streak * 50)
            self.score += 100 + bonus
            self.streak += 1
            self.feedback = "CORRECT!"
            self.feedback_color = ACCENT_GREEN
        else:
            # Wrong logic
            self.health -= 1
            self.streak = 0
            self.feedback = "WRONG!"
            self.feedback_color = ACCENT_RED
        
        self.feedback_timer = pygame.time.get_ticks()

    def use_fifty_fifty(self):
        if self.powerups["50:50"] > 0 and not self.disabled_options:
            correct = self.quiz_active['answer']
            wrong_indices = [i for i in range(4) if i != correct]
            random.shuffle(wrong_indices)
            self.disabled_options = wrong_indices[:2] # Disable 2 wrong answers
            self.powerups["50:50"] -= 1

    def use_time_freeze(self):
        if self.powerups["freeze"] > 0 and not self.is_frozen:
            self.is_frozen = True
            self.powerups["freeze"] -= 1

    def update(self):
        if self.state == "RUNNING":
            # Auto Run
            self.scroll_x += self.scroll_speed + (self.level * 0.5)
            self.distance_to_next_quiz += self.scroll_speed
            
            # Trigger Quiz every 600 pixels
            if self.distance_to_next_quiz > 600:
                self.distance_to_next_quiz = 0
                self.start_quiz()

        elif self.state == "QUIZ":
            # Timer logic
            if not self.feedback and not self.is_frozen:
                self.quiz_timer -= 1 / self.fps
                if self.quiz_timer <= 0:
                    self.check_answer(-1) # Timeout treated as wrong

            # Feedback delay handling
            if self.feedback:
                if pygame.time.get_ticks() - self.feedback_timer > 2000: # 2 seconds delay
                    if self.health <= 0:
                        self.state = "GAMEOVER"
                    else:
                        self.next_level()

    def start_quiz(self):
        self.state = "QUIZ"
        self.quiz_active = questions[self.current_q_index]
        self.quiz_timer = 15
        self.feedback = ""
        self.disabled_options = []
        self.is_frozen = False

    def next_level(self):
        self.current_q_index = (self.current_q_index + 1) % len(questions)
        if (self.current_q_index + 1) % 3 == 0:
            self.level += 1
        self.state = "RUNNING"

    # --- DRAWING FUNCTIONS ---
    def draw(self):
        SCREEN.fill(BG_COLOR)
        
        # 1. Background (Parallax Effect)
        rel_x = self.scroll_x % WIDTH
        # Draw background logic here (simplified for generic rects/image)
        if bg_img:
            SCREEN.blit(bg_img, (-rel_x, 0))
            SCREEN.blit(bg_img, (WIDTH - rel_x, 0))
        else:
            # Draw starry sky / gradient simulation
            for i in range(50):
                pygame.draw.circle(SCREEN, (255,255,255), ((i * 3752 + int(self.scroll_x * 0.2)) % WIDTH, (i * 324) % 400), 2)
            
            # Ground
            pygame.draw.rect(SCREEN, (10, 20, 30), (0, self.ground_y, WIDTH, HEIGHT - self.ground_y))
            pygame.draw.line(SCREEN, ACCENT_GREEN, (0, self.ground_y), (WIDTH, self.ground_y), 4)

        # 2. Player
        if self.state in ["RUNNING", "QUIZ"]:
            bounce = abs(pygame.time.get_ticks() % 500 - 250) / 10 if self.state == "RUNNING" else 0
            if player_img:
                SCREEN.blit(player_img, (self.player_x, self.player_y - bounce))
            else:
                # Fallback Player Shape
                draw_rounded_rect(SCREEN, ACCENT_BLUE, (self.player_x, self.player_y - bounce, 50, 50), 8)
                # Goggles
                pygame.draw.rect(SCREEN, (200,240,255), (self.player_x + 30, self.player_y - bounce + 10, 15, 10))

        # 3. HUD
        if self.state in ["RUNNING", "QUIZ"]:
            self.draw_hud()

        # 4. State Specific Overlays
        if self.state == "MENU":
            self.draw_menu()
        elif self.state == "QUIZ":
            self.draw_quiz()
        elif self.state == "GAMEOVER":
            self.draw_gameover()

        pygame.display.flip()

    def draw_hud(self):
        # Top Bar Panel
        draw_rounded_rect(SCREEN, PANEL_COLOR, (10, 10, WIDTH-20, 60), 15)
        
        # Health
        for i in range(3):
            color = ACCENT_RED if i < self.health else (60, 60, 60)
            pygame.draw.circle(SCREEN, color, (40 + i*30, 40), 10)

        # Score & Level
        draw_text_centered(f"SCORE: {self.score}", font_md, TEXT_WHITE, SCREEN, WIDTH//2, 40)
        draw_text_centered(f"LVL {self.level}", font_md, ACCENT_YELLOW, SCREEN, WIDTH - 60, 40)

    def draw_menu(self):
        # Overlay
        s = pygame.Surface((WIDTH, HEIGHT))
        s.set_alpha(200)
        s.fill(BG_COLOR)
        SCREEN.blit(s, (0,0))

        draw_text_centered("QUIZ ADVENTURE", font_xl, ACCENT_BLUE, SCREEN, WIDTH//2, 200)
        draw_text_centered("Global Edition", font_md, TEXT_GRAY, SCREEN, WIDTH//2, 260)
        
        # Start Button
        btn_rect = pygame.Rect(WIDTH//2 - 100, 350, 200, 60)
        draw_rounded_rect(SCREEN, ACCENT_PURPLE, btn_rect, 15)
        draw_text_centered("PRESS ENTER", font_md, TEXT_WHITE, SCREEN, WIDTH//2, 380)

    def draw_quiz(self):
        # Dim Background
        s = pygame.Surface((WIDTH, HEIGHT))
        s.set_alpha(180)
        s.fill((0,0,0))
        SCREEN.blit(s, (0,0))

        # Quiz Panel
        panel_rect = pygame.Rect(50, 50, WIDTH-100, HEIGHT-100)
        draw_rounded_rect(SCREEN, PANEL_COLOR, panel_rect, 20)
        pygame.draw.rect(SCREEN, (60,70,90), panel_rect, 2, border_radius=20) # Border

        # Category & Timer
        draw_text_centered(self.quiz_active['category'], font_sm, ACCENT_PURPLE, SCREEN, WIDTH//2, 90)
        
        timer_color = ACCENT_RED if self.quiz_timer < 5 else ACCENT_BLUE
        draw_text_centered(f"{int(self.quiz_timer)}s", font_lg, timer_color, SCREEN, WIDTH - 100, 90)

        # Question Text
        lines = wrap_text(self.quiz_active['question'], font_md, WIDTH - 150)
        for i, line in enumerate(lines):
            draw_text_centered(line, font_md, TEXT_WHITE, SCREEN, WIDTH//2, 160 + (i*35))

        # Options
        start_y = 300
        for i, opt in enumerate(self.quiz_active['options']):
            if i in self.disabled_options:
                color = (60, 60, 60)
                text_col = (100, 100, 100)
            else:
                color = (50, 60, 80)
                text_col = TEXT_WHITE

            rect = pygame.Rect(100, start_y + (i * 60), WIDTH-200, 50)
            draw_rounded_rect(SCREEN, color, rect, 10)
            
            # Number circle
            pygame.draw.circle(SCREEN, (80, 90, 110), (130, start_y + (i * 60) + 25), 15)
            draw_text_centered(str(i+1), font_sm, TEXT_WHITE, SCREEN, 130, start_y + (i * 60) + 25)
            
            # Option Text
            text_surf = font_sm.render(opt, True, text_col)
            SCREEN.blit(text_surf, (160, start_y + (i * 60) + 18))

        # Powerup Info
        info_text = f"[F] 50:50 ({self.powerups['50:50']})   |   [T] Freeze ({self.powerups['freeze']})"
        draw_text_centered(info_text, font_sm, TEXT_GRAY, SCREEN, WIDTH//2, HEIGHT - 80)

        # Feedback Overlay
        if self.feedback:
            overlay_rect = pygame.Rect(WIDTH//2 - 150, 250, 300, 100)
            draw_rounded_rect(SCREEN, self.feedback_color, overlay_rect, 20)
            draw_text_centered(self.feedback, font_lg, TEXT_WHITE, SCREEN, WIDTH//2, 300)

    def draw_gameover(self):
        SCREEN.fill(BG_COLOR)
        draw_text_centered("GAME OVER", font_xl, ACCENT_RED, SCREEN, WIDTH//2, 200)
        draw_text_centered(f"Final Score: {self.score}", font_lg, TEXT_WHITE, SCREEN, WIDTH//2, 300)
        draw_text_centered("Press ENTER to Retry", font_md, TEXT_GRAY, SCREEN, WIDTH//2, 400)

# --- RUN ---
def run_game():
    game = Game()
    game.run()

if __name__ == "__main__":
    run_game()