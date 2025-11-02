# API de Créditos PyMES - Especificación Técnica

**Versión:** 0.1.0  
**Base URL:** `https://<PRODUCTION_DOMAIN>/api/v1` (producción) | `http://localhost:8000/api/v1` (desarrollo)  
**Documentación interactiva:** `/docs` (Swagger UI) | `/redoc` (ReDoc)

---

## 1. Introducción

API REST para la gestión de solicitudes de crédito a pequeñas y medianas empresas (PyMES). Permite a empresas solicitar créditos, subir documentación, firmar documentos digitalmente y a operadores revisar y aprobar solicitudes.

### Características principales

- **Autenticación JWT** mediante Supabase Auth
- **Control de acceso basado en roles** (applicant, operator, admin)
- **Gestión de solicitudes de crédito** con workflow completo (draft → pending → in_review → approved/rejected)
- **Sistema de documentos** con almacenamiento en Supabase Storage
- **Firma digital** integrada con HelloSign/Dropbox Sign
- **Webhooks** para sincronización de eventos externos

---

## 2. Autenticación y Autorización

### 2.1 Obtener Token de Acceso

La API utiliza **Supabase Auth** para autenticación. Los tokens JWT deben incluirse en todas las peticiones protegidas.

**Endpoint de autenticación:** `https://<SUPABASE_PROJECT_URL>/auth/v1/token`

**Ejemplo de login:**

```bash
curl -X POST 'https://<SUPABASE_PROJECT_URL>/auth/v1/token?grant_type=password' \
  -H 'Content-Type: application/json' \
  -H 'apikey: <SUPABASE_ANON_KEY>' \
  -d '{
    "email": "usuario@example.com",
    "password": "contraseña_segura"
  }'
```

