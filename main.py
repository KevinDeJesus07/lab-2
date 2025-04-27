# -*- coding: utf-8 -*- # Especificar codificación UTF-8

"""
Cine Cultural Barranquilla - Sistema de Gestión y Reservas (Versión GUI Inicial)

Descripción:
Este script implementa una interfaz gráfica (GUI) básica para la gestión
de un cine, permitiendo visualizar salas, asientos y (en futuras versiones)
gestionar películas, funciones y la compra de tiquetes.

Desarrollo:
- Se requiere Python 3.x.
- Instalar la biblioteca Pillow para el manejo de imágenes:
  pip install Pillow
- Archivos necesarios en el mismo directorio que main.py:
  - movies.txt: Archivo de texto con la información de las funciones.
    Formato por línea: DD/MM/YYYY - HH:MM;Nombre Película;Género;Nombre Sala
  - seat_available.png: Imagen para asientos disponibles (40x40 recomendado).
  - seat_occupied.png: Imagen para asientos ocupados (40x40 recomendado).
- (Opcional/Recomendado) Crear un archivo 'tickets.txt' vacío si se implementa
  la escritura separada de tiquetes (ver TODO en clase Admin).

Autor: [Tu Nombre/Alias]
Fecha: 2025-04-27 (Fecha de esta versión)
"""

import tkinter as tk
from tkinter import ttk # ttk no se usa activamente aún, pero está importado
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from PIL import Image, ImageTk # Necesita 'pip install Pillow'

# --- Constantes ---
MOVIE_DATA_FILE = 'movies.txt'  # Archivo de datos de funciones
# TICKET_DATA_FILE = 'tickets.txt' # RECOMENDADO: Usar archivo separado para tiquetes
DEFAULT_SEATS_PER_THEATER = 80
SEAT_IMG_AVAILABLE = "seat_available.png"
SEAT_IMG_OCCUPIED = "seat_occupied.png"
SEAT_IMG_WIDTH = 40
SEAT_IMG_HEIGHT = 40
DEFAULT_THEATER_NAMES = ['Sala 1', 'Sala 2', 'Sala 3']


class Asiento:
    """Representa un único asiento en una sala de cine."""
    def __init__(self, id_asiento: str):
        """
        Inicializa un asiento.

        Args:
            id_asiento (str): Identificador único del asiento (ej. "A1", "J8").
        """
        self.id = id_asiento
        self.disponible = True

    def está_disponible(self) -> bool:
        """Verifica si el asiento está disponible."""
        return self.disponible

    def reservar(self) -> None:
        """Marca el asiento como ocupado (no disponible)."""
        if not self.disponible:
            # Considerar si realmente se debe lanzar un error o solo registrar
            print(f"Advertencia: Intento de reservar asiento {self.id} ya ocupado.")
            # raise ValueError(f"El asiento {self.id} no está disponible")
        self.disponible = False

    def desreservar(self) -> None:
        """Marca el asiento como disponible."""
        # No es necesario verificar si ya estaba disponible, simplemente se asegura
        self.disponible = True

    def __str__(self) -> str:
        """Representación textual del asiento."""
        return f"Asiento({self.id}, {'Disponible' if self.disponible else 'Ocupado'})"

    def __repr__(self) -> str:
        """Representación oficial del objeto asiento."""
        return f"Asiento(id='{self.id}')"

class Teatro:
    """Representa una sala de cine física con sus asientos."""
    def __init__(self, nombre: str, cantidad_asientos: int = DEFAULT_SEATS_PER_THEATER):
        """
        Inicializa una sala de cine.

        Args:
            nombre (str): Nombre de la sala (ej. "Sala 1").
            cantidad_asientos (int): Número total de asientos en la sala.
                                      Debe ser divisible por el número de filas (10).
        """
        self.nombre = nombre
        self.asientos: List[Asiento] = []

        # Generación inicial de IDs de asientos (requiere ajuste si el layout cambia)
        # Asume 10 filas A-J. Si cantidad_asientos no es 80, esto puede fallar.
        filas = "ABCDEFGHIJ"
        if cantidad_asientos % len(filas) != 0:
            print(f"Advertencia: La cantidad de asientos ({cantidad_asientos}) "
                  f"no es divisible por el número de filas ({len(filas)}). "
                  f"La generación de IDs puede ser incorrecta.")
        
        # Calcula asientos por fila basado en la cantidad total.
        # Esto es una simplificación; el layout real se define en la GUI ahora.
        # Mantenerlo podría ser útil para lógica no-GUI o como fallback.
        asientos_por_fila = cantidad_asientos // len(filas)
        if asientos_por_fila == 0 and cantidad_asientos > 0:
             asientos_por_fila = 1 # Evitar división por cero si hay menos asientos que filas

        asiento_count = 0
        for fila in filas:
            for num in range(1, asientos_por_fila + 1):
                if asiento_count < cantidad_asientos:
                    asiento_id = f"{fila}{num}"
                    self.asientos.append(Asiento(asiento_id))
                    asiento_count += 1
                else:
                    break # No crear más asientos de los especificados
            if asiento_count >= cantidad_asientos:
                break
        
        # Rellenar si faltan asientos por cálculo de filas/columnas inexacto
        while len(self.asientos) < cantidad_asientos:
             self.asientos.append(Asiento(f"Extra{len(self.asientos) + 1}"))


    def obtener_asientos_disponibles(self) -> List[Asiento]:
        """Devuelve una lista de los asientos que están disponibles."""
        return [asiento for asiento in self.asientos if asiento.está_disponible()]

    def obtener_asiento_por_id(self, id_asiento: str) -> Optional[Asiento]:
         """Busca y devuelve un asiento por su ID."""
         for asiento in self.asientos:
              if asiento.id == id_asiento:
                   return asiento
         return None

    def reiniciar(self) -> None:
        """Pone todos los asientos de la sala como disponibles."""
        for asiento in self.asientos:
            asiento.desreservar()

    def __str__(self) -> str:
        """Representación textual del teatro."""
        return f"Teatro({self.nombre}, Asientos: {len(self.asientos)})"

