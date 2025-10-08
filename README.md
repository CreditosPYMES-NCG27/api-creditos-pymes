# API Créditos PyMEs

API REST para gestión de solicitudes de crédito a PyMEs, desarrollada con FastAPI y Supabase.

## 📋 Requisitos

- Python 3.13+
- UV (gestor de paquetes)
- Cuenta de Supabase (base de datos y autenticación)

## 🚀 Instalación

1. Clonar el repositorio:

```bash
git clone https://github.com/CreditosPYMES-NCG27/api-creditos-pymes.git
cd api-creditos-pymes
```

2. Instalar dependencias con UV:

```bash
uv sync
```

3. Configurar variables de entorno:

```bash
cp .env.example .env
```

Editar `.env` con tus credenciales de Supabase:

```env
SUPABASE_URL=https://my-project-id.supabase.co
SUPABASE_PUBLISHABLE_KEY=my-publishable-key
SUPABASE_SECRET_KEY=my-secret-key
```

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

## 🛠️ Estructura del Proyecto

```
api-creditos-pymes/
├── app/
│   ├── main.py              # Punto de entrada de la aplicación
│   ├── config.py            # Configuración y variables de entorno
│   ├── dependencies.py      # Dependencias compartidas (auth, Supabase)
│   ├── models/              # Modelos Pydantic (schemas)
│   │   └── user.py
│   ├── repositories/        # Acceso a datos
│   │   └── user_repository.py
│   ├── routers/             # Endpoints por módulo
│   │   └── auth.py
│   └── services/            # Lógica de negocio
│       └── user_service.py
├── .env                     # Variables de entorno (no incluir en git)
├── .env.example             # Plantilla de variables de entorno
├── pyproject.toml           # Configuración del proyecto
└── README.md
```

## 📝 Endpoints Disponibles

### Raíz y Health Check

| Método | Endpoint  | Descripción                 |
| ------ | --------- | --------------------------- |
| GET    | `/`       | Estado de la API            |
| GET    | `/health` | Health check de la API      |

### Autenticación

| Método | Endpoint       | Descripción                              |
| ------ | -------------- | ---------------------------------------- |
| GET    | `/api/v1/auth/me` | Obtener perfil del usuario autenticado |

## 🔐 Autenticación

Esta API utiliza **Supabase Auth** para autenticación:

- Los usuarios se registran y autentican directamente contra Supabase
- La API valida tokens JWT en cada request
- Todos los endpoints protegidos requieren header `Authorization: Bearer {JWT_TOKEN}`

**Ejemplo de llamada autenticada:**

```bash
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1..." \
  http://localhost:8000/api/v1/auth/me
```

## 🗄️ Base de Datos

La API utiliza **Supabase (PostgreSQL)** con Row Level Security (RLS).

**Tablas principales:**
- `users` - Usuarios extendidos
- `companies` - Empresas (PyMEs)
- `credit_applications` - Solicitudes de crédito
- `documents` - Documentos de solicitudes

## 🧪 Testing

```bash
# Ejecutar tests (cuando estén implementados)
uv run pytest
```

## 🚧 Estado del Proyecto

**Fase actual:** MVP Core - Autenticación básica implementada

**Próximos pasos:**
- [ ] CRUD de empresas
- [ ] CRUD de solicitudes de crédito
- [ ] Sistema de aprobación/rechazo
- [ ] Upload de documentos

## 👥 Equipo

CreditosPYMES-NCG27

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.
