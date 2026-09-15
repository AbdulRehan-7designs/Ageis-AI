import fastembed
from qdrant_client import QdrantClient
from FlagEmbedding import FlagReranker

print('fastembed', fastembed.__version__)
print('qdrant_client module OK', __import__('qdrant_client').__name__)
print('has query_points', hasattr(QdrantClient, 'query_points'))
print('has search', hasattr(QdrantClient, 'search'))
print('FlagReranker OK', FlagReranker)
