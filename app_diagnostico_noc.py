# =========================================================================
# Proyecto: Centro de Operaciones de Seguridad · SOC (Sistema Experto de Producción & Búsqueda BFS)
# Autor: Angel Gabriel Castillo Castillo
# Copyright (c) 2026. Todos los derechos reservados. Licencia propietaria (ver archivo LICENSE).
# =========================================================================

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import os
import shutil
from datetime import datetime

class SistemaExpertoNOC:
    def __init__(self, root):
        self.root = root
        self.root.title("ITSX - Centro de Diagnóstico NOC Inteligente (Red Bayesiana + SWI-Prolog)")
        self.root.geometry("1280x820")
        self.root.minsize(1180, 750)
        self.root.configure(bg="#0f172a")

        # Variables de evidencia (Síntomas observables)
        self.var_pc1 = tk.StringVar(value="true")
        self.var_pcr = tk.StringVar(value="true")
        self.var_pc2 = tk.StringVar(value="false")

        # Estado del último diagnóstico
        self.ultimo_resultado = {
            "pe": 0.0,
            "probs": {},
            "origen": "Iniciando...",
            "causa_max": "",
            "timestamp": ""
        }

        self.pl_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sistema_experto_red.pl")
        self.configurar_estilos_ttk()
        self.construir_interfaz()
        self.ejecutar_inferencia()

    def configurar_estilos_ttk(self):
        style = ttk.Style()
        style.theme_use("default")

        # Estilo para el Notebook (Pestañas modo oscuro NOC)
        style.configure("TNotebook", background="#0f172a", borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background="#1e293b",
            foreground="#94a3b8",
            padding=[16, 8],
            font=("Segoe UI", 9, "bold"),
            borderwidth=0
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#0284c7"), ("active", "#334155")],
            foreground=[("selected", "#ffffff"), ("active", "#e2e8f0")]
        )

        # Estilo para Treeviews (Tablas CPT)
        style.configure(
            "CPT.Treeview",
            background="#1e293b",
            foreground="#f8fafc",
            fieldbackground="#1e293b",
            rowheight=22,
            font=("Segoe UI", 9),
            borderwidth=0
        )
        style.configure(
            "CPT.Treeview.Heading",
            background="#334155",
            foreground="#38bdf8",
            font=("Segoe UI", 9, "bold"),
            relief="flat"
        )
        style.map("CPT.Treeview", background=[("selected", "#0284c7")], foreground=[("selected", "#ffffff")])

    def encontrar_swipl(self):
        # Busca el ejecutable swipl en el PATH o en las rutas típicas de Windows
        ejecutable = shutil.which("swipl")
        if ejecutable:
            return ejecutable
        rutas_comunes = [
            r"C:\Program Files\swipl\bin\swipl.exe",
            r"C:\Program Files (x86)\swipl\bin\swipl.exe",
            r"C:\Program Files\swipl\bin\swipl.EXE"
        ]
        for ruta in rutas_comunes:
            if os.path.exists(ruta):
                return ruta
        return None

    def construir_interfaz(self):
        # Encabezado Institucional NOC
        header = tk.Frame(self.root, bg="#1e293b", pady=10, padx=20)
        header.pack(fill="x")

        tk.Label(
            header,
            text="CENTRO DE OPERACIONES DE RED (NOC) - LABORATORIO DE SISTEMAS (ITSX)",
            font=("Segoe UI", 13, "bold"),
            fg="#38bdf8",
            bg="#1e293b"
        ).pack(side="left")

        tk.Label(
            header,
            text="Inteligencia Artificial (SCC-1012) | Docente: Francisco Javier Torres Vera",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#1e293b"
        ).pack(side="right")

        # Contenedor Principal (Panel Lateral Izquierdo + Panel Pestañas Derecho)
        main_frame = tk.Frame(self.root, bg="#0f172a", padx=12, pady=10)
        main_frame.pack(fill="both", expand=True)

        # =====================================================================
        # PANEL IZQUIERDO: CONTROLES, ESCENARIOS Y ACCIONES
        # =====================================================================
        left_panel = tk.Frame(main_frame, bg="#1e293b", width=360, padx=14, pady=12)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        tk.Label(
            left_panel,
            text="1. EVIDENCIA DE SÍNTOMAS",
            font=("Segoe UI", 10, "bold"),
            fg="#f8fafc",
            bg="#1e293b"
        ).pack(anchor="w", pady=(0, 6))

        self.crear_selector(
            left_panel, "Estado PC 1 - Lab. Central (EEC1):", self.var_pc1,
            [("Falla (Sin Servicio)", "true"), ("Operativo Normal (OK)", "false")]
        )
        self.crear_selector(
            left_panel, "Resto Lab. Central EEC1 (PCs 2 a 24):", self.var_pcr,
            [("Todas Sin Red (Falla Masiva)", "true"), ("Operativas (OK)", "false"), ("No Verificado (_)", "_")]
        )
        self.crear_selector(
            left_panel, "Equipos Lab. Redes EELR (Salón 2):", self.var_pc2,
            [("También Sin Red (Falla)", "true"), ("Operativo Normal (OK)", "false"), ("No Verificado (_)", "_")]
        )

        btn_calc = tk.Button(
            left_panel,
            text="⚡ EJECUTAR INFERENCIA BAYESIANA",
            command=self.ejecutar_inferencia,
            bg="#0284c7",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            pady=7,
            cursor="hand2"
        )
        btn_calc.pack(fill="x", pady=(10, 14))

        # Escenarios de Demostración
        tk.Label(
            left_panel,
            text="2. ESCENARIOS RÁPIDOS (RÚBRICA)",
            font=("Segoe UI", 10, "bold"),
            fg="#f8fafc",
            bg="#1e293b"
        ).pack(anchor="w", pady=(2, 6))

        escenarios = [
            ("📌 Caso Rúbrica: Salón 1 caído, Salón 2 OK", "true", "true", "false"),
            ("🔌 Falla Aislada: Solo PC 1 de Salón 1", "true", "false", "false"),
            ("🌐 Caída General: Salón 1 y Salón 2 caídos", "true", "true", "true"),
            ("❓ Incertidumbre: Solo reportan PC 1", "true", "_", "_")
        ]
        for texto, v1, vr, v2 in escenarios:
            b = tk.Button(
                left_panel,
                text=texto,
                anchor="w",
                bg="#334155",
                fg="#e2e8f0",
                font=("Segoe UI", 8),
                relief="flat",
                padx=8,
                pady=4,
                cursor="hand2",
                command=lambda a=v1, b=vr, c=v2: self.cargar_escenario(a, b, c)
            )
            b.pack(fill="x", pady=2)

        # Botón Exportar Reporte Técnico
        btn_export = tk.Button(
            left_panel,
            text="📄 Exportar Dictamen Técnico (.txt)",
            command=self.exportar_dictamen,
            bg="#0f766e",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            pady=6,
            cursor="hand2"
        )
        btn_export.pack(fill="x", pady=(10, 10))

        # Dictamen Resumen en Panel Izquierdo
        tk.Label(
            left_panel,
            text="3. DICTAMEN DIAGNÓSTICO",
            font=("Segoe UI", 10, "bold"),
            fg="#f8fafc",
            bg="#1e293b"
        ).pack(anchor="w", pady=(4, 4))

        self.lbl_dictamen = tk.Label(
            left_panel,
            text="",
            font=("Segoe UI", 8),
            fg="#38bdf8",
            bg="#0f172a",
            wraplength=315,
            justify="left",
            padx=8,
            pady=8
        )
        self.lbl_dictamen.pack(fill="both", expand=True)

        # =====================================================================
        # PANEL DERECHO: NOTEBOOK MULTI-PESTAÑA (3 PESTAÑAS NOC)
        # =====================================================================
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(side="right", fill="both", expand=True)

        # Pestaña 1: Monitor Topológico y Bayes
        self.tab_topologia = tk.Frame(self.notebook, bg="#0f172a", padx=8, pady=8)
        self.notebook.add(self.tab_topologia, text=" 📡 Monitor Topológico & Bayes ")

        # Pestaña 2: Plano Arquitectónico Real Edificio de Sistemas ITSX
        self.tab_6_salones = tk.Frame(self.notebook, bg="#0f172a", padx=8, pady=8)
        self.notebook.add(self.tab_6_salones, text=" 🏢 Plano Arquitectónico: Edificio Sistemas ITSX ")

        # Pestaña 3: Inspector de Tablas CPT y Teorema de Bayes
        self.tab_cpt = tk.Frame(self.notebook, bg="#0f172a", padx=10, pady=10)
        self.notebook.add(self.tab_cpt, text=" 📊 Inspector de Tablas CPT y Teorema de Bayes ")

        self.construir_pestana_topologia()
        self.construir_pestana_6_salones()
        self.construir_pestana_cpt()

    # -------------------------------------------------------------------------
    # CONSTRUCCIÓN DE PESTAÑA 1: MONITOR TOPOLÓGICO Y BAYES
    # -------------------------------------------------------------------------
    def construir_pestana_topologia(self):
        # Banner discreto de ayuda interactiva
        lbl_tip = tk.Label(
            self.tab_topologia,
            text="💡 Tip Interactivo: Haz clic directamente sobre los nodos PC 1 (EEC1), PCs 2..24 (EEC1) o PCs 1..24 (EELR) para alternar fallas en vivo.",
            font=("Segoe UI", 8, "italic"),
            fg="#38bdf8",
            bg="#0f172a"
        )
        lbl_tip.pack(anchor="w", pady=(0, 4))

        # Canvas reactivo para el Grafo Bayesiano
        topo_frame = tk.Frame(self.tab_topologia, bg="#1e293b", bd=1, relief="solid")
        topo_frame.pack(fill="x", pady=(0, 8))

        self.canvas = tk.Canvas(topo_frame, height=255, bg="#0f172a", highlightthickness=0)
        self.canvas.pack(fill="x", padx=6, pady=6)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Motion>", self.on_canvas_motion)

        # Panel de Barras de Probabilidad Posterior
        prob_frame = tk.LabelFrame(
            self.tab_topologia,
            text=" Probabilidad Posterior de Causa Raíz P(Hipótesis | Evidencia) ",
            font=("Segoe UI", 9, "bold"),
            fg="#38bdf8",
            bg="#1e293b",
            bd=1,
            padx=10,
            pady=6
        )
        prob_frame.pack(fill="x", pady=(0, 8))

        self.barras = {}
        componentes = [
            ("red_telmex", "ISP Red Telmex (Enlace Externo)"),
            ("router_cisco", "Router Cisco Perimetral (Borde)"),
            ("switch_dist", "Switch Distribución Gigabit (Core)"),
            ("switch_2960_s1", "Switch Cisco 2960 - EEC1 (Lab. Central)"),
            ("pc_s1_e1_aislada", "Daño Físico Aislado PC 1 - EEC1 (Cable/NIC)")
        ]
        for clave, nombre in componentes:
            row = tk.Frame(prob_frame, bg="#1e293b", pady=2)
            row.pack(fill="x")
            tk.Label(row, text=nombre, width=36, anchor="w", font=("Segoe UI", 8, "bold"), fg="#e2e8f0", bg="#1e293b").pack(side="left")
            bar_canvas = tk.Canvas(row, height=14, bg="#0f172a", highlightthickness=0)
            bar_canvas.pack(side="left", fill="x", expand=True, padx=8)
            lbl_pct = tk.Label(row, text="0.00%", width=9, anchor="e", font=("Consolas", 9, "bold"), fg="#38bdf8", bg="#1e293b")
            lbl_pct.pack(side="right")
            self.barras[clave] = (bar_canvas, lbl_pct)

        # Consola de Trazabilidad SWI-Prolog
        console_frame = tk.LabelFrame(
            self.tab_topologia,
            text=" Consola de Inferencia SWI-Prolog y Trazabilidad Matemática (Teorema de Bayes) ",
            font=("Segoe UI", 9, "bold"),
            fg="#38bdf8",
            bg="#1e293b",
            bd=1
        )
        console_frame.pack(fill="both", expand=True)

        self.txt_consola = tk.Text(
            console_frame,
            bg="#090d16",
            fg="#4ade80",
            font=("Consolas", 8),
            height=6,
            relief="flat",
            padx=8,
            pady=6
        )
        self.txt_consola.pack(fill="both", expand=True, padx=6, pady=6)

    # -------------------------------------------------------------------------
    # CONSTRUCCIÓN DE PESTAÑA 2: VISTA COMPLETA 6 SALONES ITSX
    # -------------------------------------------------------------------------
    def construir_pestana_6_salones(self):
        lbl_info = tk.Label(
            self.tab_6_salones,
            text="PLANO ARQUITECTÓNICO REAL: EDIFICIO DE INGENIERÍA EN SISTEMAS COMPUTACIONALES (6 LABORATORIOS × 24 PCs = 144 NODOS)",
            font=("Segoe UI", 9, "bold"),
            fg="#38bdf8",
            bg="#0f172a"
        )
        lbl_info.pack(anchor="w", pady=(0, 4))

        frame_campus = tk.Frame(self.tab_6_salones, bg="#1e293b", bd=1, relief="solid")
        frame_campus.pack(fill="both", expand=True)

        self.canvas_campus = tk.Canvas(frame_campus, bg="#0f172a", highlightthickness=0)
        self.canvas_campus.pack(fill="both", expand=True, padx=8, pady=8)
        self.canvas_campus.bind("<Button-1>", self.on_campus_click)
        self.canvas_campus.bind("<Motion>", self.on_campus_motion)

    # -------------------------------------------------------------------------
    # CONSTRUCCIÓN DE PESTAÑA 3: INSPECTOR DE TABLAS CPT Y TEOREMA DE BAYES
    # -------------------------------------------------------------------------
    def construir_pestana_cpt(self):
        # Panel superior: Marco Teórico y D-Separación
        frame_teoria = tk.Frame(self.tab_cpt, bg="#1e293b", padx=12, pady=10)
        frame_teoria.pack(fill="x", pady=(0, 10))

        tk.Label(
            frame_teoria,
            text="FUNDAMENTACIÓN MATEMÁTICA: REGLA DE LA CADENA, BAYES Y D-SEPARACIÓN",
            font=("Segoe UI", 10, "bold"),
            fg="#38bdf8",
            bg="#1e293b"
        ).pack(anchor="w")

        teoria_texto = (
            "1. Regla de la Cadena Global:\n"
            "   P(T, R, SD, S1, S2, PC1, PCR, PC2) = P(T) · P(R|T) · P(SD|R) · P(S1|SD) · P(S2|SD) · P(PC1|S1) · P(PCR|S1) · P(PC2|S2)\n\n"
            "2. Teorema de Bayes para Inferencia Diagnóstica:\n"
            "   P(H_i | E) = P(H_i, E) / P(E), donde P(E) = ∑_{H} P(H, E)\n\n"
            "3. Demostración de Independencia Condicional (d-separación):\n"
            "   Dado que el Switch de Distribución Gigabit (SD) es el ancestro común que bifurca la red hacia el Salón 1 y el Salón 2,\n"
            "   el conocimiento de que el Salón 2 funciona (PC2 = false) implica que SwitchDist está operativo (SD = false).\n"
            "   Por la propiedad de d-separación en DAGs, la condición SD = false bloquea la propagación de causas hacia RouterCisco\n"
            "   y RedTelmex, demostrando formalmente que la falla queda 100% aislada en el Switch Cisco 2960 del Salón 1."
        )
        tk.Label(
            frame_teoria,
            text=teoria_texto,
            font=("Consolas", 8),
            fg="#cbd5e1",
            bg="#1e293b",
            justify="left"
        ).pack(anchor="w", pady=(4, 0))

        # Panel inferior: Tablas CPT en Paneles Divididos
        frame_tablas = tk.Frame(self.tab_cpt, bg="#0f172a")
        frame_tablas.pack(fill="both", expand=True)

        cpt_col1 = tk.Frame(frame_tablas, bg="#1e293b", padx=8, pady=8)
        cpt_col1.pack(side="left", fill="both", expand=True, padx=(0, 5))

        cpt_col2 = tk.Frame(frame_tablas, bg="#1e293b", padx=8, pady=8)
        cpt_col2.pack(side="right", fill="both", expand=True, padx=(5, 0))

        self.crear_tabla_cpt(
            cpt_col1, "CPT 1: P(RedTelmex) y P(RouterCisco | RedTelmex)",
            ["Variable / Condición", "P(Falla)", "P(Operativo)", "Notas"],
            [
                ("P(RedTelmex) [Priori]", "0.04 (4%)", "0.96 (96%)", "Nodo Raíz ISP"),
                ("P(Router | Telmex=true)", "1.00 (100%)", "0.00 (0%)", "Sin salida ISP"),
                ("P(Router | Telmex=false)", "0.02 (2%)", "0.98 (98%)", "Falla física propia")
            ]
        )

        self.crear_tabla_cpt(
            cpt_col1, "CPT 2: P(SwitchDist | Router) y P(Switch2960_S1 | SwitchDist)",
            ["Variable / Condición", "P(Falla)", "P(Operativo)", "Notas"],
            [
                ("P(SwitchDist | Router=true)", "1.00 (100%)", "0.00 (0%)", "Cascada upstream"),
                ("P(SwitchDist | Router=false)", "0.03 (3%)", "0.97 (97%)", "Falla core propia"),
                ("P(Switch2960_S1 | SD=true)", "1.00 (100%)", "0.00 (0%)", "Uplink caído"),
                ("P(Switch2960_S1 | SD=false)", "0.05 (5%)", "0.95 (95%)", "Falla acceso propia")
            ]
        )

        self.crear_tabla_cpt(
            cpt_col2, "CPT 3: P(PC_S1_E1 | Switch2960_S1) [RESTRICCIÓN FORMAL]",
            ["Variable / Condición", "P(Falla)", "P(Operativo)", "Notas"],
            [
                ("P(PC1 | Switch_S1=true)", "1.00 (100%)", "0.00 (0%)", "Obligatorio Práctica"),
                ("P(PC1 | Switch_S1=false)", "0.08 (8%)", "0.92 (92%)", "Cable UTP / NIC")
            ]
        )

        self.crear_tabla_cpt(
            cpt_col2, "CPT 4: P(PC_S1_Resto | Switch_S1) y Salón 2",
            ["Variable / Condición", "P(Falla)", "P(Operativo)", "Notas"],
            [
                ("P(PCResto | Switch_S1=true)", "1.00 (100%)", "0.00 (0%)", "Caída masiva S1"),
                ("P(PCResto | Switch_S1=false)", "0.001 (0.1%)", "0.999 (99.9%)", "23 fallas aisladas"),
                ("P(PC_S2 | Switch_S2=true)", "1.00 (100%)", "0.00 (0%)", "Salón 2 caído"),
                ("P(PC_S2 | Switch_S2=false)", "0.08 (8%)", "0.92 (92%)", "Salón 2 (Normal)")
            ]
        )

    def crear_tabla_cpt(self, parent, titulo, columnas, filas):
        frame = tk.Frame(parent, bg="#1e293b", pady=4)
        frame.pack(fill="x", pady=(0, 8))
        tk.Label(frame, text=titulo, font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#1e293b").pack(anchor="w", pady=(0, 3))

        tv = ttk.Treeview(frame, columns=columnas, show="headings", height=len(filas), style="CPT.Treeview")
        for col in columnas:
            tv.heading(col, text=col)
            tv.column(col, anchor="center", width=120)
        tv.column(columnas[0], anchor="w", width=190)

        for fila in filas:
            tv.insert("", "end", values=fila)
        tv.pack(fill="x")

    # -------------------------------------------------------------------------
    # CONTROLADORES DE EVENTOS Y SELECCIÓN
    # -------------------------------------------------------------------------
    def crear_selector(self, parent, titulo, variable, opciones):
        frame = tk.Frame(parent, bg="#1e293b", pady=3)
        frame.pack(fill="x")
        tk.Label(frame, text=titulo, font=("Segoe UI", 8, "bold"), fg="#cbd5e1", bg="#1e293b").pack(anchor="w")
        for texto, val in opciones:
            rb = tk.Radiobutton(
                frame,
                text=texto,
                variable=variable,
                value=val,
                command=self.ejecutar_inferencia,
                bg="#1e293b",
                fg="#94a3b8",
                selectcolor="#0f172a",
                activebackground="#1e293b",
                activeforeground="#38bdf8",
                font=("Segoe UI", 8)
            )
            rb.pack(anchor="w", padx=6)

    def cargar_escenario(self, v1, vr, v2):
        self.var_pc1.set(v1)
        self.var_pcr.set(vr)
        self.var_pc2.set(v2)
        self.ejecutar_inferencia()

    def ciclo_estado(self, val):
        if val == "true":
            return "false"
        elif val == "false":
            return "_"
        else:
            return "true"

    def on_canvas_click(self, event):
        x, y = event.x, event.y
        # Detección de clics sobre los nodos interactivos de evidencia en Tab 1:
        # PC_S1_E1: (x=795, y=38) -> x en [735, 855], y en [12, 64]
        if 735 <= x <= 855 and 12 <= y <= 64:
            self.var_pc1.set("false" if self.var_pc1.get() == "true" else "true")
            self.ejecutar_inferencia()
        # PCs S1 (2..24): (x=795, y=108) -> x en [735, 855], y en [82, 134]
        elif 735 <= x <= 855 and 82 <= y <= 134:
            self.var_pcr.set(self.ciclo_estado(self.var_pcr.get()))
            self.ejecutar_inferencia()
        # PCs Salón 2: (x=795, y=198) -> x en [735, 855], y en [172, 224]
        elif 735 <= x <= 855 and 172 <= y <= 224:
            self.var_pc2.set(self.ciclo_estado(self.var_pc2.get()))
            self.ejecutar_inferencia()

    def on_canvas_motion(self, event):
        x, y = event.x, event.y
        if 735 <= x <= 855 and ((12 <= y <= 64) or (82 <= y <= 134) or (172 <= y <= 224)):
            self.canvas.config(cursor="hand2")
        else:
            self.canvas.config(cursor="")

    def on_campus_click(self, event):
        x, y = event.x, event.y
        # EEC1 (Salón 1): x en [575, 815], y en [100, 240]
        if 575 <= x <= 815 and 100 <= y <= 240:
            if y <= 147:
                self.var_pcr.set(self.ciclo_estado(self.var_pcr.get()))
            else:
                self.var_pc1.set("false" if self.var_pc1.get() == "true" else "true")
            self.ejecutar_inferencia()
        # EELR (Salón 2): x en [575, 815], y en [255, 395]
        elif 575 <= x <= 815 and 255 <= y <= 395:
            self.var_pc2.set(self.ciclo_estado(self.var_pc2.get()))
            self.ejecutar_inferencia()

    def on_campus_motion(self, event):
        x, y = event.x, event.y
        if (575 <= x <= 815 and 100 <= y <= 240) or (575 <= x <= 815 and 255 <= y <= 395):
            self.canvas_campus.config(cursor="hand2")
        else:
            self.canvas_campus.config(cursor="")

    # -------------------------------------------------------------------------
    # MOTOR DE INFERENCIA (SWI-PROLOG + FALLBACK PYTHON)
    # -------------------------------------------------------------------------
    def calcular_respaldo_python(self, pc1, pcr, pc2):
        p_t = {True: 0.04, False: 0.96}
        cpt_r = {(True, True): 1.0, (False, True): 0.0, (True, False): 0.02, (False, False): 0.98}
        cpt_sd = {(True, True): 1.0, (False, True): 0.0, (True, False): 0.03, (False, False): 0.97}
        cpt_s1 = {(True, True): 1.0, (False, True): 0.0, (True, False): 0.05, (False, False): 0.95}
        cpt_s2 = {(True, True): 1.0, (False, True): 0.0, (True, False): 0.05, (False, False): 0.95}
        cpt_pc1 = {(True, True): 1.0, (False, True): 0.0, (True, False): 0.08, (False, False): 0.92}
        cpt_pcr = {(True, True): 1.0, (False, True): 0.0, (True, False): 0.001, (False, False): 0.999}
        cpt_pc2 = {(True, True): 1.0, (False, True): 0.0, (True, False): 0.08, (False, False): 0.92}

        dom = lambda v: [True, False] if v == "_" else [v == "true"]
        pe = 0.0
        sumas = {
            "red_telmex": 0.0,
            "router_cisco": 0.0,
            "switch_dist": 0.0,
            "switch_2960_s1": 0.0,
            "pc_s1_e1_aislada": 0.0
        }

        for t in [True, False]:
            for r in [True, False]:
                for sd in [True, False]:
                    for s1 in [True, False]:
                        for s2 in [True, False]:
                            for c1 in dom(pc1):
                                for cr in dom(pcr):
                                    for c2 in dom(pc2):
                                        p = (p_t[t] * cpt_r[(r, t)] * cpt_sd[(sd, r)] *
                                             cpt_s1[(s1, sd)] * cpt_s2[(s2, sd)] *
                                             cpt_pc1[(c1, s1)] * cpt_pcr[(cr, s1)] * cpt_pc2[(c2, s2)])
                                        pe += p
                                        if t: sumas["red_telmex"] += p
                                        elif r: sumas["router_cisco"] += p
                                        elif sd: sumas["switch_dist"] += p
                                        elif s1: sumas["switch_2960_s1"] += p
                                        else: sumas["pc_s1_e1_aislada"] += p
        if pe > 0:
            for k in sumas:
                sumas[k] /= pe
        return pe, sumas, "Motor Bayesiano Integrado (Python Fallback Activo)"

    def ejecutar_inferencia(self):
        pc1 = self.var_pc1.get()
        pcr = self.var_pcr.get()
        pc2 = self.var_pc2.get()

        swipl_path = self.encontrar_swipl()
        origen_motor = "SWI-Prolog (Subproceso Nativo IPC)"
        exito_prolog = False

        if swipl_path and os.path.exists(self.pl_file):
            pl_path_clean = self.pl_file.replace("\\", "/")
            goal = f"consulta_gui({pc1}, {pcr}, {pc2})"
            cmd = [swipl_path, "-q", "-s", pl_path_clean, "-g", goal, "-t", "halt"]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                for line in res.stdout.splitlines():
                    if line.startswith("RESULTADO|"):
                        partes = line.strip().split("|")
                        pe = float(partes[1])
                        probs = {
                            "red_telmex": float(partes[2]),
                            "router_cisco": float(partes[3]),
                            "switch_dist": float(partes[4]),
                            "switch_2960_s1": float(partes[5]),
                            "pc_s1_e1_aislada": float(partes[6])
                        }
                        exito_prolog = True
                        break
            except Exception:
                exito_prolog = False

        if not exito_prolog:
            pe, probs, origen_motor = self.calcular_respaldo_python(pc1, pcr, pc2)

        causa_max = max(probs, key=probs.get) if probs else ""
        self.ultimo_resultado = {
            "pe": pe,
            "probs": probs,
            "origen": origen_motor,
            "causa_max": causa_max,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.actualizar_visualizacion(pc1, pcr, pc2, pe, probs, origen_motor)

    def color_por_probabilidad(self, p, es_max=False):
        if p >= 0.30 or (es_max and p > 0.20):
            return "#ef4444", "#7f1d1d", "#ef4444"  # Rojo Crítico (Causa Raíz Probable)
        elif p >= 0.10:
            return "#f59e0b", "#78350f", "#f59e0b"  # Naranja / Ámbar (Sospechoso Secundario)
        else:
            return "#10b981", "#064e3b", "#10b981"  # Verde (Operativo Normal)

    # -------------------------------------------------------------------------
    # ACTUALIZACIÓN DE INTERFAZ Y RENDERIZADO GRÁFICO
    # -------------------------------------------------------------------------
    def actualizar_visualizacion(self, pc1, pcr, pc2, pe, probs, origen_motor):
        max_prob = max(probs.values()) if probs else 0.0

        # 1. Actualizar Barras de Probabilidad en Tab 1
        for clave, (bar_canvas, lbl_pct) in self.barras.items():
            p = probs[clave]
            lbl_pct.config(text=f"{p * 100:.2f}%")
            bar_canvas.update_idletasks()
            ancho_total = max(bar_canvas.winfo_width(), 260)
            bar_canvas.delete("all")
            es_max = (p == max_prob and p > 0.20)
            color_borde, _, _ = self.color_por_probabilidad(p, es_max=es_max)
            bar_canvas.create_rectangle(0, 0, ancho_total * p, 14, fill=color_borde, width=0)
            lbl_pct.config(fg=color_borde)

        # 2. Dibujar Grafo Bayesiano en Tab 1 con LED y Rutas Reactivas
        self.dibujar_grafo_bayesiano(pc1, pcr, pc2, probs)

        # 3. Dibujar Vista Integral de los 6 Salones en Tab 2
        self.dibujar_vista_6_salones(pc1, pcr, pc2, probs)

        # 4. Actualizar Dictamen y Consola
        causa_max = self.ultimo_resultado["causa_max"]
        nombres_limpios = {
            "red_telmex": "Caída del Proveedor ISP Telmex",
            "router_cisco": "Falla en Router Cisco Perimetral",
            "switch_dist": "Falla en Switch de Distribución Gigabit",
            "switch_2960_s1": "Falla en Switch Cisco 2960 - EEC1 (Lab. Central)",
            "pc_s1_e1_aislada": "Daño Físico Aislado en PC 1 - EEC1 (Cable / NIC)"
        }

        dictamen = (
            f"CAUSA RAÍZ IDENTIFICADA:\n"
            f"👉 {nombres_limpios.get(causa_max, 'N/A')} ({probs.get(causa_max, 0.0)*100:.2f}%)\n\n"
            f"JUSTIFICACIÓN DE INDEPENDENCIA (d-separación):\n"
        )
        if pc2 == "false":
            dictamen += (
                "Dado que el Salón 2 navega con normalidad (PC2=OK), se confirma que el Switch Gigabit "
                "está operativo. Por d-separación, se exonera al 100% al Switch Core, Router Cisco y Telmex "
                "(P = 0.00%), aislando la causa exclusivamente en el Salón 1."
            )
        elif pc2 == "true" and pcr == "true":
            dictamen += (
                "Al confirmarse falla masiva simultánea en múltiples salones (S1 y S2), la evidencia probabilística "
                "se propaga hacia los nodos superiores de la jerarquía (Telmex, Router o Switch Gigabit)."
            )
        else:
            dictamen += (
                "Evaluación bayesiana calculada por enumeración exacta de probabilidad condicional conjunta."
            )
        self.lbl_dictamen.config(text=dictamen)

        # Consola de SWI-Prolog
        self.txt_consola.delete("1.0", tk.END)
        consola_texto = (
            f"[MOTOR INFERENCIAL]: {origen_motor}\n"
            f"?- diagnostico_falla([{pc1}, {pcr}, {pc2}], Resultados).\n"
            f"--------------------------------------------------------------------------------\n"
            f"Probabilidad Marginal P(E) = {pe:.6f} | Evidencia: PC1={pc1}, PCR={pcr}, PC2={pc2}\n"
            f"Aplicación del Teorema de Bayes P(H | E) = P(H, E) / P(E):\n"
            f"  • P(RedTelmex = falla | E)      = {probs['red_telmex']:.6f}  ({probs['red_telmex']*100:.2f}%)\n"
            f"  • P(RouterCisco = falla | E)    = {probs['router_cisco']:.6f}  ({probs['router_cisco']*100:.2f}%)\n"
            f"  • P(SwitchDist = falla | E)     = {probs['switch_dist']:.6f}  ({probs['switch_dist']*100:.2f}%)\n"
            f"  • P(Switch2960_S1 = falla | E)  = {probs['switch_2960_s1']:.6f}  ({probs['switch_2960_s1']*100:.2f}%)\n"
            f"  • P(PC_S1_E1_Aislada | E)       = {probs['pc_s1_e1_aislada']:.6f}  ({probs['pc_s1_e1_aislada']*100:.2f}%)\n"
            f"true."
        )
        self.txt_consola.insert(tk.END, consola_texto)

    # -------------------------------------------------------------------------
    # DIBUJO DEL GRAFO BAYESIANO (TAB 1)
    # -------------------------------------------------------------------------
    def dibujar_grafo_bayesiano(self, pc1, pcr, pc2, probs):
        self.canvas.delete("all")
        max_prob = max(probs.values()) if probs else 0.0

        # Configuración de Nodos: Coordenadas fijas en canvas
        nodos_coords = {
            "red_telmex": (90, 130),
            "router_cisco": (245, 130),
            "switch_dist": (415, 130),
            "switch_2960_s1": (595, 70),
            "switch_2960_s2": (595, 198),
            "pc_s1_e1": (795, 38),
            "pc_s1_resto": (795, 108),
            "pc_s2": (795, 198)
        }

        # Separación estricta: Nodos de Evidencia (PCs) vs Hipótesis / Infraestructura
        nodos_data = {}

        # 1. Nodos de Hipótesis (Infraestructura de Red Core/Borde)
        hipotesis = [
            ("red_telmex", "ISP Telmex\n(RedTelmex)"),
            ("router_cisco", "Router Cisco\n(Perimetral)"),
            ("switch_dist", "Switch Dist.\n(Gigabit Core)")
        ]
        for k, lbl in hipotesis:
            pr = probs.get(k, 0.0)
            es_max = (pr == max_prob and pr > 0.20)
            b, f, led = self.color_por_probabilidad(pr, es_max=es_max)
            nodos_data[k] = {
                "borde": b, "fondo": f, "led": led,
                "texto": f"{lbl}\nP={pr*100:.1f}%",
                "interactivo": False
            }

        upstream_colapsado = (
            probs.get("red_telmex", 0.0) > 0.20 or
            probs.get("router_cisco", 0.0) > 0.20 or
            probs.get("switch_dist", 0.0) > 0.20
        )

        # 2. Switch 2960 EEC1 (Conectividad Real vs Causa Raíz)
        p_s1 = probs.get("switch_2960_s1", 0.0)
        es_causa_raiz_s1 = (p_s1 >= 0.30) or (p_s1 == max_prob and p_s1 > 0.20)

        if pcr == "true":
            # Si las PCs de EEC1 están caídas, NUNCA debe estar en verde ni decir OK
            if es_causa_raiz_s1:
                b_s1, f_s1, led_s1 = "#ef4444", "#7f1d1d", "#ef4444"
                txt_s1 = f"Switch 2960\nEEC1 (Lab. Central)\n[Falla HW: {p_s1*100:.1f}%]"
            else:
                b_s1, f_s1, led_s1 = "#ea580c", "#7c2d12", "#ea580c"
                txt_s1 = f"Switch 2960\nEEC1 (Lab. Central)\n[Sin Upstream: {p_s1*100:.1f}%]"
        elif pcr == "false":
            b_s1, f_s1, led_s1 = "#10b981", "#064e3b", "#10b981"
            txt_s1 = "Switch 2960\nEEC1 (Lab. Central)\n[OPERATIVO]"
        else:  # pcr == "_"
            if es_causa_raiz_s1:
                b_s1, f_s1, led_s1 = "#ef4444", "#7f1d1d", "#ef4444"
                txt_s1 = f"Switch 2960\nEEC1 (Lab. Central)\nP={p_s1*100:.1f}%"
            elif p_s1 >= 0.10:
                b_s1, f_s1, led_s1 = "#f59e0b", "#78350f", "#f59e0b"
                txt_s1 = f"Switch 2960\nEEC1 (Lab. Central)\nP={p_s1*100:.1f}%"
            else:
                b_s1, f_s1, led_s1 = "#64748b", "#1e293b", "#94a3b8"
                txt_s1 = f"Switch 2960\nEEC1 (Lab. Central)\nP={p_s1*100:.1f}%"

        nodos_data["switch_2960_s1"] = {
            "borde": b_s1, "fondo": f_s1, "led": led_s1,
            "texto": txt_s1,
            "interactivo": False
        }

        # 3. Switch 2960 EELR (Conectividad Real)
        if pc2 == "true":
            if upstream_colapsado:
                b_s2, f_s2, led_s2 = "#ea580c", "#7c2d12", "#ea580c"
                txt_s2 = "Switch 2960\nEELR (Lab. Redes)\n[Sin Upstream]"
            else:
                b_s2, f_s2, led_s2 = "#ef4444", "#7f1d1d", "#ef4444"
                txt_s2 = "Switch 2960\nEELR (Lab. Redes)\n[SIN RED]"
        elif pc2 == "false":
            b_s2, f_s2, led_s2 = "#10b981", "#064e3b", "#10b981"
            txt_s2 = "Switch 2960\nEELR (Lab. Redes)\n[OPERATIVO]"
        else:
            b_s2, f_s2, led_s2 = "#64748b", "#1e293b", "#94a3b8"
            txt_s2 = "Switch 2960\nEELR (Lab. Redes)\n[NO VERIFICADO]"

        nodos_data["switch_2960_s2"] = {
            "borde": b_s2, "fondo": f_s2, "led": led_s2,
            "texto": txt_s2,
            "interactivo": False
        }

        # 4. Nodos de Evidencia (PCs) - Coloreado estricto por estado observable
        # PC 1 (EEC1)
        if pc1 == "true":
            b_pc1, f_pc1, led_pc1 = "#ef4444", "#7f1d1d", "#ef4444"
            txt_pc1 = "PC 1 (EEC1)\n[FALLA ACTIVA]"
        elif pc1 == "false":
            b_pc1, f_pc1, led_pc1 = "#10b981", "#064e3b", "#10b981"
            txt_pc1 = "PC 1 (EEC1)\n[OPERATIVO]"
        else:
            b_pc1, f_pc1, led_pc1 = "#64748b", "#1e293b", "#94a3b8"
            txt_pc1 = "PC 1 (EEC1)\n[NO VERIFICADO]"
        nodos_data["pc_s1_e1"] = {"borde": b_pc1, "fondo": f_pc1, "led": led_pc1, "texto": txt_pc1, "interactivo": True}

        # PCs 2..24 (EEC1)
        if pcr == "true":
            b_pcr, f_pcr, led_pcr = "#ef4444", "#7f1d1d", "#ef4444"
            txt_pcr = "PCs 2..24\n(EEC1)\n[FALLA MASIVA]"
        elif pcr == "false":
            b_pcr, f_pcr, led_pcr = "#10b981", "#064e3b", "#10b981"
            txt_pcr = "PCs 2..24\n(EEC1)\n[OPERATIVO]"
        else:
            b_pcr, f_pcr, led_pcr = "#64748b", "#1e293b", "#94a3b8"
            txt_pcr = "PCs 2..24\n(EEC1)\n[NO VERIFICADO]"
        nodos_data["pc_s1_resto"] = {"borde": b_pcr, "fondo": f_pcr, "led": led_pcr, "texto": txt_pcr, "interactivo": True}

        # PCs 1..24 (EELR)
        if pc2 == "true":
            b_pc2, f_pc2, led_pc2 = "#ef4444", "#7f1d1d", "#ef4444"
            txt_pc2 = "PCs 1..24\n(EELR)\n[FALLA]"
        elif pc2 == "false":
            b_pc2, f_pc2, led_pc2 = "#10b981", "#064e3b", "#10b981"
            txt_pc2 = "PCs 1..24\n(EELR)\n[OPERATIVO]"
        else:
            b_pc2, f_pc2, led_pc2 = "#64748b", "#1e293b", "#94a3b8"
            txt_pc2 = "PCs 1..24\n(EELR)\n[NO VERIFICADO]"
        nodos_data["pc_s2"] = {"borde": b_pc2, "fondo": f_pc2, "led": led_pc2, "texto": txt_pc2, "interactivo": True}

        # Aristas de la Red Bayesiana
        aristas = [
            ("red_telmex", "router_cisco"),
            ("router_cisco", "switch_dist"),
            ("switch_dist", "switch_2960_s1"),
            ("switch_dist", "switch_2960_s2"),
            ("switch_2960_s1", "pc_s1_e1"),
            ("switch_2960_s1", "pc_s1_resto"),
            ("switch_2960_s2", "pc_s2")
        ]

        # Dibujar Aristas dirigidas con coloreado estricto
        for origen, destino in aristas:
            x1, y1 = nodos_coords[origen]
            x2, y2 = nodos_coords[destino]

            # La flecha que entra a una PC con falla activa DEBE ser roja
            if destino == "pc_s1_e1":
                color_linea = "#ef4444" if pc1 == "true" else "#475569"
                grosor = 3 if pc1 == "true" else 2
            elif destino == "pc_s1_resto":
                color_linea = "#ef4444" if pcr == "true" else "#475569"
                grosor = 3 if pcr == "true" else 2
            elif destino == "pc_s2":
                color_linea = "#ef4444" if pc2 == "true" else "#475569"
                grosor = 3 if pc2 == "true" else 2
            else:
                p_orig = probs.get(origen, 0.0)
                if p_orig >= 0.30 or (p_orig == max_prob and p_orig > 0.20):
                    color_linea, grosor = "#ef4444", 3
                elif p_orig >= 0.10:
                    color_linea, grosor = "#f59e0b", 2
                else:
                    color_linea, grosor = "#475569", 2

            self.canvas.create_line(x1 + 60, y1, x2 - 60, y2, fill=color_linea, width=grosor, arrow=tk.LAST)

        # Dibujar Tarjetas de Nodos con Indicador LED
        for clave, (x, y) in nodos_coords.items():
            nd = nodos_data[clave]
            # Tarjeta rectangular
            self.canvas.create_rectangle(x - 60, y - 26, x + 60, y + 26, fill=nd["fondo"], outline=nd["borde"], width=2)
            # Círculo LED indicador de estado
            self.canvas.create_oval(x - 52, y - 18, x - 40, y - 6, fill=nd["led"], outline="")
            # Texto de nodo
            self.canvas.create_text(x + 6, y, text=nd["texto"], fill="#f8fafc", font=("Segoe UI", 7, "bold"), justify="center")
            # Indicador de interactividad para las PCs
            if nd["interactivo"]:
                self.canvas.create_text(x + 48, y - 16, text="🖱", fill="#38bdf8", font=("Segoe UI", 8))

    # -------------------------------------------------------------------------
    # DIBUJO DE INFRAESTRUCTURA COMPLETA: 6 SALONES × 24 PCS (TAB 2)
    # -------------------------------------------------------------------------
    def dibujar_vista_6_salones(self, pc1, pcr, pc2, probs):
        self.canvas_campus.delete("all")
        max_prob = max(probs.values()) if probs else 0.0

        upstream_colapsado = (
            probs.get("red_telmex", 0.0) > 0.20 or
            probs.get("router_cisco", 0.0) > 0.20 or
            probs.get("switch_dist", 0.0) > 0.20
        )
        p_s1 = probs.get("switch_2960_s1", 0.0)
        es_causa_raiz_s1 = (p_s1 >= 0.30) or (p_s1 == max_prob and p_s1 > 0.20)

        # =====================================================================
        # 1. BLOQUE DE DISTRIBUCIÓN SUPERIOR: TELMEX -> ROUTER -> SWITCH DIST.
        # =====================================================================
        nodos_core = [
            (140, 32, "ISP Red Telmex (WAN)", probs.get("red_telmex", 0.0)),
            (430, 32, "Router Cisco Borde (Perimetral)", probs.get("router_cisco", 0.0)),
            (720, 32, "Switch Dist. Gigabit (Core)", probs.get("switch_dist", 0.0))
        ]
        for x, y, texto, pr in nodos_core:
            b, f, led = self.color_por_probabilidad(pr, es_max=(pr == max_prob and pr > 0.20))
            self.canvas_campus.create_rectangle(x - 70, y - 18, x + 70, y + 18, fill=f, outline=b, width=2)
            self.canvas_campus.create_oval(x - 62, y - 12, x - 52, y - 2, fill=led, outline="")
            self.canvas_campus.create_text(x + 6, y, text=f"{texto}\nP={pr*100:.1f}%", fill="#f8fafc", font=("Segoe UI", 7, "bold"))

        # Enlaces troncales WAN/Core
        col_t_r = "#ef4444" if probs.get("red_telmex", 0.0) >= 0.30 else "#475569"
        wid_t_r = 3 if probs.get("red_telmex", 0.0) >= 0.30 else 2
        self.canvas_campus.create_line(210, 32, 360, 32, fill=col_t_r, width=wid_t_r, arrow=tk.LAST)

        col_r_s = "#ef4444" if probs.get("router_cisco", 0.0) >= 0.30 else "#475569"
        wid_r_s = 3 if probs.get("router_cisco", 0.0) >= 0.30 else 2
        self.canvas_campus.create_line(500, 32, 650, 32, fill=col_r_s, width=wid_r_s, arrow=tk.LAST)

        # =====================================================================
        # 2. CONTORNO ARQUITECTÓNICO DEL EDIFICIO DE SISTEMAS ITSX
        # =====================================================================
        # Muro exterior perimetral
        self.canvas_campus.create_rectangle(30, 70, 830, 615, fill="#090d16", outline="#334155", width=3)
        self.canvas_campus.create_text(
            430, 84,
            text="🏛️ PLANO ARQUITECTÓNICO REAL - EDIFICIO DE INGENIERÍA EN SISTEMAS COMPUTACIONALES (ITSX)",
            fill="#38bdf8", font=("Segoe UI", 8, "bold")
        )

        # =====================================================================
        # 3. LÍNEAS TRONCALES DESDE EL SWITCH GIGABIT HACIA LOS SALONES
        # =====================================================================
        col_troncal = "#ef4444" if probs.get("switch_dist", 0.0) >= 0.30 else ("#ea580c" if upstream_colapsado else "#38bdf8")
        wid_troncal = 3 if (probs.get("switch_dist", 0.0) >= 0.30 or upstream_colapsado) else 2

        # Troncal horizontal superior (y = 62)
        self.canvas_campus.create_line(720, 50, 720, 62, fill=col_troncal, width=wid_troncal)
        self.canvas_campus.create_line(165, 62, 720, 62, fill=col_troncal, width=wid_troncal)

        # Bajadas a salones superiores
        self.canvas_campus.create_line(165, 62, 165, 100, fill=col_troncal, width=wid_troncal, arrow=tk.LAST)
        self.canvas_campus.create_line(430, 62, 430, 100, fill=col_troncal, width=wid_troncal, arrow=tk.LAST)
        col_drop_s1 = "#ef4444" if (pcr == "true" and es_causa_raiz_s1) else col_troncal
        self.canvas_campus.create_line(695, 62, 695, 100, fill=col_drop_s1, width=wid_troncal, arrow=tk.LAST)

        # Ductos verticales de cableado en pasillos
        # Ducto Oeste (x = 297, baja a EEC4 y Site)
        self.canvas_campus.create_line(297, 62, 297, 475, fill=col_troncal, width=wid_troncal)
        self.canvas_campus.create_line(297, 325, 285, 325, fill=col_troncal, width=wid_troncal, arrow=tk.LAST)
        self.canvas_campus.create_line(297, 475, 285, 475, fill=col_troncal, width=wid_troncal, arrow=tk.LAST)

        # Ducto Este (x = 562, baja a EELR y EEAV)
        self.canvas_campus.create_line(562, 62, 562, 475, fill=col_troncal, width=wid_troncal)
        col_drop_s2 = "#ef4444" if (pc2 == "true" and not upstream_colapsado) else col_troncal
        self.canvas_campus.create_line(562, 325, 575, 325, fill=col_drop_s2, width=wid_troncal, arrow=tk.LAST)
        self.canvas_campus.create_line(562, 475, 575, 475, fill=col_troncal, width=wid_troncal, arrow=tk.LAST)

        # =====================================================================
        # 4. ELEMENTOS ARQUITECTÓNICOS CENTRALES Y ACCESOS
        # =====================================================================
        # Pasillo Central y Vestíbulo
        self.canvas_campus.create_rectangle(310, 410, 550, 480, fill="#0f172a", outline="#334155")
        self.canvas_campus.create_text(
            430, 445,
            text="PASILLO CENTRAL Y VESTÍBULO\n(Circulación hacia Laboratorios)",
            fill="#64748b", font=("Segoe UI", 7, "bold"), justify="center"
        )

        # Cubículos de Profesores (Dos bloques en el pasillo central)
        self.canvas_campus.create_rectangle(310, 255, 550, 320, fill="#1e293b", outline="#475569", width=2)
        self.canvas_campus.create_text(
            430, 287,
            text="🏢 CUBÍCULOS DE PROFESORES\n(Sector Académico Norte)",
            fill="#cbd5e1", font=("Segoe UI", 7, "bold"), justify="center"
        )

        self.canvas_campus.create_rectangle(310, 330, 550, 395, fill="#1e293b", outline="#475569", width=2)
        self.canvas_campus.create_text(
            430, 362,
            text="🏢 CUBÍCULOS DE PROFESORES\n(Sector Académico Sur)",
            fill="#cbd5e1", font=("Segoe UI", 7, "bold"), justify="center"
        )

        # Site de Telecomunicaciones & NOC (Sector Inferior Izquierdo)
        self.canvas_campus.create_rectangle(45, 410, 285, 550, fill="#0f172a", outline="#334155", width=2)
        self.canvas_campus.create_rectangle(49, 414, 281, 432, fill="#1e293b", outline="#334155")
        self.canvas_campus.create_text(
            165, 423,
            text="🏛️ SITE CENTRAL & NOC ITSX (Core)",
            fill="#38bdf8", font=("Segoe UI", 7, "bold")
        )
        self.canvas_campus.create_rectangle(55, 436, 275, 542, fill="#1e293b", outline="#475569", width=2)
        unidades_rack = [
            ("U1: Patch Panel Cat6 (Troncales Salones)", "#10b981" if not upstream_colapsado else "#ea580c"),
            ("U2: Switch Gigabit Core 24p 10G Uplink", "#10b981" if probs.get("switch_dist", 0.0) < 0.20 else "#ef4444"),
            ("U3: Gateway ITSX / DNS / DHCP / Firewall", "#10b981" if probs.get("router_cisco", 0.0) < 0.20 else "#ef4444"),
            ("U4: Banco Baterías Online Smart-UPS", "#10b981")
        ]
        for idx_u, (u_text, u_col) in enumerate(unidades_rack):
            uy = 442 + idx_u * 25
            self.canvas_campus.create_rectangle(60, uy, 270, uy + 21, fill="#090d16", outline="#334155")
            self.canvas_campus.create_oval(66, uy + 6, 74, uy + 14, fill=u_col, outline="")
            self.canvas_campus.create_text(80, uy + 10, text=u_text, anchor="w", fill="#cbd5e1", font=("Segoe UI", 6, "bold"))

        # Acceso Principal al Edificio (Abajo al centro)
        self.canvas_campus.create_rectangle(335, 490, 525, 550, fill="#1e293b", outline="#38bdf8", width=2)
        self.canvas_campus.create_text(
            430, 520,
            text="🚪 ENTRADA SISTEMAS\n(Acceso Principal al Edificio)",
            fill="#38bdf8", font=("Segoe UI", 8, "bold"), justify="center"
        )
        self.canvas_campus.create_line(430, 550, 430, 570, fill="#38bdf8", width=2, arrow=tk.FIRST)

        # =====================================================================
        # 5. DIBUJO DE LOS 6 LABORATORIOS (24 COMPUTADORAS EN MATRIZ 4×6 C/U)
        # =====================================================================
        laboratorios = [
            # 1. Sector Superior Izquierdo: EEC3
            {
                "codigo": "EEC3",
                "titulo": "EEC3 (Lab. Cómputo 3 - 24 PCs)",
                "x1": 45, "y1": 100, "x2": 285, "y2": 240,
                "es_s1": False, "es_s2": False
            },
            # 2. Sector Superior Central: EEC2
            {
                "codigo": "EEC2",
                "titulo": "EEC2 (Lab. Cómputo 2 - 24 PCs)",
                "x1": 310, "y1": 100, "x2": 550, "y2": 240,
                "es_s1": False, "es_s2": False
            },
            # 3. Sector Superior Derecho: EEC1 (Salón 1 Bayesiano)
            {
                "codigo": "EEC1",
                "titulo": "EEC1 (Salón 1 / Lab. Central - 24 PCs)",
                "x1": 575, "y1": 100, "x2": 815, "y2": 240,
                "es_s1": True, "es_s2": False
            },
            # 4. Sector Medio Izquierdo: EEC4
            {
                "codigo": "EEC4",
                "titulo": "EEC4 (Lab. Cómputo 4 - 24 PCs)",
                "x1": 45, "y1": 255, "x2": 285, "y2": 395,
                "es_s1": False, "es_s2": False
            },
            # 5. Sector Medio Derecho: EELR (Salón 2 Bayesiano)
            {
                "codigo": "EELR",
                "titulo": "EELR (Salón 2 / Lab. Redes - 24 PCs)",
                "x1": 575, "y1": 255, "x2": 815, "y2": 395,
                "es_s1": False, "es_s2": True
            },
            # 6. Sector Inferior Derecho: EEAV
            {
                "codigo": "EEAV",
                "titulo": "EEAV (Lab. Audiovisual - 24 PCs)",
                "x1": 575, "y1": 410, "x2": 815, "y2": 550,
                "es_s1": False, "es_s2": False
            }
        ]

        for lab in laboratorios:
            lx1, ly1, lx2, ly2 = lab["x1"], lab["y1"], lab["x2"], lab["y2"]
            es_s1 = lab["es_s1"]
            es_s2 = lab["es_s2"]

            # Contorno de la sala
            self.canvas_campus.create_rectangle(lx1, ly1, lx2, ly2, fill="#0f172a", outline="#334155", width=2)

            # Barra de título del laboratorio
            self.canvas_campus.create_rectangle(lx1 + 3, ly1 + 3, lx2 - 3, ly1 + 22, fill="#1e293b", outline="#334155")
            color_titulo = "#38bdf8" if (es_s1 or es_s2) else "#94a3b8"
            self.canvas_campus.create_text(
                lx1 + 120, ly1 + 12,
                text=lab["titulo"],
                fill=color_titulo,
                font=("Segoe UI", 7, "bold")
            )

            # Determinar estado del Switch Cisco 2960 y PCs del laboratorio
            if es_s1:
                # Laboratorio EEC1 (Salón 1)
                if pcr == "true":
                    if es_causa_raiz_s1:
                        borde_sw, fondo_sw, led_sw = "#ef4444", "#7f1d1d", "#ef4444"
                        sw_tag = "Switch 2960 (Falla de Hardware / Causa Raíz)"
                    else:
                        borde_sw, fondo_sw, led_sw = "#ea580c", "#7c2d12", "#ea580c"
                        sw_tag = "Switch 2960 (Sin Enlace Upstream)"
                elif pcr == "false":
                    borde_sw, fondo_sw, led_sw = "#10b981", "#064e3b", "#10b981"
                    sw_tag = "Switch 2960 (OK - 1 Gbps)"
                else:
                    borde_sw, fondo_sw, led_sw = self.color_por_probabilidad(p_s1, es_max=es_causa_raiz_s1)
                    sw_tag = f"Switch 2960 (P={p_s1*100:.1f}%)"
            elif es_s2:
                # Laboratorio EELR (Salón 2)
                if pc2 == "true":
                    if upstream_colapsado:
                        borde_sw, fondo_sw, led_sw = "#ea580c", "#7c2d12", "#ea580c"
                        sw_tag = "Switch 2960 (Sin Enlace Upstream)"
                    else:
                        borde_sw, fondo_sw, led_sw = "#ef4444", "#7f1d1d", "#ef4444"
                        sw_tag = "Switch 2960 (Sin Red)"
                elif pc2 == "false":
                    borde_sw, fondo_sw, led_sw = "#10b981", "#064e3b", "#10b981"
                    sw_tag = "Switch 2960 (OK - 1 Gbps)"
                else:
                    borde_sw, fondo_sw, led_sw = "#64748b", "#1e293b", "#94a3b8"
                    sw_tag = "Switch 2960"
            else:
                # Salones EEC2, EEC3, EEC4, EEAV
                if upstream_colapsado:
                    borde_sw, fondo_sw, led_sw = "#ea580c", "#7c2d12", "#ea580c"
                    sw_tag = "Switch 2960 (Sin Enlace Upstream)"
                else:
                    borde_sw, fondo_sw, led_sw = "#10b981", "#064e3b", "#10b981"
                    sw_tag = "Switch 2960 (OK - 1 Gbps)"

            # Tarjeta de Switch Cisco 2960
            self.canvas_campus.create_rectangle(lx1 + 6, ly1 + 25, lx2 - 6, ly1 + 47, fill=fondo_sw, outline=borde_sw, width=2)
            self.canvas_campus.create_oval(lx1 + 12, ly1 + 31, lx1 + 22, ly1 + 41, fill=led_sw, outline="")
            self.canvas_campus.create_text(
                lx1 + 28, ly1 + 36,
                text=sw_tag,
                anchor="w",
                fill="#f8fafc",
                font=("Segoe UI", 6, "bold")
            )

            # Matriz 4×6 de Computadoras (24 PCs c/u)
            for row in range(4):
                for col in range(6):
                    pc_idx = row * 6 + col
                    px1 = lx1 + 16 + col * 36
                    py1 = ly1 + 52 + row * 18
                    px2 = px1 + 28
                    py2 = py1 + 13

                    # Asignar color según estado individual de la PC
                    if es_s1:
                        if pcr == "true":
                            pc_color = "#ef4444"
                        elif pc_idx == 0:
                            pc_color = "#ef4444" if pc1 == "true" else "#10b981"
                        elif pcr == "false":
                            pc_color = "#10b981"
                        else:
                            pc_color = "#64748b"
                    elif es_s2:
                        if pc2 == "true":
                            pc_color = "#ef4444"
                        elif pc2 == "false":
                            pc_color = "#10b981"
                        else:
                            pc_color = "#64748b"
                    else:
                        if upstream_colapsado:
                            pc_color = "#ea580c"
                        else:
                            pc_color = "#10b981"

                    self.canvas_campus.create_rectangle(px1, py1, px2, py2, fill=pc_color, outline="#090d16", width=1)
                    self.canvas_campus.create_text(
                        px1 + 14, py1 + 6,
                        text=str(pc_idx + 1),
                        fill="#ffffff",
                        font=("Segoe UI", 6, "bold")
                    )

            # Etiqueta de pie de sala
            self.canvas_campus.create_text(
                lx1 + 120, ly1 + 130,
                text="24 PCs • Conectividad LAN Gigabit",
                fill="#64748b",
                font=("Segoe UI", 6)
            )

        # =====================================================================
        # 6. NOTAS AL PIE DEL PLANO ARQUITECTÓNICO
        # =====================================================================
        self.canvas_campus.create_text(
            430, 580,
            text="Demostración de d-Separación: Cuando Switch Gigabit Core está operativo (SD=OK), aísla formalmente a los salones restantes del campus.",
            fill="#38bdf8", font=("Segoe UI", 8, "italic")
        )
        self.canvas_campus.create_text(
            430, 600,
            text="Croquis Físico: Edificio de Sistemas ITSX • 6 Laboratorios × 24 PCs = 144 PCs Monitoreadas en Tiempo Real",
            fill="#94a3b8", font=("Segoe UI", 7)
        )

    # -------------------------------------------------------------------------
    # GENERACIÓN Y EXPORTACIÓN DE DICTAMEN TÉCNICO (.TXT)
    # -------------------------------------------------------------------------
    def exportar_dictamen(self):
        res = self.ultimo_resultado
        if not res["probs"]:
            messagebox.showwarning("Atención", "Ejecute una inferencia antes de exportar el dictamen.")
            return

        pc1 = self.var_pc1.get()
        pcr = self.var_pcr.get()
        pc2 = self.var_pc2.get()
        pe = res["pe"]
        probs = res["probs"]
        causa_max = res["causa_max"]

        nombres_limpios = {
            "red_telmex": "Caída del Proveedor ISP Telmex",
            "router_cisco": "Falla en Router Cisco Perimetral",
            "switch_dist": "Falla en Switch de Distribución Gigabit",
            "switch_2960_s1": "Falla en Switch Cisco 2960 - EEC1 (Lab. Central)",
            "pc_s1_e1_aislada": "Daño Físico Aislado en PC 1 - EEC1 (Cable / NIC)"
        }

        justificacion = (
            "El Lab. Redes EELR navega con normalidad (PC2=OK), lo cual confirma que el Switch de Distribución Gigabit\n"
            "está plenamente operativo. Por el principio de d-separación (independencia condicional en DAGs),\n"
            "la falla en EEC1 queda estrictamente aislada en el Switch Cisco 2960 local, descartando al\n"
            "100% (P=0.00%) cualquier compromiso en el Switch de Distribución, Router Cisco o enlace Telmex."
            if pc2 == "false" else
            "Se detectan afectaciones simultáneas en múltiples laboratorios, por lo que la probabilidad posterior se\n"
            "propaga hacia los equipos de agregación y borde (Switch Gigabit, Router Cisco o enlace Telmex)."
        )

        recomendacion = (
            "1. Inspeccionar el Switch Cisco 2960 de EEC1 (Lab. Central) (Reinicio eléctrico / verificación de puertos).\n"
            "2. Validar el enlace uplink entre el Switch 2960 de EEC1 y el Switch de Distribución Gigabit.\n"
            "3. No es necesario intervenir el Router perimetral ni levantar ticket con el ISP Telmex."
            if causa_max == "switch_2960_s1" else
            f"1. Proceder con el protocolo de soporte técnico enfocado en: {nombres_limpios.get(causa_max, causa_max)}."
        )

        reporte = f"""================================================================================
INSTITUTO TECNOLÓGICO SUPERIOR DE XALAPA (ITSX)
DIVISIÓN DE INGENIERÍA EN SISTEMAS COMPUTACIONALES
CENTRO DE OPERACIONES DE RED (NOC) - SISTEMA EXPERTO BAYESIANO
ASIGNATURA: Inteligencia Artificial (SCC-1012)
DOCENTE: Francisco Javier Torres Vera
================================================================================
FECHA Y HORA DE EMISIÓN: {res['timestamp']}
MOTOR INFERENCIAL ACTIVO: {res['origen']}

1. EVIDENCIA OBSERVADA (VECTOR DE SÍNTOMAS)
--------------------------------------------------------------------------------
• PC 1 - Lab. Central (EEC1):          {pc1} ({'Falla' if pc1=='true' else 'OK'})
• Resto Lab. Central EEC1 (23 PCs):    {pcr} ({'Falla Masiva' if pcr=='true' else ('OK' if pcr=='false' else 'No Verificado')})
• Equipos Lab. Redes EELR (Salón 2):   {pc2} ({'Falla' if pc2=='true' else ('OK' if pc2=='false' else 'No Verificado')})
• Probabilidad Marginal de Evidencia:  P(E) = {pe:.6f}

2. COMANDO EJECUTADO EN SWI-PROLOG
--------------------------------------------------------------------------------
?- consulta_gui({pc1}, {pcr}, {pc2}).
?- diagnostico_falla([{pc1}, {pcr}, {pc2}], Resultados).

3. PROBABILIDAD POSTERIOR DE CAUSA RAÍZ P(Hipótesis | Evidencia)
--------------------------------------------------------------------------------
• ISP Red Telmex:                     {probs.get('red_telmex', 0.0):.6f} ({probs.get('red_telmex', 0.0)*100:6.2f}%)
• Router Cisco Perimetral:            {probs.get('router_cisco', 0.0):.6f} ({probs.get('router_cisco', 0.0)*100:6.2f}%)
• Switch Distribución Gigabit:        {probs.get('switch_dist', 0.0):.6f} ({probs.get('switch_dist', 0.0)*100:6.2f}%)
• Switch Cisco 2960 - EEC1:          {probs.get('switch_2960_s1', 0.0):.6f} ({probs.get('switch_2960_s1', 0.0)*100:6.2f}%)
• Daño Físico Aislado PC 1 (EEC1):   {probs.get('pc_s1_e1_aislada', 0.0):.6f} ({probs.get('pc_s1_e1_aislada', 0.0)*100:6.2f}%)

4. DICTAMEN TÉCNICO Y CAUSA RAÍZ
--------------------------------------------------------------------------------
CAUSA RAÍZ IDENTIFICADA: {nombres_limpios.get(causa_max, causa_max).upper()}
PROBABILIDAD ASIGNADA:  {probs.get(causa_max, 0.0)*100:.2f}%

FUNDAMENTACIÓN FORMAL DE INDEPENDENCIA CONDICIONAL:
{justificacion}

5. RECOMENDACIÓN OPERATIVA PARA SOPORTE DE RED:
{recomendacion}
================================================================================
Dictamen emitido automáticamente por el Sistema Experto Bayesiano ITSX.
"""

        nombre_defecto = f"dictamen_noc_itsx_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        ruta_archivo = filedialog.asksaveasfilename(
            parent=self.root,
            title="Guardar Dictamen Técnico NOC",
            defaultextension=".txt",
            initialfile=nombre_defecto,
            filetypes=[("Archivos de Texto", "*.txt"), ("Todos los Archivos", "*.*")]
        )

        if ruta_archivo:
            try:
                with open(ruta_archivo, "w", encoding="utf-8") as f:
                    f.write(reporte)
                messagebox.showinfo("Reporte Exportado", f"Dictamen técnico guardado exitosamente en:\n{ruta_archivo}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaExpertoNOC(root)
    root.mainloop()