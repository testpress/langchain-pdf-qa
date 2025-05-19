from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title
from langchain_core.documents import Document

def get_chunks_from_pdf(pdf_path: str, max_chars: int = 2000) -> list[Document]:
    elements = partition_pdf(pdf_path, strategy="hi_res", extract_images_in_pdf=True)

    chunks = chunk_by_title(
        elements,
        max_characters=max_chars,
        combine_text_under_n_chars=0
    )
    
    documents = []
    for chunk in chunks:
        page_numbers = {element.metadata.page_number for element in chunk.metadata.orig_elements}
        
        doc = Document(
            page_content=str(chunk),
            metadata={
                "source": pdf_path,
                "chunk_type": "content_based",
                "pages": page_numbers,
                "orig_elements": chunk.metadata.orig_elements
            }
        )
        documents.append(doc)
        
    return documents

if __name__ == "__main__":
    pdf_path = "data/attention_is_all_you_need.pdf"
    chunks = get_chunks_from_pdf(pdf_path)
    for chunk in chunks:
        print(chunk.page_content.split("\n")[0], chunk.metadata["pages"])
        print("-" * 100)