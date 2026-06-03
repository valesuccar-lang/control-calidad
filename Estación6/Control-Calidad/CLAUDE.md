# Control de Calidad - Guía de Desarrollo

Este documento establece estándares, preferencias y patrones para todo el desarrollo en el proyecto de Control de Calidad.

## 1. Propósito del Proyecto

Sistema de control de calidad intuitivo, profesional y accesible diseñado para:
- Registrar, rastrear y reportar resultados de calidad
- Facilitar toma de decisiones rápidas mediante visualización clara
- Funcionar perfectamente en dispositivos móviles y desktop
- Comunicar confiabilidad y profesionalismo

---

## 2. Stack Tecnológico

### Frontend
- **React 18+** con componentes funcionales y hooks
- **JavaScript** (no TypeScript obligatorio, pero recomendado para nuevos componentes)
- **Tailwind CSS** para estilos (utility-first, mobile-first)
- **React Router v6** para navegación
- **State Management**: Zustand (mantener stores simples y enfocados)

### Backend
- Según especificaciones del proyecto (API RESTful)
- Validación de datos en límites de API

### Testing
- **Jest** para unit tests
- **React Testing Library** para componentes
- **Cypress** para e2e (si aplica)

### DevOps
- **Node.js** v18+
- **npm** para package management

---

## 3. Principios de Código

### General

**Máxima**: Código simple, mantenible y que se explique a sí mismo.

