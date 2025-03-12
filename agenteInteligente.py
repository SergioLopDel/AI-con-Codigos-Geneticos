import pygame
import random
import time
import math

# Definir el tamaño inicial del mapa
tamano_inicial = 10
tamano_celda = 50

# Inicializar pygame
pygame.init()

# Colores
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)

# Cargar imágenes
img_agente = pygame.image.load("assets/pinguino.png")
img_wumpus = pygame.image.load("assets/foca.png")
img_pozo = pygame.image.load("assets/iglu.png")
img_premio = pygame.image.load("assets/pescados.png")
img_pasto = pygame.image.load("assets/grass2.jpg")
img_arena = pygame.image.load("assets/road.jpg")
img_agua = pygame.image.load("assets/agua.png")

# Redimensionar imágenes
img_agente = pygame.transform.scale(img_agente, (tamano_celda, tamano_celda))
img_wumpus = pygame.transform.scale(img_wumpus, (tamano_celda, tamano_celda))
img_pozo = pygame.transform.scale(img_pozo, (tamano_celda, tamano_celda))
img_premio = pygame.transform.scale(img_premio, (tamano_celda, tamano_celda))
img_pasto = pygame.transform.scale(img_pasto, (tamano_celda, tamano_celda))
img_arena = pygame.transform.scale(img_arena, (tamano_celda, tamano_celda))
img_agua = pygame.transform.scale(img_agua, (tamano_celda, tamano_celda))

# Clase del tablero
class Tablero:
    def __init__(self, tamano):
        self.tamano = tamano
        self.mapa = [['' for _ in range(tamano)] for _ in range(tamano)]
        self.costos = [[1 for _ in range(tamano)] for _ in range(tamano)]  # Costos iniciales
        self.peligros = []
        self.premio = []
        self.monstruo = []
        self.revelado = [[False for _ in range(tamano)] for _ in range(tamano)]  # Para mostrar costos
        self.crearMundo()

    def crearMundo(self):
        # Asegurarse de que la posición (0, 0) esté libre
        while True:
            # Se coloca el wumpus en una celda aleatoria
            self.monstruo = (random.randint(0, self.tamano - 1), random.randint(0, self.tamano - 1))
            self.mapa[self.monstruo[0]][self.monstruo[1]] = "W"

            # Se colocan los obstáculos (número de pozos)
            self.peligros = []
            for _ in range(self.tamano):  # Más pozos en niveles más difíciles
                pozo = (random.randint(0, self.tamano - 1), random.randint(0, self.tamano - 1))
                while pozo == self.monstruo or pozo in self.peligros:  # Evitar que se repitan las posiciones
                    pozo = (random.randint(0, self.tamano - 1), (random.randint(0, self.tamano - 1)))
                self.peligros.append(pozo)
                self.mapa[pozo[0]][pozo[1]] = 'P'

            # Se coloca el premio en el mapa
            self.premio = (random.randint(0, self.tamano - 1), random.randint(0, self.tamano - 1))
            while self.premio == self.monstruo or self.premio in self.peligros:
                self.premio = (random.randint(0, self.tamano - 1), random.randint(0, self.tamano - 1))
            self.mapa[self.premio[0]][self.premio[1]] = "F"

            # Asignar costos a las celdas
            for i in range(self.tamano):
                for j in range(self.tamano):
                    if self.mapa[i][j] == '':  # Celda vacía
                        # Asignar costos aleatorios: 1 (normal), 2 (agua), 3 (arena)
                        self.costos[i][j] = random.choices([1, 2, 3], weights=[5, 3, 2], k=1)[0]

            # Verificar que la posición (0, 0) esté libre
            if (0, 0) not in self.peligros and (0, 0) != self.monstruo and (0, 0) != self.premio:
                break
            else:
                # Si no está libre, reiniciar el mundo
                self.mapa = [['' for _ in range(self.tamano)] for _ in range(self.tamano)]
                self.costos = [[1 for _ in range(self.tamano)] for _ in range(self.tamano)]
                self.peligros = []
                self.premio = []
                self.monstruo = []
                self.revelado = [[False for _ in range(self.tamano)] for _ in range(self.tamano)]

    def dibujar(self, agente_pos):
        pantalla = pygame.display.get_surface()
        pantalla.fill(BLANCO)
        for i in range(self.tamano):
            for j in range(self.tamano):
                x, y = j * tamano_celda, i * tamano_celda
                if self.costos[i][j] == 3:
                    pantalla.blit(img_arena, (x, y))
                elif self.costos[i][j] == 2:
                    pantalla.blit(img_agua, (x, y))
                else:
                    pantalla.blit(img_pasto, (x, y))

                if (i, j) in self.peligros:
                    pantalla.blit(img_pozo, (x, y))
                elif (i, j) == self.monstruo:
                    pantalla.blit(img_wumpus, (x, y))
                elif (i, j) == self.premio:
                    pantalla.blit(img_premio, (x, y))
                elif (i, j) == agente_pos:
                    pantalla.blit(img_agente, (x, y))
        pygame.display.flip()

