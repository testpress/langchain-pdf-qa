# 📄 LangChain PDF Q&A

Ask questions from any PDF using OpenAI + LangChain + Chroma.

This project lets you upload a PDF and ask natural language questions about its content. It uses:
- [LangChain](https://github.com/langchain-ai/langchain)
- [OpenAI API](https://platform.openai.com/)
- [Chroma Vector Store](https://www.trychroma.com/)

---

## 🔧 Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourname/langchain-pdf-qa.git
cd langchain-pdf-qa
```

### 2. Install uv (if not already installed)

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

### 3. Install dependencies

```bash
uv sync
```

### 3. Add your OpenAI API key

Create a `.env` file based on the example:

```bash
cp .env.example .env
```

Then edit `.env` and replace with your API key.

---

## ▶️ Run the Q\&A CLI

```bash
uv run python ask_pdf.py
```

Place a PDF file (e.g., `example.pdf`) in the root and run the script. You’ll be prompted to ask questions like:

* "What is this document about?"
* "Who is the author?"
* "Summarize the key findings."

Type `exit` to quit.

---

## 🧪 Example

```text
Ask a question (or type 'exit'): What is the main purpose of this document?

Answer: This document provides an overview of ...
```

---

## 📁 Project Structure

```
.
├── ask_pdf.py
├── example.pdf        # Your PDF file (not committed)
├── .env               # Your API key (not committed)
├── .env.example
├── pyproject.toml
├── README.md
├── .gitignore
```

---

## 🛡️ Note

Do not commit your `.env` file or PDF files to GitHub. Use `.gitignore` to keep them private.

---

## 💡 Ideas for Extension

* Add a Streamlit or Flask UI
* Use FAISS or Pinecone as vector store
* Deploy to Hugging Face Spaces or Render

---

## 🛠️ Development with uv

This project uses [uv](https://github.com/astral-sh/uv) for dependency management and Python environment handling.

### Common uv commands:

```bash
# Install dependencies
uv sync

# Run a script
uv run python ask_pdf.py

# Add a new dependency
uv pip install package-name

# Remove a dependency
uv pip uninstall package-name

# Update dependencies
uv sync --upgrade

# Run tests
uv run python -m pytest

# Activate the virtual environment (if needed)
source .venv/bin/activate
```

### Why uv?

- **Fast**: Much faster than pip and Poetry
- **Reliable**: Better dependency resolution
- **Simple**: Single tool for environment management, dependency installation, and running scripts
- **Modern**: Built for Python 3.13+ with modern tooling

---

## 🧑‍💻 License

MIT — free to use and modify.
