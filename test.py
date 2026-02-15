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
score = 0
t_since_launch = 0    # timer
solution_v = 0      # hidden "correct" speed for spawning target
delta_x = 0.0
delta_y = 0.0
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
# RANDOM PHYSICS PARAMETERS
# -------------------------
def random_parameters():
    global gravity, mass, drag_k, wind_x
    gravity = random.uniform(300, 800)
    mass = random.uniform(0.5, 5)
    drag_k = random.uniform(0.0, 1.5)
    wind_x = random.uniform(-200, 200)
    # Random fixed angle and time (given to player)
    angle = random.randint(20, 70)
    flight_time = random.uniform(1.1, 1.7)
    return gravity, mass, drag_k, wind_x, angle, flight_time

def forward_displacement(v0, theta_deg, T, g, wind_x, drag_k, mass):
    theta = math.radians(theta_deg)
    vx0 = v0 * math.cos(theta)
    vy0 = -v0 * math.sin(theta)  # negative = up (pygame)

    # beta = k/m
    if mass <= 0:
        return None
    beta = drag_k / mass

    # No-drag limit (your wind has no effect when drag_k=0 in your code)
    if abs(beta) < 1e-6:
        dx = vx0 * T
        dy = vy0 * T + 0.5 * g * T * T
        return dx, dy

    A = 1.0 - math.exp(-beta * T)

    # x(t) = wT + (vx0 - w)/beta * (1 - e^{-beta T})
    dx = wind_x * T + (vx0 - wind_x) * (A / beta)

    # y(t) = (g/beta)T + (vy0 - g/beta)/beta * (1 - e^{-beta T})
    dy = (g / beta) * T + (vy0 - (g / beta)) * (A / beta)

    return dx, dy
# -------------------------
# FUNCTIONS
# -------------------------

def reset_round():
    global target_rect
    global ball_x, ball_y, vx, vy, launched
    global gravity, mass, drag_k, wind_x, flight_time, angle, velocity
    global t_since_launch, solution_v

   
    # Random physics (your function)
    gravity, mass, drag_k, wind_x, angle, flight_time = random_parameters()

    # Player-controlled variable (speed). Start at a reasonable guess.
    velocity = 700

   

    # Reset projectile state
    ball_x = 100
    ball_y = GROUND_Y - 200
    vx = 0
    vy = 0
    launched = False
    t_since_launch = 0.0

    # Choose a hidden "solution speed" to construct a guaranteed-hit target
    # Keep it inside a comfortable range for your UI
    for _ in range(80):  # try a bunch of times to find a valid on-screen target
        solution_v = random.uniform(500, 1050)

        disp = forward_displacement(solution_v, angle, flight_time,
                                    gravity, wind_x, drag_k, mass)
        if disp is None:
            continue
        dx, dy = disp

        tx = ball_x + dx
        ty = ball_y + dy

        # Target size
        tw, th = 40, 100

        # Keep the entire rect on screen (and above the bottom)
        left = int(tx - tw / 2)
        top  = int(ty - th / 2)

        if left < 300 or left + tw > WIDTH - 20:
            continue
        if top < 50 or top + th > HEIGHT - 10:
            continue

        target_rect = pygame.Rect(left, top, tw, th)
        global delta_x, delta_y
        delta_x = target_rect.centerx - ball_x
        delta_y = target_rect.centery - ball_y   # pygame: down is positive (matches your formulas)
        return

    # Fallback if nothing works (rare): put a safe target
    target_rect = pygame.Rect(750, HEIGHT - 150, 40, 100)
    solution_v = 800

    delta_x = target_rect.centerx - ball_x
    delta_y = target_rect.centery - ball_y

reset_round()

def launch():
    global vx, vy, launched, t_since_launch
    rad = math.radians(angle)
    vx = velocity * math.cos(rad)
    vy = -velocity * math.sin(rad)
    launched = True
    t_since_launch = 0.0



def update_physics():
    global target_rect
    global ball_x, ball_y, vx, vy, launched
    global vx, vy, launched
    global gravity, mass, drag_k, wind_x, velocity
    global t_since_launch, flight_time
    if not launched:
        return
    t_since_launch += DT
    # Option: end round shortly after the "official" flight time
    if t_since_launch > flight_time:
        launched = False  # stop sim at official time
        vx = vy = 0
    # do NOT reset here; level logic will detect hit, otherwise player can press R
        return
    # Relative velocity (for wind)
    rel_vx = vx - wind_x
    rel_vy = vy

    # Drag force
    drag_fx = -drag_k * rel_vx
    drag_fy = -drag_k * rel_vy

    # Accelerations
    ax = drag_fx / mass
    ay = gravity + (drag_fy / mass)

    # Update velocity
    vx += ax * DT
    vy += ay * DT

    # Update position
    ball_x += vx * DT
    ball_y += vy * DT

    # Ground collision
    if ball_y >= HEIGHT:
        reset_round()

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
    global target_rect
    global ball_x, ball_y, vx, vy, launched
    global vx, vy, launched
    global gravity, mass, drag_k, wind_x, velocity
    global delta_x, delta_y
    info = [
        f"Level: {current_level}",
        f"Gravity: {gravity:.1f}",
        f"Mass: {mass:.2f}",
        f"Drag k: {drag_k:.2f}",
        f"Wind X: {wind_x:.1f}",
        f"Angle: {angle}",
        f"Flight time:{flight_time:.2f}s " ,
        f"Δx: {delta_x:.1f}",
        f"Δy: {delta_y:.1f} (down +)",
        "",
        f"Velocity: {velocity}",
        "",
        "SPACE = Launch",
        "R = Reset",
        
    ]
    info.insert(0, f"(debug) solution v*: {solution_v:.0f}")
    scoretext = f"Score: {score}"

    y_offset = 10
    for line in info:
        text = font.render(line, True, (0,0,0))
        screen.blit(text, (10, y_offset))
        y_offset += 22
    
    scoretextobject = font.render(scoretext, True, (0,0,0))
    screen.blit(scoretextobject, (WIDTH-scoretextobject.get_width()-10, 10))

