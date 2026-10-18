import subprocess
from qiskit_ibm_runtime import QiskitRuntimeService

CUENTA = "quantum-computer-open"

print("Ahora abre IBM y copia tu API key activa usando su botón Copiar.")
input("Después vuelve aquí y pulsa SOLO Enter, sin pegar la clave: ")

# Lee el portapapeles de Windows y captura el contenido sin mostrarlo.
respuesta = subprocess.run(
    ["powershell.exe", "-NoProfile", "-NonInteractive",
     "-Command", "Get-Clipboard -Raw"],
    capture_output=True,
    text=True,
    check=True,
)

token = respuesta.stdout.strip()

# Detecta entradas vacías, caracteres de control y texto con espacios.
if len(token) < 20 or any(c.isspace() or ord(c) < 32 for c in token):
    raise ValueError(
        "El portapapeles no contiene una API key completa. "
        "Vuelve a copiarla desde IBM."
    )

# Guarda la credencial fuera del repositorio, sin imprimirla.
QiskitRuntimeService.save_account(
    channel="ibm_quantum_platform",
    token=token,
    name=CUENTA,
    plans_preference=["open"],
    overwrite=True,
    set_as_default=False,
)

print(f"Credencial guardada: {len(token)} caracteres.")

# Comprueba la autenticación y consulta dispositivos, sin ejecutar circuitos.
print("Comprobando la conexión con IBM...")
servicio = QiskitRuntimeService(
    name=CUENTA,
    plans_preference=["open"],
)

equipos = servicio.backends(operational=True, simulator=False)
print("Conexión correcta. QPUs disponibles:", [b.name for b in equipos])