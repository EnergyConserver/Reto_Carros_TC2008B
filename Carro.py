import math
from OpenGL.GL import glPushMatrix, glPopMatrix, glTranslatef, glRotatef, glScalef

class Carro:
    def __init__(self, dim, vel, Scale, inicio=None):
        self.DimBoard = dim
        self.vel = float(vel)
        self.Scale = Scale

        self.Position = list(inicio or (155.0, 3.1, 80.0))
        self.Body_Ry = 0.0
        self.component = []

        # Comunicación con AgentPy
        self.buzon = []
        self.instruccion = "DETENERSE"
        self.estado = "DETENIDO"

        # Parámetros del movimiento
        self.radio_giro = 10.0
        self.angulo_giro_restante = 0.0
        self.direccion_giro = 1.0

    def getComponents(self, componentes):
        self.component = componentes

    # COMUNICACION

    def setInstruction(self, instruccion):
        self.ejecutar_comando(instruccion)

    def recibir_mensaje(self, mensaje):
        self.buzon.append(mensaje)

    def procesar_buzon(self):
        if not self.buzon:
            return

        mensaje = self.buzon.pop(0)

        if isinstance(mensaje, dict):
            instruccion = mensaje.get("contenido", "")
        elif isinstance(mensaje, str):
            instruccion = mensaje
        else:
            return

        self.ejecutar_comando(instruccion)

    # INSTRUCCIONES

    def ejecutar_comando(self, instruccion):
        instruccion = instruccion.strip().upper()

        instrucciones_validas = (
            "AVANZAR",
            "RETROCEDER",
            "GIRAR_IZQUIERDA",
            "GIRAR_DERECHA",
            "DETENERSE"
        )

        if instruccion not in instrucciones_validas:
            return
        if instruccion == self.instruccion:
            return

        self.instruccion = instruccion

        if instruccion == "AVANZAR":
            self.estado = "AVANZANDO"

        elif instruccion == "RETROCEDER":
            self.estado = "RETROCEDIENDO"

        elif instruccion == "DETENERSE":
            self.estado = "DETENIDO"

        elif instruccion == "GIRAR_IZQUIERDA":
            self.angulo_giro_restante = 90.0
            self.direccion_giro = 1.0
            self.estado = "GIRANDO"

        elif instruccion == "GIRAR_DERECHA":
            self.angulo_giro_restante = 90.0
            self.direccion_giro = -1.0
            self.estado = "GIRANDO"

    # MOVIMIENTO

    def update(self, dt):
        dt = max(float(dt), 0.0)

        self.procesar_buzon()
        theta = math.radians(self.Body_Ry)

        if self.estado == "DETENIDO":
            return

        if self.estado == "AVANZANDO":
            distancia = self.vel * dt

            self.Position[0] += distancia * math.cos(theta)
            self.Position[2] -= distancia * math.sin(theta)

        elif self.estado == "RETROCEDIENDO":
            distancia = self.vel * dt

            self.Position[0] -= distancia * math.cos(theta)
            self.Position[2] += distancia * math.sin(theta)

        elif self.estado == "GIRANDO":

            omega = self.vel / self.radio_giro
            omega *= self.direccion_giro
            incremento = abs(math.degrees(omega * dt))

            # Evitar sobrepasar los 90 grados.
            incremento = min(incremento, self.angulo_giro_restante)

            # Ángulo inicial y final del movimiento.
            theta_inicial = math.radians(self.Body_Ry)

            theta_final = theta_inicial + math.radians(incremento * self.direccion_giro)

            # Integración exacta del arco circular.
            desplazamiento_x = (self.vel / omega) * (math.sin(theta_final) - math.sin(theta_inicial))
            desplazamiento_z = (self.vel / omega) * (math.cos(theta_final) - math.cos(theta_inicial))

            self.Position[0] += desplazamiento_x
            self.Position[2] += desplazamiento_z

            # Actualizar orientación.
            self.Body_Ry = math.degrees(theta_final) % 360.0

            # Descontar el ángulo recorrido.
            self.angulo_giro_restante -= incremento

            # Al terminar los 90 grados, continúa avanzando.
            if self.angulo_giro_restante <= 0.001:
                self.angulo_giro_restante = 0.0
                self.instruccion = "AVANZAR"
                self.estado = "AVANZANDO"

    # RENDERIZADO

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
