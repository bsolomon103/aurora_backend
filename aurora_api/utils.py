from langchain.document_loaders import PyPDFLoader
#from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
import faiss
import shutil
#from langchain_community.vectorstores import FAISS
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
#from langchain_community.embeddings import OpenAIEmbeddings
from django.conf import settings
import os

def create_vector_store(pdffile, filename: str) -> FAISS:
    # Load data
    print("Loading data")
    pdfpath = os.path.join(settings.BASE_DIR, 'media', 'training_file', pdffile)
    loader = PyPDFLoader(pdfpath)
    data = loader.load()

    # Split data into smaller docs
    print("Splitting data into docs")
    splitter = CharacterTextSplitter(separator='\n', chunk_size=500, chunk_overlap=25)
    documents = splitter.split_documents(data)

    # Create vector store
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(documents, embeddings)
    vector_store.save_local(filename)  # Save the vector store
    print("Vector store created")
    return vector_store

