import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_TIMES_ROMAN_24
import math
from PIL import Image
import random
import time

# --- Ayarlar ---
WIDTH, HEIGHT = 1280, 720
MOVE_SPEED = 40.0
MOUSE_SENSITIVITY = 0.1
CAMERA_HEIGHT = 20
TILE_SIZE = 50
STARTING_POSITION = [0.0, CAMERA_HEIGHT, 130.0]
DEFAULT_YAW = 0.0
DEFAULT_PITCH = 0.0

# --- Pygame ve OpenGL Başlat ---
pygame.init()
pygame.mixer.init()
glutInit()
pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 16)
screen = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
pygame.display.set_caption('FPS Tapınak Sahnesi')
pygame.event.set_grab(True)
pygame.mouse.set_visible(False)

# Perspektif
glMatrixMode(GL_PROJECTION)
gluPerspective(80, (WIDTH / HEIGHT), 0.1, 1000.0)
glMatrixMode(GL_MODELVIEW)

# Kamera
cam_pos = STARTING_POSITION[:]
yaw = DEFAULT_YAW
pitch = DEFAULT_PITCH

score = 0
lives = 3
font = pygame.font.SysFont('Arial', 36)

portal_x = 0.0
portal_y = 20
portal_z = -294.0

portal2_x = 0.0
portal2_y = 20
portal2_z = -2494.0

#Sesler
rock_hit_sound = pygame.mixer.Sound("sounds/rock_hit.mp3")
wood_hit_sound = pygame.mixer.Sound("sounds/wood_hit.mp3")
coin_collect_sound = pygame.mixer.Sound("sounds/coin_collect.mp3")
theme_sound = pygame.mixer.Sound("sounds/theme.mp3")
portal_sound = pygame.mixer.Sound("sounds/portal.mp3")


# Update coin rotations
coin_rotation_speed = 180  # Degrees per second

# --- Ana Döngü ---
scene1=False
scene2=False

rolling_cylinders = [
    {"x": -700.0, "z": -253.0, "angle": 0.0},
    {"x": -600.0, "z": -203.0, "angle": 0.0},
    {"x": -500.0, "z": -153.0,  "angle": 0.0},
    {"x": -400.0, "z": -33.0,    "angle": 0.0},
    {"x": -300.0, "z": 17.0,   "angle": 0.0},
    {"x": -200.0, "z": 67.0,  "angle": 0.0}
]
cylinder_speed = 230.0  

rock_positions = []  # Her rock: [x, y, z, vx, vy, vz]
rock_last_spawn = 0
rock_spawn_interval = 0.3

# Fırlatma noktaları
rock_sources = [
    (-100, 250, -2500),
    (0, 300, -2500),
    (100, 250, -2500),
    (-200, 300, -2500),
    (150, 250, -2500),
    (-150, 300, -2500),
    (200, 250, -2500)
]

rock_speed = 500.0  # Taşların hızı

column_positions = [
    (-100, -260), (100, -260),
    (-100, -210), (100, -210),
    (-100, -160), (100, -160),
    (-100, -110), (100, -110),
    (-100,  -40), (100, -40),
    (-100,  10), (100, 10),
    (-100,  60), (100, 60),
    (-100,  110), (100, 110)
]

column2_positions = [
    (-130, -1550), (45, -1580), (170, -1605),
    (-175, -1620), (15, -1650), (-75, -1690),
    (120, -1725), (-50, -1755), (180, -1770),
    (-90, -1800), (0, -1820), (-160, -1855),
    (110, -1890), (60, -1925), (-140, -1950),
    (165, -1985), (-20, -2020), (90, -2055),
    (-170, -2080), (25, -2100), (-100, -2135),
    (130, -2160), (-30, -2190), (160, -2220),
    (-110, -2260), (70, -2290), (-60, -2320),
    (180, -2360), (-10, -2410), (100, -2400)
]

wall_positions = [
    # ÜST duvar (yukarıda)
    ((0, -300), 400, 10),  # Sütunlar -250'deydi, -270 yapıldı
    # ALT duvar (aşağıda)
    ((0, 150), 400, 10),   # Sütunlar 100'deydi, 120 yapıldı
    # ORTA sol duvar
    ((-120, -75), 150, 10),
    # ORTA sağ duvar
    ((120, -75), 150, 10),
    # SOL duvar
    ((-200, -75), 10, 460),  # Sütunlar -100’deydi, -120’ye alındı
    # SAĞ duvar
    ((200, -75), 10, 460),   # Sütunlar +100’deydi, +120’ye alındı
]

wall2_positions = [
    # ÜST duvar (yukarıda)
    ((0, -2500), 400, 10),  # Sütunlar -250'deydi, -270 yapıldı
    # ALT duvar (aşağıda)
    ((0, -1500), 400, 10),   # Sütunlar 100'deydi, 120 yapıldı
    # SOL duvar
    ((-200, -2000), 10, 1000),  # Sütunlar -100’deydi, -120’ye alındı
    # SAĞ duvar
    ((200, -2000), 10, 1000),   # Sütunlar +100’deydi, +120’ye alındı
]

