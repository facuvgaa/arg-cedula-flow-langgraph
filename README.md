# 🚗 Insurtech AI Agent: Automated Vehicle Card Flow & Policy Negotiation

<p align="center">
  <b>🇪🇸 Versión en Español</b> •
  <a href="README.en.md">🇬🇧 English Version</a>
</p>

[![CI Pipeline](https://github.com/facuvgaa/arg-cedula-flow-langgraph/actions/workflows/ci.yml/badge.svg)](https://github.com/facuvgaa/arg-cedula-flow-langgraph/actions/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/Docker-Containers-blue.svg?logo=docker)](https://www.docker.com/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-State_Machine-orange.svg)](https://www.langchain.com/langgraph)
[![AWS Bedrock](https://img.shields.io/badge/AWS_Bedrock-GenAI-232F3E.svg?logo=amazon-aws)](https://aws.amazon.com/bedrock/)
[![Java 17](https://img.shields.io/badge/Java-17-ED8B00.svg?logo=openjdk)](https://www.oracle.com/java/)
[![Spring Boot 3](https://img.shields.io/badge/Spring_Boot-3.3.4-6DB33F.svg?logo=springboot)](https://spring.io/projects/spring-boot)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react)](https://react.dev/)

Sistema integral de onboarding y cotización de seguros automotores con Inteligencia Artificial. Combina visión por computadora con LLMs para extraer datos de cédulas vehiculares argentinas, valida campos faltantes mediante máquinas de estados con **LangGraph**, negocia coberturas en tiempo real con **AWS Bedrock**, y consulta cotizaciones actuariales a través de un servidor **MCP (Model Context Protocol)** implementado en **Java / Spring Boot**.

Toda la solución está diseñada bajo **Arquitectura Hexagonal**, containerizada con **Docker**, automatizada con **GitHub Actions CI/CD** y publicada en **GitHub Container Registry (GHCR)**.

---

## 🏛️ 1. Arquitectura del Sistema

El sistema implementa una arquitectura políglota distribuida en microservicios comunicados por red interna Docker:

```mermaid
flowchart TB
    User([👤 Usuario / Asegurado]) -->|HTTP / SPA| Frontend["⚛️ Frontend (React 18 + Vite + Tailwind)<br/><i>Servido por Nginx Alpine (26MB)</i>"]
    
    subgraph Core_Backend ["🐍 Python 3.12 - Core Backend (FastAPI + LangGraph)"]
        API["FastAPI Gateway"]
        WF["LangGraph Workflow State Machine"]
        ExtractNode["Extracción OCR / Visión (Qwen VL / GPT)"]
        NegNode["Asesor de Seguros (AWS Bedrock Nova Lite)"]
        McpAdapter["MCP Client Adapter (SSE)"]
        
        API --> WF
        WF --> ExtractNode
        WF --> NegNode
        WF --> McpAdapter
    end

    Frontend -->|REST API :8001| API

    subgraph MCP_Pricing ["☕ Java 17 - Pricing Engine (Spring Boot 3.3.4)"]
        McpServer["Spring AI MCP Server (SSE :8080)"]
        PricingLogic["Reglas Actuariales & Coberturas"]
        McpServer --> PricingLogic
    end

    McpAdapter -->|SSE / Tool Call :8080| McpServer

    subgraph Storage_and_Data ["💾 Capa de Persistencia & Estado"]
        PG_Vehicles[("🐘 PostgreSQL: Cédulas & Vehículos (:5434)")]
        PG_Pricing[("🐘 PostgreSQL: Reglas de Precios (:5436)")]
        MinIO[("🪣 MinIO / S3: Almacén de Cédulas (:9000)")]
        Chroma[("🔍 ChromaDB: Base Vectorial RAG (:8000)")]
        Redis[("⚡ Redis: Cache & Sesiones (:6379)")]
        Langfuse[("🔭 Langfuse: Observabilidad LLM (:3100)")]
    end

    ExtractNode --> MinIO
    WF --> PG_Vehicles
    PricingLogic --> PG_Pricing
    NegNode --> Chroma
    WF --> Redis
    NegNode --> Langfuse
```

---

## 🚀 2. Pipeline de CI/CD & DevOps (GitHub Actions + GHCR)

El repositorio cuenta con un pipeline automatizado de **Integración y Entrega Continua (CI/CD)** que garantiza calidad de código y empaqueta artefactos inmutables en cada `git push` a `main`:

```mermaid
flowchart LR
    Push["git push main"] --> GHA["GitHub Actions Runner"]
    
    subgraph CI_Parallel ["1. Validación y Calidad en Paralelo (CI)"]
        PyTest["🐍 Python CI<br/>• Pytest (Unit Tests)<br/>• Cobertura de Adaptadores"]
        ViteBuild["⚛️ Frontend CI<br/>• TypeScript Typecheck<br/>• Vite Production Build"]
        JavaTest["☕ Java CI<br/>• Maven Clean Test<br/>• Compilación Spring Boot"]
    end

    GHA --> PyTest
    GHA --> ViteBuild
    GHA --> JavaTest

    subgraph Gated_Release ["2. Empaquetado & Registro Inmutable (CD)"]
        Buildx["🐳 Docker Buildx Multi-stage"]
        GHCR[("📦 GitHub Container Registry (GHCR)<br/>• backend:latest & SHA<br/>• frontend:latest & SHA<br/>• demo:latest & SHA")]
    end

    PyTest & ViteBuild & JavaTest -->|needs: todos OK| Buildx
    Buildx --> GHCR
```

### Características del Pipeline DevOps:
1. **Compilación Multi-Stage**: 
   - El Frontend se compila con Node 20 y se transfiere a un runtime limpio de Nginx Alpine, pesando solo **26.5 MB**.
   - El Backend corre con un usuario no root (`appuser`) para máxima seguridad en entornos corporativos.
   - Java se compila con Maven y se empaqueta en una imagen liviana Eclipse Temurin JRE 17.
2. **Versionado Semántico & SHA**: Cada imagen se etiqueta con `:latest` y con el hash del commit (`:${{ github.sha }}`) para permitir **Rollbacks instantáneos** en producción.
3. **Cero almacenamiento de secretos en imágenes**: Los tokens y contraseñas se inyectan en tiempo de ejecución vía variables de entorno.

---

## 🛠️ 3. Pila Tecnológica

| Componente | Tecnologías | Propósito |
| :--- | :--- | :--- |
| **Backend** | Python 3.12, FastAPI, LangGraph, SQLAlchemy, AsyncPG | API REST, orquestación de estados y agentes IA |
| **Modelos LLM** | AWS Bedrock (Nova Lite), OpenAI Mantle, Qwen-VL | Visión computacional, extracción OCR y negociación |
| **MCP Pricing** | Java 17, Spring Boot 3.3.4, Spring AI, HikariCP | Servidor MCP por Server-Sent Events (SSE) |
| **Frontend** | React 18, Vite, TypeScript, Tailwind CSS, Lucide | UI interactiva con streaming typewriter effect |
| **Bases de Datos** | PostgreSQL 15/16, ChromaDB, Redis 7 | Datos estructurados, embeddings RAG y caché |
| **Almacenamiento** | MinIO (compatible con AWS S3) | Almacenamiento seguro de imágenes de cédulas |
| **Observabilidad** | Langfuse 2 | Trazabilidad de latencia, costo y tokens de LLMs |
| **DevOps** | Docker, Docker Compose, GitHub Actions, GHCR | Containerización y pipelines automatizados |

---

## 📦 4. Despliegue Rápido Local (Docker Compose)

El stack completo de 10 contenedores se levanta con un único comando:

### Prerrequisitos
- Docker Engine $\ge$ 24.0 y Docker Compose v2.

### Pasos

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/facuvgaa/arg-cedula-flow-langgraph.git
   cd arg-cedula-flow-langgraph
   ```

2. **Configurar variables de entorno:**
   ```bash
   cp .env.production.example prueba/.env
   # Completar con tus tokens de AWS Bedrock / OpenAI
   ```

3. **Compilar y levantar todos los servicios:**
   ```bash
   docker compose up -d --build
   ```

4. **Acceder a los servicios:**
   - 🌐 **Frontend (Web App)**: [http://localhost:5173](http://localhost:5173)
   - 📖 **Swagger / OpenAPI (FastAPI)**: [http://localhost:8001/docs](http://localhost:8001/docs)
   - ☕ **MCP Pricing Server (Java SSE)**: [http://localhost:8080](http://localhost:8080)
   - 🪣 **MinIO Console**: [http://localhost:9001](http://localhost:9001) *(User: `minioadmin` / Pass: `minioadmin`)*
   - 🔭 **Langfuse Dashboard**: [http://localhost:3100](http://localhost:3100)

---

## 🌐 5. Despliegue en Producción & Escalabilidad

Para entornos de producción reales (AWS EC2 / VPS / ECS), se provee [`docker-compose.prod.yml`](./docker-compose.prod.yml). Este archivo **no compila código en el servidor**: consume directamente las imágenes optimizadas de **GitHub Container Registry**.

```bash
# En el servidor de producción:
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### Arquitectura de Autoescalado (Cloud Ready)

```
                            [ Tráfico Masivo (9.000+ RPS) ]
                                          │
                                          ▼
                         [ AWS Application Load Balancer ]
                                          │
           ┌──────────────────────────────┼──────────────────────────────┐
           ▼                              ▼                              ▼
  [ ECS Task: Backend 1 ]        [ ECS Task: Backend 2 ]        [ ECS Task: Backend N ]
           │                              │                              │
           └──────────────────────────────┼──────────────────────────────┘
                                          ▼
                      [ Amazon CloudWatch Target Tracking ]
                        (CPU > 60% ➔ Dispara Auto-Scaling)
```

- **Stateless Core**: La aplicación no almacena estado local. Cualquier contenedor puede responder cualquier petición.
- **Connection Pooling**: PostgreSQL protegido mediante poolers asíncronos para evitar saturación de conexiones concurrentes.
- **Caché Inteligente**: Consultas frecuentes de pólizas cacheadas en Redis en memoria.

---

## 🧪 6. Testing Automatizado

Para correr los tests en tu entorno de desarrollo:

```bash
# Tests Unitarios de Python
cd prueba
pytest tests/unit/ -v

# Tests de Integración en vivo con AWS Bedrock
pytest tests/integration/test_bedrock_live.py -s -v

# Tests y compilación de Java Spring Boot
cd ../demo
mvn clean test
```

---

## 📄 Licencia

Este proyecto fue desarrollado con fines demostrativos y de arquitectura enterprise bajo licencia MIT.

