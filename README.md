# Solucionador Numérico: Método de Punto Fijo
> **Análisis Numérico — Programa de Solución de Ecuaciones No Lineales (Punto 5)**  
> Desarrollado en Python 3 con interfaz gráfica interactiva (Tkinter), visualización científica (Matplotlib) y motor de cálculo modular.

---

## 👥 Integrantes
- **Juan Manuel Gongora** — Código: `2357650` — Grupo: `2724`
- **Cristian David Alvarez** — Código: `2451034` — Grupo: `2724`

---

## 📌 Enunciado del Problema
> *(35%) Escriba un programa de computador (en el lenguaje de su preferencia) que permita encontrar una solución para una función no lineal utilizando el método de punto fijo.*

Esta aplicación permite encontrar la solución numérica para **cualquier función no lineal arbitraria** introducida por el usuario, analizando el comportamiento iterativo paso a paso, la convergencia/divergencia mediante la derivada numérica $|g'(x)|$ y generando gráficas interactivas.

---

## 🚀 Paso a Paso: 3 Formas de Ejecutar y Probar la Aplicación

Existen tres formas distintas de ejecutar el software para verificar su funcionamiento y validar matemáticamente los resultados:

---

### Método 1: Prueba Automática de Código (Verificación Matemática)
Esta opción es la más rápida y formal para certificar que el motor de cálculo, el parser de funciones y los criterios de error están funcionando al 100%.

1. Abre una terminal (PowerShell, CMD o la terminal de VS Code) en la carpeta del proyecto.
2. Ejecuta el comando de pruebas unitarias:
   ```bash
   python -m unittest test_punto_fijo.py
   ```
