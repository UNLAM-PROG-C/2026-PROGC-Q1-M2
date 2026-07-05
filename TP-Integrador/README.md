# Sistema de Venta de Entradas para Recitales

Un sistema completo de reserva y venta de entradas para recitales con manejo avanzado de concurrencia, construido con Python, FastAPI y PostgreSQL.

## 📌 Alcance del Proyecto

Este proyecto implementa una **aplicación web de venta de entradas para recitales** cuyo objetivo central es resolver, de forma correcta y demostrable, los problemas de **concurrencia** que surgen cuando múltiples usuarios interactúan simultáneamente sobre un recurso compartido y limitado: los asientos de un evento.

### Descripción de la solución

El sistema permite a varios usuarios, de manera concurrente, autenticarse, explorar recitales, seleccionar asientos, reservarlos temporalmente y confirmar su compra. El desafío principal es garantizar que **un mismo asiento nunca sea vendido a dos personas distintas**, aun cuando ambas intenten reservarlo en el mismo instante. La solución aborda esto en varias capas:

- **Exclusión mutua a nivel de base de datos:** la reserva se resuelve con una operación atómica (`UPDATE ... WHERE status = 'available'`) apoyada en el *row-level locking* de PostgreSQL. Esta es la garantía de correctitud, y se delega a la base de datos para que sea válida incluso si el sistema se ejecuta en múltiples procesos o servidores.
- **Prevención de deadlocks:** al reservar varios asientos, los identificadores se ordenan para imponer un orden de adquisición global y evitar la espera circular.
- **Concurrencia en el servidor:** el backend combina un *event loop* asíncrono (para las conexiones WebSocket y el I/O de red) con *threads worker* (para las operaciones bloqueantes contra la base de datos), coordinados mediante un *pool* de conexiones thread-safe (concurrencia manejada por el Pool de conexiones).
- **Actualizaciones en tiempo real:** mediante WebSockets, los cambios de estado de los asientos se propagan instantáneamente a todos los clientes conectados a un recital.
- **Tarea de fondo concurrente:** un *thread* dedicado libera automáticamente las reservas temporales que expiran, sin bloquear la atención de los usuarios.

### Dentro del alcance

- Autenticación de usuarios mediante tokens JWT.
- Listado de recitales y visualización interactiva de asientos por sección (Campo, Platea, Platea VIP).
- Reserva temporal de asientos con expiración configurable y confirmación de compra.
- Detección, resolución y registro (*logging*) de *race conditions*.
- Simulación del procesamiento de pago (sin integración con pasarelas reales).
- Actualización de disponibilidad en tiempo real vía WebSockets.

### Fuera del alcance

- Integración con pasarelas de pago reales (el pago es un *stub* simulado).
- Gestión administrativa avanzada (alta/baja de recitales por interfaz, reportes de ventas).
- Escalado horizontal multi-proceso de las notificaciones WebSocket (requeriría un *message broker* como Redis; la correctitud de las reservas, en cambio, sí escala por delegarse a la base de datos).
- Emisión de entradas físicas o digitales (PDF, códigos QR).

## 🎯 Características

- **Frontend interactivo** con selección visual de asientos
- **Backend robusto** con manejo de race conditions mediante BD atómica
- **WebSockets** para actualizaciones en tiempo real
- **Autenticación JWT** para seguridad
- **Logging de race conditions** para auditoría
- **Soporte para múltiples secciones**: Campo, Platea, Platea VIP
- **Reserva temporal** con expiración configurable
- **Limpeza automática** de reservas expiradas con threads

## 📋 Requisitos Previos

- **Python 3.14+**
- **PostgreSQL 18+**
- **pip** (Python package manager)

## 🧩 Frameworks y Dependencias

### Backend (Python)

