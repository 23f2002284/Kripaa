import asyncio
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from langchain_core.prompts import ChatPromptTemplate

from utils.db import get_session
from utils.logger import get_logger
from utils.llm import get_llm, call_llm_with_structured_output
from src.data_models.models import QuestionNormalized
from src.sub_agents.syll_mapping_tag_agent.schemas import TaggingBatchResponse
from src.sub_agents.syll_mapping_tag_agent.prompts import TAGGING_PROMPT

logger = get_logger()



# --- Main Logic ---

async def tag_questions(batch_size: int = 10):
    """
    Fetches untagged questions and uses an LLM to assign difficulty and taxonomy.
    """
    logger.info("Starting Question Tagging...")
    
    llm = get_llm(temperature=0.0)
    
    async for session in get_session():
        try:
            # 1. Fetch untagged questions (where difficulty is None)
            stmt = select(QuestionNormalized).where(QuestionNormalized.difficulty == None)
            result = await session.execute(stmt)
            questions = result.scalars().all()
            
            if not questions:
                logger.info("No untagged questions found.")
                return

            logger.info(f"Found {len(questions)} questions to tag.")
            
            # 2. Process in batches
            for i in range(0, len(questions), batch_size):
                batch = questions[i : i + batch_size]
                
                # Format input for prompt
                questions_text = "\n\n".join([
                    f"ID: {str(q.id)}\nText: {q.base_form}" 
                    for q in batch
                ])
                
                logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} questions)...")
                
                # Call LLM
                response = await call_llm_with_structured_output(
                    llm=llm,
                    output_class=TaggingBatchResponse,
                    messages=TAGGING_PROMPT.format_messages(questions_text=questions_text),
                    context_desc="Question Tagging"
                )
                
                if response and response.tags:
                    # Update DB
                    update_count = 0
                    tag_map = {t.question_id: t for t in response.tags}
                    
                    for q in batch:
                        tag_data = tag_map.get(str(q.id))
                        if tag_data:
                            q.difficulty = tag_data.difficulty
                            q.taxonomy = tag_data.taxonomy
                            session.add(q)
                            update_count += 1
                    
                    await session.commit()
                    logger.info(f"Updated {update_count} questions in this batch.")
                else:
                    logger.warning("Failed to get valid tags from LLM for this batch.")
            
            logger.info("Tagging run complete.")
            
        except Exception as e:
            logger.error(f"Error in tagging: {e}")
            await session.rollback()
            raise
        break

if __name__ == "__main__":
    asyncio.run(tag_questions())
