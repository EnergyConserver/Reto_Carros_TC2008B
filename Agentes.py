import agentpy as ap
import random
import math
from Configuracion import ANCHO_CALLE, MAPA_X, MAPA_Z, CONFIGURACIONES_CARROS


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
        self.distancia_parada = 25.0

        self.vehiculo_delante = None
        self.distancia_delante = float("inf")
        self.interseccion_cercana = None
        self.distancia_interseccion = float("inf")
        self.en_interseccion = False
        self.interseccion_reservada = None
        self.entro_interseccion_reservada = False
        self.direccion_reservada = None

        self.estado_semaforo = "ROJO" #Cambiar después a que el semaforo inteligente

        self.vehiculos_interseccion = []
        self.vehiculos_conflictivos = []
        self.salida_libre = True
        self.puede_entrar_interseccion = True
        self.interseccion_solicitada = None
        
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

        self.buzon = []

    def enviar_mensaje(self, receptor, performativa, contenido):
        mensaje = {
            "remitente": self,
            "performativa": performativa,
            "contenido": contenido
        }
    
        receptor.buzon.append(mensaje)

    def procesar_buzon(self):
        for mensaje in self.buzon:
            performativa = mensaje["performativa"]
            contenido = mensaje["contenido"]

            print(
                f"Carro {self.id}: "
                f"mensaje recibido: {performativa} - {contenido}"
            )

    def percibir(self):
        self.vehiculo_delante = None
        self.distancia_delante = float("inf")

        self.vehiculos_interseccion = []
        self.vehiculos_conflictivos = []
        self.salida_libre = True
        self.puede_entrar_interseccion = True

        for otro in self.model.carros:
            if otro is self:
                continue

            if self.direccion in ("+Z", "-Z"):
                if abs(self.x - otro.x) <= 2.5:
                    if self.direccion == "+Z":
                        distancia = otro.z - self.z
                    else:
                        distancia = self.z - otro.z

                    if 0 < distancia < self.distancia_delante:
                        self.distancia_delante = distancia
                        self.vehiculo_delante = otro
            else:
                if abs(self.z - otro.z) <= 2.5:
                    if self.direccion == "+X":
                        distancia = otro.x - self.x
                    else:
                        distancia = self.x - otro.x

                    if 0 < distancia < self.distancia_delante:
                        self.distancia_delante = distancia
                        self.vehiculo_delante = otro

    
            if self.interseccion_cercana is not None:
                ix, iz = self.interseccion_cercana

                if (abs(otro.x - ix) <= 10 and abs(otro.z - iz) <= 10):
                    self.vehiculos_interseccion.append(otro)

            if (
                self.interseccion_cercana is not None
                and otro.interseccion_cercana == self.interseccion_cercana
                and otro.distancia_interseccion <= 25
            ):
                self.vehiculos_conflictivos.append(otro)


        if self.vehiculos_interseccion:
            self.puede_entrar_interseccion = False

        if (self.movimiento_elegido and self.interseccion_cercana is not None):
            ix, iz = self.interseccion_cercana

            direcciones = ["+Z", "+X", "-Z", "-X"]
            indice = direcciones.index(self.direccion)

            candidatos = {
                "RECTO": self.direccion,
                "DERECHA": direcciones[(indice + 1) % 4],
                "IZQUIERDA": direcciones[(indice - 1) % 4]
            }

            direccion_salida = candidatos[self.movimiento]

            for otro in self.model.carros:
                if otro is self:
                    continue

                if direccion_salida == "+X":
                    alineado = abs(otro.z - iz) <= 2.5
                    distancia = otro.x - ix

                elif direccion_salida == "-X":
                    alineado = abs(otro.z - iz) <= 2.5
                    distancia = ix - otro.x

                elif direccion_salida == "+Z":
                    alineado = abs(otro.x - ix) <= 2.5
                    distancia = otro.z - iz

                else:
                    alineado = abs(otro.x - ix) <= 2.5
                    distancia = iz - otro.z

                if (
                    alineado
                    and 0 <= distancia <= 12
                ):
                    self.salida_libre = False
                    break

    def solicitar_paso(self):
        if self.interseccion_cercana is None:
            return

        if self.distancia_interseccion > self.distancia_parada:
            return

        if not self.movimiento_elegido:
            return

        if self.interseccion_solicitada == self.interseccion_cercana:
            return

        # Buscar el agente que representa la intersección.
        for interseccion in self.model.agentes_interseccion:
            if (interseccion.x, interseccion.z) == self.interseccion_cercana:
                flujo = ("VERTICAL" if self.direccion in ("+Z", "-Z") else "HORIZONTAL")
                
                contenido = {
                    "direccion": self.direccion,
                    "movimiento": self.movimiento,
                    "flujo": flujo
                }

                self.enviar_mensaje(interseccion, "REQUEST", contenido)

                # Registrar que ya se envió la solicitud.
                self.interseccion_solicitada = self.interseccion_cercana
                break

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
        if self.girando_bicicleta:
            self.velocidad = self.velocidad_maxima
            self.estado = "GIRANDO"
            return

        if self.interseccion_cercana is not None:
            for interseccion in self.model.agentes_interseccion:
                if (interseccion.x, interseccion.z) == self.interseccion_cercana:
                    if self.direccion in ("+Z", "-Z"):
                        self.estado_semaforo = interseccion.estado_vertical
                    else:
                        self.estado_semaforo = interseccion.estado_horizontal
                    break 

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

        # Solicitar permiso para entrar a la intersección.
        if (
            self.interseccion_cercana is not None
            and self.distancia_interseccion <= self.distancia_parada
        ):
            propietario = self.model.reservas_interseccion.get(
                self.interseccion_cercana
            )

            if propietario is None:
                if self.estado_semaforo == "VERDE":
                    self.model.reservas_interseccion[self.interseccion_cercana] = self
                    self.interseccion_reservada = self.interseccion_cercana
                    self.direccion_reservada = self.direccion

            elif propietario is not self:
                self.velocidad = 0.0
                self.estado = "ESPERANDO"
                return

        # Comprobar el estado del semáforo.
        if (
            self.interseccion_cercana is not None
            and self.distancia_interseccion <= self.distancia_parada
            and not self.en_interseccion
            and self.estado_semaforo == "ROJO"
        ):
            self.velocidad = 0.0
            self.estado = "ESPERANDO"
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

