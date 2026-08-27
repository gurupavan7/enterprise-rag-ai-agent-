import os

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Depends,
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://enterprise-rag-ai-agent-three.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pydantic import BaseModel

from app.auth import (
    SessionLocal,
    User,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.utils import (
    load_all_pdfs,
    chunk_pdf_pages,
    create_pdf_embeddings,
    create_faiss_index,
    save_faiss_index,
    load_faiss_index,
    save_metadata,
    load_metadata,
    hybrid_search,
    rerank_results,
    generate_rag_answer,
)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Enterprise RAG AI Agent API",
    version="1.0.0",
    description="Enterprise document question-answering API",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://enterprise-rag-ai-agent-three.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PATHS
# ============================================================

DOCUMENTS_FOLDER = "data/documents"

FAISS_FILE = "data/multi_document.index"

METADATA_FILE = "data/multi_document_metadata.json"


# ============================================================
# REQUEST MODELS
# ============================================================

class QuestionRequest(BaseModel):
    question: str


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ============================================================
# JWT SECURITY
# ============================================================

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    user_id = decode_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )

    database = SessionLocal()

    try:
        user = (
            database
            .query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found.",
            )

        return {
            "id": user.id,
            "email": user.email,
        }

    finally:
        database.close()


# ============================================================
# LOAD KNOWLEDGE BASE
# ============================================================

def load_knowledge_base():

    if (
        os.path.exists(FAISS_FILE)
        and os.path.exists(METADATA_FILE)
    ):

        print("Loading existing FAISS index...")

        loaded_index = load_faiss_index(
            FAISS_FILE
        )

        loaded_chunks = load_metadata(
            METADATA_FILE
        )

        return loaded_index, loaded_chunks


    print("Creating knowledge base...")

    pages = load_all_pdfs(
        DOCUMENTS_FOLDER
    )

    if not pages:

        raise RuntimeError(
            "No PDF documents found."
        )


    loaded_chunks = chunk_pdf_pages(
        pages,
        chunk_size=50,
        overlap=10,
    )


    embeddings = create_pdf_embeddings(
        loaded_chunks
    )


    loaded_index = create_faiss_index(
        embeddings
    )


    save_faiss_index(
        loaded_index,
        FAISS_FILE
    )


    save_metadata(
        loaded_chunks,
        METADATA_FILE
    )


    print(
        "Knowledge base created."
    )


    return loaded_index, loaded_chunks


# ============================================================
# REBUILD KNOWLEDGE BASE
# ============================================================

def rebuild_knowledge_base():

    print(
        "Rebuilding knowledge base..."
    )


    pages = load_all_pdfs(
        DOCUMENTS_FOLDER
    )


    if not pages:

        raise RuntimeError(
            "No readable PDF documents found."
        )


    new_chunks = chunk_pdf_pages(
        pages,
        chunk_size=50,
        overlap=10,
    )


    if not new_chunks:

        raise RuntimeError(
            "No text could be extracted."
        )


    embeddings = create_pdf_embeddings(
        new_chunks
    )


    new_index = create_faiss_index(
        embeddings
    )


    save_faiss_index(
        new_index,
        FAISS_FILE
    )


    save_metadata(
        new_chunks,
        METADATA_FILE
    )


    print(
        "Knowledge base rebuilt successfully."
    )


    return new_index, new_chunks


# ============================================================
# INITIALIZE KNOWLEDGE BASE
# ============================================================

index, chunks = load_knowledge_base()


# ============================================================
# HEALTH
# ============================================================

@app.get("/")
def root():

    document_names = {
        chunk["source"]
        for chunk in chunks
    }

    return {
        "status": "running",
        "application": "Enterprise RAG AI Agent",
        "documents": len(document_names),
        "chunks": len(chunks),
        "vectors_stored": index.ntotal,
        "vectors_stored": index.ntotal if index is not None else 0,
    }

# ============================================================
# LIST CURRENT USER'S DOCUMENTS
# ============================================================

@app.get("/documents")
def list_documents(
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]

    user_index, user_chunks = (
        load_user_knowledge_base(user_id)
    )

    documents = {}

    for chunk in user_chunks:
        source = chunk.get("source")

        if not source:
            continue

        if source not in documents:
            documents[source] = {
                "filename": source,
                "pages": set(),
                "chunks": 0,
            }

        documents[source]["chunks"] += 1

        page = chunk.get("page")

        if page is not None:
            documents[source]["pages"].add(page)

    document_list = []

    for document in documents.values():
        document_list.append({
            "filename": document["filename"],
            "pages": len(document["pages"]),
            "chunks": document["chunks"],
        })

    document_list.sort(
        key=lambda item:
            item["filename"].lower()
    )

    return {
        "total_documents": len(document_list),
        "total_chunks": len(user_chunks),
        "vectors_stored": (
            user_index.ntotal
            if user_index is not None
            else 0
        ),
        "documents": document_list,
    }

