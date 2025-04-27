import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from PIL import Image, ImageTk

class Asiento:
    def __init__(self, id: str):
        self.id = id
        self.disponible = True

    def está_disponible(self) -> bool:
        return self.disponible

    def reservar(self) -> None:
        if not self.disponible:
            raise ValueError(f"El asiento {self.id} no está disponible")
        self.disponible = False

    def desreservar(self) -> None:
        self.disponible = True

class Teatro:
    def __init__(self, nombre: str, cantidad_asientos: int = 80) -> None:
        self.nombre = nombre
        self.asientos: List[Asiento] = []

        # Asientos con ID: A1, A2, ..., J8
        filas = "ABCDEFGHIJ"
        asientos_por_fila = cantidad_asientos // len(filas)
        for fila in filas:
            for num in range(1, asientos_por_fila + 1):
                asiento_id = f"{fila}{num}"
                self.asientos.append(Asiento(asiento_id))

    def obtener_asientos_disponibles(self) -> List[Asiento]:
        return [asiento for asiento in self.asientos if asiento.está_disponible()]

    def reiniciar(self) -> None:
        for asiento in self.asientos:
            asiento.desreservar()

class Película:
    def __init__(self, nombre: str, género: str) -> None:
        self.nombre = nombre
        self.género = género

    def obtener_información(self) -> str:
        return f"{self.nombre} ({self.género})"

class Función:
    def __init__(self, fecha: datetime, película: Película, teatro: Teatro):
        self.película = película
        self.teatro = teatro
        self.fecha = fecha
        self.fechaLimite = fecha + timedelta(minutes=30)

    def obtener_información(self) -> str:
        return f"{self.película.nombre} en {self.teatro.nombre} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"

    def reiniciar(self) -> None:
        self.teatro.reiniciar()

    def fechaLimite_pasada(self) -> bool:
        return datetime.now() > self.fechaLimite

    def obtener_asientos_disponibles(self):
        return self.teatro.obtener_asientos_disponibles()

    def está_disponible(self, tiempoDeReferencia: datetime) -> bool:
        return self.fecha >= tiempoDeReferencia

class Tiquete:
    def __init__(self, precio: float, función: Función, nombre_cliente: str, asiento: Asiento):
        self.precio = precio
        self.función = función
        self.nombre_cliente = nombre_cliente
        self.asiento = asiento

    def obtener_información(self) -> str:
        return (
            f"Tiquete para {self.función.obtener_información()}\n"
            f"Nombre del cliente: {self.nombre_cliente}\n"
            f"Asiento: {self.asiento.id}\n"
            f"Precio: ${self.precio:.2f}"
        )

class Cliente:
    def __init__(self, nombre: str, id: str):
        self.nombre = nombre
        self.id = id

class ControladorDeArchivos:
    def __init__(self, ruta: str):
        self.ruta = ruta

    def leer(self) -> list[list[str]]:
        try:
            with open(self.ruta, "r", encoding='utf-8') as archivo:
                return [linea.strip().split(",") for linea in archivo if linea.strip()]
        except FileNotFoundError:
            return []

    def escribir(self, datos: list[str]) -> None:
        with open(self.ruta, "a", encoding='utf-8') as archivo:
            linea = ';'.join(datos) + '\n'
            archivo.write(linea)

    def filtrar(self, criterio: str) -> list[list[str]]:
        return [registro for registro in self.leer() if any(criterio in campo for campo in registro)]

