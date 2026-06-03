# DESIGN.md — Sistema de Gestión de Control de Calidad Textil

**Versión**: 1.0  
**Última actualización**: 2026-06-01  
**Estado**: Listo para Desarrollo  
**Audiencia**: Designers, Developers, Product Managers

---

## 1. Identidad Visual y Marca

### Logo
🦁 **León en Azul** — Representa fortaleza, confianza y liderazgo en control de calidad.
- **Tamaño principal**: 200x200px
- **Tamaño favicon**: 32x32px
- **Uso**: Header, logo app, branding
- **Espaciado mínimo**: 20px alrededor

### Nombre
**Manufacturas Eliot — Control de Calidad**  
O simplemente: **"QA Lion"** (sobrenombre interno)

---

## 2. Paleta de Colores

### Colores Primarios (Azul Intermedio)

```
Azul Intermedio (Primary)    #0066CC  — Confianza, profesionalismo, principal
Azul Oscuro (Dark)           #004A99  — Focus, hover, énfasis
Azul Claro (Light)           #E6F0FF  — Fondos, superficies
Blanco (White)               #FFFFFF — Fondos principales, texto claro
```

### Colores de Estado (Especialización Textil)

```
Aprobado (Success)     #10B981  — PASS, tela OK, defecto resuelto
Rechazo (Error)        #EF4444  — FAIL, defecto crítico, rechazado
Pendiente (Warning)    #F59E0B  — PENDING, bajo revisión, requiere acción
Información (Info)     #3B82F6  — Nota, información, contexto
```

### Colores Neutrales

```
Negro (Text Primary)         #1F2937  — Texto principal, máximo contraste
Gris Oscuro (Text Secondary) #6B7280  — Texto secundario, etiquetas
Gris Medio (Borders)         #D1D5DB  — Bordes, separadores, líneas
Gris Claro (Surfaces)        #F3F4F6  — Fondos suaves, superficies elevadas
Blanco (White)               #FFFFFF — Fondos puros
```

### Paleta Expandida (Tailwind Compatible)

```css
:root {
  /* Primarios */
  --color-primary-dark: #004A99;
  --color-primary: #0066CC;
  --color-primary-light: #E6F0FF;
  
  /* Estados */
  --color-success: #10B981;
  --color-error: #EF4444;
  --color-warning: #F59E0B;
  --color-info: #3B82F6;
  
  /* Neutrales */
  --color-text-primary: #1F2937;
  --color-text-secondary: #6B7280;
  --color-border: #D1D5DB;
  --color-surface: #F3F4F6;
  --color-white: #FFFFFF;
}
```

### Contraste WCAG AA

| Combinación | Ratio | Status |
|-------------|-------|--------|
| #0066CC (Primary) en #FFFFFF (White) | 4.9:1 | ✅ WCAG AA |
| #004A99 (Dark) en #FFFFFF | 6.3:1 | ✅ WCAG AAA |
| #1F2937 (Text) en #FFFFFF | 13:1 | ✅ WCAG AAA |
| #10B981 (Success) en #FFFFFF | 4.5:1 | ✅ WCAG AA |
| #EF4444 (Error) en #FFFFFF | 4.7:1 | ✅ WCAG AA |

**Regla**: Ratio mínimo 4.5:1 para texto pequeño; 3:1 para componentes UI.

---

## 3. Tipografía

### Fuentes del Sistema

```css
/* Primaria (interfaces) */
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;

/* Monoespaciada (código, números) */
font-family: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", "Source Code Pro", monospace;
```

### Escala Tipográfica

