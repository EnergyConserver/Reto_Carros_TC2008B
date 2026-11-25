import math
import pygame

from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective

from Configuracion import (
    ANCHO_VENTANA,
    ALTO_VENTANA,
    CENTRO_X,
    CENTRO_Z
)

class Camara:

    def __init__(self):
        self.angulo = 45.0
        self.radio = 410.0
        self.altura = 350.0

        self.desplazamiento_x = 0.0
        self.desplazamiento_z = 0.0

        self.fov = 60.0

    def actualizar_proyeccion(self):

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        gluPerspective(
            self.fov,
            ANCHO_VENTANA / ALTO_VENTANA,
            1,
            1500
        )

        glMatrixMode(GL_MODELVIEW)

    def actualizar(self):

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        rad = math.radians(self.angulo)

        objetivo_x = CENTRO_X + self.desplazamiento_x
        objetivo_z = CENTRO_Z + self.desplazamiento_z

        ojo_x = objetivo_x + self.radio * math.cos(rad)
        ojo_z = objetivo_z + self.radio * math.sin(rad)

        gluLookAt(
            ojo_x, self.altura, ojo_z,
            objetivo_x, 0, objetivo_z,
            0, 1, 0
        )

    def mover(self, teclas, dt):

        velocidad = 150.0
        velocidad_zoom = 40.0

        if teclas[pygame.K_LEFT]:
            self.angulo -= 70.0 * dt

        if teclas[pygame.K_RIGHT]:
            self.angulo += 70.0 * dt

        if teclas[pygame.K_UP]:
            self.fov -= velocidad_zoom * dt

        if teclas[pygame.K_DOWN]:
            self.fov += velocidad_zoom * dt

        self.fov = max(10.0, min(self.fov, 90.0))

        rad = math.radians(self.angulo)

        if teclas[pygame.K_a]:
            self.desplazamiento_x -= math.sin(rad) * velocidad * dt
            self.desplazamiento_z += math.cos(rad) * velocidad * dt

        if teclas[pygame.K_d]:
            self.desplazamiento_x += math.sin(rad) * velocidad * dt
            self.desplazamiento_z -= math.cos(rad) * velocidad * dt

        if teclas[pygame.K_w]:
            self.desplazamiento_x -= math.cos(rad) * velocidad * dt
            self.desplazamiento_z -= math.sin(rad) * velocidad * dt

        if teclas[pygame.K_s]:
            self.desplazamiento_x += math.cos(rad) * velocidad * dt
            self.desplazamiento_z += math.sin(rad) * velocidad * dt
