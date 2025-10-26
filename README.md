# API Créditos PyMEs

API REST para gestión de solicitudes de crédito a PyMEs, desarrollada con FastAPI y Supabase.

## 📋 Requisitos

- Python 3.13+
- UV (gestor de paquetes)
- Base de datos PostgreSQL accesible (puede ser Supabase)

## 🚀 Instalación

1. Clonar el repositorio:

```bash
git clone https://github.com/CreditosPYMES-NCG27/api-creditos-pymes.git

```

2. Instalar dependencias con UV:

```bash
uv sync
```

3. Configurar variables de entorno:

```bash
cp .env.example .env
```

Editar `.env` con tus credenciales (ver variables usadas en `app/config.py`):

```env
# Supabase
SUPABASE_URL=https://my-project-id.supabase.co
SUPABASE_SECRET_KEY=your_service_role_key_here

# Database
DB_USER=postgres
DB_PASS=postgres
DB_NAME=postgres
DB_HOST=localhost
DB_PORT=5432

# HelloSign (Dropbox Sign) - Para firma electrónica de documentos
HELLOSIGN_API_KEY=your_hellosign_api_key
HELLOSIGN_CLIENT_ID=your_hellosign_client_id
```

**Notas importantes:**
- `SUPABASE_SECRET_KEY`: La **service_role key** de tu proyecto Supabase (Settings → API)
- `HELLOSIGN_API_KEY` y `HELLOSIGN_CLIENT_ID`: Obtenerlos en [HelloSign API Settings](https://app.hellosign.com/home/myAccount#api)
- Para configurar webhooks de HelloSign, consulta [`docs/HELLOSIGN_WEBHOOK.md`](docs/HELLOSIGN_WEBHOOK.md)

## 🏃 Ejecución

Ejecutar el servidor de desarrollo:

```bash
uv run fastapi dev app/main.py
```

La API estará disponible en: `http://localhost:8000`

## 📚 Documentación de la API

Una vez iniciado el servidor, accede a:

- **Swagger UI (interactiva)**: http://localhost:8000/docs
- **ReDoc (documentación)**: http://localhost:8000/redoc

## 🛠️ Estructura del Proyecto (resumen)

```
api-creditos-pymes/
├── app/
│   ├── main.py              # Punto de entrada de la aplicación
│   ├── config.py            # Configuración y variables de entorno
│   ├── bootstrap.py         # Lifespan (DB y JWKS)
│   ├── exception_handlers.py# Mapeo de errores de dominio a HTTP
│   ├── core/                # Enums y errores
│   ├── dependencies/        # Dependencias (auth, db, services)
│   ├── schemas/             # Modelos Pydantic (esquemas de datos)
│   │   ├── company.py
│   │   ├── credit_application.py
│   │   ├── profile.py
│   │   └── __init__.py
│   ├── repositories/        # Acceso a datos (SQLModel/SQLAlchemy)
│   │   ├── companies_repository.py
│   │   ├── credit_applications_repository.py
│   │   ├── profiles_repository.py
│   │   └── __init__.py
│   ├── routers/             # Endpoints por módulo
│   │   ├── companies.py
│   │   ├── credit_applications.py
│   │   ├── metadata.py
│   │   ├── profiles.py
│   │   └── __init__.py
│   └── services/            # Lógica de negocio
│       ├── company_service.py
│       ├── credit_application_service.py
│       ├── profile_service.py
│       └── __init__.py
├── .env                     # Variables de entorno (no incluir en git)
├── .env.example             # Plantilla de variables de entorno
├── pyproject.toml           # Configuración del proyecto
└── README.md
```

Para detalles completos, consulta `SPECIFICATION.md`.

## 📝 Endpoints Disponibles (implementados)

### Raíz y Health Check

| Método | Endpoint       | Descripción                 |
| ------ | -------------- | --------------------------- |
| GET    | `/`            | Estado de la API            |
| GET    | `/health`      | Health check de la API      |

### Perfiles (Auth)

| Método | Endpoint              | Descripción                              |
| ------ | --------------------- | ---------------------------------------- |
| GET    | `/api/v1/profiles/me` | Obtener perfil del usuario autenticado   |

### Empresas

| Método | Endpoint                    | Descripción                              |
| ------ | --------------------------- | ---------------------------------------- |
| GET    | `/api/v1/companies/`        | Listar empresas (paginado)              |
| GET    | `/api/v1/companies/{id}`    | Obtener empresa por ID                  |
| GET    | `/api/v1/companies/me`      | Obtener empresa del usuario autenticado |
| PATCH  | `/api/v1/companies/me`      | Actualizar parcialmente tu empresa      |

### Solicitudes de Crédito

| Método | Endpoint                              | Descripción                              |
| ------ | ------------------------------------- | ---------------------------------------- |
| GET    | `/api/v1/credit-applications/`        | Listar solicitudes (filtros y paginación) |
| POST   | `/api/v1/credit-applications/`        | Crear nueva solicitud                    |
| GET    | `/api/v1/credit-applications/{id}`    | Obtener solicitud por ID                 |
| PATCH  | `/api/v1/credit-applications/{id}`    | Actualizar solicitud (operadores/admin)  |

### Metadatos

| Método | Endpoint                          | Descripción                              |
| ------ | --------------------------------- | ---------------------------------------- |
| GET    | `/api/v1/metadata/credit-purposes`| Listar propósitos válidos de crédito     |

## 🔐 Autenticación

Esta API valida tokens JWT emitidos por Supabase Auth (u otro emisor compatible) usando JWKS:

- El servidor valida `issuer` `${SUPABASE_URL}/auth/v1`, `audience` `authenticated` y algoritmo ES256.
- Todos los endpoints protegidos requieren header `Authorization: Bearer {JWT_TOKEN}`.

**Ejemplo de llamada autenticada:**

```bash
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1..." \
  http://localhost:8000/api/v1/profiles/me
```

## 🗄️ Base de Datos

La API utiliza PostgreSQL mediante SQLModel/SQLAlchemy. En `db/` hay scripts SQL (tipos/tablas/políticas) que puedes usar como referencia o punto de partida.

Tablas principales del modelo actual (ver `app/models/*`):
- `profiles` - Perfiles de usuarios
- `companies` - Empresas (PyMEs)
- `credit_applications` - Solicitudes de crédito

## 👥 Equipo

CreditosPYMES-NCG27

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

Para especificación técnica detallada de endpoints, esquemas y reglas de negocio, ver: [SPECIFICATION.md](./SPECIFICATION.md)