| Uso | Tamaño | Peso | Line Height | Uso |
|-----|--------|------|-------------|-----|
| Display | 32px | 600 | 1.2 | Títulos principales de página |
| Heading 1 | 28px | 600 | 1.2 | Títulos de sección principal |
| Heading 2 | 24px | 600 | 1.2 | Subtítulos importantes |
| Heading 3 | 20px | 500 | 1.3 | Encabezados de subsección |
| Body | 16px | 400 | 1.5 | Texto fluido, contenido |
| Small | 14px | 400 | 1.5 | Etiquetas, ayuda, metadata |
| Tiny | 12px | 500 | 1.4 | Timestamps, pequeño contexto |
| Code | 14px | 500 | 1.6 | Código, datos estructurados |

### Pesos y Usos

```
400 (Regular)  — Texto fluido, body
500 (Medium)   — Énfasis moderado, labels, buttons
600 (Semibold) — Headings, acentos
700 (Bold)     — Énfasis fuerte (raro, solo si necesario)
```

### Ejemplos de Uso

```jsx
// Display (página principal)
<h1 className="text-4xl font-semibold leading-tight">
  Bienvenido al Sistema de Calidad
</h1>

// Body + Strong
<p className="text-base leading-relaxed">
  Se encontraron <span className="font-semibold">47 lotes</span> con defectos.
</p>

// Code
<code className="text-sm font-medium">DEF-TON | TONODIFFERENTE</code>
```

---

## 4. Componentes y Patrones

### 4.1 Botones

#### Estados

```
Primary (Default)
━━━━━━━━━━━━━━━━━
Fondo: #0066CC
Texto: #FFFFFF
Padding: 12px 24px
Border-radius: 8px
Font-weight: 500

Primary (Hover)
━━━━━━━━━━━━━━━━━
Fondo: #004A99
Box-shadow: 0 4px 12px rgba(0, 102, 204, 0.3)

Primary (Focus)
━━━━━━━━━━━━━━━━━
Outline: 3px solid #E6F0FF (azul claro)
Outline-offset: 2px

Primary (Disabled)
━━━━━━━━━━━━━━━━━
Fondo: #D1D5DB (gris)
Texto: #6B7280 (gris oscuro)
Cursor: not-allowed
Opacity: 0.6
```

#### Variantes

```
Secondary (Outline)
━━━━━━━━━━━━━━━━━
Fondo: transparent
Border: 2px solid #0066CC
Texto: #0066CC
Hover: Fondo #E6F0FF

Danger (Rojo)
━━━━━━━━━━━━━━━━━
Fondo: #EF4444
Texto: #FFFFFF
Hover: Fondo #DC2626

Ghost (Minimal)
━━━━━━━━━━━━━━━━━
Fondo: transparent
Texto: #0066CC
Hover: Fondo #E6F0FF
```

#### Tamaños

```
Small    — 28px altura, 12px padding vertical
Medium   — 40px altura, 12px padding vertical (default)
Large    — 48px altura, 16px padding vertical
Full     — width: 100%
```

#### Ejemplo React

```jsx
<button className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:bg-gray-400 disabled:cursor-not-allowed">
  Guardar Defecto
</button>
```

---

### 4.2 Formularios

#### Input/Textarea

```
Borde:          1px solid #D1D5DB
Border-radius:  6px
Padding:        12px
Font-size:      16px (para evitar zoom en iOS)
Focus:          Border #0066CC + Ring 3px #E6F0FF
Error:          Border #EF4444 + Icon rojo
Success:        Border #10B981 + Icon verde
Disabled:       Fondo #F3F4F6, opacity 0.5
```

#### Label

```
Font-size:    14px
Font-weight:  500
Margin-bottom: 8px
Color:        #1F2937 (text primary)
Asociación:   <label for="input-id"> (accessibility)
```

#### Validation

```
Error message:   Font-size 12px, color #EF4444
Success message: Font-size 12px, color #10B981
Helper text:     Font-size 12px, color #6B7280, margin-top 4px
```

#### Ejemplo