# ============================================================
# DELETE CURRENT USER'S DOCUMENT
# ============================================================

@app.delete("/documents/{filename}")
def delete_document(
    filename: str,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]

    paths = get_user_paths(user_id)

    documents_folder = paths[
        "documents_folder"
    ]

    safe_filename = os.path.basename(
        filename
    )

    file_path = os.path.join(
        documents_folder,
        safe_filename,
    )

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    try:
        os.remove(file_path)

        user_index, user_chunks = (
            rebuild_user_knowledge_base(
                user_id
            )
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to delete document: "
                f"{error}"
            ),
        )

    document_names = {
        chunk["source"]
        for chunk in user_chunks
    }

    return {
        "message": (
            "Document deleted successfully."
        ),
        "filename": safe_filename,
        "total_documents": len(
            document_names
        ),
        "total_chunks": len(
            user_chunks
        ),
        "vectors_stored": (
            user_index.ntotal
            if user_index is not None
            else 0
        ),
    }

# ============================================================
# REGISTER
# ============================================================

@app.post("/register")
def register_user(
    request: RegisterRequest
):

    database = SessionLocal()

    try:

        email = (
            request.email
            .strip()
            .lower()
        )

        password = request.password


        if not email:

            raise HTTPException(
                status_code=400,
                detail="Email is required.",
            )


        if len(password) < 6:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Password must contain "
                    "at least 6 characters."
                ),
            )


        existing_user = (
            database
            .query(User)
            .filter(
                User.email == email
            )
            .first()
        )


        if existing_user:

            raise HTTPException(
                status_code=409,
                detail=(
                    "A user with this email "
                    "already exists."
                ),
            )


        new_user = User(
            email=email,
            password_hash=hash_password(
                password
            ),
        )


        database.add(
            new_user
        )

        database.commit()

        database.refresh(
            new_user
        )


        access_token = create_access_token(
            new_user.id
        )


        return {
            "message":
                "User registered successfully.",

            "access_token":
                access_token,

            "token_type":
                "bearer",

            "user": {
                "id":
                    new_user.id,

                "email":
                    new_user.email,
            },
        }


    finally:

        database.close()


# ============================================================
# LOGIN
# ============================================================

@app.post("/login")
def login_user(
    request: LoginRequest
):

    database = SessionLocal()


    try:

        email = (
            request.email
            .strip()
            .lower()
        )


        user = (
            database
            .query(User)
            .filter(
                User.email == email
            )
            .first()
        )


        if not user:

            raise HTTPException(
                status_code=401,
                detail=(
                    "Invalid email "
                    "or password."
                ),
            )


        if not verify_password(
            request.password,
            user.password_hash,
        ):

            raise HTTPException(
                status_code=401,
                detail=(
                    "Invalid email "
                    "or password."
                ),
            )


        access_token = create_access_token(
            user.id
        )


        return {
            "message":
                "Login successful.",

            "access_token":
                access_token,

            "token_type":
                "bearer",

            "user": {
                "id":
                    user.id,

                "email":
                    user.email,
            },
        }


    finally:

        database.close()

# ============================================================
# ASK RAG — PRIVATE PER USER
# ============================================================

@app.post("/ask")
def ask_question(
    request: QuestionRequest,
    current_user: dict = Depends(get_current_user),
):
    query = request.question.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    # ========================================================
    # LOAD ONLY CURRENT USER'S KNOWLEDGE BASE
    # ========================================================

    user_id = current_user["id"]

    user_index, user_chunks = (
        load_user_knowledge_base(user_id)
    )

    # ========================================================
    # NO PRIVATE DOCUMENTS
    # ========================================================

    if user_index is None or not user_chunks:
        return {
            "question": query,
            "answer": (
                "No documents are currently indexed "
                "for this account."
            ),
            "sources": [],
        }

    # ========================================================
    # HYBRID RETRIEVAL
    # ========================================================

    results = hybrid_search(
        query,
        user_chunks,
        user_index,
        top_k=10,
        semantic_weight=0.7,
        keyword_weight=0.3,
        threshold=0.20,
    )

    # ========================================================
    # RERANKING
    # ========================================================

    results = rerank_results(
        query,
        results,
        top_k=3,
    )

    if not results:
        return {
            "question": query,
            "answer": (
                "I could not find this information "
                "in your indexed documents."
            ),
            "sources": [],
        }

    # ========================================================
    # GENERATE ANSWER
    # ========================================================

    try:
        answer = generate_rag_answer(
            query,
            results,
            [],
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"AI generation failed: {error}",
        )

    # ========================================================
    # SOURCES
    # ========================================================

    sources = []

    for result in results:
        sources.append({
            "source": result["source"],
            "page": result["page"],
            "hybrid_score": round(
                result["score"],
                4,
            ),
            "rerank_score": round(
                result["rerank_score"],
                4,
            ),
        })

    return {
        "question": query,
        "answer": answer,
        "sources": sources,
    }
