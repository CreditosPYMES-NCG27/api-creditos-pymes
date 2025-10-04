# API Créditos PYMES

API REST para el proyecto CreditosPYMES-NCG27, desarrollado con FastAPI.

## 📋 Requisitos

- Python 3.13+
- FastAPI
- UV (gestor de paquetes)

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

3. Crear archivo `.env` con las variables de entorno necesarias (opcional)

## 🏃 Ejecución

Ejecutar el servidor de desarrollo:

```bash
uv run fastapi dev app/main.py
```

La API estará disponible en: `http://localhost:8000`

## 📚 Documentación

Una vez iniciado el servidor, accede a:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🛠️ Estructura del Proyecto

```
api-creditos-pymes/
├── app/
│   └── main.py          # Punto de entrada de la aplicación
├── .env                 # Variables de entorno (no incluir en git)
├── .gitignore
├── pyproject.toml       # Configuración del proyecto
├── uv.lock
└── README.md
```

## 📝 Endpoints Principales

| Método | Endpoint | Descripción      |
| ------ | -------- | ---------------- |
| GET    | `/`      | Estado de la API |

## 📄 Licencia

Este proyecto está bajo la licencia especificada en el archivo `LICENSE`.

## 👥 Autores

- CreditosPYMES-NCG27
