# Dataset sintetico de originacion crediticia

## Lote productivo de demostracion

El 15 de julio de 2026 se cargo en Supabase el lote determinista
`credit-bureau-demo-2026-01` (`a18be2e9-eb48-5629-99e4-3b2e3ddddec1`). Todas sus
personas tienen `is_synthetic = true`, una cedula reservada que comienza por `99`, nombres
terminados en `Demo` y trazabilidad mediante `dataset_batch_id`.

| Entidad | Filas generadas |
| --- | ---: |
| Personas | 10.000 |
| Cuentas de credito | 21.747 |
| Pagos historicos | 386.981 |
| Puntajes | 10.000 |
| Consultas crediticias | 24.494 |
| Eventos de riesgo | 836 |

La validacion transaccional confirmo 10.000 cedulas unicas, 10.000 telefonos unicos,
cero formatos invalidos, cero cuentas huerfanas y cero pagos huerfanos. Tras la carga, la
base completa ocupaba aproximadamente 103 MB.

Distribucion del ultimo puntaje por persona:

| Riesgo | Personas |
| --- | ---: |
| Bajo | 4.341 |
| Medio | 3.093 |
| Alto | 2.566 |

## Perfiles para pruebas manuales

| Cedula | Perfil | Ingreso reportado | Puntaje | Riesgo |
| --- | --- | ---: | ---: | --- |
| `9900009534` | empleado | USD 2.760,88 | 700 | bajo |
| `9900004853` | independiente | USD 1.883,32 | 580 | medio |
| `9900009740` | estudiante | USD 527,47 | 300 | alto |

Estos casos permiten probar respuestas diferentes, pero no garantizan un resultado por si
solos: monto, plazo, gastos, deudas, autorizaciones y reglas vigentes tambien influyen.

## Reproducibilidad y retiro

El generador esta en `backend/scripts/generate_synthetic_credit_data.py`. Una misma clave,
semilla y fecha de referencia produce los mismos identificadores y distribuciones. La carga
se ejecuta en una sola transaccion; si una insercion o validacion falla, no queda un lote
parcial visible.

`credit_bureau.dataset_batches` conserva semilla, version, volumen solicitado, conteos
obtenidos, estado y resumen de validacion. Las relaciones del lote usan borrado en cascada,
por lo que un administrador puede retirarlo por su `batch_key` sin mezclarlo con registros
anteriores.

## Limites de uso

- No contiene datos personales reales ni debe combinarse con ellos para entrenar o medir
  un modelo de riesgo productivo.
- Sus correlaciones son plausibles para integracion, interfaz, dialogo y pruebas de reglas;
  no representan la poblacion ecuatoriana ni sirven para inferencia estadistica real.
- Los productos y umbrales cargados son demostrativos, no una oferta ni una politica
  crediticia aprobada.
- Una decision formal requiere identidad e ingresos verificados, debida diligencia,
  autorizacion de consulta, politica aprobada y revision humana cuando corresponda.

El fundamento regulatorio y funcional del modelo se encuentra en
[`modelo-originacion-crediticia-ecuador.md`](modelo-originacion-crediticia-ecuador.md).
