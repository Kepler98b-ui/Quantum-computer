# Herramientas para construir y adaptar el circuito.
from qiskit import QuantumCircuit, transpile

# Simulador local y herramientas para introducir ruido.
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

# Herramientas para dibujar el histograma.
import matplotlib.pyplot as plt

# Configuración del experimento.
shots = 1024
p = 0.20  # Intensidad de despolarización.

# Preparamos el mismo estado de Bell del ejercicio anterior.
circuito = QuantumCircuit(2, 2)
circuito.h(0)
circuito.cx(0, 1)
circuito.measure([0, 1], [0, 1])

# Creamos un error que afecta conjuntamente a DOS cúbits.
# Su acción es: E(rho) = (1-p)*rho + p*I4/4.
# rho representa el estado; I4/4 es una mezcla completamente aleatoria.
# p NO equivale directamente al porcentaje de resultados incorrectos.
error_cnot = depolarizing_error(p, 2)

# Asociamos el error a "cx", el nombre de CNOT en Qiskit.
# Aer lo aplicará después de cada CNOT.
# En este ejemplo, Hadamard y las mediciones siguen siendo ideales.
modelo_ruido = NoiseModel()
modelo_ruido.add_all_qubit_quantum_error(error_cnot, ["cx"])

# Creamos los dos simuladores.
# density_matrix permite representar estados mezclados por el ruido.
simulador_ideal = AerSimulator(method="density_matrix")
simulador_ruido = AerSimulator(
    method="density_matrix", noise_model=modelo_ruido
)

# Conservamos las puertas H y CX durante la compilación.
# Así, la CNOT a la que asociamos el error sigue presente.
# Ejecutaremos exactamente el mismo circuito en ambos simuladores.
compilado = transpile(
    circuito, basis_gates=["h", "cx"], optimization_level=0
)

# Ejecutamos 1024 repeticiones en cada simulador.
# Las semillas permiten reproducir el muestreo en el mismo entorno.
conteos_ideal = simulador_ideal.run(
    compilado, shots=shots, seed_simulator=42
).result().get_counts()

conteos_ruido = simulador_ruido.run(
    compilado, shots=shots, seed_simulator=43
).result().get_counts()

# Incluimos los cuatro resultados, aunque alguno aparezca cero veces.
estados = ["00", "01", "10", "11"]
ideal = [conteos_ideal.get(estado, 0) for estado in estados]
ruido = [conteos_ruido.get(estado, 0) for estado in estados]

# Mostramos las frecuencias en PowerShell.
print("Ideal:", dict(zip(estados, ideal)))
print("Con ruido:", dict(zip(estados, ruido)))

# Preparamos las posiciones y el ancho de las barras.
x = list(range(len(estados)))
ancho = 0.36
figura, ejes = plt.subplots(figsize=(8, 5))

# Las barras azules muestran la simulación ideal.
barras_ideal = ejes.bar(
    [valor - ancho / 2 for valor in x], ideal, width=ancho,
    label="Ideal", color="royalblue", zorder=3
)

# Las barras naranjas muestran la simulación con ruido.
barras_ruido = ejes.bar(
    [valor + ancho / 2 for valor in x], ruido, width=ancho,
    label="Con ruido", color="darkorange", zorder=3
)

# Añadimos etiquetas, título y frecuencias sobre las barras.
ejes.set_xticks(x, estados)
ejes.set_xlabel("Resultado de la medición (q1 q0)")
ejes.set_ylabel("Frecuencia (número de veces)")
ejes.set_title(
    f"Estado de Bell — {shots} repeticiones por simulación\n"
    f"Despolarización después de CNOT: p = {p:.2f}"
)
ejes.set_ylim(0, max(ideal + ruido) * 1.2)
ejes.bar_label(barras_ideal, padding=3)
ejes.bar_label(barras_ruido, padding=3)
ejes.grid(axis="y", alpha=0.2, zorder=0)
ejes.legend()

# Guardamos la imagen en la carpeta actual y abrimos el gráfico.
figura.tight_layout()
figura.savefig("comparacion_ruido_bell.png", dpi=160)
plt.show()