def load_texture(path):
    img = Image.open(path)
    img_data = img.convert("RGB").tobytes()
    width, height = img.size

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)

    glGenerateMipmap(GL_TEXTURE_2D)

    # Daha az smoothing (keskin görünüm)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

    # Anisotropic Filtering (destekleniyorsa)
    try:
        from OpenGL.GL import GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT, GL_TEXTURE_MAX_ANISOTROPY_EXT
        max_aniso = glGetFloatv(GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAX_ANISOTROPY_EXT, min(16.0, max_aniso))  # isteğe göre düşürüldü
    except:
        pass

    return tex_id

scene1floor_texture = load_texture("images/floor1.jpg")
scene2floor_texture = load_texture("images/floor2.jpg")
column1_texture = load_texture("images/column1.jpg")
column2_texture = load_texture("images/column2.png")
wall_texture = load_texture("images/wall1.png")
wall2_texture = load_texture("images/wall2.png")
tomruk_texture = load_texture("images/tomruk.jpg")
tomrukyan_texture = load_texture("images/tomruk_yan.jpg")
portal1_texture = load_texture("images/portal1.png")
portal2_texture = load_texture("images/portal2.png")
coin_texture = load_texture("images/coin.jpg")
rock_texture = load_texture("images/rock.jpg")

def draw_ground_scene1():
    glBindTexture(GL_TEXTURE_2D, scene1floor_texture)
    glEnable(GL_TEXTURE_2D)

    for x in range(-200, 200, TILE_SIZE):
        for z in range(-300, 150, TILE_SIZE):
            glBegin(GL_QUADS)

            glTexCoord2f(0, 0); glVertex3f(x, 0, z)
            glTexCoord2f(1, 0); glVertex3f(x + TILE_SIZE, 0, z)
            glTexCoord2f(1, 1); glVertex3f(x + TILE_SIZE, 0, z + TILE_SIZE)
            glTexCoord2f(0, 1); glVertex3f(x, 0, z + TILE_SIZE)

            glEnd()

    glDisable(GL_TEXTURE_2D)

def draw_ground_scene2():
    glBindTexture(GL_TEXTURE_2D, scene2floor_texture)
    glEnable(GL_TEXTURE_2D)

    for x in range(-200, 200, TILE_SIZE):
        for z in range(-2500, -1500, TILE_SIZE):
            glBegin(GL_QUADS)

            glTexCoord2f(0, 0); glVertex3f(x, 0, z)
            glTexCoord2f(1, 0); glVertex3f(x + TILE_SIZE, 0, z)
            glTexCoord2f(1, 1); glVertex3f(x + TILE_SIZE, 0, z + TILE_SIZE)
            glTexCoord2f(0, 1); glVertex3f(x, 0, z + TILE_SIZE)

            glEnd()

    glDisable(GL_TEXTURE_2D)    

def draw_column():
    quad = gluNewQuadric()
    gluQuadricTexture(quad, True)  # Doku kullanılacak

    glPushMatrix()
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, column1_texture)

    # 🔁 Doku tekrarını ayarlamak için texture matrix
    glMatrixMode(GL_TEXTURE)
    glPushMatrix()
    glLoadIdentity()
    glScalef(1.5, 6.0, 1.0)  # V ekseninde 10 kez tekrar et
    glMatrixMode(GL_MODELVIEW)

    # Silindiri çiz
    glTranslatef(0, 0, 0)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quad, 7, 7, 120, 32, 32)

    # 🔁 Texture matrix sıfırla
    glMatrixMode(GL_TEXTURE)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    glDisable(GL_TEXTURE_2D)
    glPopMatrix()

def draw_column2():
    quad = gluNewQuadric()
    gluQuadricTexture(quad, True)  # Doku kullanılacak

    glPushMatrix()
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, column2_texture)

    # 🔁 Doku tekrarını ayarlamak için texture matrix
    glMatrixMode(GL_TEXTURE)
    glPushMatrix()
    glLoadIdentity()
    glScalef(1.5, 6.0, 1.0)  # V ekseninde 10 kez tekrar et
    glMatrixMode(GL_MODELVIEW)

    # Silindiri çiz
    glTranslatef(0, 0, 0)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quad, 7, 7, 100, 32, 32)

    # 🔁 Texture matrix sıfırla
    glMatrixMode(GL_TEXTURE)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    glDisable(GL_TEXTURE_2D)
    glPopMatrix()