**Respuesta exitosa:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "...",
  "user": {
    "id": "c213241d-b01b-4dc4-b7b1-ace7f5c4e26c",
    "email": "usuario@example.com",
    "user_metadata": {
      "email_verified": true
    },
    "app_metadata": {},
    "role": "authenticated",
    "user_role": "applicant"
  }
}
```

### 2.2 Usar el Token en Peticiones

Incluye el token en el header `Authorization`:

```bash
Authorization: Bearer <access_token>
```

### 2.3 Roles de Usuario

La API soporta tres roles distintos con diferentes permisos:

| Rol | Descripción | Permisos principales |
|-----|-------------|---------------------|
| `applicant` | Solicitante de crédito (empresa) | - Ver/crear sus propias solicitudes<br>- Subir documentos<br>- Firmar documentos<br>- Ver su propia empresa |
| `operator` | Operador de crédito | - Ver todas las solicitudes<br>- Revisar/aprobar solicitudes<br>- Solicitar documentos adicionales<br>- Cambiar estados de solicitudes |
| `admin` | Administrador | - Todos los permisos de operator<br>- Gestión completa del sistema |

**Nota:** El rol se almacena en el campo `user_role` del JWT (no en `role`, que siempre es `"authenticated"`).

### 2.4 Estructura del JWT

```json
{
  "sub": "c213241d-b01b-4dc4-b7b1-ace7f5c4e26c",
  "email": "operator@example.com",
  "role": "authenticated",
  "user_role": "operator",
  "aud": "authenticated",
  "exp": 1762047274,
  "iat": 1762043674,
  "iss": "https://<SUPABASE_PROJECT_URL>/auth/v1"
}
```

---

## 3. Endpoints por Recurso

### 3.1 Root y Health Check

#### `GET /`

Endpoint raíz para verificar que la API está funcionando.

**Autenticación:** No requerida

**Respuesta:** `200 OK`

```json
{
  "message": "API Créditos PyMES funcionando correctamente"
}
```

---

#### `GET /health`

Health check para monitoreo de la API.

**Autenticación:** No requerida

**Respuesta:** `200 OK`

```json
{
  "status": "healthy"
}
```

---

### 3.2 Profiles (Perfiles de Usuario)

#### `GET /api/v1/profiles/me`

Obtiene el perfil del usuario autenticado.

**Autenticación:** Requerida (todos los roles)

**Respuesta:** `200 OK`

```json
{
  "id": "c213241d-b01b-4dc4-b7b1-ace7f5c4e26c",
  "email": "usuario@example.com",
  "first_name": "Juan",
  "last_name": "Pérez",
  "role": "applicant",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

---

#### `GET /api/v1/profiles/{user_id}`

Obtiene el perfil de un usuario por su ID.

**Autenticación:** Requerida  
**Permisos:**
- `applicant`: solo puede ver su propio perfil
- `operator`/`admin`: pueden ver cualquier perfil

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `user_id` | UUID | ID del usuario |

**Respuesta:** `200 OK` (ver estructura en `/me`)

**Errores comunes:**

- `403 Forbidden`: Applicant intentando acceder a perfil ajeno
- `404 Not Found`: Usuario no existe

---

### 3.3 Companies (Empresas)

#### `GET /api/v1/companies/me`

Obtiene la empresa asociada al usuario autenticado.

**Autenticación:** Requerida (todos los roles)

**Respuesta:** `200 OK`

```json
{
  "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "user_id": "c213241d-b01b-4dc4-b7b1-ace7f5c4e26c",
  "legal_name": "PyME Ejemplo S.A. de C.V.",
  "tax_id": "ABC123456XYZ",
  "contact_email": "contacto@pyme-ejemplo.com",
  "contact_phone": "+52 55 1234 5678",
  "address": {
    "street": "Av. Insurgentes Sur 1234",
    "city": "Ciudad de México",
    "state": "CDMX",
    "zip_code": "03100",
    "country": "México"
  },
  "created_at": "2025-01-10T08:00:00Z",
  "updated_at": "2025-01-10T08:00:00Z"
}
```

---

#### `PATCH /api/v1/companies/me`

Actualiza parcialmente la empresa del usuario autenticado.

**Autenticación:** Requerida (todos los roles)

**Body (JSON):**

```json
{
  "contact_email": "nuevo-contacto@pyme-ejemplo.com",
  "contact_phone": "+52 55 9876 5432",
  "address": {
    "street": "Nueva Calle 456",
    "city": "Monterrey",
    "state": "Nuevo León",
    "zip_code": "64000",
    "country": "México"
  }
}
```

**Campos opcionales:**

| Campo | Tipo | Validación |
|-------|------|------------|
| `contact_email` | string | Email válido, 1-255 chars |
| `contact_phone` | string | 1-20 chars |
| `address` | object | CompanyAddress completo |

**Respuesta:** `200 OK` (CompanyResponse actualizada)

---

#### `GET /api/v1/companies/{company_id}`

Obtiene una empresa por ID.

**Autenticación:** Requerida  
**Permisos:** Solo `operator` y `admin`

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `company_id` | UUID | ID de la empresa |

**Respuesta:** `200 OK` (ver estructura en `/me`)

**Errores comunes:**

- `403 Forbidden`: Applicant intentando acceder
- `404 Not Found`: Empresa no existe

---

#### `GET /api/v1/companies/`

Lista todas las empresas con paginación.

**Autenticación:** Requerida  
**Permisos:** Solo `operator` y `admin`

**Query parameters:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Número de página (≥1) |
| `limit` | integer | 10 | Elementos por página (1-100) |
| `sort` | string | null | Campo para ordenar |
| `order` | string | "desc" | Orden: "asc" o "desc" |

**Respuesta:** `200 OK`

```json
{
  "items": [
    {
      "id": "a1b2c3d4-...",
      "legal_name": "PyME Ejemplo S.A.",
      "tax_id": "ABC123456XYZ",
      ...
    }
  ],
  "meta": {
    "total": 150,
    "page": 1,
    "per_page": 10,
    "pages": 15,
    "has_next": true,
    "has_prev": false
  }
}
```

---

### 3.4 Credit Applications (Solicitudes de Crédito)

#### `POST /api/v1/credit-applications/`

Crea una nueva solicitud de crédito.

**Autenticación:** Requerida  
**Permisos:** Solo `applicant`

**Body (JSON):**

```json
{
  "requested_amount": 500000.00,
  "term_months": 24,
  "interest_rate": 12.5,
  "status": "draft",
  "purpose": "working_capital",
  "purpose_other": null
}
```

**Campos:**

| Campo | Tipo | Requerido | Validación | Descripción |
|-------|------|-----------|------------|-------------|
| `requested_amount` | number/string | ✓ | > 0 | Monto solicitado |
| `term_months` | integer | ✓ | 1-360 | Plazo en meses |
| `interest_rate` | number/string | ✗ | > 0 | Tasa de interés (default: 10) |
| `status` | enum | ✗ | ver CreditApplicationStatus | Estado inicial (default: "pending") |
| `purpose` | enum | ✓ | ver CreditApplicationPurpose | Propósito del crédito |
| `purpose_other` | string | ✗ | - | Descripción si purpose="other" |

**Enums:**

**CreditApplicationStatus:** `draft`, `pending`, `in_review`, `approved`, `rejected`

**CreditApplicationPurpose:** `working_capital`, `equipment`, `expansion`, `inventory`, `refinancing`, `other`

**Respuesta:** `200 OK`

```json
{
  "id": "f1e2d3c4-b5a6-7890-1234-567890abcdef",
  "company_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "requested_amount": "500000.00",
  "purpose": "working_capital",
  "purpose_other": null,
  "term_months": 24,
  "status": "pending",
  "risk_score": null,
  "approved_amount": null,
  "interest_rate": "12.50",
  "created_at": "2025-11-02T10:00:00Z",
  "updated_at": "2025-11-02T10:00:00Z"
}
```

---

#### `GET /api/v1/credit-applications/`

Lista solicitudes de crédito con paginación y filtros.

**Autenticación:** Requerida  
**Permisos:**
- `applicant`: solo ve sus propias solicitudes
- `operator`/`admin`: ven todas las solicitudes

**Query parameters:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `status` | enum | null | Filtrar por estado |
| `company_id` | UUID | null | Filtrar por empresa |
| `page` | integer | 1 | Número de página |
| `limit` | integer | 10 | Elementos por página (1-100) |
| `sort` | string | null | Campo para ordenar* |
| `order` | string | "desc" | Orden: "asc" o "desc" |

**Campos permitidos para ordenamiento (`sort`):**
- `id`
- `requested_amount`
- `term_months`
- `status`
- `risk_score`
- `approved_amount`
- `interest_rate`
- `created_at`
- `updated_at`

**Respuesta:** `200 OK`

```json
{
  "items": [
    {
      "id": "f1e2d3c4-...",
      "company_id": "a1b2c3d4-...",
      "requested_amount": "500000.00",
      "status": "pending",
      ...
    }
  ],
  "meta": {
    "total": 25,
    "page": 1,
    "per_page": 10,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

---

#### `GET /api/v1/credit-applications/{application_id}`

Obtiene una solicitud por ID.

**Autenticación:** Requerida  
**Permisos:**
- `applicant`: solo su propia solicitud
- `operator`/`admin`: cualquier solicitud

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `application_id` | UUID | ID de la solicitud |

**Respuesta:** `200 OK` (ver estructura en POST)

**Errores comunes:**

- `403 Forbidden`: Applicant accediendo a solicitud ajena
- `404 Not Found`: Solicitud no existe

---

#### `PATCH /api/v1/credit-applications/{application_id}`

Actualiza parcialmente una solicitud de crédito.

**Autenticación:** Requerida  
**Permisos y restricciones:**

**Applicants:**
- Solo pueden actualizar solicitudes en estado `draft`
- Solo pueden cambiar `status` de `draft` → `pending` o `draft` → `draft`
- No pueden modificar `approved_amount` ni `risk_score`
- Si la solicitud está en `pending`, no pueden modificar ningún campo

**Operators/Admins:**
- Pueden cambiar el estado de solicitudes que NO estén en `draft` a cualquier otro estado (excepto volver a `draft`)
- Pueden modificar todos los campos incluyendo `approved_amount` y `risk_score`

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `application_id` | UUID | ID de la solicitud |

**Body (JSON) - Todos los campos opcionales:**

```json
{
  "requested_amount": 600000.00,
  "term_months": 36,
  "interest_rate": 11.0,
  "status": "in_review",
  "purpose": "expansion",
  "purpose_other": null,
  "risk_score": 75.5,
  "approved_amount": 550000.00
}
```

**Campos:**

| Campo | Tipo | Validación | Solo operator/admin |
|-------|------|------------|---------------------|
| `requested_amount` | number/string | > 0 | ✗ |
| `term_months` | integer | 1-360 | ✗ |
| `interest_rate` | number/string | > 0 | ✗ |
| `status` | enum | ver restricciones arriba | Parcial |
| `purpose` | enum | CreditApplicationPurpose | ✗ |
| `purpose_other` | string | - | ✗ |
| `risk_score` | number/string | 0-100 | ✓ |
| `approved_amount` | number/string | > 0, ≤ requested_amount | ✓ |

**Validaciones especiales:**

- `approved_amount` no puede ser mayor que `requested_amount`

**Respuesta:** `200 OK` (CreditApplicationResponse actualizada)

**Errores comunes:**

- `403 Forbidden`: 
  - Applicant intentando modificar solicitud en pending/review
  - Applicant intentando cambiar risk_score o approved_amount
  - Transición de estado no permitida
- `400 Bad Request`: Validación fallida (ej: approved_amount > requested_amount)

---

#### `DELETE /api/v1/credit-applications/{application_id}`

Elimina una solicitud de crédito.

**Autenticación:** Requerida  
**Permisos:**
- `applicant`: solo puede eliminar sus propias solicitudes en estado `draft`
- `operator`/`admin`: pueden eliminar cualquier solicitud

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `application_id` | UUID | ID de la solicitud |

**Respuesta:** `204 No Content`

**Errores comunes:**

- `403 Forbidden`: 
  - Applicant intentando eliminar solicitud ajena
  - Applicant intentando eliminar solicitud que no está en draft
- `404 Not Found`: Solicitud no existe

---

### 3.5 Documents (Documentos)

#### `GET /api/v1/documents/`

Lista documentos con paginación y filtros.

**Autenticación:** Requerida  
**Permisos:**
- `applicant`: solo ve sus propios documentos
- `operator`/`admin`: ven todos los documentos (pueden filtrar por application_id)

**Query parameters:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `application_id` | UUID | null | Filtrar por solicitud |
| `page` | integer | 1 | Número de página |
| `limit` | integer | 10 | Elementos por página (1-100) |
| `sort` | string | null | Campo para ordenar |
| `order` | string | "desc" | Orden: "asc" o "desc" |

**Respuesta:** `200 OK`

```json
{
  "items": [
    {
      "id": "d1c2b3a4-5678-90ef-1234-567890abcdef",
      "user_id": "c213241d-b01b-4dc4-b7b1-ace7f5c4e26c",
      "application_id": "f1e2d3c4-b5a6-7890-1234-567890abcdef",
      "storage_path": "documents/user123/file.pdf",
      "bucket_name": "documents",
      "file_name": "file.pdf",
      "file_size": 1048576,
      "mime_type": "application/pdf",
      "document_type": "financial_statement",
      "status": "uploaded",
      "extra_metadata": {
        "requires_signature": true
      },
      "signature_status": "pending",
      "signature_request_id": null,
      "signed_at": null,
      "signed_file_path": null,
      "created_at": "2025-11-01T14:00:00Z",
      "updated_at": "2025-11-01T14:00:00Z"
    }
  ],
  "meta": {
    "total": 8,
    "page": 1,
    "per_page": 10,
    "pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

**Enums:**

**DocumentType:** `tax_return`, `financial_statement`, `id_document`, `business_license`, `bank_statement`, `other`

**DocumentStatus:** `requested`, `uploaded`, `pending`, `approved`, `rejected`

**SignatureStatus:** `unsigned`, `pending`, `signed`, `declined`

---

#### `GET /api/v1/documents/{document_id}`

Obtiene un documento por ID.

**Autenticación:** Requerida  
**Permisos:**
- `applicant`: solo sus propios documentos
- `operator`/`admin`: cualquier documento

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `document_id` | UUID | ID del documento |

**Respuesta:** `200 OK` (ver estructura en lista)

**Errores comunes:**

- `403 Forbidden`: Applicant accediendo a documento ajeno
- `404 Not Found`: Documento no existe

---

#### `PATCH /api/v1/documents/{document_id}`

Actualiza el status de revisión de un documento.

**Autenticación:** Requerida  
**Permisos:** Solo `operator` y `admin`

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `document_id` | UUID | ID del documento |

**Body (JSON):**

```json
{
  "status": "approved"
}
```

**Valores permitidos para `status`:**
- `pending` - En revisión
- `approved` - Aprobado
- `rejected` - Rechazado

**Nota:** El estado `uploaded` lo establece automáticamente el sistema cuando el archivo es subido.

**Respuesta:** `200 OK` (DocumentResponse actualizado)

**Errores comunes:**

- `403 Forbidden`: Applicant intentando actualizar status
- `404 Not Found`: Documento no existe

---

#### `POST /api/v1/documents/request`

Crea una solicitud de documento (placeholder) sin archivo aún.

**Autenticación:** Requerida  
**Permisos:** Solo `operator` y `admin`

**Body (JSON):**

```json
{
  "application_id": "f1e2d3c4-b5a6-7890-1234-567890abcdef",
  "document_type": "bank_statement",
  "notes": "Por favor suba sus estados de cuenta de los últimos 6 meses"
}
```

**Campos:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `application_id` | UUID | ✓ | ID de solicitud asociada |
| `document_type` | enum | ✓ | Tipo de documento (DocumentType) |
| `notes` | string | ✓ | Instrucciones para el solicitante |

**Respuesta:** `200 OK`

```json
{
  "id": "d1c2b3a4-5678-90ef-1234-567890abcdef",
  "user_id": "c213241d-b01b-4dc4-b7b1-ace7f5c4e26c",
  "application_id": "f1e2d3c4-b5a6-7890-1234-567890abcdef",
  "storage_path": null,
  "bucket_name": null,
  "file_name": null,
  "file_size": null,
  "mime_type": null,
  "document_type": "bank_statement",
  "status": "requested",
  "extra_metadata": {
    "request": {
      "requested_by": "c213241d-b01b-4dc4-b7b1-ace7f5c4e26c",
      "requested_at": "2025-11-02T10:00:00Z",
      "notes": "Por favor suba sus estados de cuenta de los últimos 6 meses"
    }
  },
  "signature_status": "unsigned",
  "signature_request_id": null,
  "signed_at": null,
  "signed_file_path": null,
  "created_at": "2025-11-02T10:00:00Z",
  "updated_at": "2025-11-02T10:00:00Z"
}
```

**Flujo de trabajo:**

1. Operator crea placeholder con `POST /documents/request`
2. Documento queda en estado `status: "requested"` con campos de archivo en `null`
3. Applicant ve el documento solicitado y las notas en `extra_metadata.request.notes`
4. Applicant sube el archivo mediante Supabase Storage SDK (ver sección 6.2)
5. El trigger automático actualiza el documento con los metadatos del archivo y cambia `status` a `"uploaded"`

---

#### `POST /api/v1/documents/{document_id}/sign`

Inicia el proceso de firma digital embebida usando HelloSign.

**Autenticación:** Requerida  
**Permisos:**
- `applicant`: solo sus propios documentos
- `operator`/`admin`: pueden iniciar firma de cualquier documento

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `document_id` | UUID | ID del documento a firmar |

**Body (JSON):**

```json
{
  "signer_email": "firmante@example.com",
  "signer_name": "Juan Pérez",
  "callback_url": "https://mi-app.com/signature-callback"
}
```

**Campos:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `signer_email` | string | ✓ | Email del firmante |
| `signer_name` | string | ✓ | Nombre completo del firmante |
| `callback_url` | string | ✗ | URL de callback al completar |

**Validaciones previas:**

- El documento debe existir y tener `storage_path` válido (estar uploaded)
- El documento no debe estar ya firmado (`signature_status != "signed"`)

**Respuesta:** `200 OK`

```json
{
  "signature_request_id": "fa5c8a0b6a111a30c6e42fda87a1e5f5",
  "signing_url": "https://app.hellosign.com/editor/embeddedSign?signature_id=...",
  "expires_at": "2025-11-02T11:00:00Z"
}
```

**Uso de la URL de firma:**

- La `signing_url` puede ser abierta en un iframe o ventana nueva
- El usuario completa el proceso de firma en HelloSign
- Al finalizar, HelloSign notifica vía webhook (ver sección 6.3)
- El sistema actualiza automáticamente `signature_status` a `"signed"`

**Errores comunes:**

- `403 Forbidden`: 
  - Usuario sin acceso al documento
  - Documento ya firmado
- `404 Not Found`: Documento no existe
- `400 Bad Request`: Documento sin archivo subido (storage_path null)

---

### 3.6 Metadata (Datos de Catálogo)

#### `GET /api/v1/metadata/credit-purposes`

Obtiene la lista de propósitos de crédito válidos para el frontend.

**Autenticación:** No requerida

**Respuesta:** `200 OK`

```json
[
  {
    "value": 1,
    "slug": "working_capital",
    "label": "Capital de trabajo"
  },
  {
    "value": 2,
    "slug": "equipment",
    "label": "Compra de equipo"
  },
  {
    "value": 3,
    "slug": "expansion",
    "label": "Expansión del negocio"
  },
  {
    "value": 4,
    "slug": "inventory",
    "label": "Inventario"
  },
  {
    "value": 5,
    "slug": "refinancing",
    "label": "Refinanciamiento"
  },
  {
    "value": 6,
    "slug": "other",
    "label": "Otro"
  }
]
```

**Uso:** Usar el campo `slug` al crear/actualizar solicitudes de crédito.

---

## 4. Schemas de Datos

### 4.1 CompanyAddress

```json
{
  "street": "string",
  "city": "string",
  "state": "string",
  "zip_code": "string",
  "country": "string"
}
```

### 4.2 PaginationMeta

```json
{
  "total": 150,
  "page": 1,
  "per_page": 10,
  "pages": 15,
  "has_next": true,
  "has_prev": false
}
```

### 4.3 Enumeraciones

#### UserRole

```
applicant | operator | admin
```

#### CreditApplicationStatus

```
draft | pending | in_review | approved | rejected
```

#### CreditApplicationPurpose

```
working_capital | equipment | expansion | inventory | refinancing | other
```

#### DocumentType

```
tax_return | financial_statement | id_document | business_license | bank_statement | other
```

#### DocumentStatus

```
requested | uploaded | pending | approved | rejected
```

#### SignatureStatus

```
unsigned | pending | signed | declined
```

---

## 5. Flujos de Negocio End-to-End

### 5.1 Flujo Completo: Solicitud de Crédito

**Pasos detallados:**

1. **Applicant crea borrador** (`status: draft`)
   - Puede editar todos los campos
   - Puede eliminar la solicitud

2. **Applicant envía solicitud** (cambiar `status` a `pending`)
   - Ya no puede editar campos de la solicitud
   - Ya no puede eliminar
   - Solo puede cambiar status de vuelta a `draft` si necesita editar

3. **Operator revisa solicitud**
   - Lista solicitudes con `status: pending`
   - Puede solicitar documentos adicionales
   - Cambia `status` a `in_review`

4. **Operator evalúa y decide**
   - Actualiza `risk_score` (0-100)
   - Si aprueba: establece `approved_amount` y cambia `status` a `approved`
   - Si rechaza: cambia `status` a `rejected`

---

### 5.2 Flujo: Solicitud y Firma de Documentos

**Pasos detallados:**

1. **Operator solicita documento**
   - `POST /documents/request` con `application_id`, `document_type`, `notes`
   - Se crea un placeholder con `status: "requested"` y campos de archivo en `null`
   - El `extra_metadata.request.notes` contiene las instrucciones

2. **Applicant ve documento solicitado**
   - `GET /documents/` muestra documentos con `status: "requested"`
   - Lee las notas en `extra_metadata.request.notes`

3. **Applicant sube archivo**
   - Usa Supabase Storage SDK (JavaScript) para subir el archivo
   - **Importante:** Debe incluir el `document_id` en el `user_metadata` del upload:
     ```javascript
     const { data, error } = await supabase.storage
       .from('documents')
       .upload(filePath, file, {
         metadata: {
           user_id: userId,
           application_id: applicationId,
           document_id: documentId,  // ← ID del placeholder
           document_type: 'bank_statement'
         }
       })
     ```
   - El trigger `handle_storage_upload` detecta el `document_id` y actualiza el registro existente
   - El `status` cambia automáticamente a `"uploaded"`

4. **Operator marca documento para firma** (opcional)
   - Si el documento requiere firma, al subirlo puede incluir `requires_signature: true` en metadata
   - Esto se guarda en `extra_metadata.requires_signature`
   - **Validación:** Solo operators/admins pueden usar `requires_signature: true` (validado por rol JWT en el trigger)

5. **Applicant inicia proceso de firma**
   - `POST /documents/{id}/sign` con datos del firmante
   - Recibe `signing_url` para abrir en iframe o popup
   - El usuario firma el documento en HelloSign

6. **HelloSign notifica firma completada**
   - Webhook actualiza `signature_status` a `"signed"`
   - Se almacena la ruta del archivo firmado en `signed_file_path`

---

### 5.3 Flujo: Subida Directa de Documento (sin placeholder)

**Caso de uso:** Applicant sube un documento por iniciativa propia (no fue solicitado por operator).

**Diferencias clave:**

- **NO** incluye `document_id` en el `user_metadata` del upload
- El trigger crea un **nuevo** registro en lugar de actualizar uno existente
- El documento se crea directamente con `status: "uploaded"`

**Metadata mínimo requerido:**

```javascript
const { data, error } = await supabase.storage
  .from('documents')
  .upload(filePath, file, {
    metadata: {
      user_id: userId,                    // ✓ Requerido
      application_id: applicationId,      // Opcional
      document_type: 'financial_statement' // Opcional
    }
  })
```

---

## 6. Integraciones Externas

### 6.1 Supabase Auth

**URL base:** `https://<SUPABASE_PROJECT_URL>/auth/v1`

**Endpoints principales:**

- `POST /token?grant_type=password` - Login con email/password
- `POST /token?grant_type=refresh_token` - Renovar token
- `POST /signup` - Registro de nuevo usuario
- `POST /logout` - Cerrar sesión

**Configuración en cliente:**

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  '<SUPABASE_PROJECT_URL>',
  '<SUPABASE_ANON_KEY>'
)

// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'usuario@example.com',
  password: 'contraseña'
})

