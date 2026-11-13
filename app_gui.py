"""
Interfaz Gráfica de Usuario (GUI): Método de Punto Fijo
Análisis Numérico - Solución de Ecuaciones No Lineales

Desarrollado con Tkinter y Matplotlib.
Proporciona visualización interactiva, diagrama de telaraña (cobweb plot),
curva de convergencia semilogarítmica, tabla de iteraciones y exportación a CSV.
"""

import csv
import math
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np

# Configuración de backend para Matplotlib
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

# Importar el motor de cálculo
from punto_fijo import (
    PuntoFijoSolver,
    SolverResult,
    EJEMPLOS_PRECONFIGURADOS,
    sanitize_expression
)

# Habilitar soporte High-DPI en Windows si está disponible
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


class PuntoFijoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Método de Punto Fijo - Solución de Ecuaciones No Lineales")
        self.root.geometry("1240x820")
        self.root.minsize(1050, 700)

        # Variables de estado
        self.resultado_actual: SolverResult = None

        # Configurar estilos visuales modernos
        self._configurar_estilos()

        # Construir interfaz
        self._construir_interfaz()

        # Cargar el primer ejemplo predeterminado
        self._cargar_ejemplo(0)

    def _configurar_estilos(self):
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except Exception:
            pass

        # Colores de la paleta
        self.c_bg_dark = "#1e293b"      # Slate 800
        self.c_primary = "#2563eb"      # Blue 600
        self.c_primary_hover = "#1d4ed8"
        self.c_success = "#16a34a"      # Green 600
        self.c_danger = "#dc2626"       # Red 600
        self.c_card_bg = "#ffffff"
        self.c_border = "#e2e8f0"
        self.c_text = "#0f172a"
        self.c_text_muted = "#64748b"

        # Estilos generales TTK
        self.style.configure(".", font=("Segoe UI", 9))
        self.style.configure("TLabel", foreground=self.c_text, background="#f8fafc")
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#ffffff", background=self.c_bg_dark)
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 9), foreground="#94a3b8", background=self.c_bg_dark)
        
        self.style.configure("CardTitle.TLabel", font=("Segoe UI", 10, "bold"), foreground="#1e293b")
        self.style.configure("BadgeSuccess.TLabel", font=("Segoe UI", 10, "bold"), foreground=self.c_success)
        self.style.configure("BadgeDanger.TLabel", font=("Segoe UI", 10, "bold"), foreground=self.c_danger)
        
        self.style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=6)
        self.style.map("Action.TButton",
            foreground=[('active', '#ffffff'), ('!disabled', '#ffffff')],
            background=[('active', self.c_primary_hover), ('!disabled', self.c_primary)]
        )

        self.style.configure("Secondary.TButton", font=("Segoe UI", 9), padding=5)
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        self.style.configure("Treeview", rowheight=24, font=("Segoe UI", 9))

    def _construir_interfaz(self):
        # Contenedor principal
        self.root.configure(bg="#f8fafc")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        # 1. ENCABEZADO SUPERIOR
        header_frame = tk.Frame(self.root, bg=self.c_bg_dark, height=65)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.columnconfigure(0, weight=1)

        header_content = tk.Frame(header_frame, bg=self.c_bg_dark, padx=20, pady=10)
        header_content.pack(fill="x")

        lbl_title = ttk.Label(
            header_content,
            text="MÉTODO DE PUNTO FIJO | ANÁLISIS NUMÉRICO",
            style="Header.TLabel"
        )
        lbl_title.pack(anchor="w")

        lbl_subtitle = ttk.Label(
            header_content,
            text="Solución interactiva para ecuaciones no lineales x = g(x) | Algoritmo Iterativo de Punto Fijo",
            style="SubHeader.TLabel"
        )
        lbl_subtitle.pack(anchor="w")

        # 2. CUERPO PRINCIPAL (Split Izquierda: Entradas | Derecha: Resultados y Gráficas)
        body_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        body_paned.grid(row=1, column=0, sticky="nsew", padx=12, pady=10)

        # PANEL IZQUIERDO: CONTROLES Y ENTRADAS
        left_panel = tk.Frame(body_paned, bg="#ffffff", bd=1, relief="solid", highlightbackground=self.c_border)
        body_paned.add(left_panel, weight=0)

        self._construir_panel_izquierdo(left_panel)

        # PANEL DERECHO: RESULTADOS, GRÁFICAS Y TABLA
        right_panel = tk.Frame(body_paned, bg="#f8fafc")
        body_paned.add(right_panel, weight=1)

        self._construir_panel_derecho(right_panel)

    def _construir_panel_izquierdo(self, parent: tk.Frame):
        parent.configure(padx=16, pady=14)
        
        # 1. Selector de Ejemplos
        lbl_presets = ttk.Label(parent, text="📂 Cargar Ejemplo Preconfigurado:", style="CardTitle.TLabel", background="#ffffff")
        lbl_presets.pack(anchor="w", pady=(0, 4))

        self.combo_ejemplos = ttk.Combobox(
            parent,
            values=[ex["nombre"] for ex in EJEMPLOS_PRECONFIGURADOS],
            state="readonly",
            width=38
        )
        self.combo_ejemplos.current(0)
        self.combo_ejemplos.bind("<<ComboboxSelected>>", self._on_ejemplo_seleccionado)
        self.combo_ejemplos.pack(fill="x", pady=(0, 10))

        # Separador
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=8)

        # 2. Formulario de Parámetros
        lbl_params = ttk.Label(parent, text="⚙ Parámetros de Entrada", style="CardTitle.TLabel", background="#ffffff")
        lbl_params.pack(anchor="w", pady=(0, 8))

        # Campo g(x)
        frame_g = tk.Frame(parent, bg="#ffffff")
        frame_g.pack(fill="x", pady=3)
        ttk.Label(frame_g, text="Función g(x)  [Requerida]:", background="#ffffff", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        ttk.Label(frame_g, text="Forma contractiva x = g(x)", background="#ffffff", font=("Segoe UI", 8), foreground=self.c_text_muted).pack(anchor="w")
        self.ent_g = ttk.Entry(frame_g, font=("Consolas", 10))
        self.ent_g.pack(fill="x", pady=2)

        # Campo f(x)
        frame_f = tk.Frame(parent, bg="#ffffff")
        frame_f.pack(fill="x", pady=3)
        ttk.Label(frame_f, text="Función f(x)  [Opcional]:", background="#ffffff", font=("Segoe UI", 9)).pack(anchor="w")
        ttk.Label(frame_f, text="Ecuación original f(x) = 0 para verificar residual", background="#ffffff", font=("Segoe UI", 8), foreground=self.c_text_muted).pack(anchor="w")
        self.ent_f = ttk.Entry(frame_f, font=("Consolas", 10))
        self.ent_f.pack(fill="x", pady=2)

        # Parámetros numéricos en 2 columnas
        grid_frame = tk.Frame(parent, bg="#ffffff")
        grid_frame.pack(fill="x", pady=5)
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        # x0
        ttk.Label(grid_frame, text="Valor inicial (x₀):", background="#ffffff").grid(row=0, column=0, sticky="w", pady=2)
        self.ent_x0 = ttk.Entry(grid_frame, font=("Consolas", 9), width=12)
        self.ent_x0.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=(0, 6))

        # Tolerancia
        ttk.Label(grid_frame, text="Tolerancia (Tol):", background="#ffffff").grid(row=0, column=1, sticky="w", pady=2)
        self.ent_tol = ttk.Entry(grid_frame, font=("Consolas", 9), width=12)
        self.ent_tol.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=(0, 6))

        # Max Iteraciones
        ttk.Label(grid_frame, text="Iteraciones máx:", background="#ffffff").grid(row=2, column=0, sticky="w", pady=2)
        self.ent_max_iter = ttk.Entry(grid_frame, font=("Consolas", 9), width=12)
        self.ent_max_iter.grid(row=3, column=0, sticky="ew", padx=(0, 4), pady=(0, 6))

        # Criterio de Error
        ttk.Label(grid_frame, text="Criterio de parada:", background="#ffffff").grid(row=2, column=1, sticky="w", pady=2)
        self.var_error_type = tk.StringVar(value="abs")
        self.combo_error = ttk.Combobox(
            grid_frame,
            textvariable=self.var_error_type,
            values=["abs", "rel"],
            state="readonly",
            width=10
        )
        self.combo_error.grid(row=3, column=1, sticky="ew", padx=(4, 0), pady=(0, 6))

        # 3. Botones de Acción
        btn_frame = tk.Frame(parent, bg="#ffffff")
        btn_frame.pack(fill="x", pady=(12, 6))

        btn_calcular = tk.Button(
            btn_frame,
            text="▶  CALCULAR SOLUCIÓN",
            bg=self.c_primary,
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            activebackground=self.c_primary_hover,
            activeforeground="#ffffff",
            cursor="hand2",
            pady=8,
            command=self.calcular
        )
        btn_calcular.pack(fill="x", pady=2)

        btn_limpiar = ttk.Button(btn_frame, text="↺ Limpiar Campos", style="Secondary.TButton", command=self.limpiar)
        btn_limpiar.pack(fill="x", pady=3)

        # 4. Cuadro de Ayuda de Sintaxis
        help_card = tk.LabelFrame(parent, text="💡 Ayuda de Sintaxis Matemática", bg="#f1f5f9", font=("Segoe UI", 8, "bold"), padx=8, pady=6)
        help_card.pack(fill="x", pady=(12, 0))

        help_text = (
            "• Potencias: x^2  o  x**2\n"
            "• Raíz cuadrada: sqrt(x)\n"
            "• Exponencial: exp(x)  o  e^x\n"
            "• Logaritmo natural: ln(x)  o  log(x)\n"
            "• Trigonométricas: sin(x), cos(x), tan(x)\n"
            "• Constantes: pi, e\n"
            "• Multiplicación implícita permitida:\n"
            "   ej: 5x -> 5*x,  2cos(x) -> 2*cos(x)"
        )
        lbl_help = tk.Label(help_card, text=help_text, justify="left", bg="#f1f5f9", fg="#334155", font=("Segoe UI", 8))
        lbl_help.pack(anchor="w")

    def _construir_panel_derecho(self, parent: tk.Frame):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # 1. BANNER RESUMEN (KPI Cards)
        self.summary_frame = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid", highlightbackground=self.c_border, padx=14, pady=10)
        self.summary_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.summary_frame.columnconfigure(0, weight=2)
        self.summary_frame.columnconfigure(1, weight=2)
        self.summary_frame.columnconfigure(2, weight=1)
        self.summary_frame.columnconfigure(3, weight=2)
        self.summary_frame.columnconfigure(4, weight=2)

        # Card 1: Estado
        c1 = tk.Frame(self.summary_frame, bg="#ffffff")
        c1.grid(row=0, column=0, sticky="w", padx=6)
        ttk.Label(c1, text="ESTADO", font=("Segoe UI", 8, "bold"), foreground=self.c_text_muted, background="#ffffff").pack(anchor="w")
        self.lbl_res_estado = ttk.Label(c1, text="Listo para calcular", font=("Segoe UI", 10, "bold"), foreground=self.c_primary, background="#ffffff")
        self.lbl_res_estado.pack(anchor="w")

        # Card 2: Raíz aproximada
        c2 = tk.Frame(self.summary_frame, bg="#ffffff")
        c2.grid(row=0, column=1, sticky="w", padx=6)
        ttk.Label(c2, text="RAÍZ APROXIMADA (x*)", font=("Segoe UI", 8, "bold"), foreground=self.c_text_muted, background="#ffffff").pack(anchor="w")
        self.lbl_res_raiz = ttk.Label(c2, text="--", font=("Segoe UI", 11, "bold"), foreground=self.c_text, background="#ffffff")
        self.lbl_res_raiz.pack(anchor="w")

        # Card 3: Iteraciones
        c3 = tk.Frame(self.summary_frame, bg="#ffffff")
        c3.grid(row=0, column=2, sticky="w", padx=6)
        ttk.Label(c3, text="ITERACIONES", font=("Segoe UI", 8, "bold"), foreground=self.c_text_muted, background="#ffffff").pack(anchor="w")
        self.lbl_res_iter = ttk.Label(c3, text="--", font=("Segoe UI", 11, "bold"), foreground=self.c_text, background="#ffffff")
        self.lbl_res_iter.pack(anchor="w")

        # Card 4: Error Final
        c4 = tk.Frame(self.summary_frame, bg="#ffffff")
        c4.grid(row=0, column=3, sticky="w", padx=6)
        ttk.Label(c4, text="ERROR FINAL (Ea / Er%)", font=("Segoe UI", 8, "bold"), foreground=self.c_text_muted, background="#ffffff").pack(anchor="w")
        self.lbl_res_error = ttk.Label(c4, text="--", font=("Segoe UI", 10, "bold"), foreground=self.c_text, background="#ffffff")
        self.lbl_res_error.pack(anchor="w")

        # Card 5: Condición Banach |g'|
        c5 = tk.Frame(self.summary_frame, bg="#ffffff")
        c5.grid(row=0, column=4, sticky="w", padx=6)
        ttk.Label(c5, text="CONDICIÓN |g'(x*)|", font=("Segoe UI", 8, "bold"), foreground=self.c_text_muted, background="#ffffff").pack(anchor="w")
        self.lbl_res_gprime = ttk.Label(c5, text="--", font=("Segoe UI", 10, "bold"), foreground=self.c_text, background="#ffffff")
        self.lbl_res_gprime.pack(anchor="w")

        # 2. PESTAÑAS PRINCIPALES (Notebook)
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        # Pestaña 1: Gráficas (Cobweb y Error)
        tab_graficas = ttk.Frame(self.notebook)
        self.notebook.add(tab_graficas, text=" 📊 Gráficos y Visualización ")
        self._construir_pestana_graficas(tab_graficas)

        # Pestaña 2: Tabla de Iteraciones
        tab_tabla = ttk.Frame(self.notebook)
        self.notebook.add(tab_tabla, text=" 📋 Tabla de Iteraciones ")
        self._construir_pestana_tabla(tab_tabla)

        # Pestaña 3: Fundamento Teórico y Guía de Uso
        tab_teoria = ttk.Frame(self.notebook)
        self.notebook.add(tab_teoria, text=" 📖 Teoría y Método ")
        self._construir_pestana_teoria(tab_teoria)

    def _construir_pestana_graficas(self, parent: ttk.Frame):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        # Figura de Matplotlib con 2 subplots lado a lado
        self.fig = Figure(figsize=(9, 4.8), dpi=100)
        self.fig.patch.set_facecolor('#ffffff')

        self.ax_cobweb = self.fig.add_subplot(121)
        self.ax_error = self.fig.add_subplot(122)
        self.fig.tight_layout(pad=3.2)

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=0, column=0, sticky="nsew")

        # Barra de herramientas de navegación
        toolbar_frame = tk.Frame(parent, bg="#ffffff")
        toolbar_frame.grid(row=1, column=0, sticky="ew")
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        # Dibujo inicial vacío explicativo
        self._dibujar_grafica_inicial()

    def _construir_pestana_tabla(self, parent: ttk.Frame):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # Barra superior de la tabla (Botones exportar / copiar)
        top_bar = tk.Frame(parent, bg="#f8fafc", pady=4)
        top_bar.grid(row=0, column=0, sticky="ew")

        btn_csv = ttk.Button(top_bar, text="💾 Exportar a CSV / Excel", command=self.exportar_csv)
        btn_csv.pack(side="left", padx=4)

        btn_copiar = ttk.Button(top_bar, text="📋 Copiar al Portapapeles", command=self.copiar_tabla)
        btn_copiar.pack(side="left", padx=4)

        self.lbl_filas_info = ttk.Label(top_bar, text="0 filas", font=("Segoe UI", 9, "italic"), foreground=self.c_text_muted)
        self.lbl_filas_info.pack(side="right", padx=10)

        # Contenedor Treeview con Scrollbars
        table_frame = tk.Frame(parent)
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("k", "x_k", "x_next", "ea", "er", "g_prime", "f_val")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("k", text="Iter (k)")
        self.tree.heading("x_k", text="x_k (Actual)")
        self.tree.heading("x_next", text="x_{k+1} = g(x_k)")
        self.tree.heading("ea", text="Error Absoluto (|Ea|)")
        self.tree.heading("er", text="Error Relativo (%)")
        self.tree.heading("g_prime", text="|g'(x_k)|")
        self.tree.heading("f_val", text="f(x_{k+1}) Residual")

        self.tree.column("k", width=65, anchor="center")
        self.tree.column("x_k", width=125, anchor="e")
        self.tree.column("x_next", width=135, anchor="e")
        self.tree.column("ea", width=125, anchor="e")
        self.tree.column("er", width=125, anchor="e")
        self.tree.column("g_prime", width=95, anchor="center")
        self.tree.column("f_val", width=120, anchor="e")

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Etiquetas de color para filas alternadas
        self.tree.tag_configure("even", background="#ffffff")
        self.tree.tag_configure("odd", background="#f1f5f9")
        self.tree.tag_configure("solution", background="#dcfce7")

    def _construir_pestana_teoria(self, parent: ttk.Frame):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        txt_frame = tk.Frame(parent)
        txt_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        txt_frame.columnconfigure(0, weight=1)
        txt_frame.rowconfigure(0, weight=1)

        scroll = ttk.Scrollbar(txt_frame, orient="vertical")
        text_teoria = tk.Text(
            txt_frame,
            wrap="word",
            yscrollcommand=scroll.set,
            font=("Consolas", 10),
            bg="#ffffff",
            fg="#0f172a",
            padx=16,
            pady=16,
            relief="solid",
            bd=1
        )
        scroll.config(command=text_teoria.yview)

        text_teoria.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        teoria_doc = (
            "========================================================================================\n"
            "                      MÉTODO DE PUNTO FIJO - FUNDAMENTO TEÓRICO\n"
            "                    Solución Numérica de Ecuaciones No Lineales\n"
            "========================================================================================\n\n"
            "1. DESCRIPCIÓN DEL MÉTODO:\n"
            "   Dada una ecuación no lineal f(x) = 0, el método de punto fijo consiste en transformarla\n"
            "   algebraicamente en una ecuación equivalente de la forma:\n"
            "                      x = g(x)\n\n"
            "   A partir de un valor inicial x_0, se construye la sucesión iterativa:\n"
            "                      x_{k+1} = g(x_k),   para k = 0, 1, 2, ...\n\n"
            "   Geométricamente, la solución corresponde al punto de intersección entre la recta y = x\n"
            "   y la curva y = g(x).\n\n"
            "----------------------------------------------------------------------------------------\n"
            "2. TEOREMA DEL PUNTO FIJO DE BANACH (CONDICIÓN DE CONVERGENCIA):\n"
            "   Para que la sucesión converja a un punto fijo p en un intervalo cerrado [a, b], deben\n"
            "   cumplirse dos condiciones fundamentales:\n"
            "     a) Existencia: g(x) está en [a, b] para todo x en [a, b].\n"
            "     b) Unicidad y Contracción: La derivada cumple |g'(x)| <= k < 1 para todo x en [a, b].\n\n"
            "   Interpretación física / geométrica:\n"
            "   • Si |g'(p)| < 1: El punto fijo es ATRACTOR (convergente). Las iteraciones se acercan al punto.\n"
            "   • Si |g'(p)| > 1: El punto fijo es REPULSOR (divergente). Las iteraciones se alejan en espiral.\n"
            "   • Si -1 < g'(p) < 0: Convergencia con oscilaciones alternadas (espiral hacia adentro).\n"
            "   • Si  0 < g'(p) < 1: Convergencia monótona en escalera (staircase hacia el punto fijo).\n\n"
            "----------------------------------------------------------------------------------------\n"
            "3. CÓMO TRANSFORMAR f(x) = 0 EN x = g(x):\n"
            "   Existen múltiples formas de despejar x a partir de una ecuación f(x) = 0:\n\n"
            "   a) Despeje algebraico directo:\n"
            "      Aislar la variable x en uno de los términos (ej: lineales, cuadráticos o exponenciales).\n\n"
            "   b) Sumar x a ambos lados:\n"
            "      f(x) = 0  <=>  x = x + f(x),  es decir,  g(x) = x + f(x).\n"
            "      O de forma más general, con un factor de relajación λ:  g(x) = x - λ*f(x).\n\n"
            "   c) Elección de la g(x) contractiva:\n"
            "      No todos los despejes convergen. Para garantizar convergencia, es fundamental verificar\n"
            "      que en la vecindad de la raíz se cumpla |g'(x)| < 1.\n\n"
            "   Ejemplo didáctico con la ecuación cuadrática x² - 2x - 3 = 0 (raíz x = 3):\n"
            "   • Despeje A:  2x = x² - 3  =>  g_A(x) = (x² - 3)/2.  Derivada: g_A'(3) = 3 > 1 (¡Diverge!).\n"
            "   • Despeje B:  x² = 2x + 3  =>  g_B(x) = sqrt(2x + 3). Derivada: g_B'(3) = 1/3 ≈ 0.33 < 1 (¡Converge!).\n\n"
            "----------------------------------------------------------------------------------------\n"
            "4. CRITERIOS DE DETENCIÓN (PARADA):\n"
            "   • Error Absoluto:          |x_{k+1} - x_k| <= Tolerancia\n"
            "   • Error Relativo:          |x_{k+1} - x_k| / |x_{k+1}| <= Tolerancia\n"
            "   • Error Relativo (%):      (|x_{k+1} - x_k| / |x_{k+1}|) * 100%\n"
            "   • Límite de iteraciones:   k == Max_Iter\n"
            "========================================================================================\n"
        )
        text_teoria.insert("1.0", teoria_doc)
        text_teoria.config(state="disabled")

    def _on_ejemplo_seleccionado(self, event=None):
        idx = self.combo_ejemplos.current()
        if idx >= 0:
            self._cargar_ejemplo(idx)

    def _cargar_ejemplo(self, idx: int):
        if idx < 0 or idx >= len(EJEMPLOS_PRECONFIGURADOS):
            return
        ej = EJEMPLOS_PRECONFIGURADOS[idx]

        self.ent_g.delete(0, tk.END)
        self.ent_g.insert(0, ej["g_expr"])

        self.ent_f.delete(0, tk.END)
        if ej.get("f_expr"):
            self.ent_f.insert(0, ej["f_expr"])

        self.ent_x0.delete(0, tk.END)
        self.ent_x0.insert(0, str(ej["x0"]))

        self.ent_tol.delete(0, tk.END)
        self.ent_tol.insert(0, str(ej["tol"]))

        self.ent_max_iter.delete(0, tk.END)
        self.ent_max_iter.insert(0, str(ej["max_iter"]))

        self.combo_error.set(ej.get("error_type", "abs"))

    def limpiar(self):
        self.ent_g.delete(0, tk.END)
        self.ent_f.delete(0, tk.END)
        self.ent_x0.delete(0, tk.END)
        self.ent_tol.delete(0, tk.END)
        self.ent_max_iter.delete(0, tk.END)
        
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.lbl_filas_info.config(text="0 filas")

        # Restablecer KPIs
        self.lbl_res_estado.config(text="Listo", foreground=self.c_primary)
        self.lbl_res_raiz.config(text="--")
        self.lbl_res_iter.config(text="--")
        self.lbl_res_error.config(text="--")
        self.lbl_res_gprime.config(text="--")

        # Dibujar gráfica vacía
        self._dibujar_grafica_inicial()

    def _dibujar_grafica_inicial(self):
        self.ax_cobweb.clear()
        self.ax_error.clear()

        self.ax_cobweb.set_title("Diagrama de Telaraña (Cobweb)", fontsize=10, fontweight="bold", pad=8)
        self.ax_cobweb.text(0.5, 0.5, "Haga clic en 'Calcular Solución'\npara visualizar la trayectoria iterativa",
                           ha='center', va='center', transform=self.ax_cobweb.transAxes, color='#64748b', fontsize=10)
        self.ax_cobweb.grid(True, linestyle="--", alpha=0.5)

        self.ax_error.set_title("Curva de Convergencia del Error", fontsize=10, fontweight="bold", pad=8)
        self.ax_error.text(0.5, 0.5, "El error decreciente vs iteraciones\nse graficará aquí",
                          ha='center', va='center', transform=self.ax_error.transAxes, color='#64748b', fontsize=10)
        self.ax_error.grid(True, linestyle="--", alpha=0.5)

        self.canvas.draw_idle()

    def calcular(self):
        # Validar entradas
        g_str = self.ent_g.get().strip()
        if not g_str:
            messagebox.showerror("Campo requerido", "Por favor ingrese la función contractiva g(x).")
            return

        f_str = self.ent_f.get().strip()

        try:
            x0 = float(self.ent_x0.get().strip())
        except ValueError:
            messagebox.showerror("Valor inválido", "El valor inicial x₀ debe ser un número válido.")
            return

        try:
            tol = float(self.ent_tol.get().strip())
            if tol <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Valor inválido", "La tolerancia debe ser un número positivo (ej: 1e-6 o 0.0001).")
            return

        try:
            max_iter = int(self.ent_max_iter.get().strip())
            if max_iter <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Valor inválido", "El número máximo de iteraciones debe ser un entero positivo.")
            return

        error_type = self.var_error_type.get()

        # Ejecutar solver
        try:
            solver = PuntoFijoSolver(
                g_expr=g_str,
                f_expr=f_str,
                x0=x0,
                tol=tol,
                max_iter=max_iter,
                error_type=error_type
            )
            res = solver.solve()
            self.resultado_actual = res
        except Exception as e:
            messagebox.showerror("Error al procesar", f"No se pudo resolver la ecuación:\n{e}")
            return

        # Actualizar KPIs
        self._actualizar_kpis(res)

        # Actualizar Tabla
        self._actualizar_tabla(res)

        # Actualizar Gráficas
        self._actualizar_graficas(solver, res)

        # Si divergió, alertar
        if not res.success and res.status == "DIVERGENCIA":
            messagebox.showwarning(
                "Divergencia Detectada",
                "El método divergió. La condición de Banach |g'(x)| < 1 no se cumple en esta región.\n"
                "Sugerencia: Despeje g(x) de otra forma o use una aproximación inicial más cercana."
            )

    def _actualizar_kpis(self, res: SolverResult):
        if res.success:
            self.lbl_res_estado.config(text="✓ Convergencia Exitosa", foreground=self.c_success)
        elif res.status == "DIVERGENCIA":
            self.lbl_res_estado.config(text="✗ Divergencia (|g'| > 1)", foreground=self.c_danger)
        elif res.status == "MAX_ITER_ALCANZADO":
            self.lbl_res_estado.config(text="⚠ Máx Iteraciones", foreground="#d97706")
        else:
            self.lbl_res_estado.config(text=res.status, foreground=self.c_danger)

        if res.root is not None and math.isfinite(res.root):
            self.lbl_res_raiz.config(text=f"{res.root:.8f}")
        else:
            self.lbl_res_raiz.config(text="No finita")

        self.lbl_res_iter.config(text=str(res.iterations_count))
        self.lbl_res_error.config(text=f"Ea: {res.final_error_abs:.2e} | Er: {res.final_error_rel_pct:.3f}%")

        if res.g_prime_root is not None and math.isfinite(res.g_prime_root):
            val_gp = abs(res.g_prime_root)
            if val_gp < 1.0:
                self.lbl_res_gprime.config(text=f"|g'| = {val_gp:.4f}  (Contractiva < 1)", foreground=self.c_success)
            else:
                self.lbl_res_gprime.config(text=f"|g'| = {val_gp:.4f}  (Repulsora >= 1)", foreground=self.c_danger)
        else:
            self.lbl_res_gprime.config(text="N/A", foreground=self.c_text_muted)

    def _actualizar_tabla(self, res: SolverResult):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, step in enumerate(res.steps):
            is_last = (i == len(res.steps) - 1) and res.success
            tag = "solution" if is_last else ("even" if i % 2 == 0 else "odd")

            gp_txt = f"{abs(step.g_prime):.4f}" if step.g_prime is not None and math.isfinite(step.g_prime) else "N/A"
            f_txt = f"{step.f_val:.4e}" if step.f_val is not None and math.isfinite(step.f_val) else "N/A"

            self.tree.insert("", "end", values=(
                step.k,
                f"{step.x_k:.8f}",
                f"{step.x_next:.8f}",
                f"{step.error_abs:.4e}",
                f"{step.error_rel_pct:.4f}%",
                gp_txt,
                f_txt
            ), tags=(tag,))

        self.lbl_filas_info.config(text=f"{len(res.steps)} iteraciones registradas")

    def _actualizar_graficas(self, solver: PuntoFijoSolver, res: SolverResult):
        self.ax_cobweb.clear()
        self.ax_error.clear()

        if not res.steps:
            self._dibujar_grafica_inicial()
            return

        # -------------------------------------------------------------
        # 1. DIAGRAMA DE TELARAÑA (Cobweb Plot)
        # -------------------------------------------------------------
        # Determinar rango de graficación basado en la trayectoria
        all_x = [step.x_k for step in res.steps] + [step.x_next for step in res.steps]
        valid_x = [x for x in all_x if math.isfinite(x) and abs(x) < 1e6]

        if not valid_x:
            valid_x = [solver.x0, solver.x0 + 1.0]

        min_val = min(valid_x)
        max_val = max(valid_x)
        span = max(abs(max_val - min_val), 1.0)
        margin = span * 0.25

        x_plot_min = min_val - margin
        x_plot_max = max_val + margin

        # Curva y = x
        x_line = np.linspace(x_plot_min, x_plot_max, 400)
        self.ax_cobweb.plot(x_line, x_line, 'k--', label='y = x (Identidad)', linewidth=1.5, alpha=0.7)

        # Curva y = g(x)
        try:
            y_g = solver.g_vec(x_line)
            # Filtrar discontinuidades/inf
            y_g = np.where(np.abs(y_g) > 1e4, np.nan, y_g)
            self.ax_cobweb.plot(x_line, y_g, color='#2563eb', label='y = g(x)', linewidth=2.0)
        except Exception:
            pass

        # Trayectoria Cobweb (Escalera)
        cobweb_x = []
        cobweb_y = []

        # Iniciar en (x0, x0) sobre la recta identidad
        first_x = res.steps[0].x_k
        cobweb_x.append(first_x)
        cobweb_y.append(first_x)

        max_steps_plot = min(len(res.steps), 35) # limitar líneas para claridad visual
        for i in range(max_steps_plot):
            s = res.steps[i]
            if not math.isfinite(s.x_k) or not math.isfinite(s.x_next):
                break
            # Vertical: de (x_k, x_k) a (x_k, g(x_k))
            cobweb_x.append(s.x_k)
            cobweb_y.append(s.x_next)
            # Horizontal: de (x_k, g(x_k)) a (g(x_k), g(x_k)) = (x_{k+1}, x_{k+1})
            cobweb_x.append(s.x_next)
            cobweb_y.append(s.x_next)

        self.ax_cobweb.plot(
            cobweb_x, cobweb_y,
            color='#dc2626',
            linestyle='-',
            linewidth=1.4,
            alpha=0.85,
            label='Trayectoria Iterativa'
        )

        # Marcador de inicio x0
        self.ax_cobweb.plot(first_x, first_x, 'o', color='#ea580c', markersize=6, label=f'Inicio x₀ = {first_x:.2g}')

        # Marcador de solución final si convergió
        if res.success and res.root is not None and math.isfinite(res.root):
            self.ax_cobweb.plot(
                res.root, res.root,
                'o', color='#16a34a',
                markersize=9,
                label=f'Punto Fijo x* = {res.root:.4f}'
            )

        self.ax_cobweb.set_title("Diagrama de Telaraña (Cobweb)", fontsize=10, fontweight="bold", pad=8)
        self.ax_cobweb.set_xlabel("x", fontsize=9)
        self.ax_cobweb.set_ylabel("y = g(x)", fontsize=9)
        self.ax_cobweb.set_xlim(x_plot_min, x_plot_max)
        self.ax_cobweb.set_ylim(x_plot_min, x_plot_max)
        self.ax_cobweb.grid(True, linestyle="--", alpha=0.5)
        self.ax_cobweb.legend(loc='best', fontsize=8)

        # -------------------------------------------------------------
        # 2. CURVA DE CONVERGENCIA DEL ERROR
        # -------------------------------------------------------------
        iters = [s.k for s in res.steps]
        errors = [s.error_abs for s in res.steps]

        # Solo graficar errores positivos válidos
        valid_points = [(k, err) for k, err in zip(iters, errors) if math.isfinite(err) and err > 0]
        if valid_points:
            k_pts, err_pts = zip(*valid_points)
            self.ax_error.semilogy(k_pts, err_pts, 'o-', color='#0891b2', linewidth=1.8, markersize=4, label='Error Absoluto |x_{k+1} - x_k|')
            # Línea de tolerancia
            self.ax_error.axhline(solver.tol, color='#16a34a', linestyle='--', linewidth=1.4, label=f'Tolerancia = {solver.tol:.1e}')

        self.ax_error.set_title("Curva de Convergencia del Error", fontsize=10, fontweight="bold", pad=8)
        self.ax_error.set_xlabel("Número de Iteración (k)", fontsize=9)
        self.ax_error.set_ylabel("Error (Escala Logarítmica)", fontsize=9)
        self.ax_error.grid(True, which="both", linestyle="--", alpha=0.5)
        self.ax_error.legend(loc='best', fontsize=8)

        self.fig.tight_layout(pad=3.0)
        self.canvas.draw_idle()

    def exportar_csv(self):
        if not self.resultado_actual or not self.resultado_actual.steps:
            messagebox.showinfo("Exportar", "No hay resultados calculados para exportar.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")],
            title="Guardar reporte de iteraciones como CSV"
        )
        if not filepath:
            return

        try:
            with open(filepath, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                # Encabezado informativo
                writer.writerow(["REPORTE DE MÉTODO DE PUNTO FIJO"])
                writer.writerow(["Funcion g(x)", self.resultado_actual.steps[0].x_k if self.resultado_actual.steps else ""])
                writer.writerow(["Estado", self.resultado_actual.status])
                writer.writerow(["Raiz x*", self.resultado_actual.root])
                writer.writerow(["Iteraciones", self.resultado_actual.iterations_count])
                writer.writerow(["Error Final Abs", self.resultado_actual.final_error_abs])
                writer.writerow(["Error Final Rel %", self.resultado_actual.final_error_rel_pct])
                writer.writerow([])
                # Columnas de datos
                writer.writerow(["Iteracion_k", "x_k", "g(x_k)_x_{k+1}", "Error_Absoluto", "Error_Relativo_pct", "g_prime_x_k", "f_residual"])
                for s in self.resultado_actual.steps:
                    writer.writerow([
                        s.k,
                        s.x_k,
                        s.x_next,
                        s.error_abs,
                        s.error_rel_pct,
                        s.g_prime if s.g_prime is not None else "",
                        s.f_val if s.f_val is not None else ""
                    ])
            messagebox.showinfo("Exportación exitosa", f"Datos exportados correctamente a:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error al guardar", f"No se pudo escribir el archivo:\n{e}")

    def copiar_tabla(self):
        if not self.resultado_actual or not self.resultado_actual.steps:
            messagebox.showinfo("Copiar", "No hay resultados para copiar.")
            return

        lines = ["k\tx_k\tx_{k+1}\tError_Abs\tError_Rel%\t|g'(x_k)|\tf(x)"]
        for s in self.resultado_actual.steps:
            gp = f"{abs(s.g_prime):.4f}" if s.g_prime is not None else "N/A"
            f_val = f"{s.f_val:.4e}" if s.f_val is not None else "N/A"
            lines.append(f"{s.k}\t{s.x_k:.8f}\t{s.x_next:.8f}\t{s.error_abs:.4e}\t{s.error_rel_pct:.4f}%\t{gp}\t{f_val}")

        clipboard_text = "\n".join(lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(clipboard_text)
        messagebox.showinfo("Copiado", "Tabla de iteraciones copiada al portapapeles en formato TSV (listo para pegar en Excel o Word).")


def launch_app():
    root = tk.Tk()
    app = PuntoFijoApp(root)
    root.mainloop()


if __name__ == '__main__':
    launch_app()