```jsx
<div className="mb-4">
  <label htmlFor="comment" className="block text-sm font-medium mb-2">
    Comentario del Defecto
  </label>
  <textarea
    id="comment"
    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
    placeholder="Describe el defecto..."
    minLength="10"
    required
  />
  <p className="text-xs text-gray-500 mt-1">Mínimo 10 caracteres</p>
</div>
```

---

### 4.3 Cards

```
Borde:        1px solid #D1D5DB
Border-radius: 8px
Padding:      20px
Fondo:        #FFFFFF
Box-shadow:   0 1px 3px rgba(0, 0, 0, 0.1) (elevación baja)
Hover:        Box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15)
Transición:   box-shadow 300ms ease-in-out
```

#### Variantes

```
Flat (sin shadow):
━━━━━━━━━━━━━━━━━
Box-shadow: none
Border: 1px solid #D1D5DB

Elevated (shadow mayor):
━━━━━━━━━━━━━━━━━
Box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15)

Status:
━━━━━━━━━━━━━━━━━
Borde izquierdo 4px: color por estado (success, error, warning)
```

#### Ejemplo

```jsx
<div className="bg-white rounded-lg p-5 border border-gray-200 hover:shadow-md transition-shadow">
  <h3 className="text-lg font-semibold mb-2">Lote #12847</h3>
  <p className="text-sm text-gray-600">NOVAKREPEL | Tela Premium</p>
  <div className="mt-4 pt-4 border-t border-gray-200 flex justify-between">
    <span className="text-sm font-medium text-green-600">✓ Aprobado</span>
    <time className="text-xs text-gray-500">14:35 hoy</time>
  </div>
</div>
```

---

### 4.4 Status Indicators y Badges

#### Estados Principales

```
Aprobado (Success)
━━━━━━━━━━━━━━━━━
Icono: ✓ o checkmark
Color:     #10B981 (verde)
Texto:     "APROBADO" o "PASS"
Bg:        #ECFDF5 (muy claro)
Ejemplo:   🟢 APROBADO

Rechazado (Error)
━━━━━━━━━━━━━━━━━
Icono: ✗ o X
Color:     #EF4444 (rojo)
Texto:     "RECHAZADO" o "FAIL"
Bg:        #FEF2F2 (muy claro)
Ejemplo:   🔴 RECHAZADO

Pendiente (Warning)
━━━━━━━━━━━━━━━━━
Icono: ⚠ o reloj
Color:     #F59E0B (ámbar)
Texto:     "PENDIENTE" o "REVIEW"
Bg:        #FFFBEB (muy claro)
Ejemplo:   🟡 PENDIENTE

En Revisión (Info)
━━━━━━━━━━━━━━━━━
Icono: ⓘ
Color:     #3B82F6 (azul)
Texto:     "EN REVISIÓN"
Bg:        #EFF6FF (muy claro)
Ejemplo:   🔵 EN REVISIÓN
```

#### Badge Defecto

```
Formato: [CÓDIGO] | [NOMBRE]
Ejemplo: DEF-TON | TONODIFFERENTE

Styling:
━━━━━━━━━━━━━━━━━
Font-size:    12px
Font-weight:  500
Padding:      4px 8px
Border-radius: 4px
Bg:           #F3F4F6 (gris claro)
Color:        #1F2937 (texto oscuro)
Border:       1px solid #D1D5DB
```

---

### 4.5 Tablas (Data Tables)

```
Encabezado:
━━━━━━━━━━━━━━━━━
Bg:           #E6F0FF (azul muy claro)
Font-weight:  600
Font-size:    14px
Padding:      12px
Border-bottom: 2px solid #0066CC
Text-align:   center para estados, izquierda para texto

Filas:
━━━━━━━━━━━━━━━━━
Padding:      12px
Border-bottom: 1px solid #D1D5DB
Alternadas:   Row 1,3,5: #FFFFFF | Row 2,4,6: #F9FAFB
Hover:        Bg #E6F0FF

Densidad:     Compacta (sin mucho padding) para datos
```

#### Ejemplo

