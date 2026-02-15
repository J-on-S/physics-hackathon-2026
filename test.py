import pygame
import random
import math
import sys
import time

pygame.init()

# -------------------------
# CONFIG
# -------------------------
WIDTH, HEIGHT = 1000, 600
FPS = 60
DT = 1 / FPS
GROUND_Y = HEIGHT - 50
INIT_BALL_X = 100
INIT_BALL_Y = GROUND_Y-200
ball_radius = 10
angle = 45
t_since_launch = 0    # timer
delta_x = 0.0
delta_y = 0.0
FIXED_VELOCITY = 700
solution_angle = 0 
# -------------------------
# UNIT CONVERSION
# -------------------------
PIXELS_PER_METER = 50  # 50 pixels = 1 meter 
# --- REAL GRAVITY (m/s^2) scaled to your px/s^2 ---
EARTH_PIXEL_GRAVITY = 9.81 * PIXELS_PER_METER  # Earth will feel like 500 px/s^2 in your game

PLANET_GRAVITY_MSS = {
    1: 3.70,   # Mercury
    2: 8.87,   # Venus
    3: 9.81,   # Earth
    4: 1.62,   # Moon
    5: 3.71,   # Mars
    6: 24.79,  # Jupiter
    7: 10.44,  # Saturn
    8: 8.69,   # Uranus
    9: 11.15   # Neptune
}

redbirdskin = pygame.transform.scale(pygame.image.load("redbird.png"), (ball_radius*8, ball_radius*8))
cannon_body = pygame.transform.scale(pygame.image.load("cannon_body.png"), (ball_radius*10, ball_radius*10))
cannon_wheel = pygame.transform.scale(pygame.image.load("cannon_wheel.png"), (ball_radius*5, ball_radius*5))
platform = pygame.Rect(0, INIT_BALL_Y + cannon_wheel.get_height(), 200, 300)

pygame.mixer.init()
# Music: https://pixabay.com/music/search/game%20background/
pygame.mixer.music.load('backgroundmusicforvideos-gaming-game-minecraft-background-music-372242.mp3')
pygame.mixer.music.play(-1)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Physics Hackathon Prototype")

clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18)
bigfont = pygame.font.SysFont("Arial", 30)

GROUND_Y = HEIGHT - 50
# -------------------------
# HINT POPUP UI
# -------------------------
HINT_IMAGE_PATH = "hint_formula.png"  # <- put your png in the same folder (or change path)

hint_open = False

# Button (top-right)
HINT_BTN_W, HINT_BTN_H = 90, 34
HINT_BTN_MARGIN = 12
hint_btn_rect = pygame.Rect(WIDTH - HINT_BTN_W - HINT_BTN_MARGIN, HINT_BTN_MARGIN, HINT_BTN_W, HINT_BTN_H)

# Popup panel (top-right)
HINT_PANEL_W, HINT_PANEL_H = 360, 260
hint_panel_rect = pygame.Rect(WIDTH - HINT_PANEL_W - HINT_BTN_MARGIN, HINT_BTN_MARGIN + HINT_BTN_H + 10, HINT_PANEL_W, HINT_PANEL_H)

# Close button (inside panel)
CLOSE_BTN_SIZE = 26
hint_close_rect = pygame.Rect(
    hint_panel_rect.right - CLOSE_BTN_SIZE - 10,
    hint_panel_rect.top + 10,
    CLOSE_BTN_SIZE,
    CLOSE_BTN_SIZE
)

# Load & scale hint image once
hint_image_raw = pygame.image.load(HINT_IMAGE_PATH).convert_alpha()
# Fit image into panel with padding
HINT_PAD = 14
max_w = HINT_PANEL_W - 2 * HINT_PAD
max_h = HINT_PANEL_H - 2 * HINT_PAD - 30  # leave room for header/close button
scale = min(max_w / hint_image_raw.get_width(), max_h / hint_image_raw.get_height(), 1.0)
hint_image = pygame.transform.smoothscale(
    hint_image_raw,
    (int(hint_image_raw.get_width() * scale), int(hint_image_raw.get_height() * scale))
)
# -------------------------
# RANDOM PHYSICS PARAMETERS
# -------------------------
def random_parameters():
    global gravity, mass, drag_k, wind_x
    gravity = random.uniform(300, 800)     # px/s^2 downward
    mass = random.uniform(0.5, 5)
    drag_k = random.uniform(0.0, 0.6)
    wind_x = random.uniform(-120, 120)     # px/s  (used in drag relative velocity)
    return gravity, mass, drag_k, wind_x


