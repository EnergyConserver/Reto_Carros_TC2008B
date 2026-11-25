from OpenGL.GL import *
from Configuracion import (
    MAPA_X,
    MAPA_Z,
    ANCHO_CALLE,
    CALLES_VERTICALES,
    CALLES_HORIZONTALES
)

def generar_calles(limite, numero_manzanas, ancho_calle):
    calles = []

    espacio_manzana = (
        limite - (numero_manzanas + 1) * ancho_calle
    ) / numero_manzanas

    posicion = ancho_calle

    for i in range(numero_manzanas - 1):
        calles.append(posicion)
        posicion += espacio_manzana + ancho_calle

    return calles

def rectangulo_suelo(x1, z1, x2, z2, y, color):
    glColor3f(*color)

    glBegin(GL_QUADS)

    glVertex3f(x1, y, z1)
    glVertex3f(x2, y, z1)
    glVertex3f(x2, y, z2)
    glVertex3f(x1, y, z2)

    glEnd()

def dibujar_casa(x, z, ancho, largo, altura):

    glColor3f(0.68, 0.49, 0.33)

    glBegin(GL_QUADS)

    # Pared frontal
    glNormal3f(0, 0, -1)

    glVertex3f(x, 0, z)
    glVertex3f(x, altura, z)
    glVertex3f(x + ancho, altura, z)
    glVertex3f(x + ancho, 0, z)

    # Pared trasera
    glNormal3f(0, 0, 1)

    glVertex3f(x, 0, z + largo)
    glVertex3f(x + ancho, 0, z + largo)
    glVertex3f(x + ancho, altura, z + largo)
    glVertex3f(x, altura, z + largo)

    # Pared izquierda
    glNormal3f(-1, 0, 0)

    glVertex3f(x, 0, z)
    glVertex3f(x, 0, z + largo)
    glVertex3f(x, altura, z + largo)
    glVertex3f(x, altura, z)

    # Pared derecha
    glNormal3f(1, 0, 0)

    glVertex3f(x + ancho, 0, z)
    glVertex3f(x + ancho, altura, z)
    glVertex3f(x + ancho, altura, z + largo)
    glVertex3f(x + ancho, 0, z + largo)

    # Techo
    glNormal3f(0, 1, 0)

    glVertex3f(x, altura, z)
    glVertex3f(x, altura, z + largo)
    glVertex3f(x + ancho, altura, z + largo)
    glVertex3f(x + ancho, altura, z)

    glEnd()

def dibujar_cubo(x, y, z, ancho, alto, largo, color):

    glColor3f(*color)

    x1 = x - ancho / 2
    x2 = x + ancho / 2

    y1 = y
    y2 = y + alto

    z1 = z - largo / 2
    z2 = z + largo / 2

    glBegin(GL_QUADS)

    # Frente
    glVertex3f(x1, y1, z1)
    glVertex3f(x2, y1, z1)
    glVertex3f(x2, y2, z1)
    glVertex3f(x1, y2, z1)

    # Atrás
    glVertex3f(x1, y1, z2)
    glVertex3f(x1, y2, z2)
    glVertex3f(x2, y2, z2)
    glVertex3f(x2, y1, z2)

    # Izquierda
    glVertex3f(x1, y1, z1)
    glVertex3f(x1, y1, z2)
    glVertex3f(x1, y2, z2)
    glVertex3f(x1, y2, z1)

    # Derecha
    glVertex3f(x2, y1, z1)
    glVertex3f(x2, y2, z1)
    glVertex3f(x2, y2, z2)
    glVertex3f(x2, y1, z2)

    # Superior
    glVertex3f(x1, y2, z1)
    glVertex3f(x1, y2, z2)
    glVertex3f(x2, y2, z2)
    glVertex3f(x2, y2, z1)

    # Inferior
    glVertex3f(x1, y1, z1)
    glVertex3f(x2, y1, z1)
    glVertex3f(x2, y1, z2)
    glVertex3f(x1, y1, z2)

    glEnd()


def dibujar_semaforo(x, z):

    # Poste
    glColor3f(0.15, 0.15, 0.15)

    glLineWidth(5)

    glBegin(GL_LINES)
    glVertex3f(x, 0, z)
    glVertex3f(x, 9, z)
    glEnd()

    glLineWidth(1)

    # Caja del semáforo
    dibujar_cubo(
        x, 9, z,
        2.5, 6, 2,
        (0.08, 0.08, 0.08)
    )

    # Luces
    colores = [
        (0.9, 0.05, 0.05),   # Rojo
        (0.95, 0.65, 0.05),  # Amarillo
        (0.05, 0.8, 0.1)     # Verde
    ]

    for i, color in enumerate(colores):

        dibujar_cubo(
            x,
            9.6 + i * 1.7,
            z - 1.1,
            1.5,
            1.3,
            0.3,
            color
        )


def dibujar_semaforos():
    for x in CALLES_VERTICALES:

        for z in CALLES_HORIZONTALES:

            centro_x = x + ANCHO_CALLE / 2
            centro_z = z + ANCHO_CALLE / 2

            # Cuatro esquinas de la intersección.
            desplazamiento = 7

            esquinas = [
                (-desplazamiento, -desplazamiento),
                ( desplazamiento, -desplazamiento),
                (-desplazamiento,  desplazamiento),
                ( desplazamiento,  desplazamiento)
            ]

            for dx, dz in esquinas:

                dibujar_semaforo(
                    centro_x + dx,
                    centro_z + dz
                )

