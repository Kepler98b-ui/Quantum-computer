"""Envía Bell a una QPU real de IBM o recupera un trabajo anterior."""

import argparse  # Permite recuperar un trabajo con la opción --job-id.
from pathlib import Path  # Construye la ruta donde guardaremos el identificador.
from time import sleep  # Espacia las consultas a los servidores de IBM.
from qiskit import QuantumCircuit  # Describe las puertas y las mediciones.

# Genera el compilador que adapta el circuito a las instrucciones del dispositivo.
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

# Carga credenciales y permite consultar dispositivos y trabajos de IBM.
from qiskit_ibm_runtime import QiskitRuntimeService

# Implementación actual de Sampler con interfaz V2, disponible en Runtime 0.50.
from qiskit_ibm_runtime.executor_sampler import Sampler

CUENTA = "quantum-computer-open"  # Coincide con configurar_ibm.py.
SHOTS = 1024  # Número de preparaciones y mediciones del estado de Bell.

# Este archivo guarda solamente el identificador del trabajo, nunca el token.
ARCHIVO_JOB = Path(__file__).with_name("ultimo_job_bell_ibm.txt")


def crear_bell():
    """Construye un circuito lógico de dos cúbits, inicialmente en |00>."""

    # Aquí creamos una descripción clásica del circuito en nuestra computadora.
    circuito = QuantumCircuit(2)

    # H prepara el cúbit 0 en superposición de |0> y |1>.
    circuito.h(0)

    # CNOT entrelaza los cúbits: idealmente (|00> + |11>)/sqrt(2).
    circuito.cx(0, 1)

    # Añade mediciones y un registro clásico llamado "meas".
    circuito.measure_all()

    # El estado físico se preparará cuando estas instrucciones lleguen al chip.
    return circuito


def enviar_trabajo(servicio):
    """Selecciona una QPU, adapta las puertas y envía un solo trabajo."""

    # Consulta por internet los dispositivos disponibles en las instancias Open.
    backend = servicio.least_busy(
        operational=True,  # El dispositivo debe estar operativo.
        simulator=False,  # Selecciona hardware físico, nunca un simulador.
        min_num_qubits=2,  # Necesitamos dos cúbits, aunque el chip tenga muchos.
    )

    # El dispositivo seleccionado puede cambiar según disponibilidad y colas.
    print(f"QPU seleccionada: {backend.name}", flush=True)
    print(f"Cúbits físicos del dispositivo: {backend.num_qubits}")
    print(f"Trabajos pendientes: {backend.status().pending_jobs}")

    # least_busy compara trabajos pendientes; no garantiza la menor espera real.
    circuito = crear_bell()

    # Dibuja el circuito lógico antes de adaptarlo al hardware.
    print(circuito.draw(output="text"))

    # El compilador traduce H y CNOT a las puertas nativas del dispositivo.
    # También asigna nuestros cúbits lógicos a posiciones físicas del chip.
    compilador = generate_preset_pass_manager(
        backend=backend,  # Usa las puertas y conexiones admitidas por esta QPU.
        optimization_level=1,  # Aplica optimizaciones moderadas.
        seed_transpiler=42,  # Hace reproducibles las elecciones del compilador.
    )

    # ISA significa conjunto de instrucciones admitidas por el dispositivo.
    circuito_isa = compilador.run(circuito)

    # Usamos modo job, compatible con Open; no abrimos una Session.
    muestreador = Sampler(mode=backend)

    # Esta llamada envía instrucciones clásicas por HTTPS a los servidores de IBM.
    # IBM las encola y la electrónica de control las ejecuta sobre el chip frío.
    # Las puertas se realizan mediante señales físicas controladas.
    # Por internet viajan instrucciones y resultados clásicos, no los cúbits.
    trabajo = muestreador.run([circuito_isa], shots=SHOTS)

    # El identificador permite consultar este trabajo sin enviar otro.
    identificador = trabajo.job_id()

    # Lo mostramos inmediatamente por si después se interrumpe la conexión.
    print(f"Job ID: {identificador}", flush=True)

    # Guardamos también el identificador para recuperarlo desde PowerShell.
    ARCHIVO_JOB.write_text(identificador + "\n", encoding="utf-8")
    print(f"Identificador guardado en: {ARCHIVO_JOB}")

    # IBM puede seguir ejecutando el trabajo aunque cierres PowerShell.
    return trabajo


