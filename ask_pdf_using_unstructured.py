import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
from chunking.unstructured import get_chunks_from_pdf


load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "sk-...")

docs = get_chunks_from_pdf("data/attention_is_all_you_need.pdf")

embedding = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(docs, embedding)

qa = RetrievalQA.from_chain_type(
    llm=OpenAI(),
    retriever=vectorstore.as_retriever(search_kwargs={"k": 1}),
    return_source_documents=True
)

while True:
    query = input("\nAsk a question (or type 'exit'): ")
    if query.strip().lower() == "exit":
        break
    answer = qa.invoke({"query": query})
    
    print("\nAnswer:", answer['result'])

    for doc in answer["source_documents"]:
        print("Reference:")
        print(f"Pages: {doc.metadata['pages']}")
        print(f"Content: {doc.page_content}")
        print("-" * 80)