```jsx
<table className="w-full">
  <thead>
    <tr className="bg-blue-100">
      <th className="px-4 py-3 text-left text-sm font-semibold">Lote</th>
      <th className="px-4 py-3 text-left text-sm font-semibold">Tela</th>
      <th className="px-4 py-3 text-center text-sm font-semibold">Estado</th>
    </tr>
  </thead>
  <tbody>
    <tr className="border-b hover:bg-blue-50">
      <td className="px-4 py-3">HDR-12847</td>
      <td className="px-4 py-3">NOVAKREPEL</td>
      <td className="px-4 py-3 text-center"><Badge status="approved" /></td>
    </tr>
  </tbody>
</table>
```

---

### 4.6 Modals / Dialogs

```
Overlay:      rgba(31, 41, 55, 0.5) (black 50% opacity)
Modal:        Bg #FFFFFF, border-radius 12px
Max-width:    480px (small), 720px (medium), 1024px (large)
Padding:      24px
Box-shadow:   0 20px 25px rgba(0, 0, 0, 0.15)
Transición:   300ms ease-in-out
```

#### Estructura

```jsx
<div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
  <div className="bg-white rounded-xl p-6 max-w-md w-full">
    <h2 className="text-xl font-semibold mb-4">Confirmar Acción</h2>
    <p className="text-gray-600 mb-6">¿Estás seguro de aprobar este lote?</p>
    <div className="flex gap-3 justify-end">
      <button className="px-4 py-2 border border-gray-300 rounded-lg">Cancelar</button>
      <button className="px-4 py-2 bg-blue-600 text-white rounded-lg">Confirmar</button>
    </div>
  </div>
</div>
```

---

### 4.7 Iconografía

#### Sistema de Iconos

```
Librería:     Heroicons (heroicons.com)
Tamaños:      16px, 20px, 24px, 32px
Stroke-width: 2px (legibilidad)
Color:        Heredar del contexto (text, white, error, success, etc.)
```

#### Iconos Clave (QA)

```
📸 Capturar Foto      — heroicons/camera
✓  Aprobado           — heroicons/check
✗  Rechazado          — heroicons/x-mark
⚠  Pendiente          — heroicons/exclamation-triangle
📊 Análisis           — heroicons/chart-bar
⚙  Configuración      — heroicons/cog-6-tooth
📱 Mobile            — heroicons/device-phone-mobile
📡 Conexión           — heroicons/signal
🔔 Notificación       — heroicons/bell
```

#### Uso

```jsx
import { CheckIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

<button className="flex items-center gap-2">
  <CheckIcon className="w-5 h-5" />
  Aprobar
</button>
```

---

## 5. Layouts y Responsiveness

### Mobile-First Breakpoints

```
Mobile:       320px - 639px   (default)
Tablet:       640px - 1023px  (md:)
Desktop:      1024px+         (lg:)
Large Screen: 1280px+         (xl:)
```

### Estructura Layouts

#### Layout Mobile (Inspección)
```
┌─────────────────┐
│  Header (40px)  │
│  🦁 QA Lion     │
├─────────────────┤
│                 │
│  Main Content   │
│  (full width)   │
│                 │
├─────────────────┤
│ Bottom Action   │
│    (50px)       │
└─────────────────┘
```

#### Layout Tablet/Desktop (Análisis)
```
┌──────────────────────────────────┐
│  Header (60px)                   │
│  🦁 QA Lion | Usuario | Logout   │
├──────────────────────────────────┤
│ Sidebar     │                    │
│ (250px)     │  Main Content      │
│             │  (responsive)      │
│             │                    │
│             │                    │
└──────────────────────────────────┘
```

### Padding y Spacing

```
Mobile:       16px horizontal margin
Tablet:       24px horizontal margin
Desktop:      32px horizontal margin
Vertical:     20px entre secciones
Gutter:       8-16px entre columnas
```

---

## 6. Pantallas y Flujos