def draw_wall(width, height, depth):
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, wall_texture)

    w = width / 2
    d = depth / 2

    tile_u = width / 100  # X ekseninde kaç kez tekrarlansın
    tile_v = height / 100  # Y ekseninde kaç kez tekrarlansın
    tile_d = depth / 100  # Z ekseninde kaç kez tekrarlansın

    glBegin(GL_QUADS)

    # Ön
    glTexCoord2f(0, 0); glVertex3f(-w, 0, -d)
    glTexCoord2f(tile_u, 0); glVertex3f(w, 0, -d)
    glTexCoord2f(tile_u, tile_v); glVertex3f(w, height, -d)
    glTexCoord2f(0, tile_v); glVertex3f(-w, height, -d)

    # Orta Sol
    glTexCoord2f(0, 0); glVertex3f(-w, 0, -d)
    glTexCoord2f(tile_u, 0); glVertex3f(w, 0, -d)
    glTexCoord2f(tile_u, tile_v); glVertex3f(w, height, -d)
    glTexCoord2f(0, tile_v); glVertex3f(-w, height, -d)

    # Arka
    glTexCoord2f(0, 0); glVertex3f(-w, 0, d)
    glTexCoord2f(tile_u, 0); glVertex3f(w, 0, d)
    glTexCoord2f(tile_u, tile_v); glVertex3f(w, height, d)
    glTexCoord2f(0, tile_v); glVertex3f(-w, height, d)

    # Sol
    glTexCoord2f(0, 0); glVertex3f(-w, 0, -d)
    glTexCoord2f(tile_d, 0); glVertex3f(-w, 0, d)
    glTexCoord2f(tile_d, tile_v); glVertex3f(-w, height, d)
    glTexCoord2f(0, tile_v); glVertex3f(-w, height, -d)

    # Sağ
    glTexCoord2f(0, 0); glVertex3f(w, 0, -d)
    glTexCoord2f(tile_d, 0); glVertex3f(w, 0, d)
    glTexCoord2f(tile_d, tile_v); glVertex3f(w, height, d)
    glTexCoord2f(0, tile_v); glVertex3f(w, height, -d)

    # Üst
    glTexCoord2f(0, 0); glVertex3f(-w, height, -d)
    glTexCoord2f(tile_u, 0); glVertex3f(w, height, -d)
    glTexCoord2f(tile_u, tile_d); glVertex3f(w, height, d)
    glTexCoord2f(0, tile_d); glVertex3f(-w, height, d)

    glEnd()
    glDisable(GL_TEXTURE_2D)
    
def draw_wall2(width, height, depth):
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, wall2_texture)

    w = width / 2
    d = depth / 2

    tile_u = width / 100  # X ekseninde kaç kez tekrarlansın
    tile_v = height / 100  # Y ekseninde kaç kez tekrarlansın
    tile_d = depth / 100  # Z ekseninde kaç kez tekrarlansın

    glBegin(GL_QUADS)

    # Ön
    glTexCoord2f(0, 0); glVertex3f(-w, 0, -d)
    glTexCoord2f(tile_u, 0); glVertex3f(w, 0, -d)
    glTexCoord2f(tile_u, tile_v); glVertex3f(w, height, -d)
    glTexCoord2f(0, tile_v); glVertex3f(-w, height, -d)

    # Orta Sol
    glTexCoord2f(0, 0); glVertex3f(-w, 0, -d)
    glTexCoord2f(tile_u, 0); glVertex3f(w, 0, -d)
    glTexCoord2f(tile_u, tile_v); glVertex3f(w, height, -d)
    glTexCoord2f(0, tile_v); glVertex3f(-w, height, -d)

    # Arka
    glTexCoord2f(0, 0); glVertex3f(-w, 0, d)
    glTexCoord2f(tile_u, 0); glVertex3f(w, 0, d)
    glTexCoord2f(tile_u, tile_v); glVertex3f(w, height, d)
    glTexCoord2f(0, tile_v); glVertex3f(-w, height, d)

    # Sol
    glTexCoord2f(0, 0); glVertex3f(-w, 0, -d)
    glTexCoord2f(tile_d, 0); glVertex3f(-w, 0, d)
    glTexCoord2f(tile_d, tile_v); glVertex3f(-w, height, d)
    glTexCoord2f(0, tile_v); glVertex3f(-w, height, -d)

    # Sağ
    glTexCoord2f(0, 0); glVertex3f(w, 0, -d)
    glTexCoord2f(tile_d, 0); glVertex3f(w, 0, d)
    glTexCoord2f(tile_d, tile_v); glVertex3f(w, height, d)
    glTexCoord2f(0, tile_v); glVertex3f(w, height, -d)

    # Üst
    glTexCoord2f(0, 0); glVertex3f(-w, height, -d)
    glTexCoord2f(tile_u, 0); glVertex3f(w, height, -d)
    glTexCoord2f(tile_u, tile_d); glVertex3f(w, height, d)
    glTexCoord2f(0, tile_d); glVertex3f(-w, height, d)

    glEnd()
    glDisable(GL_TEXTURE_2D)    

def draw_roof(width, depth):
    # Çatı için düz bir dörtgen çizelim
    # Çatıyı, duvarların üstüne ekleyebilmek için Z eksenini biraz yükselteceğiz

    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, wall_texture)  # Çatının dokusu
    half_width = width / 2
    half_depth = depth / 2

    # Dokunun tekrarını kontrol etmek için
    tile_u = width / 100  # Dokunun X ekseninde kaç kez tekrarlansın
    tile_v = depth / 100  # Dokunun Y ekseninde kaç kez tekrarlansın

    # Çatıyı çizmek için QUADS kullanıyoruz
    glBegin(GL_QUADS)

    # Çatının dört köşesi
    glTexCoord2f(0, 0); glVertex3f(-half_width, 0, -half_depth)
    glTexCoord2f(tile_u, 0); glVertex3f(half_width, 0, -half_depth)
    glTexCoord2f(tile_u, tile_v); glVertex3f(half_width, 0, half_depth)
    glTexCoord2f(0, tile_v); glVertex3f(-half_width, 0, half_depth)

    glEnd()

    glDisable(GL_TEXTURE_2D)