class Pelicula:
    """Representa una película con su nombre y género."""
    def __init__(self, nombre: str, genero: str):
        """
        Inicializa una película.

        Args:
            nombre (str): Título de la película.
            genero (str): Género de la película.
        """
        self.nombre = nombre
        self.genero = genero

    def obtener_informacion(self) -> str:
        """Devuelve una cadena con el nombre y género de la película."""
        return f"{self.nombre} ({self.genero})"

    def __str__(self) -> str:
        """Representación textual de la película."""
        return self.obtener_informacion()

class Funcion:
    """Representa una proyección específica de una película en una sala y hora."""
    def __init__(self, fecha: datetime, pelicula: Pelicula, teatro: Teatro):
        """
        Inicializa una función (proyección).

        Args:
            fecha (datetime): Fecha y hora de inicio de la función.
            pelicula (Pelicula): Objeto Pelicula que se proyecta.
            teatro (Teatro): Objeto Teatro donde se proyecta.
                             Importante: Esta clase NO gestiona el estado de los
                             asientos para esta función específica; asume que
                             el objeto Teatro recibido refleja el estado deseado
                             o que será gestionado externamente.
        """
        self.pelicula = pelicula
        # TODO: Considerar si Función debería tener su *propia copia*
        # del estado de los asientos del teatro para esa hora específica,
        # en lugar de depender del estado global del objeto Teatro.
        self.teatro = teatro
        self.fecha = fecha
        # Define un límite (ej. 30 min después del inicio) - Uso potencial futuro
        self.fechaLimite = fecha + timedelta(minutes=30)

    def obtener_informacion(self) -> str:
        """Devuelve una cadena con los detalles de la función."""
        return f"{self.pelicula.nombre} en {self.teatro.nombre} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"

    def reiniciar_asientos_asociados(self) -> None:
        """Reinicia el estado de los asientos en el Teatro asociado a esta función."""
        # CUIDADO: Esto afecta al objeto Teatro compartido. Ver TODO en __init__.
        self.teatro.reiniciar()

    def fechaLimite_pasada(self) -> bool:
        """Verifica si la fecha límite para esta función ya pasó."""
        return datetime.now() > self.fechaLimite

    def obtener_asientos_disponibles(self) -> List[Asiento]:
         """Obtiene los asientos disponibles DEL TEATRO asociado."""
         # CUIDADO: Devuelve disponibilidad global del teatro, no específica de la función. Ver TODO.
         return self.teatro.obtener_asientos_disponibles()

    def esta_disponible_en_fecha(self, tiempoDeReferencia: datetime) -> bool:
        """Verifica si la función aún no ha comenzado respecto a un tiempo dado."""
        return self.fecha >= tiempoDeReferencia

    def __str__(self) -> str:
        """Representación textual de la función."""
        return self.obtener_informacion()

class Tiquete:
    """Representa un tiquete o boleto comprado para una función."""
    def __init__(self, precio: float, funcion: Funcion, nombre_cliente: str, asiento: Asiento):
        """
        Inicializa un tiquete.

        Args:
            precio (float): Precio del tiquete.
            funcion (Funcion): La función para la cual es el tiquete.
            nombre_cliente (str): Nombre del cliente que compró el tiquete.
            asiento (Asiento): El asiento específico reservado.
        """
        self.precio = precio
        self.funcion = funcion
        self.nombre_cliente = nombre_cliente
        self.asiento = asiento # Guarda la referencia al objeto Asiento

    def obtener_informacion(self) -> str:
        """Devuelve una cadena con todos los detalles del tiquete."""
        return (
            f"Tiquete para {self.funcion.obtener_informacion()}\n"
            f"Nombre del cliente: {self.nombre_cliente}\n"
            f"Asiento: {self.asiento.id}\n"
            f"Precio: ${self.precio:.2f}"
        )

    def __str__(self) -> str:
        """Representación textual del tiquete."""
        return f"Tiquete({self.funcion.pelicula.nombre}, Asiento: {self.asiento.id}, Cliente: {self.nombre_cliente})"

