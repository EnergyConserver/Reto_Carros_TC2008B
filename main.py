import math
from pathlib import Path

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *

from Agentes import ModeloTrafico
from Carro import Carro
from objloader import OBJ

from Camara import Camara
from Configuracion import (
    ANCHO_VENTANA,
    ALTO_VENTANA,
    MAPA_X,
    MAPA_Z,
    INTERVALO_SIMULACION,
    FPS,
    ORIENTACIONES,
    CONFIGURACIONES_CARROS
)

import Ciudad


def iniciar():
    pygame.init()

    pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA), DOUBLEBUF | OPENGL)

    pygame.display.set_caption("Carro 3D - Calles y manzanas 2x2")

    # Configuración de OpenGL
    glClearColor(0.08, 0.09, 0.13, 1)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)

    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    glLightfv(GL_LIGHT0, GL_POSITION, (200, 500, 200, 1))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.55, 0.55, 0.55, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.75, 0.75, 0.75, 1))

def obtener_centro_obj(ruta):
    vertices = []
    with open(ruta, "r") as archivo:
        for linea in archivo:
            if linea.startswith("v "):
                _, x, y, z = linea.split()[:4]
                vertices.append((float(x), float(z), float(y)))

    minimos = [min(v[i] for v in vertices) for i in range(3)]
    maximos = [max(v[i] for v in vertices) for i in range(3)]

    return tuple((minimos[i] + maximos[i]) / 2 for i in range(3))


def cargar_carros():
    carpeta = Path(__file__).resolve().parent

    nombres = (
        "carroceria.obj",
        "llanta_FL.obj",
        "llanta_FR.obj",
        "llantas_traseras.obj"
    )

    carros = []
    centro_FL = obtener_centro_obj(carpeta / nombres[1])
    centro_FR = obtener_centro_obj(carpeta / nombres[2])
    centro_TR = obtener_centro_obj(carpeta / nombres[3])

    for x, z, orientacion, color in CONFIGURACIONES_CARROS:
        carroceria = OBJ(str(carpeta / nombres[0]), swapyz=True, body_color=color)

        llantas = [
            OBJ(str(carpeta / nombre), swapyz=True)
            for nombre in nombres[1:]
        ]

        vehiculo = Carro([MAPA_X, MAPA_Z], 0, 2.7, inicio=(x, 3.1, z))

        vehiculo.Body_Ry = orientacion
        vehiculo.centro_FL = centro_FL
        vehiculo.centro_FR = centro_FR
        vehiculo.centro_TR = centro_TR
        vehiculo.getComponents([carroceria] + llantas)

        carros.append(vehiculo)

    return carros


def dibujar(carros):

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    Ciudad.dibujar_ciudad()
    Ciudad.dibujar_flechas()
    Ciudad.dibujar_semaforos()

    for vehiculo in carros:
        vehiculo.draw()

    pygame.display.flip()


def main():
    iniciar()

    camara = Camara()
    camara.actualizar_proyeccion()

    carros = cargar_carros()

    # Modelo multiagente
    modelo = ModeloTrafico()
    modelo.sim_setup()

    acumulador = 0.0
    reloj = pygame.time.Clock()

    ejecutando = True
    pausado = False

    camara.actualizar()

    while ejecutando:
        dt = reloj.tick(FPS) / 1000.0

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    ejecutando = False
                elif evento.key == pygame.K_SPACE:
                    pausado = not pausado

        teclas = pygame.key.get_pressed()

        camara.mover(teclas, dt)
        camara.actualizar_proyeccion()
        camara.actualizar()

        # Simulación
        if not pausado:
            acumulador += dt
            while acumulador >= INTERVALO_SIMULACION:
                posiciones_anteriores = [
                    (agente.x, agente.z)
                    for agente in modelo.carros
                ]

                modelo.sim_step()

                for agente, vehiculo, posicion_anterior in zip(modelo.carros, carros, posiciones_anteriores):

                    dx = agente.x - posicion_anterior[0]
                    dz = agente.z - posicion_anterior[1]

                    distancia = math.hypot(dx, dz)

                    vehiculo.actualizar_ruedas(distancia)

                    vehiculo.Position = [
                        agente.x,
                        3.1,
                        agente.z
                    ]

                    vehiculo.Body_Ry = ORIENTACIONES[agente.direccion]

                acumulador -= INTERVALO_SIMULACION

        # Renderizado
        dibujar(carros)

    pygame.quit()


if __name__ == "__main__":
    main()