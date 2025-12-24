"""
Context Restoration Test - Shows how data flows through the system
This demonstrates: SAVE → STORE → RESTORE with detailed logs
"""

import os
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()

from database.database import SessionLocal, Base
from database.models.conversation import ConversationContext

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def log_section(title):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*100}")
    print(f"  {title}")
    print(f"{'='*100}{Colors.ENDC}\n")

def log_step(step_num, description):
    print(f"{Colors.OKBLUE}[STEP {step_num}]{Colors.ENDC} {Colors.BOLD}{description}{Colors.ENDC}")

def log_info(info):
    print(f"{Colors.OKCYAN}   ℹ️  {info}{Colors.ENDC}")

def log_success(msg):
    print(f"{Colors.OKGREEN}   ✅ {msg}{Colors.ENDC}")

def log_data(title, data):
    print(f"{Colors.WARNING}   📊 {title}:{Colors.ENDC}")
    if isinstance(data, dict):
        print(f"      {json.dumps(data, indent=6)[:300]}...")
    else:
        print(f"      {str(data)[:300]}...")

def log_query(query_desc, result):
    print(f"{Colors.OKBLUE}   🔍 Query: {query_desc}{Colors.ENDC}")
    print(f"      Result: {result}")

# ============================================================================
# PART 1: SAVE CONTEXT (Frontend → Backend → Database)
# ============================================================================

log_section("PART 1: SAVE CONTEXT - Frontend sends data to database")

db = SessionLocal()