### 📱 Screen 1: Home / Dashboard (Analista)

```
┌─────────────────────────┐
│ 🦁 QA Lion              │
├─────────────────────────┤
│                         │
│ Bienvenida, [Nombre]    │
│ Tienes 3 lotes para     │
│ inspeccionar hoy.       │
│                         │
├─────────────────────────┤
│ [Botón Principal]       │
│ 📸 Escanear Lote        │
│                         │
│ [Card 1]                │
│ Lotes Pendientes: 3     │
│                         │
│ [Card 2]                │
│ Últimas Inspecciones: 5 │
│                         │
└─────────────────────────┘
```

### 📱 Screen 2: Escanear Lote

```
┌─────────────────────────┐
│ ← Atrás | Escanear      │
├─────────────────────────┤
│                         │
│ 📱 Cámara Escaneo       │
│                         │
│ (Rect cuadrado para     │
│  enfocar código QR)     │
│                         │
│ O ingresa número:       │
│ [HDR-____-____]         │
│                         │
│         [Buscar]        │
│                         │
└─────────────────────────┘
```

### 📱 Screen 3: Inspección (Principal)

```
┌─────────────────────────┐
│ ← Atrás | Inspeccionar  │
├─────────────────────────┤
│                         │
│ HDR #12847              │
│ NOVAKREPEL | 500m       │
│ Flujo: AGOTAMIENTO 80   │
│ Estación: POST-AGOT 80  │
│ Check-in: 14:32         │
│ ⏱ 03:22 (contador)      │
│                         │
├─────────────────────────┤
│                         │
│ [📸 Capturar Defecto]   │
│                         │
│ ¿Foto capturada?        │
│ ☐ No | ☑ Sí            │
│                         │
│ [Tipo Defecto]          │
│ ↙ Selecciona...         │
│                         │
│ [Comentario]            │
│ Describe el defecto...  │
│ (10 caracteres mín)     │
│                         │
│ Máquina Culpable:       │
│ Est: AGOTAMIENTO 80     │
│ [✓ Confirmar] [Cambiar]│
│                         │
│        [Guardar]        │
│                         │
└─────────────────────────┘
```

### 💻 Screen 4: Dashboard Jefe QA (Desktop)

```
┌────────────────────────────────────────────────────────────┐
│ 🦁 QA Lion        Jefe QA, [Nombre]           ⚙️  Logout   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ 📊 Lotes Pendientes: 12                                   │
│                                                            │
│ [Card 1]            [Card 2]            [Card 3]         │
│ Hoy: 45 lotes      Semana: 200 lotes   Aprobación: 85%   │
│                                                            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ Filtros:                                                  │
│ [Período: Últimas 24h ↙] [Defecto: Todos ↙]              │
│ [Máquina: Todas ↙]      [Status: Pendiente ↙]            │
│                                                            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ # | Lote      | Tela       | Defecto   | Estado | Acciones│
│ 1 | HDR-12847 | NOVAKREPEL | TONODIFF  | ⚠ PEND | [A] [R] │
│ 2 | HDR-12846 | AMORELA    | MANCHAS   | ⚠ PEND | [A] [R] │
│ 3 | HDR-12845 | SUEA OS    | MAREO     | ⚠ PEND | [A] [R] │
│                                                            │
│                      [Ver Más]                            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 💻 Screen 5: Análisis (Gerente)

```
┌────────────────────────────────────────────────────────────┐
│ 🦁 QA Lion        Gerente, [Nombre]          ⚙️  Logout    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ KPIs - Últimas 24h                                        │
│                                                            │
│ [Card 1]           [Card 2]            [Card 3]          │
│ Total Reprocesos   Tendencia          Máquina #1         │
│ 45 lotes           ↘ -15.7% (semana)  AGOTAMIENTO 80     │
│                                        28 lotes (59%)     │
│                                                            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ Gráfico 1: Reprocesos por Máquina (últimas 24h)          │
│                                                            │
│    │ ███ AGOTAMIENTO 80  (28) 59%                         │
│    │ ██ AGOTAMIENTO 19   (15) 32%                         │
│    │ █ RAMAS 19          (4)  9%                          │
│    └─────────────────────────────                         │
│                                                            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ Gráfico 2: Tendencia (últimas 7 días)                     │
│ 260K │                                                    │
│      │     ╱╲                                             │
│      │    ╱  ╲    ╱─                                      │
│ 240K │───╱    ╲──╱    (Bajando desde identificación)      │
│      │                                                    │
│                                                            │
│ [Descargar PDF] [Exportar Excel]                          │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 7. Animaciones y Transiciones

