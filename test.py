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

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Physics Hackathon Prototype")

clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18)

GROUND_Y = HEIGHT - 50

# -------------------------
# RANDOM PHYSICS PARAMETERS
# -------------------------
def random_parameters():
    gravity = random.uniform(300, 800)
    mass = random.uniform(0.5, 5)
    drag_k = random.uniform(0.0, 1.5)
    wind_x = random.uniform(-200, 200)

    return gravity, mass, drag_k, wind_x


# -------------------------
# FUNCTIONS
# -------------------------
global score
score = 0
def reset_round():
    global gravity, mass, drag_k, wind_x
    global ball_x, ball_y, vx, vy, launched
    global target_rect
    global angle
    global velocity
    global ball_radius

    angle = 45
    velocity = 400

    gravity, mass, drag_k, wind_x = random_parameters()

    ball_radius = 10
    ball_x = 100
    ball_y = GROUND_Y
    vx = 0
    vy = 0
    launched = False

    target_rect = pygame.Rect(
        random.randint(600, 900),
        GROUND_Y - 100,
        40,
        100
    )

reset_round()

def launch():
    global vx, vy, launched

    rad = math.radians(angle)
    vx = velocity * math.cos(rad)
    vy = -velocity * math.sin(rad)
    launched = True

def update_physics():
    global ball_x, ball_y, vx, vy, launched

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
    ball_rect = pygame.Rect(
        ball_x - ball_radius,
        ball_y - ball_radius,
        ball_radius * 2,
        ball_radius * 2
    )
    return ball_rect.colliderect(target_rect)

def draw_ui():
    info = [
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

    update_physics()

    # Draw ground
    pygame.draw.line(screen, (0,0,0), (0, GROUND_Y), (WIDTH, GROUND_Y), 2)

    # Draw target
    pygame.draw.rect(screen, (200, 0, 0), target_rect)

    # Draw ball
    pygame.draw.circle(screen, (0, 100, 255), (int(ball_x), int(ball_y)), ball_radius)

    # Draw launcher line
    if not launched:
        rad = math.radians(angle)
        lx = ball_x + 40 * math.cos(rad)
        ly = ball_y - 40 * math.sin(rad)
        pygame.draw.line(screen, (0,0,0), (ball_x, ball_y), (lx, ly), 3)

    if check_hit():
        win_text = font.render("TARGET HIT!", True, (0,150,0))
        screen.blit(win_text, (WIDTH//2 - 60, 50))
        #press key to continue

        score += 1
        reset_round()

    draw_ui()

    pygame.display.flip()

pygame.quit()
sys.exit()