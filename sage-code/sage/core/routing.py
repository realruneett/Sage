import faiss
import numpy as np
from typing import List, Tuple, Dict
from sage.core.aode import topological_route

class CodeRouter:
    """FAISS HNSW + Gudhi Routing over code embeddings.

    This router identifies 'topological voids' in the codebase—regions that are 
    semantically novel or under-tested—using Persistent Homology.
    """
    def __init__(self, dimension: int = 1024) -> None:
        """Initializes the HNSW index for high-speed semantic retrieval.
        
        Args:
            dimension: The dimensionality of the embedding vectors.
        """
        self.index = faiss.IndexHNSWFlat(dimension, 32)
        self.metadata: List[Dict[str, Any]] = []

    def add_files(self, vectors: np.ndarray, file_info: List[Dict[str, Any]]) -> None:
        """Adds code file embeddings and metadata to the router.
        
        Args:
            vectors: Matrix of embedding vectors.
            file_info: Metadata for each file (path, line ranges, etc.).
        """
        self.index.add(vectors.astype('float32'))
        self.metadata.extend(file_info)

    def search_topology(
        self, 
        query_vec: np.ndarray, 
        k: int = 5
    ) -> Tuple[List[Dict[str, Any]], Tuple[int, int]]:
        """Routes to topological voids (under-tested/novel areas).

        Args:
            query_vec: The embedding vector of the user's task.
            k: The number of void regions to return.

        Returns:
            Tuple containing the list of file metadata and the Betti numbers (β₁, β₂).
        """
        if self.index.ntotal == 0:
            return [], (0, 0)

        # Retrieve a broad set of semantic candidates
        dist, indices = self.index.search(query_vec.reshape(1, -1).astype('float32'), min(k * 5, self.index.ntotal))
        candidates = indices[0]
        
        # Filter out invalid indices
        valid_candidates = [int(i) for i in candidates if i >= 0]
        if not valid_candidates:
            return [], (0, 0)
            
        candidate_vecs = np.array([self.index.reconstruct(i) for i in valid_candidates])
        
        # Apply topological void discovery
        void_indices, bettis = topological_route(query_vec, candidate_vecs, k=min(k, len(valid_candidates)))
        
        results = [self.metadata[valid_candidates[i]] for i in void_indices]
        return results, bettis
