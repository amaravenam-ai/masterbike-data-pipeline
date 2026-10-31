# Datos y reglas de demostración

Los seis JSON son fixtures sintéticos con errores deliberados. El orden es ingesta, validación, transformación y almacenamiento; transformar no rescata un registro ya rechazado. Las validaciones enumeradas son locales: no comprueban referencias contra los microservicios ni contra personas reales.

| Fuente | Criterios principales | Transformación de registros aceptados |
|---|---|---|
| Ventas | IDs positivos, fecha válida, total mayor que cero, estado PAGADA/PENDIENTE/CANCELADA | IDs y total a tipos numéricos; total a dos decimales; estado en mayúsculas |
| Usuarios | ID positivo, nombre requerido (máx. 100), correo con formato válido, rol ADMINISTRADOR/TECNICO/VENDEDOR | Nombre en formato título, correo en minúsculas, rol en mayúsculas |
| Inventario | ID positivo, nombre requerido (máx. 150), categoría Repuesto/Accesorio/Equipamiento, stock no negativo, mínimo positivo | Tipos enteros, nombre/categoría en formato título, estado de stock derivado |
| Arriendos | IDs positivos, fechas válidas y fin no anterior al inicio, costo positivo | Tipos numéricos y duración inclusiva en días |
| Bicicletas | ID positivo, código requerido, tipo Montana/Ruta/Urbana, estado DISPONIBLE/MANTENCION/ARRENDADA, tarifa positiva | Código/estado en mayúsculas, tipo en formato título, tipos numéricos |
| Despachos | IDs positivos, dirección requerida (máx. 250), fecha válida, estado EN_PREPARACION/EN_RUTA/PENDIENTE/ENTREGADO | Dirección sin espacios externos, estado en mayúsculas, IDs enteros |

El código de app/validation y app/transformations determina los detalles exactos (incluida normalización al comparar enumeraciones). Las tablas raw guardan la entrada; clean, la transformación aceptada; error, el rechazo y su motivo. Cada ejecución tiene un UUID distinto. Repetir una fuente añade otra ejecución y sus filas; no deduplica ni reemplaza ejecuciones anteriores.

Un archivo ausente, JSON ilegible o raíz que no sea un array produce FAILED. Una lista vacía produce COMPLETED con cero filas. Un registro inválido se rechaza y se cuenta en error sin impedir que el lote finalice. Una base no disponible impide persistir y responde con error; si no se pudo crear el run, no habrá historial de ese intento.
