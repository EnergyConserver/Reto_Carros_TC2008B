"""Automovil 3D y rutas automaticas para la simulacion de Cholula."""
import math
from OpenGL.GL import glPushMatrix, glPopMatrix, glTranslatef, glRotatef, glScalef


class Carro:
    def __init__(self, dim, vel, Scale, ruta="recta_x", inicio=None):
        self.DimBoard = dim
        self.vel = float(vel)  # Unidades del mapa por segundo
        self.Scale = Scale
        self.Position = list(inicio or (155.0, 3.1, 80.0))
        self.Body_Ry = 0.0
        self.component = []
        self.ruta = ruta
        self.tiempo = 0.0

    def getComponents(self, componentes):
        self.component = componentes

    def update(self, dt):
        """Actualiza posicion usando tiempo real, independientemente de los FPS."""
        dt = min(max(float(dt), 0.0), 0.1)
        self.tiempo += dt
        recorrido = self.vel * self.tiempo

        if self.ruta == "giro":
            # Parte 1: avanza por calle vertical x=155 hacia +Z.
            # Parte 2: cuarto de circunferencia de radio 10, dentro del cruce.
            # Parte 3: continua sobre calle horizontal z=155 hacia +X.
            # Al terminar la calle, reinicia la demostracion.
            z_inicial = 72.0
            z_giro = 145.0
            radio = 10.0
            tramo_1 = z_giro - z_inicial
            tramo_giro = math.pi * radio / 2
            tramo_3 = 360.0 - (155.0 + radio)
            periodo = tramo_1 + tramo_giro + tramo_3
            s = recorrido % periodo

            if s < tramo_1:
                self.Position[0] = 155.0
                self.Position[2] = z_inicial + s
                self.Body_Ry = -90.0
            elif s < tramo_1 + tramo_giro:
                theta = (s - tramo_1) / radio
                self.Position[0] = 165.0 - radio * math.cos(theta)
                self.Position[2] = 145.0 + radio * math.sin(theta)
                self.Body_Ry = -90.0 + math.degrees(theta)
            else:
                self.Position[0] = 165.0 + s - tramo_1 - tramo_giro
                self.Position[2] = 155.0
                self.Body_Ry = 0.0

        elif self.ruta == "recta_x":
            # Calle horizontal z=280, circula hacia +X.
            self.Position[0] = 45.0 + recorrido % 325.0
            self.Position[2] = 280.0
            self.Body_Ry = 0.0

        elif self.ruta == "recta_z":
            # Calle vertical x=280, circula hacia -Z.
            self.Position[0] = 280.0
            self.Position[2] = 370.0 - recorrido % 315.0
            self.Body_Ry = 90.0

    def draw(self):
        if len(self.component) != 4:
            return
        glPushMatrix()
        glTranslatef(*self.Position)
        glRotatef(self.Body_Ry, 0, 1, 0)
        glScalef(self.Scale, self.Scale, self.Scale)
        for pieza in self.component:
            pieza.render()
        glPopMatrix()
