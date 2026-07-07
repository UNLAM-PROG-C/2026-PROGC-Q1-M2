# Patrones de Diseño

Este documento describe los patrones de diseño **implementados en el backend** del
Sistema de Venta de Entradas para Recitales. Para cada uno se detalla su intención,
el problema concreto que resuelve dentro del proyecto, dónde vive en el código y las
consideraciones de concurrencia relevantes (el eje central del trabajo).

> Referencia conceptual: [Refactoring Guru — Design Patterns](https://refactoring.guru/design-patterns).

---

## 🔒 Singleton

**Categoría:** Creacional.

### Intención

Garantizar que una clase (o recurso) tenga **una única instancia** en todo el proceso
y proveer un punto de acceso global a ella.

### Problema que resuelve en este proyecto

Varios recursos deben existir **una sola vez** y ser compartidos por todos los threads
que atienden requests HTTP y por el thread de limpieza:

- El **pool de conexiones** a PostgreSQL: crear más de un pool desperdiciaría
  conexiones y rompería el límite `max_connections` del servidor de base de datos.
- El **gestor de WebSockets**: todas las notificaciones en tiempo real deben pasar por
  la misma tabla de conexiones; dos instancias significarían clientes "invisibles"
  entre sí.
- El **logger de race conditions** y el **thread cleaner**: deben ser únicos para no
  duplicar archivos de log ni tareas de fondo.

### Implementación

En Python el patrón se resuelve idiomáticamente con **estado a nivel de módulo**
(el módulo se importa una sola vez y se cachea en `sys.modules`), reforzado con
*lazy initialization* y bloqueo cuando la creación debe ser *thread-safe*.

**Pool de conexiones — `backend/database.py`** (con *double-checked locking*):

```python
_pool = None
_pool_lock = threading.Lock()

def init_pool():
    global _pool
    with _pool_lock:                      # exclusión mutua en la creación
        if _pool is None:                 # segunda comprobación dentro del lock
            _pool = ConnectionPool(...)

def get_pool():
    if _pool is None:                     # primera comprobación (rápida, sin lock)
        init_pool()
    return _pool
```

**Gestor de WebSockets — `backend/ws_manager.py`:**

```python
class ConnectionManager:
    ...

manager = ConnectionManager()   # única instancia, importada como singleton
```

Otros singletons del sistema: `_logger` en `backend/race_logger.py` y `_cleaner` en
`backend/cleaner.py`.

### Consideraciones de concurrencia

- La inicialización del pool usa **double-checked locking**: la comprobación rápida
  sin lock evita el costo de adquirirlo en el *happy path*, y la segunda comprobación
  **dentro** del lock evita que dos threads creen dos pools en una carrera de arranque.
- Una vez creado, el pool es internamente *thread-safe* (psycopg lo sincroniza), por lo
  que el singleton puede compartirse entre todos los handlers sin locks adicionales.

### Trade-offs

- ✅ Un único punto de acceso; evita duplicar recursos caros.
- ⚠️ Estado global: dificulta el aislamiento en tests. Se mitiga con `close_pool()` /
  `init_pool()`, que permiten reiniciar el recurso entre ejecuciones.

---

## 📡 Observer (Publish–Subscribe)

**Categoría:** De comportamiento.

### Intención

Definir una dependencia **uno-a-muchos** entre objetos, de forma que cuando el
*sujeto* cambia de estado, todos sus *observadores* sean notificados automáticamente,
sin que el sujeto conozca sus detalles concretos.

### Problema que resuelve en este proyecto

Cuando un asiento cambia de estado (`reserved`, `released`, `sold`), **todos los
usuarios que están mirando ese recital** deben verlo reflejado al instante, sin recargar
la página. El backend no debe acoplarse a cuántos clientes hay ni a quiénes son: solo
"publica" el cambio y el gestor lo entrega a los suscriptores.

- **Sujeto observado:** el recital (`concert_id`).
- **Observadores:** cada navegador conectado por WebSocket a ese recital.
- **Evento:** un mensaje JSON con el nuevo estado del asiento.

### Implementación

**Registro y notificación de observadores — `backend/ws_manager.py`:**

```python
class ConnectionManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._connections: Dict[int, Set[WebSocket]] = {}   # concert_id -> observadores

    async def connect(self, concert_id, websocket):         # suscribirse
        await websocket.accept()
        with self._lock:
            self._connections.setdefault(concert_id, set()).add(websocket)

    def disconnect(self, concert_id, websocket):            # desuscribirse
        with self._lock:
            self._connections.get(concert_id, set()).discard(websocket)

    async def broadcast_to_concert(self, concert_id, message):   # notificar a todos
        with self._lock:
            connections = list(self._connections.get(concert_id, set()))
        for websocket in connections:
            await websocket.send_json(message)
```

**Publicación del evento desde la lógica de negocio — `backend/seat_service.py`:**

```python
for seat in reserved:
    ws_manager.broadcast_from_thread(
        concert_id,
        {"type": "seat_reserved", "seat_id": seat["id"], "status": "reserved"},
    )
```

El `seat_service` no sabe cuántos clientes hay ni cómo se les envía el mensaje: solo
publica el cambio. El `ConnectionManager` se encarga de la entrega.

### Consideraciones de concurrencia

Este es el punto donde el patrón se cruza con el eje del trabajo:

- Los eventos se **publican desde threads worker** (handlers HTTP y el thread
  `ReservationCleaner`), pero los WebSockets viven en el **event loop asíncrono** de
  FastAPI. El puente se resuelve con `broadcast_from_thread`, que usa
  `asyncio.run_coroutine_threadsafe` para agendar la notificación en el loop:

  ```python
  def broadcast_from_thread(self, concert_id, message):
      if self._loop and not self._loop.is_closed():
          asyncio.run_coroutine_threadsafe(
              self.broadcast_to_concert(concert_id, message), self._loop,
          )
  ```

- La tabla de observadores (`_connections`) es un recurso compartido: se protege con
  `threading.Lock` en todas las operaciones (`connect`, `disconnect`, `broadcast`).
- El *broadcast* copia la lista de conexiones **dentro** del lock y luego envía **fuera**
  de él, para no mantener el lock tomado durante el I/O de red y evitar bloquear a otros
  threads. Las conexiones muertas detectadas al enviar se limpian en un segundo paso.

### Trade-offs

- ✅ Desacopla la lógica de negocio de la entrega en tiempo real; agregar nuevos tipos
  de evento no requiere tocar a los productores.
- ✅ Escala a N clientes por recital sin cambios en `seat_service`.
- ⚠️ Las notificaciones se mantienen en memoria del proceso: no escalan *horizontalmente*
  a múltiples procesos sin un *message broker* (ej. Redis Pub/Sub). La **correctitud** de
  las reservas no depende de esto, porque se delega a la atomicidad de la base de datos.

---

## Resumen

| Patrón     | Categoría      | Archivo(s)                              | Rol en el sistema                                          |
|------------|----------------|-----------------------------------------|------------------------------------------------------------|
| Singleton  | Creacional     | `database.py`, `ws_manager.py`, `race_logger.py`, `cleaner.py` | Instancia única de recursos compartidos (pool, gestor WS, logger, cleaner). |
| Observer   | Comportamiento | `ws_manager.py` (+ `seat_service.py`, `cleaner.py` como productores) | Notificar en tiempo real los cambios de asientos a todos los clientes del recital. |
