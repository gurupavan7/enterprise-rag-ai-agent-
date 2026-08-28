# 🚀 Enterprise RAG AI Agent

A production-ready **Retrieval-Augmented Generation (RAG) document intelligence system** that allows users to securely upload PDF documents and ask natural-language questions grounded in their own knowledge base.

The application combines **FastAPI, React, FAISS, Sentence Transformers, Cross-Encoder reranking, Google Gemini, JWT authentication, and per-user document isolation** to provide accurate, context-aware answers from uploaded documents.

---

## 🌐 Live Application

**Frontend:**  
https://enterprise-rag-ai-agent-three.vercel.app

**Backend API:**  
https://enterprise-rag-ai-agent-production.up.railway.app

---

## ✨ Features

- 🔐 User registration and login with JWT authentication
- 👤 Private knowledge base for each authenticated user
- 📄 PDF document upload and processing
- ✂️ Intelligent document chunking
- 🧠 Sentence Transformer embeddings
- 🔎 FAISS vector similarity search
- 🔀 Hybrid document retrieval
- 🎯 Cross-Encoder reranking
- 🤖 Google Gemini-powered answer generation
- 📚 Source-aware responses
- 🗑️ Document deletion and knowledge-base rebuilding
- 📊 Document and chunk statistics
- 💬 Interactive RAG chat interface
- 🌐 REST API built with FastAPI
- ⚛️ Responsive React/Vite frontend
- 🐳 Dockerized frontend and backend
- ☁️ Production deployment using Railway and Vercel

---

## 🧠 What is RAG?

Retrieval-Augmented Generation (RAG) combines information retrieval with a Large Language Model.

Instead of asking an LLM to answer purely from its pretrained knowledge, this application first retrieves relevant information from the user's uploaded documents and then provides that context to the language model.

This helps produce answers that are more relevant and grounded in the user's own documents.

---

## 🏗️ System Architecture

```text
                     ┌─────────────────────┐
                     │        User         │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │   React / Vite UI   │
                     │      Vercel         │
                     └──────────┬──────────┘
                                │ HTTPS
                                ▼
                     ┌─────────────────────┐
                     │      FastAPI        │
                     │      Railway        │
                     └──────────┬──────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
       ┌────────────┐    ┌─────────────┐   ┌──────────────┐
       │ JWT Auth   │    │ PDF Pipeline│   │ User Storage │
       └────────────┘    └──────┬──────┘   └──────────────┘
                                │
                                ▼
                         ┌─────────────┐
                         │  Chunking   │
                         └──────┬──────┘
                                │
                                ▼
                         ┌─────────────┐
                         │ Embeddings  │
                         └──────┬──────┘
                                │
                                ▼
                         ┌─────────────┐
                         │    FAISS    │
                         │Vector Index │
                         └──────┬──────┘
                                │
                                ▼
                         ┌─────────────┐
                         │ Retrieval + │
                         │  Reranking  │
                         └──────┬──────┘
                                │
                                ▼
                         ┌─────────────┐
                         │   Gemini    │
                         │     LLM     │
                         └──────┬──────┘
                                │
                                ▼
                         Grounded Answer
```

---

## 🔄 RAG Pipeline

```text
PDF Upload
    ↓
PDF Text Extraction
    ↓
Document Chunking
    ↓
Embedding Generation
    ↓
FAISS Vector Index
    ↓
User Question
    ↓
Query Embedding
    ↓
Relevant Chunk Retrieval
    ↓
Hybrid Retrieval
    ↓
Cross-Encoder Reranking
    ↓
Context Construction
    ↓
Google Gemini
    ↓
Grounded Answer + Sources
```

---

## 🔐 User Data Isolation

Each authenticated user receives an independent document knowledge base.

```text
data/
└── users/
    ├── user_1/
    │   ├── documents/
    │   ├── FAISS index
    │   └── metadata
    │
    └── user_2/
        ├── documents/
        ├── FAISS index
        └── metadata
```

This prevents one user's documents from being retrieved by another user's RAG queries.

---

