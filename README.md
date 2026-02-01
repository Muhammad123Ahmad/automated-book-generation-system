# Automated AI Book Generation System 📚🤖

A powerful, modular AI agent built with **Python**, **Streamlit**, and **Groq (LLM)**. This system allows a human "Editor" to collaborate with an AI "Ghostwriter" to create full-length books from scratch, ensuring high quality through a **Human-in-the-Loop** review process.

## 🚀 Key Features

*   **Modular Workflow**: Separate stages for Planning, Writing, and Compilation.
*   **Human-in-the-Loop**: Pause at every step (Outline, Chapter) for user feedback and approval.
*   **Context Awareness**: The AI reads summaries of *previous* chapters before writing the *next* one, ensuring plot continuity.
*   **Database Backed**: Uses SQLite (adaptable to Supabase) to persist work between sessions.
*   **Real-time Notifications**: In-app toasts and sidebar logs keep you updated on AI progress.
*   **Export**: Compiles the finished book into a downloadable text file.

## 🛠️ Tech Stack

*   **Language**: Python 3.10+
*   **Interface**: Streamlit
*   **Database**: SQLite (SQLAlchemy ORM)
*   **AI Model**: Groq API (Llama 3 / Mixtral)
*   **Notifications**: Custom Module (Console + Streamlit Toast + SMTP Support)

## 📦 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Muhammad123Ahmad/automated-book-generation-system.git
    cd automated-book-generation-system
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Environment Variables**:
    Create a `.env` file in the root directory:
    ```ini
    GROQ_API_KEY=gsk_your_api_key_here
    LOG_LEVEL=INFO
    # Optional: SMTP Settings for Email Notifications
    # SMTP_SERVER=smtp.gmail.com
    # SMTP_USER=your_email@gmail.com
    # ...
    ```

4.  **Run the App**:
    ```bash
    streamlit run app.py
    ```

## 📖 How to Use

1.  **Start a Book**: Enter a Title and Concept (e.g., "A sci-fi mystery on Mars").
2.  **Outline Phase**: The AI generates a chapter list. You can Approve it or Request Changes.
3.  **Writing Phase**: 
    *   Click **"Generate Chapter"**. The AI writes based on the outline + previous chapter context.
    *   Review the text. If you like it, click **"Approve"**. If not, add notes and "Regenerate".
4.  **Compile**: Once all chapters are done, click **"Compile Final Book"** to download your work.

## 🏗️ Project Structure

*   `app.py`: Main Streamlit Interface.
*   `db.py`: Database models (Book, Outline, Chapter).
*   `llm_client.py`: Wrapper for Groq API calls (Generation & Summarization).
*   `modules/`:
    *   `outline.py`: Logic for creating/refining outlines.
    *   `chapter.py`: Logic for context management and chapter generation.
    *   `notifications.py`: Handles alerts (Toasts/Logs).
    *   `book_compiler.py`: Stitches approved chapters into final file.

---
*Created for the Kickstart AI Challenge.*