class Admin:
    def __init__(self, nombre: str):
        self.nombre = nombre
        self.clientes: List[Cliente] = []
        self.teatros: Dict[str, Teatro] = {
            'Sala 1': Teatro('Sala 1'),
            'Sala 2': Teatro('Sala 2'),
            'Sala 3': Teatro('Sala 3')
        }
        self.funciones_diarias: Dict[str, List[Función]] = {
            'Sala 1': [],
            'Sala 2': [],
            'Sala 3': []
        }
        self.tiquetes: Dict[int, List[Tiquete]] = {}
        self.controlador_de_archivos = ControladorDeArchivos('data/movies.txt')

    def add_cliente(self, cliente: Cliente) -> None:
        self.clientes.append(cliente)
        self.tiquetes[cliente.id] = []

    def get_cliente(self, id_cliente: str) -> Optional[Cliente]:
        for cliente in self.clientes:
            if cliente.id == id_cliente:
                return cliente
        return None

    def asignar_función(self, función: Función) -> None:
        funciones_de_sala = self.funciones_diarias[función.teatro.nombre]
        if len(funciones_de_sala) >= 2:
            raise ValueError(f"El teatro {función.teatro.nombre} ya tiene dos funciones programadas")
        funciones_de_sala.append(función)

    def comprar_tiquetes(self, función: Función, cliente: Cliente, id_asientos: List[str], precio: float) -> List[Tiquete]:
        tiquetes = []
        asientos_disponibles = [asiento for asiento in función.obtener_asientos_disponibles() if asiento.id in id_asientos]
        if len(asientos_disponibles) != len(id_asientos):
            raise ValueError("Algunos asientos no están disponibles")
        for asiento in asientos_disponibles:
            asiento.reservar()
            tiquete = Tiquete(precio, función, cliente.nombre, asiento)
            tiquetes.append(tiquete)
            self.tiquetes[cliente.id].append(tiquete)
            self.guardar_tiquete_en_archivo(tiquete)
        return tiquetes

    def get_tiquetes_por_cliente(self, id_cliente: str) -> List[Tiquete]:
        return self.tiquetes.get(id_cliente, [])

    def cargar_funciones_desde_archivo(self) -> None:
        funciones = []
        for registro in self.controlador_de_archivos.leer():
            if len(registro) >= 4:
                try:
                    fecha = datetime.strptime(registro[0], '%d%m%Y - %H:%M')
                    película = Película(registro[1], registro[2])
                    teatro = self.teatros.get(registro[3])
                    if teatro is None:
                        raise ValueError(f"Teatro {registro[3]} inválido")
                    función = Función(fecha, película, teatro)
                    funciones.append(función)
                    self.asignar_función(función)
                except ValueError as e:
                    print(f"Error al cargar la función: {e}")
        return funciones

    def get_funciones_por_fecha(self, fecha: datetime, incluir_desde_ahora: bool = False) -> List[Función]:
        tiempoDeReferencia = datetime.now() if incluir_desde_ahora and fecha.date() == datetime.now().date() else fecha.replace(hour=0, minute=0)
        todas_las_funciones = []
        for funciones in self.funciones_diarias.values():
            funciones_coincidentes = [
                función for función in funciones
                if función.fecha.date() == fecha.date() and función.está_disponible(tiempoDeReferencia)
            ]
            todas_las_funciones.extend(funciones_coincidentes)
        return sorted(todas_las_funciones, key=lambda x: x.fecha)

    def guardar_tiquete_en_archivo(self, tiquete: Tiquete) -> None:
        tiquete_data = [
            tiquete.función.fecha.strftime('%Y-%m-%d %H:%M'),
            tiquete.función.película.nombre,
            tiquete.función.teatro.nombre,
            tiquete.asiento.id,
            tiquete.nombre_cliente,
            f"{tiquete.precio:.2f}"
        ]
        self.controlador_de_archivos.escribir(tiquete_data)

    def mostrar_tablero(self, teatro: Teatro) -> None:
        filas = "ABCDEFGHIJ"
        asientos_por_fila = len(teatro.asientos) // len(filas)

        print("\nEstado de los asientos:\n")

        for i, fila in enumerate(filas):
            fila_asientos = teatro.asientos[i * asientos_por_fila:(i + 1) * asientos_por_fila]
            linea = ""
            for asiento in fila_asientos:
                estado = "[ ]" if asiento.está_disponible() else "[X]"
                linea += f"{asiento.id} {estado}  "
            print(linea)

class TheaterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cine Cultural Barranquilla")
        self.root.geometry("1280x720")


        try:
            img_avail_path = "seat_available.png"
            img_occup_path = "seat_occupied.png"

            pil_img_available = Image.open(img_avail_path)
            pil_img_occupied = Image.open(img_occup_path)

            self.img_available = ImageTk.PhotoImage(pil_img_available)
            self.img_occupied = ImageTk.PhotoImage(pil_img_occupied)
        except FileNotFoundError:
            print(f"Error: No se encontraron los archivos de imagen ({img_avail_path}, {img_occup_path}). Usando colores.")
            self.img_available = None
            self.img_occupied = None
        except ImportError:
            print("Error: La biblioteca Pillow no está instalada. pip install Pillow. Usando colores.")
            self.img_available = None
            self.img_occupied = None

        # Crear 3 salas (Theater) con 80 asientos cada una
        self.salas = [Teatro(f"Sala {i+1}") for i in range(3)]
        self.sala_actual_idx = 0

        # Modo desarrollar
        self.developer_mode_enabled = False

        # Configurar layout principal
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Barra de menú superior
        self.menu_frame = tk.Frame(self.root, bg='#e0e0e0', height=50)
        self.menu_frame.grid(row=0, column=0, sticky='ew')
        self.menu_frame.grid_propagate(False)

        for idx, sala in enumerate(self.salas):
            btn = tk.Button(self.menu_frame, text=sala.nombre, command=lambda i=idx: self.mostrar_sala(i))
            btn.pack(side='left', padx=10, pady=10)

        # Boton para modo desarrollador
        self.dev_mode_button = tk.Button(self.menu_frame, text="Activar Modo Dev", command=self.toggle_developer_mode)
        self.dev_mode_button.pack(side='right', padx=10, pady=10)

        # Zona dinámica central
        self.content_frame = tk.Frame(self.root, bg='#f8f8f8')
        self.content_frame.grid(row=1, column=0, sticky='nsew')
        # self.content_frame.grid_propagate(True)

        # Barra de estado inferior
        self.status_frame = tk.Frame(self.root, bg='#e0e0e0', height=30)
        self.status_frame.grid(row=2, column=0, sticky='ew')
        self.status_frame.grid_propagate(False)
        self.status_label = tk.Label(self.status_frame, text="Listo", anchor='w', bg='#e0e0e0')
        self.status_label.pack(fill='both', padx=10)

        self.mostrar_sala(self.sala_actual_idx)

    def toggle_developer_mode(self):
        """Activa o desactiva el modo desarrollador."""
        self.developer_mode_enabled = not self.developer_mode_enabled
        status = "ACTIVADO" if self.developer_mode_enabled else "DESACTIVADO"
        button_text = "Desactivar Modo Dev" if self.developer_mode_enabled else "Activar Modo Dev"
        
        self.dev_mode_button.config(text=button_text)
        self.status_label.config(text=f"Modo Desarrollador {status}")
        print(f"Modo Desarrollador: {status}") # También en consola para claridad

        # Actualizar la apariencia de los asientos (bordes?) si es necesario
        # para indicar visualmente que son clickables de forma diferente
        self.mostrar_sala(self.sala_actual_idx) # Vuelve a dibujar la sala actual

    def mostrar_sala(self, idx):
        """Limpia el frame de contenido y muestra los asientos de la sala indicada."""
        # Limpiar contenido anterior
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        sala = self.salas[idx]
        self.sala_actual_idx = idx # Guardamos el índice actual
        
        mode_text = "(Modo Dev)" if self.developer_mode_enabled else ""
        self.status_label.config(text=f"Mostrando {sala.nombre} {mode_text}")

        # --- Añadir Pantalla Visual Abajo ---
        # Usar un Frame simple para representar la pantalla
        screen_frame = tk.Frame(self.content_frame, bg='black', height=20) 
        # Empaquetar la pantalla en la parte INFERIOR del content_frame
        screen_frame.pack(side='bottom', fill='x', padx=50, pady=(10, 20))

        screen_label = tk.Label(screen_frame, text="PANTALLA", bg='black', fg='white', font=('Arial', 10, 'bold'))
        screen_label.pack(pady=2)

        # Pasar el frame padre y la sala a la función que dibuja asientos
        self.mostrar_asientos(self.content_frame, sala)


