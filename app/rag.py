import os
import uuid

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import CHROMA_HOST, CHROMA_PORT, RAG_DOCS_PATH

_store = None
_ready = False


def _load_docs() -> list[Document]:
    os.makedirs(RAG_DOCS_PATH, exist_ok=True)
    loader = DirectoryLoader(
        RAG_DOCS_PATH,
        glob="**/*.*",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    return loader.load()


def initialize_rag():
    global _store, _ready
    try:
        from langchain_chroma import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(model_name=os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5"))
        import chromadb

        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        _store = Chroma(client=client, collection_name="naofpa_rag", embedding_function=embeddings)
        docs = _load_docs()
        try:
            count = _store._collection.count()  # noqa: SLF001
        except Exception:
            count = 0
        if docs and count == 0:
            chunks = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100).split_documents(docs)
            _store.add_documents(chunks)
        _ready = True
        print(f"RAG ready ({count} existing chunks)")
    except Exception as e:
        print(f"RAG disabled ({e})")
        _ready = False


def retrieve_context(query: str, k: int = 4) -> str:
    if not _ready or _store is None:
        return ""
    docs = _store.similarity_search(query, k=k)
    return "\n\n".join(d.page_content for d in docs)


def ingest_text(text: str, source: str = "upload") -> int:
    if not _ready or _store is None:
        return 0
    chunks = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100).split_text(text)
    docs = [Document(page_content=c, metadata={"source": source}) for c in chunks]
    _store.add_documents(docs, ids=[uuid.uuid4().hex for _ in docs])
    return len(docs)