- Nombres descriptivos (variables, funciones, componentes)
- Funciones pequeñas y enfocadas (Una Responsabilidad)
- No comentarios innecesarios - el código debe ser autoexplicativo
- Comentarios solo si la lógica es no-obvia o hay un workaround específico
- DRY (Don't Repeat Yourself): Reutilizar código, pero no prematuramente

### React y Componentes

```js
// ✅ BIEN: Componente simple y enfocado
function QualityScore({ score, total }) {
  const percentage = Math.round((score / total) * 100);
  const statusColor = percentage >= 80 ? 'text-green-600' : 'text-red-600';
  
  return (
    <div className="flex items-center gap-2">
      <span className={`text-lg font-semibold ${statusColor}`}>{percentage}%</span>
      <ProgressBar value={percentage} />
    </div>
  );
}

// ❌ MAL: Demasiada lógica, componente acoplado
function QualityScore({ data, onUpdate, shouldAnimate, config, theme, ... }) {
  // ... 50 líneas de lógica compuesta
}
```

#### Reglas de Componentes

- Componentes funcionales con hooks (nada de clases)
- Props claros y tipados (incluso en JS, usar comentarios JSDoc)
- Estado local con `useState` para UI, Zustand para estado global
- Efectos simples, evitar dependencias circulares
- Memoización solo si provoca re-renders innecesarios (no prematura)
- Extraer componentes cuando tienen más de 150 líneas

### Hooks Personalizados

```js
// Patrón: useNombre, enfocado en una responsabilidad
function useQualityData(testId) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchQualityData(testId).then(setData).finally(() => setLoading(false));
  }, [testId]);
  
  return { data, loading };
}
```

### CSS y Tailwind

```jsx
// ✅ BIEN: Tailwind limpio, responsive
<button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
  Guardar
</button>

// ❌ MAL: Classes desorganizadas o inline styles
<button style={{backgroundColor: '#005eb8', padding: '10px 16px'}} className="...">
```

#### Tailwind Conventions

- Mobile-first: base styles luego `md:`, `lg:`, `xl:`
- Usar config customizado (colores, spacing)
- Extraer componentes repetidos a archivos dedicados
- Usar `@apply` en exceso = mala señal (refactoriza)

---

## 4. Estructura de Carpetas

```
src/
├── components/          # Componentes reutilizables
│   ├── common/         # Botones, inputs, cards genéricas
│   ├── forms/          # Componentes de formulario
│   ├── layouts/        # Header, Sidebar, layouts
│   └── features/       # Componentes específicos de features
├── pages/              # Páginas/vistas (rutas principales)
├── hooks/              # Custom hooks
├── store/              # Zustand stores
├── services/           # API calls, utilidades
├── utils/              # Helpers, constantes, formatters
├── types/              # TypeScript types / JSDoc definitions
├── styles/             # Estilos globales, Tailwind overrides
├── assets/             # Imágenes, iconos, fonts
└── App.jsx             # Componente raíz

```

### Ejemplo: Agregar Feature de "Test Results"

```
src/
├── components/features/TestResults/
│   ├── TestResultCard.jsx
│   ├── TestResultForm.jsx
│   └── index.js
├── pages/TestResults.jsx
├── hooks/useTestResults.js
├── store/testResultsStore.js
└── services/testResultsService.js
```

---

## 5. Convenciones de Nombres

| Tipo | Patrón | Ejemplo |
|------|--------|---------|
| Componentes | PascalCase | `QualityScore`, `TestResultCard` |
| Hooks | camelCase, prefijo `use` | `useQualityData`, `useTestForm` |
| Variables/funciones | camelCase | `testResults`, `calculateScore` |
| Constantes | UPPER_SNAKE_CASE | `MAX_SCORE`, `API_ENDPOINT` |
| Booleanos | prefijo `is`, `has`, `should` | `isLoading`, `hasError`, `shouldValidate` |
| Archivos componentes | PascalCase.jsx | `QualityScore.jsx` |
| Archivos utilidad | camelCase.js | `formatters.js`, `validators.js` |
| CSS classes | kebab-case | `quality-badge`, `test-row` |

---

## 6. Estándares de Accesibilidad (WCAG AA)

### Mínimos Requeridos

```jsx
// ✅ BIEN: Accesible
<button 
  className="px-4 py-2 bg-blue-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
  aria-label="Guardar cambios"
  onClick={handleSave}
>
  Guardar
</button>

// ❌ MAL: No accesible
<div onClick={handleSave} className="cursor-pointer">Guardar</div>
```

### Checklist

- [ ] Semántica HTML (button, a, nav, main, section, etc.)
- [ ] Focus visible en todos los elementos interactivos
- [ ] Aria labels para iconos y elementos sin texto visible
- [ ] Contraste de color mínimo 4.5:1
- [ ] Navegación por teclado (Tab, Enter, Escape)
- [ ] Formularios con labels (for/id)
- [ ] Texto alternativo en imágenes (alt)
- [ ] ARIA-live para cambios dinámicos

### Recursos

- `axe DevTools` para testing automático
- Lighthouse audit en Chrome DevTools
- Pruebas manuales con teclado

---

## 7. Performance

### Objetivos Web Vitals

- **LCP** (Largest Contentful Paint): < 2.5s
- **FID** (First Input Delay): < 100ms
- **CLS** (Cumulative Layout Shift): < 0.1

### Prácticas

```jsx
// ✅ BIEN: Lazy loading con React.lazy
const ReportPage = React.lazy(() => import('./pages/Report'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <ReportPage />
    </Suspense>
  );
}

// ✅ BIEN: Image optimization
<img 
  src="image.jpg"
  alt="Quality chart"
  loading="lazy"
  decoding="async"
  width="400"
  height="300"
/>

// ❌ MAL: Cargar todo en bundle principal
import HeavyChart from './components/HeavyChart'; // Siempre se carga
```

### Checklist

- [ ] Code splitting por ruta con React.lazy
- [ ] Lazy load imágenes (loading="lazy")
- [ ] Memoización de componentes costosos (React.memo)
- [ ] Eliminar dependencias no usadas
- [ ] Usar DevTools Lighthouse regularmente

---

## 8. Testing

### Principios

- Test lo que importa (comportamiento, no implementación)
- Escribe tests mientras desarrollas (TDD)
- Mínimo de coverage: 70% para lógica crítica

### Ejemplos

```js
// ✅ BIEN: Test de comportamiento
test('mostrar error cuando el score es inválido', () => {
  render(<QualityScore score={101} total={100} />);
  expect(screen.getByRole('alert')).toHaveTextContent('Score inválido');
});

// ❌ MAL: Test de implementación
test('QualityScore renderiza <div>', () => {
  const { container } = render(<QualityScore {...props} />);
  expect(container.querySelector('div')).toBeInTheDocument();
});
```

### Estructuras

- **Unit**: Funciones utilidad, lógica pura
- **Component**: Renderizado, interacciones usuario
- **Integration**: Flujos completos (form submit → API call)
- **E2E** (Cypress): Rutas críticas

---

## 9. Estándares de API

### Endpoints

Documentar en un archivo `API_SPEC.md`:

```markdown
## GET /api/quality-tests/:testId
- Returns: { id, name, score, total, status, timestamp }
- Errors: 404 Not Found, 500 Server Error
- Auth: Requiere token JWT
```

### Consumo en Frontend

```js
// ✅ BIEN: Service layer limpio
const testService = {
  getTest: async (id) => {
    const res = await fetch(`/api/quality-tests/${id}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },
};

