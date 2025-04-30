# -*- coding: utf-8 -*-
"""
Cine Cultural Barranquilla - Sistema de Gestión y Reservas

Descripción:
Interfaz gráfica (GUI) para la gestión de un cine, usando ttkbootstrap.
Permite visualizar funciones filtradas por fecha/película/sala, seleccionar
asientos de forma interactiva y simular la compra de tiquetes. Las reservas
se guardan en 'tickets.txt' para persistencia básica entre sesiones.

Desarrollo:
- Python 3.x
- Bibliotecas requeridas:
  pip install Pillow ttkbootstrap tkcalendar
- Archivos necesarios (mismo directorio):
  - movies.txt: Datos de funciones (Formato: DD/MM/YYYY - HH:MM;Película;Género;Sala)
  - tickets.txt: (Se crea automáticamente) Guarda las reservas.
  - seat_available.png: Imagen asiento disponible (40x40, fondo opaco #FFFFFF recomendado)
  - seat_occupied.png: Imagen asiento ocupado (40x40, fondo opaco #FFFFFF recomendado)
  - seat_selected.png: Imagen asiento seleccionado (40x40, fondo opaco #FFFFFF recomendado)

Autor: [Tu Nombre/Alias] - Adaptado por Asistente AI
Fecha: 2025-04-30 
"""

import tkinter as tk
# MODIFICADO: Usar ttkbootstrap en lugar de tkinter.ttk
import ttkbootstrap as ttk # <--- CORRECTO
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Tuple
from PIL import Image, ImageTk  # Necesita Pillow
#from tkcalendar import DateEntry # <-- ¡ESTA ES LA LÍNEA! 
import copy
import os 

# --- Constantes ---
APP_TITLE = "Cine Cultural Barranquilla - Taquilla"
WINDOW_GEOMETRY = "1280x768"
COLOR_FONDO_ASIENTOS = '#FFFFFF' # Blanco, para coincidir con tema 'flatly' y fondo de imagen opaco

# Archivos de datos
MOVIE_DATA_FILE = 'movies.txt'
TICKET_DATA_FILE = 'tickets.txt' # Archivo separado para persistencia

# Configuración Teatro/Asientos
DEFAULT_SEATS_PER_THEATER = 80
DEFAULT_THEATER_NAMES = ['Sala 1', 'Sala 2', 'Sala 3']

# Imágenes (Asegúrate que tengan fondo opaco COLOR_FONDO_ASIENTOS)
SEAT_IMG_AVAILABLE = "seat_available.png"
SEAT_IMG_OCCUPIED = "seat_occupied.png"
SEAT_IMG_SELECTED = "seat_selected.png"
SEAT_IMG_WIDTH = 40
SEAT_IMG_HEIGHT = 40

# Otros
PRECIO_TIQUETE = 15000 # Precio base por tiquete (COP)
DATE_FORMAT_FILE = '%d/%m/%Y - %H:%M' # Formato en movies.txt y tickets.txt
DATE_FORMAT_DISPLAY = '%Y-%m-%d %H:%M' # Formato para mostrar en info
DATE_FORMAT_CALENDAR = 'dd/mm/yyyy' # Formato para DateEntry
LOCALE_CALENDAR = 'es_ES' # Español para DateEntry

# --- Clases de Modelo de Datos (Asiento, Teatro, Pelicula, Funcion, Tiquete, Cliente) ---
# (Sin cambios funcionales respecto a tu última versión con correcciones aplicadas)

class Asiento:
    """Representa un único asiento en una sala de cine."""
    def __init__(self, id_asiento: str):
        self.id = id_asiento
        self.disponible = True

    def está_disponible(self) -> bool:
        return self.disponible

    def reservar(self) -> None:
        if not self.disponible:
            print(f"Advertencia: Intento de reservar asiento {self.id} ya ocupado.")
        self.disponible = False

    def desreservar(self) -> None:
        self.disponible = True

    def __str__(self) -> str:
        return f"Asiento({self.id}, {'Disp' if self.disponible else 'Ocup'})"

    def __repr__(self) -> str:
        return f"Asiento(id='{self.id}')"

class Teatro:
    """Representa una plantilla de sala de cine física con sus asientos."""
    def __init__(self, nombre: str, cantidad_asientos: int = DEFAULT_SEATS_PER_THEATER):
        self.nombre = nombre
        self.asientos: List[Asiento] = self._generar_asientos(cantidad_asientos)

    def _generar_asientos(self, cantidad: int) -> List[Asiento]:
        """Genera la lista inicial de objetos Asiento."""
        # Nota: La generación de ID aquí es básica (A1..J8) y puede no coincidir
        # perfectamente con layouts complejos si cantidad != 80.
        # El layout visual se define en la GUI.
        asientos_generados = []
        filas = "ABCDEFGHIJ"
        asientos_por_fila = cantidad // len(filas) if len(filas) > 0 else cantidad
        if asientos_por_fila == 0 and cantidad > 0: asientos_por_fila = 1

        count = 0
        for fila in filas:
            for num in range(1, asientos_por_fila + 1):
                if count < cantidad:
                    asientos_generados.append(Asiento(f"{fila}{num}"))
                    count += 1
                else: break
            if count >= cantidad: break
        
        # Relleno por si acaso
        while len(asientos_generados) < cantidad:
             asientos_generados.append(Asiento(f"Extra{len(asientos_generados) + 1}"))
        return asientos_generados

    def obtener_asiento_por_id(self, id_asiento: str) -> Optional[Asiento]:
        for asiento in self.asientos:
            if asiento.id == id_asiento: return asiento
        return None

    def reiniciar(self) -> None:
        for asiento in self.asientos: asiento.desreservar()

    def __str__(self) -> str:
        return f"Teatro({self.nombre}, Asientos: {len(self.asientos)})"

