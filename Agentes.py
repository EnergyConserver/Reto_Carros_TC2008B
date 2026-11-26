import agentpy as ap
import random
import math
from Configuracion import ANCHO_CALLE, MAPA_X, MAPA_Z


class CarroAgente(ap.Agent):

    def setup(self):
        # Posicion dentro de la ciudad
        self.x = 0.0
        self.z = 0.0

        # Caracteristicas del vehiculo
        self.velocidad = 0.0
        self.velocidad_maxima = 0.8
        self.distancia_sensor = 45.0
        self.distancia_segura = 30.0

        self.vehiculo_delante = None
        self.distancia_delante = float("inf")
        self.interseccion_cercana = None
        self.distancia_interseccion = float("inf")
        self.en_interseccion = False
        self.tiempo_espera = 0.0
        self.intersecciones_atendidas = set()
        
        # Direccion de circulacion
        self.direccion = "+Z"

        # Orientación continua del vehículo (grados)
        self.angulo = 270.0

        # Modelo de bicicleta
        self.longitud_entre_ejes = 3.0
        self.radio_giro_bicicleta = 10.0
        self.angulo_direccion = 0.0

        # Control del giro programado
        self.girando_bicicleta = False
        self.giro_completado = False
        self.angulo_girado = 0.0

        self.direccion_salida = None
        self.angulo_objetivo = None
        self.sentido_giro = 1
        self.interseccion_decidida = None

        # Estado del vehiculo
        self.estado = "AVANZANDO"
        self.movimiento = None
        self.movimiento_elegido = False

    def percibir(self):
        self.vehiculo_delante = None
        self.distancia_delante = float("inf")

        for otro in self.model.carros:
            if otro is self:
                continue

            # Comprobar si están en la misma trayectoria.
            if self.direccion in ("+Z", "-Z"):
                if abs(self.x - otro.x) > 2.5:
                    continue
                if self.direccion == "+Z":
                    distancia = otro.z - self.z
                else:
                    distancia = self.z - otro.z
            else:
                if abs(self.z - otro.z) > 2.5:
                    continue
                if self.direccion == "+X":
                    distancia = otro.x - self.x
                else:
                    distancia = self.x - otro.x

            # Buscar el vehículo más cercano que esté delante.
            if 0 < distancia < self.distancia_delante:
                self.distancia_delante = distancia
                self.vehiculo_delante = otro

    def detectar_interseccion(self):
        self.interseccion_cercana = None
        self.distancia_interseccion = float("inf")
        self.en_interseccion = False

        for ix, iz in self.model.intersecciones:

            # Comprobar si la intersección está en la misma calle.
            if self.direccion in ("+Z", "-Z"):
                if abs(self.x - ix) > 10:
                    continue

                distancia = (
                    iz - self.z if self.direccion == "+Z"
                    else self.z - iz
                )

            else:
                if abs(self.z - iz) > 10:
                    continue

                distancia = (
                    ix - self.x if self.direccion == "+X"
                    else self.x - ix
                )

            # Solo considerar intersecciones que estén adelante.
            if distancia >= 0 and distancia < self.distancia_interseccion:
                self.distancia_interseccion = distancia
                self.interseccion_cercana = (ix, iz)

        # La intersección ocupa 20 unidades por cada lado.
        self.en_interseccion = self.distancia_interseccion <= 10

    def sentido_permitido(self, direccion, ix, iz):
        # Calles verticales: el sentido depende de X.
        if direccion in ("+Z", "-Z"):
            indice = self.model.centros_x.index(ix)

            sentido = "+Z" if indice % 2 == 0 else "-Z"

        # Calles horizontales: el sentido depende de Z.
        else:
            indice = self.model.centros_z.index(iz)

            sentido = "-X" if indice % 2 == 0 else "+X"

        return direccion == sentido

    def obtener_movimientos_validos(self, interseccion):
        ix, iz = interseccion

        direcciones = ["+Z", "+X", "-Z", "-X"]
        indice = direcciones.index(self.direccion)

        candidatos = {
            "RECTO": self.direccion,
            "DERECHA": direcciones[(indice + 1) % 4],
            "IZQUIERDA": direcciones[(indice - 1) % 4]
        }

        movimientos_validos = []

        for movimiento, direccion_salida in candidatos.items():

            # Evitar salir de los límites de las calles.
            if direccion_salida == "+Z" and iz >= max(self.model.centros_z):
                continue

            if direccion_salida == "-Z" and iz <= min(self.model.centros_z):
                continue

            if direccion_salida == "+X" and ix >= max(self.model.centros_x):
                continue

            if direccion_salida == "-X" and ix <= min(self.model.centros_x):
                continue

            # Comprobar el sentido de circulación de la calle de salida.
            if not self.sentido_permitido(direccion_salida, ix, iz):
                continue

            movimientos_validos.append(movimiento)

        return movimientos_validos

    def elegir_movimiento(self):
        if self.interseccion_cercana is None:
            return False

        movimientos = self.obtener_movimientos_validos(
            self.interseccion_cercana
        )

        if not movimientos:
            self.movimiento = None
            self.movimiento_elegido = False
            return False

        self.movimiento = random.choice(movimientos)
        self.movimiento_elegido = True

        return True

    def iniciar_giro(self):
        direcciones = ["+Z", "+X", "-Z", "-X"]

        candidatos = {
            "RECTO": self.direccion,
            "DERECHA": direcciones[(direcciones.index(self.direccion) + 1) % 4],
            "IZQUIERDA": direcciones[(direcciones.index(self.direccion) - 1) % 4]
        }

        self.direccion_salida = candidatos[self.movimiento]

        orientaciones = {
            "+X": 0.0,
            "-Z": 90.0,
            "-X": 180.0,
            "+Z": 270.0
        }

        angulo_final = orientaciones[self.direccion_salida]

        diferencia = (angulo_final - self.angulo + 180) % 360 - 180

        # Determinar hacia qué lado debe girar.
        self.sentido_giro = 1 if diferencia > 0 else -1

        self.angulo_objetivo = angulo_final
        self.angulo_girado = 0.0

        # Calcular el ángulo de dirección usando el radio de giro.
        delta = math.atan(
            self.longitud_entre_ejes / self.radio_giro_bicicleta
        )

        self.angulo_direccion = math.degrees(delta) * self.sentido_giro

        self.girando_bicicleta = True
        self.giro_completado = False

    def decidir(self):
        # Si está esperando, mantener el vehículo detenido.
        if self.tiempo_espera > 0:
            self.tiempo_espera -= self.model.dt_simulacion
            self.velocidad = 0.0
            self.estado = "ESPERANDO"
            return

        if self.girando_bicicleta:
            self.velocidad = self.velocidad_maxima
            self.estado = "GIRANDO"
            return

        # Detectar si estamos frente a una nueva intersección.
        if (
            self.interseccion_cercana is not None
            and self.interseccion_cercana != self.interseccion_decidida
        ):
            self.interseccion_decidida = self.interseccion_cercana
            self.movimiento = None
            self.movimiento_elegido = False
            self.giro_completado = False

        if (
            self.interseccion_cercana is not None
            and self.distancia_interseccion <= 25
            and not self.movimiento_elegido
        ):
            if not self.elegir_movimiento():
                self.velocidad = 0.0
                self.estado = "DETENIDO"
                return

        # Comprobar si debe detenerse antes de una intersección.
        if (
            self.interseccion_cercana is not None
            and self.distancia_interseccion <= 25
            and self.interseccion_cercana not in self.intersecciones_atendidas
        ):
            self.velocidad = 0.0
            self.estado = "ESPERANDO"

            self.tiempo_espera = 3.0
            
            # Marcar esta intersección como atendida.
            self.intersecciones_atendidas.add(
                self.interseccion_cercana
            )

            return

        # No continuar si no existen movimientos válidos.
        if self.movimiento_elegido and self.movimiento is None:
            self.velocidad = 0.0
            self.estado = "DETENIDO"
            return

        # Iniciar el giro al llegar a la intersección.
        if (
            self.movimiento_elegido
            and self.movimiento in ("DERECHA", "IZQUIERDA")
            and self.interseccion_cercana in self.intersecciones_atendidas
            and self.distancia_interseccion <= 10
            and not self.giro_completado
        ):
            self.iniciar_giro()
            self.velocidad = self.velocidad_maxima
            self.estado = "GIRANDO"
            return

        # Comportamiento normal: mantener distancia con otros vehículos.
        if self.distancia_delante <= self.distancia_segura:
            self.velocidad = 0.0
            self.estado = "DETENIDO"

        elif self.distancia_delante < self.distancia_sensor:
            proporcion = (
                (self.distancia_delante - self.distancia_segura)
                / (self.distancia_sensor - self.distancia_segura)
            )

            self.velocidad = self.velocidad_maxima * proporcion
            self.estado = "REDUCIENDO"

        else:
            self.velocidad = self.velocidad_maxima
            self.estado = "AVANZANDO"

    def step(self):
        if self.girando_bicicleta:
            delta = math.radians(self.angulo_direccion)

            # Curvatura con el sentido del giro.
            curvatura = math.tan(delta) / self.longitud_entre_ejes

            # Incremento angular de este paso.
            incremento = self.velocidad * abs(curvatura)

            # Evitar sobrepasar los 90 grados.
            restante = math.radians(90) - self.angulo_girado
            incremento = min(incremento, restante)

            # Aplicar el sentido correcto.
            incremento_firmado = incremento * self.sentido_giro
            curvatura_firmada = abs(curvatura) * self.sentido_giro

            theta_inicial = math.radians(self.angulo)
            theta_final = theta_inicial + incremento_firmado

            nueva_x = self.x + (
                math.sin(theta_final) - math.sin(theta_inicial)
            ) / curvatura_firmada

            nueva_z = self.z + (
                math.cos(theta_final) - math.cos(theta_inicial)
            ) / curvatura_firmada

            if not (0 <= nueva_x <= MAPA_X and 0 <= nueva_z <= MAPA_Z):
                self.bloqueado = True
                self.girando_bicicleta = False
                self.velocidad = 0.0
                self.estado = "DETENIDO"
                return

            self.x = nueva_x
            self.z = nueva_z

            # Actualizar orientación.
            self.angulo = math.degrees(theta_final) % 360
            self.angulo_girado += incremento

            # Terminar el giro.
            if self.angulo_girado >= math.radians(90) - 0.0001:
                self.angulo = self.angulo_objetivo
                self.direccion = self.direccion_salida

                self.angulo_direccion = 0.0
                self.girando_bicicleta = False
                self.giro_completado = True

                self.estado = "AVANZANDO"

            return

        nueva_x = self.x
        nueva_z = self.z

        if self.direccion == "+Z":
            nueva_z += self.velocidad
        elif self.direccion == "-Z":
            nueva_z -= self.velocidad
        elif self.direccion == "+X":
            nueva_x += self.velocidad
        elif self.direccion == "-X":
            nueva_x -= self.velocidad

        if not (0 <= nueva_x <= MAPA_X and 0 <= nueva_z <= MAPA_Z):
            self.bloqueado = True
            self.velocidad = 0.0
            self.estado = "DETENIDO"
            return

        self.x = nueva_x
        self.z = nueva_z

