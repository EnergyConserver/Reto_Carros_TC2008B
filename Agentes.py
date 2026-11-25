import agentpy as ap

class CarroAgente(ap.Agent):

    def setup(self):
        # Posicion dentro de la ciudad
        self.x = 0.0
        self.z = 0.0

        # Caracteristicas del vehiculo
        self.velocidad = 0.0
        self.velocidad_maxima = 0.8
        self.distancia_sensor = 35.0
        self.distancia_segura = 25.0

        self.vehiculo_delante = None
        self.distancia_delante = float("inf")

        # Direccion de circulacion
        self.direccion = "+Z"

        # Estado del vehiculo
        self.estado = "AVANZANDO"

    def percibir(self):
        self.vehiculo_delante = None
        self.distancia_delante = float("inf")

        for otro in self.model.carros:
            if otro is self:
                continue

            if self.direccion != otro.direccion:
                continue

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

            if 0 < distancia < self.distancia_delante:
                self.distancia_delante = distancia
                self.vehiculo_delante = otro

    def decidir(self):
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

        for carro, configuracion in zip(self.carros, configuraciones):
            carro.x = configuracion[0]
            carro.z = configuracion[1]
            carro.direccion = configuracion[2]

    def step(self):
        for carro in self.carros:
            carro.percibir()
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
            f"Velocidad={carro.velocidad:.2f}, "
            f"Estado={carro.estado}, "
            f"Distancia={carro.distancia_delante:.2f}"
        )