def check_portal_collision(cam_x, cam_y, cam_z, portal_x, portal_y, portal_z, radius=40.0):
    distance = math.hypot(cam_x - portal_x, cam_z - portal_z + 30)
    if distance < radius:
        return True
    return False

def teleport_camera():
    # Update camera position to the destination point after portal collision
    cam_pos[0] = 0.0  # New X position after teleportation
    cam_pos[1] = CAMERA_HEIGHT  # Y remains the same
    cam_pos[2] = -1510.0  # New Z position after teleportation
    
def draw_portal(x, y, z, texture_id, radius=40.0):
    glPushMatrix()
    
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    
    glColor4f(1.0, 1.0, 1.0, 1.0)  # Texture’ın kendi renklerini bozmamak için
    
    glTranslatef(x, y, z)

    quad = gluNewQuadric()
    gluQuadricTexture(quad, True)  # <-- Bu gerekli! Texture Quadric'e uygulanmalı
    gluQuadricDrawStyle(quad, GLU_FILL)

    gluDisk(quad, 0, radius * 0.9, 64, 1)       # İç kısım

    glDisable(GL_TEXTURE_2D)
    glPopMatrix()

def draw_coin(x, y, z, radius=7.0, thickness=1.0, rotation_angle=0.0):
    glPushMatrix()

    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, coin_texture)  # coin_texture tanımlı olmalı
    glColor4f(1.0, 1.0, 1.0, 1.0)

    glTranslatef(x, y, z)
    glRotatef(rotation_angle, 0, 1, 0)  # Coinin etrafında dönme açısını uygula
    
    quad = gluNewQuadric()
    gluQuadricTexture(quad, True)
    gluQuadricDrawStyle(quad, GLU_FILL)

    # Ön yüzey (disk)
    glTranslatef(0,15,0)
    glRotatef(180, 1, 0, 0)
    gluDisk(quad, 0, radius, 32, 1)

    glDisable(GL_TEXTURE_2D)
    glPopMatrix()  

def check_collision(cam_x, cam_y, cam_z, move_x, move_z, walls, columns):
    new_x = cam_x + move_x
    new_z = cam_z + move_z

    margin = 2.0  # küçük bir tampon (dilersen 1.5 - 2.0 da deneyebilirsin)

    for (x, z), w, d in walls:
        half_w = w / 2 + margin
        half_d = d / 2 + margin
        if (new_x > x - half_w and new_x < x + half_w) and (new_z > z - half_d and new_z < z + half_d):
            return True

    for col_x, col_z in columns:
        if (new_x > col_x - 8 and new_x < col_x + 8) and (new_z > col_z - 8 and new_z < col_z + 8):
            return True

    return False

def draw_score_and_lives():
    # Draw score
    glColor3f(1, 1, 1)
    if scene1:
        if score != 50:
            glWindowPos2d(570, HEIGHT - 50)
            for c in f'Tüm Coinleri Topla':
                glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(c))
        else:
            glWindowPos2d(590, HEIGHT - 50)
            for c in f'Portala Gir':
                glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(c))
    elif scene2:
        if score != 200:
            glWindowPos2d(570, HEIGHT - 50)
            for c in f'Tüm Coinleri Topla':
                glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(c))
        else:
            glWindowPos2d(590, HEIGHT - 50)
            for c in f'Portala Gir':
                glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(c))         
                   
    glWindowPos2d(10, HEIGHT - 30)
    for c in f'Skor: {score}':
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(c))
    
    # Draw lives
    glWindowPos2d(10, HEIGHT - 60)
    for c in f'Kalan Can: {lives}':
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(c))
        
# Coin çarpışmasını kontrol et
def check_coin_collision(cam_x, cam_y, cam_z, coins):
    global score
    COIN_RADIUS = 20.0  # bu değeri oyununa göre ayarla

    for coin in coins:
        coin_x, coin_z = coin
        distance = math.hypot(cam_x - coin_x, cam_z - coin_z)
        if distance < COIN_RADIUS:
            coin_collect_sound.set_volume(0.5)
            coin_collect_sound.play()
            coins.remove(coin)
            score += 10
            break
# Silindir çarpışmasını kontrol et ve canları güncelle
def check_cylinder_collision(cam_x, cam_y, cam_z, move_x, move_z, cylinders, ):
    global lives, yaw, pitch
    new_x = cam_x + move_x
    new_z = cam_z + move_z

    cyl_radius = 7
    cyl_height = 35

    for cyl in cylinders:
        cyl_start_z = cyl["z"]
        cyl_end_z = cyl["z"] + cyl_height

        # Z ekseni boyunca silindirin içinde mi?
        if cyl_start_z <= new_z <= cyl_end_z:
            # X ekseninde silindirin yarıçapı içinde mi?
            if abs(new_x - cyl["x"]) <= cyl_radius:
                # Çarpışma gerçekleşti
                wood_hit_sound.play()
                lives -= 1
                cam_pos[0] = STARTING_POSITION[0]
                cam_pos[2] = STARTING_POSITION[2]
                yaw = DEFAULT_YAW
                pitch = DEFAULT_PITCH
                if lives <= 0:
                    return True
                break
    return False

