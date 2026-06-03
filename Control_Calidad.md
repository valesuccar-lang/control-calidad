# Problema: Control de Calidad — Planta Textil

La gerencia de la planta textil necesita llevar un control del proceso de control de calidad (QA). Este proceso necesita detallarse en sus diferentes actividades para poder generar información de:

- Tiempos de revisión
- Tipo de problema que tiene la tela
- KPI de actividades de los diferentes analistas
- Cuánta tela es aprobada / cuánta tiene problemas de calidad

Las telas con problemas de calidad deben tener un **registro fotográfico**, un comentario del problema y la actividad de corrección a realizar.

El sistema debe contar con **check in y check out**: fecha y hora de entrada y salida del proceso de Calidad (QA). En el proceso de revisión debe haber pasos de verificación por analistas y el jefe de calidad.

---

## Objetivo

Crear un asistente que tenga el control detallado de calidad de la planta textil.

---

## Beneficios Esperados

- Llevar control de actividades de los operarios.
- Registrar el tiempo que tarda la revisión de una tela.
- Reducir consultas repetitivas.
- Estandarizar respuestas.
- Mejorar tiempos de atención.
- Documentar conocimiento disperso.
- Tener KPI del proceso: número de revisiones, tipo de problemas de la tela.

---

## Usuarios

- Jefe de Calidad
- Analista de Calidad
- Jefes de Procesos de planta
- Gerente de Planta

---

## Procesos de Calidad (Los más comunes)

| # | Actividad |
|---|-----------|
| 1 | Se carga la HDR a la sección de calidad |
| 2 | Se abre la fase de calidad |
| 3 | Según el tipo de tejido (plano, punto, tricot) y fibras, se realizan varios análisis |
| 4 | Pruebas de resistencia (tejidos planos) |
| 5 | Prueba de encogimientos (algodones) |
| 6 | Peso de la tela |
| 7 | Ancho de la tela |
| 8 | Rendimiento de la tela |
| 9 | Pilling |
| 10 | Humedad |
| 11 | Grado de blancura |
| 12 | Entorche |
| 13 | Sublimación |
| 14 | Solidez al frote |

---

## Alcance Inicial

Tener todo el proceso de control de calidad. **Solo en el área de calidad.**

## Fuera de Alcance

- Procesos de la planta que no tienen que ver con el proceso de calidad.

---

# Proceso de Calidad — Planta de Producción de Telas
*(Trituración / Estampación / Acabados)*

## Flujo General de Calidad

```
Recepción Tela Base
       ↓
Trituración / Preparación
       ↓
Control de Calidad Proceso 1
       ↓
Estampación
       ↓
Control de Calidad Proceso 2
       ↓
Acabados
       ↓
Control de Calidad Final
       ↓
Liberación de Tela
```

---

## 1. Calidad en Trituración / Preparación de Tela

**Objetivo:** Garantizar que la tela quede uniforme y apta para estampación y acabado.

### Mediciones más comunes

| Medición | Descripción |
|----------|-------------|
| Gramaje | Peso de la tela |
| Ancho útil | Ancho real de la tela |
| Humedad | Nivel de humedad de la tela |
| Uniformidad | Regularidad de la superficie |
| Tensión de tela | Control durante proceso |
| Defectos visuales | Huecos, barras, fibras sueltas |
| Metros procesados | Producción por lote |

### Datos típicos para sistematizar

- Máquina
- Operario
- Lote
- Hora inicio / fin
- Resultado inspección
- Estado: aprobado / reproceso

---

## 2. Calidad en Estampación

**Objetivo:** Garantizar correcta aplicación del diseño y color.

### Mediciones más comunes

| Medición | Descripción |
|----------|-------------|
| Registro del estampado | Alineación del diseño |
| Intensidad de color | Uniformidad tonal |
| Matching color | Comparación contra patrón |
| Repetición del diseño | Exactitud del rapport |
| Manchas | Presencia de contaminación |
| Corrimiento | Desplazamiento del estampado |
| Cobertura | Nivel de cubrimiento |
| Secado | Curado correcto |

### Defectos más comunes

- Desalineación
- Mancha
- Diferencia de tono
- Arrastre de tinta
- Falta de estampado
- Sobre estampado

### Datos clave para el sistema

- Diseño
- Color
- Máquina estampación
- Velocidad
- Temperatura
- Operario
- Metros aprobados / rechazados

---

## 3. Calidad en Acabados

**Objetivo:** Garantizar propiedades finales de la tela.

### Mediciones más comunes

| Medición | Descripción |
|----------|-------------|
| Encogimiento | Variación después de lavado |
| Tacto | Suavidad |
| Elasticidad | Recuperación |
| Solidez del color | Resistencia lavado / frote |
| Torque | Deformación de tela |
| Ancho final | Validación especificación |
| Gramaje final | Peso final |
| Apariencia visual | Arrugas, marcas, manchas |

### Pruebas comunes

- Lavado
- Frote seco / húmedo
- Temperatura
- Estabilidad dimensional

---

## 4. Auditoría Final de Calidad

**Objetivo:** Liberar o rechazar lotes de tela.

### Mediciones más comunes

| Medición | Descripción |
|----------|-------------|
| Metros inspeccionados | Cantidad revisada |
| Puntos por defecto | Sistema 4 puntos |
| % defectos | Calidad del lote |
| Clasificación defecto | Crítico, mayor, menor |
| Resultado final | Aprobado / Rechazado |

---

## Indicadores más comunes (KPIs)

| Indicador | Fórmula |
|-----------|---------|
| % Rechazo | Tela rechazada / producida |
| DHU | Defectos por 100 unidades |
| Metros defectuosos | Metros con falla |
| Reproceso | Tela enviada a corrección |
| Eficiencia calidad | Producción aprobada |

---

## Procesos recomendados para sistematizar primero

### Prioridad Alta

1. Inspección en estampación
2. Auditoría final
3. Registro de defectos
4. Trazabilidad por lote
5. Control de color y tono

### Prioridad Media

- Calidad en trituración
- Pruebas laboratorio
- Gestión reprocesos

---

## Catálogo típico de defectos

### Trituración
- Fibra abierta
- Hueco
- Tensión irregular
- Barra

### Estampación
- Mancha
- Corrimiento
- Desalineación
- Diferencia de tono
- Arrastre de tinta

### Acabados
- Encogimiento excesivo
- Marca
- Rigidez
- Torque
- Cambio de color

---

## Estructura ideal del sistema

### Maestros
- Máquinas
- Lotes
- Diseños
- Colores
- Defectos
- Operarios

### Transacciones
- Inspección proceso
- Auditoría final
- Registro defectos
- Reproceso
- Liberación lote

### Reportes
- Pareto defectos
- Calidad por máquina
- Calidad por diseño
- Calidad por lote
- Tendencia rechazos
- KPI diarios / turno
