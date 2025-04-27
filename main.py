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
from tkinter import ttk, messagebox, simpledialog # ttk no se usa activamente aún, pero está importado
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Tuple
from PIL import Image, ImageTk # Necesita 'pip install Pillow'
import copy

# --- Constantes ---
MOVIE_DATA_FILE = 'movies.txt'  # Archivo de datos de funciones
# TICKET_DATA_FILE = 'tickets.txt' # RECOMENDADO: Usar archivo separado para tiquetes
DEFAULT_SEATS_PER_THEATER = 80
SEAT_IMG_AVAILABLE = "seat_available.png"
SEAT_IMG_OCCUPIED = "seat_occupied.png"
SEAT_IMG_WIDTH = 40
SEAT_IMG_HEIGHT = 40
DEFAULT_THEATER_NAMES = ['Sala 1', 'Sala 2', 'Sala 3']
PRECIO_TIQUETE = 15000 # Precio estándar por tiquete

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
        self.teatro_funcion = copy.deepcopy(teatro)
        self.fecha = fecha
        self.fechaLimite = fecha + timedelta(minutes=30) # Límite de 30 min post-incio

    def obtener_informacion(self) -> str:
        """Devuelve una cadena con los detalles de la función."""
        return f"{self.pelicula.nombre} en {self.teatro_funcion.nombre} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"

    def reiniciar_asientos_asociados(self) -> None:
        """Reinicia el estado de los asientos en el Teatro asociado a esta función."""
        # CUIDADO: Esto afecta al objeto Teatro compartido. Ver TODO en __init__.
        self.teatro_funcion.reiniciar()

    def fechaLimite_pasada(self) -> bool:
        """Verifica si la fecha límite para esta función ya pasó."""
        return datetime.now() > self.fechaLimite

    def obtener_asientos_disponibles(self) -> List[Asiento]:
         """Obtiene los asientos disponibles DEL TEATRO asociado."""
         # CUIDADO: Devuelve disponibilidad global del teatro, no específica de la función. Ver TODO.
         return self.teatro_funcion.obtener_asientos_disponibles()
    
    def obtener_asiento_por_id(self, id_asiento: str) -> Optional[Asiento]:
         """Busca un asiento por ID DENTRO de esta función."""
         for asiento in self.teatro_funcion.asientos:
              if asiento.id == id_asiento:
                   return asiento
         return None

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
            asiento = funcion.obtener_asiento_por_id(asiento_id)
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
    """
    Interfaz gráfica principal para la aplicación del cine.
    Permite visualizar funciones, seleccionar asientos y comprar tiquetes.
    """

    def __init__(self, root: tk.Tk, admin_instance: Admin):
        """
        Inicializa la interfaz gráfica.

        Args:
            root (tk.Tk): La ventana raíz de Tkinter.
            admin_instance (Admin): La instancia del gestor de lógica del cine.
        """
        self.root = root
        self.admin = admin_instance
        self.funcion_seleccionada: Optional[Funcion] = None
        self.asientos_seleccionados_para_compra: List[Asiento] = [] # Asientos marcados para comprar
        self.mapa_widgets_asientos: Dict[str, ttk.Button] = {} # Mapea asiento.id -> widget Button

        self.root.title("Cine Cultural Barranquilla - Taquilla")
        self.root.geometry("1280x768") # Un poco más alto para info de compra

        # --- Carga de Imágenes ---
        self.img_available: Optional[ImageTk.PhotoImage] = None
        self.img_occupied: Optional[ImageTk.PhotoImage] = None
        self.img_selected: Optional[ImageTk.PhotoImage] = None # Imagen para asiento seleccionado
        self._cargar_imagenes_asientos() # Llama a método helper

        # --- Configuración del Layout Principal ---
        self._setup_gui_layout()

        # --- Carga Inicial ---
        # Cargar funciones para la fecha actual al iniciar
        self._on_date_filter_apply()

    def _cargar_imagenes_asientos(self) -> None:
        """Carga las imágenes de los asientos desde archivos."""
        try:
            # Cargar y redimensionar disponible y ocupado
            pil_avail = Image.open(SEAT_IMG_AVAILABLE).resize((SEAT_IMG_WIDTH, SEAT_IMG_HEIGHT), Image.Resampling.LANCZOS)
            pil_occup = Image.open(SEAT_IMG_OCCUPIED).resize((SEAT_IMG_WIDTH, SEAT_IMG_HEIGHT), Image.Resampling.LANCZOS)
            self.img_available = ImageTk.PhotoImage(pil_avail)
            self.img_occupied = ImageTk.PhotoImage(pil_occup)

            # Crear imagen seleccionada (ej: disponible con borde amarillo)
            # Esto requiere manipulación con Pillow, ejemplo básico:
            try:
                from PIL import ImageDraw
                pil_select = pil_avail.copy()
                draw = ImageDraw.Draw(pil_select)
                # Dibuja un borde amarillo de 2px
                draw.rectangle([(0, 0), (SEAT_IMG_WIDTH-1, SEAT_IMG_HEIGHT-1)], outline="gold", width=3)
                self.img_selected = ImageTk.PhotoImage(pil_select)
            except Exception as draw_err:
                print(f"Advertencia: No se pudo crear imagen seleccionada con borde: {draw_err}. Se usará disponible.")
                self.img_selected = self.img_available # Fallback

            print("Imágenes de asientos cargadas.")
        except FileNotFoundError:
            print(f"ERROR CRÍTICO: No se encontraron archivos de imagen ({SEAT_IMG_AVAILABLE}, etc.). La GUI no funcionará correctamente.")
        except Exception as e:
            print(f"Error inesperado al cargar imágenes: {e}")

    def _setup_gui_layout(self) -> None:
        """Configura la estructura principal de widgets de la GUI."""
        self.root.rowconfigure(1, weight=1) # Permitir que fila de contenido principal crezca
        self.root.columnconfigure(0, weight=1)

        # --- Frame Superior (Filtros) ---
        filter_frame = ttk.Frame(self.root, padding="10")
        filter_frame.grid(row=0, column=0, sticky='ew')

        ttk.Label(filter_frame, text="Fecha (DD/MM/YYYY):").pack(side='left', padx=(0, 5))
        self.date_entry_var = tk.StringVar(value=datetime.now().strftime('%d/%m/%Y'))
        date_entry = ttk.Entry(filter_frame, textvariable=self.date_entry_var, width=12)
        date_entry.pack(side='left', padx=5)
        # TODO: Añadir validación o un widget de calendario para la fecha

        search_button = ttk.Button(filter_frame, text="Buscar Funciones", command=self._on_date_filter_apply)
        search_button.pack(side='left', padx=5)

        # --- Frame Principal (Funciones y Asientos) ---
        # Usar PanedWindow permite redimensionar las áreas
        main_pane = ttk.PanedWindow(self.root, orient='horizontal')
        main_pane.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)

        # Frame Izquierdo: Lista de Funciones
        functions_frame = ttk.Frame(main_pane, padding="5")
        main_pane.add(functions_frame, weight=1) # Añadir al PanedWindow

        ttk.Label(functions_frame, text="Funciones Disponibles", font=('Calibri', 12, 'bold')).pack(pady=5)
        
        # Treeview para mostrar funciones
        cols = ('pelicula', 'hora', 'sala')
        self.functions_treeview = ttk.Treeview(functions_frame, columns=cols, show='headings', height=15)
        self.functions_treeview.heading('pelicula', text='Película')
        self.functions_treeview.heading('hora', text='Hora')
        self.functions_treeview.heading('sala', text='Sala')
        self.functions_treeview.column('pelicula', width=200)
        self.functions_treeview.column('hora', width=80, anchor='center')
        self.functions_treeview.column('sala', width=100, anchor='center')

        # Scrollbar para el Treeview
        scrollbar = ttk.Scrollbar(functions_frame, orient='vertical', command=self.functions_treeview.yview)
        self.functions_treeview.configure(yscrollcommand=scrollbar.set)

        self.functions_treeview.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Evento al seleccionar una función en el Treeview
        self.functions_treeview.bind('<<TreeviewSelect>>', self._on_function_select)

        # Frame Derecho: Mapa de Asientos y Pantalla
        self.seat_area_frame = ttk.Frame(main_pane, padding="5")
        main_pane.add(self.seat_area_frame, weight=3) # Dar más peso al área de asientos

        # --- Frame Inferior (Compra y Estado) ---
        purchase_status_frame = ttk.Frame(self.root, padding="5 10 5 10") # padding left, top, right, bottom
        purchase_status_frame.grid(row=2, column=0, sticky='ew')

        # Info de compra
        self.purchase_info_label = ttk.Label(purchase_status_frame, text="Seleccione una función y asientos.", anchor='w')
        self.purchase_info_label.pack(side='left', fill='x', expand=True, padx=5)

        # Botón Comprar
        buy_button = ttk.Button(purchase_status_frame, text="Comprar Entradas", command=self._confirm_purchase)
        buy_button.pack(side='right', padx=5)

        # (Opcional: Botón Modo Dev si aún lo quieres)
        # self.dev_mode_button = ttk.Button(...)

    def _on_date_filter_apply(self) -> None:
        """Obtiene la fecha, busca funciones y las muestra en el Treeview."""
        date_str = self.date_entry_var.get()
        try:
            # Validar y parsear fecha
            selected_date = datetime.strptime(date_str, '%d/%m/%Y')
            print(f"Buscando funciones para: {selected_date.strftime('%Y-%m-%d')}")

            # Obtener funciones del Admin
            # Pide sólo las futuras para hoy por defecto
            funciones = self.admin.get_funciones_disponibles_por_fecha(selected_date, incluir_pasadas_hoy=False)

            # Limpiar vista de funciones
            for item in self.functions_treeview.get_children():
                self.functions_treeview.delete(item)
            
            # Limpiar área de asientos y selección actual
            self._clear_seat_display()
            self.funcion_seleccionada = None
            self.asientos_seleccionados_para_compra = []
            self._update_purchase_info() # Resetear info de compra

            # Poblar Treeview
            self.function_map = {} # Diccionario para mapear iid -> Funcion object
            if funciones:
                for func in funciones:
                    # Insertar fila en el treeview
                    iid = self.functions_treeview.insert('', 'end', values=(
                        func.pelicula.nombre,
                        func.fecha.strftime('%H:%M'),
                        func.teatro_funcion.nombre # Usa la copia profunda
                    ))
                    # Guardar el objeto Funcion asociado a este item id
                    self.function_map[iid] = func
            else:
                self.functions_treeview.insert('', 'end', values=("No hay funciones", "para esta fecha", ""))
                
        except ValueError:
            messagebox.showerror("Error de Fecha", "Formato de fecha inválido. Use DD/MM/YYYY.")
            self._clear_seat_display()
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al buscar funciones: {e}")
            self._clear_seat_display()


    def _on_function_select(self, event=None) -> None:
        """Manejador cuando se selecciona una función en el Treeview."""
        selected_items = self.functions_treeview.selection()
        if not selected_items: # Si no hay selección (ej. al limpiar)
            self.funcion_seleccionada = None
            self._clear_seat_display()
            return

        selected_iid = selected_items[0] # Tomar el primero seleccionado

        # Recuperar el objeto Funcion usando el mapa
        selected_function = self.function_map.get(selected_iid)

        if selected_function:
            self.funcion_seleccionada = selected_function
            print(f"Función seleccionada: {self.funcion_seleccionada}")
            self.asientos_seleccionados_para_compra = [] # Limpiar selección anterior
            self._update_seat_display() # Mostrar asientos de esta función
            self._update_purchase_info() # Actualizar info de compra (costo 0)
        else:
            print(f"Error: No se encontró el objeto Funcion para iid {selected_iid}")
            self.funcion_seleccionada = None
            self._clear_seat_display()

    def _clear_seat_display(self) -> None:
        """Limpia el área de visualización de asientos."""
        for widget in self.seat_area_frame.winfo_children():
            widget.destroy()
        # Podrías poner un Label indicando "Seleccione una función"
        ttk.Label(self.seat_area_frame, text="Seleccione una función para ver los asientos.").pack(padx=20, pady=50)

    def _update_seat_display(self) -> None:
        """Limpia y vuelve a dibujar el área de asientos para la función seleccionada."""
        # 1. Limpiar el frame derecho
        for widget in self.seat_area_frame.winfo_children():
            widget.destroy()

        # 2. Verificar si hay una función seleccionada
        if not self.funcion_seleccionada:
            self._clear_seat_display() # Muestra mensaje "Seleccione función"
            return

        # 3. Dibujar la Pantalla (abajo del seat_area_frame)
        screen_frame = ttk.Frame(self.seat_area_frame, style='Black.TFrame') # Estilo para fondo negro
        self.root.style = ttk.Style()
        self.root.style.configure('Black.TFrame', background='black')
        screen_frame.pack(side='bottom', fill='x', padx=50, pady=(10, 20))
        ttk.Label(screen_frame, text="PANTALLA", background='black', foreground='white', font=('Calibri', 10, 'bold')).pack(pady=2)

        # 4. Dibujar los Asientos (arriba de la pantalla)
        self.mostrar_asientos(self.seat_area_frame, self.funcion_seleccionada)


    def mostrar_asientos(self, parent_frame: tk.Frame, funcion: Funcion) -> None:
        """
        Dibuja la cuadrícula de asientos para la FUNCIÓN dada en el frame padre.
        Usa el layout realista definido y el estado de asientos de funcion.teatro_funcion.

        Args:
            parent_frame (tk.Frame): Frame donde dibujar (seat_area_frame).
            funcion (Funcion): La función específica cuyos asientos se mostrarán.
        """
        # --- Layout y Configuración ---
        seats_layout = [11]*2 + [9]*2 + [7]*5 + [5]*1
        num_rows = len(seats_layout)
        max_seats_in_row = 11
        num_grid_cols = 1 + max_seats_in_row + 1
        parent_bg_color = parent_frame.winfo_toplevel().cget('bg') # Obtener color de fondo raíz
        self.mapa_widgets_asientos = {} # Limpiar mapa para esta función

        # Frame para la grilla
        grid_frame = ttk.Frame(parent_frame) # Usar ttk.Frame
        grid_frame.pack(side='top', expand=True, pady=(20, 10))

        asiento_index = 0
        asientos_de_la_funcion = funcion.teatro_funcion.asientos # Usar asientos de la copia

        # --- Dibujar Grilla ---
        for i in range(num_rows):
            num_seats_this_row = seats_layout[i]
            indent = (max_seats_in_row - num_seats_this_row) // 2
            start_col = 1 + indent
            end_col = start_col + num_seats_this_row - 1

            for j in range(num_grid_cols):
                widget_to_place = None # Widget a colocar en la celda

                # Pasillos
                if j == 0 or j == num_grid_cols - 1:
                    widget_to_place = ttk.Frame(grid_frame, width=30, height=SEAT_IMG_HEIGHT+5)
                # Asientos o Vacíos
                else:
                    if start_col <= j <= end_col: # Zona de asiento
                        if asiento_index < len(asientos_de_la_funcion):
                            asiento = asientos_de_la_funcion[asiento_index]
                            is_available = asiento.está_disponible()
                            is_selected = asiento in self.asientos_seleccionados_para_compra

                            img = None
                            if is_selected and self.img_selected:
                                img = self.img_selected
                            elif not is_available and self.img_occupied:
                                img = self.img_occupied
                            elif is_available and self.img_available:
                                img = self.img_available

                            btn_conf = {"borderwidth": 0, "highlightthickness": 0,
                                        "relief": "flat", "style": "Seat.TButton"}
                                        
                            # Estilo base para botones de asiento (sin bordes)
                            style = ttk.Style()
                            style.configure("Seat.TButton", background=parent_bg_color, borderwidth=0, highlightthickness=0, relief='flat')
                            # Estilo para asiento seleccionado
                            style.map("Selected.TButton", background=[('active', 'gold'), ('!active', 'gold')]) # Ejemplo simple

                            if img:
                                seat_btn = ttk.Button(grid_frame, image=img, style="Seat.TButton",
                                                      **btn_conf)
                                seat_btn.image = img
                            else: # Fallback
                                color = "red" if not is_available else "green"
                                if is_selected: color = "gold"
                                seat_btn = ttk.Button(grid_frame, text=asiento.id, # Usar ttk.Button
                                                      style="Seat.TButton", # Aplicar estilo base
                                                      width=5) # Ancho para texto
                                # Necesitaría configurar colores directamente si no hay tema
                                # seat_btn.configure(background=color) # No siempre funciona bien con ttk

                            seat_btn.config(command=lambda a=asiento, b=seat_btn: self.on_seat_click(a, b))
                            widget_to_place = seat_btn
                            self.mapa_widgets_asientos[asiento.id] = seat_btn # Guardar ref al widget
                            asiento_index += 1
                        else: # Error
                            widget_to_place = ttk.Frame(grid_frame, width=SEAT_IMG_WIDTH+5, height=SEAT_IMG_HEIGHT+5, style='Toolbutton') # Usar estilo base
                            widget_to_place.configure(background='magenta') # Indicar error
                    else: # Espacio vacío
                        widget_to_place = ttk.Frame(grid_frame, width=SEAT_IMG_WIDTH+5, height=SEAT_IMG_HEIGHT+5, style='Toolbutton')

                # Colocar el widget en la grilla
                if widget_to_place:
                    widget_to_place.grid(row=i, column=j, padx=2, pady=2) # Reducir padding
                    if isinstance(widget_to_place, ttk.Frame):
                         widget_to_place.pack_propagate(False)

        if asiento_index != len(asientos_de_la_funcion):
             print(f"Advertencia Layout: Se colocaron {asiento_index} asientos, "
                   f"la función tiene {len(asientos_de_la_funcion)}.")


    def on_seat_click(self, asiento: Asiento, button: ttk.Button) -> None:
        """
        Manejador de clic en asiento para selección/deselección de compra.
        """
        if not self.funcion_seleccionada:
            messagebox.showwarning("Selección Requerida", "Por favor, seleccione primero una función.")
            return

        # Verificar si la función ya pasó el límite de tiempo para comprar/seleccionar
        if self.funcion_seleccionada.fechaLimite_pasada():
             messagebox.showwarning("Tiempo Excedido", "El tiempo para comprar entradas para esta función ha expirado.")
             return

        # Verificar si el asiento está realmente disponible EN ESTA FUNCIÓN
        # (El objeto 'asiento' viene de la copia profunda de la función)
        if asiento.está_disponible():
            if asiento in self.asientos_seleccionados_para_compra:
                # --- Deseleccionar ---
                self.asientos_seleccionados_para_compra.remove(asiento)
                # Cambiar imagen a disponible normal
                if self.img_available:
                    button.config(image=self.img_available)
                    button.image = self.img_available
                else: # Fallback
                    button.config(text=asiento.id) # Quitar estilo seleccionado
                    # Necesitaría reconfigurar color si se usa fallback
            else:
                # --- Seleccionar ---
                self.asientos_seleccionados_para_compra.append(asiento)
                # Cambiar imagen a seleccionada
                if self.img_selected:
                    button.config(image=self.img_selected)
                    button.image = self.img_selected
                else: # Fallback
                    button.config(text=f"[{asiento.id}]") # Indicar selección
                    # Necesitaría configurar color si se usa fallback
        else:
            # Si el asiento no está disponible (ya comprado), informar
            messagebox.showinfo("Asiento Ocupado", f"El asiento {asiento.id} ya está ocupado para esta función.")

        # Actualizar la información de compra (costo, etc.)
        self._update_purchase_info()


    def _update_purchase_info(self) -> None:
        """Actualiza la etiqueta inferior con el número de asientos y costo."""
        num_seleccionados = len(self.asientos_seleccionados_para_compra)
        if num_seleccionados > 0:
            costo_total = num_seleccionados * PRECIO_TIQUETE
            ids_texto = ", ".join(sorted([a.id for a in self.asientos_seleccionados_para_compra]))
            self.purchase_info_label.config(
                text=f"Seleccionados: {num_seleccionados} ({ids_texto}) - Total: ${costo_total:,.0f} COP"
            )
        else:
            self.purchase_info_label.config(text="Seleccione asientos haciendo clic.")


    def _confirm_purchase(self) -> None:
        """Inicia el proceso para confirmar y realizar la compra."""
        # 1. Validaciones Previas
        if not self.funcion_seleccionada:
            messagebox.showwarning("Acción Requerida", "Seleccione una función primero.")
            return
        if not self.asientos_seleccionados_para_compra:
            messagebox.showwarning("Acción Requerida", "Seleccione al menos un asiento.")
            return
        if self.funcion_seleccionada.fechaLimite_pasada():
             messagebox.showerror("Tiempo Excedido", "Ya no se pueden comprar entradas para esta función.")
             return

        # 2. Obtener Datos del Cliente
        id_cliente = simpledialog.askstring("Identificación Cliente", "Ingrese el ID (cédula) del cliente:", parent=self.root)
        if not id_cliente: # Si el usuario cancela
            return

        cliente = self.admin.get_cliente(id_cliente)
        if not cliente:
            nombre_cliente = simpledialog.askstring("Nombre Cliente Nuevo", f"Cliente con ID {id_cliente} no encontrado.\nIngrese el nombre:", parent=self.root)
            if not nombre_cliente: # Si cancela de nuevo
                return
            cliente = Cliente(nombre_cliente, id_cliente)
            self.admin.add_cliente(cliente) # Registrar nuevo cliente

        # 3. Intentar Realizar la Compra a través del Admin
        try:
            ids_a_comprar = [a.id for a in self.asientos_seleccionados_para_compra]
            tiquetes_comprados = self.admin.comprar_tiquetes(
                self.funcion_seleccionada,
                cliente,
                ids_a_comprar,
                PRECIO_TIQUETE
            )

            # 4. Éxito
            messagebox.showinfo("Compra Exitosa",
                                f"Se compraron {len(tiquetes_comprados)} tiquetes para {cliente.nombre} (ID: {cliente.id}).\n"
                                f"Película: {self.funcion_seleccionada.pelicula.nombre}\n"
                                f"Asientos: {', '.join(ids_a_comprar)}")

            # Limpiar selección y refrescar vista
            self.asientos_seleccionados_para_compra = []
            self._update_purchase_info()
            self._update_seat_display() # ¡Importante para ver asientos ocupados!

        except (ValueError, TypeError) as e:
            # 5. Error durante la compra
            messagebox.showerror("Error en la Compra", f"No se pudo completar la compra:\n{e}")
            # No limpiar selección, el usuario puede intentar corregir


# Nota: Las clases Admin, Funcion, Asiento, etc., y la función main() deben estar
# definidas en el mismo archivo o importadas correctamente para que esto funcione.
# Asegúrate de haber aplicado la corrección de `copy.deepcopy` en `Funcion.__init__`.

def main() -> None:
    """Función principal: Inicializa y ejecuta la aplicación Tkinter."""
    print("Iniciando aplicación Cine...")
    admin = Admin("Cine Cultural Barranquilla")
    admin.cargar_funciones_desde_archivo()
    root = tk.Tk()
    app = TheaterGUI(root, admin) # Crear la instancia de la GUI
    root.mainloop() # Iniciar el bucle de eventos de Tkinter
    print("Aplicación Cine cerrada.")

# Punto de entrada del script
if __name__ == "__main__":
    main()