try:
    # Step 1: Create test data (simulating frontend)
    log_step(1, "Frontend creates context data")
    
    test_conversation_id = "test-conv-" + str(int(datetime.now().timestamp() * 1000))
    test_user_id = "guest"
    
    # Simulate user messages
    test_messages = [
        {
            "id": "msg-001",
            "role": "user",
            "content": "Tell me about machine learning",
            "type": "chat",
            "timestamp": datetime.now().isoformat() + "Z",
            "tone": "informative",
            "length": "medium"
        },
        {
            "id": "msg-002",
            "role": "assistant",
            "content": "Machine learning is a subset of AI that enables systems to learn and improve from experience...",
            "type": "chat",
            "timestamp": datetime.now().isoformat() + "Z",
        },
        {
            "id": "msg-003",
            "role": "user",
            "content": "What are the types of ML?",
            "type": "chat",
            "timestamp": datetime.now().isoformat() + "Z",
            "tone": "informative",
            "length": "medium"
        },
        {
            "id": "msg-004",
            "role": "assistant",
            "content": "There are three main types: Supervised Learning, Unsupervised Learning, and Reinforcement Learning...",
            "type": "chat",
            "timestamp": datetime.now().isoformat() + "Z",
        }
    ]
    
    test_blog_content = """## Understanding Machine Learning

Machine Learning is revolutionizing how we build intelligent systems. 
It enables computers to learn from data without being explicitly programmed.

### Types of Machine Learning
1. **Supervised Learning** - Learning from labeled data
2. **Unsupervised Learning** - Finding patterns in unlabeled data  
3. **Reinforcement Learning** - Learning through rewards and penalties
"""
    
    log_info(f"Conversation ID: {test_conversation_id}")
    log_info(f"User ID: {test_user_id}")
    log_info(f"Number of messages: {len(test_messages)}")
    log_data("Message structure", test_messages[0])
    
    # Step 2: Create context record (backend processes)
    log_step(2, "Backend receives data and processes it")
    
    # Format chat context
    chat_context = "\n".join([
        f"{m['role'].title()}: {m['content']}"
        for m in test_messages
    ])
    
    # Create full context data
    context_data = {
        "user_id": test_user_id,
        "conversation_id": test_conversation_id,
        "messages": test_messages,
        "current_blog": test_blog_content
    }
    
    log_info("Formatting chat context...")
    log_data("Chat context preview", chat_context[:200])
    
    log_info("Creating context JSON structure...")
    log_success(f"Context data prepared with {len(test_messages)} messages")
    
    # Step 3: Check if context already exists
    log_step(3, "Database: Check if context already exists")
    
    existing = db.query(ConversationContext).filter(
        ConversationContext.conversation_id == test_conversation_id,
        ConversationContext.user_id == test_user_id
    ).first()
    
    if existing:
        log_info("Found existing context - UPDATING")
        log_query("Existing context found", existing.id)
    else:
        log_info("No existing context - CREATING NEW")
        log_success("Will create new ConversationContext record")
    
    # Step 4: Save or update in database
    log_step(4, "Backend saves data to Supabase")
    
    if existing:
        log_info("Updating existing record...")
        existing.messages_context = context_data
        existing.chat_context = chat_context
        existing.blog_context = test_blog_content
        existing.message_count = len(test_messages)
        existing.last_updated_at = datetime.utcnow()
        log_success("Updated existing ConversationContext")
    else:
        log_info("Creating new record...")
        new_context = ConversationContext(
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            messages_context=context_data,
            chat_context=chat_context,
            blog_context=test_blog_content,
            message_count=len(test_messages),
            last_updated_at=datetime.utcnow()
        )
        db.add(new_context)
        log_success("Created new ConversationContext")
    
    # Step 5: Commit to database
    log_step(5, "Backend commits to Supabase database")
    
    log_info("Executing database transaction...")
    db.commit()
    log_success(f"✨ Context saved successfully!")
    log_query("Table", "conversation_contexts")
    log_info(f"Columns stored:")
    log_info(f"  - user_id: '{test_user_id}'")
    log_info(f"  - conversation_id: '{test_conversation_id}'")
    log_info(f"  - messages_context: JSON (4 messages)")
    log_info(f"  - chat_context: TEXT (formatted conversation)")
    log_info(f"  - blog_context: TEXT (blog content)")
    log_info(f"  - message_count: 4")
    log_info(f"  - last_updated_at: {datetime.utcnow().isoformat()}")

    # ============================================================================
    # PART 2: RESTORE CONTEXT (Database → Backend → Frontend)
    # ============================================================================
    
    log_section("PART 2: RESTORE CONTEXT - Loading data from database")
    
    # Step 6: Frontend requests context
    log_step(6, "Frontend requests: GET /v1/context/load/{conversation_id}")
    
    log_info(f"Request parameters:")
    log_info(f"  - conversation_id: {test_conversation_id}")
    log_info(f"  - user_id: {test_user_id}")
    
    # Step 7: Backend queries database
    log_step(7, "Backend queries Supabase for matching context")
    
    log_info("Executing SQL query...")
    print(f"{Colors.WARNING}   SQL:{Colors.ENDC}")
    print(f"      SELECT * FROM conversation_contexts")
    print(f"      WHERE conversation_id = '{test_conversation_id}'")
    print(f"      AND user_id = '{test_user_id}'")
    
    # Load from database
    loaded_context = db.query(ConversationContext).filter(
        ConversationContext.conversation_id == test_conversation_id,
        ConversationContext.user_id == test_user_id
    ).first()
    
    if loaded_context:
        log_success("✨ Found matching context in database!")
        log_query("Record ID", loaded_context.id)
        log_query("Created at", loaded_context.created_at)
        log_query("Last updated", loaded_context.last_updated_at)
    else:
        print(f"{Colors.FAIL}   ❌ ERROR: No context found!{Colors.ENDC}")
        sys.exit(1)
    
    # Step 8: Backend deserializes data
    log_step(8, "Backend deserializes JSON data from database")
    
    log_info("Parsing messages_context from JSON...")
    restored_messages = loaded_context.messages_context.get("messages", [])
    log_success(f"Restored {len(restored_messages)} messages from JSON")
    
    for i, msg in enumerate(restored_messages, 1):
        print(f"{Colors.OKCYAN}      Message {i}: {msg['role']}{Colors.ENDC}")
        print(f"         Content: {msg['content'][:60]}...")
    
    log_info("Loading chat context...")
    restored_chat = loaded_context.chat_context
    log_success("Chat context loaded (formatted conversation)")
    
    log_info("Loading blog context...")
    restored_blog = loaded_context.blog_context
    log_success("Blog context loaded")
    
    # Step 9: Format response for frontend
    log_step(9, "Backend formats response for frontend")
    
    response = {
        "user_id": loaded_context.user_id,
        "conversation_id": loaded_context.conversation_id,
        "messages": restored_messages,
        "chat_context": restored_chat,
        "blog_context": restored_blog,
        "message_count": loaded_context.message_count,
        "last_updated_at": loaded_context.last_updated_at.isoformat()
    }
    
    log_info("Response structure:")
    log_data("Response", {k: str(v)[:50] + "..." if len(str(v)) > 50 else v 
                          for k, v in response.items()})
    
    # Step 10: Frontend receives and restores state
    log_step(10, "Frontend receives response and restores UI state")
    
    print(f"{Colors.OKGREEN}   ✨ UI STATE RESTORATION:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}      1. Restoring chat history...{Colors.ENDC}")
    print(f"         - Messages loaded: {len(response['messages'])}")
    for i, msg in enumerate(response['messages'], 1):
        role_emoji = "👤" if msg['role'] == "user" else "🤖"
        print(f"         {role_emoji} {msg['role']}: {msg['content'][:60]}...")
    
    print(f"\n{Colors.OKCYAN}      2. Rendering blog content...{Colors.ENDC}")
    print(f"         {response['blog_context'][:100]}...")
    
    print(f"\n{Colors.OKCYAN}      3. Updating UI state...{Colors.ENDC}")
    print(f"         - Conversation ID set: {response['conversation_id']}")
    print(f"         - User ID set: {response['user_id']}")
    print(f"         - Message count: {response['message_count']}")
    print(f"         - Last updated: {response['last_updated_at']}")
    
    print(f"\n{Colors.OKGREEN}   ✅ Context restoration COMPLETE!{Colors.ENDC}")
    
    # ============================================================================
    # SUMMARY
    # ============================================================================
    
    log_section("SUMMARY: Complete Context Lifecycle")
    
    print(f"{Colors.BOLD}Frontend → Backend → Database Flow:{Colors.ENDC}\n")
    print(f"1. {Colors.OKCYAN}Frontend{Colors.ENDC}: Creates SaveContextRequest")
    print(f"   └─ conversation_id, user_id, messages, blog_content\n")
    
    print(f"2. {Colors.OKBLUE}Backend{Colors.ENDC}: Processes data (api/v1/context.py)")
    print(f"   ├─ Checks if context exists (query)")
    print(f"   ├─ Formats chat_context (string)")
    print(f"   └─ Creates/Updates ConversationContext\n")
    
    print(f"3. {Colors.WARNING}Database{Colors.ENDC} (Supabase): Stores in conversation_contexts")
    print(f"   ├─ messages_context: JSON")
    print(f"   ├─ chat_context: TEXT")
    print(f"   ├─ blog_context: TEXT")
    print(f"   └─ Timestamps + metadata\n")
    
    print(f"Database → Backend → Frontend Flow:\n")
    
    print(f"1. {Colors.OKCYAN}Frontend{Colors.ENDC}: Requests GET /v1/context/load/:id\n")
    
    print(f"2. {Colors.OKBLUE}Backend{Colors.ENDC}: Queries database")
    print(f"   └─ Loads ConversationContext from DB\n")
    
    print(f"3. {Colors.WARNING}Backend{Colors.ENDC}: Deserializes JSON")
    print(f"   ├─ Parses messages_context")
    print(f"   ├─ Formats response")
    print(f"   └─ Returns ContextResponse\n")
    
    print(f"4. {Colors.OKCYAN}Frontend{Colors.ENDC}: Restores UI")
    print(f"   ├─ Renders chat history")
    print(f"   ├─ Displays blog content")
    print(f"   └─ ✨ User continues where they left off!\n")
    
    print(f"{Colors.OKGREEN}{Colors.BOLD}✅ CONTEXT RESTORATION TEST COMPLETE!{Colors.ENDC}\n")
    
finally:
    db.close()