### Duraciones Estándar

```
Quick:   150ms  — Hovers, cambios de estado rápidos
Normal:  300ms  — Transiciones, fades
Slow:    500ms  — Entradas, modales
```

### Easing

```
ease-in-out   — Movimientos naturales (default)
ease-out      — Apariciones, fadein
ease-in       — Desapariciones, fadeout
linear        — Contadores, spinners
```

### Ejemplos Clave

```css
/* Button Hover */
transition: all 150ms ease-in-out;
hover:shadow-md hover:bg-blue-700

/* Card Elevation */
transition: box-shadow 300ms ease-in-out;

/* Loading Spinner */
animation: spin 1s linear infinite;

/* Fade In */
animation: fadeIn 300ms ease-out forwards;
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Slide Up */
animation: slideUp 300ms ease-out forwards;
@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
```

---

## 8. Accesibilidad (WCAG AA)

### Requisitos Mínimos

- ✅ Semantic HTML (`<button>`, `<a>`, `<nav>`, `<main>`, `<section>`, etc.)
- ✅ Focus visible en todos elementos interactivos (outline 3px)
- ✅ Aria labels para iconos sin texto visible
- ✅ Contraste mínimo 4.5:1 (texto pequeño), 3:1 (componentes)
- ✅ Navegación por teclado completa (Tab, Enter, Escape, Arrow keys)
- ✅ Alt text en todas las imágenes
- ✅ Formularios con labels asociados (for/id)
- ✅ ARIA-live para cambios dinámicos (notificaciones)
- ✅ Color no es único indicador (usar iconos + color)

### Implementación

```jsx
// ✅ Semántica correcta
<button 
  className="px-4 py-2 bg-blue-600 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
  onClick={handleSave}
  aria-label="Guardar defecto"
>
  Guardar
</button>

// ✅ Iconos con label
<button aria-label="Capturar foto">
  <CameraIcon className="w-5 h-5" />
</button>

// ✅ Formulario accesible
<label htmlFor="defect-type" className="block text-sm font-medium mb-2">
  Tipo de Defecto
</label>
<select id="defect-type" required>
  <option>-- Selecciona --</option>
  <option>TONODIFFERENTE</option>
</select>

// ✅ Notificación dinámica
<div aria-live="polite" role="status">
  ✓ Defecto guardado
</div>

// ✅ Contraste WCAG AA
// Texto #1F2937 en fondo #FFFFFF = 13:1 ✅
```

### Testing

- Usar **axe DevTools** (extensión Chrome)
- Pruebas manuales con teclado (Tab, Enter, Escape)
- Screen reader testing (NVDA, JAWS, VoiceOver)
- Lighthouse audit (Chrome DevTools)

---

## 9. Imágenes y Fotografía

### Fotos de Defectos

```
Formato:      JPEG (compresión), WebP (web)
Dimensiones:  Min 640x480px, Max 2048x2048px
Tamaño archivo: Max 3MB por foto
Compresión:   85% calidad JPEG
Almacenamiento: Local (app) + Cloud (S3 opcional)
```

#### Orientación

