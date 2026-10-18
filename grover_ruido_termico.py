"""Compara Grover ideal con ruido térmico artificial, usando dos cúbits."""

from pathlib import Path  # Guarda el gráfico junto a este archivo.
import numpy as np  # Proporciona pi y posiciones para las barras.
import matplotlib.pyplot as plt  # Dibuja el histograma comparativo.
from qiskit import QuantumCircuit, transpile  # Construye y compila circuitos.
from qiskit_aer import AerSimulator  # Simula en nuestra computadora.
from qiskit_aer.noise import NoiseModel, thermal_relaxation_error

SOLUCION = "11"  # Objetivo en orden q1 q0; también admite 00, 01 o 10.
SHOTS = 1024  # Repeticiones completas del experimento.
ESTADOS = ("00", "01", "10", "11")  # Los cuatro candidatos.
BASE = ["rz", "sx", "x", "cx"]  # Puertas que usará el circuito compilado.

# Todas las duraciones usan la MISMA unidad: nanosegundos.
# Son valores didácticos artificiales, no calibraciones de un chip de IBM.
T1 = 20_000.0  # 20 microsegundos: relajación energética hacia |0>.
T2 = 15_000.0  # 15 microsegundos: pérdida de coherencia de fase.

# Duración que atribuimos a cada puerta para calcular su error.
DURACIONES = {
    "sx": 100.0,    # Raíz cuadrada de X.
    "x": 200.0,     # Puerta X.
    "cx": 1_000.0,  # CNOT, que afecta a dos cúbits.
}

# El modelo debe cumplir T1 > 0 y 0 < T2 <= 2*T1.
# RZ se trata como una rotación virtual de duración cero, sin error añadido.


def crear_oraculo(solucion):
    """Marca la solución invirtiendo su fase, sin medirla."""

    # Comprobamos que la solución sea uno de los cuatro candidatos.
    if solucion not in ESTADOS:
        raise ValueError("SOLUCION debe ser 00, 01, 10 o 11.")

    oraculo = QuantumCircuit(2, name="Oraculo")

    # Qiskit muestra q1 q0; al invertir la cadena obtenemos q0, q1.
    # Identificamos los cúbits cuyo bit objetivo es cero.
    ceros = [
        q
        for q, bit in enumerate(reversed(solucion))
        if bit == "0"
    ]

    # Convertimos temporalmente el objetivo en |11>.
    for q in ceros:
        oraculo.x(q)

    # CZ cambia únicamente el signo de la amplitud de |11>.
    # Cambiar el signo no modifica todavía la probabilidad de medir ese estado.
    oraculo.cz(0, 1)

    # Deshacemos las X para restaurar las etiquetas originales.
    for q in ceros:
        oraculo.x(q)

    # Efecto final: O|solución> = -|solución>.
    # Las demás amplitudes conservan su signo.
    return oraculo


def crear_difusor():
    """Construye D = 2|s><s| - I, con |s> la superposición uniforme."""

    difusor = QuantumCircuit(2, name="Difusor")

    # Cambia de base: la superposición uniforme pasa a |00>.
    difusor.h([0, 1])

    # Convierte |00> en |11> para aplicar la reflexión usando CZ.
    difusor.x([0, 1])

    # Invierte la fase de esa componente.
    difusor.cz(0, 1)

    # Deshace los intercambios de bits.
    difusor.x([0, 1])

    # Regresa a la base original.
    difusor.h([0, 1])

    # Ajusta un signo global para obtener exactamente D.
    # Esta fase global no cambia ninguna probabilidad observable.
    difusor.global_phase = np.pi

    return difusor


def crear_grover(solucion):
    """Una iteración basta para cuatro candidatos y una única solución."""

    circuito = QuantumCircuit(2)  # Inicialmente, ambos cúbits están en |0>.

    # Prepara |s> = (|00> + |01> + |10> + |11>)/2.
    # Cada amplitud es 1/2 y cada probabilidad es (1/2)^2 = 1/4.
    circuito.h([0, 1])

    # El oráculo deja tres amplitudes +1/2 y la marcada -1/2.
    circuito.append(crear_oraculo(solucion).to_gate(), [0, 1])

    # Después del oráculo, la media de las amplitudes es:
    # media = (3*(1/2) - 1/2)/4 = 1/4.
    circuito.append(crear_difusor().to_gate(), [0, 1])

    # El difusor transforma cada amplitud a en 2*media - a.
    #
    # Para la solución:
    #     2*(1/4) - (-1/2) = 1.
    #
    # Para los otros tres estados:
    #     2*(1/4) - 1/2 = 0.
    #
    # La interferencia amplifica la solución y cancela las otras amplitudes.
    # Idealmente, la probabilidad de encontrar la solución es 100 %.
    #
    # Con ruido, el estado puede ser mixto y la cancelación deja de ser perfecta.

    # Mide ambos cúbits y devuelve una cadena clásica en orden q1 q0.
    circuito.measure_all()

    return circuito


