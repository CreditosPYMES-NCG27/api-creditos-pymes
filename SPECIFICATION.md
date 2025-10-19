# API Créditos PyMEs — Especificación (alineada al código actual)

Versión: 0.1.0

Base URL: `/` (raíz) y `/api/v1` (API versionada)

Este documento refleja únicamente lo implementado en el código bajo `app/` a la fecha.

---

## Autenticación y Seguridad

- Esquema: `Authorization: Bearer <JWT>` (HTTP Bearer).
- Validación de tokens vía JWKS de Supabase usando el `SUPABASE_URL` de configuración:
  - Algoritmo: ES256
  - `audience`: `authenticated`
  - `issuer`: `${SUPABASE_URL}/auth/v1`
- Respuestas de error relacionadas:
  - 403: falta el header Authorization (HTTPBearer)
  - 401: token inválido/expirado/audience/issuer inválidos
- El payload JWT debe contener al menos: `sub` (user id). `email` es opcional.

### Encabezados HTTP

- `Authorization: Bearer <JWT>` en todos los endpoints bajo `/api/v1` salvo `/api/v1/metadata/*` (público).
- `Content-Type: application/json` para peticiones con cuerpo.
- `Accept: application/json` recomendado.

---

## Convenciones de Datos

- UUID: strings UUID v4.
- Decimal: serializado como string (ej.: "25000.0").
- Fechas: ISO 8601 (por ejemplo, `2025-01-01T12:00:00Z`).
- Enums (slugs):
  - `UserRole`: `applicant`, `operator`, `admin`
  - `CreditApplicationStatus`: `pending`, `in_review`, `approved`, `rejected`
  - `CreditApplicationPurpose`: `working_capital`, `equipment`, `expansion`, `inventory`, `refinancing`, `other`

---

## Manejo de Errores

Formato estándar: `{ "detail": string }`

- 400 Bad Request: validaciones de dominio (p. ej., transición de estado inválida, datos faltantes de negocio).
- 401 Unauthorized: token inválido/expirado o payload sin `sub`.
- 403 Forbidden: falta de credenciales (HTTPBearer) o rol no autorizado o sin rol asignado.
- 404 Not Found: recurso inexistente (empresa, solicitud de crédito, etc.).
- 409 Conflict: reservado para conflictos (no utilizado en flujos actuales).
- 422 Unprocessable Entity: validaciones de esquema (Pydantic/FastAPI).
- 500 Internal Server Error: error de servicio no controlado.

Mensajes de error relevantes (ejemplos reales del código):

```
// 401 token expirado
{ "detail": "Expired token" }

// 401 audience inválido
{ "detail": "Invalid token audience" }

// 401 issuer inválido
{ "detail": "Invalid token issuer" }

// 401 token inválido genérico
{ "detail": "Invalid token" }

// 401 payload sin sub
{ "detail": "Token no contiene user_id (sub)" }

// 403 rol no autorizado
{ "detail": "Rol no autorizado" }

// 403 perfil sin rol
{ "detail": "Perfil sin rol" }

// 404 recursos no encontrados
{ "detail": "Empresa no encontrada" }
{ "detail": "Empresa no encontrada para el usuario dado" }
{ "detail": "Solicitud no encontrada" }

// 400 validaciones de dominio
{ "detail": "Campo de ordenamiento no permitido: <campo>. Campos permitidos: ..." }
{ "detail": "Debes registrar una empresa antes de solicitar crédito" }
{ "detail": "Ya tienes una solicitud pendiente" }
{ "detail": "purpose_other es requerido cuando purpose es 'other'" }
{ "detail": "No hay datos para actualizar" }
{ "detail": "No se proporcionaron campos para actualizar" }
{ "detail": "Transición de estado no válida: in_review → pending. Transiciones permitidas desde in_review: ['approved', 'rejected']" }
{ "detail": "approved_amount es requerido cuando el status es 'approved'" }
{ "detail": "interest_rate es requerido cuando el status es 'approved'" }
{ "detail": "review_notes es requerido cuando el status es 'rejected'" }
```

---

## Paginación

Parámetros (query):

- `page`: int >= 1 (default 1)
- `limit`: int [1, 100] (default 10)
- `sort`: string opcional (campo)
- `order`: `asc` | `desc` (default `desc`)

Respuesta paginada:

```
{
  "items": [ ... ],
  "meta": {
    "total": 123,
    "page": 1,
    "per_page": 10,
    "pages": 13,
    "has_next": true,
    "has_prev": false
  }
}
```

Notas:
- En empresas, si `sort` no es un campo válido, se ignora y se ordena por `created_at desc`.
- En solicitudes de crédito, solo se permiten campos específicos (ver endpoint); si es inválido, retorna 400.

---

## Esquemas

ProfileResponse

```
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "applicant",
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-01T12:00:00Z"
}
```

CompanyResponse

