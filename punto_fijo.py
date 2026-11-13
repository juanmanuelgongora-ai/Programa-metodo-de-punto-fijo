"""
Módulo de Cálculo: Método de Punto Fijo
Análisis Numérico - Solución de Ecuaciones No Lineales

Este módulo implementa el algoritmo iterativo de Punto Fijo:
    x_{k+1} = g(x_k)
para resolver ecuaciones de la forma f(x) = 0 reescritas como x = g(x).
"""

import ast
import math
import re
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple, Union
import numpy as np


# Nombres matemáticos seguros permitidos
SAFE_NAMES = {
    'x', 'pi', 'e',
    'sin', 'cos', 'tan',
    'asin', 'acos', 'atan',
    'sinh', 'cosh', 'tanh',
    'exp', 'log', 'log10', 'log2', 'ln',
    'sqrt', 'abs', 'cbrt'
}

# Nodos sintácticos AST permitidos para evaluación segura
ALLOWED_AST_NODES = {
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
    ast.Name, ast.Call, ast.Load, ast.Add, ast.Sub,
    ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.USub, ast.UAdd
}

# Funciones y constantes matemáticas estándar (escalares)
MATH_ENV: Dict[str, Union[float, Callable]] = {
    'pi': math.pi,
    'e': math.e,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'asin': math.asin,
    'acos': math.acos,
    'atan': math.atan,
    'sinh': math.sinh,
    'cosh': math.cosh,
    'tanh': math.tanh,
    'exp': math.exp,
    'log': math.log,
    'log10': math.log10,
    'log2': math.log2,
    'ln': math.log,
    'sqrt': math.sqrt,
    'abs': abs,
    'cbrt': lambda v: math.copysign(abs(v)**(1.0/3.0), v),
}

# Funciones y constantes matemáticas para NumPy (vectorizadas)
NUMPY_ENV: Dict[str, Union[float, Callable]] = {
    'pi': np.pi,
    'e': np.e,
    'sin': np.sin,
    'cos': np.cos,
    'tan': np.tan,
    'asin': np.arcsin,
    'acos': np.arccos,
    'atan': np.arctan,
    'sinh': np.sinh,
    'cosh': np.cosh,
    'tanh': np.tanh,
    'exp': np.exp,
    'log': np.log,
    'log10': np.log10,
    'log2': np.log2,
    'ln': np.log,
    'sqrt': np.sqrt,
    'abs': np.abs,
    'cbrt': np.cbrt,
}


def sanitize_expression(expr: str) -> str:
    """
    Limpia y transforma la expresión matemática ingresada por el usuario
    en una sintaxis válida de Python:
      - Reemplaza '^' por '**'
      - Reemplaza 'ln(' por 'log('
      - Soporta multiplicación implícita: 5x -> 5*x, 3(x) -> 3*(x), etc.
      - Preserva notación científica (ej: 1e-4, 2.5E+3)
    """
    s = expr.strip()
    if not s:
        raise ValueError("La expresión matemática no puede estar vacía.")

    # Reemplazar potencias
    s = s.replace('^', '**')

    # Reemplazar ln por log si está como palabra completa
    s = re.sub(r'\bln\b', 'log', s)

    # Multiplicación implícita:
    # 1. Dígito seguido de letra (excepto 'e' o 'E' en notación científica como 1e-5 o 2E3)
    # Ejemplo: 5x -> 5*x, 2cos(x) -> 2*cos(x)
    s = re.sub(r'(?<=\d)(?=[a-df-zA-DF-Z\(])|(?<=\d)(?:e|E)(?![+\-]?\d)', '*\\g<0>', s)

    # 2. Paréntesis de cierre seguido de paréntesis de apertura: ) ( -> )*(
    s = re.sub(r'(\))\s*(\()', r'\1*\2', s)

    # 3. Paréntesis de cierre seguido de letra o número: )x -> )*x
    s = re.sub(r'(\))\s*([a-zA-Z0-9])', r'\1*\2', s)

    return s