def crear_ruido_termico():
    """Asocia canales de relajación a las puertas del circuito compilado."""

    modelo = NoiseModel(basis_gates=BASE)

    # Calculamos un error diferente según cuánto dura cada puerta.
    for puerta, tiempo in DURACIONES.items():
        error = thermal_relaxation_error(
            t1=T1,  # A temperatura muy baja, |1> tiende a relajarse hacia |0>.
            t2=T2,  # Decaen las coherencias necesarias para la interferencia.
            time=tiempo,  # Más duración permite que estos procesos actúen más.
            excited_state_population=0.0,  # Equilibrio térmico aproximado en |0>.
        )

        # CNOT ocupa dos cúbits durante el mismo intervalo.
        if puerta == "cx":
            # El producto tensorial modela relajación independiente en ambos.
            error = error.tensor(error)

        # Aer aplica el canal de error después de cada puerta de este tipo.
        modelo.add_all_qubit_quantum_error(error, [puerta])

    # Este ejemplo modela relajación asociada a las puertas.
    # No añadimos errores de lectura ni relajación extra durante tiempos ociosos.
    return modelo


def simular(circuito):
    """Ejecuta el mismo circuito compilado con y sin ruido."""

    # H y CZ deben descomponerse en las puertas que tienen errores asignados.
    # Así evitamos que el circuito use instrucciones sin el ruido esperado.
    compilado = transpile(
        circuito,
        basis_gates=BASE,
        optimization_level=0,  # Evita optimizaciones adicionales de la secuencia.
        seed_transpiler=42,  # Hace reproducible la compilación.
    )

    print("Puertas del circuito compilado:", dict(compilado.count_ops()))

    # La matriz de densidad permite representar estados puros y mixtos.
    ideal = AerSimulator(method="density_matrix")

    # El segundo simulador añade los canales térmicos definidos anteriormente.
    ruidoso = AerSimulator(
        method="density_matrix",
        noise_model=crear_ruido_termico(),
    )

    # Primera ejecución: evolución ideal, sin ruido.
    resultado_ideal = ideal.run(
        compilado,
        shots=SHOTS,
        seed_simulator=42,
    ).result()

    # Segunda ejecución: exactamente el mismo circuito, con ruido térmico.
    resultado_ruidoso = ruidoso.run(
        compilado,
        shots=SHOTS,
        seed_simulator=43,
    ).result()

    # Las semillas permiten repetir el experimento con esta configuración.
    return resultado_ideal.get_counts(), resultado_ruidoso.get_counts()


def graficar(conteos_ideal, conteos_ruido):
    """Compara frecuencias y guarda una imagen del experimento."""

    # get(..., 0) incluye los estados que no aparecieron.
    ideal = [conteos_ideal.get(estado, 0) for estado in ESTADOS]
    ruido = [conteos_ruido.get(estado, 0) for estado in ESTADOS]

    posiciones = np.arange(len(ESTADOS))  # Una posición por candidato.
    ancho = 0.36  # Anchura de cada barra.

    figura, eje = plt.subplots(figsize=(9, 5))

    # Coloca las barras ideales a la izquierda de cada posición.
    barras_ideal = eje.bar(
        posiciones - ancho / 2,
        ideal,
        ancho,
        label="Ideal",
    )

    # Coloca las barras ruidosas a la derecha.
    barras_ruido = eje.bar(
        posiciones + ancho / 2,
        ruido,
        ancho,
        label="Ruido térmico",
    )

    # Escribe el número de resultados encima de cada barra.
    eje.bar_label(barras_ideal, padding=3)
    eje.bar_label(barras_ruido, padding=3)

    eje.set_xticks(posiciones, ESTADOS)
    eje.set_xlabel("Resultado de la medición (q1 q0)")
    eje.set_ylabel("Frecuencia (número de veces)")

    eje.set_title(
        f"Grover: búsqueda de {SOLUCION} — {SHOTS} repeticiones por simulación\n"
        f"Ruido artificial: T1 = {T1 / 1000:g} µs, T2 = {T2 / 1000:g} µs"
    )

    eje.set_ylim(0, SHOTS * 1.15)  # Deja espacio para las etiquetas.
    eje.legend()  # Identifica ambas simulaciones.
    eje.grid(axis="y", alpha=0.2)  # Facilita comparar alturas.
    eje.set_axisbelow(True)  # Coloca la cuadrícula detrás de las barras.
    figura.tight_layout()  # Ajusta los márgenes.

    # Guarda el gráfico junto al script.
    ruta = Path(__file__).with_name("grover_ruido_termico.png")
    figura.savefig(ruta, dpi=150)
    print(f"Gráfico guardado en: {ruta}")

    # Muestra la ventana; ciérrala para que el programa termine.
    plt.show()


def main():
    circuito = crear_grover(SOLUCION)  # Construye el experimento lógico.
    print(circuito.draw(output="text"))  # Muestra las etapas del algoritmo.

    # Ambas ejecuciones son completamente locales.
    ideal, ruido = simular(circuito)

    # Muestra los conteos de todos los estados posibles.
    print("\nEstado | Ideal | Con ruido")
    for estado in ESTADOS:
        print(
            f"  {estado}   | {ideal.get(estado, 0):5d} "
            f"| {ruido.get(estado, 0):5d}"
        )

    # Éxito significa obtener el estado que marcó el oráculo.
    exito_ideal = ideal.get(SOLUCION, 0) / sum(ideal.values())
    exito_ruido = ruido.get(SOLUCION, 0) / sum(ruido.values())

    print(f"\nÉxito ideal:     {exito_ideal:.2%}")
    print(f"Éxito con ruido: {exito_ruido:.2%}")

    # Esta diferencia se expresa en puntos porcentuales.
    print(
        f"Caída observada: "
        f"{100 * (exito_ideal - exito_ruido):.2f} puntos porcentuales"
    )

    graficar(ideal, ruido)


# Importar este archivo desde otro programa no inicia las simulaciones.
if __name__ == "__main__":
    main()