import pygame
import random
import math
import sys

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
velocity = 400
score = 0

redbirdskin = pygame.transform.scale(pygame.image.load("redbird.png"), (ball_radius*8, ball_radius*8))
cannon_body = pygame.transform.scale(pygame.image.load("cannon_body.png"), (ball_radius*10, ball_radius*10))
cannon_wheel = pygame.transform.scale(pygame.image.load("cannon_wheel.png"), (ball_radius*5, ball_radius*5))

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Physics Hackathon Prototype")

clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18)

GROUND_Y = HEIGHT - 50
FLOOR_HEIGHT = 80
floor_rect = pygame.Rect(0, HEIGHT - FLOOR_HEIGHT, WIDTH, FLOOR_HEIGHT)
# -------------------------
# RANDOM PHYSICS PARAMETERS
# -------------------------
def random_parameters():
    global gravity, mass, drag_k, wind_x
    gravity = random.uniform(300, 800)
    mass = random.uniform(0.5, 5)
    drag_k = random.uniform(0.0, 1.5)
    wind_x = random.uniform(-200, 200)

    return gravity, mass, drag_k, wind_x


# -------------------------
# FUNCTIONS
# -------------------------

def reset_round():
    global target_rect
    global ball_x, ball_y, vx, vy, launched
    global vx, vy, launched
    global gravity, mass, drag_k, wind_x
    angle = 45
    velocity = 400

    gravity, mass, drag_k, wind_x = random_parameters()

    ball_radius = 10
    ball_x = 100
    ball_y = GROUND_Y-200 #200 will be height of slingshot
    vx = 0
    vy = 0
    launched = False

    target_rect = pygame.Rect(
        random.randint(600, 900),
        HEIGHT - 100,
        40,
        100
    )

reset_round()

def launch():
    global target_rect
    global ball_x, ball_y, vx, vy, launched
    global vx, vy, launched
    global gravity, mass, drag_k, wind_x
    rad = math.radians(angle)
    vx = velocity * math.cos(rad)
    vy = -velocity * math.sin(rad)
    launched = True

def update_physics():
    global target_rect
    global ball_x, ball_y, vx, vy, launched
    global vx, vy, launched
    global gravity, mass, drag_k, wind_x
    if not launched:
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
    global gravity, mass, drag_k, wind_x
    ball_rect = pygame.Rect(
        ball_x - ball_radius,
        ball_y - ball_radius,
        ball_radius * 2,
        ball_radius * 2
    )
    return ball_rect.colliderect(target_rect)

#predicted trajectory line

def calculate_trajectory():
    points = []
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

        points.append((int(sim_x), int(sim_y)))

    return points

def draw_ui():
    global target_rect
    global ball_x, ball_y, vx, vy, launched
    global vx, vy, launched
    global gravity, mass, drag_k, wind_x
    info = [
        f"Level: {current_level}",
        f"Gravity: {gravity:.1f}",
        f"Mass: {mass:.2f}",
        f"Drag: {drag_k:.2f}",
        f"Wind X: {wind_x:.1f}",
        "",
        f"Angle: {angle}",
        f"Velocity: {velocity}",
        "",
        "SPACE = Launch",
        "R = Reset"
    ]

    scoretext = f"Score: {score}"

    y_offset = 10
    for line in info:
        text = font.render(line, True, (0,0,0))
        screen.blit(text, (10, y_offset))
        y_offset += 22
    
    scoretextobject = font.render(scoretext, True, (0,0,0))
    screen.blit(scoretextobject, (WIDTH-scoretextobject.get_width()-10, 10))

def level1():
    screen.fill((128, 128, 128))
    pygame.draw.rect(screen, (80, 80, 80), floor_rect)
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
    screen.fill((255, 128, 0))
    pygame.draw.rect(screen, (153, 76, 0), floor_rect)
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
    screen.fill((0, 128, 255))
    pygame.draw.rect(screen, (0, 153, 0), floor_rect)
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
    screen.fill((192, 192, 192))
    pygame.draw.rect(screen, (160, 160, 160), floor_rect)
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
    screen.fill((255, 0, 0))
    pygame.draw.rect(screen, (153, 0, 0), floor_rect)
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
    screen.fill((153, 73, 0))
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
    screen.fill((153, 153, 0))
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
    screen.fill((0, 204, 204))
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
    screen.fill((0, 0, 153))
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
    screen.fill((255, 255, 255))
    pygame.draw.rect(screen, (80, 80, 80), floor_rect)
    global score, current_level
    pygame.draw.rect(screen, (10, 100, 0), target_rect)

    if check_hit():
        youwin = font.render("CONGRATULATIONS! YOU HAVE COMPLETED THE GAME!", True, (0, 0, 0))
        screen.blit(youwin, (WIDTH//2 - 60,50))
        pygame.display.flip()
        pygame.time.delay(10000)
        

LEVELS = [level1, level2, level3, level4, level5, level6, level7, level8, level9, winlevel10]
current_level = 1

#def updatescore():
#    scoretext = f"Score: {score}"
#    scoretextobject = font.render(scoretext, True, (0,0,0))
#    screen.blit(scoretextobject, (WIDTH-scoretextobject.width-10, 10))

# -------------------------
# MAIN LOOP
# -------------------------
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
    
    keys = pygame.key.get_pressed()
    if keys[pygame.K_r] or (ball_x > WIDTH):
        reset_round()

    if not launched:
        if keys[pygame.K_UP]:
            angle += 1
        if keys[pygame.K_DOWN]:
            angle -= 1
        if keys[pygame.K_RIGHT]:
            velocity += 5
        if keys[pygame.K_LEFT]:
            velocity -= 5

    angle = max(5, min(85, angle))
    velocity = max(50, min(1000, velocity))
    rad = math.radians(angle)

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
    
    # Draw launcher line
    #if not launched:
    #    rad = math.radians(angle)
    #    lx = ball_x + 40 * math.cos(rad)
    #    ly = ball_y - 40 * math.sin(rad)
    #    pygame.draw.line(screen, (0,0,0), (ball_x, ball_y), (lx, ly), 3)

    # Draw predicted trajectory as a dotted line
    if not launched:
        trajectory_points = calculate_trajectory()
        if len(trajectory_points) > 1:
            for i in range(0, len(trajectory_points)-1, 3):  # skip every 3 points to create gaps
                start = trajectory_points[i]
                end = trajectory_points[i+1]
                pygame.draw.line(screen, (150, 150, 150), start, end, 2)


    draw_ui()

    pygame.display.flip()

pygame.quit()
sys.exit()
