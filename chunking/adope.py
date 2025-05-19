import json
import os
from datetime import datetime
import zipfile
from typing import List, Dict, Any, Tuple
import re
from dotenv import load_dotenv
from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.exception.exceptions import ServiceApiException, ServiceUsageException, SdkException
from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
from adobe.pdfservices.operation.io.stream_asset import StreamAsset
from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.pdfjobs.jobs.extract_pdf_job import ExtractPDFJob
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_element_type import ExtractElementType
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_pdf_params import ExtractPDFParams
from adobe.pdfservices.operation.pdfjobs.result.extract_pdf_result import ExtractPDFResult
from chunking import adobe_generated_response
from langchain_core.documents import Document

load_dotenv()

PDF_SERVICES_CLIENT_ID = os.getenv('PDF_SERVICES_CLIENT_ID')
PDF_SERVICES_CLIENT_SECRET = os.getenv('PDF_SERVICES_CLIENT_SECRET')

def get_chunks_from_pdf(pdf_path: str, max_chars: int = 2000, test: bool = False):
    if test:
        chunks =  get_section_chunks(adobe_generated_response.TEST_RESPONSE['elements'], max_chars)
        documents = create_documents(chunks, pdf_path)
        return documents
    
    """Get section-based chunks from PDF."""
    credentials = ServicePrincipalCredentials(
        client_id=PDF_SERVICES_CLIENT_ID,
        client_secret=PDF_SERVICES_CLIENT_SECRET
    )
    pdf_services = PDFServices(credentials=credentials)
    input_stream = get_file_stream(pdf_path)

    input_asset = pdf_services.upload(input_stream=input_stream, mime_type=PDFServicesMediaType.PDF)
    
    extract_pdf_params = ExtractPDFParams(
        elements_to_extract=[ExtractElementType.TEXT, ExtractElementType.TABLES],
    )
    
    extract_pdf_job = ExtractPDFJob(input_asset=input_asset, extract_pdf_params=extract_pdf_params)
    location = pdf_services.submit(extract_pdf_job)

    pdf_services_response = pdf_services.get_job_result(location, ExtractPDFResult)

    result_asset: CloudAsset = pdf_services_response.get_result().get_resource()

    stream_asset: StreamAsset = pdf_services.get_content(result_asset)

    output_file_path = create_output_file_path()

    with open(output_file_path, "wb") as file:
        file.write(stream_asset.get_input_stream())

    archive = zipfile.ZipFile(output_file_path, 'r')
    jsonentry = archive.open('structuredData.json')
    jsondata = json.loads(jsonentry.read())
    
    # Extract elements and create section chunks
    elements = jsondata.get('elements', [])
    chunks = get_section_chunks(elements, max_chars)
    documents = create_documents(chunks, pdf_path)
    return documents


def get_section_chunks(elements: List[Dict[str, Any]], max_chunk_size: int = 2000) -> List[Dict[str, Any]]:
    chunks = []
    current_section = {
        "header": "",
        "content": [],
        "level": 0,
        "parent": "",
        "bounds": None,
        "path": ""
    }
    
    current_paragraph = []
    current_path = None
    
    for element in elements:
        if not isinstance(element, dict) or 'Text' not in element:
            continue
            
        text = element.get('Text', '').strip()
        if not text:
            continue
            
        path = element.get('Path', '')
        
        if is_section_header(element):
            # Process any accumulated paragraph content
            if current_paragraph:
                current_section["content"].append(' '.join(current_paragraph))
                current_paragraph = []
            
            # Save previous section if exists
            if current_section["content"]:
                content = ' '.join(current_section["content"])
                for chunk in split_content_semantically(content, max_chunk_size):
                    chunks.append(create_section_chunk(current_section, chunk))
            
            # Start new section
            level = get_section_level(element)
            if level == 1:
                current_section["parent"] = text
            elif level > current_section["level"]:
                current_section["parent"] = current_section["header"]
                
            current_section = {
                "header": text,
                "content": [],
                "level": level,
                "parent": current_section["parent"],
                "bounds": element.get('Bounds'),
                "path": path
            }
            current_path = None
        else:
            if path != current_path:
                if current_paragraph:
                    current_section["content"].append(' '.join(current_paragraph))
                    current_paragraph = []
                current_path = path
            current_paragraph.append(text)
    
    if current_paragraph:
        current_section["content"].append(' '.join(current_paragraph))
    
    if current_section["content"]:
        content = ' '.join(current_section["content"])
        for chunk in split_content_semantically(content, max_chunk_size):
            chunks.append(create_section_chunk(current_section, chunk))
    
    return chunks

def is_section_header(element: Dict[str, Any]) -> bool:
    path = element.get('Path', '')
    
    section_paths = [
        '//Document/Title',  # Document title
        '//Document/H1',     # Main section
        '//Document/H2',     # Subsection
        '//Document/H3',     # Sub-subsection
    ]
    
    return any(path.startswith(header_path) for header_path in section_paths)

def get_section_level(element: Dict[str, Any]) -> int:
    path = element.get('Path', '')
    
    if path.startswith(('//Document/Title', '//Document/H1')):
        return 1
    elif path.startswith('//Document/H2'):
        return 2 
    elif path.startswith('//Document/H3'):
        return 3
    return 0 

def create_section_chunk(section: Dict[str, Any], content: str) -> Dict[str, Any]:
    return {
        "header": section['header'],
        "content": content,
        "level": section['level'],
        "parent_header": section['parent'],
        "bounds": section['bounds'],
        "path": section['path']
    }
    

def split_content_semantically(content: str, max_size: int) -> List[str]:
    if len(content) <= max_size:
        return [content]
    
    # Split into paragraphs first
    paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
    chunks = []
    current_chunk = []
    current_size = 0
    
    for paragraph in paragraphs:
        if current_size + len(paragraph) + 1 > max_size:
            if current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0
        
        # If a single paragraph is too long, split it into sentences
        if len(paragraph) > max_size:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                if current_size + len(sentence) + 1 > max_size:
                    if current_chunk:
                        chunks.append(' '.join(current_chunk))
                        current_chunk = []
                        current_size = 0
                current_chunk.append(sentence)
                current_size += len(sentence) + 1
        else:
            current_chunk.append(paragraph)
            current_size += len(paragraph) + 1
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


def get_file_stream(pdf_path: str):
    with open(pdf_path, "rb") as pdf_file:
        return pdf_file.read()


def create_output_file_path() -> str:
    now = datetime.now()
    time_stamp = now.strftime("%Y-%m-%dT%H-%M-%S")
    os.makedirs("output/ExtractTextInfoFromPDF", exist_ok=True)
    return f"output/ExtractTextInfoFromPDF/extract{time_stamp}.zip"


def create_documents(chunks: List[Dict[str, Any]], pdf_path: str) -> List[Document]:
    documents = []
    for chunk in chunks:
        parent = chunk['parent_header']
        header = chunk['header']
        content = chunk['content']
        page_content = f"Header: {header}\nContent: {content}"
        if parent:
            page_content = f"Parent: {parent}\n{page_content}"
        documents.append(
            Document(
                page_content=page_content, 
                metadata={
                    "source": pdf_path, 
                    "chunk_type": "content_based", 
                    "bounds": chunk['bounds'], 
                    "path": chunk['path']
                    }
                )
            )
    return documents

if __name__ == "__main__":
    documents = get_chunks_from_pdf("data/attention_is_all_you_need.pdf")
    for document in documents:
        print(f"Path: {document.metadata['path']}")
        print(f"Content: {document.page_content}")
        print("-" * 100)
        input()