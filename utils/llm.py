from pydantic import BaseModel
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from utils.settings import settings
from utils.logger import get_logger
from typing import Any, Awaitable, Callable, List, Optional, Tuple, Type, TypeVar, Union

logger = get_logger()

T = TypeVar("T")
R = TypeVar("R")
M = TypeVar("M", bound=BaseModel)


def get_llm(
    model_name: str = "gemini-2.5-flash",
    temperature: float = 0.0,
    completions: int = 1,
) -> BaseChatModel:
    """Get LLM with specified configuration.

    Args:
        model_name: The model to use
        temperature: Temperature for generation
        completions: How many completions we need (affects temperature for diversity)

    Returns:
        Configured LLM instance
    """
    # Use higher temp when doing multiple completions for diversity
    if completions > 1 and temperature == 0.0:
        temperature = 0.2

    if not settings.google_api_key:
        raise ValueError("GOOGLE_API_KEY must be set in environment variables for Vertex AI")

    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        google_api_key=settings.google_api_key,
    )

def get_default_llm() -> BaseChatModel:
    """Get default LLM instance."""
    return get_llm()

async def call_llm_with_structured_output(
    llm: ChatGoogleGenerativeAI,
    output_class: Type[M],
    messages: Union[List[Tuple[str, str]], List[BaseMessage]],
    context_desc: str = "",
) -> Optional[M]:
    """Call LLM with structured output and consistent error handling.

    Args:
        llm: LLM instance
        output_class: Pydantic model for structured output
        messages: Messages to send to the LLM (tuples or BaseMessage objects)
        context_desc: Description for error logs

    Returns:
        Structured output or None if error
    """
    try:
        return await llm.with_structured_output(output_class).ainvoke(messages)
    except Exception as e:
        logger.error(f"Error in LLM call for {context_desc}: {e}")
        return None


async def process_with_voting():
    pass

async def generate_embedding(text: str) -> List[float]:
    """Generate vector embedding for text using Google GenAI."""
    if not settings.google_api_key:
        raise ValueError("GOOGLE_API_KEY must be set in environment variables")
        
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=settings.google_api_key
    )
    
    # embed_query returns a list of floats
    return await embeddings.aembed_query(text)