## 🛠️ Technology Stack

### Frontend

- React
- Vite
- JavaScript
- CSS
- Fetch API

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic

### AI / Machine Learning

- Google Gemini
- Sentence Transformers
- Cross-Encoder reranking
- FAISS
- Semantic Search
- Hybrid Retrieval
- Retrieval-Augmented Generation

### Authentication

- JWT
- PBKDF2 password hashing
- SQLite
- SQLAlchemy

### DevOps & Deployment

- Docker
- Docker Compose
- Git
- GitHub
- Railway
- Vercel
- Nginx

---

## 📁 Project Structure

```text
enterprise-rag-ai-agent/
│
├── app/
│   ├── api.py
│   ├── auth.py
│   ├── utils.py
│   └── main.py
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── ...
│   ├── package.json
│   └── Dockerfile
│
├── data/
│   └── users/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── .gitignore
```

---

## ⚙️ Local Installation

### 1. Clone the repository

```bash
git clone https://github.com/gurupavan7/enterprise-rag-ai-agent-.git
cd enterprise-rag-ai-agent-
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file.

```env
GEMINI_API_KEY=your_gemini_api_key
JWT_SECRET=your_secure_jwt_secret
```

Never commit real API keys or secrets to GitHub.

### 5. Start the backend

```bash
uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
```

Backend:

```text
http://localhost:8000
```

FastAPI documentation:

```text
http://localhost:8000/docs
```

### 6. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

## 🐳 Running with Docker Compose

Build and start the application:

```bash
docker compose up --build
```

Stop the application:

```bash
docker compose down
```

---

## 🔌 API Overview

The backend provides endpoints for:

| Endpoint | Purpose |
|---|---|
| `POST /register` | Create a user account |
| `POST /login` | Authenticate and receive JWT |
| `POST /upload` | Upload and index a PDF |
| `GET /documents` | Retrieve user's documents |
| `DELETE /documents/{filename}` | Delete a document |
| RAG query endpoint | Ask questions about indexed documents |
| `GET /` | Backend health/status |

Authentication-protected endpoints use:

```text
Authorization: Bearer <JWT_TOKEN>
```

---

## 🔍 Retrieval Strategy

The retrieval pipeline combines multiple stages:

1. **Semantic retrieval** identifies chunks that are meaningfully related to the user's question.
2. **FAISS** performs efficient vector similarity search.
3. **Hybrid retrieval** improves candidate selection.
4. **Cross-Encoder reranking** evaluates retrieved chunks more precisely.
5. The highest-quality context is sent to **Google Gemini**.
6. Gemini generates the final response using the retrieved document context.

---

## 🔒 Security

The application includes:

- Password hashing
- JWT-based authentication
- Protected API endpoints
- Per-user document directories
- Per-user vector indexes
- CORS configuration
- Environment-variable based secret management
- User-specific document retrieval

---

## ☁️ Production Deployment

The application uses a separated frontend/backend production architecture.

```text
GitHub
   │
   ├──────────────► Vercel
   │                 │
   │              React UI
   │
   └──────────────► Railway
                     │
                  FastAPI
                     │
                RAG Pipeline
```

**Frontend:** Vercel  
**Backend:** Railway

---

## 🎯 Use Cases

This architecture can be adapted for:

- Resume intelligence
- Enterprise knowledge assistants
- Internal company documentation
- Research-paper assistants
- Policy and compliance documents
- Technical manuals
- Educational material
- Knowledge-management systems

---

## 🚧 Future Improvements

Potential improvements include:

- Incremental FAISS indexing
- Asynchronous document processing
- Streaming LLM responses
- Conversation history
- PostgreSQL
- Object/cloud storage
- Advanced document metadata filtering
- OCR support for scanned PDFs
- More document formats
- Administrative dashboard
- Automated testing and CI/CD

---

## 👨‍💻 Author

**Guru Pavan**

AI/ML Engineer | Python Developer | Full Stack Developer

GitHub: https://github.com/gurupavan7

---

## ⭐ Support

If you find this project useful, consider giving the repository a ⭐.