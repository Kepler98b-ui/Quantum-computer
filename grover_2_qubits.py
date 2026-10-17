# Herramientas para construir el circuito, simularlo y dibujar resultados.
from math import pi
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import matplotlib.pyplot as plt

# PASO 1: representar los cuatro candidatos.
# Qiskit muestra los bits en el orden q1 q0.
# Estos estados representan los índices 0, 1, 2 y 3.
estados = ["00", "01", "10", "11"]
shots = 1024

# PASO 2: construir el oráculo.
# CZ cambia el signo de la amplitud de |11>.
# Las amplitudes de |00>, |01> y |10> permanecen iguales.
# Este cambio de fase todavía no modifica las probabilidades.
oraculo = QuantumCircuit(2, name="Oraculo")
oraculo.cz(0, 1)

# PASO 3: construir el operador de difusión.
# Refleja cada amplitud respecto de la media:
# nueva_amplitud = 2 * media - amplitud_actual.
#
# Después del oráculo, las amplitudes serán:
# [1/2, 1/2, 1/2, -1/2], cuya media es 1/4.
# La difusión las transforma en [0, 0, 0, 1].
difusion = QuantumCircuit(2, name="Difusion")

# Aplicamos H y X a ambos cúbits.
difusion.h([0, 1])
difusion.x([0, 1])

# Introducimos el cambio de fase necesario para la reflexión.
difusion.cz(0, 1)

# Deshacemos las transformaciones anteriores.
difusion.x([0, 1])
difusion.h([0, 1])

# Ajustamos el signo global para obtener exactamente la reflexión descrita.
# Una fase global no cambia las probabilidades de medición.
difusion.global_phase = pi

# PASO 4: crear el circuito completo.
# Usamos dos cúbits y dos bits clásicos para guardar las mediciones.
circuito = QuantumCircuit(2, 2)

# Preparamos una superposición uniforme.
# Cada candidato empieza con amplitud 1/2 y probabilidad 1/4.
circuito.h([0, 1])

# PASO 5: ejecutar UNA iteración de Grover.
# to_gate() convierte cada circuito auxiliar en una puerta compuesta.
# append() coloca ese bloque sobre los cúbits indicados.
circuito.append(oraculo.to_gate(), [0, 1])
circuito.append(difusion.to_gate(), [0, 1])

# Para cuatro candidatos y una única solución, una iteración basta.
# La interferencia cancela las amplitudes de los candidatos incorrectos
# y concentra la probabilidad en |11>.

# PASO 6: medir los dos cúbits.
circuito.measure([0, 1], [0, 1])

# Creamos un simulador ideal, sin el ruido del ejercicio anterior.
simulador = AerSimulator()

# Descomponemos Oraculo y Difusion en puertas que admite el simulador.
compilado = transpile(circuito, simulador)

# Repetimos el experimento completo 1024 veces.
# Cada repetición contiene UNA iteración de Grover.
conteos = simulador.run(
    compilado, shots=shots
).result().get_counts()

# Incluimos los candidatos que aparecieron cero veces.
frecuencias = [conteos.get(estado, 0) for estado in estados]

# Mostramos el circuito y los resultados en PowerShell.
print(circuito.draw(output="text"))
print("Resultados:", dict(zip(estados, frecuencias)))

# PASO 7: dibujar el histograma final.
figura, ejes = plt.subplots(figsize=(7, 5))
barras = ejes.bar(estados, frecuencias, color="royalblue")

# Añadimos el título, las etiquetas y los valores sobre las barras.
ejes.set_title("Grover: búsqueda de 11 entre cuatro candidatos")
ejes.set_xlabel("Candidato (q1 q0)")
ejes.set_ylabel("Frecuencia (número de veces)")
ejes.set_ylim(0, shots * 1.15)
ejes.bar_label(barras, padding=3)

# Guardamos una imagen y abrimos la ventana del gráfico.
figura.tight_layout()
figura.savefig("histograma_grover.png", dpi=160)
plt.show()