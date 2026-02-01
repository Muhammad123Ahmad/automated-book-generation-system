import streamlit as st
import sys
import os
import time

# Add current dir to path
sys.path.append(os.getcwd())

from db import init_db, get_session, Book, Chapter
from sqlalchemy import select
from modules import outline, chapter, book_compiler

# Page Config
st.set_page_config(page_title="AI Book Generator", layout="wide")

# Initialize DB
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

def get_db():
    return get_session()

# Sidebar: Book Selection
st.sidebar.title("📚 Book Manager")

# Create New Book
with st.sidebar.expander("Start New Book", expanded=False):
    new_title = st.text_input("Title")
    new_notes = st.text_area("Concept / Notes")
    if st.button("Create Book"):
        if new_title:
            with get_db() as session:
                book = Book(title=new_title, status="PLANNING")
                session.add(book)
                session.commit()
                st.success(f"Created '{new_title}'!")
                # Attempt to generate outline immediately
                outline.create_initial_outline(session, book.id, new_notes)
                st.rerun()

# List Books
st.sidebar.markdown("---")
st.sidebar.subheader("Your Library")

with get_db() as session:
    books = session.execute(select(Book).order_by(Book.id.desc())).scalars().all()
    
    if not books:
        st.sidebar.info("No books yet.")
        selected_book_id = None
    else:
        book_options = {b.id: f"{b.title} ({b.status})" for b in books}
        selected_book_id = st.sidebar.radio(
            "Select a Book:",
            options=books,
            format_func=lambda x: f"{x.title}",
            key="selected_book_obj"
        ).id
        
        st.sidebar.markdown("---")
        if st.sidebar.button("❌ Delete Selected Book", type="primary"):
            with get_db() as session:
                b_to_del = session.get(Book, selected_book_id)
                session.delete(b_to_del)
                session.commit()
                st.sidebar.success(f"Deleted '{b_to_del.title}'")
                time.sleep(1)
                st.rerun()
        
    with st.sidebar.expander("🛠️ Database Inspector"):
        if st.checkbox("Show Raw Tables"):
            st.subheader("Books Table")
            st.dataframe([{"ID": b.id, "Title": b.title, "Status": b.status} for b in books])
            
            if selected_book_id:
                st.subheader("Chapters Table")
                with get_db() as session:
                   chaps = session.get(Book, selected_book_id).chapters
                   st.dataframe([{"#": c.chapter_number, "Title": c.title, "Status": c.status} for c in chaps])

    # Persistent Notification Log
    st.sidebar.markdown("---")
    with st.sidebar.expander("🔔 Notification Log"):
        if 'notification_log' in st.session_state and st.session_state['notification_log']:
            for msg in reversed(st.session_state['notification_log'][-5:]): # Show last 5
                st.text(msg)
            if st.sidebar.button("Clear Log"):
                st.session_state['notification_log'] = []
                st.rerun()
        else:
            st.caption("No recent notifications.")

# Main Content Area
if selected_book_id:
    with get_db() as session:
        # Refresh book object attached to this session
        book = session.get(Book, selected_book_id)
        
        st.title(f"📖 {book.title}")
        st.markdown(f"**Status:** `{book.status}`")
        st.divider()
        
        # --- PLANNING PHASE ---
        if book.status == "PLANNING":
            st.subheader("📝 Outline Phase")
            
            if not book.outline:
                st.warning("No outline found. Generating now...")
                with st.spinner("Generating outline..."):
                    outline.create_initial_outline(session, book.id, "Auto-generated")
                    st.rerun()
            
            st.text_area("Current Outline", book.outline.content, height=400)
            
            col1, col2 = st.columns([1, 2])
            with col1:
                if st.button("✅ Approve Outline", type="primary"):
                    outline.approve_outline(session, book.id)
                    with st.spinner("Parsing chapters..."):
                        chapter.parse_chapters_from_outline(session, book.id)
                    st.success("Outline approved! Moving to Writing phase.")
                    st.rerun()
            
            with col2:
                notes = st.text_input("Feedback for AI (if requesting changes):", placeholder="E.g. Make it strictly 5 chapters.")
                if st.button("🔄 Request Changes"):
                    if notes:
                        with st.spinner("Refining outline..."):
                            outline.update_outline_with_feedback(session, book.id, notes)
                        st.rerun()
                    else:
                        st.error("Please enter feedback notes first.")

        # --- WRITING PHASE ---
        elif book.status == "WRITING_CHAPTERS":
            st.subheader("✍️ Writing Phase")
            
            # Show Chapter Progress
            chapters = book.chapters
            if not chapters:
                st.error("No chapters found! Parsing error?")
                if st.button("Retry Parsing"):
                    chapter.parse_chapters_from_outline(session, book.id)
                    st.rerun()
            else:
                completed = sum(1 for c in chapters if c.status == "APPROVED")
                total = len(chapters)
                progress = completed / total if total > 0 else 0
                st.progress(progress, text=f"Progress: {completed}/{total} Chapters")
                
                # Find active chapter
                current_chapter = next((c for c in chapters if c.status != "APPROVED"), None)
                
                if not current_chapter:
                    # All done
                    st.success("🎉 All chapters written!")
                    if st.button("Compile Final Book", type="primary"):
                        book_compiler.compile_book(session, book.id)
                        st.rerun()
                else:
                    st.markdown(f"### Current: Chapter {current_chapter.chapter_number} - {current_chapter.title}")
                    st.caption(f"Status: {current_chapter.status}")
                    
                    if current_chapter.status == "PENDING":
                        notes = st.text_input("Notes for this chapter (optional):")
                        if st.button("✨ Generate Chapter content"):
                            with st.spinner("Writing chapter..."):
                                chapter.generate_next_chapter(session, book.id, notes)
                                st.toast(f"Generated Chapter {current_chapter.chapter_number}", icon="✅")
                                time.sleep(1) # Wait for toast
                            st.rerun()
                            
                    elif current_chapter.status in ["WAITING_FOR_REVIEW", "DRAFT"]:
                        st.markdown("#### Review Content")
                        st.text_area("Chapter Content", current_chapter.content, height=600)
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✅ Approve Chapter", type="primary"):
                                with st.spinner("Summarizing and saving..."):
                                    chapter.approve_chapter(session, current_chapter.id)
                                    st.toast("Chapter Approved!", icon="🎉")
                                    time.sleep(1)
                                st.rerun()
                        with c2:
                            feedback = st.text_input("Refinement Notes:")
                            if st.button("🔄 Rewrite Chapter"):
                                if feedback:
                                    with st.spinner("Rewriting..."):
                                        chapter.regenerate_chapter(session, current_chapter.id, feedback)
                                    st.rerun()
                                else:
                                    st.warning("Enter notes.")

        # --- COMPLETED PHASE ---
        elif book.status == "COMPLETED":
            st.success("Analysis Complete. Book is ready.")
            st.balloons()
            
            compile_path = f"{book.title.replace(' ', '_')}_Final.txt"
            full_path = os.path.abspath(compile_path)
            
            if os.path.exists(full_path):
                with open(full_path, "r", encoding='utf-8') as f:
                    data = f.read()
                
                st.download_button(
                    label="📥 Download Book (.txt)",
                    data=data,
                    file_name=compile_path,
                    mime="text/plain"
                )
                
                st.text_area("Preview", data, height=500)
            else:
                st.error("File not found on disk. Re-compile?")
                if st.button("Re-compile"):
                    book_compiler.compile_book(session, book.id)
                    st.rerun()

else:
    st.info("👈 Select a book from the sidebar or Create a New One.")
