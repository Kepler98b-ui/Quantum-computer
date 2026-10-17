# secrets genera bits y elecciones aleatorias usando el sistema operativo.
import secrets

# Qiskit construye los circuitos y Aer realiza la simulación local.
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Cambia a False para comparar el funcionamiento sin espionaje.
ataque_eva = False

# Número de señales independientes que enviará Alice.
numero_bits = 256


# ETAPA 1: Alice genera sus datos, elige bases y prepara los cúbits.
def preparar_alice(cantidad):
    # Cada llamada genera un bit: 0 o 1 con la misma probabilidad.
    bits = [secrets.randbits(1) for _ in range(cantidad)]

    # Las bases se eligen independientemente de los datos.
    bases = [secrets.choice(("Z", "X")) for _ in range(cantidad)]

    # Cada circuito representa una señal cuántica independiente.
    circuitos = []

    # zip permite recorrer conjuntamente cada bit y su base.
    for bit, base in zip(bits, bases):
        # Un cúbit y dos bits clásicos: c0 para Eva, c1 para Bob.
        circuito = QuantumCircuit(1, 2)

        # El cúbit comienza en |0>; X lo transforma en |1> si corresponde.
        if bit == 1:
            circuito.x(0)

        # Para la base X, H transforma |0> en |+> y |1> en |->.
        # Así quedan codificados los cuatro estados posibles de BB84.
        if base == "X":
            circuito.h(0)

        # Guardamos la descripción de esta señal.
        circuitos.append(circuito)

    return bits, bases, circuitos


# ETAPA 2: canal ideal o ataque de interceptación y reenvío.
def canal_cuantico(circuitos, ataque_eva):
    # Copiamos descripciones de circuitos, no estados físicos.
    # Esta operación de Python no representa una clonación cuántica.
    recibidos = [circuito.copy() for circuito in circuitos]

    # Sin Eva, las señales pasan directamente a Bob.
    if not ataque_eva:
        return recibidos

    for circuito in recibidos:
        # Eva desconoce la base de Alice y elige una al azar.
        base_eva = secrets.choice(("Z", "X"))

        # Medir en X equivale a aplicar H y después medir en Z.
        if base_eva == "X":
            circuito.h(0)

        # Eva mide y guarda su resultado clásico en c0.
        circuito.measure(0, 0)

        # El teorema de no clonación impide copiar perfectamente
        # un estado cuántico desconocido de forma universal.
        # En este ataque, Eva mide: una base incompatible con Alice
        # produce un resultado aleatorio y altera el estado.

        # Representamos la nueva señal de Eva reutilizando el mismo hilo.
        # reset prepara |0>, eliminando el estado anterior.
        circuito.reset(0)

        # Eva prepara el bit que obtuvo al medir.
        # if_test evalúa c0 durante la ejecución del circuito.
        with circuito.if_test((circuito.clbits[0], 1)):
            circuito.x(0)

        # Si su base era X, convierte el bit en |+> o |->.
        # Esta es la señal que reenvía a Bob.
        if base_eva == "X":
            circuito.h(0)

    return recibidos


# ETAPA 3: Bob elige sus propias bases y mide las señales.
def medir_bob(circuitos):
    # Las elecciones de Bob son independientes de Alice y Eva.
    bases = [secrets.choice(("Z", "X")) for _ in circuitos]

    for circuito, base in zip(circuitos, bases):
        # H permite medir en la base X.
        if base == "X":
            circuito.h(0)

        # Guardamos la medición de Bob en c1.
        circuito.measure(0, 1)

    # Simulamos sin ruido adicional al ataque de Eva.
    simulador = AerSimulator(method="statevector")

    # Adaptamos las puertas y las condiciones al simulador.
    compilados = transpile(
        circuitos,
        simulador,
        optimization_level=0,
        num_processes=1
    )

    # Cada circuito se ejecuta UNA vez: una medición por señal enviada.
    # memory=True permite recuperar individualmente los resultados.
    resultado = simulador.run(
        compilados, shots=1, memory=True
    ).result()

    bits = []

    for indice in range(len(compilados)):
        # Qiskit devuelve los bits en el orden c1c0.
        # El carácter izquierdo contiene la medición de Bob.
        memoria = resultado.get_memory(indice)[0]
        bits.append(int(memoria[0]))

    return bits, bases


# ETAPA 4: Alice y Bob anuncian sus bases y conservan las coincidencias.
# Esta función solo recibe bases; no necesita conocer los datos secretos.
def conciliar_bases(bases_alice, bases_bob):
    return [
        indice
        for indice, (alice, bob) in enumerate(zip(bases_alice, bases_bob))
        if alice == bob
    ]


# Función principal: conecta las etapas y muestra los resultados.
def main():
    # Alice prepara las señales.
    bits_alice, bases_alice, circuitos = preparar_alice(numero_bits)

    # Las señales atraviesan el canal, con o sin Eva.
    recibidos = canal_cuantico(circuitos, ataque_eva)

    # Bob mide las señales recibidas.
    bits_bob, bases_bob = medir_bob(recibidos)

    # Ambos identifican públicamente las bases coincidentes.
    posiciones = conciliar_bases(bases_alice, bases_bob)

    # Cada participante obtiene su clave usando SUS propios resultados.
    clave_alice = [bits_alice[i] for i in posiciones]
    clave_bob = [bits_bob[i] for i in posiciones]

    # La terminal muestra información educativa del simulador.
    # Mostrar las claves aquí no representa publicarlas en el protocolo.
    print("BB84 — simulación educativa")
    print("Ataque de Eva:", "activado" if ataque_eva else "desactivado")
    print("Bases de Alice:", "".join(bases_alice))
    print("Bases de Bob:  ", "".join(bases_bob))
    print("Señales enviadas:", numero_bits)
    print("Bits conservados:", len(posiciones))
    print("Clave filtrada de Alice:", "".join(str(b) for b in clave_alice))
    print("Clave filtrada de Bob:  ", "".join(str(b) for b in clave_bob))

    # Evitamos dividir entre cero si ninguna base coincidió.
    if not posiciones:
        print("No hay bits conservados; repite el experimento.")
        return

    # Contamos discrepancias entre los bits conservados.
    # Comparar toda la clave es un diagnóstico interno de esta simulación.
    # Alice y Bob no intercambian sus claves completas para calcularlo.
    errores = sum(a != b for a, b in zip(clave_alice, clave_bob))

    # QBER: proporción de errores sobre los bits conservados.
    qber = 100 * errores / len(posiciones)

    print(f"Errores entre bits conservados: {errores}")
    print(f"QBER (diagnóstico del simulador): {qber:.2f} %")

    if errores:
        print("Hay discrepancias: estas claves todavía no son compartidas.")
    else:
        print("Las claves coinciden; esta muestra no demuestra seguridad.")

    # El protocolo completo requiere más procesamiento y autenticación.
    print("Resultado: claves candidatas, no claves finales para uso real.")


# Ejecuta main al iniciar este archivo desde PowerShell.
# Permite también importar las funciones desde otros programas.
if __name__ == "__main__":
    main()