# ============================================================
# UPLOAD PDF
# ============================================================

# ============================================================
# UPLOAD PDF — PRIVATE PER USER
# ============================================================

@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    # ========================================================
    # VALIDATE FILENAME
    # ========================================================

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Missing filename.",
        )

    safe_filename = os.path.basename(
        file.filename
    )

    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed.",
        )

    # ========================================================
    # CURRENT USER
    # ========================================================

    user_id = current_user["id"]

    paths = get_user_paths(
        user_id
    )

    documents_folder = paths[
        "documents_folder"
    ]

    file_path = os.path.join(
        documents_folder,
        safe_filename,
    )

    # ========================================================
    # PREVENT DUPLICATE PDF
    # ========================================================

    if os.path.exists(file_path):
        raise HTTPException(
            status_code=409,
            detail=(
                "A document with this filename "
                "already exists."
            ),
        )

    try:
        # ====================================================
        # READ PDF
        # ====================================================

        contents = await file.read()

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="Uploaded PDF is empty.",
            )

        if not contents.startswith(b"%PDF"):
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is not a valid PDF.",
            )

        # ====================================================
        # SAVE INTO PRIVATE USER FOLDER
        # ====================================================

        with open(
            file_path,
            "wb",
        ) as output_file:
            output_file.write(
                contents
            )

        print(
            f"User {user_id} PDF saved: "
            f"{file_path}"
        )

        # ====================================================
        # REBUILD ONLY THIS USER'S INDEX
        # ====================================================

        user_index, user_chunks = (
            rebuild_user_knowledge_base(
                user_id
            )
        )

    except HTTPException:
        raise

    except Exception as error:

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to process document: "
                f"{error}"
            ),
        )

    finally:
        await file.close()

    # ========================================================
    # PRIVATE DOCUMENT COUNT
    # ========================================================

    document_names = {
        chunk["source"]
        for chunk in user_chunks
    }

    return {
        "message": (
            "Document uploaded and indexed successfully."
        ),
        "filename": safe_filename,
        "total_documents": len(
            document_names
        ),
        "total_chunks": len(
            user_chunks
        ),
        "vectors_stored": (
            user_index.ntotal
            if user_index is not None
            else 0
        ),
    }

# ============================================================
# PER-USER STORAGE PATHS
# ============================================================

def get_user_paths(user_id):
    user_folder = os.path.join(
        "data",
        "users",
        str(user_id),
    )

    documents_folder = os.path.join(
        user_folder,
        "documents",
    )

    faiss_file = os.path.join(
        user_folder,
        "documents.index",
    )

    metadata_file = os.path.join(
        user_folder,
        "metadata.json",
    )

    os.makedirs(
        documents_folder,
        exist_ok=True,
    )

    return {
        "user_folder": user_folder,
        "documents_folder": documents_folder,
        "faiss_file": faiss_file,
        "metadata_file": metadata_file,
    }

# ============================================================
# LOAD USER KNOWLEDGE BASE
# ============================================================

def load_user_knowledge_base(user_id):
    paths = get_user_paths(user_id)

    faiss_file = paths["faiss_file"]
    metadata_file = paths["metadata_file"]

    if (
        os.path.exists(faiss_file)
        and os.path.exists(metadata_file)
    ):
        user_index = load_faiss_index(
            faiss_file
        )

        user_chunks = load_metadata(
            metadata_file
        )

        if user_index.ntotal != len(user_chunks):
            raise RuntimeError(
                "User FAISS index and metadata do not match."
            )

        return user_index, user_chunks

    return None, []


# ============================================================
# REBUILD USER KNOWLEDGE BASE
# ============================================================

def rebuild_user_knowledge_base(user_id):
    paths = get_user_paths(user_id)

    documents_folder = paths[
        "documents_folder"
    ]

    faiss_file = paths[
        "faiss_file"
    ]

    metadata_file = paths[
        "metadata_file"
    ]

    pages = load_all_pdfs(
        documents_folder
    )

    # User has no PDFs
    if not pages:
        if os.path.exists(faiss_file):
            os.remove(faiss_file)

        if os.path.exists(metadata_file):
            os.remove(metadata_file)

        return None, []

    user_chunks = chunk_pdf_pages(
        pages,
        chunk_size=50,
        overlap=10,
    )

    embeddings = create_pdf_embeddings(
        user_chunks
    )

    user_index = create_faiss_index(
        embeddings
    )

    save_faiss_index(
        user_index,
        faiss_file
    )

    save_metadata(
        user_chunks,
        metadata_file
    )

    return user_index, user_chunks