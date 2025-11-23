import asyncio
import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import select, func
from src.data_models.models import SyllabusNode, VariantGroup
from src.sub_agents.syll_mapping_tag_agent.mapping_agent import enrich_syllabus_nodes, enrich_variant_groups, map_questions_to_syllabus
from utils.db import get_session

@pytest.mark.asyncio
async def test_mapping_real_data():
    """
    Verify syllabus enrichment and question mapping.
    """
    
    # 1. Enrich Syllabus
    print("\n--- Enriching Syllabus Nodes ---")
    await enrich_syllabus_nodes()

    # 2. Enrich Variant Groups
    print("\n--- Enriching Variant Groups ---")
    await enrich_variant_groups()
    
    async for session in get_session():
        # Check if embeddings exist
        # Note: checking vector column for NULL via ORM can be tricky, let's just count
        stmt = select(func.count()).select_from(SyllabusNode)
        result = await session.execute(stmt)
        total_nodes = result.scalar()
        print(f"Total Syllabus Nodes: {total_nodes}")
        
        # 2. Run Mapping
        print("\n--- Mapping Questions to Syllabus ---")
        await map_questions_to_syllabus()
        
        # 3. Verify Results
        stmt = select(func.count()).select_from(VariantGroup).where(VariantGroup.syllabus_node_id != None)
        result = await session.execute(stmt)
        mapped_count = result.scalar()
        
        stmt = select(func.count()).select_from(VariantGroup)
        result = await session.execute(stmt)
        total_groups = result.scalar()
        
        print(f"Mapped Variant Groups: {mapped_count} / {total_groups}")
        
        # Show samples
        stmt = select(VariantGroup, SyllabusNode).join(SyllabusNode).limit(5)
        result = await session.execute(stmt)
        samples = result.all()
        
        print("\nSample Mappings:")
        for group, node in samples:
            print(f"Question: {group.canonical_stem[:50]}...")
            print(f"Topic: {node.topic} (Module: {node.module})")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_mapping_real_data())