```
Vertical (portrait):   Recomendado para fotos desde celular
Horizontal (landscape): Segundo plano, máquinas
Square (1:1):          Gallería, thumbnails
```

### Logo y Branding

```
Logo Azul:      200x200px mínimo
Logo Blanco:    Para fondos oscuros (opcional)
Favicon:        32x32px
Isotype (león): 64x64px mínimo para uso aislado
Aplicación:     No aplastar, respetar espaciado
```

---

## 10. Dark Mode (Opcional - v2.0)

**No incluido en MVP.** Pero estructura lista para futura implementación:

```css
/* Light Mode (Default) */
:root {
  --bg-primary: #FFFFFF;
  --text-primary: #1F2937;
}

/* Dark Mode (Future) */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #1F2937;
    --text-primary: #F9FAFB;
  }
}
```

---

## 11. Escritura y Microcopy

### Tono
- **Profesional pero accesible**: Evita jerga innecesaria
- **Directo**: Pocas palabras, máximo impacto
- **Español colombiano**: Familiar pero formal

### Ejemplos

```
✅ "Captura foto clara del defecto"
❌ "Por favor, procede a capturar una fotografía de calidad superior del defecto identificado"

✅ "Defecto no reconocido. ¿Es similar a MANCHAS?"
❌ "Error 404: Defecto no encontrado en maestro. Intenta nuevamente o contacta soporte."

✅ "Lote guardado. Sincronizando..."
❌ "Transacción completada exitosamente. Sistema enviando datos al servidor..."
```

### Mensajes de Error

```
❌ "Campo requerido"      → "Selecciona un tipo de defecto"
❌ "Error"                → "Foto no se cargó. Intenta de nuevo."
❌ "Fallo"                → "Sin wifi. Vamos a sincronizar cuando haya señal."
```

### Mensajes de Éxito

```
✅ "✓ Guardado"                    → "✓ Defecto registrado. Máquina: AGOTAMIENTO 80"
✅ "✓ Sincronizado"                → "✓ 3 registros sincronizados a servidor"
✅ "✓ Completado"                  → "✓ Inspección completada en 3'22""
```

---

## 12. Performance y Web Vitals

### Objetivos

```
LCP (Largest Contentful Paint):     < 2.5s
FID (First Input Delay):             < 100ms
CLS (Cumulative Layout Shift):       < 0.1
TTFB (Time to First Byte):           < 600ms
```

### Estrategias

- **Lazy loading** para imágenes fuera de viewport
- **Image compression**: WebP, JPEG 85%, max 500KB
- **Code splitting** por ruta (React.lazy)
- **Caché** para offline-first (Service Workers)
- **Minify** CSS/JS en producción
- **Preload** fuentes críticas
- **Pagination** para listas largas (100+ items)

---

## 13. Componentes Específicos de Control de Calidad

### Status Badge Defecto

```jsx
function DefectBadge({ defectCode, defectName }) {
  return (
    <span className="inline-flex items-center gap-2 px-3 py-1 bg-gray-100 border border-gray-300 rounded-md text-sm font-medium">
      <code className="text-gray-700">{defectCode}</code>
      <span className="text-gray-600">|</span>
      <span className="text-gray-700">{defectName}</span>
    </span>
  );
}

// Uso:
<DefectBadge defectCode="DEF-TON" defectName="TONODIFFERENTE" />
```

### Foto Display

```jsx
function DefectPhoto({ photoUrl, defectName }) {
  return (
    <div className="relative bg-gray-100 rounded-lg overflow-hidden aspect-square">
      <img 
        src={photoUrl}
        alt={`Foto de defecto: ${defectName}`}
        className="w-full h-full object-cover"
        loading="lazy"
      />
      <div className="absolute top-2 right-2 bg-white/80 backdrop-blur-sm px-2 py-1 rounded-md text-xs font-medium">
        Defecto
      </div>
    </div>
  );
}
```

### Status Timeline

