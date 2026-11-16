# Centro de Operaciones de Seguridad · SOC

*Sistema Experto de Producción & Búsqueda BFS — ITSX*

## Descripción General

Este proyecto implementa un **Sistema Experto Híbrido** orientado al diagnóstico inteligente de incidentes y fallas en infraestructura de red y operaciones de seguridad/conectividad (**SOC / NOC**). La solución combina razonamiento lógico-probabilístico en **SWI-Prolog** con una interfaz gráfica interactiva de escritorio y un orquestador en **Python** con exploración del espacio de estados mediante **Búsqueda en Anchura (BFS)**.

## Arquitectura Híbrida

El sistema se divide en dos capas desacopladas que se comunican mediante un puente de ejecución de procesos:

1. **Motor de Inferencia Lógica (`sistema_experto_red.pl`)**
   - Implementado en **SWI-Prolog** mediante reglas de producción y cláusulas de Horn.
   - Evalúa la base de conocimiento con encadenamiento hacia adelante y hacia atrás sobre la topología de red y tablas de probabilidad condicional (CPT).
   - Expone el predicado puente `consulta_gui/3` para devolver diagnósticos estructurados hacia la capa de presentación.

2. **Orquestador, Búsqueda BFS e Interfaz Gráfica (`app_diagnostico_noc.py`)**
   - Desarrollado en **Python 3** con interfaz de escritorio nativa en `tkinter` (sin dependencias externas de UI).
   - Orquesta las consultas hacia el motor Prolog y cuenta con un motor de respaldo matemático en Python para garantizar continuidad operativa.
   - Incorpora exploración de espacio de estados mediante **Búsqueda en Anchura (BFS)**, visualización interactiva de nodos en tiempo real, inspección de probabilidades/CPTs y exportación de reportes técnicos en `.txt`.

## Requisitos Previos

- **Python 3.x** (con `tkinter` incluido en la instalación estándar).
- **SWI-Prolog** instalado y accesible en el `PATH` del sistema (comando `swipl`).
- *(Opcional)* `pyswip` si se desea extender la integración nativa en entornos compatibles.

## Ejecución Local

1. Clona o descarga el repositorio en tu entorno local (previa autorización del autor).
2. Asegúrate de que `swipl` esté disponible en la terminal:
   ```bash
   swipl --version
   ```
3. Ejecuta la aplicación principal desde la raíz del proyecto:
   ```bash
   python app_diagnostico_noc.py
   ```

## Autoría y Derechos de Autor

- **Autor:** Angel Gabriel Castillo Castillo
- **Año:** 2026
- **Licencia:** Licencia Propietaria — Todos los Derechos Reservados (ver archivo [`LICENSE`](./LICENSE)).

Este código se publica únicamente con fines de visualización y portafolio profesional. Queda estrictamente prohibida su copia, modificación, distribución o uso académico/comercial sin autorización expresa y por escrito del autor.