3. **Resultado esperado:**
   ```text
   ......
   ----------------------------------------------------------------------
   Ran 6 tests in 0.003s

   OK
   ```
   - Cada punto (`.`) indica una prueba exitosa (evaluación segura, multiplicación implícita como `5x`, convergencia cuadrática, cálculo de derivadas $|g'(x)| < 1$, detección de divergencia y funciones trascendentes). El mensaje `OK` confirma la validez matemática del algoritmo.

---

### Método 2: Aplicación Gráfica Interactiva (GUI Recomendada)
Ofrece una interfaz de usuario completa con gráficos en tiempo real, tabla de iteraciones y exportación de datos.

1. **Cómo iniciarla:**
   - **Opción Rápida (Windows):** Haz doble clic en el archivo **`ejecutar.bat`**.
   - **Opción Terminal:** Ejecuta en la consola:
     ```bash
     python main.py
     ```
2. **Paso a paso para probarla dentro de la interfaz:**
   - **Cálculo Directo:** Al abrirse, ya incluye una función cargada por defecto ($x = \cos(x)$). Haz clic en el botón azul **`▶ CALCULAR SOLUCIÓN`**.
     - Observa cómo las tarjetas superiores se actualizan inmediatamente con la **Raíz aproximada** ($x^* \approx 0.73908482$), el número de iteraciones, el error final y la confirmación de contracción **`|g'| < 1`**.
     - En el lado derecho se genera el **Diagrama de Telaraña (Cobweb Plot)** con la trayectoria en escalera hacia la recta $y = x$, y al lado la **Curva Semilogarítmica del Error**.
   - **Revisar la Tabla:** Haz clic en la pestaña **`📋 Tabla de Iteraciones`** para ver cada paso con su valor de $x_k$, $x_{k+1}$, error absoluto, error relativo porcentual y $|g'(x_k)|$.
   - **Exportar Datos:** Usa el botón **`💾 Exportar a CSV`** para guardar la tabla en formato compatible con Excel, o **`📋 Copiar al Portapapeles`** para pegarla en un informe.
   - **Probar otras funciones:** Selecciona cualquier otro ejemplo del menú desplegable superior (ej. *Función Exponencial*, *Polinomio Cúbico* o *Demostración de Divergencia*), o escribe tu propia función en el campo **`Función g(x)`** (ejemplo: `sqrt(2*x + 3)` o `exp(-x)`).

---

### Método 3: Modo Consola / Terminal (CLI)
Ideal para entornos sin entorno gráfico o ejecución por comandos directos.

- **Modo interactivo paso a paso por teclado:**
  ```bash
  python main.py --cli
  ```
  El programa solicitará la función $g(x)$, la aproximación inicial $x_0$ y la tolerancia directamente en la terminal e imprimirá la tabla de resultados.

- **Ejecución directa por parámetros en una sola línea:**
  ```bash
  python main.py --g "cos(x)" --x0 0.5 --tol 1e-6
  python main.py --g "exp(-x)" --x0 0.5 --tol 1e-6
  python main.py --g "sqrt(2*x + 3)" --x0 1.0 --tol 1e-6
  ```

---

## 📐 Fundamento Matemático del Método

Dada una ecuación no lineal general:
$$f(x) = 0$$

El **Método de Punto Fijo** consiste en transformarla algebraicamente en una ecuación equivalente de la forma:
$$x = g(x)$$

A partir de un valor inicial $x_0$, se genera la sucesión recursiva:
$$x_{k+1} = g(x_k), \quad k = 0, 1, 2, \dots$$

Geométricamente, la solución o punto fijo $x^*$ es la abscisa donde la curva $y = g(x)$ se intersecta con la recta identidad $y = x$.

### Teorema de Convergencia (Punto Fijo de Banach)
Para asegurar que la sucesión iterativa converja a la raíz en un intervalo $[a, b]$, la función $g(x)$ debe ser contractiva, lo que se verifica mediante su derivada:
$$|g'(x)| < 1 \quad \forall x \in [a, b]$$

- **Si $|g'(x^*)| < 1$**: El punto fijo es **atractor** (el método converge hacia la raíz).
- **Si $|g'(x^*)| > 1$**: El punto fijo es **repulsor** (el método diverge y se aleja de la raíz).
- **Si $0 < g'(x^*) < 1$**: Convergencia monótona en escalera (*staircase*).
- **Si $-1 < g'(x^*) < 0$**: Convergencia oscilatoria alternada en espiral (*cobweb*).

### Criterios de Parada Implementados
1. **Error Absoluto:**
   $$E_a = |x_{k+1} - x_k| \le \text{Tol}$$
2. **Error Relativo Porcentual:**
   $$E_r(\%) = \frac{|x_{k+1} - x_k|}{|x_{k+1}|} \times 100\% \le \text{Tol}$$
3. **Límite de Iteraciones:** $k = N_{\max}$
4. **Detección Automática de Divergencia:** Si $|x| > 10^{14}$ o los errores crecen exponencialmente.

---

## ✨ Características de la Aplicación

1. **Entrada Flexible de Funciones:**
   - Permite ingresar cualquier expresión no lineal $g(x)$ (y opcionalmente $f(x)$ para verificar residual).
   - Soporta multiplicación implícita (`5x` $\to$ `5*x`, `2cos(x)` $\to$ `2*cos(x)`).
   - Soporta potencias con `^` o `**`.
   - Funciones matemáticas reconocidas: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sinh`, `cosh`, `tanh`, `exp`, `log`, `ln`, `sqrt`, `cbrt`, `abs`, y constantes `pi`, `e`.
2. **Visualización Gráfica Científica (Matplotlib integrado):**
   - **Diagrama de Telaraña (Cobweb Plot):** Muestra la curva $y=g(x)$, la recta $y=x$, la trayectoria paso a paso y el punto fijo final.
   - **Curva Semilogarítmica del Error:** Muestra cómo disminuye el error en cada iteración frente a la línea de tolerancia.
3. **Tabla de Iteraciones:**
   - Columnas detalladas: Iteración ($k$), $x_k$, $x_{k+1} = g(x_k)$, Error Absoluto, Error Relativo %, $|g'(x_k)|$ y residual $f(x_{k+1})$.
   - **Exportación a CSV / Excel**: Guarda el informe tabular en un archivo `.csv`.
   - **Copiar al Portapapeles**: Listo para pegar en Word, Excel o informes académicos.
4. **Ejemplos Preconfigurados:**
   - Menú desplegable con 5 casos didácticos clásicos (funciones trigonométricas, exponenciales, cuadráticas contractivas y casos de divergencia).

---

## 📁 Estructura del Proyecto

```
Parcial de analisis numerico/
│
├── main.py               # Punto de entrada principal (inicia GUI o CLI)
├── app_gui.py            # Interfaz gráfica interactiva con gráficos Matplotlib
├── punto_fijo.py         # Motor de cálculo del Método de Punto Fijo
├── test_punto_fijo.py    # Pruebas unitarias automatizadas
├── ejecutar.bat          # Acceso directo para ejecutar en Windows con doble clic
├── .gitignore            # Exclusión de archivos temporales de Git
└── README.md             # Documentación técnica, integrantes y guía de uso
```
