from fastapi import APIRouter, Depends
from src.rag.schemas import SimpleRagEntryRequest, SimpleRagEntryResponse
from src.rag.rag_factory.weviate.weviate import WeviateDatabaseInistance
from src.rag.rag_factory.weviate.seed.dbOps.run import run_seed

router = APIRouter()

async def get_db_insance():
    db = WeviateDatabaseInistance()    
    try:
        yield db
    finally:
        db.disconnect()

@router.post("/entries", response_model=SimpleRagEntryResponse)
async def query(request: SimpleRagEntryRequest, db: WeviateDatabaseInistance = Depends(get_db_insance)):
    
    entries = []
    for entry in request.entries:
        entries.append({    
            "document": entry.document,
            "document_type": entry.document_type,
            "tag": entry.tag
        })

    db.post_chunk(request.collection_name, entries)    
        
    return {
        "message": f"Successfully Added {len(entries)} Entries to RAG",
        "entries": entries
    }
    
@router.get("/entries/{collection_name}")
async def query(collection_name: str, limit: int = 10, page: int = 1, db: WeviateDatabaseInistance = Depends(get_db_insance)):        

    entries = db.get_all_chunks(collection_name, limit, page)
        
    return {
        "message": f"Successfully Fetched {len(entries)} Entries from RAG",
        "entries": entries
    }

@router.get("/entries/count/{collection_name}")
async def query(collection_name: str, db: WeviateDatabaseInistance = Depends(get_db_insance)):        

    entries = db.get_number_of_chunks(collection_name)
    print(entries)
        
    return entries

@router.get("/entries/{collection_name}/{id}")
async def query(collection_name: str, id: str, db: WeviateDatabaseInistance = Depends(get_db_insance)):        

    entries = db.get_chunks_by_ids(collection_name, [id])
        
    return {
        "message": f"Successfully Fetched {len(entries)} Entries from RAG",
        "entries": entries
    }

@router.delete("/entries/{collection_name}/{id}")
async def query(collection_name: str, id: str, db: WeviateDatabaseInistance = Depends(get_db_insance)):        

    db.delete_chunks_by_id(collection_name, [id])
        
    return {
        "message": f"Successfully Deleted {id} Entries from RAG",
    }

@router.get("/collections")
async def query(db: WeviateDatabaseInistance = Depends(get_db_insance)):        

    entries = db.get_collection_names()
        
    return {
        "message": f"Successfully Fetched Collections from RAG",
        "entries": entries
    }

@router.get("/query/{collection_name}/{query}")
async def query(collection_name: str, query: str, topk: int = 3, db: WeviateDatabaseInistance = Depends(get_db_insance)):

    entries = db.get_top_k_chunks(collection_name, query, topk, False)
        
    return {
        "message": f"Successfully Fetched {len(entries)} Entries from RAG",
        "entries": entries
    }
    
@router.get("/seed")
async def seed(file_path: str, collection_name: str = "PIHR_DATASET", db: WeviateDatabaseInistance = Depends(get_db_insance)):        
    run_seed(file_path=file_path, collection_name=collection_name)
        
    return {
        "message": f"Successfully Seeded RAG from {file_path}",
    }