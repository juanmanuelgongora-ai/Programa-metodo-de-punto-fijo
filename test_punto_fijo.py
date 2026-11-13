"""
Pruebas Unitarias Automatizadas para el Solucionador de Punto Fijo
"""

import math
import unittest
from punto_fijo import (
    PuntoFijoSolver,
    sanitize_expression,
    compile_expression
)


class TestPuntoFijo(unittest.TestCase):

    def test_sanitize_expression(self):
        # Potencias
        self.assertEqual(sanitize_expression("x^2 + 4"), "x**2 + 4")
        # Multiplicación implícita
        self.assertEqual(sanitize_expression("5x"), "5*x")
        self.assertEqual(sanitize_expression("7x^2"), "7*x**2")
        self.assertEqual(sanitize_expression("2cos(x)"), "2*cos(x)")
        # Notación científica no debe alterarse
        self.assertEqual(sanitize_expression("1e-5"), "1e-5")
        self.assertEqual(sanitize_expression("2.5E+3"), "2.5E+3")
        # Logaritmo natural
        self.assertEqual(sanitize_expression("ln(x)"), "log(x)")

    def test_evaluator_safety(self):
        # Bloquear imports o llamadas no autorizadas
        with self.assertRaises(ValueError):
            compile_expression("__import__('os').system('dir')")
        with self.assertRaises(ValueError):
            compile_expression("open('archivo.txt')")
        with self.assertRaises(ValueError):
            compile_expression("eval('1+1')")

    def test_quadratic_convergent(self):
        # Ecuación x^2 - 2x - 3 = 0 -> Despeje contractivo: x = sqrt(2x + 3)
        # Raíz analítica exacta: x = 3.0
        solver = PuntoFijoSolver(
            g_expr="sqrt(2*x + 3)",
            f_expr="x^2 - 2*x - 3",
            x0=1.0,
            tol=1e-6,
            max_iter=50
        )
        res = solver.solve()
        self.assertTrue(res.success)
        self.assertIsNotNone(res.root)
        self.assertAlmostEqual(res.root, 3.0, places=5)
        self.assertLess(res.final_error_abs, 1e-6)
        # En x = 3, g'(3) = 1/(2*sqrt(9)) * 2 = 1/3 ≈ 0.3333 < 1
        self.assertTrue(res.is_contractive)
        self.assertAlmostEqual(abs(res.g_prime_root), 1.0 / 3.0, places=3)
        # Residual f(x*) cercano a cero
        self.assertAlmostEqual(res.f_root, 0.0, places=4)

    def test_divergent_function(self):
        # Despeje no contractivo: g(x) = (x^2 - 3)/2 para x^2 - 2x - 3 = 0
        # En x = 3, |g'(3)| = 3 > 1 (Divergente)
        solver = PuntoFijoSolver(
            g_expr="(x^2 - 3) / 2",
            x0=3.5,
            tol=1e-6,
            max_iter=30
        )
        res = solver.solve()
        self.assertFalse(res.success)
        self.assertEqual(res.status, "DIVERGENCIA")

    def test_dottie_number(self):
        # x = cos(x) -> x ≈ 0.73908513
        solver = PuntoFijoSolver(
            g_expr="cos(x)",
            f_expr="cos(x) - x",
            x0=0.5,
            tol=1e-6,
            max_iter=60
        )
        res = solver.solve()
        self.assertTrue(res.success)
        self.assertAlmostEqual(res.root, 0.739085, places=4)

    def test_exponential(self):
        # x = exp(-x) -> x ≈ 0.567143
        solver = PuntoFijoSolver(
            g_expr="exp(-x)",
            f_expr="exp(-x) - x",
            x0=0.5,
            tol=1e-6,
            max_iter=50
        )
        res = solver.solve()
        self.assertTrue(res.success)
        self.assertAlmostEqual(res.root, 0.567143, places=4)


if __name__ == '__main__':
    unittest.main()