def apply_camera():
    glRotatef(pitch, 1, 0, 0)
    glRotatef(yaw, 0, 1, 0)
    glTranslatef(-cam_pos[0], -cam_pos[1], -cam_pos[2])

def draw_rolling_cylinders():
    quad = gluNewQuadric()
    gluQuadricTexture(quad, True)  # Texture kullanılacak

    for cyl in rolling_cylinders:
        glPushMatrix()

        # Silindiri doğru konumda yerleştir
        glTranslatef(cyl["x"], 7, cyl["z"])  # Silindiri yeryüzüne yerleştir (yarıçap kadar yukarı)
        glRotatef(cyl["angle"], 0, 0, -1)  # Silindirin dönme açısını uygula

        glEnable(GL_TEXTURE_2D)
        # Texture'ı bağla
        glBindTexture(GL_TEXTURE_2D, tomruk_texture)

        # Silindiri çiz
        gluCylinder(quad, 7, 7, 35, 32, 32)  # Yarıçap 7, yükseklik 30

        glPopMatrix()
        glDisable(GL_TEXTURE_2D)

        # Alt diski çiz (silindirin alt kısmı)
        glPushMatrix()
        glTranslatef(cyl["x"], 7, cyl["z"]+35)  # Silindirin alt kısmı
        glRotatef(cyl["angle"], 0, 0, -1)  # Silindirin dönme açısını uygula
        glEnable(GL_TEXTURE_2D) # Texture'ı bağla
        glBindTexture(GL_TEXTURE_2D, tomrukyan_texture)
        gluDisk(quad, 0, 7, 32, 1)  # Alt disk çiz (yarıçap 7)
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)

        # Üst diski çiz (silindirin üst kısmı)
        glPushMatrix()
        glTranslatef(cyl["x"], 7, cyl["z"])  # Silindirin üst kısmı (30 birim yukarı)
        glRotatef(cyl["angle"], 0, 0, -1)  # Silindirin dönme açısını uygula
        glEnable(GL_TEXTURE_2D) # Texture'ı bağla
        glBindTexture(GL_TEXTURE_2D, tomrukyan_texture)
        gluDisk(quad, 0, 7, 32, 1)  # Üst disk çiz (yarıçap 7)
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)

def check_rock_collision(pos, target_y):
    global lives, scene2, yaw, pitch

    x, y, z = pos

    # Oyuncunun dikey yüksekliğini dikkate al: cam_pos[1] ile cam_pos[1] - 10 aralığı
    player_y_top = cam_pos[1]
    player_y_bottom = cam_pos[1] - 10

    # Taş, oyuncunun dikey yüksekliği içinde mi?
    if player_y_bottom <= y <= player_y_top:
        # Yatay mesafe (x ve z) ile genel mesafe kontrolü
        distance = ((x - cam_pos[0]) ** 2 + (z - cam_pos[2]) ** 2) ** 0.5
        if distance < 10:
            rock_hit_sound.play()
            lives -= 1
            cam_pos[0] = STARTING_POSITION[0]
            cam_pos[2] = STARTING_POSITION[2] - 1645
            yaw = DEFAULT_YAW
            pitch = DEFAULT_PITCH  
            return True

    # Zemine çarpma kontrolü
    if y <= target_y:
        return True

    # Sütunlara çarpma kontrolü (silindir şeklinde)
    column_radius = 10  # kolonun yarıçapı
    column_height = 100  # kolon yüksekliği (örnek)

    for col_x, col_z in column2_positions:
        dx = x - col_x
        dz = z - col_z
        horizontal_dist_squared = dx**2 + dz**2

        # Taşın y'si kolonun taban ve tavanı arasında mı kontrolü
        if y >= 0 and y <= column_height:
            # Yatayda çarpışma kontrolü (silindir çapında)
            if horizontal_dist_squared < column_radius**2:
                return True

    # Duvarlara çarpma kontrolü (dikdörtgen prizma: genişlik, yükseklik, derinlik)
    wall_height = 100

    for (wall_xz, wall_width, wall_depth) in wall2_positions:
        wall_x, wall_z = wall_xz

        min_x = wall_x - wall_width / 2
        max_x = wall_x + wall_width / 2
        min_z = wall_z - wall_depth / 2
        max_z = wall_z + wall_depth / 2
        min_y = 0
        max_y = wall_height

        if min_x <= x <= max_x and min_z <= z <= max_z and min_y <= y <= max_y:
            return True

    return False

