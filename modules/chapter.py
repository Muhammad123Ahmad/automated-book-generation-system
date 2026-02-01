from sqlalchemy.orm import Session
from sqlalchemy import select
from db import Book, Chapter
import llm_client
import re

def parse_chapters_from_outline(session: Session, book_id: int):
    """
    Parses the approved outline text to create Chapter placeholders in the DB.
    This is a heuristic parser. It expects lines starting with 'Chapter X:'.
    """
    book = session.get(Book, book_id)
    if not book or not book.outline:
        return

    content = book.outline.content
    # Simple regex to find "Chapter <number>: <Title>" or "## Chapter <number>"
    # Adjust regex based on LLM output patterns. 
    # Valid patterns: 
    # "Chapter 1: The Beginning"
    # "1. The Beginning"
    # "**Chapter 1**: The Beginning"
    # "## Chapter 1: The Beginning"
    
    lines = content.split('\n')
    chapter_count = 0
    
    # Regex to match:
    # Optional markdown (#, ##, **, etc)
    # The word "Chapter" (case insensitive) followed by a number
    # OR just a Number followed by a dot
    pattern = re.compile(r'^(?:[#*]+\s*)?(?:chapter\s+(\d+)|(\d+)\.)', re.IGNORECASE)

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        match = pattern.match(line)
        if match:
            # If we matched, it's a chapter line
            chapter_count += 1
            
            # Clean title: Remove the "Chapter X:" part
            # Split by first colon or just take the whole line if not clean
            if ':' in line:
                title = line.split(':', 1)[-1].strip()
            # If no colon, try to strip the number prefix (e.g. "1. Title")
            elif match.group(2) and line.startswith(match.group(2) + '.'):
                 title = line[len(match.group(2))+1:].strip()
            else:
                title = line # Fallback
                
            # Remove trailing markdown
            title = title.replace('*', '').strip()
            
            # Check if exists
            existing = session.execute(
                select(Chapter).where(Chapter.book_id == book_id, Chapter.chapter_number == chapter_count)
            ).scalar_one_or_none()
            
            if not existing:
                new_chapter = Chapter(
                    book_id=book_id,
                    chapter_number=chapter_count,
                    title=title,
                    status="PENDING"
                )
                session.add(new_chapter)
    
    session.commit()
    print(f"Parsed {chapter_count} chapters from outline.")
    
    if chapter_count == 0:
        print("[WARNING] Could not parse any chapters! The outline format might be too unique.")
        print("Raw Outline Content (First 200 chars):")
        print(content[:200])

def generate_next_chapter(session: Session, book_id: int, notes: str = ""):
    """Finds the next pending chapter and generates it."""
    book = session.get(Book, book_id)
    
    # Get all chapters sorted
    chapters = book.chapters
    previous_summaries = []
    
    target_chapter = None
    
    for ch in chapters:
        if ch.status == "APPROVED":
            if ch.summary:
                previous_summaries.append(f"Chapter {ch.chapter_number} Summary: {ch.summary}")
        elif ch.status in ["PENDING", "DRAFT", "WAITING_FOR_REVIEW"] and target_chapter is None:
            target_chapter = ch
            # We found our target, but we keep iterating to build full context if we wanted, 
            # though usually we only need context UP TO this point.
            break
            
    if not target_chapter:
        print("No pending chapters found. Book might be complete.")
        return None

    print(f"Generating Chapter {target_chapter.chapter_number}: {target_chapter.title}...")
    
    # Combine summaries
    context_str = "\n".join(previous_summaries)
    
    content = llm_client.generate_chapter_content(
        book.title,
        target_chapter.title,
        book.outline.content,
        context_str,
        notes
    )
    
    target_chapter.content = content
    target_chapter.status = "WAITING_FOR_REVIEW"
    target_chapter.editor_notes = "" # Reset notes
    session.commit()
    
    return target_chapter

def approve_chapter(session: Session, chapter_id: int):
    """Approves chapter and generates summary."""
    chapter = session.get(Chapter, chapter_id)
    if not chapter:
        return
        
    print("Approving chapter and generating summary...")
    summary = llm_client.summarize_text(chapter.content)
    
    chapter.summary = summary
    chapter.status = "APPROVED"
    session.commit()
    print(f"Chapter {chapter.chapter_number} approved.")

def regenerate_chapter(session: Session, chapter_id: int, notes: str):
    """Regenerates a specific chapter with notes."""
    chapter = session.get(Chapter, chapter_id)
    # Similar to generate, but we already have the object
    # We need to rebuild context (expensive in a real app to query DB again, but fine here)
    book = chapter.book
    
    previous_summaries = []
    for ch in book.chapters:
        if ch.chapter_number < chapter.chapter_number and ch.summary:
            previous_summaries.append(f"Chapter {ch.chapter_number}: {ch.summary}")
            
    context_str = "\n".join(previous_summaries)
    
    print(f"Regenerating Chapter {chapter.chapter_number} with notes: {notes}")
    content = llm_client.generate_chapter_content(
        book.title,
        chapter.title,
        book.outline.content,
        context_str,
        notes
    )
    
    chapter.content = content
    chapter.status = "WAITING_FOR_REVIEW"
    chapter.editor_notes = notes
    session.commit()
    return chapter
