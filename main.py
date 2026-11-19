import pygame
from pygame.locals import *

# Cargamos las bibliotecas de OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import math

# Se carga el archivo de la clase Cubo
import sys
sys.path.append('..')
from Carro import Carro

# Import obj loader
from objloader import *

screen_width = 1400
screen_height = 800
#vc para el obser.
FOVY=60.0
ZNEAR=1.0
ZFAR=900.0
#Variables para definir la posicion del observador
#gluLookAt(EYE_X,EYE_Y,EYE_Z,CENTER_X,CENTER_Y,CENTER_Z,UP_X,UP_Y,UP_Z)
EYE_X = 500.0
EYE_Y = 450.0
EYE_Z = 500.0
CENTER_X = 100
CENTER_Y = 0
CENTER_Z = 100
UP_X=0
UP_Y=1
UP_Z=0
#Variables para dibujar los ejes del sistema
X_MIN=0
X_MAX=450
Y_MIN=0
Y_MAX=100
Z_MIN=0
Z_MAX=450
#Dimension del plano
DimBoardX = 400
DimBoardZ = 410

# Array para los objetos tipo carro
objetos = []
carros = []
ncarros = 1

#Variables para el control del observador
theta = 0.0
radius = 200

pygame.init()

def Axis():
    glLineWidth(3.0)
    #X axis in red
    glColor3f(1.0,0.0,0.0)
    glBegin(GL_LINES)
    glVertex3f(X_MIN,0.0,0.0)
    glVertex3f(X_MAX,0.0,0.0)
    glEnd()
    #Y axis in green
    glColor3f(0.0,1.0,0.0)
    glBegin(GL_LINES)
    glVertex3f(0.0,Y_MIN,0.0)
    glVertex3f(0.0,Y_MAX,0.0)
    glEnd()
    #Z axis in blue
    glColor3f(0.0,0.0,1.0)
    glBegin(GL_LINES)
    glVertex3f(0.0,0.0,Z_MIN)
    glVertex3f(0.0,0.0,Z_MAX)
    glEnd()
    glLineWidth(1.0)


