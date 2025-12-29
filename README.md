# Knowledge Graph Visualizer (IA + Web)

Aplicación web que transforma texto no estructurado (o artículos completos vía URL) en un **grafo de conocimiento interactivo**, utilizando modelos de lenguaje y visualización basada en fuerzas físicas.

El objetivo del proyecto es demostrar cómo **LLMs pueden convertir información compleja en estructuras relacionales explorables**, combinando backend de IA y frontend visual moderno.

---

## Qué hace

- Pega un texto o una URL de un artículo
- Extrae entidades clave (personas, organizaciones, conceptos)
- Detecta relaciones entre ellas
- Renderiza un **grafo interactivo** de nodos y enlaces
- Permite elegir proveedor de IA:
  - **OpenAI** (mayor calidad)
  - **Ollama** (local y sin coste)

---

## Por qué este proyecto es interesante

- Convierte texto libre en **datos estructurados**
- Usa **LLMs de forma dirigida**, no solo para “resumir”
- Aplica normalización y control de ruido
- Visualización dinámica basada en simulación de fuerzas
- Arquitectura limpia, desacoplada y configurable
- Preparado para demo, portfolio y extensión futura

---

## Arquitectura

```

Frontend (React + Force Graph)
↓
FastAPI (API REST)
↓
Proveedor IA (OpenAI / Ollama)

````

---

## Stack técnico

### Backend
- Python 3.11+
- FastAPI + Uvicorn
- Pydantic
- httpx
- BeautifulSoup + readability-lxml
- OpenAI API / Ollama
- Control de presupuesto mensual (OpenAI)

### Frontend
- React + Vite
- react-force-graph-2d
- CSS custom (dark UI)

### DevOps
- Docker
- Docker Compose

---

## Ejecución con Docker (recomendado)

### Requisitos
- Docker Desktop
- (Opcional) Ollama instalado localmente

### Pasos

```bash
docker compose up --build
````

* Frontend: [http://localhost:8080](http://localhost:8080)
* Backend (docs): [http://localhost:8000/docs](http://localhost:8000/docs)

Por defecto:

* El backend puede usar **Ollama** (gratis) o **OpenAI** (si se configura la API key).

---

## Variables de entorno

Las claves **no se suben al repositorio**.

Ejemplo de `.env.docker` (solo para uso local):

```env
OPENAI_API_KEY=sk-xxxx
OPENAI_MODEL=gpt-4o-mini
OPENAI_ADMIN_KEY=sk-admin-xxxx
OPENAI_PROJECT_ID=proj-xxxx
```

El archivo `.env.docker` está ignorado por Git.

---

## Proveedores de IA

### OpenAI

* Mayor calidad de extracción
* Incluye control de gasto mensual
* Ideal para resultados más precisos

### Ollama

* Ejecución local
* Sin coste
* Ideal para demos o pruebas offline

El proveedor se puede cambiar directamente desde la interfaz.

---

## Posibles mejoras futuras

* Persistencia en base de datos de grafos (Neo4j)
* Colores y tamaños por tipo de entidad
* Panel de detalle por nodo
* Exportación del grafo
* Autodetección de hubs principales
* Autenticación multiusuario

---

## Demo

<p align="center">
  <img src="assets/demo.gif" width="700" />
</p>

---

## Autor

Proyecto desarrollado como ejercicio de integración entre **IA, backend y visualización web**, enfocado a demostrar capacidad de abstracción, arquitectura y experiencia de usuario en proyectos modernos.

## Estado del proyecto

Proyecto funcional, orientado a demostración técnica y portfolio.
Diseñado para ser extensible (nuevos proveedores de IA, layouts y análisis).
