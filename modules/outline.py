from sqlalchemy.orm import Session
from db import Book, Outline
import llm_client

def create_initial_outline(session: Session, book_id: int, notes: str) -> Outline:
    """Generates the first draft of an outline."""
    book = session.get(Book, book_id)
    if not book:
        raise ValueError("Book not found")

    print(f"Generating outline for '{book.title}'... (This may take a moment)")
    outline_content = llm_client.generate_outline_from_llm(book.title, notes)
    
    # Check if outline already exists, if so update, else create
    if book.outline:
        book.outline.content = outline_content
        book.outline.status = "waiting_for_review"
        book.outline.editor_notes = "" # Reset notes
        outline = book.outline
    else:
        outline = Outline(book_id=book_id, content=outline_content, status="waiting_for_review")
        session.add(outline)
    
    session.commit()
    return outline

def update_outline_with_feedback(session: Session, book_id: int, notes: str) -> Outline:
    """Regenerates outline based on user feedback."""
    book = session.get(Book, book_id)
    if not book or not book.outline:
        raise ValueError("Outline not found")

    print(f"Refining outline for '{book.title}'...")
    new_content = llm_client.regenerate_outline_from_llm(book.outline.content, notes)
    
    book.outline.content = new_content
    book.outline.status = "waiting_for_review"
    book.outline.editor_notes = notes # Keep history if we wanted, but here just replace
    
    session.commit()
    return book.outline

def approve_outline(session: Session, book_id: int):
    """Marks outline as approved and ready for writing."""
    book = session.get(Book, book_id)
    if not book or not book.outline:
        raise ValueError("Outline not found")
        
    book.outline.status = "approved"
    book.status = "WRITING_CHAPTERS"
    session.commit()
    print("Outline approved! Moving to Chapter Generation.")
