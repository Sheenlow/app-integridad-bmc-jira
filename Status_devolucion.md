# Devolución — `app-integracion`

## Resumen ejecutivo

El refactor de la capa defensiva de Jira quedó bien, pero dejó **tres asimetrías/olvidos** que, a mi criterio, son lo primero que atacaría:

1. **BMC no tiene la misma capa defensiva que Jira** — arreglaste la fragilidad de un lado y la dejaste intacta del otro.
2. **La lógica de colores está duplicada en 5 lugares** y ahora quedó "aplastada" (todos los "Revisar" son el mismo naranja).
3. **No hay tests de las funciones exactas que tenían el bug** (`_agregar_columnas_conciliacion`, `_formatear_output_conciliacion`).

---

## 1. Robustez / arquitectura (lo más importante)

### 1.1 BMC sigue siendo frágil (asimetría)
La ingesta de Jira ahora normaliza tildes, caso y alias. Pero `normalizar_bmc_wo` y `normalizar_bmc_pbi` en `src/transform.py` siguen matcheando **literalmente**:
- `ID Propuesta` → si BMC exporta `Id Propuesta`, `ID de la propuesta` o `ID Propuesta ` (espacio final), devuelve `None` silencioso.
- La columna de estado usa `_renombrar_columna_estado` con `["Estado", "Status", "state", "estado"]` — **case-sensitive y literal**. `ESTADO`, `Estado ` (con espacio) o `Estado de la WO` no se detectan.

El mismo bug de descalce que arreglaste para Jira sigue latente en BMC. La solución natural es **reutilizar `normalizar_texto` + un `ALIASES_BMC`** en `constants.py`, simétrico a `ALIASES_JIRA`. Es más trabajo, pero hoy el pipeline es "defensivo de un solo lado".

### 1.2 Acoplamiento reglas ↔ enriquecimiento
`aplicar_reglas_negocio` corre **antes** que `_agregar_columnas_conciliacion` en `app.py`, así que las reglas leen `Proceso`/`Estado propuesta` por su nombre fuente (por eso `_buscar_columna` prueba `[canonico, fuente]`). Funciona, pero es un acoplamiento sutil: el orden del pipeline importa y no está documentado en ningún lado. Una refactorización futura puede romperlo sin darse cuenta. Lo haría explícito: o reordenar el pipeline (agregar columnas antes de reglas) o documentar fuerte el contrato.

### 1.3 Errores enmascarados en lectura
`leer_archivo_robusto` hace `except Exception` y sigue bajando en cascada (Excel → CSV → HTML). Si openpyxl falla por una **razón real** (no por corrupto), el error se pierde y al final larga un `ValueError` genérico. Perdés la causa raíz. Agregaría el `exc_xlsx`/`exc_csv` original al mensaje final o un `logger.warning` con el detalle.

---

## 2. Bugs / deuda técnica detectada (con evidencia)

| Item | Estado | Dónde |
|---|---|---|
| `_leer_archivo_cache` definida pero **nunca llamada** | Código muerto | `app.py:49` |
| `EQUIVALENCIAS` ya **no se usa** (quedó huérfano tras el rewrite) | Código muerto | `src/constants.py:190` |
| Ramas de color `Falta` / `Sobra` / `Actualizar` **inalcanzables** | Código muerto | `app.py:439-443` y `535-539` |
| `VERSION = "v1.1"` sin bump pese a 2 refactors grandes | Deriva | `src/constants.py:261` |
| `AGENTS.md` dice que `rules.py` depende de `EQUIVALENCIAS` + `_JIRA_A_BMC` | **Falso hoy** | `AGENTS.md` |
| `AGENTS.md`/`README` decían "30 tests" | Desactualizado (hoy 53) | `AGENTS.md` |

Los tres primeros son fáciles de limpiar. Los dos últimos son deriva de documentación que te va a morder cuando otro agente/persona lea el repo.

---

## 3. UX/UI (cosas concretas)

### 3.1 El naranja "aplastó" la distinción que acabás de ganar
Ahora tenés **tres** mensajes distintos (`Falta en Jira`, `Sobra en Jira`, `Estado en incongruencia con Jira`) que arrancan con "Revisar" → los tres caen en el mismo naranja. Irónicamente, el código viejo **ya tenía** colores más granulares (Falta=ámbar, Sobra=rojo). Mi recomendación:

- `Revisar: Falta en Jira` → **ámbar** (hay que crear)
- `Revisar: Sobra en Jira` → **rojo** (hay que borrar/revisar)
- `Revisar: Estado en incongruencia...` → **naranja** (hay que corregir estado)
- `OK` → verde

Esto es un win de UX directo: de un vistazo sabés si es crear, borrar o corregir.

### 3.2 Falta un "resumen ejecutivo" arriba
Hoy tenés métricas sueltas (`both`/`left_only`/`right_only`) y después la tabla filtrada. Faltaría un **dashboard de cabecera**: "X OK · Y Falta en Jira · Z Sobra en Jira · W incongruencias", con los totales ya calculados. El usuario no debería tener que filtrar para saber el estado general.

### 3.3 Colores duplicados en 5 lugares
La paleta OK/Revisar/… está hardcodeada en:
- `_color_accion` (tab2 conciliación)
- `_color_fila_accion` (tab3 conciliación)
- `_color_validacion` (tab2 épicas)
- `_color_fila_validacion` (tab3 épicas)
- `formatear_excel` (dict `colores`)

