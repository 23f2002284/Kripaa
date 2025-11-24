import json
import os
import base64
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
import pymupdf4llm
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
import google.generativeai as genai

from utils import get_llm, get_logger
from utils.settings import settings
from src.data_models.models import QuestionRaw
from src.sub_agents.ocr_agent.prompts import system_prompt, user_prompt
from src.sub_agents.ocr_agent.schemas import ExtractionResult

logger = get_logger()

async def extract_questions_from_pdf(pdf_path: str) -> List[QuestionRaw]:
    """
    Extracts questions from a PDF using a Hybrid Strategy:
    1. Try fast Markdown extraction (pymupdf4llm).
    2. If question count is low (< 26), fallback to Gemini Multimodal (Native PDF).
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # 1. Try Markdown Extraction
    logger.info(f"Attempting Markdown Extraction for: {pdf_path}")
    questions = await _extract_via_markdown(pdf_path)
    
    # 2. Check Quality / Quantity
    # User suggested threshold of 26.
    if len(questions) < 26:
        logger.warning(f"Low question count ({len(questions)}) detected. Attempting Multimodal Fallback...")
        try:
            multimodal_questions = await _extract_via_multimodal(pdf_path)
            
            # If Multimodal found significantly more, use it.
            # Or if Markdown found 0, use Multimodal.
            if len(multimodal_questions) > len(questions):
                logger.info(f"Multimodal extraction yielded more questions ({len(multimodal_questions)} vs {len(questions)}). Using Multimodal result.")
                return multimodal_questions
            else:
                logger.info(f"Multimodal extraction did not improve result ({len(multimodal_questions)} found). Keeping Markdown result.")
                return questions
                
        except Exception as e:
            logger.error(f"Multimodal fallback failed: {e}")
            # Return what we have from Markdown
            return questions
            
    return questions

async def _extract_via_markdown(pdf_path: str) -> List[QuestionRaw]:
    """Helper to extract via pymupdf4llm -> LLM"""
    try:
        md_text = pymupdf4llm.to_markdown(pdf_path)

    except Exception as e:
        logger.error(f"Error extracting text with pymupdf4llm: {e}")
        return []

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", user_prompt)
    ])
    
    messages = prompt_template.format_messages(md_text=md_text)

    return await _call_llm_and_parse(messages, pdf_path, "Markdown Extraction")

async def _extract_via_multimodal(pdf_path: str) -> List[QuestionRaw]:
    """Helper to extract via Gemini Native PDF (File API)"""
    try:
        # settings.google_api_key is a SecretStr, so we need .get_secret_value()
        api_key = settings.google_api_key.get_secret_value() if settings.google_api_key else None
        if not api_key:
             raise ValueError("GOOGLE_API_KEY not found in settings")
             
        genai.configure(api_key=api_key)
        logger.info(f"Uploading PDF to Google AI File API: {pdf_path}")
        uploaded_file = genai.upload_file(pdf_path)
        logger.info(f"File uploaded successfully: {uploaded_file.uri}")
    except Exception as e:
        logger.error(f"Error uploading PDF file: {e}")
        raise

    # We pass the prompt text AND the PDF file URI in a single HumanMessage
    clean_user_prompt = user_prompt.replace("{md_text}", "")
    
    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": clean_user_prompt
            },
            {
                "type": "media",
                "file_uri": uploaded_file.uri,
                "mime_type": "application/pdf"
            }
        ]
    )
    
    messages = [
        ("system", system_prompt),
        message
    ]
    
    return await _call_llm_and_parse(messages, pdf_path, "Multimodal Extraction")

async def _call_llm_and_parse(messages, pdf_path: str, context_desc: str) -> List[QuestionRaw]:
    """Shared helper to call LLM and parse results"""
    from utils.llm import get_default_llm, call_llm_with_structured_output
    
    try:
        llm = get_default_llm()
        extraction_result = await call_llm_with_structured_output(
            llm=llm,
            output_class=ExtractionResult,
            messages=messages,
            context_desc=f"{context_desc}: {os.path.basename(pdf_path)}"
        )
        
        if not extraction_result:
            return []
            
        questions_data = extraction_result.questions
        
        extracted_questions = []
        for q_data in questions_data:
            question = QuestionRaw(
                id=uuid4(),
                year=q_data.year,
                section=q_data.section,
                original_numbering=q_data.original_numbering,
                raw_text=q_data.raw_text,
                marks=q_data.marks,
                source_pdf=os.path.basename(pdf_path),
                ocr_confidence=1.0, 
                ingestion_time=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            extracted_questions.append(question)
            
        logger.info(f"{context_desc}: Extracted {len(extracted_questions)} questions.")
        return extracted_questions
        
    except Exception as e:
        logger.error(f"Error during LLM extraction ({context_desc}): {e}")
        return []

async def populate_db(extracted_questions: List[QuestionRaw]):
    """
    Populates the database with the extracted questions asynchronously.
    """
    from utils.db import get_session
    
    logger.info(f"Populating database with {len(extracted_questions)} questions...")
    async for session in get_session():
        try:
            for question in extracted_questions:
                session.add(question)
            await session.commit()
            logger.info("Database population successful.")
        except Exception as e:
            logger.error(f"Error populating database: {e}")
            await session.rollback()
            raise
        break

async def extract_syllabus_from_pdf(pdf_path: str) -> List['ExtractedTopic']:
    """
    Extracts syllabus topics from a PDF using pymupdf4llm and an LLM.
    Returns a list of ExtractedTopic Pydantic objects.
    """
    from src.sub_agents.ocr_agent.prompts import syllabus_system_prompt, syllabus_user_prompt
    from src.sub_agents.ocr_agent.schemas import SyllabusExtractionResult, ExtractedTopic
    from utils.llm import get_default_llm, call_llm_with_structured_output

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # 1. Extract text/markdown using pymupdf4llm
    try:
        md_text = pymupdf4llm.to_markdown(pdf_path)
        logger.info(f"Extracted text/markdown from Syllabus PDF: {pdf_path}")
    except Exception as e:
        logger.error(f"Error extracting text with pymupdf4llm: {e}")
        raise

    # 2. Construct Prompt for LLM
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", syllabus_system_prompt),
        ("human", syllabus_user_prompt)
    ])
    
    messages = prompt_template.format_messages(md_text=md_text)

    # 3. Call LLM with structured output
    try:
        llm = get_default_llm()
    except Exception as e:
        logger.error(f"Error getting LLM: {e}")
        raise
    
    try:
        extraction_result = await call_llm_with_structured_output(
            llm=llm,
            output_class=SyllabusExtractionResult,
            messages=messages,
            context_desc=f"Syllabus Extraction: {os.path.basename(pdf_path)}"
        )
        
        if not extraction_result:
            logger.error("Failed to extract syllabus topics.")
            return []
            
        topics_data = extraction_result.topics
        logger.info(f"Extracted {len(topics_data)} syllabus topics from PDF: {pdf_path}")
        return topics_data
        
    except Exception as e:
        logger.error(f"Error during LLM extraction: {e}")
        return []

async def populate_syllabus_db(extracted_topics: List['ExtractedTopic']):
    """
    Populates the database with the extracted syllabus topics, flattening the hierarchy.
    """
    from utils.db import get_session
    from src.data_models.models import SyllabusNode
    
    logger.info(f"Populating database with {len(extracted_topics)} syllabus topics...")
    async for session in get_session():
        try:
            # We need to flatten the hierarchy.
            # The LLM returns a list of topics with parent_name.
            # We need to infer Module and Parent Topic.
            
            # 1. Build a map of all items to resolve hierarchy
            topic_map = {t.name: t for t in extracted_topics}
            
            flat_nodes = []
            
            for topic in extracted_topics:
                # We only want to store "leaf" nodes or actual topics as rows.
                # If an item is a Module (Level 1) or Chapter (Level 2), we don't store it as a row 
                # UNLESS it has no children (which we can't easily know without checking all others).
                # BUT, the user said "having only topics in the datatable".
                # So we filter for Level 3 (Topic) or maybe Level 2 if it's a direct topic.
                
                # Let's assume Level 3 are the topics.
                # And Level 1 is Module, Level 2 is Title/Chapter.
                
                if topic.level >= 2: # Store Level 2 and 3. Level 1 is just a container.
                    
                    # Resolve Module and Parent Topic
                    module_name = None
                    parent_topic_name = None
                    
                    current = topic
                    
                    # Traverse up to find Module
                    # This is tricky with just parent_name strings if names aren't unique, but let's try.
                    
                    # Immediate parent
                    if current.parent_name:
                        parent = topic_map.get(current.parent_name)
                        if parent:
                            if parent.level == 1:
                                module_name = parent.name
                                parent_topic_name = None # Direct child of module
                            elif parent.level == 2:
                                parent_topic_name = parent.name
                                # Grandparent should be module
                                if parent.parent_name:
                                    grandparent = topic_map.get(parent.parent_name)
                                    if grandparent and grandparent.level == 1:
                                        module_name = grandparent.name
                    
                    # If we couldn't resolve module, maybe it IS a module? No, we filtered level >= 2.
                    # If we are at level 2, and parent is Module, then module is parent.
                    
                    if topic.level == 2:
                         # It's a Chapter/Title.
                         # User wants "topics in datatable... module and title in separate column"
                         # If this is a Title, does it go in?
                         # Maybe user means ONLY the lowest level things go in.
                         pass

                    # Let's simplify: Store EVERYTHING that is NOT a root module as a row?
                    # Or strictly follow: Row = Topic. Columns = Module, Title.
                    
                    # Let's try to store Level 3 items.
                    if topic.level == 3:
                        node = SyllabusNode(
                            id=uuid4(),
                            topic=topic.name,
                            description=topic.description,
                            module=module_name if module_name else "Unknown",
                            parent_topic=parent_topic_name,
                            level=topic.level,
                            estimated_hours=topic.estimated_hours if topic.estimated_hours else 0.0,
                            created_at=datetime.utcnow()
                        )
                        flat_nodes.append(node)
                    
                    # What if there are topics at Level 2 (direct under module)?
                    elif topic.level == 2:
                         # Check if this has children. If not, it might be a topic itself.
                         # For now, let's assume the LLM follows the 1-2-3 structure.
                         # If we miss Level 2 topics, we might miss data.
                         # Let's store Level 2 as well, treating them as "Topics" with no "Parent Topic" (Title).
                         
                         # But wait, if Level 2 is a "Title" that contains Level 3 "Topics", we don't want a row for the Title itself?
                         # The user said "keeping the module name and title in separate column".
                         # This implies the Row IS the Topic.
                         # So we only store the "leaves".
                         
                         # To find leaves: Check if any other topic has this topic as parent.
                         is_parent = any(t.parent_name == topic.name for t in extracted_topics)
                         if not is_parent:
                             # It's a leaf.
                             node = SyllabusNode(
                                id=uuid4(),
                                topic=topic.name,
                                description=topic.description,
                                module=module_name if module_name else "Unknown",
                                parent_topic=parent_topic_name, # Might be None if direct under Module
                                level=topic.level,
                                estimated_hours=topic.estimated_hours if topic.estimated_hours else 0.0,
                                created_at=datetime.utcnow()
                            )
                             flat_nodes.append(node)

            for node in flat_nodes:
                session.add(node)
            
            await session.commit()
            logger.info(f"Syllabus database population successful. Added {len(flat_nodes)} topics.")
        except Exception as e:
            logger.error(f"Error populating syllabus database: {e}")
            await session.rollback()
            raise
        break