# API Créditos PyMEs

API REST para gestión de solicitudes de crédito a PyMEs, desarrollada con FastAPI y Supabase.

## 📋 Requisitos

- Python 3.13+
- UV (gestor de paquetes y entorno virtual)
- Cuenta de Supabase (base de datos PostgreSQL y autenticación)
- Cuenta de HelloSign/Dropbox Sign (para firma electrónica de documentos)

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
- `SUPABASE_URL`: URL de tu proyecto Supabase (ej: `https://xxxxx.supabase.co`)
- `SUPABASE_SECRET_KEY`: La **service_role key** de tu proyecto Supabase (Settings → API)
- `HELLOSIGN_API_KEY` y `HELLOSIGN_CLIENT_ID`: Obtenerlos en [HelloSign API Settings](https://app.hellosign.com/home/myAccount#api)
- La API utiliza Supabase Auth para autenticación JWT y Supabase Storage para almacenamiento de documentos

## 🗄️ Configuración de la Base de Datos

### Paso 1: Inicializar el esquema

1. Abre tu proyecto en **Supabase Dashboard**
2. Ve a **SQL Editor** (icono de base de datos en el menú lateral)
3. Abre el archivo `init_db.sql` de este repositorio
4. Copia todo su contenido y pégalo en el editor SQL
5. Haz clic en **Run** para ejecutar el script

El script creará automáticamente:
- ✅ Tipos ENUM personalizados
- ✅ Tablas con constraints e índices
- ✅ Funciones PL/pgSQL
- ✅ Triggers para automatización

### Paso 2: Configurar Custom Access Token Hook

Este paso es **crucial** para que el sistema de roles funcione correctamente.

1. Ve a **Authentication → Hooks** en Supabase Dashboard
2. Selecciona **Custom Access Token Hook**
3. En el campo **Hook Name**, ingresa: `custom_access_token_hook`
4. En **Schema**, selecciona: `public`
5. Haz clic en **Enable Hook**

Esto inyectará automáticamente el `user_role` en el JWT de cada usuario.

### Paso 3: Habilitar Row Level Security (RLS)

Por defecto, las tablas no tienen RLS activado. Para evitar accesos no autorizados, habilítalo:

1. Ve a **Authentication → Policies** en Supabase Dashboard
2. Para cada tabla (`profiles`, `companies`, `credit_applications`, `documents`):
   - Haz clic en **Enable RLS**

### Paso 4: Migrar claves de API

Este proyecto utiliza las nuevas API Keys de Supabase, por lo cual es necesario ir a la configuración del proyecto en Supabase Dashboard, deshabilitar las claves legacy  (anon y service_role) y habilitar las nuevas API Keys (publishable y secret).

### Paso 5: Migrar JWT Secret a JWT Signing Key

Este proyecto utiliza JWKS para validar los tokens JWT emitidos por Supabase Auth. Para configurar esto necesitas migrar la clave secreta JWT a una clave de firma asimétrica desde la configuración del proyecto en Supabase Dashboard.

## 🏃 Ejecución

Ejecutar el servidor de desarrollo:

```bash
uv run fastapi dev app/main.py
```

La API estará disponible en: `http://localhost:8000`

## 📚 Documentación de la API

**Para la especificación completa de la API**, incluyendo todos los endpoints, esquemas de datos, flujos de negocio y ejemplos, consulta: **[SPECIFICATION.md](./SPECIFICATION.md)**

Una vez iniciado el servidor, también puedes acceder a la documentación interactiva:

- **Swagger UI (interactiva)**: http://localhost:8000/docs
- **ReDoc (documentación)**: http://localhost:8000/redoc

## 🛠️ Estructura del Proyecto

```
📂api-creditos-pymes/
├── 📂app/
│   ├── 📂core/                # Enums y errores de dominio
│   ├── 📂dependencies/        # Dependencias (auth, db, services)
│   ├── 📂models/              # Modelos SQLModel (entidades de BD)
│   ├── 📂schemas/             # Schemas Pydantic (request/response)
│   ├── 📂repositories/        # Acceso a datos (capa de persistencia)
│   ├── 📂routers/             # Endpoints por módulo
│   ├── 📂services/            # Lógica de negocio
│   ├── 🐍main.py              # Punto de entrada de la aplicación
│   ├── 🐍config.py            # Configuración y variables de entorno
│   ├── 🐍bootstrap.py         # Lifespan (DB y JWKS)
│   └── 🐍exception_handlers.py# Mapeo de errores de dominio a HTTP
├── 🔑.env.example             # Plantilla de variables de entorno
├── 📜init_db.sql              # Script de inicialización de BD
├── ⚙️pyproject.toml           # Configuración del proyecto y dependencias
├── 📑README.md                # Este archivo
└── 📄SPECIFICATION.md         # Especificación técnica completa de la API
```

## 🔐 Autenticación

La API utiliza **Supabase Auth** para autenticación mediante tokens JWT:

- Todos los endpoints protegidos requieren el header: `Authorization: Bearer {JWT_TOKEN}`
- El servidor valida automáticamente los tokens usando JWKS (JSON Web Key Set)
- Validaciones: `issuer` = `${SUPABASE_URL}/auth/v1`, `audience` = `authenticated`, algoritmo ES256
- El rol del usuario (`user_role`) se inyecta automáticamente en el JWT mediante custom claims

**Ejemplo de llamada autenticada:**

```bash
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1..." \
  http://localhost:8000/api/v1/profiles/me
```

## 🧰 Servicios Externos

### Supabase

La API utiliza los siguientes servicios de Supabase:

- **Supabase Auth**: Autenticación de usuarios con JWT
- **Supabase Database**: PostgreSQL con políticas RLS (Row Level Security)
- **Supabase Storage**: Almacenamiento de documentos (estados financieros, identificaciones, etc.)

### HelloSign (Dropbox Sign)

Para la firma electrónica de documentos se integra con HelloSign:

- Los documentos que requieren firma son enviados automáticamente a HelloSign
- Los usuarios reciben notificaciones por email para firmar
- El sistema recibe webhooks cuando se completa la firma

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.
