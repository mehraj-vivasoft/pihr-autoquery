from weaviate import WeaviateClient
from weaviate.collections.classes.grpc import MetadataQuery


def get_top_k_chunks(collection_name: str, query: str, instance: WeaviateClient, k: int = 3, is_simple: bool = False):
    include_distance = False
    if is_simple is False:
        include_distance = True
    collection = instance.collections.get(collection_name)
    chunks = collection.query.near_text(query, limit=k, return_metadata=MetadataQuery(distance=include_distance)).objects
    
    if is_simple:
        chunks = [chunk.properties["document"] for chunk in chunks]
    
    return chunks