def compile_expression(expr_str: str) -> Tuple[Callable[[float], float], Callable[[np.ndarray], np.ndarray], str]:
    """
    Valida la sintaxis de la expresión de forma segura mediante AST y compila
    dos evaluadores: uno escalar rápido y uno vectorizado para NumPy.
    """
    sanitized = sanitize_expression(expr_str)

    try:
        tree = ast.parse(sanitized, mode='eval')
    except SyntaxError as e:
        raise ValueError(f"Error de sintaxis en la expresión '{expr_str}': {e.msg}")

    # Validar que solo contenga nodos y nombres seguros
    for node in ast.walk(tree):
        if type(node) not in ALLOWED_AST_NODES:
            raise ValueError(f"Elemento no permitido en la expresión: '{type(node).__name__}'")
        if isinstance(node, ast.Name):
            if node.id not in SAFE_NAMES:
                raise ValueError(
                    f"Identificador desconocido o no permitido: '{node.id}'. "
                    f"Solo se permite la variable 'x', constantes ('pi', 'e') y funciones matemáticas estándar."
                )

    code = compile(tree, filename='<math_expr>', mode='eval')

    # Función escalar
    def scalar_func(x_val: float) -> float:
        local_scope = dict(MATH_ENV)
        local_scope['x'] = float(x_val)
        try:
            res = eval(code, {'__builtins__': {}}, local_scope)
            if isinstance(res, complex):
                raise ValueError("El resultado es un número complejo (dominio inválido).")
            return float(res)
        except ZeroDivisionError:
            raise ValueError(f"División por cero al evaluar en x = {x_val}")
        except OverflowError:
            raise OverflowError(f"Desbordamiento numérico (Overflow) al evaluar en x = {x_val}")
        except ValueError as ve:
            raise ValueError(f"Error de dominio matemático en x = {x_val}: {ve}")
        except Exception as e:
            raise ValueError(f"Error al evaluar la expresión en x = {x_val}: {e}")

    # Función vectorizada (para gráficas)
    def vector_func(x_arr: np.ndarray) -> np.ndarray:
        local_scope = dict(NUMPY_ENV)
        local_scope['x'] = x_arr
        try:
            res = eval(code, {'__builtins__': {}}, local_scope)
            # Manejar si devuelve un escalar constante
            if not isinstance(res, np.ndarray):
                res = np.full_like(x_arr, float(res), dtype=float)
            return res.astype(float)
        except Exception:
            # Fallback seguro punto a punto si falla la vectorización directa
            out = np.empty_like(x_arr, dtype=float)
            for idx, val in enumerate(x_arr):
                try:
                    out[idx] = scalar_func(val)
                except Exception:
                    out[idx] = np.nan
            return out

    return scalar_func, vector_func, sanitized


@dataclass
class IterationStep:
    """Representa los datos numéricos de una única iteración."""
    k: int                   # Número de iteración
    x_k: float               # Aproximación actual x_k
    x_next: float            # Nueva aproximación x_{k+1} = g(x_k)
    g_x: float               # Valor de g(x_k) (es igual a x_next)
    error_abs: float         # Error absoluto |x_{k+1} - x_k|
    error_rel_pct: float     # Error relativo porcentual (|x_{k+1} - x_k| / |x_{k+1}|) * 100%
    g_prime: Optional[float] # Derivada numérica g'(x_k)
    f_val: Optional[float]   # Valor f(x_{k+1}) si f(x) fue suministrada


@dataclass
class SolverResult:
    """Resultado completo del método de punto fijo."""
    success: bool
    status: str
    message: str
    root: Optional[float]
    iterations_count: int
    final_error_abs: float
    final_error_rel_pct: float
    steps: List[IterationStep] = field(default_factory=list)
    g_prime_root: Optional[float] = None
    is_contractive: Optional[bool] = None
    f_root: Optional[float] = None
    execution_time_ms: float = 0.0


