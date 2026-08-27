import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";

function App() {
  const [token, setToken] = useState(
    localStorage.getItem("rag_token") || ""
  );

  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("rag_user");

    return savedUser
      ? JSON.parse(savedUser)
      : null;
  });

  const [authMode, setAuthMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text:
        "Hello! I'm your Enterprise RAG AI Assistant. " +
        "Upload a PDF or ask me a question about your documents.",
      sources: [],
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [selectedFile, setSelectedFile] =
    useState(null);

  const [uploading, setUploading] =
    useState(false);

  const [uploadStatus, setUploadStatus] =
    useState("");

  const [documentCount, setDocumentCount] =
    useState(0);

  const [chunkCount, setChunkCount] =
    useState(0);

  const [documents, setDocuments] =
  useState([]);

  const messagesEndRef = useRef(null);


  // =========================================================
  // AUTO-SCROLL
  // =========================================================

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);


  // =========================================================
  // LOAD STATUS AFTER LOGIN
  // =========================================================

  useEffect(() => {
    if (token) {
      loadStatus();
    }
  }, [token]);


  // =========================================================
  // AUTH REQUEST
  // =========================================================

  const handleAuth = async (event) => {
    event.preventDefault();

    setAuthError("");
    setAuthLoading(true);

    try {
      const endpoint =
        authMode === "login"
          ? "/login"
          : "/register";

      const response = await fetch(
        `${API_URL}${endpoint}`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            email: email.trim(),
            password,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
          "Authentication failed."
        );
      }

      localStorage.setItem(
        "rag_token",
        data.access_token
      );

      localStorage.setItem(
        "rag_user",
        JSON.stringify(data.user)
      );

      setToken(data.access_token);
      setUser(data.user);

      setEmail("");
      setPassword("");
      setAuthError("");

    } catch (error) {
      setAuthError(
        error.message ||
        "Authentication failed."
      );

    } finally {
      setAuthLoading(false);
    }
  };


  // =========================================================
  // LOGOUT
  // =========================================================

  const handleLogout = () => {
    localStorage.removeItem("rag_token");
    localStorage.removeItem("rag_user");

    setToken("");
    setUser(null);

    setMessages([
      {
        role: "assistant",
        text:
          "Hello! I'm your Enterprise RAG AI Assistant.",
        sources: [],
      },
    ]);

    setDocumentCount(0);
    setChunkCount(0);
  };


  // =========================================================
  // LOAD BACKEND STATUS
  // =========================================================

  const loadStatus = async () => {
  try {
    const statusResponse = await fetch(
      `${API_URL}/`
    );

    if (statusResponse.ok) {
      const statusData =
        await statusResponse.json();

      setDocumentCount(
        statusData.documents || 0
      );

      setChunkCount(
        statusData.chunks || 0
      );
    }


    const documentsResponse = await fetch(
      `${API_URL}/documents`,
      {
        headers: {
          Authorization:
            `Bearer ${token}`,
        },
      }
    );


    if (documentsResponse.status === 401) {
      handleLogout();
      return;
    }


    if (!documentsResponse.ok) {
      return;
    }


    const documentsData =
      await documentsResponse.json();


    setDocuments(
      documentsData.documents || []
    );

    setDocumentCount(
      documentsData.total_documents || 0
    );

  } catch (error) {
    console.error(
      "Document loading error:",
      error
    );
  }
};


  // =========================================================
  // SEND QUESTION
  // =========================================================

  const handleSend = async () => {
    const question = input.trim();

    if (
      !question ||
      loading ||
      uploading
    ) {
      return;
    }

    setMessages((previousMessages) => [
      ...previousMessages,
      {
        role: "user",
        text: question,
        sources: [],
      },
    ]);

    setInput("");
    setLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/ask`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",

            Authorization:
              `Bearer ${token}`,
          },

          body: JSON.stringify({
            question,
          }),
        }
      );

      const data = await response.json();

      if (response.status === 401) {
        handleLogout();

        throw new Error(
          "Your session expired. Please login again."
        );
      }

      if (!response.ok) {
        throw new Error(
          data.detail ||
          "AI request failed."
        );
      }

      setMessages(
        (previousMessages) => [
          ...previousMessages,
          {
            role: "assistant",
            text: data.answer,
            sources: data.sources || [],
          },
        ]
      );

    } catch (error) {
      console.error(error);

      setMessages(
        (previousMessages) => [
          ...previousMessages,
          {
            role: "assistant",
            text:
              error.message ||
              "I couldn't complete your request.",
            sources: [],
          },
        ]
      );

    } finally {
      setLoading(false);
    }
  };


  // =========================================================
  // ENTER KEY
  // =========================================================

  const handleKeyDown = (event) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      handleSend();
    }
  };


  // =========================================================
  // SELECT PDF
  // =========================================================

  const handleFileChange = (event) => {
    const file =
      event.target.files[0];

    setUploadStatus("");

    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (
      file.type !== "application/pdf" &&
      !file.name
        .toLowerCase()
        .endsWith(".pdf")
    ) {
      setSelectedFile(null);

      setUploadStatus(
        "Please select a PDF file."
      );

      return;
    }

    setSelectedFile(file);
  };


  // =========================================================
  // UPLOAD PDF
  // =========================================================

  const handleUpload = async () => {
    if (
      !selectedFile ||
      uploading
    ) {
      return;
    }

    setUploading(true);

    setUploadStatus(
      "Uploading and indexing..."
    );

    try {
      const formData =
        new FormData();

      formData.append(
        "file",
        selectedFile
      );

      const response = await fetch(
        `${API_URL}/upload`,
        {
          method: "POST",

          headers: {
            Authorization:
              `Bearer ${token}`,
          },

          body: formData,
        }
      );

      const data =
        await response.json();

      if (response.status === 401) {
        handleLogout();

        throw new Error(
          "Your session expired. Please login again."
        );
      }

      if (!response.ok) {
        throw new Error(
          data.detail ||
          "Upload failed."
        );
      }

      setDocumentCount(
        data.total_documents
      );

      setChunkCount(
        data.total_chunks
      );

      setUploadStatus(
        "Document indexed successfully."
      );

      setMessages(
        (previousMessages) => [
          ...previousMessages,
          {
            role: "assistant",

            text:
              `${data.filename} has been added to the ` +
              "knowledge base. You can ask questions about it now.",

            sources: [],
          },
        ]
      );

      setSelectedFile(null);
      await loadStatus();

      const fileInput =
        document.getElementById(
          "pdf-upload"
        );

      if (fileInput) {
        fileInput.value = "";
      }

    } catch (error) {
      console.error(error);

      setUploadStatus(
        error.message ||
        "Upload failed."
      );

    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (filename) => {
  const confirmed = window.confirm(
    `Are you sure you want to delete "${filename}"?`
  );

  if (!confirmed) {
    return;
  }

  try {
    const response = await fetch(
      `${API_URL}/documents/${encodeURIComponent(filename)}`,
      {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    const data = await response.json();

    if (response.status === 401) {
      handleLogout();
      return;
    }

    if (!response.ok) {
      throw new Error(
        data.detail || "Failed to delete document."
      );
    }

    await loadStatus();

    setMessages((previousMessages) => [
      ...previousMessages,
      {
        role: "assistant",
        text: `${filename} was deleted from your knowledge base.`,
        sources: [],
      },
    ]);

  } catch (error) {
    console.error("Delete error:", error);

    alert(
      error.message ||
      "Failed to delete document."
    );
  }
};


  // =========================================================
  // CLEAR CHAT
  // =========================================================

  const clearChat = () => {
    setMessages([
      {
        role: "assistant",
        text:
          "Chat cleared. Ask me another question about your documents.",
        sources: [],
      },
    ]);
  };


  // =========================================================
  // AUTH SCREEN
  // =========================================================

  if (!token || !user) {
    return (
      <div className="auth-page">

        <div className="auth-card">

          <div className="auth-brand-icon">
            AI
          </div>

          <h1>
            Enterprise RAG
          </h1>

          <p className="auth-subtitle">
            Secure Document Intelligence
          </p>


          <div className="auth-tabs">

            <button
              className={
                authMode === "login"
                  ? "auth-tab active"
                  : "auth-tab"
              }
              onClick={() => {
                setAuthMode("login");
                setAuthError("");
              }}
            >
              Login
            </button>

            <button
              className={
                authMode === "register"
                  ? "auth-tab active"
                  : "auth-tab"
              }
              onClick={() => {
                setAuthMode("register");
                setAuthError("");
              }}
            >
              Create Account
            </button>

          </div>


          <form
            className="auth-form"
            onSubmit={handleAuth}
          >

            <label>
              Email
            </label>

            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              required
              onChange={(event) =>
                setEmail(
                  event.target.value
                )
              }
            />


            <label>
              Password
            </label>

            <input
              type="password"
              placeholder="Minimum 6 characters"
              value={password}
              required
              minLength={6}
              onChange={(event) =>
                setPassword(
                  event.target.value
                )
              }
            />


            {authError && (
              <div className="auth-error">
                {authError}
              </div>
            )}


            <button
              className="auth-submit"
              type="submit"
              disabled={authLoading}
            >
              {authLoading
                ? "Please wait..."
                : authMode === "login"
                  ? "Login"
                  : "Create Account"}
            </button>

          </form>

        </div>

      </div>
    );
  }


  // =========================================================
  // MAIN APP
  // =========================================================

  return (
    <div className="app-shell">

      <aside className="sidebar">

        <div className="brand">

          <div className="brand-icon">
            AI
          </div>

          <div>
            <h1>
              Enterprise RAG
            </h1>

            <p>
              Document Intelligence
            </p>
          </div>

        </div>


        <div className="user-card">

          <span>
            Signed in as
          </span>

          <strong>
            {user.email}
          </strong>

        </div>


        <div className="sidebar-section">

          <p className="section-label">
            KNOWLEDGE BASE
          </p>

          <div className="stats-grid">

            <div className="stat-card">
              <span>Documents</span>
              <strong>
                {documentCount}
              </strong>
            </div>

            <div className="stat-card">
              <span>Chunks</span>
              <strong>
                {chunkCount}
              </strong>
            </div>

          </div>

          <div className="document-list">

            {documents.length === 0 ? (

              <p className="empty-documents">
                No documents indexed.
              </p>

            ) : (

              documents.map((document, index) => (

                <div
  className="document-item"
  key={`${document.filename}-${index}`}
>
  <div className="document-icon">
    PDF
  </div>

  <div className="document-info">
    <strong>
      {document.filename}
    </strong>

    <span>
      {document.pages} pages
      {" • "}
      {document.chunks} chunks
    </span>
  </div>

  <button
    type="button"
    className="document-delete-button"
    onClick={() =>
      handleDeleteDocument(document.filename)
    }
  >
    Delete
  </button>
</div>

              ))
            )}

          </div>

        </div>


        <div className="sidebar-section">

          <p className="section-label">
            ADD DOCUMENT
          </p>

          <label
            className="file-picker"
            htmlFor="pdf-upload"
          >

            <span className="upload-icon">
              ↑
            </span>

            <span>
              {selectedFile
                ? selectedFile.name
                : "Choose PDF"}
            </span>

          </label>

          <input
            id="pdf-upload"
            className="hidden-file-input"
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileChange}
            disabled={uploading}
          />

          <button
            className="upload-button"
            onClick={handleUpload}
            disabled={
              !selectedFile ||
              uploading
            }
          >
            {uploading
              ? "Indexing..."
              : "Upload Document"}
          </button>

          {uploadStatus && (
            <div className="upload-status">
              {uploadStatus}
            </div>
          )}

        </div>


        <div className="sidebar-bottom">

          <button
            className="logout-button"
            onClick={handleLogout}
          >
            Logout
          </button>

        </div>

      </aside>


      <main className="main-panel">

        <header className="topbar">

          <div>
            <h2>
              AI Document Assistant
            </h2>

            <p>
              Grounded answers from your knowledge base
            </p>
          </div>

          <button
            className="clear-button"
            onClick={clearChat}
          >
            Clear Chat
          </button>

        </header>


        <section className="chat-area">

          <div className="messages">

            {messages.map(
              (message, index) => (

                <div
                  key={index}
                  className={
                    `message-row ${message.role}`
                  }
                >

                  {message.role ===
                    "assistant" && (

                    <div className="avatar">
                      AI
                    </div>

                  )}


                  <div className="message-content">

                    <div className="role-label">
                      {message.role ===
                      "assistant"
                        ? "RAG Assistant"
                        : "You"}
                    </div>

                    <div className="message-bubble">
                      {message.text}
                    </div>


                    {message.sources &&
                      message.sources.length >
                        0 && (

                        <div className="sources">

                          <div className="sources-title">
                            Sources
                          </div>

                          <div className="source-list">

                            {message.sources.map(
                              (
                                source,
                                sourceIndex
                              ) => (

                                <div
                                  key={
                                    sourceIndex
                                  }
                                  className="source-card"
                                >

                                  <span>
                                    📄
                                  </span>

                                  <div>

                                    <strong>
                                      {
                                        source.source
                                      }
                                    </strong>

                                    <p>
                                      Page{" "}
                                      {
                                        source.page
                                      }
                                    </p>

                                  </div>

                                </div>

                              )
                            )}

                          </div>

                        </div>

                      )}

                  </div>

                </div>

              )
            )}


            {loading && (

              <div className="message-row assistant">

                <div className="avatar">
                  AI
                </div>

                <div className="message-content">

                  <div className="role-label">
                    RAG Assistant
                  </div>

                  <div className="message-bubble thinking">
                    <span />
                    <span />
                    <span />
                  </div>

                </div>

              </div>

            )}


            <div ref={messagesEndRef} />

          </div>

        </section>


        <footer className="composer">

          <div className="composer-box">

            <textarea
              placeholder={
                "Ask anything about your documents..."
              }
              value={input}
              disabled={
                loading ||
                uploading
              }
              onChange={(event) =>
                setInput(
                  event.target.value
                )
              }
              onKeyDown={
                handleKeyDown
              }
              rows="1"
            />

            <button
              className="send-button"
              onClick={handleSend}
              disabled={
                loading ||
                uploading ||
                !input.trim()
              }
            >
              ↑
            </button>

          </div>

          <p className="composer-note">
            Answers are generated only from your indexed documents.
          </p>

        </footer>

      </main>

    </div>
  );
}

export default App;