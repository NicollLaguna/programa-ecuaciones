from flask import Flask, request, render_template
from sympy import symbols, diff, simplify, latex, Eq, solve, integrate
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

app = Flask(__name__)

x, y = symbols('x y')
m, n = symbols('m n', real=True)

transformaciones = standard_transformations + (implicit_multiplication_application,)

def es_exacta(M, N):
    dM_dy = simplify(diff(M, y))
    dN_dx = simplify(diff(N, x))
    exacta = simplify(dM_dy - dN_dx) == 0
    return exacta, dM_dy, dN_dx

def factor_integrante_x(M, N):
    dM_dy = diff(M, y)
    dN_dx = diff(N, x)
    f = simplify((dM_dy - dN_dx)/N)
    if f.has(y):
        return None
    try:
        mu = integrate(f, x)
        return simplify('exp(mu)'.replace('mu', str(mu)))
    except Exception:
        return None

def factor_integrante_y(M, N):
    dM_dy = diff(M, y)
    dN_dx = diff(N, x)
    g = simplify((dN_dx - dM_dy)/M)
    if g.has(x):
        return None
    try:
        mu = integrate(g, y)
        return simplify('exp(mu)'.replace('mu', str(mu)))
    except Exception:
        return None


def factor_integrante_xm_yn(M, N, rango=range(-10, 11)):
    for m_val in rango:
        for n_val in rango:
            try:
                mu = x**m_val * y**n_val
                M_mu = simplify(mu * M)
                N_mu = simplify(mu * N)
                if simplify(diff(M_mu, y) - diff(N_mu, x)) == 0:
                    return simplify(mu), True
            except Exception:
                continue
    return None, False


def integrar_exacta(M, N):
    psi_x = integrate(M, x)
    dpsi_x_dy = diff(psi_x, y)
    h_prime = simplify(N - dpsi_x_dy)
    h = integrate(h_prime, y)
    psi = psi_x + h
    return psi

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    M_usuario = ""
    N_usuario = ""

    if request.method == "POST":
        try:
            M_usuario = request.form["M"]
            N_usuario = request.form["N"]

            M_expr = M_usuario.replace("^", "**")
            N_expr = N_usuario.replace("^", "**")

            M = parse_expr(M_expr, transformations=transformaciones, evaluate=False)
            N = parse_expr(N_expr, transformations=transformaciones, evaluate=False)

            exacta, dM_dy, dN_dx = es_exacta(M, N)

            resultado = {
                "M": latex(M),
                "N": latex(N),
                "dM_dy": latex(dM_dy),
                "dN_dx": latex(dN_dx),
                "exacta_inicial": "Sí" if exacta else "No",
                "mensaje_inicial": "La ecuación es exacta." if exacta else "La ecuación NO es exacta."
            }

            if exacta:
                psi = integrar_exacta(M, N)
                resultado["solucion"] = latex(psi) + " = C"
            else:
                mu_x = factor_integrante_x(M, N)
                if mu_x:
                    factor = mu_x
                    tipo_factor = "Dependiente solo de x"
                else:
                    mu_y = factor_integrante_y(M, N)
                    if mu_y:
                        factor = mu_y
                        tipo_factor = "Dependiente solo de y"
                    else:
                        factor, exito = factor_integrante_xm_yn(M, N)
                        if exito:
                            tipo_factor = "Forma x^m y^n"
                        else:
                            factor = None
                            tipo_factor = None

                if factor is not None:
                    resultado["factor"] = latex(factor)
                    resultado["tipo_factor"] = tipo_factor

                    M_nuevo = simplify(factor * M)
                    N_nuevo = simplify(factor * N)

                    exacta2, dM_dy2, dN_dx2 = es_exacta(M_nuevo, N_nuevo)

                    resultado.update({
                        "M_nuevo": latex(M_nuevo),
                        "N_nuevo": latex(N_nuevo),
                        "dM_dy2": latex(dM_dy2),
                        "dN_dx2": latex(dN_dx2),
                        "exacta_final": "Sí" if exacta2 else "No",
                        "mensaje_final": "Después de multiplicar por el factor integrante, la ecuación es exacta." if exacta2 else "La ecuación sigue NO siendo exacta."
                    })

                    if exacta2:
                        psi = integrar_exacta(M_nuevo, N_nuevo)
                        resultado["solucion"] = latex(psi) + " = C"
                else:
                    resultado["factor"] = None
                    resultado["tipo_factor"] = None
                    resultado["exacta_final"] = "No"
                    resultado["mensaje_final"] = "No se encontró un factor integrante de los tipos probados."

        except Exception as e:
            resultado = {
                "error": f"Ocurrió un error: {str(e)}"
            }

    return render_template("index.html", resultado=resultado, M_valor=M_usuario, N_valor=N_usuario)



import os

port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port, debug=True)

