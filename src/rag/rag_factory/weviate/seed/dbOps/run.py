from src.rag.rag_factory.weviate.seed.dbOps.create_collection import create_collection, pihr_schema
from src.rag.rag_factory.weviate.seed.dbOps.delete_collection import delete_collection
from src.rag.rag_factory.weviate.seed.dbOps.csv_poplator import populate_collection, get_data_rows

def run_seed(file_path: str):
    delete_collection("PIHR_DATASET")
    create_collection("PIHR_DATASET", pihr_schema)
    populate_collection("PIHR_DATASET", get_data_rows(file_path))