class Pelicula:
    """Representa una película con su nombre y género."""
    def __init__(self, nombre: str, genero: str):
        self.nombre = nombre
        self.genero = genero

    def obtener_informacion(self) -> str:
        return f"{self.nombre} ({self.genero})"

    def __str__(self) -> str:
        return self.obtener_informacion()

class Funcion:
    """Representa una proyección específica con su propia copia del estado de asientos."""
    def __init__(self, fecha: datetime, pelicula: Pelicula, teatro_plantilla: Teatro):
        self.pelicula = pelicula
        # --- IMPORTANTE: Copia profunda para estado de asientos independiente ---
        self.teatro_funcion = copy.deepcopy(teatro_plantilla)
        self.fecha = fecha
        # Límite (30 min después del inicio) para permitir/bloquear compras
        self.fechaLimite = fecha + timedelta(minutes=30)

    def obtener_informacion(self) -> str:
        """Devuelve una cadena con los detalles de la función."""
        # Usa teatro_funcion para obtener el nombre correcto de la sala
        return f"{self.pelicula.nombre} en {self.teatro_funcion.nombre} - {self.fecha.strftime(DATE_FORMAT_DISPLAY)}"

    def fechaLimite_pasada(self) -> bool:
        """Verifica si ya pasaron 30 mins desde el inicio de la función."""
        return datetime.now() > self.fechaLimite

    def obtener_asientos_disponibles(self) -> List[Asiento]:
         """Obtiene los asientos disponibles para ESTA función específica."""
         return [a for a in self.teatro_funcion.asientos if a.está_disponible()]

    def obtener_asiento_por_id(self, id_asiento: str) -> Optional[Asiento]:
         """Busca un asiento por ID DENTRO del estado de esta función."""
         for asiento in self.teatro_funcion.asientos:
              if asiento.id == id_asiento: return asiento
         return None

    def esta_disponible_en_fecha(self, tiempoDeReferencia: datetime) -> bool:
        """Verifica si la función aún no ha comenzado respecto a un tiempo dado."""
        return self.fecha >= tiempoDeReferencia

    def __str__(self) -> str:
        return self.obtener_informacion()

class Cliente:
    """Representa a un cliente del cine."""
    def __init__(self, nombre: str, id_cliente: str):
        self.nombre = nombre
        self.id = id_cliente

    def __str__(self) -> str:
        return f"Cliente({self.nombre}, ID: {self.id})"
    
# MODIFICADO: Tiquete ahora guarda el objeto Cliente
class Tiquete:
    """Representa un tiquete o boleto comprado."""
    def __init__(self, precio: float, funcion: Funcion, cliente: Cliente, asiento: Asiento):
        self.precio = precio
        self.funcion = funcion
        self.cliente = cliente # Guarda el objeto Cliente
        self.asiento = asiento

    def obtener_informacion(self) -> str:
        return (
            f"Tiquete para {self.funcion.obtener_informacion()}\n"
            f"Cliente: {self.cliente.nombre} (ID: {self.cliente.id})\n"
            f"Asiento: {self.asiento.id}\n"
            f"Precio: ${self.precio:,.2f} COP" # Formato con comas y decimales
        )

    def __str__(self) -> str:
        return f"Tiquete({self.funcion.pelicula.nombre}, Asiento: {self.asiento.id}, Cliente: {self.cliente.nombre})"


# --- Clases de Lógica y Datos ---

class ControladorDeArchivos:
    """Gestiona la lectura y escritura simple en archivos de texto delimitados por ';'."""
    def __init__(self, ruta: str):
        self.ruta = ruta
        # Verificar si el archivo existe al inicio, crearlo si no (para tickets.txt)
        if not os.path.exists(self.ruta):
            try:
                with open(self.ruta, "w", encoding='utf-8') as f:
                    f.write("") # Crear archivo vacío
                print(f"Archivo '{self.ruta}' no encontrado, se ha creado vacío.")
            except Exception as e:
                print(f"Error: No se pudo crear el archivo '{self.ruta}': {e}")

    def leer(self) -> List[List[str]]:
        """Lee líneas del archivo, divide por ';' y devuelve lista de listas."""
        try:
            with open(self.ruta, "r", encoding='utf-8') as archivo:
                return [linea.strip().split(";")
                        for linea in archivo if linea.strip()]
        except FileNotFoundError:
            # Ya no debería ocurrir si lo creamos en __init__, pero por si acaso.
            print(f"Advertencia: Archivo no encontrado en '{self.ruta}' al leer.")
            return []
        except Exception as e:
            print(f"Error inesperado al leer el archivo '{self.ruta}': {e}")
            return []

    def escribir(self, datos: List[str]) -> None:
        """Añade una línea al final del archivo, uniendo datos con ';'."""
        try:
            # Convertir todos los datos a string antes de unir
            datos_str = [str(d) for d in datos]
            with open(self.ruta, "a", encoding='utf-8') as archivo:
                linea = ';'.join(datos_str) + '\n'
                archivo.write(linea)
        except Exception as e:
            print(f"Error inesperado al escribir en el archivo '{self.ruta}': {e}")