class Cliente:
    """Representa a un cliente del cine."""
    def __init__(self, nombre: str, id_cliente: str):
        """
        Inicializa un cliente.

        Args:
            nombre (str): Nombre del cliente.
            id_cliente (str): Identificador único del cliente (ej. cédula).
        """
        self.nombre = nombre
        self.id = id_cliente # Usar 'id_cliente' para evitar colisión con builtin 'id'

    def __str__(self) -> str:
        """Representación textual del cliente."""
        return f"Cliente({self.nombre}, ID: {self.id})"


class ControladorDeArchivos:
    """Gestiona la lectura y escritura de datos en archivos de texto."""
    def __init__(self, ruta: str):
        """
        Inicializa el controlador apuntando a un archivo específico.

        Args:
            ruta (str): Ruta al archivo de datos (ej. 'movies.txt').
        """
        self.ruta = ruta

    def leer(self) -> List[List[str]]:
        """
        Lee todas las líneas del archivo y las devuelve como una lista de listas.
        Cada sublista representa una línea dividida por el delimitador ';'.

        Returns:
            List[List[str]]: Lista de registros, donde cada registro es una lista
                             de campos (strings). Devuelve lista vacía si hay error
                             o el archivo no existe.
        """
        try:
            with open(self.ruta, "r", encoding='utf-8') as archivo:
                # Lee líneas no vacías, quita espacios extra, divide por ';'
                return [linea.strip().split(";")
                        for linea in archivo if linea.strip()]
        except FileNotFoundError:
            print(f"Advertencia: Archivo no encontrado en '{self.ruta}'. Se creará uno nuevo al escribir.")
            return []
        except Exception as e:
            print(f"Error inesperado al leer el archivo '{self.ruta}': {e}")
            return []

    def escribir(self, datos: List[str]) -> None:
        """
        Añade una nueva línea al final del archivo.
        Los datos se unen con ';' antes de escribirse.

        Args:
            datos (List[str]): Una lista de strings que representan los campos
                               de la línea a escribir.
        """
        try:
            with open(self.ruta, "a", encoding='utf-8') as archivo:
                # Une los datos con ';' y añade un salto de línea
                linea = ';'.join(datos) + '\n'
                archivo.write(linea)
        except Exception as e:
            print(f"Error inesperado al escribir en el archivo '{self.ruta}': {e}")

    def filtrar(self, criterio: str) -> List[List[str]]:
        """
        (Experimental) Filtra los registros leídos buscando un criterio en cualquiera de sus campos.

        Args:
            criterio (str): Texto a buscar dentro de los campos de cada registro.

        Returns:
            List[List[str]]: Lista de registros que cumplen el criterio.
        """
        registros = self.leer()
        return [registro for registro in registros
                if any(criterio in campo for campo in registro)]

