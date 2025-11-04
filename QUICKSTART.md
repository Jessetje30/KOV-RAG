# Quick Start Guide

Get your RAG application up and running in 5 minutes!

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Mistral AI API key ([Get one here](https://console.mistral.ai/))

## Setup Steps

### 1. Configure Environment

```bash
# Copy the environment template
cp .env.example .env

# Edit .env and add your Mistral API key
# You can use nano, vim, or any text editor
nano .env
```

Add your Mistral API key:
```
MISTRAL_API_KEY=your_actual_api_key_here
```

### 2. Start the Application

#### Option A: Using the startup script (Recommended)

```bash
./start.sh
```

This script will:
- Start Qdrant in Docker
- Install dependencies
- Start the backend API
- Start the frontend UI

#### Option B: Manual startup

**Terminal 1 - Start Qdrant:**
```bash
docker-compose up -d
```

**Terminal 2 - Start Backend:**
```bash
cd backend
pip install -r requirements.txt
python main.py
```

**Terminal 3 - Start Frontend:**
```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

### 3. Access the Application

Open your browser and go to:
- **Frontend**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs

### 4. Create an Account

1. Click on the "Register" tab
2. Enter your details (username, email, password)
3. Click "Register"
4. You'll be automatically logged in

### 5. Upload a Document

1. Navigate to "Upload Documents" in the sidebar
2. Click "Browse files" and select a PDF, DOCX, or TXT file
3. Click "Upload and Process"
4. Wait for processing to complete

### 6. Ask Questions

1. Navigate to "Query Documents"
2. Type your question in the text area
3. Click "Submit Query"
4. View the answer and sources!

## Stopping the Application

### Using the stop script:
```bash
./stop.sh
```

### Manual stop:
- Press `Ctrl+C` in each terminal
- Stop Qdrant: `docker-compose down`

## Troubleshooting

### "Cannot connect to backend server"
- Make sure the backend is running on http://localhost:8000
- Check: `curl http://localhost:8000/health`

### "Qdrant connection error"
- Verify Qdrant is running: `docker ps`
- Check logs: `docker-compose logs qdrant`

### "Invalid API key"
- Verify your Mistral API key in `.env`
- Check you have credits at https://console.mistral.ai/

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the [API documentation](http://localhost:8000/docs)
- Try different types of documents
- Experiment with different query styles

## Example Workflow

1. **Register/Login**
   - Create account: username "john", email "john@example.com"

2. **Upload Documents**
   - Upload a research paper (PDF)
   - Upload meeting notes (DOCX)
   - Upload a text file (TXT)

3. **Query Examples**
   - "What are the main findings in the research paper?"
   - "Summarize the key points from the meeting notes"
   - "What does the document say about [specific topic]?"

4. **View Sources**
   - See which document chunks were used
   - Check relevance scores
   - Verify the answer against source text

Enjoy using your RAG application!