# Clase para representar un nodo en el mundo
class Nodo:
    def __init__(self, posicion, padre=None):
        self.posicion = posicion  # Coordenadas (x, y) en el mapa
        self.padre = padre  # Nodo padre para reconstruir la ruta
        self.g = 0  # Costo desde el inicio hasta este nodo
        self.h = 0  # Heurística (estimación del costo hasta el objetivo)
        self.f = 0  # Costo total (g + h)

    def __eq__(self, otro):
        # Comparar dos nodos por su posición
        return self.posicion == otro.posicion

    def __repr__(self):
        # Representación del nodo para debugging
        return f"{self.posicion} (g={self.g}, h={self.h}, f={self.f})"

# Ruta del archivo para guardar la información de los pingüinos
ARCHIVO_PINGUINOS = "assets/pinguinos.txt"

# Diccionarios de descripciones para cada característica
descripciones = {
    "Plumaje": {
        "0000": "Plumaje negro",
        "0001": "Plumaje blanco",
        "0010": "Plumaje gris",
        "0011": "Plumaje marrón",
        "0100": "Plumaje rubio",
        "0101": "Plumaje rojizo",
        "0110": "Plumaje dorado",
        "0111": "Plumaje plateado",
        "1000": "Plumaje azulado",
        "1001": "Plumaje verde",
        "1010": "Plumaje naranja",
        "1011": "Plumaje rosado",
        "1100": "Plumaje violeta",
        "1101": "Plumaje multicolor",
        "1110": "Plumaje brillante",
        "1111": "Plumaje rayado"
    },
    "Habilidad de Nado": {
        "0000": "Nada torpemente",
        "0001": "Nada lentamente",
        "0010": "Nada con dificultad",
        "0011": "Nada decentemente",
        "0100": "Nada bien",
        "0101": "Nada muy bien",
        "0110": "Nada rápido",
        "0111": "Nada muy rápido",
        "1000": "Nada como un experto",
        "1001": "Nada como un atleta",
        "1010": "Nada como un campeón",
        "1011": "Nada como un rayo",
        "1100": "Nada con gracia",
        "1101": "Nada con elegancia",
        "1110": "Nada perfectamente",
        "1111": "Nada como un dios"
    },
    "Resistencia al Frío": {
        "0000": "Muy sensible",
        "0001": "Sensible",
        "0010": "Poco resistente",
        "0011": "Resistencia media",
        "0100": "Resistente",
        "0101": "Muy resistente",
        "0110": "Extremadamente resistente",
        "0111": "Inmune al frío",
        "1000": "Adaptado al frío",
        "1001": "Prospera en el frío",
        "1010": "Ama el frío",
        "1011": "No siente el frío",
        "1100": "Genera calor propio",
        "1101": "Nunca tiene frío",
        "1110": "Vive en el hielo",
        "1111": "Rey del frío"
    },
    "Habilidad para cruzar arena": {
        "0000": "No camina en arena",
        "0001": "Camina torpemente",
        "0010": "Camina lentamente",
        "0011": "Camina con dificultad",
        "0100": "Camina decentemente",
        "0101": "Camina bien",
        "0110": "Camina muy bien",
        "0111": "Camina rápido",
        "1000": "Camina como un experto",
        "1001": "Camina como un atleta",
        "1010": "Camina como un campeón",
        "1011": "Camina como un rayo",
        "1100": "Camina con gracia",
        "1101": "Camina con elegancia",
        "1110": "Camina perfectamente",
        "1111": "Rey de la arena"
    },
    "Resistencia al agotamiento": {
        "0000": "Muy débil",
        "0001": "Débil",
        "0010": "Normal",
        "0011": "Resistente",
        "0100": "Muy resistente",
        "0101": "Casi inmune",
        "0110": "Inmune",
        "0111": "Energético",
        "1000": "Estratega",
        "1001": "Sabio",
        "1010": "Guerrero",
        "1011": "Explorador",
        "1100": "Místico",
        "1101": "Legendario",
        "1110": "Dios de la energía",
        "1111": "Rey de la energía"
    },
    "Altura": {
        "0000": "Muy bajo",
        "0001": "Bajo",
        "0010": "Intermedio",
        "0011": "Alto",
        "0100": "Muy alto",
        "0101": "Gigante",
        "0110": "Enano",
        "0111": "Mediano",
        "1000": "Estilizado",
        "1001": "Robusto",
        "1010": "Compacto",
        "1011": "Delgado",
        "1100": "Ancho",
        "1101": "Estrecho",
        "1110": "Desproporcionado",
        "1111": "Perfecto"
    }
}