class Admin:
    """
    Clase principal para la lógica de negocio del cine.
    Gestiona teatros, funciones, clientes y tiquetes.
    (Actualmente desacoplada de la GUI).
    """
    def __init__(self, nombre_cine: str):
        """
        Inicializa el administrador del cine.

        Args:
            nombre_cine (str): Nombre del cine.
        """
        self.nombre = nombre_cine
        self.clientes: List[Cliente] = []

        # Inicializa los teatros definidos en las constantes
        self.teatros: Dict[str, Teatro] = {
            nombre: Teatro(nombre) for nombre in DEFAULT_THEATER_NAMES
        }

        # Diccionario para almacenar las funciones programadas por sala
        self.funciones_diarias: Dict[str, List[Funcion]] = {
            nombre: [] for nombre in DEFAULT_THEATER_NAMES
        }

        # Diccionario para almacenar los tiquetes comprados por ID de cliente
        self.tiquetes: Dict[str, List[Tiquete]] = {} # Clave es id_cliente (str)

        # Controlador para leer/escribir datos de funciones
        # TODO: Crear un controlador/archivo separado para tiquetes.
        self.controlador_funciones = ControladorDeArchivos(MOVIE_DATA_FILE)
        # self.controlador_tiquetes = ControladorDeArchivos(TICKET_DATA_FILE) # Recomendado

        # *** ADVERTENCIA IMPORTANTE ***
        # La lógica actual para guardar tiquetes usa el mismo archivo
        # que las funciones (MOVIE_DATA_FILE). Esto puede CORROMPER
        # el archivo movies.txt. Se recomienda implementar un archivo
        # separado ('tickets.txt') y usar un segundo ControladorDeArchivos.
        print("\n*** ADVERTENCIA: Guardado de tiquetes configurado en 'movies.txt'. "
              "Se recomienda usar un archivo 'tickets.txt' separado. ***\n")
        self.controlador_tiquetes_actual = self.controlador_funciones # Temporal, ¡cambiar!


    def add_cliente(self, cliente: Cliente) -> None:
        """Añade un nuevo cliente al sistema."""
        if not isinstance(cliente, Cliente):
             print("Error: Intento de añadir objeto que no es Cliente.")
             return
        # Verificar si el cliente ya existe por ID
        if self.get_cliente(cliente.id):
             print(f"Advertencia: Cliente con ID {cliente.id} ya existe.")
             return
        self.clientes.append(cliente)
        # Inicializar lista de tiquetes para el nuevo cliente
        self.tiquetes[cliente.id] = []
        print(f"Cliente '{cliente.nombre}' añadido.")

    def get_cliente(self, id_cliente: str) -> Optional[Cliente]:
        """Busca y devuelve un cliente por su ID."""
        for cliente in self.clientes:
            if cliente.id == id_cliente:
                return cliente
        return None

    def asignar_función(self, funcion: Funcion) -> bool:
        """
        Añade una función a la programación de la sala correspondiente.
        Actualmente limita a 2 funciones por sala por día (lógica simplificada).

        Args:
            funcion (Funcion): La función a programar.

        Returns:
            bool: True si se asignó correctamente, False si hubo un error
                  (ej. sala llena o no existe).
        """
        if funcion.teatro.nombre not in self.funciones_diarias:
            print(f"Error: Teatro '{funcion.teatro.nombre}' no existe en la programación.")
            return False

        funciones_sala = self.funciones_diarias[funcion.teatro.nombre]

        # Lógica de validación simple (ej: no más de 2 funciones por sala)
        # TODO: Implementar validación de horarios más robusta (solapamientos)
        if len(funciones_sala) >= 2:
            print(f"Advertencia: El teatro {funcion.teatro.nombre} ya tiene 2 funciones. No se añadió '{funcion.pelicula.nombre}'.")
            # Considerar lanzar un error si es una regla estricta
            # raise ValueError(f"El teatro {funcion.teatro.nombre} ya tiene dos funciones programadas")
            return False

        funciones_sala.append(funcion)
        print(f"Función asignada: {funcion}")
        return True

    def cargar_funciones_desde_archivo(self) -> List[Funcion]:
        """
        Carga las funciones desde el archivo MOVIE_DATA_FILE y las asigna.

        Returns:
            List[Funcion]: Lista de las funciones cargadas y asignadas exitosamente.
        """
        funciones_cargadas = []
        print(f"Cargando funciones desde '{self.controlador_funciones.ruta}'...")
        registros = self.controlador_funciones.leer()

        if not registros:
             print("No se encontraron funciones en el archivo o el archivo está vacío.")
             return []

        for i, registro in enumerate(registros):
            # Verificar que el registro tenga el número esperado de campos
            if len(registro) >= 4:
                fecha_str, nombre_pelicula, genero, nombre_sala = registro[:4]
                try:
                    # Parsear la fecha - CORREGIDO EL FORMATO
                    fecha = datetime.strptime(fecha_str.strip(), '%d/%m/%Y - %H:%M')

                    # Obtener el teatro correspondiente
                    teatro = self.teatros.get(nombre_sala.strip())
                    if teatro is None:
                        raise ValueError(f"Teatro '{nombre_sala.strip()}' inválido en línea {i+1}")

                    # Crear objetos Pelicula y Funcion
                    pelicula = Pelicula(nombre_pelicula.strip(), genero.strip())
                    funcion = Funcion(fecha, pelicula, teatro)

                    # Intentar asignar la función
                    if self.asignar_función(funcion):
                         funciones_cargadas.append(funcion)

                except ValueError as e:
                    # Error al parsear fecha, encontrar teatro o asignar función
                    print(f"Error al procesar línea {i+1} del archivo: {e}")
                except Exception as e:
                    print(f"Error inesperado procesando línea {i+1}: {registro} -> {e}")
            else:
                print(f"Advertencia: Línea {i+1} ignorada por tener formato incorrecto (campos: {len(registro)}): {registro}")

        print(f"Se cargaron {len(funciones_cargadas)} funciones exitosamente.")
        return funciones_cargadas


    def comprar_tiquetes(self, funcion: Funcion, cliente: Cliente, ids_asientos: List[str], precio_unitario: float) -> List[Tiquete]:
        """
        Procesa la compra de uno o más tiquetes para una función y cliente.

        Args:
            funcion (Funcion): La función para la que se compran los tiquetes.
            cliente (Cliente): El cliente que realiza la compra.
            ids_asientos (List[str]): Lista de IDs de los asientos a comprar.
            precio_unitario (float): Precio de cada tiquete.

        Returns:
            List[Tiquete]: Lista de los tiquetes generados.

        Raises:
            ValueError: Si alguno de los asientos no está disponible o si
                        ocurre un error inesperado.
            TypeError: Si los argumentos no son del tipo esperado.
        """
        if not isinstance(funcion, Funcion) or not isinstance(cliente, Cliente):
            raise TypeError("Argumentos 'funcion' y 'cliente' inválidos.")
        if not ids_asientos:
             raise ValueError("Se debe seleccionar al menos un asiento.")

        tiquetes_comprados = []
        asientos_a_reservar: List[Asiento] = []

        # 1. Verificar disponibilidad y obtener objetos Asiento
        for asiento_id in ids_asientos:
            asiento = funcion.teatro.obtener_asiento_por_id(asiento_id)
            if asiento is None:
                raise ValueError(f"El asiento con ID '{asiento_id}' no existe en la sala '{funcion.teatro.nombre}'.")
            if not asiento.está_disponible():
                raise ValueError(f"El asiento {asiento_id} no está disponible para la función seleccionada.")
            asientos_a_reservar.append(asiento)

        # 2. Reservar asientos y crear tiquetes
        # (Hacer esto después de verificar todos para atomicidad parcial)
        try:
            for asiento in asientos_a_reservar:
                asiento.reservar() # Marcar como ocupado en el objeto Teatro
                tiquete = Tiquete(precio_unitario, funcion, cliente.nombre, asiento)
                tiquetes_comprados.append(tiquete)

                # Añadir tiquete a la lista del cliente
                if cliente.id not in self.tiquetes:
                    self.tiquetes[cliente.id] = [] # Asegurar que la lista existe
                self.tiquetes[cliente.id].append(tiquete)

                # Guardar tiquete en archivo (¡Usando controlador incorrecto!)
                self.guardar_tiquete_en_archivo(tiquete) # ¡¡ADVERTENCIA!!

            print(f"Compra exitosa para {cliente.nombre}: {len(tiquetes_comprados)} tiquetes.")
            return tiquetes_comprados

        except Exception as e:
            # Revertir reservas si algo falla durante la creación/guardado
            print(f"Error durante la compra, revirtiendo reservas: {e}")
            for asiento in asientos_a_reservar:
                # Solo des-reserva si fue marcado como no disponible en este intento
                if not asiento.está_disponible():
                     asiento.desreservar()
            raise ValueError(f"Error al procesar la compra: {e}")


    def get_tiquetes_por_cliente(self, id_cliente: str) -> List[Tiquete]:
        """Obtiene la lista de tiquetes comprados por un cliente."""
        return self.tiquetes.get(id_cliente, [])

    def get_funciones_disponibles_por_fecha(self, fecha: datetime, incluir_pasadas_hoy: bool = False) -> List[Funcion]:
        """
        Obtiene las funciones programadas para una fecha específica.

        Args:
            fecha (datetime): La fecha para la cual buscar funciones. La hora se ignora
                              a menos que sea hoy y 'incluir_pasadas_hoy' sea False.
            incluir_pasadas_hoy (bool): Si es True y la fecha es hoy, incluye todas las
                                      funciones del día. Si es False y la fecha es hoy,
                                      solo incluye las que aún no han comenzado.

        Returns:
            List[Función]: Lista ordenada por hora de las funciones encontradas.
        """
        tiempo_referencia: datetime
        hoy = datetime.now().date()

        if fecha.date() == hoy and not incluir_pasadas_hoy:
            # Si es hoy y solo queremos futuras, usar hora actual
            tiempo_referencia = datetime.now()
        else:
            # Para otras fechas o si queremos todas las de hoy, usar inicio del día
            tiempo_referencia = fecha.replace(hour=0, minute=0, second=0, microsecond=0)

        todas_las_funciones_dia: List[Funcion] = []
        for nombre_sala in self.funciones_diarias:
            for funcion in self.funciones_diarias[nombre_sala]:
                # Comprobar si la función es del día buscado
                if funcion.fecha.date() == fecha.date():
                    # Comprobar si cumple el criterio de tiempo (futura o todas)
                    if funcion.esta_disponible_en_fecha(tiempo_referencia):
                        todas_las_funciones_dia.append(funcion)

        # Ordenar por hora de la función
        return sorted(todas_las_funciones_dia, key=lambda f: f.fecha)


    def guardar_tiquete_en_archivo(self, tiquete: Tiquete) -> None:
        """
        Guarda la información de un tiquete en el archivo configurado.
        *** ADVERTENCIA: Configurado para usar el archivo de películas. ***
        *** ¡Esto puede corromper 'movies.txt'! ***
        """
        tiquete_data = [
            tiquete.funcion.fecha.strftime('%d/%m/%Y - %H:%M'), # Formato consistente
            tiquete.funcion.pelicula.nombre,
            tiquete.funcion.teatro.nombre,
            tiquete.asiento.id,
            tiquete.nombre_cliente,
            f"{tiquete.precio:.2f}" # Formatear precio
        ]
        # Usar el controlador configurado (¡que apunta a movies.txt por defecto!)
        self.controlador_tiquetes_actual.escribir(tiquete_data)


    def mostrar_tablero_consola(self, teatro: Teatro) -> None:
        """
        (Utilidad de Depuración) Muestra el estado de los asientos de un teatro
        en la consola. Asume un layout simple de 10x(N/10).
        """
        if not teatro or not teatro.asientos:
             print(f"No se puede mostrar tablero para el teatro: {teatro.nombre if teatro else 'N/A'}")
             return

        filas = "ABCDEFGHIJ"
        asientos_por_fila = len(teatro.asientos) // len(filas)
        if asientos_por_fila == 0:
             print("No se pueden determinar asientos por fila.")
             return

        print(f"\n--- Estado Asientos: {teatro.nombre} ---")
        asiento_idx = 0
        for i, fila_letra in enumerate(filas):
            if asiento_idx >= len(teatro.asientos): break # Evitar salir de rango

            linea = f"{fila_letra} | "
            # Obtener los asientos para esta fila conceptual
            asientos_en_fila = teatro.asientos[asiento_idx : asiento_idx + asientos_por_fila]
            for asiento in asientos_en_fila:
                estado = "[ ]" if asiento.está_disponible() else "[X]"
                # Ajustar padding para IDs cortos/largos
                linea += f"{asiento.id:<3}{estado} "
            print(linea)
            asiento_idx += asientos_por_fila
        print("------------------------------")