class Admin:
    """Clase principal para la lógica de negocio y gestión de datos del cine."""
    def __init__(self, nombre_cine: str):
        self.nombre = nombre_cine
        self.clientes: List[Cliente] = []
        self.teatros: Dict[str, Teatro] = {
            nombre: Teatro(nombre) for nombre in DEFAULT_THEATER_NAMES
        }
        self.funciones_diarias: Dict[str, List[Funcion]] = {
            nombre: [] for nombre in DEFAULT_THEATER_NAMES
        }
        self.tiquetes: Dict[str, List[Tiquete]] = {} # id_cliente -> Lista de Tiquetes

        self.controlador_funciones = ControladorDeArchivos(MOVIE_DATA_FILE)
        self.controlador_tiquetes = ControladorDeArchivos(TICKET_DATA_FILE)

    def add_cliente(self, cliente: Cliente) -> bool:
        """Añade un nuevo cliente si no existe por ID. Devuelve True si añadido."""
        if not isinstance(cliente, Cliente): return False
        if self.get_cliente(cliente.id): return False # Ya existe
        self.clientes.append(cliente)
        self.tiquetes[cliente.id] = [] # Inicializar lista de tiquetes
        print(f"Cliente '{cliente.nombre}' añadido.")
        return True

    def get_cliente(self, id_cliente: str) -> Optional[Cliente]:
        for cliente in self.clientes:
            if cliente.id == id_cliente: return cliente
        return None

    def asignar_función(self, funcion: Funcion) -> bool:
        """Añade una función cargada a la programación interna."""
        nombre_sala = funcion.teatro_funcion.nombre
        if nombre_sala not in self.funciones_diarias:
            print(f"Error: Sala '{nombre_sala}' desconocida para función {funcion.pelicula.nombre}.")
            return False

        # TODO: Implementar validación de horarios y límite de funciones más robusta.
        # La validación actual de >= 2 es muy simple y se aplicó durante la carga.
        # Aquí simplemente la añadimos a la lista correspondiente.
        self.funciones_diarias[nombre_sala].append(funcion)
        # print(f"Función asignada internamente: {funcion}") # Log menos verboso
        return True

    def cargar_funciones_desde_archivo(self) -> int:
        """Carga funciones desde MOVIE_DATA_FILE. Devuelve número de funciones cargadas."""
        funciones_cargadas_count = 0
        print(f"Cargando funciones desde '{self.controlador_funciones.ruta}'...")
        registros = self.controlador_funciones.leer()

        if not registros:
             print("No se encontraron funciones en el archivo.")
             return 0

        # Limpiar programación anterior antes de cargar
        for sala in self.funciones_diarias:
            self.funciones_diarias[sala] = []

        funciones_por_sala_contador = {sala: 0 for sala in DEFAULT_THEATER_NAMES}

        for i, registro in enumerate(registros):
            if len(registro) >= 4:
                fecha_str, nombre_peli, genero, nombre_sala = registro[:4]
                try:
                    fecha = datetime.strptime(fecha_str.strip(), DATE_FORMAT_FILE)
                    nombre_sala = nombre_sala.strip()
                    teatro_plantilla = self.teatros.get(nombre_sala)

                    if teatro_plantilla is None:
                        raise ValueError(f"Teatro '{nombre_sala}' inválido")

                    # --- Aplicar límite de 2 funciones por sala aquí ---
                    if funciones_por_sala_contador[nombre_sala] >= 2:
                         print(f"Advertencia L.{i+1}: Límite de 2 funciones alcanzado para {nombre_sala}. Se ignora '{nombre_peli}'.")
                         continue # Saltar a la siguiente línea del archivo

                    pelicula = Pelicula(nombre_peli.strip(), genero.strip())
                    funcion = Funcion(fecha, pelicula, teatro_plantilla)

                    # Añadir directamente a la lista (validación de límite ya hecha)
                    self.funciones_diarias[nombre_sala].append(funcion)
                    funciones_por_sala_contador[nombre_sala] += 1
                    funciones_cargadas_count += 1

                except ValueError as e:
                    print(f"Error procesando L.{i+1} archivo funciones: {e} - Registro: {registro}")
                except Exception as e:
                    print(f"Error inesperado L.{i+1} archivo funciones: {registro} -> {e}")
            else:
                print(f"Adv. L.{i+1} archivo funciones: Formato incorrecto: {registro}")

        print(f"Se cargaron {funciones_cargadas_count} funciones.")
        return funciones_cargadas_count

    # MODIFICADO: Acepta objeto Cliente
    def comprar_tiquetes(self, funcion: Funcion, cliente: Cliente, ids_asientos: List[str], precio_unitario: float) -> List[Tiquete]:
        if not isinstance(funcion, Funcion) or not isinstance(cliente, Cliente):
            raise TypeError("Argumentos 'funcion' y 'cliente' inválidos.")
        if not ids_asientos:
             raise ValueError("Se debe seleccionar al menos un asiento.")

        tiquetes_comprados = []
        asientos_a_reservar = []

        # 1. Verificar disponibilidad en la copia de la función
        for asiento_id in ids_asientos:
            asiento = funcion.obtener_asiento_por_id(asiento_id)
            if asiento is None:
                raise ValueError(f"Asiento ID '{asiento_id}' no existe en sala '{funcion.teatro_funcion.nombre}'.")
            if not asiento.está_disponible():
                raise ValueError(f"Asiento {asiento_id} no disponible para esta función.")
            asientos_a_reservar.append(asiento)

        # 2. Reservar y crear Tiquetes (ahora pasando objeto Cliente)
        try:
            for asiento in asientos_a_reservar:
                asiento.reservar() # Modifica la copia de la función
                # --- CORREGIDO: Pasar objeto cliente ---
                tiquete = Tiquete(precio_unitario, funcion, cliente, asiento)
                tiquetes_comprados.append(tiquete)

                # Añadir tiquete a la lista del cliente en memoria
                if cliente.id not in self.tiquetes: self.tiquetes[cliente.id] = []
                self.tiquetes[cliente.id].append(tiquete)

                # Guardar registro simple en tickets.txt
                self.guardar_tiquete_en_archivo(tiquete)

            print(f"Compra exitosa para {cliente.nombre}: {len(tiquetes_comprados)} tiquetes.")
            return tiquetes_comprados
        except Exception as e:
            print(f"Error durante la compra, revirtiendo reservas: {e}")
            for asiento in asientos_a_reservar:
                 if not asiento.está_disponible(): asiento.desreservar() # Revertir en la copia
            # Re-lanzar como ValueError para que la GUI lo capture
            raise ValueError(f"Error al procesar la compra: {e}")

    def get_funciones_disponibles_por_fecha(self, fecha: datetime, incluir_pasadas_hoy: bool = False) -> List[Funcion]:
        """Obtiene funciones para una fecha, opcionalmente filtrando pasadas de hoy."""
        tiempo_referencia: datetime
        hoy = datetime.now().date()

        if fecha.date() == hoy and not incluir_pasadas_hoy:
            tiempo_referencia = datetime.now()
        else:
            tiempo_referencia = fecha.replace(hour=0, minute=0, second=0, microsecond=0)

        funciones_del_dia: List[Funcion] = []
        for lista_funciones in self.funciones_diarias.values():
            for funcion in lista_funciones:
                if funcion.fecha.date() == fecha.date():
                    if funcion.esta_disponible_en_fecha(tiempo_referencia):
                        funciones_del_dia.append(funcion)
        return sorted(funciones_del_dia, key=lambda f: f.fecha)

    # MODIFICADO: guardar_tiquete_en_archivo (Versión simple para persistencia de reserva)
    def guardar_tiquete_en_archivo(self, tiquete: Tiquete) -> None:
        """
        Guarda la información ESENCIAL de un tiquete (para restaurar estado)
        en el archivo TICKET_DATA_FILE.
        Formato: FechaFuncion;NombreSala;NombrePelicula;IDAsiento
        """
        try:
            # Guardar solo lo necesario para identificar la reserva al reiniciar
            tiquete_data_simple = [
                tiquete.funcion.fecha.strftime(DATE_FORMAT_FILE), # Usar formato consistente
                tiquete.funcion.teatro_funcion.nombre,
                tiquete.funcion.pelicula.nombre,
                tiquete.asiento.id,
                # Podríamos añadir cliente ID aquí si quisiéramos reconstruir Tiquetes al cargar
                # tiquete.cliente.id
            ]
            self.controlador_tiquetes.escribir(tiquete_data_simple)
        except Exception as e:
            print(f"Error al intentar guardar tiquete simple en '{TICKET_DATA_FILE}': {e}")

    # RENOMBRADO y LÓGICA AJUSTADA: Carga y aplica reservas
    def _cargar_y_aplicar_reservas(self) -> None:
        """
        Lee tickets.txt y marca asientos como ocupados en las funciones en memoria.
        """
        print(f"Cargando y aplicando reservas desde '{TICKET_DATA_FILE}'...")
        reservas_guardadas = self.controlador_tiquetes.leer()
        reservas_aplicadas = 0
        funciones_map = {} # Cache: (fecha_dt, sala_str, peli_str) -> Funcion

        # Crear mapa para búsqueda rápida
        for lista_funciones in self.funciones_diarias.values():
            for func in lista_funciones:
                key = (func.fecha, func.teatro_funcion.nombre, func.pelicula.nombre)
                funciones_map[key] = func

        if not reservas_guardadas:
            print("No hay reservas guardadas para aplicar.")
            return

        for i, record in enumerate(reservas_guardadas):
            # El formato guardado ahora tiene 4 campos esenciales
            if len(record) >= 4:
                fecha_str, nombre_sala, nombre_peli, asiento_id = record[:4]
                try:
                    fecha_dt = datetime.strptime(fecha_str.strip(), DATE_FORMAT_FILE)
                    nombre_sala = nombre_sala.strip()
                    nombre_peli = nombre_peli.strip()
                    asiento_id = asiento_id.strip()

                    key_busqueda = (fecha_dt, nombre_sala, nombre_peli)
                    funcion_encontrada = funciones_map.get(key_busqueda)

                    if funcion_encontrada:
                        asiento = funcion_encontrada.obtener_asiento_por_id(asiento_id)
                        if asiento and asiento.está_disponible():
                            asiento.reservar()
                            reservas_aplicadas += 1
                        # else: Asiento no existe o ya estaba ocupado, ignorar línea
                    # else: Función no encontrada, ignorar línea

                except ValueError as e:
                    print(f"Error parse Tkt L.{i+1}: {record} -> {e}")
                except Exception as e:
                    print(f"Error inesperado Tkt L.{i+1}: {record} -> {e}")
            else:
                print(f"Adv Tkt L.{i+1}: Formato incorrecto: {record}")

        print(f"Se aplicaron {reservas_aplicadas} reservas desde archivo.")


