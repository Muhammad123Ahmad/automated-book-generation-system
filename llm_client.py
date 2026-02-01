import os
import logging
from typing import Optional
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Initialize Groq Client
api_key = os.getenv("GROQ_API_KEY")
client = None

if api_key:
    client = Groq(api_key=api_key)
else:
    logger.warning("GROQ_API_KEY not found in environment variables.")

MODEL_NAME = "openai/gpt-oss-20b" # Updated to supported model

def generate_outline_from_llm(title: str, notes: str) -> str:
    """Generate a book outline based on title and notes."""
    if not client:
        return "Error: GROQ_API_KEY not set."
    
    prompt = f"""
    You are an expert book editor and ghostwriter.
    Create a detailed, chapter-by-chapter outline for a book titled: "{title}".
    
    Additional Author Notes:
    {notes}
    
    Format:
    - Provide a list of Chapters (1 to N).
    - For each chapter, provide a Title and a brief 1-sentence description.
    - Do not write the chapters yet.
    - Output ONLY the outline.
    """
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a professional book outliner."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating outline: {e}")
        return f"Error creating outline: {str(e)}"

def regenerate_outline_from_llm(current_outline: str, feedback: str) -> str:
    """Refine existing outline based on feedback."""
    if not client:
        return "Error: GROQ_API_KEY not set."
        
    prompt = f"""
    Current Outline:
    {current_outline}
    
    Editor Feedback needed for revisions:
    {feedback}
    
    Please rewrite the outline satisfying the feedback. Keep the structure clear.
    """
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a professional book editor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error updating outline: {e}")
        return f"Error updating outline: {str(e)}"

def generate_chapter_content(book_title: str, chapter_title: str, outline_context: str, previous_summaries: str, notes: Optional[str] = "") -> str:
    """Generate full text for a chapter."""
    if not client:
        return "Error: GROQ_API_KEY not set."

    context_str = ""
    if previous_summaries:
        context_str = f"STORY SO FAR (Summaries of previous chapters):\n{previous_summaries}\n"
    else:
        context_str = "This is the first chapter.\n"

    prompt = f"""
    Book Title: {book_title}
    Current Chapter: {chapter_title}
    
    Full Book Outline Reference:
    {outline_context}
    
    Context:
    {context_str}
    
    Specific Author Notes for this Chapter:
    {notes if notes else "None"}
    
    Task:
    Write the complete content for '{chapter_title}'. 
    Write in an engaging style suitable for the topic.
    Ensure continuity with previous chapters.
    """

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a best-selling author."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8, # Slightly higher for creativity
            max_tokens=6000 # Allow for long chapters
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating chapter: {e}")
        return f"Error generating chapter: {str(e)}"

def summarize_text(text: str) -> str:
    """Create a concise summary of the chapter for context window."""
    if not client:
        return "Error: GROQ_API_KEY not set."
        
    prompt = f"""
    Summarize the following chapter content into a concise paragraph (approx 150 words). 
    Focus on key plot points or information that is necessary for future context.
    
    Content:
    {text[:15000]} # Truncate just in case, though usually not needed if chunking 
    """ # Note: Llama 3 has a large context, but good to be safe.
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a summarizer bot."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error summarizing: {e}")
        return f"Error summarizing: {str(e)}"
