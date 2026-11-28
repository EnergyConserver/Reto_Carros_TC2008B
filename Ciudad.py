from OpenGL.GL import *
from Configuracion import (
    MAPA_X,
    MAPA_Z,
    ANCHO_CALLE,
    CALLES_VERTICALES,
    CALLES_HORIZONTALES
)
from pathlib import Path
from objloader import OBJ

ruta_casa = Path(__file__).resolve().parent / "casa.obj"
modelo_casa = None

def obtener_datos_casa():
    vertices = []

    with open(ruta_casa, "r") as archivo:
        for linea in archivo:
            if linea.startswith("v "):
                _, x, y, z = linea.split()[:4]
                vertices.append((float(x), float(y), float(z)))

    minimos = [min(v[i] for v in vertices) for i in range(3)]
    maximos = [max(v[i] for v in vertices) for i in range(3)]

    centro = tuple((minimos[i] + maximos[i]) / 2 for i in range(3))
    dimensiones = tuple(maximos[i] - minimos[i] for i in range(3))

    return centro, dimensiones

centro_casa, dimensiones_casa = obtener_datos_casa()

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

def dibujar_casa(x, z, ancho, largo, rotacion):
    escala = 27.5

    glPushMatrix()

    glTranslatef(x + ancho / 2, 0, z + largo / 2)
    glRotatef(rotacion, 0, 1, 0)
    glScalef(escala, escala, escala)

    glTranslatef(
        -centro_casa[0],
        -centro_casa[1] + dimensiones_casa[1] / 2,
        -centro_casa[2]
    )

    glEnable(GL_NORMALIZE)
    glColor4f(1.0, 1.0, 1.0, 1.0)

    modelo_casa.render()

    glPopMatrix()

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


def dibujar_semaforo(x, z, rotacion, estado):

    glPushMatrix()

    glTranslatef(x, 0, z)
    glRotatef(rotacion, 0, 1, 0)

    # Poste
    glColor3f(0.15, 0.15, 0.15)

    glLineWidth(5)

    glBegin(GL_LINES)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 9, 0)
    glEnd()

    glLineWidth(1)

    # Caja del semáforo
    dibujar_cubo(
        0, 9, 0,
        2.5, 6, 2,
        (0.08, 0.08, 0.08)
    )

    # Determinar qué luz está encendida
    rojo = (0.9, 0.05, 0.05) if estado == "ROJO" else (0.12, 0.12, 0.12)
    amarillo = (0.12, 0.12, 0.12)
    verde = (0.05, 0.8, 0.1) if estado == "VERDE" else (0.12, 0.12, 0.12)

    colores = [rojo, amarillo, verde]

    for i, color in enumerate(colores):

        dibujar_cubo(
            0,
            9.6 + i * 1.7,
            -1.1,
            1.5,
            1.3,
            0.3,
            color
        )

    glPopMatrix()


def dibujar_semaforos(modelo):

    for interseccion in modelo.agentes_interseccion:

        ix = interseccion.x
        iz = interseccion.z

        indice_x = modelo.centros_x.index(ix)
        indice_z = modelo.centros_z.index(iz)

        # Dirección permitida para entrar desde la calle vertical.
        direccion_vertical = "-Z" if indice_x % 2 == 0 else "+Z"

        # Dirección permitida para entrar desde la calle horizontal.
        direccion_horizontal = "+X" if indice_z % 2 == 0 else "-X"

        # Posición y orientación de cada semáforo.
        posiciones = {
            "+Z": (ix + 7, iz - 7, 180),
            "-Z": (ix - 7, iz + 7, 0),
            "+X": (ix - 7, iz - 7, 270),
            "-X": (ix + 7, iz + 7, 90)
        }

        x, z, rotacion = posiciones[direccion_vertical]

        dibujar_semaforo(
            x, z, rotacion,
            interseccion.estado_vertical
        )

        x, z, rotacion = posiciones[direccion_horizontal]

        dibujar_semaforo(
            x, z, rotacion,
            interseccion.estado_horizontal
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

    rotaciones = [
        [180, 0],
        [180, 0]
    ]

    # Cuatro casas distribuidas en 2 filas y 2 columnas
    for fila in range(2):
        for columna in range(2):

            x = x1 + margen + columna * (ancho + separacion)
            z = z1 + margen + fila * (largo + separacion)

            dibujar_casa(
                x,
                z,
                ancho,
                largo,
                rotaciones[fila][columna]
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
    global modelo_casa

    if modelo_casa is None:
        modelo_casa = OBJ(str(ruta_casa), swapyz=False)

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