# Clase para representar al pingüino
class Pinguino:
    def __init__(self):
        # Inicializar el plumaje y la altura
        plumaje = f"{random.randint(0, 15):04b}"  # Valor aleatorio entre 0000 y 1111
        altura = f"{random.randint(0, 15):04b}"  # Valor aleatorio entre 0000 y 1111
        
        # Calcular la resistencia al frío basada en el plumaje
        resistencia_al_frio = self.calcular_resistencia_al_frio(plumaje)
        
        # Inicializar todas las características
        self.caracteristicas = {
            "Plumaje": plumaje,
            "Habilidad de Nado": "0000",
            "Resistencia al Frío": resistencia_al_frio,
            "Habilidad para cruzar arena": "0000",
            "Resistencia al agotamiento": "0000",  # Resistencia a la fatiga
            "Altura": altura
        }

    def calcular_resistencia_al_frio(self, plumaje):
        # Calcular la resistencia al frío basada en el plumaje
        valor_plumaje = int(plumaje, 2)
        # A mayor valor de plumaje, mayor resistencia al frío
        resistencia = min(valor_plumaje + random.randint(0, 3), 15)  # Valor entre 0 y 15
        return f"{resistencia:04b}"

    def mejorar_caracteristica(self, caracteristica, incremento=1):
        # Convertir la cadena de bits a un número entero
        valor_actual = int(self.caracteristicas[caracteristica], 2)
        # Incrementar el valor (sin exceder el máximo de 15)
        nuevo_valor = min(valor_actual + incremento, 15)
        # Convertir el nuevo valor a una cadena de 4 bits
        self.caracteristicas[caracteristica] = f"{nuevo_valor:04b}"
        print(f"¡{caracteristica} mejorada a {self.caracteristicas[caracteristica]}!")

    def describir(self):
        descripcion = "Tu pingüino es:\n"
        for caracteristica, valor in self.caracteristicas.items():
            if caracteristica in descripciones:
                descripcion += f"- {caracteristica}: {descripciones[caracteristica][valor]}\n"
        return descripcion

    def __str__(self):
        return " ".join(self.caracteristicas.values())

