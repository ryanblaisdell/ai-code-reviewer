from fastapi import HTTPException, status
from pymongo import MongoClient
from pymongo.collection import Collection as MongoCollection

mongo_client_instance: MongoClient | None = None
chat_collection_instance: MongoCollection | None = None
users_collection_instance: MongoCollection | None = None

def get_mongo_client() -> MongoClient:
    """Dependency to get the MongoDB client instance."""
    if mongo_client_instance is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MongoDB client not initialized."
        )
    return mongo_client_instance

def get_chat_collection() -> MongoCollection:
    """Dependency to get the 'chats' MongoDB collection."""
    if chat_collection_instance is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MongoDB 'chats' collection not initialized."
        )
    return chat_collection_instance

def get_users_collection() -> MongoCollection:
    """Dependency to get the 'users' MongoDB collection."""
    if users_collection_instance is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MongoDB 'users' collection not initialized."
        )
    return users_collection_instance