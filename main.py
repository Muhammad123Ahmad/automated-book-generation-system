import sys
import os
import time

# Ensure we can import our local modules
sys.path.append(os.getcwd())

from db import init_db, get_session, Book, Outline, Chapter
from sqlalchemy import select
from modules import outline, chapter, book_compiler, notifications

def clear_screen():
    # Simple clear (optional, maybe just print lines to keep history visible for debugging)
    print("\n" * 2)

def print_header():
    print("=" * 50)
    print("   AUTOMATED BOOK GENERATION SYSTEM (AI AGENT)   ")
    print("=" * 50)

def main_menu(session):
    print_header()
    print("1. Start a New Book")
    print("2. Continue Existing Book")
    print("3. Exit")
    
    choice = input("\nSelect an option: ")
    
    if choice == "1":
        create_new_book(session)
    elif choice == "2":
        list_and_select_book(session)
    elif choice == "3":
        print("Goodbye!")
        sys.exit(0)
    else:
        print("Invalid choice.")
        time.sleep(1)
        main_menu(session)

def create_new_book(session):
    print("\n--- NEW BOOK ---")
    title = input("Enter Book Title: ")
    notes = input("Enter Initial Notes/Concept: ")
    
    new_book = Book(title=title, status="PLANNING")
    session.add(new_book)
    session.commit()
    
    print(f"Book '{title}' created!")
    
    # Immediately trigger outline generation
    notifications.send_notification(f"Starting outline generation for: {title}")
    outline.create_initial_outline(session, new_book.id, notes)
    
    manage_book(session, new_book.id)

def list_and_select_book(session):
    print("\n--- EXISTING BOOKS ---")
    books = session.execute(select(Book)).scalars().all()
    
    if not books:
        print("No books found.")
        input("Press Enter to return...")
        main_menu(session)
        return

    for i, b in enumerate(books):
        print(f"{i+1}. {b.title} [{b.status}]")
    
    try:
        idx = int(input("\nSelect book # (or 0 to cancel): "))
        if idx == 0:
            main_menu(session)
            return
        
        selected_book = books[idx-1]
        manage_book(session, selected_book.id)
    except (ValueError, IndexError):
        print("Invalid selection.")
        list_and_select_book(session)

def manage_book(session, book_id):
    while True:
        # Refresh book state
        # using expire_all to ensure fresh data from DB
        session.expire_all() 
        book = session.get(Book, book_id)
        
        clear_screen()
        print(f"MANAGING: {book.title}")
        print(f"STATUS: {book.status}")
        
        if book.status == "PLANNING":
            handle_planning_phase(session, book)
        
        elif book.status == "WRITING_CHAPTERS":
            handle_writing_phase(session, book)
            
        elif book.status == "COMPLETED":
            print("This book is completed!")
            print(f"Outline: {book.outline.status}")
            print(f"Chapters: {len(book.chapters)}")
            input("Press Enter to return to menu...")
            break
        
        else:
            print(f"Unknown status: {book.status}")
            break
            
        # Check if we want to stay in this book loop
        # The handlers will mostly return control here.
        # If a handler returns "EXIT", we break.
        
        cont = input("\nContinue managing this book? (y/n): ")
        if cont.lower() != 'y':
            break

def handle_planning_phase(session, book):
    if not book.outline:
        print("Error: No outline found despite being in PLANNING.")
        return

    print("\n--- OUTLINE STATUS: " + book.outline.status + " ---")
    print(book.outline.content)
    print("-" * 30)
    
    if book.outline.status == "approved":
        # Should have moved to WRITING_CHAPTERS, but update if stuck
        book.status = "WRITING_CHAPTERS"
        session.commit()
        return

    print("\nOptions:")
    print("1. Approve Outline")
    print("2. Request Changes (Add Notes)")
    print("3. Regenerate entirely")
    
    choice = input("Choice: ")
    
    if choice == "1":
        outline.approve_outline(session, book.id)
        notifications.send_notification("Outline Approved. Parsing chapters...")
        chapter.parse_chapters_from_outline(session, book.id)
    elif choice == "2":
        notes = input("Enter feedback notes: ")
        notifications.send_notification("Regenerating outline with feedback...")
        outline.update_outline_with_feedback(session, book.id, notes)
    elif choice == "3":
        # Simple regeneration
        print("Regenerating...")
        outline.create_initial_outline(session, book.id, "Regenerate from scratch")

def handle_writing_phase(session, book):
    # Check for pending chapters
    chapters = book.chapters
    if not chapters:
        print("No chapters found. Did parsing fail?")
        return

    # Find the active chapter (First one not APPROVED)
    current_chapter = None
    for ch in chapters:
        if ch.status != "APPROVED":
            current_chapter = ch
            break
            
    if not current_chapter:
        print("\nALL CHAPTERS APPROVED!")
        print("Ready to compile final book.")
        book_compiler.compile_book(session, book.id)
        return

    print(f"\n--- CURRENT CHAPTER: {current_chapter.chapter_number}. {current_chapter.title} ---")
    print(f"Status: {current_chapter.status}")
    
    if current_chapter.status == "PENDING":
        print("Ready to generate.")
        opt = input("Generate now? (y/n/skip): ")
        if opt == 'y':
            notes = input("Add specific notes for this chapter (optional): ")
            notifications.send_notification(f"Generating Chapter {current_chapter.chapter_number}...")
            chapter.generate_next_chapter(session, book.id, notes)
        elif opt == 'skip':
            # Manual skip/hack if needed
            current_chapter.status = "APPROVED" # Dangerous but useful for debugging
            current_chapter.content = "Skipped"
            current_chapter.summary = "Chapter was skipped."
            session.commit()
            
    elif current_chapter.status in ["WAITING_FOR_REVIEW", "DRAFT"]:
        print("\n--- CONTENT PREVIEW (First 500 chars) ---")
        print(current_chapter.content[:500] + "...\n")
        
        print("Options:")
        print("1. Approve & Continue")
        print("2. Request Changes (Regenerate with Notes)")
        print("3. Edit manually (Not implemented in CLI)")
        
        choice = input("Choice: ")
        
        if choice == "1":
            chapter.approve_chapter(session, current_chapter.id)
            notifications.send_notification(f"Chapter {current_chapter.chapter_number} Approved.")
        elif choice == "2":
            notes = input("Enter feedback notes: ")
            chapter.regenerate_chapter(session, current_chapter.id, notes)

if __name__ == "__main__":
    init_db()
    
    # Check env
    import os
    if "DummyKey" in os.getenv("GROQ_API_KEY", ""):
        print("\n[WARNING] It looks like you are using the Dummy API Key.")
        print("Please update .env with your actual Groq API Key to generate content.")
        print("The system will likely error out on LLM calls otherwise.\n")
    
    with get_session() as session:
        main_menu(session)
