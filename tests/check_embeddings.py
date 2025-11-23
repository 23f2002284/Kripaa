import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import select, func
from utils.db import get_session
from src.data_models.models import SyllabusNode

async def check_syllabus_embeddings():
    print("--- Checking Syllabus Embeddings ---")
    async for session in get_session():
        # Count total nodes
        stmt_total = select(func.count(SyllabusNode.id))
        total = (await session.execute(stmt_total)).scalar()
        
        # Count nodes with embeddings
        # We need to check if embedding is not null and not empty
        # Since it's a Vector/ARRAY type, we can check for not null first
        stmt_emb = select(SyllabusNode).limit(5)
        result = await session.execute(stmt_emb)
        nodes = result.scalars().all()
        
        print(f"Total Syllabus Nodes: {total}")
        
        count_with_emb = 0
        for node in nodes:
            has_emb = False
            if node.embedding is not None:
                if isinstance(node.embedding, list) and node.embedding:
                    has_emb = True
                elif hasattr(node.embedding, 'size') and node.embedding.size > 0:
                    has_emb = True
            
            print(f"Node: {node.topic[:30]}... | Has Embedding: {has_emb}")
            if has_emb: count_with_emb += 1
            
        print(f"Sampled 5 nodes. {count_with_emb} have embeddings.")

if __name__ == "__main__":
    asyncio.run(check_syllabus_embeddings())
