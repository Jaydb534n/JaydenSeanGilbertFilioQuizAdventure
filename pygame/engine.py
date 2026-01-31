import os
import pygame
from data import questions

# --- HEADLESS MODE SETUP ---
# Ini perintah agar Pygame tidak membuka window (karena di server tidak ada layar)
os.environ["SDL_VIDEODRIVER"] = "dummy"

class GameEngine:
    def __init__(self):
        pygame.init()
        self.WIDTH = 800
        self.HEIGHT = 600
        
        # Game State
        self.score = 0
        self.level = 1
        self.current_q_index = 0
        
        # Player Logic (Menggunakan Pygame Rect)
        self.player_rect = pygame.Rect(50, 450, 40, 60)
        self.speed = 5
        
        # Checkpoints/Quiz Spots (Menggunakan Pygame Rect untuk Collision)
        # Kita buat kotak tak terlihat di koordinat tertentu
        self.checkpoints = []
        positions = [400, 900, 1500, 2100, 2600, 3200]
        for pos in positions:
            # Rect checkpoint: x, y, width, height
            rect = pygame.Rect(pos, 400, 50, 150) 
            self.checkpoints.append({"rect": rect, "active": True})
            
        self.finish_line = 3500

    def process_input(self, action):
        """Menerima input 'move' dari Flask, update posisi rect"""
        status = "RUNNING"
        quiz_data = None
        
        if action == "right":
            self.player_rect.x += self.speed
        elif action == "left":
            self.player_rect.x -= self.speed
            
        # --- PYGAME LOGIC: COLLISION DETECTION ---
        # Di sini kita pakai fungsi asli pygame untuk mengecek tabrakan
        # antara Pemain dan Checkpoint Soal
        
        for i, cp in enumerate(self.checkpoints):
            if cp["active"]:
                # rect.colliderect adalah fungsi murni Pygame
                if self.player_rect.colliderect(cp["rect"]):
                    status = "QUIZ"
                    q_idx = self.current_q_index % len(questions)
                    quiz_data = questions[q_idx]
                    # Nonaktifkan checkpoint ini agar tidak memicu soal berulang kali
                    cp["active"] = False 
                    break
        
        # Cek Finish
        if self.player_rect.x >= self.finish_line:
            status = "WIN"

        # Return data bersih ke Flask (JSON friendly)
        return {
            "player_x": self.player_rect.x,
            "status": status,
            "score": self.score,
            "level": self.level,
            "quiz_data": quiz_data
        }

    def answer_quiz(self, is_correct):
        if is_correct:
            self.score += 100
        self.current_q_index += 1
        if self.current_q_index % 3 == 0:
            self.level += 1
        
        # Geser pemain sedikit agar tidak nyangkut di collision checkpoint
        self.player_rect.x += 60 
        
        return {
            "score": self.score,
            "level": self.level,
            "player_x": self.player_rect.x
        }

    def reset(self):
        self.__init__()