# Agente Inteligente
class Agente:
    def __init__(self, mundo):
        self.mundo = mundo
        self.posicion = (0, 0)  # Comienza en la esquina superior izquierda
        self.vivo = True
        self.oro_recogido = False
        self.ruta = []  # Para almacenar la ruta completa
        self.costo_total = 0  # Para almacenar el costo total de la ruta
        self.pinguino = Pinguino()  # Crear un pingüino

    def distancia_manhattan(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def a_estrella(self):
        # Inicializar nodo inicial y nodo objetivo
        nodo_inicio = Nodo(self.posicion)
        nodo_objetivo = Nodo(self.mundo.premio)

        # Listas abierta y cerrada
        abierta = []
        cerrada = set()

        # Agregar el nodo inicial a la lista abierta
        abierta.append(nodo_inicio)

        while abierta:
            # Obtener el nodo con el menor costo f
            nodo_actual = min(abierta, key=lambda n: n.f)
            abierta.remove(nodo_actual)
            cerrada.add(nodo_actual.posicion)

            # Verificar si hemos llegado al objetivo
            if nodo_actual == nodo_objetivo:
                return self.reconstruir_ruta(nodo_actual)

            # Generar nodos hijos
            for movimiento in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nueva_pos = (nodo_actual.posicion[0] + movimiento[0], nodo_actual.posicion[1] + movimiento[1])

                # Verificar si la nueva posición es válida
                if 0 <= nueva_pos[0] < self.mundo.tamano and 0 <= nueva_pos[1] < self.mundo.tamano:
                    # Verificar si la nueva posición es un peligro
                    if nueva_pos in self.mundo.peligros or nueva_pos == self.mundo.monstruo:
                        continue

                    # Crear un nuevo nodo
                    nodo_hijo = Nodo(nueva_pos, nodo_actual)

                    # Si el nodo ya está en la lista cerrada, ignorarlo
                    if nodo_hijo.posicion in cerrada:
                        continue

                    # Calcular g, h y f
                    costo_movimiento = self.mundo.costos[nueva_pos[0]][nueva_pos[1]]  # Costo de la celda
                    nodo_hijo.g = nodo_actual.g + costo_movimiento
                    nodo_hijo.h = self.distancia_manhattan(nodo_hijo.posicion, nodo_objetivo.posicion)
                    nodo_hijo.f = nodo_hijo.g + nodo_hijo.h

                    # Si el nodo ya está en la lista abierta y tiene un costo mayor, ignorarlo
                    if any(nodo_hijo.posicion == n.posicion and nodo_hijo.g > n.g for n in abierta):
                        continue

                    # Agregar el nodo a la lista abierta
                    abierta.append(nodo_hijo)

        return None  # No se encontró un camino

    def reconstruir_ruta(self, nodo):
        ruta = []
        while nodo:
            ruta.append(nodo.posicion)
            nodo = nodo.padre
        ruta.reverse()
        return ruta

    def mover_hacia_premio(self):
        if not self.vivo or self.oro_recogido:
            return

        # Encontrar el camino usando A*
        ruta = self.a_estrella()
        if not ruta:
            print("No hay camino seguro hacia el premio.")
            return

        # Moverse paso a paso por la ruta
        for paso in ruta:
            self.posicion = paso
            self.ruta.append(self.posicion)  # Agregar la posición actual a la ruta
            self.costo_total += self.mundo.costos[paso[0]][paso[1]]  # Sumar el costo de la celda
            self.mundo.revelado[paso[0]][paso[1]] = True  # Revelar el costo de la celda
            self.percepcion()
            self.mundo.dibujar(self.posicion)
            print(f"Ruta actual: {self.ruta}")  # Mostrar la ruta actual
            time.sleep(1)

            if not self.vivo or self.oro_recogido:
                break

        # Mostrar la ruta completa y el costo total al final
        if self.oro_recogido:
            print("\n¡Ruta completa encontrada!")
            print(" -> ".join(map(str, self.ruta)))
            print(f"Costo total de la ruta: {self.costo_total}")
            print(f"Características finales del pingüino: {self.pinguino}")

            # Mejorar la resistencia a la fatiga en función del costo total
            incremento_resistencia = self.costo_total // 10  # Cada 10 unidades de costo, +1 de resistencia
            self.pinguino.mejorar_caracteristica("Resistencia al agotamiento", incremento_resistencia)

    def percepcion(self):
        x, y = self.posicion
        # Ver si el agente ha caído en un pozo
        if self.posicion in self.mundo.peligros:
            print("¡Has caído en un pozo! Estás muerto.")
            self.vivo = False
            return

        # Ver si el agente está cerca del Wumpus
        if abs(x - self.mundo.monstruo[0]) <= 1 and abs(y - self.mundo.monstruo[1]) <= 1:
            print("Sientes el olor del Wumpus... ¡Cuidado!")
        
        # Ver si el agente ha encontrado el oro
        if self.posicion == self.mundo.premio:
            print("¡Has encontrado el oro!")
            self.oro_recogido = True

        # Ver si el agente ha llegado al Wumpus
        if self.posicion == self.mundo.monstruo:
            print("¡Has sido devorado por el Wumpus! Estás muerto.")
            self.vivo = False

        # Mejorar características del pingüino según las condiciones
        if self.mundo.costos[x][y] == 2:  # Agua
            print("El pingüino ha pasado por agua. Mejorando habilidad de nado...")
            self.pinguino.mejorar_caracteristica("Habilidad de Nado")
        elif self.mundo.costos[x][y] == 3:  # Arena
            print("El pingüino ha cruzado arena. Mejorando habilidad para cruzar arena...")
            self.pinguino.mejorar_caracteristica("Habilidad para cruzar arena")

    def estado(self):
        if self.vivo:
            print(f"Posición actual: {self.posicion}")
        else:
            print("El agente ha muerto.")

# Función para guardar la información del pingüino en un archivo
def guardar_pinguino(pinguino, numero_pinguino, nivel):
    with open(ARCHIVO_PINGUINOS, "a") as archivo:
        archivo.write(f"Pinguino {numero_pinguino}\n")
        archivo.write(f"Nivel {nivel} - Cadena genética: {pinguino}\n")
        archivo.write("Características:\n")
        for caracteristica, valor in pinguino.caracteristicas.items():
            if caracteristica in descripciones:
                archivo.write(f"- {caracteristica}: {descripciones[caracteristica][valor]}\n")
        archivo.write("-" * 55 + "\n")  # Línea separadora

# Función principal del juego
def jugar():
    # Preguntar al usuario cuántos niveles desea que el pingüino complete
    niveles_a_jugar = int(input("¿Cuántos niveles deseas que el pingüino complete? "))

    nivel = 1
    tamano_mapa = tamano_inicial
    numero_pinguino = 1  # Contador de pingüinos

    while nivel <= niveles_a_jugar:
        print(f"\n--- Nivel {nivel} ---")
        mundo = Tablero(tamano_mapa)
        agente = Agente(mundo)

        # Dibujar el estado inicial
        pantalla = pygame.display.set_mode((tamano_mapa * tamano_celda, tamano_mapa * tamano_celda))
        pygame.display.set_caption(f"Proyecto 1.- Agente Inteligente - Nivel {nivel}")
        mundo.dibujar(agente.posicion)
        time.sleep(2)

        # El agente intenta moverse hacia el premio
        agente.mover_hacia_premio()

        # Mostrar la descripción del pingüino
        print(agente.pinguino.describir())

        # Guardar la información del pingüino en el archivo
        guardar_pinguino(agente.pinguino, numero_pinguino, nivel)
        numero_pinguino += 1  # Incrementar el contador de pingüinos

        # Pasar al siguiente nivel automáticamente
        if agente.oro_recogido:
            nivel += 1
            tamano_mapa += 2  # Aumentar el tamaño del mapa para el siguiente nivel
        else:
            print("¡Juego terminado!")
            break

    print("\n¡Todos los niveles completados!")

# Ejecutar el juego
jugar()
pygame.quit()