def update_rocks(dt):
    global rock_last_spawn, lives, scene2_running

    current_time = time.time()

    if current_time - rock_last_spawn >= rock_spawn_interval:
        src = random.choice(rock_sources)

        target_x = random.uniform(cam_pos[0] - 50, cam_pos[0] + 50)
        target_y = 5
        target_z = random.uniform(cam_pos[2] - 50, cam_pos[2] + 50) 

        # Yön vektörü
        dx = target_x - src[0]
        dy = target_y - src[1]
        dz = target_z - src[2]

        length = math.sqrt(dx**2 + dy**2 + dz**2)
        if length == 0: length = 0.001  # Bölme hatası engeli

        direction = [dx / length, dy / length, dz / length]

        rock_positions.append({
            'pos': [src[0], src[1], src[2]],
            'dir': direction,
            'target_y': target_y,
            'angle': 0.0
        })

        rock_last_spawn = current_time

    to_remove = []
    for rock in rock_positions:
        # dt ile zaman bazlı hareket
        rock['pos'][0] += rock['dir'][0] * rock_speed * dt
        rock['pos'][1] += rock['dir'][1] * rock_speed * dt
        rock['pos'][2] += rock['dir'][2] * rock_speed * dt

        rock['angle'] += (30 / (2 * math.pi * 8)) * (rock_speed * dt)
        
        if check_rock_collision(rock['pos'], rock['target_y']):
            to_remove.append(rock)
        elif rock['pos'][1] <= rock['target_y']:
            to_remove.append(rock)

    for r in to_remove:
        rock_positions.remove(r)

def draw_rocks():
    for rock in rock_positions:
        glPushMatrix()
        glTranslatef(rock['pos'][0], rock['pos'][1], rock['pos'][2])
        glRotatef(rock['angle'], 1, 0, 0)
        draw_rock()
        glPopMatrix()

def draw_rock():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, rock_texture)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

    # Texture matrisi ölçekle (4 kez tekrar)
    glMatrixMode(GL_TEXTURE)
    glLoadIdentity()
    glScalef(4.0, 4.0, 1.0)
    glMatrixMode(GL_MODELVIEW)

    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glEnable(GL_COLOR_MATERIAL)

    quad = gluNewQuadric()
    gluQuadricTexture(quad, GL_TRUE)

    glPushMatrix()
    glScalef(1.0, 1.0, 1.0)
    gluSphere(quad, 8, 40, 40)
    glPopMatrix()

    gluDeleteQuadric(quad)

    glBindTexture(GL_TEXTURE_2D, 0)
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_COLOR_MATERIAL)
    glDisable(GL_LIGHT0)
    glDisable(GL_LIGHTING)

    # Texture matrisi sıfırla
    glMatrixMode(GL_TEXTURE)
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)

def is_valid_coin_position(x, z, existing_positions, walls, columns, min_distance=120):
    # Duvar çakışma kontrolü
    for (wxz, w, d) in walls:
        wx, wz = wxz
        if (x > wx - w / 2 and x < wx + w / 2) and (z > wz - d and z < wz + d):
            return False

    # Sütun çakışma kontrolü
    for col_x, col_z in columns:
        if (x > col_x - 8 and x < col_x + 8) and (z > col_z - 8 and z < col_z + 8):
            return False

    # Diğer coin'lerle mesafe kontrolü
    for pos_x, pos_z in existing_positions:
        distance = math.hypot(pos_x - x, pos_z - z)
        if distance < min_distance:
            return False

    return True

def generate_valid_coin_positions(count, walls, columns, area_bounds):
    coins = []
    tries = 0
    max_tries = 1000
    xmin, xmax, zmin, zmax = area_bounds

    while len(coins) < count and tries < max_tries:
        x = random.randint(xmin, xmax)
        z = random.randint(zmin, zmax)

        if is_valid_coin_position(x, z, coins, walls, columns):
            coins.append((x, z))

        tries += 1

    return coins

def draw_text(x, y, text, font=GLUT_BITMAP_TIMES_ROMAN_24):
    glColor3f(1, 1, 1)
    glWindowPos2d(x, y)
    for c in text:
        glutBitmapCharacter(font, ord(c))

def menu_start():
    global scene1, score, lives,cam_pos,yaw,pitch
    score = 0
    lives = 3
    cam_pos = STARTING_POSITION[:]
    yaw = DEFAULT_YAW
    pitch = DEFAULT_PITCH
    pygame.mouse.set_visible(True)  # İmleç görünür

    button_rect = pygame.Rect(540, 340, 160, 40)  # Buton alanı
    
    while True:
        # Pencereyi donmaktan kurtarır
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = event.pos
                # OpenGL'de y ekseni ters (720'yi kendi pencere yüksekliğinle değiştir)
                if button_rect.collidepoint(mouse_x, 720 - mouse_y):
                    print("Butona tıklandı!")
                    pygame.mouse.set_visible(False)
                    scene1 = True
                    return False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            pygame.quit()
            exit()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        draw_text(550, 360, "OYUNA BASLA")
        pygame.display.flip()  