| Dependencia | Versión | Rol |
|-------------|---------|-----|
| **FastAPI** | 0.109.0 | Framework web (API REST + WebSockets) |
| **Uvicorn** | 0.27.0 | Servidor ASGI que corre el event loop |
| **psycopg** | 3.2.13 | Driver de PostgreSQL (SQL directo, sin ORM) |
| **psycopg_pool** | 3.2.4 | Pool de conexiones thread-safe |
| **PyJWT** | 2.8.0 | Autenticación mediante tokens JWT |
| **passlib** + **bcrypt** | 1.7.4 / 4.1.1 | Hashing seguro de contraseñas |
| **slowapi** | 0.1.9 | Rate limiting (protección del login) |
| **aiohttp** | 3.13.2 | Cliente HTTP asíncrono (pruebas de concurrencia) |

### Base de datos

- **PostgreSQL 18** — la concurrencia crítica se delega aquí (UPDATE atómico + row-level locking).

### Frontend

- **HTML5 + CSS3 + JavaScript (ES6+) puro**, sin frameworks ni librerías externas (no usa React/Vue/jQuery).

## 🖥️ Restricciones y Compatibilidad

### Requisitos de Hardware

- **Sin requisitos especiales.** La aplicación es *I/O-bound* (espera de red y base de datos), no *CPU-bound*: no realiza cálculo intensivo ni requiere GPU.
- **RAM recomendada:** ~1 GB libre es suficiente para el backend + PostgreSQL en desarrollo. El pool está configurado hasta 100 conexiones y PostgreSQL con `max_connections=200`; en cargas altas, más conexiones consumen más memoria en el servidor de BD.
- Funciona en cualquier máquina moderna (x86-64 o ARM64, ej. Apple Silicon).

### Restricciones de Sistema Operativo

- **Multiplataforma.** El backend usa únicamente primitivas estándar y portables (`threading`, `asyncio`, sockets), sin llamadas específicas de un SO. Corre en **Linux, macOS y Windows**.
- Los **scripts de ayuda** (`init_db.sh`, `run_server.sh`, `quick_start.sh`) están escritos en **Bash**, por lo que asumen un entorno Unix (Linux/macOS) o, en Windows, WSL o Git Bash.
- **Con Docker no hay ninguna restricción de SO:** `docker compose up` levanta backend + PostgreSQL de forma idéntica en cualquier plataforma. Es la vía recomendada para evitar diferencias de entorno.

### Restricciones de Navegador

- Requiere un **navegador moderno "evergreen"**: **Chrome, Firefox, Edge o Safari** en versiones recientes (aprox. 2018 en adelante).
- El frontend depende de APIs modernas: **WebSocket API**, **Fetch API**, **`localStorage`**, **`URLSearchParams`**, **`Set`**, además de sintaxis **ES6+** (`async/await`, *arrow functions*, *template literals*).
- **No es compatible con Internet Explorer** (no soporta `fetch`, `async/await` ni WebSockets de forma adecuada).
- **JavaScript debe estar habilitado.** Para las actualizaciones en tiempo real, el navegador debe poder establecer una conexión **WebSocket** (`ws://` o `wss://`) contra el servidor.

## 🚀 Instalación

### 1. Clonar el repositorio
```bash
cd /Users/kevin.arias/Documents/Git/programacion-concurrente/tp-metricas
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar PostgreSQL

Asegúrate de que PostgreSQL esté corriendo:
```bash
# En macOS con Homebrew
brew services start postgresql

