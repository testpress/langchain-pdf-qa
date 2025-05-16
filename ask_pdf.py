import os
from collections import defaultdict
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
loader = PyPDFLoader("/Users/bharath/Downloads/1640701.pdf")
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
    retriever=vectorstore.as_retriever(),
    return_source_documents=True
)

# 6. Ask interactively
while True:
    query = input("\nAsk a question (or type 'exit'): ")
    if query.strip().lower() == "exit":
        break
    answer = qa.invoke({"query": query})
    
    seen = set()
    print("\nAnswer:", answer['result'])

    unique_pages = defaultdict(set)  # {source: set(pages)}
    for doc in answer["source_documents"]:
        source = os.path.basename(doc.metadata.get("source", "Unknown"))
        try:
            page = int(doc.metadata.get("page"))
        except (TypeError, ValueError):
            continue
        unique_pages[source].add(page)

    # 3. Sort and display
    print("\nSources:")
    for source in sorted(unique_pages):
        for page in sorted(unique_pages[source]):
            print(f"- Page {page} from {source}")