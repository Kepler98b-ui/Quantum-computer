# Importamos la herramienta para crear circuitos.
from qiskit import QuantumCircuit

# Importamos el simulador local.
from qiskit_aer import AerSimulator

# Importamos las herramientas para dibujar el histograma.
import matplotlib.pyplot as plt

# Creamos 2 cúbits y 2 bits clásicos para guardar sus mediciones.
# El simulador inicia ambos cúbits en 0: estado |00>.
circuito = QuantumCircuit(2, 2)

# Aplicamos Hadamard al primer cúbit, cuyo índice es 0.
# Este cúbit queda en una superposición con amplitudes iguales.
#
# IMPORTANTE: Qiskit escribe los resultados en el orden q1 q0.
# Por eso, tras H sobre q0, el estado es:
# (|00> + |01>) / sqrt(2).
circuito.h(0)

# Aplicamos CNOT: q0 es el control y q1 es el objetivo.
# La puerta invierte q1 solamente en la componente donde q0 vale 1.
# Actúa coherentemente sobre la superposición, sin medir el control.
#
# En el orden q1 q0:
# |00> permanece como |00>.
# |01> se transforma en |11>.
#
# El estado resultante es (|00> + |11>) / sqrt(2).
# Este es el estado de Bell llamado Phi+.
circuito.cx(0, 1)

# ¿POR QUÉ NO APARECEN 01 Y 10?
# Sus amplitudes en este estado son exactamente cero.
# La probabilidad de cada resultado es el módulo al cuadrado
# de su amplitud, por lo que:
# P(00) = 1/2, P(11) = 1/2, P(01) = 0 y P(10) = 0.
#
# Medimos en la base computacional y guardamos q0 en c0 y q1 en c1.
# Cada repetición produce 00 o 11 con igual probabilidad.
circuito.measure([0, 1], [0, 1])

# Creamos un simulador ideal, sin ruido.
# Con ruido o errores de lectura, 01 y 10 podrían aparecer.
simulador = AerSimulator()

# Repetimos 1024 veces la preparación completa y la medición.
# Cada repetición comienza de nuevo con ambos cúbits en |00>.
resultado = simulador.run(circuito, shots=1024).result()

# Obtenemos cuántas veces apareció cada resultado.
conteos = resultado.get_counts()

# Mostramos el circuito y sus resultados en la terminal.
print(circuito.draw(output="text"))
print("Resultados de las 1024 repeticiones:", conteos)

# Incluimos los cuatro resultados posibles en el gráfico.
estados = ["00", "01", "10", "11"]

# Si un resultado no aparece en el diccionario, su frecuencia es 0.
frecuencias = [conteos.get(estado, 0) for estado in estados]

# Creamos la figura y el área donde dibujaremos las barras.
figura, ejes = plt.subplots(figsize=(7, 5))

# La altura de cada barra indica el número de veces que apareció.
barras = ejes.bar(estados, frecuencias, color="royalblue")

# Añadimos el título y las etiquetas de los ejes.
ejes.set_title("Estado de Bell — 1024 repeticiones")
ejes.set_xlabel("Resultado de la medición (q1 q0)")
ejes.set_ylabel("Frecuencia (número de veces)")

# Dejamos espacio para mostrar los valores sobre las barras.
ejes.set_ylim(0, max(frecuencias) * 1.15)
ejes.bar_label(barras, padding=3)

# Ajustamos los márgenes y abrimos la ventana del gráfico.
figura.tight_layout()
plt.show()