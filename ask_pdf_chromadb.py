import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

# Load .env variables (if present)
load_dotenv()

# --- Setup OpenAI ---
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "sk-...")

# --- Load PDF ---
loader = PyPDFLoader("/Users/bharath/Downloads/1640701.pdf")
pages = loader.load_and_split()

# --- Split Text ---
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = splitter.split_documents(pages)

# --- Embed & Store ---
embedding = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(docs, embedding)

# --- Build QA Chain ---
qa = RetrievalQA.from_chain_type(
    llm=OpenAI(),
    retriever=vectorstore.as_retriever()
)

# --- Ask a Question ---
while True:
    query = input("\nAsk a question (or type 'exit'): ")
    if query.lower() == "exit":
        break
    #answer = qa.run(query)
    answer = qa.invoke({"query": query})
    print("\nAnswer:", answer['result'])