class ModeloTrafico(ap.Model):

    def setup(self):
        self.dt_simulacion = 1 / 30

        self.centros_x = [x + ANCHO_CALLE / 2 for x in [20, 145, 270, 380]]
        self.centros_z = [z + ANCHO_CALLE / 2 for z in [20, 145, 270, 380]]

        self.intersecciones = [
            (x, z)
            for x in self.centros_x
            for z in self.centros_z
        ]
        
        self.carros = ap.AgentList(self, 6, CarroAgente)

        # Posiciones iniciales y sentidos
        configuraciones = [
            (30, 60, "+Z"),
            (30, 100, "+Z"),
            (30, 140, "+Z"),

            (155, 300, "-Z"),
            (155, 260, "-Z"),
            (155, 220, "-Z")
        ]

        self.carros[2].velocidad_maxima = 0.5
        self.carros[5].velocidad_maxima = 0.5

        orientaciones = {
            "+X": 0.0,
            "-Z": 90.0,
            "-X": 180.0,
            "+Z": 270.0
        }

        for carro, configuracion in zip(self.carros, configuraciones):
            carro.x = configuracion[0]
            carro.z = configuracion[1]
            carro.direccion = configuracion[2]
            carro.angulo = orientaciones[carro.direccion]

    def obtener_sentido_calle(self, x, z):
        if x in [30, 155, 280, 390]:
            indice = [30, 155, 280, 390].index(x)
            return "+Z" if indice % 2 == 0 else "-Z"
        if z in [30, 155, 280, 390]:
            indice = [30, 155, 280, 390].index(z)
            return "+X" if indice % 2 == 0 else "-X"
        return None

    def step(self):
        for carro in self.carros:
            carro.percibir()
            carro.detectar_interseccion()
        for carro in self.carros:
            carro.decidir()
        for carro in self.carros:
            carro.step()

if __name__ == "__main__":
    modelo = ModeloTrafico()
    modelo.run(steps=300)

    for carro in modelo.carros:
        print(
            f"Carro {carro.id}: "
            f"Posicion=({carro.x:.2f}, {carro.z:.2f}), "
            f"Direccion={carro.direccion}, "
            f"Interseccion={carro.interseccion_cercana}, "
            f"Distancia={carro.distancia_interseccion:.2f}, "
            f"En interseccion={carro.en_interseccion}"
        )