def Init():
    screen = pygame.display.set_mode(
        (screen_width, screen_height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("OpenGL: cubos")

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOVY, screen_width/screen_height, ZNEAR, ZFAR)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(EYE_X,EYE_Y,EYE_Z,CENTER_X,CENTER_Y,CENTER_Z,UP_X,UP_Y,UP_Z)
    glClearColor(0,0,0,0)
    glEnable(GL_DEPTH_TEST)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glShadeModel(GL_SMOOTH)
        
    #glLightfv(GL_LIGHT0, GL_POSITION,  (-40, 200, 100, 0.0))
    glLightfv(GL_LIGHT0, GL_POSITION,  (0, 200, 0, 0.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.5, 0.5, 0.5, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0))
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    
    # Se generan los componentes graficos del carro y se gregan
    # al array objetos
    objetos.append(OBJ("carroceria.obj", swapyz=True))
    objetos.append(OBJ("llanta_FL.obj", swapyz=True))
    objetos.append(OBJ("llanta_FR.obj", swapyz=True))
    objetos.append(OBJ("llantas_traseras.obj", swapyz=True))

    for obj in objetos:
        obj.generate()
    
    # se genera un carro
    for i in range(ncarros):
        carros.append(Carro([DimBoardX, DimBoardZ], 1.0, 3.5))
        carros[-1].getComponents(objetos)

#Se mueve al observador circularmente al rededor del plano XZ a una altura fija (EYE_Y)
def lookat():
    global EYE_X
    global EYE_Z
    global radius
    EYE_X = CENTER_X + radius * math.cos(math.radians(theta))
    EYE_Z = CENTER_Z + radius * math.sin(math.radians(theta))
    glLoadIdentity()
    gluLookAt(EYE_X,EYE_Y,EYE_Z,CENTER_X,CENTER_Y,CENTER_Z,UP_X,UP_Y,UP_Z)

def dibujarCasa(x, z, ancho, largo, altura):
    glBegin(GL_QUADS)

    # Color de las casas
    glColor3f(0.8, 0.6, 0.4)

    # Cara frontal
    glVertex3f(x, 0, z)
    glVertex3f(x + ancho, 0, z)
    glVertex3f(x + ancho, altura, z)
    glVertex3f(x, altura, z)

    # Cara trasera
    glVertex3f(x, 0, z + largo)
    glVertex3f(x + ancho, 0, z + largo)
    glVertex3f(x + ancho, altura, z + largo)
    glVertex3f(x, altura, z + largo)

    # Cara izquierda
    glVertex3f(x, 0, z)
    glVertex3f(x, 0, z + largo)
    glVertex3f(x, altura, z + largo)
    glVertex3f(x, altura, z)

    # Cara derecha
    glVertex3f(x + ancho, 0, z)
    glVertex3f(x + ancho, 0, z + largo)
    glVertex3f(x + ancho, altura, z + largo)
    glVertex3f(x + ancho, altura, z)

    # Techo
    glVertex3f(x, altura, z)
    glVertex3f(x + ancho, altura, z)
    glVertex3f(x + ancho, altura, z + largo)
    glVertex3f(x, altura, z + largo)

    # Base
    glVertex3f(x, 0, z)
    glVertex3f(x + ancho, 0, z)
    glVertex3f(x + ancho, 0, z + largo)
    glVertex3f(x, 0, z + largo)

    glEnd()

#Generacion de manzanas
def dibujarManzanas(x_inicio, z_inicio, columnas, filas, ancho, largo, separacion_x, separacion_z):
    glColor3f(0.2, 0.5, 0.2)
    glBegin(GL_QUADS)

    for fila in range(filas):
        for columna in range(columnas):

            # Coordenadas de la manzana
            x = x_inicio + columna * (ancho + separacion_x)
            z = z_inicio + fila * (largo + separacion_z)

            # Dibujar manzana
            glVertex3d(x, 0.1, z)
            glVertex3d(x, 0.1, z + largo)
            glVertex3d(x + ancho, 0.1, z + largo)
            glVertex3d(x + ancho, 0.1, z)

    glEnd()

    # Distribución de las casas
    margen = 5
    separacion_casas = 5

    ancho_casa = (ancho - 2 * margen - separacion_casas) / 2
    largo_casa = (largo - 2 * margen - separacion_casas) / 2

    altura = 25

    for fila in range(filas):
        for columna in range(columnas):

            x = x_inicio + columna * (ancho + separacion_x)
            z = z_inicio + fila * (largo + separacion_z)

            # Cuatro casas por manzana
            for i in range(2):
                for j in range(2):

                    x_casa = x + margen + i * (ancho_casa + separacion_casas)
                    z_casa = z + margen + j * (largo_casa + separacion_casas)

                    dibujarCasa(x_casa, z_casa, ancho_casa, largo_casa, altura)


def dibujarLineaAvenida(ancho_manzana, separacion, columnas, x_inicio):
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(3.0)

    glBegin(GL_LINES)

    for columna in range(columnas):
        x = x_inicio + columna * (ancho_manzana + separacion)

        glVertex3d(x, 0.2, 200)
        glVertex3d(x + ancho_manzana, 0.2, 200)

    glEnd()

    glLineWidth(1.0)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    Axis()
    #Se dibuja el plano gris
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_QUADS)
    glVertex3d(0, 0, 0)
    glVertex3d(0, 0, DimBoardZ)
    glVertex3d(DimBoardX, 0, DimBoardZ)
    glVertex3d(DimBoardX, 0, 0)
    glEnd()

    # Se dibujan las manzanas
    dibujarManzanas(x_inicio=0, z_inicio=0, columnas=7, filas=3, ancho=40, largo=40, separacion_x=20, separacion_z=20)
    dibujarManzanas(x_inicio=0, z_inicio=250, columnas=7, filas=3, ancho=40, largo=40, separacion_x=20, separacion_z=20)

    dibujarLineaAvenida(ancho_manzana=40, separacion=20, columnas=7, x_inicio=0)
        
    # Se dibuja el carro
    for car in carros:
        car.update()
        car.draw()
    
done = False
Init()
while not done:
    keys = pygame.key.get_pressed()
    #avanzar observador
    if keys[pygame.K_RIGHT]:
        if theta > 359.0:
            theta = 0
        else:
            theta += 1.0
        lookat()        
    if keys[pygame.K_LEFT]:
        if theta < 1.0:
            theta = 360.0
        else:
            theta += -1.0
        lookat()
    # solo se controla el ultimo carrito en el array
    if keys[pygame.K_w]:
        carros[-1].setAvanza()
    if keys[pygame.K_a]:
        carros[-1].setRota('L')
    if keys[pygame.K_d]:
        carros[-1].setRota('R')
    
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                done = True

    display()

    pygame.display.flip()
    pygame.time.wait(10)

pygame.quit()