def last_menu(score):
    pygame.mouse.set_visible(True)

    button_rect = pygame.Rect(540, 300, 200, 50)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if button_rect.collidepoint(mx,720 - my):
                    print("YENIDEN BASLAT")
                    pygame.mouse.set_visible(False)
                    return False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            pygame.quit()
            exit()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        draw_text(550, 480, f'Oyun Bitti! Skor: {score}')
        draw_text(550, 430, 'Çikmak için ESC\'ye basiniz.')
        draw_text(550, 320, 'YENIDEN BASLAT')

        pygame.display.flip()  

def draw_portal_background():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 1, 0, 1, -1, 1)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, portal1_texture)

    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex2f(0.0, 0.0)

    glTexCoord2f(1.0, 0.0)
    glVertex2f(1.0, 0.0)

    glTexCoord2f(1.0, 1.0)
    glVertex2f(1.0, 1.0)

    glTexCoord2f(0.0, 1.0)
    glVertex2f(0.0, 1.0)
    glEnd()

    glDisable(GL_TEXTURE_2D)
    glEnable(GL_DEPTH_TEST)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def scene_1():
    global yaw, pitch, scene1, scene2
    coin_positions = generate_valid_coin_positions(5, wall_positions, column_positions,(-180, 180, -280, 130))
    while True:
        dt = clock.tick(60) / 1000.0
        move = MOVE_SPEED * dt
        
        for cyl in rolling_cylinders:
            # Silindirin pozisyonunu güncelle (tek yönde hareket)
            cyl["x"] += cylinder_speed * dt  # Yalnızca x ekseninde hareket ediyor

            # Silindir x = 200 noktasına ulaştığında başa dönsün
            if cyl["x"] >= 200.0:
                cyl["x"] = -200.0  # Başlangıç noktalarına dön
                cyl["angle"] = 0.0  # Açıyı sıfırla

            # Silindirin yuvarlanma hareketini (dönüş açısını) güncelle
            # Yuvarlanma açısını güncellerken, silindirin dönüşü için bir hız ekleniyor
            cyl["angle"] += (180 / (2 * math.pi * 7)) * (cylinder_speed * dt)  # Yaricap 7, dönüşü ayarlıyoruz

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

        mx, my = pygame.mouse.get_rel()
        yaw += mx * MOUSE_SENSITIVITY
        pitch += my * MOUSE_SENSITIVITY
        pitch = max(-89.0, min(89.0, pitch))

        rad_yaw = math.radians(yaw)
        dir_x = math.sin(rad_yaw)
        dir_z = -math.cos(rad_yaw)
        right_x = math.cos(rad_yaw)
        right_z = math.sin(rad_yaw)

        keys = pygame.key.get_pressed()
        move_x, move_z = 0, 0
        
        # Kamerayı hareket ettirirken çarpışma kontrolünü yapalım
        if keys[pygame.K_w] and (keys[pygame.K_LSHIFT]) and not check_collision(cam_pos[0], cam_pos[1], cam_pos[2], dir_x * move, dir_z * move, wall_positions, column_positions):
            cam_pos[0] += dir_x * move * 2
            cam_pos[2] += dir_z * move * 2
        elif keys[pygame.K_w] and not check_collision(cam_pos[0], cam_pos[1], cam_pos[2], dir_x * move, dir_z * move, wall_positions, column_positions):
            cam_pos[0] += dir_x * move
            cam_pos[2] += dir_z * move
        if keys[pygame.K_s] and not check_collision(cam_pos[0], cam_pos[1], cam_pos[2], -dir_x * move, -dir_z * move, wall_positions, column_positions):
            cam_pos[0] -= dir_x * move
            cam_pos[2] -= dir_z * move
        if keys[pygame.K_a] and not check_collision(cam_pos[0], cam_pos[1], cam_pos[2], -right_x * move, -right_z * move, wall_positions, column_positions):
            cam_pos[0] -= right_x * move
            cam_pos[2] -= right_z * move
        if keys[pygame.K_d] and not check_collision(cam_pos[0], cam_pos[1], cam_pos[2], right_x * move, right_z * move, wall_positions, column_positions):
            cam_pos[0] += right_x * move
            cam_pos[2] += right_z * move
        
        if keys[pygame.K_q]:
            scene1 = False
            return False  
         
        # Coin çarpışması kontrolü
        check_coin_collision(cam_pos[0], cam_pos[1], cam_pos[2], coin_positions)
        
        # Silindir çarpışması kontrolü ve canların sıfırlanması
        if check_cylinder_collision(cam_pos[0], cam_pos[1], cam_pos[2], move_x, move_z, rolling_cylinders):
            scene1 = False  # Eğer oyun bitmişse, çık
            break    
        
        if score == 50:
            if check_portal_collision(cam_pos[0], cam_pos[1], cam_pos[2], portal_x, portal_y, portal_z):
                scene2 = True
                scene1 = False
                teleport_camera()
                theme_sound.set_volume(0.0) 
                portal_sound.play()
                start_time = time.time()
                while time.time() - start_time < 1.5:
                    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                    draw_portal_background()
                    pygame.display.flip()
                break        
            
        cam_pos[1] = CAMERA_HEIGHT

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        glLoadIdentity()

        apply_camera()
        
        draw_portal(portal_x, portal_y, portal_z, portal1_texture)
        
        for i, (x, z) in enumerate(coin_positions):
            rotation_angle = pygame.time.get_ticks() / 1000.0 * coin_rotation_speed  # Total rotation angle
            draw_coin(x, 0, z, rotation_angle=rotation_angle)
        
        draw_rolling_cylinders()
        draw_ground_scene1()
        
        for x, z in column_positions:
            glPushMatrix()
            glTranslatef(x, 0, z)
            draw_column()
            glPopMatrix()   

        # Çatıyı eklemek
        glPushMatrix()
        glTranslatef(0, 120, -75)  # Çatıyı duvarın üstüne yerleştiriyoruz (120 birim yukarı)
        draw_roof(400, 465)  # Çatının boyutları
        glPopMatrix()

        for (x, z), w, d in wall_positions:
            glPushMatrix()
            glTranslatef(x, 0, z)
            draw_wall(w, 120, d)  # Yükseklik 100 birim yapıldı
            glPopMatrix()
        
        draw_score_and_lives()     
        
        pygame.display.flip()
        
