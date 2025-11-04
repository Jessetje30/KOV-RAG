# 🚀 RAG Chat Interface Implementation Plan
**Perplexity-Style Conversational Chat met User-Level Privacy**

## 📋 Executive Summary

Dit plan implementeert een volledige chat interface met:
- ✅ **User-isolated chat sessions** (architect ziet aannemer's chats NIET)
- ✅ **Inline citations [1][2][3]** zoals Perplexity
- ✅ **Conversation history** met context
- ✅ **Session management** (create, list, delete)
- ✅ **Modern chat UI** in Streamlit

---

## ✅ Reeds Voltooid

### Database Schema (database.py)
- [x] `ChatSessionDB` model met user_id foreign key
- [x] `ChatMessageDB` model met role, content, sources (JSON)
- [x] `ChatRepository` klasse met volledige CRUD operaties
- [x] User relationships in `UserDB`

**Privacy:** Alle database operaties hebben user_id verificatie!

---

## 🔨 Implementatie Stappen

### STAP 1: Pydantic Models Toevoegen

**Bestand:** `backend/models.py`

**Locatie:** Aan het einde van het bestand toevoegen

```python
# Chat Models
class ChatMessage(BaseModel):
    """Model for chat message."""
    role: str = Field(..., regex="^(user|assistant)$")
    content: str = Field(..., min_length=1)
    sources: Optional[List[dict]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatSessionCreate(BaseModel):
    """Model for creating a chat session."""
    title: str = Field(..., min_length=1, max_length=200)


class ChatSession(BaseModel):
    """Model for chat session."""
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[ChatMessage]] = []

    class Config:
        from_attributes = True


class ChatSessionList(BaseModel):
    """Model for list of chat sessions."""
    sessions: List[ChatSession]
    total_count: int


class ChatQueryRequest(BaseModel):
    """Model for chat query request."""
    session_id: Optional[int] = None  # None = create new session
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=100, ge=1, le=200)


class Citation(BaseModel):
    """Model for inline citation."""
    number: int
    text: str
    document_id: str
    filename: str
    chunk_index: int
    score: float


class ChatQueryResponse(BaseModel):
    """Model for chat query response."""
    session_id: int
    answer: str
    citations: List[Citation]
    processing_time_seconds: float
    message_id: int
```

---

### STAP 2: RAG Inline Citations Update

**Bestand:** `backend/rag.py`

**Functie:** `query()` methode aanpassen

**Huidige locatie:** Regel ~522-627

**Nieuwe implementatie:**

```python
def query(
    self,
    user_id: int,
    query_text: str,
    top_k: int = 5
) -> Tuple[str, List[Dict[str, Any]], float]:
    """
    Query the RAG system: retrieve relevant chunks and generate answer with inline citations.

    Args:
        user_id: User ID
        query_text: Query text
        top_k: Number of top results to retrieve

    Returns:
        Tuple containing:
            - Generated answer with inline citations (str)
            - List of source chunks with citation numbers (List[Dict])
            - Processing time in seconds (float)

    Raises:
        ValueError: If no documents found for user
    """
    start_time = time.time()

    # Ensure collection exists
    collection_name = self._get_collection_name(user_id)
    collections = self.qdrant_client.get_collections().collections
    collection_names = [col.name for col in collections]

    if collection_name not in collection_names:
        raise ValueError("No documents found. Please upload documents first.")

    # Get query embedding
    query_embedding = self._get_embeddings([query_text])[0]

    # Search in Qdrant
    search_results = self.qdrant_client.search(
        collection_name=collection_name,
        query_vector=query_embedding,
        limit=top_k,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                )
            ]
        )
    )

    if not search_results:
        raise ValueError("No relevant documents found for your query.")

    # Extract source chunks with score filtering
    SIMILARITY_THRESHOLD = 0.5
    sources = []
    context_texts = []

    for result in search_results:
        # Filter on similarity score
        if result.score >= SIMILARITY_THRESHOLD:
            source = {
                "text": result.payload["text"],
                "document_id": result.payload["document_id"],
                "filename": result.payload["filename"],
                "score": result.score,
                "chunk_index": result.payload["chunk_index"]
            }
            sources.append(source)
            context_texts.append(result.payload["text"])

    # If no chunks above threshold, use top 3 best
    if not sources and search_results:
        logger.warning(f"No chunks above threshold {SIMILARITY_THRESHOLD}, using top 3")
        for result in search_results[:3]:
            source = {
                "text": result.payload["text"],
                "document_id": result.payload["document_id"],
                "filename": result.payload["filename"],
                "score": result.score,
                "chunk_index": result.payload["chunk_index"]
            }
            sources.append(source)
            context_texts.append(result.payload["text"])

    # Build context with citation numbers
    context = "\n\n".join([f"[{i+1}] {text}" for i, text in enumerate(context_texts)])

    # Generate answer using LLM with citation instruction
    prompt = f"""Answer the question based on the context below. You MUST cite sources using inline citations [1], [2], etc. whenever you reference information.

Place the citation number [X] immediately after the relevant sentence or claim. Use multiple citations if combining information from multiple sources.

Context:
{context}

Question: {query_text}

Answer (with inline citations):"""

    answer = self.llm_provider.generate_answer(prompt, max_length=1024)

    # Add citation numbers to sources for frontend
    for i, source in enumerate(sources):
        source["citation_number"] = i + 1

    processing_time = time.time() - start_time

    return answer, sources, processing_time
```

---

### STAP 3: Chat Endpoints Toevoegen

**Bestand:** `backend/main.py`

**Import toevoegen bovenaan:**

```python
from database import ChatRepository, ChatSessionDB, ChatMessageDB
from models import (
    # ... existing imports ...
    ChatSessionCreate,
    ChatSession,
    ChatSessionList,
    ChatMessage,
    ChatQueryRequest,
    ChatQueryResponse,
    Citation
)
```

**Endpoints toevoegen (na de huidige query endpoint):**

```python
# ==========================================
# CHAT ENDPOINTS
# ==========================================

@app.post("/api/chat/sessions", response_model=ChatSession, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new chat session.

    Args:
        session_data: Session title
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChatSession: Created session
    """
    try:
        session = ChatRepository.create_session(
            db=db,
            user_id=current_user.id,
            title=session_data.title
        )

        logger.info(f"Chat session created by {current_user.username}: {session.id}")

        return ChatSession(
            id=session.id,
            user_id=session.user_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            messages=[]
        )

    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
        )


@app.get("/api/chat/sessions", response_model=ChatSessionList)
async def list_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all chat sessions for current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChatSessionList: List of user's chat sessions
    """
    try:
        sessions_db = ChatRepository.get_user_sessions(db=db, user_id=current_user.id)

        sessions = []
        for session in sessions_db:
            # Get message count
            messages = ChatRepository.get_session_messages(db=db, session_id=session.id, user_id=current_user.id)

            sessions.append(ChatSession(
                id=session.id,
                user_id=session.user_id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
                messages=[]  # Don't load all messages for list view
            ))

        return ChatSessionList(sessions=sessions, total_count=len(sessions))

    except Exception as e:
        logger.error(f"Error listing chat sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat sessions"
        )


@app.get("/api/chat/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific chat session with all messages.

    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChatSession: Session with messages
    """
    try:
        session = ChatRepository.get_session(db=db, session_id=session_id, user_id=current_user.id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )

        # Get all messages
        messages_db = ChatRepository.get_session_messages(db=db, session_id=session_id, user_id=current_user.id)

        messages = [
            ChatMessage(
                role=msg.role,
                content=msg.content,
                sources=msg.sources,
                created_at=msg.created_at
            )
            for msg in messages_db
        ]

        return ChatSession(
            id=session.id,
            user_id=session.user_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            messages=messages
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat session"
        )


@app.delete("/api/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a chat session.

    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Success message
    """
    try:
        success = ChatRepository.delete_session(db=db, session_id=session_id, user_id=current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )

        logger.info(f"Chat session deleted by {current_user.username}: {session_id}")

        return {"message": "Chat session deleted successfully", "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete chat session"
        )


@app.post("/api/chat/query", response_model=ChatQueryResponse)
async def chat_query(
    query_data: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message in chat and get AI response.

    Args:
        query_data: Query request with optional session_id
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChatQueryResponse: Answer with citations and session info
    """
    try:
        # Create new session if needed
        if query_data.session_id is None:
            # Generate title from first few words of query
            title = query_data.query[:50] + ("..." if len(query_data.query) > 50 else "")
            session = ChatRepository.create_session(
                db=db,
                user_id=current_user.id,
                title=title
            )
            session_id = session.id
        else:
            # Verify session belongs to user
            session = ChatRepository.get_session(
                db=db,
                session_id=query_data.session_id,
                user_id=current_user.id
            )
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat session not found"
                )
            session_id = query_data.session_id

        # Save user message
        ChatRepository.add_message(
            db=db,
            session_id=session_id,
            role="user",
            content=query_data.query,
            sources=None
        )

        # Execute RAG query
        answer, sources, processing_time = rag_pipeline.query(
            user_id=current_user.id,
            query_text=query_data.query,
            top_k=query_data.top_k
        )

        # Convert sources to citations
        citations = [
            Citation(
                number=source["citation_number"],
                text=source["text"],
                document_id=source["document_id"],
                filename=source["filename"],
                chunk_index=source["chunk_index"],
                score=source["score"]
            )
            for source in sources
        ]

        # Save assistant message
        assistant_message = ChatRepository.add_message(
            db=db,
            session_id=session_id,
            role="assistant",
            content=answer,
            sources=[c.dict() for c in citations]
        )

        logger.info(f"Chat query by {current_user.username} in session {session_id}")

        return ChatQueryResponse(
            session_id=session_id,
            answer=answer,
            citations=citations,
            processing_time_seconds=round(processing_time, 2),
            message_id=assistant_message.id
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Chat query error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat query"
        )
```

---

### STAP 4: Frontend Chat Interface

**Bestand:** `frontend/app.py`

**Nieuwe functie toevoegen (vervang de huidige `show_query_page`):**

```python
# Page: Query Documents (Chat Interface)
def show_query_page():
    """Display chat interface for querying documents."""
    st.markdown('<div class="main-header">Chat with Your Documents</div>', unsafe_allow_html=True)

    # Check if user has documents
    documents_response = api_request("/api/documents", auth=True)
    has_documents = documents_response and documents_response.get("total_count", 0) > 0

    if not has_documents:
        st.warning("You haven't uploaded any documents yet. Go to 'Upload Documents' to add some.")
        return

    # Initialize session state
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []

    # Sidebar: Session Management
    with st.sidebar:
        st.markdown("### 💬 Chat Sessions")

        # New chat button
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.current_session_id = None
            st.session_state.chat_messages = []
            st.rerun()

        st.markdown("---")

        # List existing sessions
        sessions_response = api_request("/api/chat/sessions", auth=True)
        if sessions_response:
            sessions = sessions_response.get("sessions", [])

            if sessions:
                st.markdown("**Your Chats:**")
                for session in sessions:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if st.button(
                            f"💬 {session['title'][:30]}...",
                            key=f"sess_{session['id']}",
                            use_container_width=True
                        ):
                            # Load session
                            session_data = api_request(
                                f"/api/chat/sessions/{session['id']}",
                                auth=True
                            )
                            if session_data:
                                st.session_state.current_session_id = session['id']
                                st.session_state.chat_messages = session_data.get('messages', [])
                                st.rerun()

                    with col2:
                        if st.button("🗑️", key=f"del_{session['id']}"):
                            # Delete session
                            api_request(
                                f"/api/chat/sessions/{session['id']}",
                                method="DELETE",
                                auth=True
                            )
                            if st.session_state.current_session_id == session['id']:
                                st.session_state.current_session_id = None
                                st.session_state.chat_messages = []
                            st.rerun()

    # Main chat area
    st.markdown("""
    <div class="info-box">
        <strong>🤖 Model:</strong> OpenAI GPT-5<br>
        <strong>📊 Embeddings:</strong> text-embedding-3-large<br>
        <strong>💡 Tip:</strong> Citations appear as [1], [2], [3] in responses
    </div>
    """, unsafe_allow_html=True)

    # Display chat history
    for message in st.session_state.chat_messages:
        if message['role'] == 'user':
            st.markdown(f"**👤 You:** {message['content']}")
        else:
            st.markdown(f"**🤖 Assistant:** {message['content']}")

            # Display citations if available
            if message.get('sources'):
                with st.expander("📚 View Sources"):
                    for source in message['sources']:
                        st.markdown(f"**[{source['number']}]** {source['filename']} (Score: {source['score']:.3f})")
                        st.markdown(f'<div class="source-box">{source["text"]}</div>', unsafe_allow_html=True)
                        st.markdown("---")

        st.markdown("---")

    # Chat input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Your message:",
            placeholder="Ask a question about your documents...",
            height=100,
            key="chat_input"
        )

        submitted = st.form_submit_button("Send", use_container_width=True)

        if submitted and user_input.strip():
            # Add user message to display
            st.session_state.chat_messages.append({
                'role': 'user',
                'content': user_input
            })

            # Send query to backend
            with st.spinner("Thinking..."):
                response = api_request(
                    "/api/chat/query",
                    method="POST",
                    data={
                        "session_id": st.session_state.current_session_id,
                        "query": user_input,
                        "top_k": 100
                    },
                    auth=True
                )

                if response:
                    # Update session ID if new
                    if st.session_state.current_session_id is None:
                        st.session_state.current_session_id = response['session_id']

                    # Add assistant message to display
                    st.session_state.chat_messages.append({
                        'role': 'assistant',
                        'content': response['answer'],
                        'sources': response.get('citations', [])
                    })

                    st.rerun()
```

---

## 🧪 Testing Checklist

### Privacy Testing
- [ ] User A creates chat session
- [ ] User B logs in
- [ ] User B cannot see User A's sessions in API call
- [ ] User B cannot access User A's session by ID (404 error)
- [ ] User B cannot delete User A's session (404 error)

### Functional Testing
- [ ] Create new chat session
- [ ] Send message in new session (auto-creates session)
- [ ] View chat history in session
- [ ] Switch between sessions
- [ ] Delete chat session
- [ ] Inline citations [1][2][3] appear in answers
- [ ] Click citations to view sources
- [ ] Sources grouped by document

### Performance Testing
- [ ] Load 10+ chat sessions (should be fast)
- [ ] Send 20 messages in one session (history loads correctly)
- [ ] Large response with 10+ citations (renders properly)

---

## 🔄 Database Migration

**Run after implementing all code:**

```bash
cd /Users/jesse/PycharmProjects/fontysRAG/rag-app/backend

# Stop backend
lsof -ti:8000 | xargs kill -9

# Backup existing database (IMPORTANT!)
cp rag_app.db rag_app.db.backup

# Start Python and create new tables
python3 << EOF
from database import init_db
init_db()
print("✅ Chat tables created successfully!")
EOF

# Restart backend
source venv/bin/activate && python main.py
```

---

## 📝 Implementation Order

1. **Backend First (60 min)**
   - [x] Database (already done)
   - [ ] Pydantic models (5 min)
   - [ ] RAG inline citations (10 min)
   - [ ] Chat endpoints (30 min)
   - [ ] Test endpoints with curl/Postman (15 min)

2. **Frontend Second (45 min)**
   - [ ] Chat interface function (30 min)
   - [ ] Test in browser (15 min)

3. **Testing (30 min)**
   - [ ] Privacy testing
   - [ ] Functional testing
   - [ ] Performance testing

**Total Time: ~2.5 hours**

---

## 🚨 Important Notes

1. **Privacy is Built-In**: Alle chat operaties filteren op `user_id` in de database
2. **Inline Citations**: GPT-5 wordt geïnstrueerd om [1][2][3] te gebruiken
3. **Session Management**: Streamlit session_state houdt chat bij
4. **Auto-Create**: Als `session_id=None`, wordt automatisch nieuwe chat gemaakt

---

## 🎯 Success Criteria

✅ Chat interface lijkt op Perplexity
✅ Architect kan aannemer's chats NIET zien
✅ Inline citations [1][2][3] in antwoorden
✅ Sources klikbaar en gegroepeerd
✅ Chat history persistent
✅ Multiple sessions per user

---

## 📞 Support

Als je tegen problemen aanloopt:
1. Check backend logs: `tail -f backend.log`
2. Check database: `sqlite3 rag_app.db` → `.tables` → `.schema chat_sessions`
3. Test API: `curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/chat/sessions`

Good luck! 🚀