```
{
  "id": "uuid",
  "user_id": "uuid",
  "legal_name": "Acme Inc",
  "tax_id": "123456789",
  "contact_email": "contact@acme.com",
  "contact_phone": "+000000000",
  "address": {
    "street": "Main St 123",
    "city": "City",
    "state": "State",
    "zip_code": "12345",
    "country": "Country"
  },
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-01T12:00:00Z"
}
```

CompanyUpdate (request)

```
{
  "contact_email": "new@acme.com",
  "contact_phone": "+111111111",
  "address": { ... }
}
```

CreditApplicationCreate (request)

```
{
  "requested_amount": 25000.0,
  "term_months": 24,
  "purpose": "expansion",
  "purpose_other": null
}
```

CreditApplicationUpdate (request)

```
{
  "status": "approved" | "rejected" | "pending" | "in_review",
  "risk_score": 85.0,
  "operator_id": "uuid",
  "review_notes": "Approved",
  "reviewed_at": "2025-01-01T12:00:00Z",
  "approved_amount": 20000.0,
  "interest_rate": 8.5,
  "purpose": "other",
  "purpose_other": "Detalle"
}
```

CreditApplicationResponse

```
{
  "id": "uuid",
  "company_id": "uuid",
  "requested_amount": "25000.0",
  "purpose": "expansion",
  "purpose_other": null,
  "term_months": 24,
  "status": "pending",
  "risk_score": null,
  "operator_id": null,
  "reviewed_at": null,
  "review_notes": null,
  "approved_amount": null,
  "interest_rate": null,
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-01T12:00:00Z"
}
```

CreditPurposeResponse (catálogo)

```
{
  "value": 0,
  "slug": "expansion",
  "label": "Expansión"
}
```

---

## Endpoints

### Raíz (público)

- GET `/`
  - 200 OK
  - Respuesta: `{ "name": "API Créditos PyMEs", "version": "0.1.0", "docs": "/docs" }`

- GET `/health`
  - 200 OK
  - Respuesta: `{ "status": "healthy" }`

---

### Perfiles

- GET `/api/v1/profiles/me`
  - Auth: Bearer requerido
  - 200 OK: `ProfileResponse`
  - Errores: 401 (token inválido), 403 (sin rol), 404 (usuario no encontrado)

---

### Empresas

- GET `/api/v1/companies/me`
  - Auth: Bearer requerido
  - 200 OK: `CompanyResponse`
  - Errores: 401, 403, 404 (empresa no encontrada para el usuario)

- PATCH `/api/v1/companies/me`
  - Auth: Bearer requerido
  - Body: `CompanyUpdate`
  - 200 OK: `CompanyResponse`
  - Errores: 400 ("No hay datos para actualizar"), 401, 403, 404

- GET `/api/v1/companies/{company_id}`
  - Auth: Bearer requerido
  - Autorización: roles `admin` o `operator`
  - 200 OK: `CompanyResponse`
  - Errores: 401, 403, 404

- GET `/api/v1/companies/`
  - Auth: Bearer requerido
  - Query: `page`, `limit`, `sort`, `order`
  - 200 OK: `Paginated[CompanyResponse]`
  - Notas: si `sort` es inválido, se ignora (orden por `created_at desc`).
  - Errores: 401, 403

---

### Solicitudes de Crédito

- GET `/api/v1/credit-applications/`
  - Auth: Bearer requerido
  - Query: `page`, `limit`, `sort`, `order`, `status` (enum), `company_id` (UUID)
  - Autorización:
    - `applicant`: solo ve solicitudes de su propia empresa. Si no tiene empresa, retorna lista vacía con `total=0`.
    - `operator`/`admin`: ven todas, opcionalmente filtradas por `company_id`.
  - Ordenamiento permitido (`sort`): `id`, `requested_amount`, `term_months`, `status`, `risk_score`, `approved_amount`, `interest_rate`, `created_at`, `updated_at`. Si es inválido → 400.
  - 200 OK: `Paginated[CreditApplicationResponse]`
  - Errores: 400 (sort inválido), 401, 403

- POST `/api/v1/credit-applications/`
  - Auth: Bearer requerido
  - Body: `CreditApplicationCreate`
  - 200 OK: `CreditApplicationResponse`
  - Validaciones de dominio (400): usuario sin empresa; solicitud `pending` existente; `purpose == "other"` requiere `purpose_other` no vacío.
  - Validaciones de esquema (422): montos <= 0, términos fuera de rango, etc.
  - Errores: 401, 403

- GET `/api/v1/credit-applications/{application_id}`
  - Auth: Bearer requerido
  - Autorización:
    - `applicant`: solo si la solicitud pertenece a su empresa (sino 403)
    - `operator`/`admin`: acceso permitido
  - 200 OK: `CreditApplicationResponse`
  - Errores: 401, 403, 404

