from weaviate import WeaviateClient

def get_chunks_count(collection_name: str, instance: WeaviateClient):
    """
    Retrieves all chunks from a given Weaviate collection.

    Args:
        collection_name (str): The name of the collection to retrieve chunks from.
        instance (WeaviateClient): The Weaviate client instance with an active connection.

    Returns:
        List[Dict[str, str]]: A list of dictionaries, where each dictionary contains the properties of a single chunk.
    """
    collection = instance.collections.get(collection_name)
    # chunks_count = collection.query.fetch_objects().objects
    chunks_count = sum(1 for _ in collection.iterator())    
    
    print("Chunks count: ", chunks_count)
    
    return chunks_count