class InterseccionAgente(ap.Agent):
    def setup(self):
        # Ubicación de la intersección
        self.x = 0.0
        self.z = 0.0

        self.estado_vertical = "ROJO"
        self.estado_horizontal = "ROJO"

        # Comunicación
        self.buzon = []

        # Solicitudes recibidas
        self.solicitudes = []

        # Coordinación (se implementará después)
        self.flujo_vertical = {
            "vehiculos": [],
            "tiempo_espera": 0
        }

        self.flujo_horizontal = {
            "vehiculos": [],
            "tiempo_espera": 0
        }

    def enviar_mensaje(self, receptor, performativa, contenido):
        mensaje = {
            "remitente": self,
            "performativa": performativa,
            "contenido": contenido
        }

        receptor.buzon.append(mensaje)
    
    def procesar_buzon(self):
        for mensaje in self.buzon:
            performativa = mensaje["performativa"]
            contenido = mensaje["contenido"]
            remitente = mensaje["remitente"]

            if performativa == "REQUEST":
                self.solicitudes.append({
                    "carro": remitente,
                    "contenido": contenido,
                    "estado": "PENDIENTE"
                })

                print(
                    f"Intersección ({self.x}, {self.z}): "
                    f"solicitud recibida de {remitente.id} "
                    f"para flujo {contenido['flujo']}"
                )

        self.buzon.clear()

    def actualizar_semaforos(self):
        propietario = self.model.reservas_interseccion.get(
            (self.x, self.z)
        )

        # Mantener el verde para quien ya tiene la reserva.
        if propietario is not None:

            if propietario.direccion_reservada in ("+Z", "-Z"):
                self.estado_vertical = "VERDE"
                self.estado_horizontal = "ROJO"
            else:
                self.estado_vertical = "ROJO"
                self.estado_horizontal = "VERDE"

            return

        demanda_vertical = False
        demanda_horizontal = False

        for carro in self.model.carros:

            if carro.interseccion_cercana != (self.x, self.z):
                continue

            if not (0 <= carro.distancia_interseccion <= 45):
                continue

            if carro.direccion in ("+Z", "-Z"):
                demanda_vertical = True

            elif carro.direccion in ("+X", "-X"):
                demanda_horizontal = True

        if demanda_vertical:
            self.estado_vertical = "VERDE"
            self.estado_horizontal = "ROJO"

        elif demanda_horizontal:
            self.estado_vertical = "ROJO"
            self.estado_horizontal = "VERDE"

        else:
            self.estado_vertical = "ROJO"
            self.estado_horizontal = "ROJO"

    def actualizar_demanda(self):
        estados_espera = ("DETENIDO", "REDUCIENDO", "ESPERANDO")

        vehiculos_fila = []

        # Buscar los vehículos que encabezan una fila.
        for carro in self.model.carros:
            if (
                carro.interseccion_cercana == (self.x, self.z)
                and carro.distancia_interseccion <= carro.distancia_parada
                and carro.estado in estados_espera
            ):
                vehiculos_fila.append(carro)

        cambio = True

        while cambio:
            cambio = False

            for carro in self.model.carros:
                if carro in vehiculos_fila:
                    continue

                if (
                    carro.interseccion_cercana == (self.x, self.z)
                    and carro.vehiculo_delante in vehiculos_fila
                    and carro.estado in estados_espera
                ):
                    vehiculos_fila.append(carro)
                    cambio = True

        # Separar los vehículos por flujo.
        self.flujo_vertical["vehiculos"] = [
            carro for carro in vehiculos_fila
            if carro.direccion in ("+Z", "-Z")
        ]

        self.flujo_horizontal["vehiculos"] = [
            carro for carro in vehiculos_fila
            if carro.direccion in ("+X", "-X")
        ]

        # Actualizar tiempo de espera de cada flujo.
        if self.flujo_vertical["vehiculos"]:
            self.flujo_vertical["tiempo_espera"] += self.model.dt_simulacion
        else:
            self.flujo_vertical["tiempo_espera"] = 0

        if self.flujo_horizontal["vehiculos"]:
            self.flujo_horizontal["tiempo_espera"] += self.model.dt_simulacion
        else:
            self.flujo_horizontal["tiempo_espera"] = 0

        vertical = len(self.flujo_vertical["vehiculos"])
        horizontal = len(self.flujo_horizontal["vehiculos"])

        if vertical > 0 or horizontal > 0:
            print(
                f"Intersección ({self.x}, {self.z}) | "
                f"Vertical: {vertical} | "
                f"Horizontal: {horizontal}"
            )

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

        self.agentes_interseccion = ap.AgentList(
            self,
            len(self.intersecciones),
            InterseccionAgente
        )

        for agente, (x, z) in zip(
            self.agentes_interseccion,
            self.intersecciones
        ):
            agente.x = x
            agente.z = z

        for interseccion in self.agentes_interseccion:
            print(
                f"Intersección {interseccion.id}: "
                f"({interseccion.x}, {interseccion.z})"
            )
        
        self.carros = ap.AgentList(self, len(CONFIGURACIONES_CARROS), CarroAgente)

        direcciones = {
            0.0: "+X",
            90.0: "-Z",
            180.0: "-X",
            270.0: "+Z"
        }

        for carro, (x, z, orientacion, color) in zip(
            self.carros,
            CONFIGURACIONES_CARROS
        ):
            carro.x = x
            carro.z = z
            carro.direccion = direcciones[orientacion]
            carro.angulo = orientacion

        self.reservas_interseccion = {}

    def obtener_sentido_calle(self, x, z):
        if x in [30, 155, 280, 390]:
            indice = [30, 155, 280, 390].index(x)
            return "+Z" if indice % 2 == 0 else "-Z"
        if z in [30, 155, 280, 390]:
            indice = [30, 155, 280, 390].index(z)
            return "+X" if indice % 2 == 0 else "-X"
        return None

    def step(self):
        # 1. Detectar intersecciones y percibir el entorno.
        for carro in self.carros:
            carro.detectar_interseccion()
            carro.percibir()

        for interseccion in self.agentes_interseccion:
            interseccion.actualizar_semaforos()

        # 2. Decidir el movimiento de cada carro.
        for carro in self.carros:
            carro.decidir()

        for interseccion in self.agentes_interseccion:
            interseccion.actualizar_demanda()

        # 3. Enviar solicitudes.
        for carro in self.carros:
            carro.solicitar_paso()

        # 4. Procesar mensajes de las intersecciones.
        for interseccion in self.agentes_interseccion:
            interseccion.procesar_buzon()

        # 5. Procesar mensajes de los carros.
        for carro in self.carros:
            carro.procesar_buzon()

        # 6. Actualizar movimiento de los carros.
        for carro in self.carros:
            carro.step()

            if carro.interseccion_reservada is not None:
                ix, iz = carro.interseccion_reservada

                dentro_interseccion = (
                    abs(carro.x - ix) <= 10
                    and abs(carro.z - iz) <= 10
                )

                # Registrar que el vehículo ya entró al cruce.
                if dentro_interseccion:
                    carro.entro_interseccion_reservada = True

                # Liberar solamente después de haber entrado y salido.
                elif carro.entro_interseccion_reservada:
                    if self.reservas_interseccion.get(
                        carro.interseccion_reservada
                    ) is carro:
                        del self.reservas_interseccion[
                            carro.interseccion_reservada
                        ]

                    carro.interseccion_reservada = None
                    carro.entro_interseccion_reservada = False
                    carro.interseccion_solicitada = None
                    carro.direccion_reservada = None

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