# --- Clase de Interfaz Gráfica (TheaterGUI) ---

class TheaterGUI:
    """Interfaz gráfica principal usando ttkbootstrap."""

    def __init__(self, root: tk.Tk, admin_instance: Admin):
        """Inicializa la GUI con ttkbootstrap."""
        self.root = root
        self.admin = admin_instance
        self.funcion_seleccionada: Optional[Funcion] = None
        self.asientos_seleccionados_para_compra: List[Asiento] = []
        self.mapa_widgets_asientos: Dict[str, tk.Button] = {} # Ahora tk.Button

        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_GEOMETRY)

        # Variables para filtros
        self.movie_filter_var = tk.StringVar(value="Todas")
        self.sala_filter_var = tk.StringVar(value="Todas")

        # Carga de imágenes (mantener fondo opaco #FFFFFF recomendado)
        self._cargar_imagenes_asientos()

        # Configuración de layout y widgets (ahora usa ttk)
        self._setup_gui_layout()

        # Carga inicial de funciones para hoy
        self._on_filter_apply()

    def _cargar_imagenes_asientos(self) -> None:
        """Carga y prepara las imágenes de los asientos."""
        # (Asumiendo que las imágenes ya tienen fondo opaco blanco #FFFFFF)
        try:
            pil_avail = Image.open(SEAT_IMG_AVAILABLE).resize((SEAT_IMG_WIDTH, SEAT_IMG_HEIGHT), Image.Resampling.LANCZOS)
            pil_occup = Image.open(SEAT_IMG_OCCUPIED).resize((SEAT_IMG_WIDTH, SEAT_IMG_HEIGHT), Image.Resampling.LANCZOS)
            pil_select = Image.open(SEAT_IMG_SELECTED).resize((SEAT_IMG_WIDTH, SEAT_IMG_HEIGHT), Image.Resampling.LANCZOS)
            self.img_available = ImageTk.PhotoImage(pil_avail)
            self.img_occupied = ImageTk.PhotoImage(pil_occup)
            self.img_selected = ImageTk.PhotoImage(pil_select)
            print("Imágenes de asientos cargadas.")
        except FileNotFoundError as e:
            print(f"ERROR CRÍTICO: Falta archivo de imagen '{e.filename}'. Se usará fallback.")
            messagebox.showerror("Error de Imagen", f"No se encontró la imagen: {e.filename}")
            self.img_available = self.img_occupied = self.img_selected = None
        except Exception as e:
            print(f"Error inesperado cargando imágenes: {e}")
            messagebox.showerror("Error de Imagen", f"Error al cargar imágenes: {e}")
            self.img_available = self.img_occupied = self.img_selected = None

    def _setup_gui_layout(self) -> None:
        """Configura la estructura de widgets usando ttkbootstrap."""
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Frame Superior (Filtros) - Usar ttk.Frame
        filter_frame = ttk.Frame(self.root, padding="10")
        filter_frame.grid(row=0, column=0, sticky='ew')

        # Filtro de Fecha (DateEntry) - Quitar colores manuales
        ttk.Label(filter_frame, text="Fecha:").pack(side='left', padx=(0, 5))
        date_format_widget = DATE_FORMAT_FILE.split(' ')[0].replace('%d','dd').replace('%m','mm').replace('%Y','yyyy')
        date_format_python = DATE_FORMAT_FILE.split(' ')[0] 

        self.date_entry_widget = ttk.DateEntry(
                filter_frame,
                # bootstyle=INFO, # Estilo opcional bootstrap
                firstweekday=0, # 0 para Lunes
                # Usar dateformat con códigos strftime que ttkbootstrap/tkcalendar entienden
                # Convertimos desde tu constante DATE_FORMAT_FILE
                dateformat=date_format_widget, 
                # locale no se soporta directamente
                width=12 
            )
        self.date_entry_widget.pack(side='left', padx=5)
        #self.date_entry_widget.entry.insert(0, datetime.now().strftime(DATE_FORMAT_FILE.split(' ')[0])) 

        try:
            # Limpiar por si acaso el widget puso algo por defecto
            self.date_entry_widget.entry.delete(0, tk.END) 
            # Insertar fecha actual usando formato Python
            self.date_entry_widget.entry.insert(0, datetime.now().strftime(date_format_python)) 
        except Exception as e:
            print(f"Error al insertar fecha inicial en DateEntry: {e}")

        # Filtro de Película (ttk.Combobox)
        ttk.Label(filter_frame, text="Película:").pack(side='left', padx=(15, 5))
        self.movie_combobox = ttk.Combobox(filter_frame, textvariable=self.movie_filter_var,
                                           state='disabled', width=30) # Inicia deshabilitado
        self.movie_combobox['values'] = ["Todas"]
        self.movie_combobox.current(0)
        self.movie_combobox.pack(side='left', padx=5)

        # Filtro de Sala (ttk.Combobox)
        ttk.Label(filter_frame, text="Sala:").pack(side='left', padx=(15, 5))
        self.sala_combobox = ttk.Combobox(filter_frame, textvariable=self.sala_filter_var,
                                          state='readonly', width=15)
        self.sala_combobox['values'] = ["Todas"] + DEFAULT_THEATER_NAMES
        self.sala_combobox.current(0)
        self.sala_combobox.pack(side='left', padx=5)

        # Botón Aplicar Filtros (ttk.Button)
        apply_button = ttk.Button(filter_frame, text="Aplicar Filtros",
                                  command=self._on_filter_apply, bootstyle=PRIMARY) # Estilo bootstrap
        apply_button.pack(side='left', padx=15)

        # Frame Principal (PanedWindow) - Usar ttk.PanedWindow
        main_pane = ttk.PanedWindow(self.root, orient='horizontal')
        main_pane.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)

        # Frame Izquierdo (Funciones) - Usar ttk.Frame
        functions_frame = ttk.Frame(main_pane, padding="5")
        main_pane.add(functions_frame, weight=1)
        ttk.Label(functions_frame, text="Funciones Disponibles", font="-weight bold").pack(pady=5) # Fuente bold

        # Treeview (ya es ttk)
        cols = ('pelicula', 'hora', 'sala')
        self.functions_treeview = ttk.Treeview(functions_frame, columns=cols, show='headings', height=15, bootstyle=INFO) # Estilo tabla
        # ... (configuración headings/columns igual) ...
        self.functions_treeview.heading('pelicula', text='Película')
        self.functions_treeview.heading('hora', text='Hora')
        self.functions_treeview.heading('sala', text='Sala')
        self.functions_treeview.column('pelicula', width=200, anchor='w') # Alinear a la izquierda
        self.functions_treeview.column('hora', width=80, anchor='center')
        self.functions_treeview.column('sala', width=100, anchor='center')
        scrollbar = ttk.Scrollbar(functions_frame, orient='vertical', command=self.functions_treeview.yview, bootstyle=ROUND) # Scrollbar redondeado
        self.functions_treeview.configure(yscrollcommand=scrollbar.set)
        self.functions_treeview.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        self.functions_treeview.bind('<<TreeviewSelect>>', self._on_function_select)

        # Frame Derecho (Asientos) - Usar ttk.Frame
        self.seat_area_frame = ttk.Frame(main_pane, padding="5")
        main_pane.add(self.seat_area_frame, weight=3)

        # Frame Inferior (Compra) - Usar ttk.Frame
        purchase_status_frame = ttk.Frame(self.root, padding="5 10 5 10")
        purchase_status_frame.grid(row=2, column=0, sticky='ew')
        self.purchase_info_label = ttk.Label(purchase_status_frame, text="Seleccione función y asientos.", anchor='w')
        self.purchase_info_label.pack(side='left', fill='x', expand=True, padx=5)
        buy_button = ttk.Button(purchase_status_frame, text="Comprar Entradas",
                                command=self._confirm_purchase, bootstyle=SUCCESS) # Botón verde
        buy_button.pack(side='right', padx=5)


    def _on_filter_apply(self) -> None:
        """Obtiene todos los filtros, busca funciones en Admin y actualiza la GUI."""
        try:
            # --- 1. Obtener Fecha y Convertir ---
            date_str = self.date_entry_widget.entry.get()
            # Usar solo la parte de fecha del formato para parsear la entrada
            date_format_str = DATE_FORMAT_FILE.split(' ')[0] # Ej: '%d/%m/%Y' -> 'dd/mm/yyyy'
            # Asegurarse que el formato de parseo coincida con DATE_FORMAT_FILE
            date_format_parse = '%d/%m/%Y' # Asumiendo que DATE_FORMAT_FILE usa este orden
            
            selected_date_obj = datetime.strptime(date_str, date_format_parse).date()
            selected_datetime = datetime.combine(selected_date_obj, datetime.min.time())
            print(f"Filtrando funciones para: {selected_datetime.strftime('%Y-%m-%d')}")

            # --- 2. Obtener Filtros de Combobox ---
            movie_filter = self.movie_filter_var.get()
            sala_filter = self.sala_filter_var.get()
            print(f"Filtros aplicados - Película: '{movie_filter}', Sala: '{sala_filter}'")

            # --- 3. Obtener TODAS las funciones para la fecha desde Admin ---
            todas_funciones_dia = self.admin.get_funciones_disponibles_por_fecha(
                selected_datetime, 
                incluir_pasadas_hoy=False # No mostrar funciones que ya empezaron hoy
            )

            # --- 4. Actualizar Combobox de Películas ---
            # Obtener nombres únicos de películas de las funciones de ESE DÍA
            if todas_funciones_dia:
                 nombres_peliculas = sorted(list(set(f.pelicula.nombre for f in todas_funciones_dia)))
                 current_movie_selection = self.movie_filter_var.get() # Guardar selección actual
                 self.movie_combobox['values'] = ["Todas"] + nombres_peliculas
                 self.movie_combobox.config(state='readonly') # Habilitar
                 # Intentar restaurar selección anterior si aún es válida
                 if current_movie_selection in self.movie_combobox['values']:
                     self.movie_filter_var.set(current_movie_selection)
                 else:
                     self.movie_filter_var.set("Todas") # Resetear si no es válida
                     movie_filter = "Todas" # Actualizar filtro local si se reseteó
            else:
                 # No hay funciones, deshabilitar y resetear combobox de películas
                 self.movie_combobox['values'] = ["Todas"]
                 self.movie_combobox.config(state='disabled')
                 self.movie_filter_var.set("Todas")
                 movie_filter = "Todas"

            # --- 5. Filtrar Funciones en la GUI ---
            filtered_functions = todas_funciones_dia
            if movie_filter != "Todas":
                filtered_functions = [f for f in filtered_functions if f.pelicula.nombre == movie_filter]
            if sala_filter != "Todas":
                filtered_functions = [f for f in filtered_functions if f.teatro_funcion.nombre == sala_filter]

            # --- 6. Limpiar Vistas y Estado Actual ---
            for item in self.functions_treeview.get_children():
                self.functions_treeview.delete(item)
            self._clear_seat_display() # Limpiar área de asientos
            self.funcion_seleccionada = None # Deseleccionar función
            self.asientos_seleccionados_para_compra = [] # Limpiar asientos seleccionados
            self._update_purchase_info() # Resetear etiqueta de compra

            # --- 7. Poblar Treeview con Resultados Filtrados ---
            self.function_map = {} # Resetear mapa de iid -> funcion
            if filtered_functions:
                for func in filtered_functions:
                    # Insertar en Treeview
                    iid = self.functions_treeview.insert('', 'end', values=(
                        func.pelicula.nombre,
                        func.fecha.strftime('%H:%M'), # Solo hora
                        func.teatro_funcion.nombre
                    ))
                    # Guardar mapeo para selección posterior
                    self.function_map[iid] = func
                print(f"Mostrando {len(filtered_functions)} funciones filtradas.")
            else:
                # Mostrar mensaje si no hay resultados
                self.functions_treeview.insert('', 'end', values=("No hay funciones", "con estos filtros", ""))
                print("No se encontraron funciones con los filtros aplicados.")

        except ValueError as e:
            # Error específico al parsear la fecha
            messagebox.showerror("Error de Fecha", f"Formato de fecha inválido en la caja: '{date_str}'. Use dd/mm/yyyy.\n({e})")
            # Podrías limpiar solo el treeview, o todo
            for item in self.functions_treeview.get_children(): self.functions_treeview.delete(item)
            self._clear_seat_display()
        except Exception as e:
            # Otros errores inesperados
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al aplicar filtros: {e}")
            self._clear_seat_display()

    def _clear_seat_display(self) -> None:
        """Limpia el área de asientos y muestra mensaje."""
        for widget in self.seat_area_frame.winfo_children(): widget.destroy()
        ttk.Label(self.seat_area_frame, text="Seleccione una función para ver los asientos.").pack(padx=20, pady=50)


    def _update_seat_display(self) -> None:
        """Limpia y redibuja pantalla y asientos para la función actual."""
        for widget in self.seat_area_frame.winfo_children(): widget.destroy()
        if not self.funcion_seleccionada:
            self._clear_seat_display(); return

        # Dibujar Pantalla (usando estilo ttk)
        screen_frame = ttk.Frame(self.seat_area_frame, style='Black.TFrame', height=20)
        # Nota: La configuración de estilo 'Black.TFrame' debería estar en __init__
        # self.style.configure('Black.TFrame', background='black') # Mover a __init__ si no está
        screen_frame.pack(side='bottom', fill='x', padx=50, pady=(10, 20))
        ttk.Label(screen_frame, text="PANTALLA", style='Inverse-light.TLabel').pack(pady=2) # Estilo ttkbootstrap para texto claro sobre fondo oscuro

        # Dibujar Asientos
        self.mostrar_asientos(self.seat_area_frame, self.funcion_seleccionada)

    def _on_function_select(self, event=None) -> None:
        """
        Manejador de evento cuando se selecciona una función en el Treeview.
        Actualiza la función seleccionada y muestra sus asientos.

        Args:
            event: El objeto de evento (opcional, proporcionado por bind).
        """
        selected_items = self.functions_treeview.selection() # Obtiene los IDs de items seleccionados

        # Verificar si algo está seleccionado
        if not selected_items:
            self.funcion_seleccionada = None
            self._clear_seat_display() # Limpiar vista de asientos si no hay selección
            self._update_purchase_info() # Resetear info de compra
            return

        # Obtener el ID del primer item seleccionado
        selected_iid = selected_items[0]

        # Recuperar el objeto Funcion completo usando el mapa que poblamos antes
        # (self.function_map se llena en _on_filter_apply)
        selected_function = self.function_map.get(selected_iid)

        if selected_function:
            # Guardar la función seleccionada
            self.funcion_seleccionada = selected_function
            print(f"Función seleccionada: {self.funcion_seleccionada}")

            # Resetear la selección de asientos para esta nueva función
            self.asientos_seleccionados_para_compra = []

            # Actualizar la vista para mostrar los asientos de esta función
            self._update_seat_display()

            # Actualizar la info de compra (costo volverá a 0)
            self._update_purchase_info()
        else:
            # Esto no debería pasar si function_map está correcto, pero por si acaso:
            print(f"Error: No se encontró el objeto Funcion para el item ID {selected_iid}")
            self.funcion_seleccionada = None
            self._clear_seat_display()
            self._update_purchase_info()

    # MODIFICADO: Para usar tk.Button y fondo explícito
    def mostrar_asientos(self, parent_frame: ttk.Frame, funcion: Funcion) -> None:
        """Dibuja la cuadrícula de asientos usando tk.Button y fondo explícito."""
        seats_layout = [11]*2 + [9]*2 + [7]*5 + [5]*1
        num_rows = len(seats_layout)
        max_seats_in_row = 11
        num_grid_cols = 1 + max_seats_in_row + 1

        self.mapa_widgets_asientos = {}

        # Usar tk.Frame para asegurar el color de fondo #FFFFFF
        grid_frame = tk.Frame(parent_frame, bg=COLOR_FONDO_ASIENTOS)
        grid_frame.pack(side='top', expand=True, pady=(20, 10))

        asiento_index = 0
        asientos_de_la_funcion = funcion.teatro_funcion.asientos

        for i in range(num_rows):
            num_seats_this_row = seats_layout[i]
            indent = (max_seats_in_row - num_seats_this_row) // 2
            start_col = 1 + indent
            end_col = start_col + num_seats_this_row - 1

            for j in range(num_grid_cols):
                widget_to_place = None
                is_button = False

                # Pasillos / Vacíos (usar tk.Frame)
                if j == 0 or j == num_grid_cols - 1 or not (start_col <= j <= end_col):
                    widget_to_place = tk.Frame(grid_frame, width=SEAT_IMG_WIDTH+5, height=SEAT_IMG_HEIGHT+5, bg=COLOR_FONDO_ASIENTOS)
                    if j == 0 or j == num_grid_cols - 1: # Hacer pasillos más angostos
                        widget_to_place.config(width=30)

                # Asientos (usar tk.Button)
                elif start_col <= j <= end_col:
                    if asiento_index < len(asientos_de_la_funcion):
                        asiento = asientos_de_la_funcion[asiento_index]
                        is_available = asiento.está_disponible()
                        is_selected = asiento in self.asientos_seleccionados_para_compra

                        img = None
                        if is_selected and self.img_selected: img = self.img_selected
                        elif not is_available and self.img_occupied: img = self.img_occupied
                        elif is_available and self.img_available: img = self.img_available

                        if img:
                            # --- Usar tk.Button para control de fondo ---
                            seat_btn = tk.Button(grid_frame, image=img,
                                                 bg=COLOR_FONDO_ASIENTOS, # Fondo explícito
                                                 borderwidth=0, highlightthickness=0, relief='flat',
                                                 activebackground=COLOR_FONDO_ASIENTOS)
                            seat_btn.image = img
                        else: # Fallback
                            fb_text = asiento.id
                            if is_selected: fb_text = f"[{asiento.id}]"
                            color = "red" if not is_available else "green"
                            if is_selected: color = "gold"
                            seat_btn = tk.Button(grid_frame, text=fb_text, fg="white", bg=color,
                                                 width=5, height=2, borderwidth=0, relief='flat', activebackground=color)

                        if seat_btn: # Si se creó botón (no error de índice)
                            seat_btn.config(command=lambda a=asiento, b=seat_btn: self.on_seat_click(a, b))
                            self.mapa_widgets_asientos[asiento.id] = seat_btn

                        widget_to_place = seat_btn
                        is_button = True
                        asiento_index += 1
                    else: # Error de índice
                         print(f"Error Layout: Índice {asiento_index} fuera de rango.")
                         widget_to_place = tk.Frame(grid_frame, width=SEAT_IMG_WIDTH+5, height=SEAT_IMG_HEIGHT+5, bg="magenta")

                # Colocar widget
                if widget_to_place:
                    widget_to_place.grid(row=i, column=j, padx=1, pady=1) # Padding reducido
                    if isinstance(widget_to_place, tk.Frame):
                         widget_to_place.pack_propagate(False)


    # MODIFICADO: Ajustar type hint si se usa tk.Button
    def on_seat_click(self, asiento: Asiento, button: tk.Button) -> None: # Cambiado a tk.Button
        """Manejador de clic en asiento para selección/deselección."""
        # (Lógica interna no cambia, ya actualiza la imagen manualmente)
        if not self.funcion_seleccionada:
            messagebox.showwarning("Selección Requerida", "Por favor, seleccione primero una función.")
            return
        if self.funcion_seleccionada.fechaLimite_pasada():
             messagebox.showwarning("Tiempo Excedido", "El tiempo para comprar/seleccionar ha expirado.")
             return

        if asiento.está_disponible():
            if asiento in self.asientos_seleccionados_para_compra: # Deseleccionar
                self.asientos_seleccionados_para_compra.remove(asiento)
                img_actualizar = self.img_available
                fb_text = asiento.id
            else: # Seleccionar
                self.asientos_seleccionados_para_compra.append(asiento)
                img_actualizar = self.img_selected
                fb_text = f"[{asiento.id}]"
            
            # Actualizar apariencia del botón
            if img_actualizar:
                 button.config(image=img_actualizar)
                 button.image = img_actualizar # Actualizar referencia
            else: # Fallback
                 button.config(text=fb_text)
                 # Reajustar color de fallback si es necesario
        
        else: # Asiento ocupado (ya comprado)
             if asiento not in self.asientos_seleccionados_para_compra:
                 messagebox.showinfo("Asiento Ocupado", f"El asiento {asiento.id} ya está ocupado.")

        self._update_purchase_info()


    def _update_purchase_info(self) -> None:
        """Actualiza etiqueta de información de compra."""
        # (Sin cambios funcionales necesarios aquí)
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
        # (Sin cambios funcionales necesarios aquí, ya usa Admin y dialogs)
        # ... (Validaciones: funcion_seleccionada, asientos_seleccionados, fechaLimite) ...
        if not self.funcion_seleccionada or not self.asientos_seleccionados_para_compra or self.funcion_seleccionada.fechaLimite_pasada():
             # Mostrar mensajes apropiados (ya implementado)
             return

        # ... (Obtener Cliente: simpledialog, get_cliente, add_cliente) ...
        id_cliente = simpledialog.askstring("Identificación Cliente", "Ingrese el ID (cédula) del cliente:", parent=self.root)
        if not id_cliente: return
        cliente = self.admin.get_cliente(id_cliente)
        if not cliente:
            nombre_cliente = simpledialog.askstring("Nombre Cliente Nuevo", f"Cliente ID {id_cliente} no encontrado.\nIngrese nombre:", parent=self.root)
            if not nombre_cliente: return
            cliente = Cliente(nombre_cliente, id_cliente)
            self.admin.add_cliente(cliente)

        # ... (Llamar a Admin.comprar_tiquetes) ...
        try:
            ids_a_comprar = [a.id for a in self.asientos_seleccionados_para_compra]
            tiquetes = self.admin.comprar_tiquetes(self.funcion_seleccionada, cliente, ids_a_comprar, PRECIO_TIQUETE)
            
            # ... (Éxito: messagebox, limpiar selección, actualizar GUI) ...
            messagebox.showinfo("Compra Exitosa", f"Compra realizada para {cliente.nombre} (ID: {cliente.id}).\nAsientos: {', '.join(ids_a_comprar)}")
            self.asientos_seleccionados_para_compra = []
            self._update_purchase_info()
            self._update_seat_display() # Refrescar asientos

        except (ValueError, TypeError) as e:
            # ... (Error: messagebox) ...
             messagebox.showerror("Error en Compra", f"No se pudo completar:\n{e}")


# --- Función Principal ---

def main() -> None:
    """Inicializa Admin, carga datos, aplica tema y ejecuta la GUI."""
    print("Iniciando aplicación Cine...")
    admin = Admin("Cine Cultural Barranquilla")
    admin.cargar_funciones_desde_archivo()
    admin._cargar_y_aplicar_reservas() # Cargar estado persistente

    # MODIFICADO: Inicializar con ttkbootstrap y tema 'flatly'
    # Usar ttk.Window en lugar de tk.Tk puede ser mejor para bootstrap
    # root = tk.Tk() 
    root = ttk.Window(themename="flatly") # Crea ventana raíz con tema

    # Ya no es necesario llamar a style.theme_use() explícitamente aquí

    app = TheaterGUI(root, admin)
    root.mainloop()
    print("Aplicación Cine cerrada.")

# --- Punto de Entrada ---
if __name__ == "__main__":
    main()