import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq

# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv()

# -----------------------------
# Streamlit Config
# -----------------------------
st.set_page_config(
    page_title="Student Notes AI Assistant",
    page_icon="📚",
    layout="wide"
)

# -----------------------------
# Session State
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "summary" not in st.session_state:
    st.session_state.summary = ""

if "important_questions" not in st.session_state:
    st.session_state.important_questions = ""

if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""

# -----------------------------
# Header
# -----------------------------
st.title("📚 Student Notes AI Assistant")
st.caption("🚀 AI Powered PDF Question Answering using RAG, FAISS and Groq")

st.markdown("---")

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:

    st.header("⚙️ Project Info")

    st.write("🤖 Model : Llama 3.3 70B")
    st.write("🧠 Embeddings : MiniLM")
    st.write("🔍 Vector DB : FAISS")
    st.write("⚡ Framework : Streamlit")

    st.markdown("---")

    if st.button("🗑 Clear Chat"):

        st.session_state.chat_history = []

        st.success("Chat Cleared")

st.write("📄 Upload your PDF notes and start asking questions.")

uploaded_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"]
)
if uploaded_file is not None:

    # -----------------------------
    # Save Uploaded PDF
    # -----------------------------
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(uploaded_file.read())
        temp_pdf_path = temp_file.name

    st.success("✅ PDF Uploaded Successfully")

    # -----------------------------
    # Load PDF
    # -----------------------------
    loader = PyMuPDFLoader(temp_pdf_path)
    documents = loader.load()

    st.success(f"✅ Total Pages : {len(documents)}")

    # -----------------------------
    # Split into Chunks
    # -----------------------------
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(documents)

    st.success(f"✅ Total Chunks : {len(chunks)}")

    # -----------------------------
    # Embedding Model
    # -----------------------------
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # -----------------------------
    # Create FAISS Vector Store
    # -----------------------------
    vector_db = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings
    )

    st.success("✅ FAISS Vector Database Created")

    # -----------------------------
    # Initialize Groq
    # -----------------------------
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0
    )

    st.success("✅ Groq Connected")
        # =========================================================
    # SUMMARY
    # =========================================================
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📄 Summarize Notes"):

            context = "\n\n".join([doc.page_content for doc in chunks])

            prompt = f"""
You are a helpful AI assistant.

Read the following notes and generate a short and easy-to-understand summary.

Notes:
{context}

Summary:
"""

            with st.spinner("Generating Summary..."):
                response = llm.invoke(prompt)

            st.session_state.summary = response.content

    with col2:
        if st.button("🎯 Generate Important Questions"):

            context = "\n\n".join([doc.page_content for doc in chunks])

            prompt = f"""
You are an expert teacher.

Read the following notes and generate the 10 most important exam questions.

Rules:
- Generate only questions.
- Number them from 1 to 10.
- Do not provide answers.

Notes:
{context}
"""

            with st.spinner("Generating Questions..."):
                response = llm.invoke(prompt)

            st.session_state.important_questions = response.content

    # -----------------------------
    # Display Summary
    # -----------------------------
    if st.session_state.summary:

        st.markdown("---")
        st.subheader("📄 Notes Summary")
        st.write(st.session_state.summary)

    # -----------------------------
    # Display Important Questions
    # -----------------------------
    if st.session_state.important_questions:

        st.markdown("---")
        st.subheader("🎯 Important Questions")
        st.write(st.session_state.important_questions)

    # =========================================================
    # ASK QUESTION
    # =========================================================
    st.markdown("---")

    question = st.text_input("💬 Ask a question from your PDF")

    if question:

        docs = vector_db.similarity_search(question, k=3)

        context = "\n\n".join([doc.page_content for doc in docs])

        prompt = f"""
You are a helpful AI assistant.

Answer the user's question ONLY using the context below.

Context:
{context}

Question:
{question}

Answer:
"""

        with st.spinner("Generating Answer..."):
            response = llm.invoke(prompt)

        st.session_state.last_answer = response.content

        st.session_state.chat_history.append(
            {
                "question": question,
                "answer": response.content
            }
        )

    # -----------------------------
    # Display Answer
    # -----------------------------
    if st.session_state.last_answer:

        st.subheader("📖 Answer")
        st.write(st.session_state.last_answer)
            # =========================================================
    # Retrieved Chunks
    # =========================================================
    if question and "docs" in locals():

        with st.expander("🔍 Retrieved Chunks"):

            for i, doc in enumerate(docs, start=1):

                st.markdown(f"### 📄 Chunk {i}")

                st.write(doc.page_content)

                st.markdown("---")

    # =========================================================
    # Download Answer
    # =========================================================
    if st.session_state.last_answer:

        st.download_button(
            label="📥 Download Answer",
            data=st.session_state.last_answer,
            file_name="answer.txt",
            mime="text/plain"
        )

    # =========================================================
    # Chat History
    # =========================================================
    if st.session_state.chat_history:

        st.markdown("---")
        st.subheader("💬 Conversation History")

        for chat in reversed(st.session_state.chat_history):

            with st.chat_message("user"):
                st.write(chat["question"])

            with st.chat_message("assistant"):
                st.write(chat["answer"])

    # =========================================================
    # Footer
    # =========================================================
    st.markdown("---")

    st.caption(
        "🚀 Built with Python • Streamlit • LangChain • FAISS • HuggingFace • Groq"
    )