# O en Linux
sudo systemctl start postgresql
```

### 4. Inicializar la base de datos
```bash
./init_db.sh
```

Si necesitas usar diferentes credenciales, puedes configurarlas:
```bash
DB_HOST=localhost DB_PORT=5432 DB_USER=ticketuser DB_PASSWORD=ticketpass ./init_db.sh
```

## ▶️ Ejecución

### Iniciar el servidor backend
```bash
./run_server.sh
```

El servidor estará disponible en:
- **API**: http://localhost:8000
- **Frontend**: http://localhost:8000
- **Documentación Swagger**: http://localhost:8000/docs
- **Documentación ReDoc**: http://localhost:8000/redoc

### Acceso a la aplicación

1. Abre http://localhost:8000 en tu navegador
2. Ingresa con las credenciales de prueba:
   - **Usuario**: `test_user`
   - **Contraseña**: `test123`

O usa cualquiera de los otros usuarios de prueba (`testuser1`-`testuser10` con la misma contraseña).

## 🧪 Pruebas de Concurrencia

Para ejecutar las pruebas de concurrencia que simulan múltiples usuarios intentando reservar asientos simultáneamente:

```bash
# Asegúrate de que el servidor esté ejecutándose en otra terminal
pip install aiohttp  # Dependencia adicional para las pruebas
python tests/concurrent_test.py
```

Las pruebas incluyen:
- **Reservas concurrentes**: 10+ usuarios intentando reservar los mismos asientos
- **Detección de race conditions**: Validación de que solo 1 usuario obtiene cada asiento
- **Pruebas secuenciales**: Usuarios reservando diferentes asientos

## 📊 Estructura del Proyecto

```
tp-metricas/
├── backend/                    # Backend FastAPI
│   ├── main.py                # Punto de entrada
│   ├── config.py              # Configuración
│   ├── database.py            # Pool de conexiones PostgreSQL
│   ├── auth.py                # Autenticación JWT
│   ├── models.py              # Modelos Pydantic
│   ├── seat_service.py        # Lógica de negocio de asientos
│   ├── ws_manager.py          # Gestor de WebSockets
│   ├── cleaner.py             # Thread de limpieza de reservas
│   ├── concert_loader.py      # Cargador de recitales desde JSON
│   ├── race_logger.py         # Logger de race conditions
│   └── payment_stub.py        # Stub de procesamiento de pagos
├── frontend/                   # Frontend HTML/CSS/JS
│   ├── index.html             # Página de login
│   ├── concerts.html          # Listado de recitales
│   ├── seats.html             # Selección de asientos
│   ├── payment.html           # Confirmación de compra
│   └── static/
│       ├── css/style.css      # Estilos globales
│       └── js/app.js          # Utilidades JavaScript
├── db/                         # Scripts de base de datos
│   ├── schema.sql             # Definición de tablas
│   └── seed.sql               # Datos de prueba
├── data/                       # Datos de recitales en JSON
│   ├── recital_rock_nacional.json
│   └── recital_pop_internacional.json
├── logs/                       # Logs de la aplicación
├── tests/                      # Pruebas
│   └── concurrent_test.py     # Pruebas de concurrencia
├── requirements.txt            # Dependencias Python
├── init_db.sh                 # Script de inicialización de BD
└── run_server.sh              # Script para ejecutar el servidor
```

## 🔧 Configuración

### Variables de Entorno

```bash
# Base de datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ticketdb
DB_USER=ticketuser
DB_PASSWORD=ticketpass
DB_MIN_CONNECTIONS=5
DB_MAX_CONNECTIONS=20

# Servidor
HOST=0.0.0.0
PORT=8000

# Reservas
RESERVATION_TIMEOUT_MINUTES=5       # Tiempo de reserva temporal
PURCHASE_TIMEOUT_MINUTES=10         # Tiempo total de compra

# Limpieza
CLEANUP_INTERVAL_SECONDS=30         # Intervalo de limpieza de reservas expiradas