Son 4 funciones casi idénticas + 1 dict. Deberían ser **una sola función compartida** (ej. `color_accion(valor)` en `ui.py` o un módulo de estilos) que reciba el valor y devuelva el estilo. Así, cambiar un color es tocar UN lugar (esto costó 5 edits recién).

### 3.4 HTML inline frágil
`ui.py` y `app.py` usan `unsafe_allow_html=True` con CSS inline y selectores `[data-testid="..."]` de Streamlit (ej. `stSidebar`, `stMetric`). Son selectores **no estables** (cambian entre versiones de Streamlit sin aviso). El badge de "cargado" y los headers del sidebar podrían ser componentes nativos (`st.caption`, `st.markdown` simple) o al menos aislar todo el CSS en un único lugar (hoy está repartido entre `ui.py` y los `st.markdown` inline de `app.py`).

### 3.5 Feedback de error para BMC
Jira tiene warnings de "columna no detectada". BMC no: si falta `ID Propuesta`, `normalizar_bmc_wo` devuelve `None` y en la UI simplemente no aparece la tabla. El usuario no sabe si el archivo está mal o si el reporte cambió. Mismo tratamiento de warning que Jira.

---

## 4. Testing

### 4.1 Vacío exacto donde estaba el bug
No hay tests de `_agregar_columnas_conciliacion` ni de `_formatear_output_conciliacion` — que son, justamente, las funciones donde estaba el bug de `CELULA`/`CATEGORIA DE ESTADO` vacías. Un **test de integración** del pipeline completo (`cruzar → reglas → agregar → formatear`) con un Jira con tildes habría atrapado el bug original y habría prevenido la regresión. Es la primera prueba que agregaría.

### 4.2 Aserciones débiles
- `test_epics.py:54` hace `assert "Revisar" in accion` (substring, poco estricto).
- El viejo `test_both_sincronizado` usaba `any("OK" in ...)` — vacuo si cambia la data.

### 4.3 Cobertura faltante
- Sin tests de `excel_export.formatear_excel` (y tiene un edge case: si `df` viene vacío, `.max()` de una serie vacía devuelve `NaN` y rompe el auto-ajuste).
- Sin tests de la normalización BMC (porque todavía no es defensiva).
- Sin test de extracción de `BMC_ID` con formatos raros (`WO001` vs `WO-001`).

---

## 5. Mantenibilidad

### 5.1 `app.py` es un monolito de ~800 líneas
Todo el renderizado de tabs, los 4 `_color_*` duplicados, y los buffers de exportación Excel viven en el mismo archivo. Yo extraería: (a) los renderizadores de tabs a funciones/módulos, (b) la paleta de colores a `ui.py`, (c) la construcción de los Excel de descarga a `excel_export.py` (hoy el armado de `BytesIO` + `pd.ExcelWriter` está duplicado en tab2 y tab3, y entre modos).

### 5.2 Strings de acción duplicados entre `rules.py` y la UI
Los mensajes (`"Revisar: Falta en Jira"`, etc.) viven en `rules.py` como constantes, pero el popover de ayuda de `app.py` los lista a mano y los `startswith("Revisar")` de los colores los referencian por prefijo. Si mañana cambiás un mensaje, la ayuda y el color se desincronizan. Centralizaría los prefijos/categorías.

### 5.3 Versionado
`VERSION = "v1.1"` no refleja dos cambios de comportamiento grandes. Lo subiría a `v1.3` o `v2.0` (el cambio de reglas de negocio es semver-minor/major).

---

## 6. Menor / nice-to-have

- **URLs hardcodeadas** (`URL_WO_BMC`, filtros Jira) en `constants.py`: pasaría a un `.env` o config externa; hoy un cambio de orgId/filter exige editar código.
- **Cache**: `_pipeline_conciliacion` recibe los DataFrames completos como argumentos (sin prefijo `_`), así que Streamlit los hashea además del `_hash_*`. Redundante y más lento; alcanza con los hashes.
- **`selectbox` dentro de un condicional** en `leer_archivo_subido` (elección de hoja): anti-patrón leve de Streamlit; preferible un widget siempre presente.
- **`resumen.md`** (el que te generé) quedó desactualizado respecto a las reglas nuevas; si lo usás para Gemini, hay que regenerarlo.
- **Encoding**: el parser ZIP/XML no contempla `t="str"` (fórmulas como string) ni `xml:space="preserve"`; es borde, pero si aparece un `.xlsx` raro puede dar valores mal.
- **Detección de duplicados**: `detectar_columnas_duplicadas` avisa pero deja que pandas renombre con sufijos `.1/.2` — eso puede cambiar qué columna resuelve el alias. Convendría avisar más fuerte o abortar.

---

## Qué haría primero (mi top 5 en orden)

1. **Test de integración del pipeline completo** (cruzar → reglas → agregar → formatear) con Jira con tildes. Es la red de seguridad que faltó.
2. **Simetrizar la normalización defensiva a BMC** (`ALIASES_BMC` + `normalizar_texto`), porque el bug no está muerto, está del otro lado.
3. **Centralizar los colores** en una sola función y **diferenciar los subtipos de "Revisar"** (ámbar/rojo/naranja).
4. **Limpiar código muerto** (`_leer_archivo_cache`, `EQUIVALENCIAS`, ramas `Falta/Sobra/Actualizar`) y **bump de versión**.
5. **Actualizar `AGENTS.md`** (quitar la mención a `EQUIVALENCIAS`, corregir conteo de tests) para no confundir al próximo agente.