- PATCH `/api/v1/credit-applications/{application_id}`
  - Auth: Bearer requerido
  - Autorización: roles `operator` o `admin`
  - Body: `CreditApplicationUpdate`
  - 200 OK: `CreditApplicationResponse`
  - Validaciones de dominio (400): sin campos para actualizar; transiciones de estado inválidas; reglas específicas para `approved` y `rejected`; `purpose == other` requiere `purpose_other`.
  - Validaciones de esquema (422): valores fuera de rango (p. ej., `interest_rate < 0`).
  - Errores: 401, 403, 404

---

### Metadatos (público)

- GET `/api/v1/metadata/credit-purposes`
  - Auth: no requerido
  - 200 OK: `CreditPurposeResponse[]` (lista ordenada)
  - Notas: `slug` es el identificador estable; `label` es el texto para UI (p. ej., "Expansión").

---

## Autorización por Roles

- Perfiles: `GET /profiles/me` requiere usuario autenticado (rol cualquiera). Si no existe perfil → 404.
- Empresas:
  - `/companies/me` lectura/actualización: autenticado (rol cualquiera); opera sobre la empresa del usuario.
  - `/companies/{id}` y listado: solo `admin` u `operator`.
- Solicitudes de crédito:
  - Listado: autenticado; `applicant` ve solo las de su empresa, `operator`/`admin` ven todas.
  - Crear: autenticado; requiere tener una empresa.
  - Obtener por id: autenticado; `applicant` solo si pertenece a su empresa, `operator`/`admin` acceso.
  - Actualizar: `operator` o `admin`.

---

## Descubrimiento y Documentación

- Documentación interactiva: `/docs` (Swagger UI) y `/redoc` (si está habilitado).
- Esquema OpenAPI: `/openapi.json`.

---

## Versionado

- Prefijo `/api/v1` para endpoints versionados.
  - Raíz y salud (`/`, `/health`) están fuera de la versión.

---

## Configuración Relevante

- Variables de entorno usadas por la app (`app/config.py`):
  - `SUPABASE_URL`
  - `DB_USER`, `DB_PASS`, `DB_NAME`, `DB_HOST`, `DB_PORT`
- Base de datos: PostgreSQL (asyncpg) vía SQLModel.
- Autenticación: JWT validado con JWKS de Supabase.
- Arquitectura: routers / services / repositories / schemas / models.

---

## Estructura del Proyecto (actual)

```
app/
├── main.py                 # Aplicación FastAPI con lifespan (bootstrap)
├── bootstrap.py            # Lifespan: DB y JWKS
├── config.py               # Configuración con Pydantic Settings
├── core/
│   ├── enums.py            # Enums para estados y tipos
│   └── errors.py           # Excepciones de dominio
├── dependencies/
│   ├── auth.py             # Validación JWT y extracción de Principal
│   ├── db.py               # Sesión Async SQLModel/SQLAlchemy
│   └── services.py         # Inyección de servicios
├── models/                 # Modelos SQLModel (DB)
├── repositories/           # Acceso a datos
├── routers/                # Endpoints REST (profiles, companies, credit_applications, metadata)
├── schemas/                # Schemas Pydantic (API)
└── services/               # Lógica de negocio
```

---

## Modelo de Datos (implementado)

- Tipos ENUM (ver `db/types.sql`): `userrole`, `creditapplicationstatus`, `creditapplicationpurpose`.
- Tablas principales:
  - `profiles`: id, email, first_name, last_name, role, created_at, updated_at.
  - `companies`: id, user_id, legal_name, tax_id, contact_email, contact_phone, address, created_at, updated_at.
  - `credit_applications`: id, company_id, requested_amount, purpose, purpose_other, term_months, status, risk_score, operator_id, reviewed_at, review_notes, approved_amount, interest_rate, created_at, updated_at.

Notas:
- No existe columna `user_id` en `credit_applications` en el modelo actual.
- Los scripts RLS existen en `db/policies`, pero pueden requerir ajuste fino según el modelo vigente.

---

## Estado de funcionalidades

- Implementado:
  - Autenticación JWT (validación JWKS) y extracción de usuario actual
  - Perfiles: `GET /api/v1/profiles/me`
  - Empresas: `GET /api/v1/companies/me`, `PATCH /api/v1/companies/me`, `GET /api/v1/companies/{id}`, `GET /api/v1/companies/`
  - Solicitudes de crédito: `GET/POST/PATCH /api/v1/credit-applications`, `GET /api/v1/credit-applications/{id}`
  - Metadatos: `GET /api/v1/metadata/credit-purposes` (público)
  - Paginación y validaciones de negocio

- Pendiente / fuera del alcance actual del código:
  - Registro/login desde la API (delegado a Supabase, sin endpoints propios)
  - CRUD de empresas con creación vía API (no existe `POST /companies`)
  - Documentos/Storage, Reportes, Notificaciones, KYC/AML, Firma digital, ML

---

## Referencias

- FastAPI: https://fastapi.tiangolo.com/
- SQLModel: https://sqlmodel.tiangolo.com/
- Supabase Auth: https://supabase.com/docs

---

Última actualización: Octubre 2025