# ... dentro de la clase TheaterGUI ...

    def mostrar_asientos(self, parent, sala):
        """Dibuja la cuadrícula de asientos con el layout especificado por el usuario."""

        # --- Definición del Layout Específico (80 asientos) ---
        # Pantalla abajo, Fila 0 es la más lejana
        seats_per_row = [11]*2 + [9]*2 + [7]*5 + [5]*1  # -> Total 80 asientos
        num_rows = len(seats_per_row)

        # El máximo de asientos define el ancho necesario del bloque central
        max_seats_in_row = 11 # Definido por las primeras filas
        # Columnas necesarias: 1 (pasillo izq) + 11 (max asientos) + 1 (pasillo der)
        num_grid_cols = 1 + max_seats_in_row + 1 # = 13 columnas

        parent_bg_color = parent['bg']

        # Frame para contener la cuadrícula de asientos
        grid_frame = tk.Frame(parent, bg=parent_bg_color)
        grid_frame.pack(side='top', expand=True, pady=(20, 10))

        # --- Lógica para colocar asientos con indentación ---
        asiento_index = 0

        for i in range(num_rows): # Iterar filas 0 a 9
            num_seats_this_row = seats_per_row[i]

            # Calcular cuántas columnas vacías dejar a cada lado respecto al máximo (11)
            # La diferencia siempre será par (0, 2, 4, 6), así que //2 funciona bien para simetría
            indent_each_side = (max_seats_in_row - num_seats_this_row) // 2

            # Columna de la grilla donde empiezan los asientos en esta fila
            # (Columna 0 es pasillo, luego vienen los 'indent_each_side' espacios vacíos)
            start_seat_col = 1 + indent_each_side
            # Columna de la grilla donde terminan los asientos en esta fila
            end_seat_col = start_seat_col + num_seats_this_row - 1

            for j in range(num_grid_cols): # Iterar columnas 0 a 12
                # 1. Pasillo Izquierdo (Columna 0)
                if j == 0:
                    aisle_frame = tk.Frame(grid_frame, width=30, height=45, bg=parent_bg_color)
                    aisle_frame.grid(row=i, column=j, padx=5, pady=5)
                    aisle_frame.pack_propagate(False)

                # 2. Pasillo Derecho (Última Columna: 12)
                elif j == num_grid_cols - 1:
                    aisle_frame = tk.Frame(grid_frame, width=30, height=45, bg=parent_bg_color)
                    aisle_frame.grid(row=i, column=j, padx=5, pady=5)
                    aisle_frame.pack_propagate(False)

                # 3. Espacio de Asientos / Espacios Vacíos (Columnas 1 a 11)
                else:
                    # ¿Esta columna 'j' debe tener un asiento en esta fila 'i'?
                    if start_seat_col <= j <= end_seat_col:
                        # Sí, colocar asiento
                        if asiento_index < len(sala.asientos):
                            asiento = sala.asientos[asiento_index]

                            img_to_use = self.img_available
                            if not asiento.está_disponible():
                                img_to_use = self.img_occupied

                            button_config = {
                                "borderwidth": 0,
                                "highlightthickness": 0,
                                "relief": "flat",
                                "bg": parent_bg_color,
                                "activebackground": parent_bg_color
                            }

                            if self.img_available and self.img_occupied:
                                seat_btn = tk.Button(grid_frame, image=img_to_use,
                                                     width=40, height=40,
                                                     **button_config)
                                seat_btn.image = img_to_use
                            else: # Fallback
                                seat_btn = tk.Button(grid_frame, text=asiento.id, bg='gray',
                                                     width=4, height=2, relief='ridge')

                            seat_btn.config(state='normal')
                            seat_btn.config(command=lambda a=asiento, b=seat_btn: self.on_seat_click(a, b))

                            if self.developer_mode_enabled:
                                seat_btn.config(highlightthickness=1, highlightbackground="blue")
                            else:
                                seat_btn.config(highlightthickness=0)

                            seat_btn.grid(row=i, column=j, padx=5, pady=5)
                            asiento_index += 1
                        else:
                            # Error lógico si esto ocurre
                            print(f"Error: Se esperaban más asientos. Índice {asiento_index}")
                            tk.Frame(grid_frame, width=45, height=45, bg="red").grid(row=i, column=j, padx=5, pady=5)

                    else:
                        # No, esta columna 'j' es un espacio vacío indentado en esta fila 'i'
                        empty_space = tk.Frame(grid_frame, width=45, height=45, bg=parent_bg_color)
                        empty_space.grid(row=i, column=j, padx=5, pady=5)

        # Debug: Verificar si se usaron todos los asientos
        if asiento_index != len(sala.asientos):
            print(f"Advertencia: El layout usó {asiento_index} asientos, pero la sala tiene {len(sala.asientos)}.")

    def on_seat_click(self, asiento: Asiento, button: tk.Button):
        """Manejador de eventos para cuando se hace clic en un asiento."""
        print(f"Clic en asiento: {asiento.id}, Disponible: {asiento.está_disponible()}") # Log de consola

        if self.developer_mode_enabled:
            # --- Lógica del Modo Desarrollador: Cambiar estado ---
            nueva_imagen = None
            nuevo_estado_str = ""
            color_fallback = ""

            if asiento.está_disponible():
                # Simular reserva (solo para Dev Mode)
                # En lugar de asiento.reservar() que puede fallar si ya está ocupado,
                # simplemente cambiamos el estado directamente para el toggle.
                asiento.disponible = False 
                nueva_imagen = self.img_occupied
                nuevo_estado_str = "Ocupado (Dev)"
                color_fallback = "red"
            else:
                # Simular des-reserva (solo para Dev Mode)
                asiento.disponible = True
                nueva_imagen = self.img_available
                nuevo_estado_str = "Disponible (Dev)"
                color_fallback = "green"

            # Actualizar la apariencia del botón
            if self.img_available and self.img_occupied:
                 button.config(image=nueva_imagen)
                 button.image = nueva_imagen # ¡Actualizar referencia!
            else:
                 button.config(bg=color_fallback, text=asiento.id) # Actualizar color si no hay imagen

            self.status_label.config(text=f"DevMode: Asiento {asiento.id} -> {nuevo_estado_str}")

        else:
            # --- Lógica Normal (cuando NO está en Modo Dev) ---
            # Aquí iría la lógica para seleccionar asientos para comprar (más adelante)
            # Por ahora, solo informa
            estado = "Disponible" if asiento.está_disponible() else "Ocupado"
            self.status_label.config(text=f"Asiento {asiento.id} seleccionado ({estado}). Compra no implementada.")
            
            # Podrías añadir una lógica visual para marcar asientos seleccionados
            # (ej. cambiando el borde) antes de confirmar la compra.
def main():
    root = tk.Tk()
    app = TheaterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 