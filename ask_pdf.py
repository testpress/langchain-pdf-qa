import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import OpenAI
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

# Load .env variables (if present)
load_dotenv()

# 1. Set your API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "sk-...")

# 2. Load PDF
loader = PyPDFLoader("/Users/bharath/Downloads/ncert_crop.pdf")
pages = loader.load_and_split()

# 3. Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = splitter.split_documents(pages)

# 4. Create vectorstore with FAISS
embedding = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(docs, embedding)

# 5. Build Retrieval Q&A chain
qa = RetrievalQA.from_chain_type(
    llm=OpenAI(),
    retriever=vectorstore.as_retriever()
)

# 6. Ask interactively
while True:
    query = input("\nAsk a question (or type 'exit'): ")
    if query.strip().lower() == "exit":
        break
    answer = qa.run(query)
    print("\nAnswer:", answer)

