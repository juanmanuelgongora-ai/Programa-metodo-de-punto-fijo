"""
Punto de Entrada Principal (Main Entry Point)
Método de Punto Fijo - Análisis Numérico
Solución de Ecuaciones No Lineales

Uso:
    python main.py             -> Abre la interfaz gráfica interactiva (GUI)
    python main.py --cli       -> Ejecuta en modo consola interactiva
    python main.py --help      -> Muestra las opciones disponibles
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Solucionador de Ecuaciones No Lineales mediante el Método de Punto Fijo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py                             (Inicia la interfaz gráfica interactiva con gráficos Cobweb)
  python main.py --cli                       (Inicia el modo interactivo por consola)
  python main.py --g "cos(x)" --x0 0.5       (Cálculo directo por línea de comandos)
  python main.py --g "exp(-x)" --x0 0.5 --tol 1e-6
        """
    )

    parser.add_argument("--cli", action="store_true", help="Ejecutar en la terminal / consola en lugar de la GUI")
    parser.add_argument("--g", type=str, default=None, help="Expresión para g(x) en la ecuación x = g(x)")
    parser.add_argument("--f", type=str, default=None, help="Expresión para f(x) en f(x) = 0 (opcional para verificar residual)")
    parser.add_argument("--x0", type=float, default=0.5, help="Valor o aproximación inicial x0 (por defecto 0.5)")
    parser.add_argument("--tol", type=float, default=1e-6, help="Tolerancia de convergencia (por defecto 1e-6)")
    parser.add_argument("--max-iter", type=int, default=100, help="Número máximo de iteraciones (por defecto 100)")
    parser.add_argument("--error-type", choices=["abs", "rel"], default="abs", help="Criterio de error: 'abs' o 'rel'")

    args = parser.parse_args()

    # Si se especificó una función g directamente por CLI
    if args.g is not None:
        from punto_fijo import PuntoFijoSolver, imprimir_tabla_consola
        print(f"Resolviendo x = {args.g} con x0 = {args.x0}, Tol = {args.tol}...")
        solver = PuntoFijoSolver(
            g_expr=args.g,
            f_expr=args.f,
            x0=args.x0,
            tol=args.tol,
            max_iter=args.max_iter,
            error_type=args.error_type
        )
        res = solver.solve()
        imprimir_tabla_consola(res)
        return

    # Si se solicitó explícitamente modo CLI interactivo
    if args.cli:
        from punto_fijo import PuntoFijoSolver, imprimir_tabla_consola
        print("=" * 70)
        print("    MÉTODO DE PUNTO FIJO - SOLUCIONADOR DE ECUACIONES NO LINEALES")
        print("=" * 70)
        g_in = input("Ingrese la función g(x) [Enter para cos(x)]: ").strip()
        if not g_in:
            g_in = "cos(x)"

        f_in = input("Ingrese la función f(x) opcional [Enter para cos(x) - x]: ").strip()
        if not f_in:
            f_in = "cos(x) - x"

        x0_in = input("Ingrese aproximación inicial x0 [Enter para 0.5]: ").strip()
        x0_val = float(x0_in) if x0_in else 0.5

        tol_in = input("Ingrese tolerancia de error [Enter para 1e-6]: ").strip()
        tol_val = float(tol_in) if tol_in else 1e-6

        solver = PuntoFijoSolver(g_expr=g_in, f_expr=f_in, x0=x0_val, tol=tol_val)
        res = solver.solve()
        imprimir_tabla_consola(res)
        return

    # Por defecto: Iniciar la interfaz gráfica de usuario
    try:
        from app_gui import launch_app
        launch_app()
    except Exception as e:
        print(f"No se pudo iniciar la interfaz gráfica: {e}")
        print("Iniciando en modo consola alternativo...\n")
        from punto_fijo import PuntoFijoSolver, imprimir_tabla_consola
        solver = PuntoFijoSolver(g_expr="cos(x)", f_expr="cos(x) - x", x0=0.5, tol=1e-6)
        res = solver.solve()
        imprimir_tabla_consola(res)


if __name__ == '__main__':
    main()