def dibujar_flecha(x, z, direccion):

    glColor3f(0.95, 0.95, 0.85)

    # Dirección de movimiento
    direcciones = {
        "+X": (1, 0),
        "-X": (-1, 0),
        "+Z": (0, 1),
        "-Z": (0, -1)
    }

    dx, dz = direcciones[direccion]

    # Vector perpendicular
    px = -dz
    pz = dx

    # Forma de la flecha
    puntos = [
        (-4.5, -1),
        ( 1.0, -1),
        ( 1.0, -2.5),
        ( 4.5,  0),
        ( 1.0,  2.5),
        ( 1.0,  1),
        (-4.5,  1)
    ]

    glBegin(GL_POLYGON)

    for frente, lateral in puntos:

        vx = x + dx * frente + px * lateral
        vz = z + dz * frente + pz * lateral

        glVertex3f(vx, 0.12, vz)

    glEnd()

def dibujar_flechas():
    for i, x in enumerate(CALLES_VERTICALES):

        centro_x = x + ANCHO_CALLE / 2

        # Alternar entre +Z y -Z
        direccion = "+Z" if i % 2 == 0 else "-Z"

        # Espacios entre calles horizontales
        tramos = tramos_entre_calles(
            MAPA_Z,
            CALLES_HORIZONTALES,
            ANCHO_CALLE
        )

        for z1, z2 in tramos:

            centro_z = (z1 + z2) / 2

            dibujar_flecha(
                centro_x,
                centro_z,
                direccion
            )

    for i, z in enumerate(CALLES_HORIZONTALES):

        centro_z = z + ANCHO_CALLE / 2

        # Alternar entre +X y -X
        direccion = "+X" if i % 2 == 0 else "-X"

        # Espacios entre calles verticales
        tramos = tramos_entre_calles(
            MAPA_X,
            CALLES_VERTICALES,
            ANCHO_CALLE
        )

        for x1, x2 in tramos:

            centro_x = (x1 + x2) / 2

            dibujar_flecha(
                centro_x,
                centro_z,
                direccion
            )

def dibujar_manzana_2x2(x1, z1, x2, z2):

    # Terreno verde de la manzana
    rectangulo_suelo(
        x1, z1, x2, z2,
        0.04,
        (0.16, 0.38, 0.16)
    )

    margen = 5.0
    separacion = 5.0

    ancho = (x2 - x1 - 2 * margen - separacion) / 2
    largo = (z2 - z1 - 2 * margen - separacion) / 2

    if ancho <= 2 or largo <= 2:
        return

    # Cuatro casas distribuidas en 2 filas y 2 columnas
    for fila in range(2):
        for columna in range(2):

            x = x1 + margen + columna * (ancho + separacion)
            z = z1 + margen + fila * (largo + separacion)

            altura = 15 + ((fila + columna) % 2) * 5

            dibujar_casa(
                x,
                z,
                ancho,
                largo,
                altura
            )

def tramos_entre_calles(limite, calles, ancho_calle):

    tramos = []
    inicio = 0

    for posicion in sorted(calles):

        if posicion > inicio:
            tramos.append((inicio, posicion))

        inicio = posicion + ancho_calle

    if inicio < limite:
        tramos.append((inicio, limite))

    return tramos


def dibujar_ciudad():

    # Asfalto base de toda la ciudad
    rectangulo_suelo(
        0, 0,
        MAPA_X, MAPA_Z,
        0,
        (0.20, 0.20, 0.22)
    )

    # Crear manzanas entre calles verticales y horizontales
    intervalos_x = tramos_entre_calles(
        MAPA_X,
        CALLES_VERTICALES,
        ANCHO_CALLE
    )

    intervalos_z = tramos_entre_calles(
        MAPA_Z,
        CALLES_HORIZONTALES,
        ANCHO_CALLE
    )

    for x1, x2 in intervalos_x:
        for z1, z2 in intervalos_z:

            if x2 - x1 >= 35 and z2 - z1 >= 35:

                dibujar_manzana_2x2(
                    x1, z1,
                    x2, z2
                )

    # Líneas blancas discontinuas
    blanco = (0.92, 0.92, 0.83)

    # Líneas de las calles verticales
    for x in CALLES_VERTICALES:

        centro = x + ANCHO_CALLE / 2

        for z1, z2 in intervalos_z:

            z = z1 + 3

            while z + 7 < z2 - 3:

                rectangulo_suelo(
                    centro - 0.45,
                    z,
                    centro + 0.45,
                    z + 7,
                    0.09,
                    blanco
                )

                z += 15

    # Líneas de las calles horizontales
    for z in CALLES_HORIZONTALES:

        centro = z + ANCHO_CALLE / 2

        for x1, x2 in intervalos_x:

            x = x1 + 3

            while x + 7 < x2 - 3:

                rectangulo_suelo(
                    x,
                    centro - 0.45,
                    x + 7,
                    centro + 0.45,
                    0.09,
                    blanco
                )

                x += 15