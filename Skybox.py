import pygame

from OpenGL.GL import *
from OpenGL.GLU import *

class Skybox:

    def __init__(self, ruta):
        
        imagen = pygame.image.load(ruta)
        ancho, alto = imagen.get_size()
        datos = pygame.image.tostring(
            imagen,
            "RGB",
            True
        )

        # Guardar estado de textura
        glPushAttrib(GL_TEXTURE_BIT)

        # Crear textura
        self.textura = glGenTextures(1)

        glBindTexture(GL_TEXTURE_2D, self.textura)

        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGB,
            ancho,
            alto,
            0,
            GL_RGB,
            GL_UNSIGNED_BYTE,
            datos
        )

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        # Restaurar estado anterior
        glPopAttrib()

        # Crear esfera
        self.esfera = gluNewQuadric()

        gluQuadricTexture(self.esfera, GL_TRUE)
        gluQuadricOrientation(self.esfera, GLU_INSIDE)

    def dibujar(self, x, y, z):

        glPushAttrib(GL_ALL_ATTRIB_BITS)

        glDisable(GL_LIGHTING)
        glDisable(GL_LIGHT0)
        glDisable(GL_COLOR_MATERIAL)

        glDisable(GL_DEPTH_TEST)
        glDepthMask(GL_FALSE)

        glDisable(GL_CULL_FACE)

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.textura)

        glColor3f(1.0, 1.0, 1.0)

        glPushMatrix()

        glTranslatef(x, y, z)
        glRotatef(-90, 1, 0, 0)

        gluSphere(self.esfera, 1000, 60, 60)

        glPopMatrix()

        glPopAttrib()