class PuntoFijoSolver:
    """
    Solucionador del Método de Punto Fijo para ecuaciones no lineales.
    """

    def __init__(
        self,
        g_expr: str,
        f_expr: Optional[str] = None,
        x0: float = 0.0,
        tol: float = 1e-5,
        max_iter: int = 100,
        error_type: str = 'abs', # 'abs' o 'rel'
    ):
        self.g_expr_raw = g_expr
        self.f_expr_raw = f_expr
        self.x0 = float(x0)
        self.tol = float(tol)
        self.max_iter = int(max_iter)
        self.error_type = error_type.lower()

        # Compilar g(x)
        self.g_func, self.g_vec, self.g_sanitized = compile_expression(g_expr)

        # Compilar f(x) opcional
        self.f_func = None
        self.f_vec = None
        self.f_sanitized = None
        if f_expr and f_expr.strip():
            self.f_func, self.f_vec, self.f_sanitized = compile_expression(f_expr)

    def numerical_derivative(self, func: Callable[[float], float], x: float, h: float = 1e-6) -> Optional[float]:
        """Calcula la derivada numérica g'(x) usando diferencias finitas centradas."""
        try:
            return (func(x + h) - func(x - h)) / (2.0 * h)
        except Exception:
            return None

    def solve(self) -> SolverResult:
        """
        Ejecuta las iteraciones del método de punto fijo:
          x_{k+1} = g(x_k)
        hasta satisfacer la tolerancia, detectar divergencia o alcanzar max_iter.
        """
        start_time = time.perf_counter()
        steps: List[IterationStep] = []

        x_curr = self.x0
        success = False
        status = "PENDING"
        message = ""
        diverged = False

        for k in range(1, self.max_iter + 1):
            try:
                x_next = self.g_func(x_curr)
            except Exception as e:
                diverged = True
                status = "ERROR_EVALUACION"
                message = f"Error al evaluar g(x) en la iteración {k} (x = {x_curr:.6g}): {e}"
                break

            # Verificar valores no finitos (inf, nan, o desbordamiento)
            if not math.isfinite(x_next) or abs(x_next) > 1e14:
                diverged = True
                status = "DIVERGENCIA"
                message = (
                    f"Divergencia detectada en la iteración {k}. El valor de x creció sin límite "
                    f"(|x| > 10^14). Esto ocurre cuando |g'(x)| > 1 en la región de iteración."
                )
                break

            # Cálculo de errores
            ea = abs(x_next - x_curr)
            if abs(x_next) > 1e-15:
                er_pct = (ea / abs(x_next)) * 100.0
            else:
                er_pct = ea * 100.0

            # Derivada g'(x_curr)
            g_prime = self.numerical_derivative(self.g_func, x_curr)

            # Residual f(x_next) si f fue dada
            f_val = None
            if self.f_func is not None:
                try:
                    f_val = self.f_func(x_next)
                except Exception:
                    f_val = None

            step = IterationStep(
                k=k,
                x_k=x_curr,
                x_next=x_next,
                g_x=x_next,
                error_abs=ea,
                error_rel_pct=er_pct,
                g_prime=g_prime,
                f_val=f_val
            )
            steps.append(step)

            # Criterio de parada por error
            error_check = ea if self.error_type == 'abs' else (er_pct / 100.0)
            if error_check <= self.tol:
                success = True
                status = "CONVERGENCIA_EXITOSA"
                criterio_str = "Error Absoluto" if self.error_type == 'abs' else "Error Relativo"
                message = (
                    f"¡Convergencia alcanzada con éxito en {k} iteraciones!\n"
                    f"El criterio ({criterio_str} <= {self.tol:.2e}) fue satisfecho."
                )
                x_curr = x_next
                break

            # Alerta de divergencia si el error aumenta drásticamente
            if k >= 5 and ea > 1e6 and ea > steps[0].error_abs * 1e4:
                diverged = True
                status = "DIVERGENCIA"
                message = (
                    f"Divergencia acelerada detectada en la iteración {k}. "
                    f"Los errores sucesivos están creciendo exponencialmente."
                )
                break

            x_curr = x_next
        else:
            # Se agotaron las iteraciones sin divergir ni cumplir tolerancia
            status = "MAX_ITER_ALCANZADO"
            message = (
                f"Se alcanzó el número máximo de iteraciones permitido ({self.max_iter}) "
                f"sin alcanzar la tolerancia requerida ({self.tol:.2e}). "
                f"Último error estimado: {steps[-1].error_abs if steps else 0:.4e}."
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Raíz y derivada final
        root = steps[-1].x_next if steps else None
        g_prime_root = None
        is_contractive = None
        f_root = None

        if root is not None:
            g_prime_root = self.numerical_derivative(self.g_func, root)
            if g_prime_root is not None:
                is_contractive = abs(g_prime_root) < 1.0
            if self.f_func is not None:
                try:
                    f_root = self.f_func(root)
                except Exception:
                    f_root = None

        final_ea = steps[-1].error_abs if steps else 0.0
        final_er = steps[-1].error_rel_pct if steps else 0.0

        return SolverResult(
            success=success,
            status=status,
            message=message,
            root=root,
            iterations_count=len(steps),
            final_error_abs=final_ea,
            final_error_rel_pct=final_er,
            steps=steps,
            g_prime_root=g_prime_root,
            is_contractive=is_contractive,
            f_root=f_root,
            execution_time_ms=elapsed_ms
        )


# Ejemplos preconfigurados de referencia de análisis numérico
EJEMPLOS_PRECONFIGURADOS = [
    {
        "nombre": "1. Función Coseno (Número Dottie): x = cos(x)",
        "descripcion": "Ecuación trascendente universal. Converge suavemente a x ≈ 0.739085.",
        "g_expr": "cos(x)",
        "f_expr": "cos(x) - x",
        "x0": 0.5,
        "tol": 1e-6,
        "max_iter": 60,
        "error_type": "abs"
    },
    {
        "nombre": "2. Función Exponencial: x = e^(-x)",
        "descripcion": "Función decreciente clásica (constante Omega). Converge a x ≈ 0.567143.",
        "g_expr": "exp(-x)",
        "f_expr": "exp(-x) - x",
        "x0": 0.5,
        "tol": 1e-6,
        "max_iter": 50,
        "error_type": "abs"
    },
    {
        "nombre": "3. Ecuación Cuadrática Contractiva: x = sqrt(2x + 3)",
        "descripcion": "Provienen de x² - 2x - 3 = 0. Despeje contractivo que converge a la raíz x = 3.0.",
        "g_expr": "sqrt(2*x + 3)",
        "f_expr": "x^2 - 2*x - 3",
        "x0": 1.0,
        "tol": 1e-6,
        "max_iter": 40,
        "error_type": "abs"
    },
    {
        "nombre": "4. Polinomio Cúbico: x = (x³ + 1) / 3",
        "descripcion": "Provienen de x³ - 3x + 1 = 0. Converge rápidamente a x ≈ 0.347296.",
        "g_expr": "(x^3 + 1) / 3",
        "f_expr": "x^3 - 3*x + 1",
        "x0": 0.0,
        "tol": 1e-6,
        "max_iter": 40,
        "error_type": "abs"
    },
    {
        "nombre": "5. Ejemplo de Divergencia (|g'| > 1): x = x² - 2",
        "descripcion": "Muestra pedagógica de divergencia cuando |g'(x)| > 1 en la vecindad del punto.",
        "g_expr": "x^2 - 2",
        "f_expr": "x^2 - x - 2",
        "x0": 2.5,
        "tol": 1e-6,
        "max_iter": 20,
        "error_type": "abs"
    }
]


def imprimir_tabla_consola(resultado: SolverResult):
    """Muestra los resultados formateados en la consola estándar."""
    print("=" * 86)
    print("                    MÉTODO DE PUNTO FIJO - REPORTE DE ITERACIONES")
    print("=" * 86)
    print(f"Estado:              {resultado.status}")
    print(f"Mensaje:             {resultado.message}")
    if resultado.root is not None:
        print(f"Raíz aproximada x*:  {resultado.root:.8f}")
        print(f"Iteraciones totales: {resultado.iterations_count}")
        print(f"Error Absoluto final: {resultado.final_error_abs:.4e}")
        print(f"Error Relativo (%):  {resultado.final_error_rel_pct:.4f}%")
        if resultado.g_prime_root is not None:
            cond = "CUMPLE (|g'| < 1, convergencia asegurada)" if resultado.is_contractive else "NO CUMPLE (|g'| >= 1)"
            print(f"|g'(x*)| numérico:   {abs(resultado.g_prime_root):.4f} -> {cond}")
        if resultado.f_root is not None:
            print(f"Residual f(x*):      {resultado.f_root:.4e}")
    print(f"Tiempo de ejecución: {resultado.execution_time_ms:.2f} ms")
    print("-" * 86)
    print(f"{'k':<4} | {'x_k':<14} | {'g(x_k) = x_{k+1}':<18} | {'Error Abs (Ea)':<16} | {'Error Rel % (Er)':<16} | {'|g\'(x_k)|':<10}")
    print("-" * 86)
    for s in resultado.steps:
        gp_str = f"{abs(s.g_prime):.4f}" if s.g_prime is not None else "N/A"
        print(f"{s.k:<4} | {s.x_k:<14.8f} | {s.x_next:<18.8f} | {s.error_abs:<16.4e} | {s.error_rel_pct:<16.4f} | {gp_str:<10}")
    print("=" * 86)


if __name__ == '__main__':
    # Modo interactivo simple de consola
    print("--- MÉTODO DE PUNTO FIJO PARA ECUACIONES NO LINEALES ---")
    print("Ecuación de la forma: x = g(x)")
    g_input = input("Ingrese g(x) [Enter para cos(x)]: ").strip()
    if not g_input:
        g_input = "cos(x)"

    f_input = input("Ingrese f(x) opcional [Enter para cos(x) - x]: ").strip()
    if not f_input:
        f_input = "cos(x) - x"

    x0_str = input("Ingrese aproximación inicial x0 [Enter para 0.5]: ").strip()
    x0_val = float(x0_str) if x0_str else 0.5

    tol_str = input("Ingrese tolerancia de error [Enter para 1e-6]: ").strip()
    tol_val = float(tol_str) if tol_str else 1e-6

    solver = PuntoFijoSolver(g_expr=g_input, f_expr=f_input, x0=x0_val, tol=tol_val)
    res = solver.solve()
    imprimir_tabla_consola(res)