// Uso en componente
function TestDetail({ testId }) {
  const { data, error } = useAsync(() => testService.getTest(testId), [testId]);
}
```

---

## 10. Control de Versiones (Git)

### Commits

```
[feature] Agregar QualityScore component
[fix] Corregir cálculo de porcentaje en score
[refactor] Simplificar lógica de validación
[docs] Actualizar DESIGN.md con colores nuevos
[test] Agregar tests para TestResultCard
[style] Ajustar espaciado en buttons
```

Primer commit mensaje describe QUÉ, no POR QUÉ. POR QUÉ va en PR description.

### Ramas

- `main`: Producción, estable
- `develop`: Staging, próxima release
- `feature/nombre`: Nuevas features
- `fix/nombre`: Bug fixes

### PRs

Incluir:
- Descripción clara del cambio
- Screenshots/videos si hay cambios visuales
- Testing realizado (unit, manual)
- Breaking changes (si aplica)

---

## 11. Herramientas y Setup

### Linting y Formatting

```bash
npm install -D eslint prettier eslint-config-react-app
```

`.eslintrc.json`:
```json
{
  "extends": "react-app",
  "rules": {
    "no-unused-vars": "warn",
    "no-console": "warn"
  }
}
```

`.prettierrc`:
```json
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "tabWidth": 2
}
```

### Pre-commit Hooks

```bash
npm install -D husky lint-staged
npx husky install
```

`.husky/pre-commit`:
```bash
npx lint-staged
```

`package.json`:
```json
{
  "lint-staged": {
    "*.{js,jsx}": ["eslint --fix", "prettier --write"],
    "*.css": ["prettier --write"]
  }
}
```

---

## 12. Proceso de Desarrollo

### 1. Antes de Empezar
- [ ] Crear rama desde `develop` o `main`
- [ ] Escribir descripción clara en el PR (después)

### 2. Durante Desarrollo
- [ ] Seguir estructura de carpetas
- [ ] Escribir tests mientras desarrollas
- [ ] Usar Tailwind para estilos
- [ ] Seguir convenciones de nombres
- [ ] Commit messages claros

### 3. Antes de Mergear
- [ ] [ ] Tests pasando (100% coverage para cambios críticos)
- [ ] ESLint y Prettier pasando
- [ ] Verificar accesibilidad (axe DevTools)
- [ ] Testear responsivo (móvil, tablet, desktop)
- [ ] Lighthouse score > 90
- [ ] Revisar con compañero (code review)
- [ ] Actualizar DESIGN.md si hay nuevos patrones

---

## 13. Debugging

### Herramientas Recomendadas

- **React DevTools**: Inspeccionar componentes, hooks, props
- **Redux DevTools**: Si usamos Zustand, inspeccionar estado
- **Network tab**: Verificar API calls
- **Lighthouse**: Auditoría de performance
- **Axe DevTools**: Accesibilidad

### Técnicas

```js
// Logging estructurado
console.log('USER_ACTION', { action: 'save', timestamp: Date.now() });

// Debug condicional
if (process.env.NODE_ENV === 'development') {
  console.log('DEBUG:', componentState);
}
```

---

## 14. Documentación

### Comentarios en Código

```js
// ✅ BIEN: Explica POR QUÉ, no QUÉ
// Redondeamos al entero más cercano porque el API retorna decimales
const percentage = Math.round((score / total) * 100);

// ❌ MAL: Explica QUÉ (obvio del código)
// Calcula el porcentaje
const percentage = Math.round((score / total) * 100);
```

### README.md (en raíz del proyecto)

```markdown
# Control de Calidad - Frontend

## Setup

npm install
npm run dev

## Testing

npm test
npm run test:e2e

## Building

npm run build

## Deployment

Pushear a `main`, CI/CD se encarga del deploy.
```

---

## 15. Checklist Final: Antes de Mergear

- [ ] Código sigue principios de la sección 3
- [ ] Estructura de carpetas según sección 4
- [ ] Nombres siguiendo convenciones (sección 5)
- [ ] Accesibilidad WCAG AA validada (sección 6)
- [ ] Performance verificada con Lighthouse (sección 7)
- [ ] Tests escritos y pasando (sección 8)
- [ ] API integration correcta (sección 9)
- [ ] Git commits limpios y descriptivos (sección 10)
- [ ] Linting y formatting pasando (sección 11)
- [ ] Documentación actualizada si es necesario
- [ ] Responsivo en móvil/tablet/desktop
- [ ] No hay console.error o warnings
- [ ] Screenshots/videos en PR si hay cambios visuales

---

## 16. Contacto y Escalación

- **Preguntas sobre diseño**: Revisar DESIGN.md
- **Dudas técnicas**: Code review en PR
- **Issues de accesibilidad**: Usar axe DevTools, crear issue
- **Performance problems**: Lighthouse audit + profile con DevTools

---

**Última actualización**: 2026-06-01  
**Versión**: 1.0  
**Estado**: Activo, sujeto a cambios con feedback de implementación