// Obtener token para la API
const token = data.session.access_token

// Usar en peticiones a la API
fetch('http://localhost:8000/api/v1/credit-applications/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

**Gestión de roles:**

Los roles se asignan mediante custom claims en el JWT. El campo `user_role` debe configurarse en el JWT payload durante el proceso de autenticación (configurar mediante Supabase Auth Hooks o Database Triggers).

---

### 6.2 Supabase Storage

**Bucket:** `documents`

**Trigger automático (`handle_storage_upload`):**

Al subir un archivo a Supabase Storage, el trigger `handle_storage_upload` se ejecuta automáticamente en el evento `AFTER INSERT` de `storage.objects`.

**Comportamiento del trigger:**

1. **Si hay `document_id` en `user_metadata`:**
   - Busca el documento con ese ID en `public.documents`
   - Si existe, lo actualiza con los metadatos del archivo:
     - `storage_path`, `bucket_name`, `file_name`, `file_size`, `mime_type`
     - Cambia `status` a `"uploaded"`
     - Añade info del upload en `metadata.upload` (uploaded_at, uploader_user_id, etc.)
   - Si no existe, continúa con el flujo de inserción normal

2. **Si NO hay `document_id` (flujo normal de inserción):**
   - Valida que `user_id` en metadata sea válido
   - Si hay `application_id`, valida que pertenezca a la empresa del usuario
   - Crea un nuevo documento con los metadatos del archivo
   - Establece `status` como `"uploaded"`

3. **Si hay `requires_signature: true` en `user_metadata`:**
   - **Validación de seguridad:** Solo usuarios con `user_role: "operator"` o `"admin"` pueden usar este flag
   - El rol se extrae del JWT: `current_setting('request.jwt.claims')::jsonb->>'user_role'`
   - Si un applicant intenta usar este flag, el trigger lanza excepción: `"PERMISO DENEGADO"`
   - Se guarda en `extra_metadata.requires_signature` para consulta desde la API

**Ejemplos de subida:**

```javascript
// Caso 1: Asociar a placeholder existente
const { data, error } = await supabase.storage
  .from('documents')
  .upload(`applications/${applicationId}/${fileName}`, file, {
    metadata: {
      user_id: user.id,
      application_id: applicationId,
      document_id: placeholderId,  // ← Actualiza documento existente
      document_type: 'bank_statement'
    }
  })

// Caso 2: Subida por iniciativa propia
const { data, error } = await supabase.storage
  .from('documents')
  .upload(`applications/${applicationId}/${fileName}`, file, {
    metadata: {
      user_id: user.id,
      application_id: applicationId,
      document_type: 'financial_statement'
      // NO incluir document_id → crea nuevo documento
    }
  })

// Caso 3: Operator sube documento que requiere firma
const { data, error } = await supabase.storage
  .from('documents')
  .upload(`applications/${applicationId}/${fileName}`, file, {
    metadata: {
      user_id: user.id,
      application_id: applicationId,
      document_type: 'contract',
      requires_signature: true  // ← Solo operator/admin
    }
  })
```

**Validaciones de seguridad en el trigger:**

- El `user_id` debe ser un UUID válido
- Si hay `application_id`, debe existir en `credit_applications` y pertenecer a la empresa del usuario
- Solo usuarios con rol `operator` o `admin` pueden usar `requires_signature: true`
- El trigger usa `security definer` y `set search_path = public` para mayor seguridad

---

### 6.3 HelloSign (Dropbox Sign)

**Propósito:** Firma digital embebida de documentos.

**API:** HelloSign Embedded Signature Request API

**Configuración:**

- `HELLOSIGN_API_KEY` - API key de HelloSign
- `HELLOSIGN_CLIENT_ID` - Client ID para modo embebido

**Flujo:**

1. API crea Signature Request con `POST /documents/{id}/sign`
2. HelloSign genera URL de firma embebida
3. Usuario firma el documento en iframe/popup
4. HelloSign envía webhook al completar

**Webhook:**

El webhook de HelloSign se configura en el dashboard de HelloSign. Cuando un documento es firmado, HelloSign envía una notificación POST al endpoint configurado.

**Eventos del webhook:**

- `signature_request_signed` - Documento firmado por un firmante
- `signature_request_all_signed` - Todos los firmantes completaron
- `signature_request_declined` - Firma rechazada
- `signature_request_viewed` - Documento visto

**Procesamiento del webhook:**

Cuando HelloSign notifica que un documento fue firmado:

1. API valida la firma HMAC del webhook
2. Extrae el `signature_request_id` del payload
3. Busca el documento correspondiente en la BD
4. Actualiza:
   - `signature_status` → `"signed"`
   - `signed_at` → timestamp actual
   - `signed_file_path` → ruta del archivo firmado (si disponible)

**Nota:** La implementación del webhook handler no está documentada en el OpenAPI actual. Se recomienda implementarlo como un endpoint separado (ej: `POST /api/v1/webhooks/hellosign`) que no requiera autenticación JWT pero valide la firma HMAC de HelloSign.

---

## 7. Manejo de Errores

### 7.1 Códigos de Estado HTTP

| Código | Significado | Uso |
|--------|-------------|-----|
| 200 | OK | Operación exitosa (GET, PATCH, POST) |
| 204 | No Content | Operación exitosa sin contenido (DELETE) |
| 400 | Bad Request | Validación fallida, datos inválidos |
| 401 | Unauthorized | Token ausente o inválido |
| 403 | Forbidden | Token válido pero sin permisos |
| 404 | Not Found | Recurso no existe |
| 422 | Unprocessable Entity | Validación de campos Pydantic fallida |
| 500 | Internal Server Error | Error del servidor |

### 7.2 Formato de Errores

**Errores de validación (422):**

```json
{
  "detail": [
    {
      "loc": ["body", "requested_amount"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

**Errores de negocio (400, 403, 404):**

```json
{
  "detail": "approved_amount (600000.00) no puede ser mayor que requested_amount (500000.00)"
}
```

**Errores de autenticación (401):**

```json
{
  "detail": "Could not validate credentials"
}
```

**Errores de permisos (403):**

```json
{
  "detail": "No tiene permisos para acceder a este recurso"
}
```

### 7.3 Errores Comunes por Endpoint

Ver sección de cada endpoint para errores específicos.

---

## 8. Paginación y Filtrado

### 8.1 Parámetros de Paginación

Todos los endpoints de listado soportan:

| Parámetro | Tipo | Default | Rango | Descripción |
|-----------|------|---------|-------|-------------|
| `page` | integer | 1 | ≥ 1 | Número de página |
| `limit` | integer | 10 | 1-100 | Elementos por página |
| `sort` | string | null | - | Campo para ordenar |
| `order` | string | "desc" | asc, desc | Orden ascendente/descendente |

### 8.2 Formato de Respuesta Paginada

```json
{
  "items": [...],
  "meta": {
    "total": 150,
    "page": 1,
    "per_page": 10,
    "pages": 15,
    "has_next": true,
    "has_prev": false
  }
}
```

### 8.3 Ejemplos de Uso

```bash
# Primera página (10 items)
GET /api/v1/credit-applications/?page=1&limit=10

# Ordenar por monto solicitado (mayor a menor)
GET /api/v1/credit-applications/?sort=requested_amount&order=desc

# Filtrar por estado y ordenar por fecha
GET /api/v1/credit-applications/?status=pending&sort=created_at&order=asc

# Página 3 con 25 items, filtrado por empresa
GET /api/v1/companies/?page=3&limit=25&sort=legal_name&order=asc
```

---

## 9. Seguridad y Mejores Prácticas

### 9.1 Autenticación

- **NUNCA** exponer tokens en URLs, logs o mensajes de error
- Renovar tokens antes de que expiren usando `refresh_token`
- Implementar logout del lado del cliente eliminando tokens del storage

### 9.2 Almacenamiento de Tokens (Frontend)

**Opción recomendada:** `localStorage` o `sessionStorage`

```javascript
// Guardar token
localStorage.setItem('access_token', token)

// Recuperar token
const token = localStorage.getItem('access_token')

// Logout
localStorage.removeItem('access_token')
localStorage.removeItem('refresh_token')
```

**Nota:** Para mayor seguridad en producción, considerar usar cookies `httpOnly` con backend proxy.

### 9.3 Validación de Permisos

El cliente debe validar permisos antes de mostrar UI:

```javascript
// Ejemplo: Mostrar botón solo a operators
if (user.user_role === 'operator' || user.user_role === 'admin') {
  showApproveButton()
}
```

**Importante:** La validación del lado del cliente es solo para UX. La API siempre valida permisos del lado del servidor.

### 9.4 Subida de Archivos

**Validaciones recomendadas del cliente:**

- Tamaño máximo: 10MB (ajustar según necesidades)
- Tipos MIME permitidos: `application/pdf`, `image/*`, etc.
- Sanitizar nombres de archivo antes de subir

**Ejemplo:**

```javascript
const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB

if (file.size > MAX_FILE_SIZE) {
  alert('El archivo es demasiado grande')
  return
}

if (!file.type.startsWith('application/pdf') && !file.type.startsWith('image/')) {
  alert('Solo se permiten archivos PDF e imágenes')
  return
}
```

### 9.5 CORS

La API implementa CORS dinámico basado en el entorno:

- **Desarrollo (`ENVIRONMENT != "production"`)**: Permite todos los orígenes (`*`)
- **Producción (`ENVIRONMENT == "production"`)**: 
  - Si `PROD_DOMAIN` está configurado → permite solo ese dominio
  - Si `PROD_DOMAIN` no está configurado → lanza `RuntimeError` al iniciar

**Configuración recomendada para producción:**

```bash
ENVIRONMENT=production
PROD_DOMAIN=https://app.example.com
```

---

## 10. Variables de Entorno

Variables requeridas para ejecutar la API:

```bash
# Supabase
SUPABASE_URL=https://<project-id>.supabase.co
SUPABASE_ANON_KEY=<anon-key>
SUPABASE_SERVICE_KEY=<service-key>

# HelloSign
HELLOSIGN_API_KEY=<api-key>
HELLOSIGN_CLIENT_ID=<client-id>

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# API
ENVIRONMENT=development  # development | production
PROD_DOMAIN=https://api.example.com  # Solo requerido para production
PORT=8000
```

---

## 11. Comandos Útiles

**Iniciar servidor de desarrollo:**

```bash
uv run fastapi dev app/main.py
```

**Ejecutar tests:**

```bash
uv run pytest -q
```

**Generar OpenAPI JSON:**

```bash
curl http://localhost:8000/openapi.json > openapi.json
```

**Aplicar migraciones de BD:**

```bash
# Aplicar función de trigger
psql -U <user> -d <database> -f db/functions/handle_storage_upload.sql

# Aplicar migración de enum
psql -U <user> -d <database> -f db/migrations/add_requested_to_document_status.sql
```

---

## 12. Changelog

### Versión 0.1.0 (2025-11-02)

**Features iniciales:**

- Sistema completo de autenticación con Supabase Auth y roles
- CRUD de empresas (companies)
- CRUD de solicitudes de crédito (credit applications) con workflow de estados
- Sistema de documentos con placeholders y subida a Supabase Storage
- Integración de firma digital con HelloSign
- Trigger automático `handle_storage_upload` para asociar uploads con documentos
- Validación de permisos por rol en trigger (requires_signature solo para operators)
- CORS dinámico basado en entorno
- Paginación y filtrado en endpoints de listado
- Metadata de catálogos (credit purposes)

**Reglas de negocio implementadas:**

- Applicants solo pueden modificar solicitudes en draft
- Applicants solo pueden cambiar status de draft→pending
- Applicants solo pueden eliminar solicitudes en draft
- Operators/admins pueden modificar y cambiar estados de solicitudes (excepto volver a draft)
- Validación: approved_amount ≤ requested_amount
- Documentos requested → uploaded (trigger automático)
- Solo operators/admins pueden marcar documentos para firma

---

## 13. Soporte

**Repositorio:** `api-creditos-pymes`

**Documentación interactiva:** 
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

**Fin de la especificación técnica**

*Documento generado el 2025-11-02 basado en OpenAPI 0.1.0*