def esperar_resultados(trabajo):
    """Consulta el estado hasta finalizar y muestra las frecuencias medidas."""

    # Cada vuelta consulta el mismo trabajo; no vuelve a enviar el circuito.
    while True:
        estado = trabajo.status()  # Devuelve cadenas como QUEUED o DONE.
        print(f"Estado del trabajo: {estado}", flush=True)

        # DONE indica que IBM terminó correctamente el experimento.
        if estado == "DONE":
            break  # Continúa con la descarga de resultados.

        # ERROR indica que el servicio informó de un fallo.
        if estado == "ERROR":
            raise RuntimeError(trabajo.error_message())

        # Un trabajo cancelado no tiene los resultados esperados del experimento.
        if estado == "CANCELLED":
            print("El trabajo fue cancelado.")
            return

        # Esperamos antes de hacer otra petición por internet.
        sleep(20)

    # Descarga los resultados del trabajo que ya terminó.
    resultado = trabajo.result()

    # [0] selecciona el primer circuito enviado.
    # meas es el registro creado por measure_all().
    # get_counts() cuenta cuántas veces apareció cada cadena de bits.
    conteos = resultado[0].data.meas.get_counts()

    # Calcula cuántas mediciones devolvió realmente el servicio.
    total = sum(conteos.values())
    print(f"\nResultados del hardware real: {total} mediciones")

    # Las cadenas se muestran en el orden convencional q1 q0.
    for estado in ("00", "01", "10", "11"):
        cantidad = conteos.get(estado, 0)  # Incluye resultados que no aparecieron.
        print(
            f"{estado}: {cantidad:4d} veces "
            f"({100 * cantidad / total:.2f} %)"
        )

    # Idealmente solo aparecen 00 y 11, cada uno con probabilidad del 50 %.
    # El ruido de puertas, decoherencia y lectura puede producir también 01 y 10.
    # Estos conteos por sí solos no certifican el entrelazamiento físico.
    return conteos


def main():
    # Configura las opciones que puedes escribir después del nombre del archivo.
    parser = argparse.ArgumentParser(description=__doc__)

    # Esta opción permite recuperar un trabajo sin consumir cuota enviando otro.
    parser.add_argument(
        "--job-id",
        help="Consulta un trabajo existente sin enviar otro.",
    )

    # Lee los argumentos introducidos en PowerShell.
    argumentos = parser.parse_args()

    # Carga la credencial local y autentica con IBM mediante HTTPS.
    # Sin especificar instance, este filtro excluye planes distintos de Open.
    servicio = QiskitRuntimeService(
        name=CUENTA,
        plans_preference=["open"],
    )

    # Si proporcionas un identificador, consulta el trabajo existente.
    if argumentos.job_id:
        trabajo = servicio.job(argumentos.job_id)
        print(f"Consultando el trabajo existente: {trabajo.job_id()}")

    # Sin --job-id, cada ejecución envía un trabajo nuevo.
    else:
        trabajo = enviar_trabajo(servicio)

    # Permite interrumpir la espera local con Ctrl+C.
    try:
        esperar_resultados(trabajo)

    # Interrumpir nuestra consulta no cancela el trabajo que está en IBM.
    except KeyboardInterrupt:
        print("\nConsulta interrumpida; esto no cancela el trabajo en IBM.")
        print(
            "Para recuperarlo, ejecuta el script con "
            f"--job-id {trabajo.job_id()}"
        )


# Importar el archivo no conecta a IBM ni envía trabajos automáticamente.
if __name__ == "__main__":
    main()