```jsx
function InspectionTimeline({ checkIn, checkOut }) {
  const duration = calculateDuration(checkIn, checkOut);
  
  return (
    <div className="flex items-center gap-4">
      <div className="text-center">
        <p className="text-xs text-gray-500">Check-in</p>
        <p className="font-mono font-semibold">{formatTime(checkIn)}</p>
      </div>
      <div className="flex-1 border-t-2 border-blue-400"></div>
      <div className="text-center">
        <p className="text-xs text-gray-500">Duración</p>
        <p className="font-mono font-semibold text-blue-600">{duration}</p>
      </div>
      <div className="flex-1 border-t-2 border-blue-400"></div>
      <div className="text-center">
        <p className="text-xs text-gray-500">Check-out</p>
        <p className="font-mono font-semibold">{formatTime(checkOut)}</p>
      </div>
    </div>
  );
}
```

---

## 14. Especificación de Código

### CSS Framework
**Tailwind CSS** — Utility-first, mobile-first, especializado para este proyecto.

### Estructura Variables CSS

```css
/* Design Tokens */
:root {
  /* Colors */
  --color-primary: #0066CC;
  --color-primary-dark: #004A99;
  --color-primary-light: #E6F0FF;
  --color-success: #10B981;
  --color-error: #EF4444;
  --color-warning: #F59E0B;
  --color-info: #3B82F6;
  --color-text-primary: #1F2937;
  --color-border: #D1D5DB;
  
  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  
  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
}
```

### Tailwind Config

```js
module.exports = {
  content: ["./src/**/*.{js,jsx}"],
  theme: {
    colors: {
      primary: {
        dark: '#004A99',
        DEFAULT: '#0066CC',
        light: '#E6F0FF',
      },
      success: '#10B981',
      error: '#EF4444',
      warning: '#F59E0B',
      info: '#3B82F6',
    },
    fontFamily: {
      sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto'],
      mono: ['SF Mono', 'Monaco', 'Roboto Mono'],
    },
    extend: {
      spacing: {
        xs: '4px',
        sm: '8px',
        md: '16px',
        lg: '24px',
        xl: '32px',
      },
    },
  },
};
```

---

## 15. Checklist de Implementación

### Antes de Mergear Componente

- [ ] Diseño visualmente aprobado
- [ ] Responsive en 3 breakpoints (mobile, tablet, desktop)
- [ ] Accesibilidad WCAG AA verificada (axe DevTools)
- [ ] Focus visible en elementos interactivos
- [ ] Colores pasan contraste 4.5:1 minimum
- [ ] Semántica HTML correcta
- [ ] Performance: <200ms render
- [ ] Funciona en navegadores principales (Chrome, Firefox, Safari, Edge)
- [ ] Testing: Component tests + snapshot tests
- [ ] Documentación: Props, estados, ejemplos
- [ ] Dark mode compatible (futura)

---

## 16. Herramientas Recomendadas

| Herramienta | Uso | Link |
|-------------|-----|------|
| **Figma** | Prototipos, guía de estilo | figma.com |
| **Tailwind CSS** | Framework CSS | tailwindcss.com |
| **Heroicons** | Iconografía | heroicons.com |
| **axe DevTools** | Testing accesibilidad | deque.com/axe |
| **Lighthouse** | Auditoría performance | developers.google.com |
| **Color Contrast Analyzer** | Validar contrastes | webaim.org/resources/contrastchecker |

---

## 17. Referencias

- [Material Design 3](https://m3.material.io)
- [Web Content Accessibility Guidelines (WCAG)](https://www.w3.org/WAI/WCAG21/quickref/)
- [Web Vitals](https://web.dev/vitals/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Accesibilidad MDN](https://developer.mozilla.org/es/docs/Web/Accessibility)

---

**DESIGN.md Completado**  
Versión 1.0 | Listo para Desarrollo | 2026-06-01  
Próximo: Implementar componentes en React + Tailwind CSS
