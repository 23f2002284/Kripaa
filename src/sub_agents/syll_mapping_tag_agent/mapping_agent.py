import asyncio
import numpy as np
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utils.db import get_session
from utils.logger import get_logger
from utils.llm import generate_embedding
from src.data_models.models import SyllabusNode, VariantGroup

logger = get_logger()

# Threshold tiers for mapping questions to syllabus topics (High to Low)
MAPPING_THRESHOLDS = [0.75, 0.65, 0.60, 0.50, 0.40, 0.30]

async def enrich_syllabus_nodes():
    """
    Generates embeddings for all SyllabusNodes that don't have them.
    """
    logger.info("Starting Syllabus Enrichment (Embeddings)...")
    
    async for session in get_session():
        try:
            stmt = select(SyllabusNode).where(SyllabusNode.embedding == None)
            result = await session.execute(stmt)
            nodes = result.scalars().all()
            
            logger.info(f"Found {len(nodes)} syllabus nodes needing embeddings.")
            
            updated_count = 0
            
            for node in nodes:
                # Create text for embedding: Topic + Description + Module
                text_to_embed = f"{node.topic}. {node.description or ''}. Module: {node.module}"
                
                embedding = await generate_embedding(text_to_embed)
                node.embedding = embedding
                session.add(node)
                updated_count += 1
                
                if updated_count % 10 == 0:
                    logger.info(f"Enriched {updated_count} syllabus nodes.")
                    await session.commit()
            
            await session.commit()
            logger.info(f"Enriched {updated_count} syllabus nodes.")
            
        except Exception as e:
            logger.error(f"Error enriching syllabus: {e}")
            await session.rollback()
            raise
        break

async def enrich_variant_groups():
    """
    Generates embeddings for all VariantGroups that don't have them.
    """
    logger.info("Starting Variant Group Enrichment (Embeddings)...")
    
    async for session in get_session():
        try:
            stmt = select(VariantGroup).where(VariantGroup.embedding == None)
            result = await session.execute(stmt)
            groups = result.scalars().all()
            
            logger.info(f"Found {len(groups)} variant groups needing embeddings.")
            
            updated_count = 0
            
            for group in groups:
                embedding = await generate_embedding(group.canonical_stem)
                group.embedding = embedding
                session.add(group)
                updated_count += 1
                
                if updated_count % 10 == 0:
                    logger.info(f"Enriched {updated_count} variant groups.")
                    await session.commit()
            
            await session.commit()
            logger.info(f"Enriched {updated_count} variant groups.")
            
        except Exception as e:
            logger.error(f"Error enriching variant groups: {e}")
            await session.rollback()
            raise
        break

async def map_questions_to_syllabus():
    """
    Maps VariantGroups to SyllabusNodes using vector similarity with dynamic thresholds.
    """
    logger.info("Starting Question Mapping...")
    
    async for session in get_session():
        try:
            # 1. Fetch all VariantGroups that are not mapped
            stmt = select(VariantGroup).where(VariantGroup.syllabus_node_id == None)
            result = await session.execute(stmt)
            groups = result.scalars().all()
            
            logger.info(f"Found {len(groups)} unmapped variant groups.")
            
            if not groups:
                return

            # 2. Fetch all SyllabusNodes with embeddings
            stmt = select(SyllabusNode).where(SyllabusNode.embedding != None)
            result = await session.execute(stmt)
            syllabus_nodes = result.scalars().all()
            
            if not syllabus_nodes:
                logger.warning("No enriched syllabus nodes found. Please run enrichment first.")
                return
            
            mapped_count = 0
            tier_counts = {t: 0 for t in MAPPING_THRESHOLDS}
            
            def cosine_similarity(a, b):
                return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
            
            for group in groups:
                if group.embedding is None:
                    logger.warning(f"Group {group.id} has no embedding. Skipping.")
                    continue

                best_node = None
                best_score = -1.0
                
                for node in syllabus_nodes:
                    score = cosine_similarity(group.embedding, node.embedding)
                    if score > best_score:
                        best_score = score
                        best_node = node
                
                # Dynamic Threshold Logic
                matched_tier = None
                for threshold in MAPPING_THRESHOLDS:
                    if best_score >= threshold:
                        matched_tier = threshold
                        break
                
                if matched_tier is not None:
                    group.syllabus_node_id = best_node.id
                    session.add(group)
                    mapped_count += 1
                    tier_counts[matched_tier] += 1
                    logger.info(f"Mapped Group '{group.canonical_stem[:30]}...' -> '{best_node.topic}' (Score: {best_score:.2f} | Tier: {matched_tier})")
                else:
                    # Log the best attempt to debug why it failed
                    best_topic = best_node.topic if best_node else "None"
                    logger.info(f"Unmapped '{group.canonical_stem[:30]}...' | Best: '{best_topic}' ({best_score:.2f}) < Min Threshold {MAPPING_THRESHOLDS[-1]}")
                
                if mapped_count % 10 == 0:
                    await session.commit()
            
            await session.commit()
            
            # Log summary of tiers
            summary_msg = ", ".join([f">={t}: {c}" for t, c in tier_counts.items()])
            logger.info(f"Mapping complete. Mapped {mapped_count} groups. Breakdown: [{summary_msg}]")
            
        except Exception as e:
            logger.error(f"Error in mapping: {e}")
            await session.rollback()
            raise
        break