def scene_2():
    global yaw, pitch, scene2
    coin_positions2 = generate_valid_coin_positions(15, wall2_positions, column2_positions,(-180, 180, -2480, -1520))
    while True:
        dt = clock.tick(60) / 1000.0
        move = MOVE_SPEED * dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

        mx, my = pygame.mouse.get_rel()
        yaw += mx * MOUSE_SENSITIVITY
        pitch += my * MOUSE_SENSITIVITY
        pitch = max(-89.0, min(89.0, pitch))

        rad_yaw = math.radians(yaw)
        dir_x = math.sin(rad_yaw)
        dir_z = -math.cos(rad_yaw)
        right_x = math.cos(rad_yaw)
        right_z = math.sin(rad_yaw)

        keys = pygame.key.get_pressed()
        
        # Kamerayı hareket ettirirken çarpışma kontrolünü yapalım
        if keys[pygame.K_w] and (keys[pygame.K_LSHIFT]) and not check_collision(cam_pos[0], cam_pos[1], cam_pos[2], dir_x * move, dir_z * move, wall2_positions, column2_positions):
            cam_pos[0] += dir_x * move * 2
            cam_pos[2] += dir_z * move * 2
        elif keys[pygame.K_w] and not check_collision(cam_pos[0], cam_pos[1], cam_pos[2], dir_x * move, dir_z * move, wall2_positions, column2_positions):
            cam_pos[0] += dir_x * move
            cam_pos[2] += dir_z * move
        if keys[pygame.K_s] and not check_collision(cam_pos[0], cam_pos[1], cam_pos[2], -dir_x * move, -dir_z * move, wall2_positions, column2_positions):
            cam_pos[0] -= dir_x * move
            cam_pos[2] -= dir_z * move
        if keys[pygame.K_a] and not check_collision(cam_pos[0], cam_pos[1], cam_pos[2], -right_x * move, -right_z * move, wall2_positions, column2_positions):
            cam_pos[0] -= right_x * move
            cam_pos[2] -= right_z * move
        if keys[pygame.K_d] and not check_collision(cam_pos[0], cam_pos[1], cam_pos[2], right_x * move, right_z * move, wall2_positions, column2_positions):
            cam_pos[0] += right_x * move
            cam_pos[2] += right_z * move
        
        if keys[pygame.K_q]:
            scene2 = False
            return False  
        
        update_rocks(dt)
        if lives == 0:
            scene2 = False
            return False
                
        # Coin çarpışması kontrolü
        check_coin_collision(cam_pos[0], cam_pos[1], cam_pos[2], coin_positions2)
        if score == 200:
            if check_portal_collision(cam_pos[0], cam_pos[1], cam_pos[2], portal2_x, portal2_y, portal2_z):
                scene2 = False
                break
            
        cam_pos[1] = CAMERA_HEIGHT

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        glLoadIdentity()
        apply_camera()
        
        draw_rocks()

        draw_portal(portal2_x, portal2_y, portal2_z, portal2_texture)
        
        for i, (x, z) in enumerate(coin_positions2):
            rotation_angle = pygame.time.get_ticks() / 1000.0 * coin_rotation_speed  # Total rotation angle
            draw_coin(x, 0, z, rotation_angle=rotation_angle)
        
        draw_ground_scene2()
            
        for x, z in column2_positions:
            glPushMatrix()
            glTranslatef(x, 0, z)
            draw_column2()
            glPopMatrix()    
            
        for (x, z), w, d in wall2_positions:
            glPushMatrix()
            glTranslatef(x, 0, z)
            draw_wall2(w, 120, d)  # Yükseklik 100 birim yapıldı
            glPopMatrix()    
        
        draw_score_and_lives()     
        
        pygame.display.flip()    

while True:
    theme_sound.set_volume(0.8)  
    theme_sound.play()
    menu_start()
    if scene1:
        theme_sound.set_volume(0.4) 
        clock = pygame.time.Clock()
        scene_1() 
    if scene2:
        theme_sound.set_volume(0.4) 
        scene_2()
    theme_sound.set_volume(0.8)     
    last_menu(score)  
    
    pygame.display.flip()         