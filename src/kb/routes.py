import tempfile
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from src.rag.rag_factory.weviate.weviate import WeviateDatabaseInistance
from langchain_community.document_loaders import PyPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
from src.db.db_factory.db_interface import DBInterface
from src.db.db_factory.mongo.mongo import MongoDB

router = APIRouter()

async def get_db_instance():
    db = WeviateDatabaseInistance()    
    try:
        yield db
    finally:
        db.disconnect()
        
# Dependency to ensure MongoDB is connected
async def get_db() -> DBInterface:
    """Dependency to ensure MongoDB is connected with proper error handling."""
    db_instance = None
    try:
        db_instance = MongoDB(uri="mongodb://admin:kothinAdminPass@mongodb:27017", db_name="chat_db")
        db_instance.connect()
        
        if db_instance.db is None:
            raise HTTPException(
                status_code=503, 
                detail="Database connection not available"
            )
            
        yield db_instance
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection error: {str(e)}"
        )
    finally:
        if db_instance:
            db_instance.disconnect()

@router.post("/")
async def upload_pdf(
    pdf_file: UploadFile = File(...),
    rag_db: WeviateDatabaseInistance = Depends(get_db_instance),
    mongo_db: DBInterface = Depends(get_db)
):
    file_name = pdf_file.filename
    
    if not pdf_file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")

    # Save uploaded file to a temporary location
    with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as temp_pdf:
        temp_pdf.write(await pdf_file.read())
        temp_pdf.flush()  # Ensure the file is written before reading it

        # Load the PDF and extract text
        loader = PyPDFLoader(temp_pdf.name)
        pages = [page.page_content for page in loader.load()]
        # pages = ["\n".join(pages)]
        
        # Split text into chunks using SemanticChunker
        text_splitter = SemanticChunker(OpenAIEmbeddings(model="text-embedding-3-large"), min_chunk_size=500)
        chunks = text_splitter.create_documents(pages)
        
        processed_chunks = []
        
        for chunk in chunks:
            processed_chunks.append({
                "document": chunk.page_content,
                "document_type": file_name,
                "tag": [file_name, "pdf"]
            })        

        mongo_db.post_file(file_name)
        rag_db.post_chunk("PIHR_DATASET_PDF", processed_chunks)


    return processed_chunks