def level1():
    background = load_background("mercury.png")
    screen.blit(background, (0, 0))
    global score, current_level
    # Draw target
    pygame.draw.rect(screen, (200, 0, 0), target_rect)

    # Draw ball
    #pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        pygame.display.flip() # Show the win text for 500ms
        pygame.time.delay(500)
        score += 1
        current_level = 2 # Move to level 2
        #press key to continue
        reset_round()

def level2():
    background = load_background("venus2.png")
    screen.blit(background, (0, 0))
    global score, current_level
    # Draw target
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    # Draw ball
    #pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        pygame.display.flip() # Show the win text for 500ms
        pygame.time.delay(500)
        score += 1
        current_level += 1 # Move back to level 1
        #press key to continue
        reset_round()

def level3():
    background = load_background("earth2.png")
    screen.blit(background, (0, 0))
    global score, current_level
    # Draw target
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    # Draw ball
    #pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        pygame.display.flip() # Show the win text for 500ms
        pygame.time.delay(500)
        score += 1
        current_level += 1 # Move back to level 1
        #press key to continue
        reset_round()
def level4():
    background = load_background("moon2.png")
    screen.blit(background, (0, 0))
    global score, current_level
    # Draw target
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    # Draw ball
    #pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        pygame.display.flip() # Show the win text for 500ms
        pygame.time.delay(500)
        score += 1
        current_level += 1 # Move back to level 1
        #press key to continue
        reset_round()
def level5():
    background = load_background("mars2.png")
    screen.blit(background, (0, 0))
    global score, current_level
    # Draw target
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    # Draw ball
    #pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        pygame.display.flip() # Show the win text for 500ms
        pygame.time.delay(500)
        score += 1
        current_level += 1 # Move back to level 1
        #press key to continue
        reset_round()
def level6():
    background = load_background("jupiter.png")
    screen.blit(background, (0, 0))
    global score, current_level
    # Draw target
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    # Draw ball
    #pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        pygame.display.flip() # Show the win text for 500ms
        pygame.time.delay(500)
        score += 1
        current_level += 1 # Move back to level 1
        #press key to continue
        reset_round()
def level7():
    background = load_background("saturn.png")
    screen.blit(background, (0, 0))
    global score, current_level
    # Draw target
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    # Draw ball
    #pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        pygame.display.flip() # Show the win text for 500ms
        pygame.time.delay(500)
        score += 1
        current_level += 1 # Move back to level 1
        #press key to continue
        reset_round()
def level8():
    background = load_background("uranus.png")
    screen.blit(background, (0, 0))
    global score, current_level
    # Draw target
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    # Draw ball
    #pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        pygame.display.flip() # Show the win text for 500ms
        pygame.time.delay(500)
        score += 1
        current_level += 1 # Move back to level 1
        #press key to continue
        reset_round()
def level9():
    background = load_background("neptune.png")
    screen.blit(background, (0, 0))
    global score, current_level
    # Draw target
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    # Draw ball
    #pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        pygame.display.flip() # Show the win text for 500ms
        pygame.time.delay(500)
        score += 1
        current_level += 1 # Move back to level 1
        #press key to continue
        reset_round()


def winlevel10():
    background = load_background("mystery.png")
    screen.blit(background, (0, 0))
    global score, current_level, win, FPS
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    if check_hit():
        FPS = 2
        win = True
        

backgrounds = {}
LEVELS = [ level1, level2, level3,level4, level5,level6,level7, level8, level9,winlevel10]
current_level = 1

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

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not launched:
                launch()
            if event.key == pygame.K_n:
                current_level += 1
                if current_level > len(LEVELS):
                    current_level = len(LEVELS)
            if event.key == pygame.K_w:
                if current_level == len(LEVELS):
                    win = True
                else:
                    current_level = len(LEVELS)
    
    keys = pygame.key.get_pressed()
    if keys[pygame.K_r] or (ball_x > WIDTH):
        reset_round()

    if not launched:
        if keys[pygame.K_UP]:
            velocity += 5
        if keys[pygame.K_DOWN]:
            velocity -= 5
    velocity = max(100,min(1500,velocity))
    rad = math.radians(angle)

    if not win:
        update_physics()

    # Run level-specific logic
    LEVELS[current_level - 1]()

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


    draw_ui()

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