class TheaterGUI:
    """Interfaz gráfica principal para la aplicación del cine."""

    def __init__(self, root: tk.Tk):
        """
        Inicializa la interfaz gráfica.

        Args:
            root (tk.Tk): La ventana raíz de Tkinter.
        """
        self.root = root
        self.root.title("Cine Cultural Barranquilla")
        self.root.geometry("1280x720") # Tamaño ventana principal

        # --- Carga de Imágenes para Asientos ---
        self.img_available = None
        self.img_occupied = None
        try:
            # Abrir imágenes originales con Pillow
            pil_img_available = Image.open(SEAT_IMG_AVAILABLE)
            pil_img_occupied = Image.open(SEAT_IMG_OCCUPIED)

            # Redimensionar si es necesario (ej. a 40x40 píxeles)
            pil_img_available = pil_img_available.resize(
                (SEAT_IMG_WIDTH, SEAT_IMG_HEIGHT), Image.Resampling.LANCZOS
            )
            pil_img_occupied = pil_img_occupied.resize(
                (SEAT_IMG_WIDTH, SEAT_IMG_HEIGHT), Image.Resampling.LANCZOS
            )

            # Convertir a formato Tkinter y guardar
            self.img_available = ImageTk.PhotoImage(pil_img_available)
            self.img_occupied = ImageTk.PhotoImage(pil_img_occupied)
            print("Imágenes de asientos cargadas correctamente.")

        except FileNotFoundError:
            print(f"Error: No se encontraron archivos de imagen ({SEAT_IMG_AVAILABLE}, {SEAT_IMG_OCCUPIED}). "
                  "Se usarán botones grises como fallback.")
        except ImportError:
             print("Error: La biblioteca Pillow no está instalada ('pip install Pillow'). "
                   "Se usarán botones grises como fallback.")
        except Exception as e:
             print(f"Error inesperado al cargar imágenes: {e}")


        # --- Gestión de Salas (Versión GUI Desacoplada) ---
        # TODO: Esta GUI crea sus propias instancias de Teatro.
        # NECESITA conectarse con la instancia de Admin para obtener
        # las salas reales, las funciones y el estado de los asientos
        # actualizado según la función seleccionada.
        print("\n*** ADVERTENCIA: La GUI opera con datos de sala locales. "
              "No conectada a la lógica de Admin/Funciones/Reservas reales. ***\n")
        self.salas = [Teatro(nombre) for nombre in DEFAULT_THEATER_NAMES]
        self.sala_actual_idx = 0 # Índice de la sala mostrada actualmente

        # --- Estado del Modo Desarrollador ---
        self.developer_mode_enabled = False

        # --- Configuración del Layout Principal de la GUI ---
        # Permitir que la fila central (1) se expanda
        self.root.rowconfigure(1, weight=1)
        # Permitir que la columna única (0) se expanda
        self.root.columnconfigure(0, weight=1)

        # --- Barra de Menú Superior ---
        self.menu_frame = tk.Frame(self.root, bg='#e0e0e0', height=50)
        self.menu_frame.grid(row=0, column=0, sticky='ew') # Ocupa todo el ancho
        # Evitar que los widgets internos redimensionen el frame
        self.menu_frame.pack_propagate(False)

        # Crear botones para cada sala
        for idx, sala in enumerate(self.salas):
            btn = tk.Button(
                self.menu_frame,
                text=sala.nombre,
                command=lambda i=idx: self.mostrar_sala(i) # Lambda para pasar el índice correcto
            )
            btn.pack(side='left', padx=10, pady=10) # Empaquetar a la izquierda

        # Botón para activar/desactivar Modo Desarrollador
        self.dev_mode_button = tk.Button(
            self.menu_frame,
            text="Activar Modo Dev",
            command=self.toggle_developer_mode
        )
        self.dev_mode_button.pack(side='right', padx=10, pady=10) # Empaquetar a la derecha

        # --- Zona de Contenido Central ---
        # Frame donde se dibujarán los asientos y la pantalla
        self.content_frame = tk.Frame(self.root, bg='#f8f8f8')
        self.content_frame.grid(row=1, column=0, sticky='nsew') # Ocupa el espacio central

        # --- Barra de Estado Inferior ---
        self.status_frame = tk.Frame(self.root, bg='#e0e0e0', height=30)
        self.status_frame.grid(row=2, column=0, sticky='ew') # Ocupa todo el ancho
        self.status_frame.pack_propagate(False) # Evitar redimensión

        # Etiqueta para mostrar mensajes de estado
        self.status_label = tk.Label(self.status_frame, text="Listo.", anchor='w', bg='#e0e0e0')
        self.status_label.pack(fill='both', padx=10)

        # --- Inicialización Visual ---
        # Mostrar la primera sala al iniciar la aplicación
        self.mostrar_sala(self.sala_actual_idx)


    def toggle_developer_mode(self) -> None:
        """Activa o desactiva el modo desarrollador y actualiza la GUI."""
        self.developer_mode_enabled = not self.developer_mode_enabled
        status_msg = "ACTIVADO" if self.developer_mode_enabled else "DESACTIVADO"
        button_txt = "Desactivar Modo Dev" if self.developer_mode_enabled else "Activar Modo Dev"

        self.dev_mode_button.config(text=button_txt)
        self.status_label.config(text=f"Modo Desarrollador {status_msg}")
        print(f"Modo Desarrollador: {status_msg}")

        # Volver a dibujar la sala actual para aplicar/quitar el estilo Dev
        self.mostrar_sala(self.sala_actual_idx)


    def mostrar_sala(self, idx: int) -> None:
        """
        Limpia el frame de contenido y muestra la pantalla y los asientos
        de la sala con el índice proporcionado.

        Args:
            idx (int): Índice de la sala a mostrar (en la lista self.salas).
        """
        # 1. Validar índice
        if not 0 <= idx < len(self.salas):
            print(f"Error: Índice de sala {idx} fuera de rango.")
            return

        # 2. Limpiar contenido anterior del frame central
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # 3. Obtener la sala y actualizar estado
        sala = self.salas[idx]
        self.sala_actual_idx = idx
        mode_text = "(Modo Dev)" if self.developer_mode_enabled else ""
        self.status_label.config(text=f"Mostrando {sala.nombre} {mode_text}")

        # 4. Dibujar la Pantalla (abajo)
        screen_frame = tk.Frame(self.content_frame, bg='black', height=20)
        screen_frame.pack(side='bottom', fill='x', padx=50, pady=(10, 20)) # pady=(top, bottom)
        screen_label = tk.Label(screen_frame, text="PANTALLA", bg='black', fg='white', font=('Calibri', 10, 'bold'))
        screen_label.pack(pady=2)

        # 5. Dibujar los Asientos (arriba de la pantalla)
        self.mostrar_asientos(self.content_frame, sala)


    def mostrar_asientos(self, parent_frame: tk.Frame, sala: Teatro) -> None:
        """
        Dibuja la cuadrícula de asientos para la sala dada en el frame padre,
        usando el layout realista definido internamente.

        Args:
            parent_frame (tk.Frame): El frame donde se dibujará la cuadrícula de asientos.
            sala (Teatro): La instancia de Teatro (local de la GUI) cuyos asientos se mostrarán.
        """

        # --- Definición del Layout Realista (80 asientos) ---
        seats_layout = [11]*2 + [9]*2 + [7]*5 + [5]*1  # 10 filas
        num_rows = len(seats_layout)
        max_seats_in_row = 11
        num_grid_cols = 1 + max_seats_in_row + 1 # 13 columnas (Pasillo + MaxAsientos + Pasillo)

        parent_bg_color = parent_frame['bg'] # Color de fondo para widgets internos

        # Frame contenedor para la grilla de asientos, centrado
        grid_frame = tk.Frame(parent_frame, bg=parent_bg_color)
        grid_frame.pack(side='top', expand=True, pady=(20, 10)) # Empaquetar arriba

        asiento_index = 0 # Para recorrer la lista sala.asientos

        # --- Iterar y colocar cada elemento en la grilla ---
        for i in range(num_rows): # Filas 0 a 9
            num_seats_this_row = seats_layout[i]
            indent_each_side = (max_seats_in_row - num_seats_this_row) // 2
            start_seat_col = 1 + indent_each_side
            end_seat_col = start_seat_col + num_seats_this_row - 1

            for j in range(num_grid_cols): # Columnas 0 a 12
                # Colocar Pasillo Izquierdo
                if j == 0:
                    aisle_widget = tk.Frame(grid_frame, width=30, height=SEAT_IMG_HEIGHT+10, bg=parent_bg_color)
                # Colocar Pasillo Derecho
                elif j == num_grid_cols - 1:
                    aisle_widget = tk.Frame(grid_frame, width=30, height=SEAT_IMG_HEIGHT+10, bg=parent_bg_color)
                # Colocar Asiento o Espacio Vacío
                else:
                    if start_seat_col <= j <= end_seat_col: # ¿Va un asiento aquí?
                        if asiento_index < len(sala.asientos):
                            asiento = sala.asientos[asiento_index]
                            img = self.img_occupied if not asiento.está_disponible() else self.img_available
                            
                            # Configuración base del botón (sin borde, fondo correcto)
                            btn_conf = { "borderwidth": 0, "highlightthickness": 0,
                                         "relief": "flat", "bg": parent_bg_color,
                                         "activebackground": parent_bg_color }

                            if img: # Si las imágenes se cargaron bien
                                seat_widget = tk.Button(grid_frame, image=img,
                                                        width=SEAT_IMG_WIDTH, height=SEAT_IMG_HEIGHT,
                                                        **btn_conf)
                                seat_widget.image = img # Guardar referencia!
                            else: # Fallback si no hay imágenes
                                color = "red" if not asiento.está_disponible() else "green"
                                seat_widget = tk.Button(grid_frame, text=asiento.id, bg=color,
                                                        width=4, height=2, relief='ridge')

                            # Configuración común (comando, estado dev)
                            seat_widget.config(state='normal')
                            seat_widget.config(command=lambda a=asiento, b=seat_widget: self.on_seat_click(a, b))
                            if self.developer_mode_enabled:
                                seat_widget.config(highlightthickness=1, highlightbackground="blue")

                            asiento_index += 1
                        else: # Error: layout pide más asientos de los que hay
                             print(f"Error Layout: Índice asiento {asiento_index} fuera de rango.")
                             seat_widget = tk.Frame(grid_frame, width=SEAT_IMG_WIDTH+5, height=SEAT_IMG_HEIGHT+5, bg="magenta") # Error visual
                    else: # Espacio vacío por indentación
                        seat_widget = tk.Frame(grid_frame, width=SEAT_IMG_WIDTH+5, height=SEAT_IMG_HEIGHT+5, bg=parent_bg_color)
                    
                    # Colocar el widget (asiento, vacío, pasillo) en la grilla
                    seat_widget.grid(row=i, column=j, padx=5, pady=5)
                    if isinstance(seat_widget, tk.Frame): # Evitar que Frames se encojan
                         seat_widget.pack_propagate(False)


        # Verificar si se usaron todos los asientos esperados
        if asiento_index != DEFAULT_SEATS_PER_THEATER:
            print(f"Advertencia: Layout finalizó usando {asiento_index} asientos, "
                  f"se esperaban {DEFAULT_SEATS_PER_THEATER}.")


    def on_seat_click(self, asiento: Asiento, button: tk.Button) -> None:
        """
        Manejador de eventos para el clic en un botón de asiento.
        Si el modo desarrollador está activo, cambia el estado del asiento (visual).
        Si no, muestra información (lógica de selección/compra futura aquí).

        Args:
            asiento (Asiento): La instancia del asiento asociado al botón clickeado.
            button (tk.Button): El widget del botón que fue clickeado.
        """
        print(f"Clic en asiento: {asiento.id}, Disponible: {asiento.está_disponible()}")

        if self.developer_mode_enabled:
            # --- Modo Desarrollador: Cambiar Estado (Visualmente) ---
            
            # Cambiar estado directamente en el objeto asiento (de la GUI local)
            if asiento.está_disponible():
                asiento.disponible = False
                nueva_imagen = self.img_occupied
                nuevo_estado_str = "Ocupado (Dev)"
                color_fallback = "red"
            else:
                asiento.disponible = True
                nueva_imagen = self.img_available
                nuevo_estado_str = "Disponible (Dev)"
                color_fallback = "green"

            # Actualizar apariencia del botón específico
            if self.img_available and self.img_occupied:
                 button.config(image=nueva_imagen)
                 button.image = nueva_imagen # ¡Actualizar referencia!
            else: # Actualizar fallback
                 button.config(bg=color_fallback, text=asiento.id)

            self.status_label.config(text=f"DevMode: Asiento {asiento.id} -> {nuevo_estado_str}")

        else:
            # --- Modo Normal: Lógica de Selección (Futura) ---
            # TODO: Implementar la selección de asientos para compra.
            # - Marcar visualmente el asiento seleccionado (ej. borde diferente).
            # - Añadir/quitar asiento de una lista de selección temporal.
            # - Mostrar información del asiento/precio.
            estado = "Disponible" if asiento.está_disponible() else "Ocupado"
            self.status_label.config(text=f"Asiento {asiento.id} ({estado}). "
                                           "Seleccione asientos y pulse 'Comprar' (no implementado).")


def main() -> None:
    """Función principal: Inicializa y ejecuta la aplicación Tkinter."""
    print("Iniciando aplicación Cine...")
    root = tk.Tk()
    app = TheaterGUI(root) # Crear la instancia de la GUI
    root.mainloop() # Iniciar el bucle de eventos de Tkinter
    print("Aplicación Cine cerrada.")

# Punto de entrada del script
if __name__ == "__main__":
    main()