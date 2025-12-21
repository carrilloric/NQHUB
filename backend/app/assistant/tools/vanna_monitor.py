"""
Vanna.AI Monitoring and Training Management
"""
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class VannaMonitor:
    """Monitor and analyze Vanna training progress"""

    def __init__(self, vanna_client=None):
        """
        Initialize VannaMonitor with a Vanna client instance

        Args:
            vanna_client: VannaNQHub instance to monitor (optional, will get singleton if not provided)
        """
        self.vanna_client = vanna_client
        self._chroma_client = None

    @property
    def chroma_client(self):
        """Lazy access to ChromaDB client from Vanna instance"""
        if self._chroma_client is None and self.vanna_client:
            if hasattr(self.vanna_client, 'vn') and self.vanna_client.vn:
                # Access the ChromaDB client from Vanna's vector store
                if hasattr(self.vanna_client.vn, 'chroma_client'):
                    self._chroma_client = self.vanna_client.vn.chroma_client
        return self._chroma_client

    def get_training_stats(self) -> Dict[str, Any]:
        """
        Get statistics about Vanna's training data

        Returns:
            Dict with counts and metadata
        """
        # Ensure we have a vanna_client
        if not self.vanna_client:
            # Try to get singleton
            try:
                from app.assistant.tools.vanna_sql import get_vanna_client
                self.vanna_client = get_vanna_client()
            except Exception as e:
                logger.error(f"Failed to get Vanna client: {e}")

        if not self.vanna_client or not self.vanna_client.vn:
            return {
                "status": "unavailable",
                "message": "Vanna not available or not initialized yet"
            }

        try:
            # Get ChromaDB client from Vanna
            chroma = self.chroma_client
            if not chroma:
                return {
                    "status": "unavailable",
                    "message": "ChromaDB client not accessible"
                }

            # Get all collections
            collections = chroma.list_collections()

            # Get chroma path from config
            from app.assistant.config import assistant_config
            chroma_path = assistant_config.VANNA_CHROMA_PATH

            stats = {
                "status": "active",
                "chroma_path": chroma_path,
                "collections": [],
                "total_documents": 0,
                "total_ddl": 0,
                "total_sql_examples": 0,
                "total_documentation": 0
            }

            for collection in collections:
                col_data = {
                    "name": collection.name,
                    "count": collection.count(),
                    "metadata": collection.metadata if hasattr(collection, 'metadata') else None
                }
                stats["collections"].append(col_data)
                stats["total_documents"] += col_data["count"]

                # Categorize by collection name
                if "ddl" in collection.name.lower():
                    stats["total_ddl"] += col_data["count"]
                elif "sql" in collection.name.lower():
                    stats["total_sql_examples"] += col_data["count"]
                elif "doc" in collection.name.lower():
                    stats["total_documentation"] += col_data["count"]

            return stats

        except Exception as e:
            logger.error(f"Failed to get training stats: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def get_learned_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get list of queries Vanna has learned

        Args:
            limit: Maximum number of queries to return

        Returns:
            List of {question, sql} dicts
        """
        chroma = self.chroma_client
        if not chroma:
            return []

        try:
            # Look for SQL collection (Vanna typically uses 'sql' collection)
            collections = chroma.list_collections()
            sql_collection = None

            for col in collections:
                if "sql" in col.name.lower():
                    sql_collection = col
                    break

            if not sql_collection:
                return []

            # Get all documents
            results = sql_collection.get(limit=limit)

            queries = []
            if results and "documents" in results:
                for i, doc in enumerate(results["documents"]):
                    query_data = {
                        "id": results["ids"][i] if "ids" in results else None,
                        "content": doc,
                        "metadata": results["metadatas"][i] if "metadatas" in results else {}
                    }
                    queries.append(query_data)

            return queries

        except Exception as e:
            logger.error(f"Failed to get learned queries: {e}")
            return []

    def export_training_data(self, output_path: str) -> bool:
        """
        Export all training data to JSON file

        Args:
            output_path: Path to save JSON file

        Returns:
            True if successful
        """
        try:
            stats = self.get_training_stats()
            queries = self.get_learned_queries(limit=1000)

            export_data = {
                "exported_at": datetime.utcnow().isoformat(),
                "stats": stats,
                "learned_queries": queries
            }

            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Exported training data to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export training data: {e}")
            return False

    def clear_training_data(self, confirm: bool = False) -> bool:
        """
        Clear all training data (DANGEROUS - requires confirmation)

        Args:
            confirm: Must be True to actually clear data

        Returns:
            True if cleared
        """
        if not confirm:
            logger.warning("Clear operation requires confirm=True")
            return False

        if not self.client:
            return False

        try:
            # Delete all collections
            collections = self.client.list_collections()
            for col in collections:
                self.client.delete_collection(col.name)

            logger.info("Cleared all Vanna training data")
            return True

        except Exception as e:
            logger.error(f"Failed to clear training data: {e}")
            return False

    def get_category_breakdown(self) -> Dict[str, int]:
        """
        Get breakdown of queries by category (FVG, LP, OB, ETL, Candles)

        Returns:
            Dict with counts per category
        """
        breakdown = {
            "fvg": 0,
            "liquidity_pools": 0,
            "order_blocks": 0,
            "etl": 0,
            "candles": 0,
            "other": 0
        }

        queries = self.get_learned_queries(limit=1000)

        for query in queries:
            content_lower = query["content"].lower()

            # Categorize by keywords
            if "fvg" in content_lower or "fair value gap" in content_lower:
                breakdown["fvg"] += 1
            elif "liquidity pool" in content_lower or "eqh" in content_lower or "eql" in content_lower:
                breakdown["liquidity_pools"] += 1
            elif "order block" in content_lower or "ob_" in content_lower:
                breakdown["order_blocks"] += 1
            elif "etl" in content_lower or "etl_job" in content_lower:
                breakdown["etl"] += 1
            elif "candlestick" in content_lower or "candle" in content_lower:
                breakdown["candles"] += 1
            else:
                breakdown["other"] += 1

        return breakdown

    def get_similar_queries(self, question: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar queries that Vanna has learned

        Args:
            question: Natural language question
            limit: Number of similar queries to return

        Returns:
            List of similar queries with similarity scores
        """
        chroma = self.chroma_client
        if not chroma:
            return []

        try:
            # Look for SQL collection
            collections = chroma.list_collections()
            sql_collection = None

            for col in collections:
                if "sql" in col.name.lower():
                    sql_collection = col
                    break

            if not sql_collection:
                return []

            # Query for similar documents
            results = sql_collection.query(
                query_texts=[question],
                n_results=limit
            )

            similar = []
            if results and "documents" in results:
                for i, doc_list in enumerate(results["documents"]):
                    for j, doc in enumerate(doc_list):
                        similar_query = {
                            "content": doc,
                            "distance": results["distances"][i][j] if "distances" in results else None,
                            "metadata": results["metadatas"][i][j] if "metadatas" in results else {}
                        }
                        similar.append(similar_query)

            return similar

        except Exception as e:
            logger.error(f"Failed to find similar queries: {e}")
            return []


# Singleton instance
_vanna_monitor: Optional[VannaMonitor] = None


def get_vanna_monitor() -> VannaMonitor:
    """Get or create Vanna monitor singleton (shares Vanna client instance)"""
    global _vanna_monitor
    if _vanna_monitor is None:
        # Get the Vanna client singleton to share the same ChromaDB instance
        from app.assistant.tools.vanna_sql import get_vanna_client
        vanna_client = get_vanna_client()
        _vanna_monitor = VannaMonitor(vanna_client=vanna_client)
    return _vanna_monitor
