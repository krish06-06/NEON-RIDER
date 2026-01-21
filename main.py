import pygame
import sys
import random
import os

# --- CONFIGURATION ---
WIDTH, HEIGHT = 1280, 720
FPS = 60

# --- DIFFICULTY SETTINGS ---
INITIAL_SCROLL_SPEED = 5   # Starts slow (was 10)
MAX_SPEED = 25             # The fastest it can ever get
SPEED_INCREMENT = 0.5      # How much speed to add every level up
SPEED_UP_TIME = 5000       # How often to speed up (in milliseconds, 5000 = 5 sec)

# Player movement speed (this should stay responsive)
PLAYER_SPEED = 7 

# --- ROAD BOUNDARIES (Your custom values) ---
ROAD_TOP = 420
ROAD_BOTTOM = 620 
ROAD_LEFT = 0
ROAD_RIGHT = 1280

# --- SETUP ---
pygame.init()
pygame.font.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TRON RIDER: SURVIVAL MODE")
clock = pygame.time.Clock()

# --- CUSTOM EVENTS ---
# This creates a custom timer event for speeding up
SPEED_UP_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(SPEED_UP_EVENT, SPEED_UP_TIME)

# --- FONTS ---
font_score = pygame.font.SysFont("Arial", 30, bold=True)
font_gameover = pygame.font.SysFont("Arial", 60, bold=True)

# --- LOAD ASSETS ---
try:
    # 1. Background
    bg_raw = pygame.image.load("assets/bg.jpg").convert()
    bg_image = pygame.transform.scale(bg_raw, (WIDTH, HEIGHT))
    
    # 2. Bike
    bike_raw = pygame.image.load("assets/bike.jpg").convert()
    bike_raw.set_colorkey((255, 255, 255)) 
    bike_flipped = pygame.transform.flip(bike_raw, True, False) 
    bike_image = pygame.transform.scale(bike_flipped, (100, 60))
    
    # 3. Wall
    wall_raw = pygame.image.load("assets/wall.png").convert()
    wall_image = pygame.transform.scale(wall_raw, (50, 50)) 

except FileNotFoundError:
    print("Error: Missing files in assets/ folder.")
    sys.exit()

# --- HIGH SCORE SYSTEM ---
def get_high_score():
    if os.path.exists("highscore.txt"):
        with open("highscore.txt", "r") as f:
            try: return int(f.read())
            except: return 0
    return 0

def save_high_score(new_score):
    current_high = get_high_score()
    if new_score > current_high:
        with open("highscore.txt", "w") as f:
            f.write(str(new_score))

# --- GAME FUNCTIONS ---
def draw_text(surf, text, font, color, x, y):
    img = font.render(text, True, color)
    rect = img.get_rect(center=(x, y))
    surf.blit(img, rect)

def reset_game():
    player_rect = bike_image.get_rect()
    player_rect.x = 100
    player_rect.y = 500
    obstacles = []
    score = 0
    bg_x = 0
    
    # Reset speed to the slow initial value
    current_speed = INITIAL_SCROLL_SPEED
    
    return player_rect, obstacles, score, bg_x, current_speed

# --- MAIN GAME LOOP ---
def main():
    player_rect, obstacles, score, bg_x, current_speed = reset_game()
    high_score = get_high_score()
    
    velocity_x = 0
    velocity_y = 0
    
    # Timer for spawning walls
    last_spawn_time = pygame.time.get_ticks()
    
    game_active = True
    running = True

    while running:
        current_time = pygame.time.get_ticks()

        # 1. EVENT HANDLING
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if game_active:
                # Speed Up Timer (Happens every 5 seconds)
                if event.type == SPEED_UP_EVENT:
                    if current_speed < MAX_SPEED:
                        current_speed += SPEED_INCREMENT
                        
                # MOVEMENT
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w: velocity_y = -PLAYER_SPEED
                    if event.key == pygame.K_s: velocity_y = PLAYER_SPEED
                    if event.key == pygame.K_a: velocity_x = -PLAYER_SPEED
                    if event.key == pygame.K_d: velocity_x = PLAYER_SPEED
                
                if event.type == pygame.KEYUP:
                    if event.key in [pygame.K_w, pygame.K_s]: velocity_y = 0
                    if event.key in [pygame.K_a, pygame.K_d]: velocity_x = 0
            
            else:
                # RESTART
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    player_rect, obstacles, score, bg_x, current_speed = reset_game()
                    high_score = get_high_score()
                    game_active = True
                    velocity_x = 0 
                    velocity_y = 0

        if game_active:
            # --- LOGIC ---
            
            # A. Scroll Background (Using current_speed)
            bg_x -= current_speed
            if bg_x <= -WIDTH:
                bg_x = 0
            
            # B. Move Player
            player_rect.x += velocity_x
            player_rect.y += velocity_y
            
            # Boundaries
            if player_rect.top < ROAD_TOP: player_rect.top = ROAD_TOP
            if player_rect.bottom > ROAD_BOTTOM: player_rect.bottom = ROAD_BOTTOM
            if player_rect.left < 0: player_rect.left = 0
            if player_rect.right > WIDTH: player_rect.right = WIDTH
            
            # C. Spawn Obstacles
            # We adjust spawn rate based on speed so it doesn't become unfair
            # (Faster speed = spawn slightly faster)
            current_spawn_rate = 1500 - (current_speed * 20) 
            if current_spawn_rate < 400: current_spawn_rate = 400 # Limit max spawn rate

            if current_time - last_spawn_time > current_spawn_rate:
                spawn_y = random.randint(ROAD_TOP, ROAD_BOTTOM - 40)
                new_wall = wall_image.get_rect(midleft=(WIDTH + 50, spawn_y))
                obstacles.append(new_wall)
                last_spawn_time = current_time

            # D. Move Obstacles & Check Collision
            for wall in obstacles[:]:
                wall.x -= current_speed # Walls move at the new speed
                
                if player_rect.colliderect(wall):
                    save_high_score(score)
                    game_active = False # GAME OVER
                
                if wall.right < 0:
                    obstacles.remove(wall)
                    score += 1
            
            # --- DRAWING ---
            screen.blit(bg_image, (bg_x, 0))
            screen.blit(bg_image, (bg_x + WIDTH, 0))
            screen.blit(bike_image, player_rect)
            
            for wall in obstacles:
                screen.blit(wall_image, wall)
            
            # Draw UI
            score_surf = font_score.render(f"Score: {score}", True, (255, 255, 255))
            speed_surf = font_score.render(f"Speed: {int(current_speed)} MPH", True, (0, 255, 255))
            screen.blit(score_surf, (20, 20))
            screen.blit(speed_surf, (20, 60))
            
        else:
            # --- GAME OVER SCREEN ---
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(150)
            overlay.fill((0,0,0))
            screen.blit(overlay, (0,0))
            
            draw_text(screen, "CRASHED!", font_gameover, (255, 0, 0), WIDTH//2, HEIGHT//2 - 50)
            draw_text(screen, f"Final Score: {score}", font_score, (255, 255, 255), WIDTH//2, HEIGHT//2 + 10)
            draw_text(screen, f"High Score: {high_score}", font_score, (255, 215, 0), WIDTH//2, HEIGHT//2 + 50)
            draw_text(screen, "Press SPACE to Restart", font_score, (0, 255, 255), WIDTH//2, HEIGHT//2 + 100)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()