import agentpy as ap
import math
from Configuracion import ANCHO_CALLE


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
        self.giro_programado = False
        self.girando_bicicleta = False
        self.giro_completado = False
        self.angulo_girado = 0.0

        # Estado del vehiculo
        self.estado = "AVANZANDO"

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

        # Iniciar el giro 10 unidades antes del centro
        # de la primera intersección.
        if (
            self.giro_programado
            and not self.giro_completado
            and self.direccion == "+Z"
            and abs(self.x - 30) < 1
            and self.z >= 145
        ):
            self.girando_bicicleta = True
            self.angulo_girado = 0.0

            # Ángulo de dirección calculado con el radio de giro.
            self.angulo_direccion = math.degrees(
                math.atan(
                    self.longitud_entre_ejes / self.radio_giro_bicicleta
                )
            )

            self.velocidad = self.velocidad_maxima
            self.estado = "GIRANDO"
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
            theta_inicial = math.radians(self.angulo)

            # Curvatura del movimiento.
            curvatura = math.tan(delta) / self.longitud_entre_ejes

            # Incremento angular de este paso.
            incremento = self.velocidad * curvatura

            # No sobrepasar los 90 grados.
            restante = math.radians(90) - self.angulo_girado
            incremento = min(incremento, restante)

            theta_final = theta_inicial + incremento

            # Integración del movimiento sobre el arco circular.
            self.x += (math.sin(theta_final) - math.sin(theta_inicial)) / curvatura
            self.z += (math.cos(theta_final) - math.cos(theta_inicial)) / curvatura

            # Actualizar orientación.
            self.angulo = math.degrees(theta_final) % 360

            self.angulo_girado += incremento

            # Terminar el giro.
            if self.angulo_girado >= math.radians(90) - 0.0001:
                self.angulo = 0.0
                self.direccion = "+X"

                self.angulo_direccion = 0.0
                self.girando_bicicleta = False
                self.giro_completado = True

                self.estado = "AVANZANDO"
            return
        
        if self.direccion == "+Z":
            self.z += self.velocidad
        elif self.direccion == "-Z":
            self.z -= self.velocidad
        elif self.direccion == "+X":
            self.x += self.velocidad    
        elif self.direccion == "-X":
            self.x -= self.velocidad


class ModeloTrafico(ap.Model):

    def setup(self):
        self.dt_simulacion = 1 / 30

        centros_x = [x + ANCHO_CALLE / 2 for x in [20, 145, 270, 380]]
        centros_z = [z + ANCHO_CALLE / 2 for z in [20, 145, 270, 380]]

        self.intersecciones = [
            (x, z)
            for x in centros_x
            for z in centros_z
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

        self.carros[0].giro_programado = True
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
    modelo.run(steps=40)

    for carro in modelo.carros:
        print(
            f"Carro {carro.id}: "
            f"Posicion=({carro.x:.2f}, {carro.z:.2f}), "
            f"Direccion={carro.direccion}, "
            f"Interseccion={carro.interseccion_cercana}, "
            f"Distancia={carro.distancia_interseccion:.2f}, "
            f"En interseccion={carro.en_interseccion}"
        )