# JWT
SECRET_KEY=supersecretkey-change-in-production-2026
```

## 🎨 Flujo del Usuario

1. **Login**: Autenticación con usuario/contraseña
2. **Seleccionar Recital**: Ver lista de conciertos disponibles
3. **Elegir Asientos**: Seleccionar asientos visualmente con actualizaciones en tiempo real
4. **Reservar**: Reservar los asientos por 10 minutos
5. **Pagar**: Confirmar la compra (pago simulado)
6. **Confirmación**: Entradas compradas exitosamente

## 🔐 Manejo de Concurrencia

### Estrategia Principal: Atomicidad en BD

La reserva de asientos se realiza mediante una consulta UPDATE con cláusula WHERE:
```sql
UPDATE seats
SET status = 'reserved', reserved_by = %s, ...
WHERE id = %s AND status = 'available'
```

Esta estrategia garantiza que:
- Solo el primer usuario que ejecute la consulta obtendrá el asiento
- Los demás recibirán `rowcount = 0` (race condition)
- Las race conditions se registran en logs

### Conceptos de SO Utilizados

- **Threads**: ReservationCleaner (limpieza automática)
- **Locks (OS-level)**: threading.Lock para WebSocket manager
- **Connection Pool**: psycopg2 ThreadedConnectionPool
- **Sincronización**: threading.Event para parar el cleaner
- **Atomicidad en BD**: Transacciones y consultas atómicas

## 📝 Logging

Los logs se guardan en `logs/`:
- **race_conditions.log**: Registro de condiciones de carrera detectadas
- Salida estándar: Logs generales de la aplicación

### Ejemplo de Log de Race Condition
```
2026-05-25 19:45:32 [RACE_CONDITION] Asiento ID:145 (CAMPO A1) del recital 'Rock Nacional: La Gran Noche' - Usuario 'testuser5' (ID:7) intentó reservar un asiento ya tomado por otro usuario. Solo 1 usuario obtuvo el asiento. Thread: ThreadPoolExecutor-0_0
```

## 🔄 API Endpoints

### Autenticación
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Obtener usuario actual

### Recitales
- `GET /api/concerts` - Listar recitales
- `GET /api/concerts/{concert_id}` - Obtener detalle de recital
- `GET /api/concerts/{concert_id}/seats` - Obtener asientos

### Asientos
- `GET /api/concerts/{concert_id}/my-seats` - Asientos reservados del usuario
- `POST /api/seats/reserve` - Reservar asientos
- `POST /api/seats/release` - Liberar asientos
- `POST /api/seats/confirm` - Confirmar compra

### Pagos
- `POST /api/payment/process` - Procesar pago (simulado)

### Admin
- `GET /api/admin/race-conditions` - Ver historial de race conditions

### WebSocket
- `WS /ws/{concert_id}` - Conexión WebSocket para actualizaciones en tiempo real

## 🐛 Troubleshooting

### Error: "database connection failed"
Verifica que PostgreSQL está corriendo y que las credenciales son correctas.

### Error: "Could not find user"
Reinicializa la BD ejecutando `./init_db.sh`

### Error: "Address already in use"
El puerto 8000 está en uso. Cambia el puerto:
```bash
PORT=8001 ./run_server.sh
```

### WebSocket no conecta
Verifica que estés usando `ws://` (o `wss://` para HTTPS) en la URL. El navegador debe estar en la misma conexión.

## 📚 Referencias de Concurrencia

### Race Conditions
Una race condition ocurre cuando dos o más threads acceden al mismo recurso sin sincronización. En este sistema:
- **Problema**: Dos usuarios intentan reservar el mismo asiento simultáneamente
- **Solución**: La BD garantiza atomicidad - solo uno obtiene el asiento
- **Detección**: El otro recibe `rowcount = 0` y se registra la condición

### Deadlock Prevention
El sistema evita deadlocks mediante:
- Reservas siempre en el mismo orden
- Transacciones cortas y precisas
- No se mantienen locks entre transacciones
- Timeout de 10 minutos en reservas temporales

### Thread Safety
- **WebSocket Manager**: Usa `threading.Lock` (primitiva de SO)
- **Connection Pool**: psycopg2 proporciona sincronización interna
- **Reserva Cleaner**: Thread daemon con Event para parada limpia

## 📄 Licencia

Este proyecto es parte de un trabajo académico de Programación Concurrente.

## 👤 Autor

Kevin Arias - kevinnahuelarias@gmail.com