# -------------------------
# FUNCTIONS
# -------------------------
def forward_displacement_for_angle(test_angle, velocity, gravity, wind_x, drag_k, mass, max_steps=2000):
    rad = math.radians(test_angle)

    sim_vx = velocity * math.cos(rad)
    sim_vy = -velocity * math.sin(rad)   # up is negative in pygame

    sim_x = INIT_BALL_X
    sim_y = INIT_BALL_Y

    t = 0.0

    for _ in range(max_steps):
        # relative velocity for drag (wind only affects x-relative speed)
        rel_vx = sim_vx - wind_x
        rel_vy = sim_vy

        drag_fx = -drag_k * rel_vx
        drag_fy = -drag_k * rel_vy

        ax = drag_fx / mass
        ay = gravity + (drag_fy / mass)

        sim_vx += ax * DT
        sim_vy += ay * DT

        sim_x += sim_vx * DT
        sim_y += sim_vy * DT

        t += DT

        # stop if it hits "ground"
        if sim_y >= GROUND_Y:
            break

        # stop if totally offscreen
        if sim_x < -200 or sim_x > WIDTH + 200 or sim_y > HEIGHT + 200:
            break

    dx = sim_x - INIT_BALL_X
    dy = sim_y - INIT_BALL_Y
    return dx, dy, t

def find_target_point_for_angle(test_angle, velocity, gravity, wind_x, drag_k, mass):
    rad = math.radians(test_angle)

    sim_vx = velocity * math.cos(rad)
    sim_vy = -velocity * math.sin(rad)
    sim_x = INIT_BALL_X
    sim_y = INIT_BALL_Y
    t = 0.0

    tw, th = 40, 100

    best_rect = None
    best_t = None
    best_dx = -1e9

    for _ in range(2000):
        # drag (wind affects relative x speed)
        rel_vx = sim_vx - wind_x
        rel_vy = sim_vy

        drag_fx = -drag_k * rel_vx
        drag_fy = -drag_k * rel_vy

        ax = drag_fx / mass
        ay = gravity + (drag_fy / mass)

        sim_vx += ax * DT
        sim_vy += ay * DT
        sim_x += sim_vx * DT
        sim_y += sim_vy * DT
        t += DT

        # stop at ground
        if sim_y >= GROUND_Y:
            break

        dx = sim_x - INIT_BALL_X

        # check if we can place a target centered here
        left = int(sim_x - tw / 2)
        top  = int(sim_y - th / 2)

        on_screen = (left >= 300 and left + tw <= WIDTH - 20 and
                     top >= 50 and top + th <= HEIGHT - 60)

        if on_screen and dx > best_dx:
            best_dx = dx
            best_rect = pygame.Rect(left, top, tw, th)
            best_t = t

    return best_rect, best_t

def draw_hint_ui():
    global hint_open

    # Draw Hint button (always visible)
    pygame.draw.rect(screen, (245, 245, 245), hint_btn_rect, border_radius=8)
    pygame.draw.rect(screen, (0, 0, 0), hint_btn_rect, 2, border_radius=8)
    label = font.render("HINT", True, (0, 0, 0))
    screen.blit(label, (hint_btn_rect.centerx - label.get_width() // 2,
                        hint_btn_rect.centery - label.get_height() // 2))

    if not hint_open:
        return

    # Panel background
    pygame.draw.rect(screen, (255, 255, 255), hint_panel_rect, border_radius=12)
    pygame.draw.rect(screen, (0, 0, 0), hint_panel_rect, 2, border_radius=12)

    # Title
    title = font.render("Hint", True, (0, 0, 0))
    screen.blit(title, (hint_panel_rect.x + 14, hint_panel_rect.y + 12))

    # Close button
    pygame.draw.rect(screen, (240, 240, 240), hint_close_rect, border_radius=6)
    pygame.draw.rect(screen, (0, 0, 0), hint_close_rect, 2, border_radius=6)
    x_text = font.render("X", True, (0, 0, 0))
    screen.blit(x_text, (hint_close_rect.centerx - x_text.get_width() // 2,
                         hint_close_rect.centery - x_text.get_height() // 2))

    # Draw hint image centered in the remaining space
    img_x = hint_panel_rect.x + (hint_panel_rect.w - hint_image.get_width()) // 2
    img_y = hint_panel_rect.y + 44 + (hint_panel_rect.h - 44 - hint_image.get_height()) // 2
    screen.blit(hint_image, (img_x, img_y))

def gravity_for_level(level):
    # levels 1..9 use real gravities (scaled)
    if level in PLANET_GRAVITY_MSS:
        real_g = PLANET_GRAVITY_MSS[level]
        return EARTH_PIXEL_GRAVITY * (real_g / 9.81)  # scale vs Earth
    # last level (10) stays randomized (your request)
    return random.uniform(300, 800)

current_level = 0   # tutorial level first

def reset_round():
    global target_rect
    global ball_x, ball_y, vx, vy, launched
    global flight_time, angle, velocity
    global t_since_launch, solution_angle
    global delta_x, delta_y

    global current_level
    global gravity, mass, drag_k, wind_x

    # Set gravity based on the planet (level)
    gravity = gravity_for_level(current_level)

    # Randomize the other parameters like before
    mass = random.uniform(0.5, 5)
    drag_k = random.uniform(0.0, 1.5)
    wind_x = random.uniform(-200, 200)
    

    # fixed velocity for the whole game
    velocity = FIXED_VELOCITY

    # reset projectile
    ball_x = INIT_BALL_X
    ball_y = INIT_BALL_Y
    vx = 0
    vy = 0
    launched = False
    t_since_launch = 0.0

    # player starts here
    angle = 45

    # pick a hidden winning angle and spawn target based on it
    for _ in range(200):
        solution_angle = random.uniform(10, 80)

        rect, t_sol = find_target_point_for_angle(
            solution_angle, velocity, gravity, wind_x, drag_k, mass
    )
        if rect is None:
            continue

        target_rect = rect
        flight_time = t_sol
        delta_x = target_rect.centerx - ball_x
        delta_y = target_rect.centery - ball_y
        return

    # fallback
    target_rect = pygame.Rect(750, HEIGHT - 150, 40, 100)
    solution_angle = 45
    flight_time = 2.5
    delta_x = target_rect.centerx - ball_x
    delta_y = target_rect.centery - ball_y

reset_round()

def launch():
    global target_rect
    global ball_x, ball_y, vx, vy, launched
    global vx, vy, launched
    global gravity, mass, drag_k, wind_x, velocity
    rad = math.radians(angle)
    vx = velocity * math.cos(rad)
    vy = -velocity * math.sin(rad)
    launched = True



def update_physics():
    global ball_x, ball_y, vx, vy, launched, t_since_launch
    global gravity, mass, drag_k, wind_x, flight_time

    if not launched:
        return

    t_since_launch += DT

    # stop after the "expected" time window
    if t_since_launch > flight_time:
        launched = False
        vx = 0
        vy = 0
        return

    # drag with wind-relative x speed
    rel_vx = vx - wind_x
    rel_vy = vy

    drag_fx = -drag_k * rel_vx
    drag_fy = -drag_k * rel_vy

    ax = drag_fx / mass
    ay = gravity + (drag_fy / mass)

    vx += ax * DT
    vy += ay * DT

    ball_x += vx * DT
    ball_y += vy * DT

    if ball_y >= GROUND_Y:
        launched = False

def check_hit():
    global target_rect
    global ball_x, ball_y, vx, vy, launched
    global vx, vy, launched
    global gravity, mass, drag_k, wind_x, velocity
    ball_rect = pygame.Rect(
        ball_x - ball_radius,
        ball_y - ball_radius,
        ball_radius * 2,
        ball_radius * 2
    )
    return ball_rect.colliderect(target_rect)

#predicted trajectory line

def calculate_trajectory():
    init_time = time.time()
    global point
    rad = math.radians(angle)
    sim_vx = velocity * math.cos(rad)
    sim_vy = -velocity * math.sin(rad)
    sim_x = ball_x
    sim_y = ball_y

    for _ in range(300):  # number of simulation steps
        rel_vx = sim_vx - wind_x
        rel_vy = sim_vy

        drag_fx = -drag_k * rel_vx
        drag_fy = -drag_k * rel_vy

        ax = drag_fx / mass
        ay = gravity + (drag_fy / mass)

        sim_vx += ax * DT
        sim_vy += ay * DT

        sim_x += sim_vx * DT
        sim_y += sim_vy * DT

        if sim_y >= HEIGHT:
            break
        point = (int(sim_x), int(sim_y))

    return (int(sim_x), int(sim_y))

images = {}
def load_background(filename):
    global images
    if filename not in images:
        background = pygame.image.load(filename).convert()
        background = pygame.transform.scale(background, (WIDTH, HEIGHT))
        background.set_alpha(206)
        images[filename] = background
        return background
    else:
        return images[filename]

anims = {}
def load_anim(filenames):
    anims
    if (filenames not in anims) or (anims[filenames] == len(filenames) - 1):
        anims[filenames] = 0
    else:
        anims[filenames] += 1
    frame_no = anims[filenames]
    image = load_background(filenames[frame_no])
    return image


def draw_ui():
    global gravity, mass, drag_k, wind_x, velocity
    global delta_x, delta_y, current_level, solution_angle
    global PIXELS_PER_METER, flight_time, angle

    # Convert internal pixel-units to SI-units for display
    gravity_mss = gravity / PIXELS_PER_METER       # px/s² -> m/s²
    velocity_ms = velocity / PIXELS_PER_METER      # px/s  -> m/s
    wind_ms = wind_x / PIXELS_PER_METER            # px/s  -> m/s
    dx_m = delta_x / PIXELS_PER_METER              # px -> m
    dy_m = delta_y / PIXELS_PER_METER              # px -> m

    info = [
        f"(debug) solution angle*: {solution_angle:.1f}°",
        f"Level: {current_level}",
        f"Gravity: {gravity_mss:.2f} m/s²",   # ONE line only (works for planets + random)
        f"Mass: {mass:.2f}",
        f"Drag k: {drag_k:.2f}",
        f"Wind X: {wind_ms:.2f} m/s",
        f"Angle: {angle:.1f}°",
        f"Flight time: {flight_time:.2f}s",
        f"Δx: {dx_m:.2f} m",
        f"Δy: {dy_m:.2f} m (down +)",
        "",
        f"Velocity (fixed): {velocity_ms:.2f} m/s",
        "",
        "UP/DOWN = Change angle",
        "SPACE = Launch",
        "R = Reset",
    ]

    y_offset = 10
    for line in info:
        text = font.render(line, True, (0, 0, 0))
        screen.blit(text, (10, y_offset))
        y_offset += 22


TUTORIAL_SCREENS = ['tutorial-1.png', 'tutorial-2.png']
tutorial_screen_no = 0
def tutorial():
    global tutorial_screen_no
    tutorial_screen = TUTORIAL_SCREENS[tutorial_screen_no]
    screen.blit(load_background(tutorial_screen), (0, 0))


def level1():
    background = load_background("mercury.png")
    screen.blit(background, (0, 0))
    global current_level
    # Draw target
    pygame.draw.rect(screen, (200, 0, 0), target_rect)

    # Draw ball
    #pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        pygame.display.flip() # Show the win text for 500ms
        pygame.time.delay(500)
        current_level = 2 # Move to level 2
        #press key to continue
        reset_round()

def level2():
    background = load_background("venus2.png")
    screen.blit(background, (0, 0))
    global current_level
    # Draw target
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    # Draw ball
    #pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        pygame.display.flip() # Show the win text for 500ms
        pygame.time.delay(500)
        current_level += 1 # Move back to level 1
        #press key to continue
        reset_round()

def level3():
    background = load_background("earth2.png")
    screen.blit(background, (0, 0))
    global current_level
    # Draw target
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    # Draw ball
    #pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        pygame.display.flip() # Show the win text for 500ms
        pygame.time.delay(500)
        current_level += 1 # Move back to level 1
        #press key to continue
        reset_round()
def level4():
    background = load_background("moon2.png")
    screen.blit(background, (0, 0))
    global current_level
    # Draw target
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    # Draw ball
    #pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        pygame.display.flip() # Show the win text for 500ms
        pygame.time.delay(500)
        current_level += 1 # Move back to level 1
        #press key to continue
        reset_round()
def level5():
    background = load_background("mars2.png")
    screen.blit(background, (0, 0))
    global current_level
    # Draw target
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    # Draw ball
    #pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        pygame.display.flip() # Show the win text for 500ms
        pygame.time.delay(500)
        current_level += 1 # Move back to level 1
        #press key to continue
        reset_round()
def level6():
    background = load_background("jupiter.png")
    screen.blit(background, (0, 0))
    global current_level
    # Draw target
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    # Draw ball
    #pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        pygame.display.flip() # Show the win text for 500ms
        pygame.time.delay(500)
        current_level += 1 # Move back to level 1
        #press key to continue
        reset_round()
def level7():
    background = load_background("saturn.png")
    screen.blit(background, (0, 0))
    global current_level
    # Draw target
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    # Draw ball
    #pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        pygame.display.flip() # Show the win text for 500ms
        pygame.time.delay(500)
        current_level += 1 # Move back to level 1
        #press key to continue
        reset_round()
def level8():
    background = load_background("uranus.png")
    screen.blit(background, (0, 0))
    global current_level
    # Draw target
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    # Draw ball
    #pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        pygame.display.flip() # Show the win text for 500ms
        pygame.time.delay(500)
        current_level += 1 # Move back to level 1
        #press key to continue
        reset_round()
def level9():
    background = load_background("neptune.png")
    screen.blit(background, (0, 0))
    global current_level
    # Draw target
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    # Draw ball
    #pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        pygame.display.flip() # Show the win text for 500ms
        pygame.time.delay(500)
        current_level += 1 # Move back to level 1
        #press key to continue
        reset_round()


def winlevel10():
    background = load_background("mystery.png")
    screen.blit(background, (0, 0))
    global current_level, win, FPS
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    if check_hit():
        FPS = 2
        win = True
        

backgrounds = {}
LEVELS = [tutorial, level1, level2, level3, level4, level5, level6, level7, level8, level9, winlevel10]


#def updatescore():
#    scoretext = f"Score: {score}"
#    scoretextobject = font.render(scoretext, True, (0,0,0))
#    screen.blit(scoretextobject, (WIDTH-scoretextobject.width-10, 10))

# -------------------------
# MAIN LOOP
# -------------------------
win = False
running = True
while running:
    clock.tick(FPS)
    screen.fill((220, 220, 255))

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos   # <-- define them here

        # Click Hint button
            if hint_btn_rect.collidepoint(mx, my):
                hint_open = not hint_open

        # Click close button
            elif hint_open and hint_close_rect.collidepoint(mx, my):
                hint_open = False

        # Optional: click outside closes popup
            elif hint_open and not hint_panel_rect.collidepoint(mx, my):
                hint_open = False

        if event.type == pygame.KEYDOWN:
            if hint_open and event.key == pygame.K_ESCAPE:
                hint_open = False

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            # Tutorial "level"
            if current_level == 0:
                tutorial_screen_no += 1
                if tutorial_screen_no == len(TUTORIAL_SCREENS):
                    # Move to next level after tutorial
                    current_level += 1
                    reset_round()
            elif event.key == pygame.K_SPACE and not launched:
                launch()
            if event.key == pygame.K_n:
                current_level += 1
                if current_level >= len(LEVELS):
                    current_level = len(LEVELS) - 1
                reset_round()
            if event.key == pygame.K_w:
                if current_level == len(LEVELS) - 1:
                    win = True
                else:
                    current_level = len(LEVELS) - 1
    
    keys = pygame.key.get_pressed()
    if keys[pygame.K_r] or (ball_x > WIDTH):
        reset_round()

    if not launched:
        if keys[pygame.K_UP]:
            angle += 1
        if keys[pygame.K_DOWN]:
            angle -= 1

    angle = max(5, min(85, angle))
    rad = math.radians(angle)


    # Run level-specific logic
    if not win:
        LEVELS[current_level]()

    paused = (win or current_level == 0)
    if not paused:
        update_physics()

        #Draws bird
        if not launched:
            redbirdskin.set_alpha(128) 
            bird_x = (ball_x - (redbirdskin.get_width()/2))+ 60 * math.cos(rad)
            bird_y = (ball_y - (redbirdskin.get_height()/2)) - 60 * math.sin(rad)
            screen.blit(redbirdskin, (bird_x, bird_y))
        else: 
            redbirdskin.set_alpha(256)
            bird_x = int(ball_x) - (redbirdskin.get_width()/2)
            bird_y = int(ball_y) - (redbirdskin.get_height()/2)
            screen.blit(redbirdskin, (bird_x, bird_y))

        #Draws cannon
        cannon_body = pygame.transform.rotate(pygame.transform.scale(pygame.image.load("cannon_body.png"), (ball_radius*10, ball_radius*10)), angle)
        cannon_x = (INIT_BALL_X - (cannon_body.get_width()/2))
        cannon_y = (INIT_BALL_Y - (cannon_body.get_height()/2))
        screen.blit(cannon_body, (cannon_x, cannon_y))
        screen.blit(cannon_wheel, (INIT_BALL_X - (cannon_wheel.get_width()/2), INIT_BALL_Y + (cannon_wheel.get_height()/3)))

        #Draws ground
        pygame.draw.rect(screen, (0, 0, 0), platform)

    #give final vy
    #f_v_x = calculate_trajectory()[0]
    #f_v_y = calculate_trajectory()[1]
    #if point[0] > target_rect.x and point[1] > target_rect.y and point[0] < (target_rect.x + target_rect.width) and point[1] < HEIGHT:
    #    final_v_x = font.render(f"Vfx = {f_v_x}, Vfy = {f_v_y}", True, (0,150,0))
    #else:
    #    final_v_x = font.render(f"Vfx = {f_v_x}, Vfy = {f_v_y}", True, (0,0,0))
    #screen.blit(final_v_x, (WIDTH//2 - 60, 50))
    # Draw launcher line
    #if not launched:
    #    rad = math.radians(angle)
    #    lx = ball_x + 40 * math.cos(rad)
    #    ly = ball_y - 40 * math.sin(rad)
    #    pygame.draw.line(screen, (0,0,0), (ball_x, ball_y), (lx, ly), 3)

    # Draw predicted trajectory as a dotted line
    #if not launched:
    #    trajectory_points = calculate_trajectory()
    #    if len(trajectory_points) > 1:
    #        for i in range(0, len(trajectory_points)-1, 3):  # skip every 3 points to create gaps
    #            start = trajectory_points[i]
    #            end = trajectory_points[i+1]
    #            pygame.draw.line(screen, (150, 150, 150), start, end, 2)


    if not paused:
        draw_ui()
    
    draw_hint_ui()

    if win:
        win_anim = ('modal-1.png', 'modal-2.png')
        screen.blit(load_anim(win_anim), (0,0))
        congrats = font.render("CONGRATULATIONS!", True, (220, 220, 120))
        screen.blit(congrats, (WIDTH//2 - congrats.width//2, 300))
        youwin = font.render("YOU HAVE COMPLETED THE GAME!", True, (220, 220, 120))
        screen.blit(youwin, (WIDTH//2 - youwin.width//2, 350))
        hacking = bigfont.render("Happy 10th Hackathon!", True, (255, 255, 255))
        screen.blit(hacking, (WIDTH//2 - hacking.width//2, 250))
        pygame.display.flip()
        pygame.time.delay(300)
    else:
        pygame.display.flip()



pygame.quit()
sys.exit()
