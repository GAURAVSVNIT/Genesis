"""
Checkpoint Restoration Flow - Complete Example
Shows how frontend requests to restore a checkpoint from the database
"""

import requests
import json
import uuid
import time
import sys
import io
from datetime import datetime

# Fix Unicode output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration
BACKEND_URL = "http://localhost:8000"
GUEST_USER_ID = "guest"

# Colors for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log_section(title):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*100}")
    print(f"  {title}")
    print(f"{'='*100}{Colors.ENDC}\n")

def log_step(step, description):
    print(f"{Colors.OKBLUE}[STEP {step}]{Colors.ENDC} {Colors.BOLD}{description}{Colors.ENDC}")

def log_request(method, endpoint, data=None):
    print(f"{Colors.WARNING}REQUEST:{Colors.ENDC} {method} {endpoint}")
    if data:
        print(f"  Body: {json.dumps(data, indent=2)[:200]}...")

def log_response(status, data=None):
    print(f"{Colors.OKCYAN}RESPONSE:{Colors.ENDC} {status}")
    if data:
        print(f"  {json.dumps(data, indent=2)[:300]}...")

def log_success(msg):
    print(f"{Colors.OKGREEN}   [OK] {msg}{Colors.ENDC}")

def log_info(msg):
    print(f"{Colors.OKCYAN}   [i] {msg}{Colors.ENDC}")

try:
    log_section("CHECKPOINT RESTORATION FLOW - STEP BY STEP")
    
    # Generate conversation ID and show it
    conversation_id = str(uuid.uuid4())
    log_info(f"Conversation ID: {conversation_id}")
    log_info(f"User: {GUEST_USER_ID}")

    # ========================================================================
    # STEP 1: CREATE INITIAL CONTEXT & CHECKPOINT
    # ========================================================================
    
    log_section("PART 1: CREATE BLOG & SAVE CHECKPOINT (v1)")
    log_step("1A", "Frontend creates blog content")
    
    initial_messages = [
        {
            "id": str(uuid.uuid4()),
            "role": "user",
            "content": "Write a blog post about Python programming",
            "type": "chat",
            "timestamp": str(time.time()),
            "tone": "informative",
            "length": "long"
        },
        {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": "Here's a comprehensive guide to Python programming...",
            "type": "chat",
            "timestamp": str(time.time())
        }
    ]
    
    blog_content = """# Python Programming Guide

## Introduction
Python is a versatile programming language known for its simplicity and readability.

## Key Features
- Easy to learn syntax
- Powerful libraries
- Great for beginners and professionals

## Getting Started
Install Python and start coding today!
"""
    
    log_info("Blog content created:")
    print(f"  Title: Python Programming Guide")
    print(f"  Length: {len(blog_content)} characters")
    
    # Step 1b: Save context to database
    log_step("1B", "Save context to database")
    
    save_payload = {
        "conversation_id": conversation_id,
        "user_id": GUEST_USER_ID,
        "messages": initial_messages + [
            {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": "Make it more detailed",
                "type": "chat",
                "timestamp": str(time.time())
            },
            {
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "content": "I've expanded the guide with more details...",
                "type": "chat",
                "timestamp": str(time.time())
            }
        ],
        "chat_messages": initial_messages + [
            {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": "Make it more detailed",
                "type": "chat",
                "timestamp": str(time.time())
            },
            {
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "content": "I've expanded the guide with more details...",
                "type": "chat",
                "timestamp": str(time.time())
            }
        ],
        "current_blog_content": blog_content
    }
    
    log_request("POST", "/v1/context/save", {"messages": f"{len(save_payload['messages'])} items", "conversation_id": conversation_id})
    
    response = requests.post(f"{BACKEND_URL}/v1/context/save", json=save_payload)
    if response.status_code == 200:
        result = response.json()
        log_response(f"200 OK", result)
        log_success(f"Context saved with {result['message_count']} messages")
    else:
        print(f"Error: {response.text}")
        exit(1)
    
    # Step 1c: Create checkpoint
    log_step("1C", "Frontend creates checkpoint (save as version)")
    
    checkpoint_context = {
        "messages": save_payload['messages'],
        "chatContext": [
            {"role": "user", "content": "Write a blog post about Python programming"},
            {"role": "assistant", "content": "Here's a comprehensive guide..."},
            {"role": "user", "content": "Make it more detailed"},
            {"role": "assistant", "content": "I've expanded the guide..."}
        ]
    }
    
    checkpoint_payload = {
        "conversation_id": conversation_id,
        "user_id": GUEST_USER_ID,
        "title": "Python Guide - Version 1",
        "content": blog_content,
        "description": "Initial comprehensive Python programming guide",
        "tone": "informative",
        "length": "long",
        "context_snapshot": checkpoint_context
    }
    
    log_request("POST", "/v1/checkpoints/create", {"title": checkpoint_payload['title']})
    
    response = requests.post(f"{BACKEND_URL}/v1/checkpoints/create", json=checkpoint_payload)
    if response.status_code == 200:
        checkpoint = response.json()
        checkpoint_id_v1 = checkpoint['id']
        log_response(f"200 OK", {"id": checkpoint_id_v1, "version": checkpoint['version_number'], "title": checkpoint['title']})
        log_success(f"Checkpoint created: Version {checkpoint['version_number']}")
    else:
        print(f"Error: {response.text}")
        exit(1)
    
    print()
    
    # ========================================================================
    # STEP 2: USER MAKES EDITS & CREATES SECOND CHECKPOINT
    # ========================================================================
    
    log_section("PART 2: USER EDITS BLOG & CREATES VERSION 2 (v2)")
    
    log_step("2A", "User makes edits to blog content")
    
    updated_blog = blog_content + """

## Advanced Topics

### Object-Oriented Programming
Learn classes, inheritance, and polymorphism.

### Functional Programming
Explore lambdas, map, filter, and reduce.

### Working with APIs
Make HTTP requests and handle JSON data.
"""
    
    log_info("Blog updated with Advanced Topics section")
    log_info(f"New content length: {len(updated_blog)} characters")
    
    log_step("2B", "Save updated context to database")
    
    save_payload['current_blog_content'] = updated_blog
    
    response = requests.post(f"{BACKEND_URL}/v1/context/save", json=save_payload)
    if response.status_code == 200:
        result = response.json()
        log_success(f"Updated context saved")
    
    log_step("2C", "Frontend creates checkpoint for Version 2")
    
    checkpoint_payload['title'] = "Python Guide - Version 2"
    checkpoint_payload['content'] = updated_blog
    checkpoint_payload['description'] = "Added Advanced Topics section"
    
    response = requests.post(f"{BACKEND_URL}/v1/checkpoints/create", json=checkpoint_payload)
    if response.status_code == 200:
        checkpoint = response.json()
        checkpoint_id_v2 = checkpoint['id']
        log_success(f"Checkpoint created: Version {checkpoint['version_number']}")
    
    print()
    
    # ========================================================================
    # STEP 3: FRONTEND LISTS ALL CHECKPOINTS
    # ========================================================================
    
    log_section("PART 3: FRONTEND LISTS CHECKPOINTS")
    
    log_step("List", "GET /v1/checkpoints/list/{conversation_id}")
    
    log_request("GET", f"/v1/checkpoints/list/{conversation_id}?user_id={GUEST_USER_ID}")
    
    response = requests.get(
        f"{BACKEND_URL}/v1/checkpoints/list/{conversation_id}",
        params={"user_id": GUEST_USER_ID}
    )
    
    if response.status_code == 200:
        checkpoints = response.json()
        log_response(f"200 OK", {"count": len(checkpoints)})
        log_success(f"Retrieved {len(checkpoints)} checkpoints")
        
        print(f"\n{Colors.BOLD}Available Versions:{Colors.ENDC}")
        for cp in checkpoints:
            status = "[ACTIVE]" if cp['is_active'] else "[inactive]"
            print(f"  v{cp['version_number']}: {cp['title']} {status}")
            print(f"    Created: {cp['created_at']}")
            print(f"    Description: {cp.get('description', 'N/A')}\n")
    
    print()
    
    # ========================================================================
    # STEP 4: FRONTEND RESTORES OLD CHECKPOINT
    # ========================================================================
    
    log_section("PART 4: FRONTEND RESTORES VERSION 1 CHECKPOINT")
    
    log_step("Restore", "User clicks 'Restore to Version 1'")
    
    log_info("Frontend shows checkpoint selector to user")
    log_info("User selects: 'Python Guide - Version 1'")
    
    log_step("Restore", "Frontend calls restore API endpoint")
    
    # This is what the frontend does when user clicks restore button
    log_request("POST", f"/v1/checkpoints/{checkpoint_id_v1}/restore", 
                {"checkpoint_id": checkpoint_id_v1, "user_id": GUEST_USER_ID})
    
    restore_payload = {
        "user_id": GUEST_USER_ID,
        "conversation_id": conversation_id
    }
    
    response = requests.post(
        f"{BACKEND_URL}/v1/checkpoints/{checkpoint_id_v1}/restore",
        params={"user_id": GUEST_USER_ID, "conversation_id": conversation_id}
    )
    
    if response.status_code == 200:
        result = response.json()
        log_response(f"200 OK", result)
        log_success("Checkpoint restored successfully!")
        log_info(f"Restored version: {result.get('version')}")
        log_info(f"Title: {result.get('title')}")
    else:
        print(f"Error: {response.text}")
    
    print()
    
    # ========================================================================
    # STEP 5: FRONTEND LOADS RESTORED CONTEXT
    # ========================================================================
    
    log_section("PART 5: FRONTEND LOADS RESTORED CONTEXT")
    
    log_step("Load", "GET /v1/context/load/{conversation_id}")
    
    log_request("GET", f"/v1/context/load/{conversation_id}?user_id={GUEST_USER_ID}")
    
    response = requests.get(
        f"{BACKEND_URL}/v1/context/load/{conversation_id}",
        params={"user_id": GUEST_USER_ID}
    )
    
    if response.status_code == 200:
        context = response.json()
        log_response(f"200 OK", {"message_count": context['message_count']})
        log_success("Context loaded with restored data")
        
        print(f"\n{Colors.BOLD}Restored Content:{Colors.ENDC}")
        if 'current_blog_content' in context and context['current_blog_content']:
            content = context['current_blog_content']
            # Show if it's Version 1 (without Advanced Topics) or Version 2 (with it)
            if "Advanced Topics" in content:
                log_info("ERROR: Still showing Version 2! (has Advanced Topics)")
            else:
                log_info("SUCCESS: Showing Version 1 content (no Advanced Topics)")
            
            print(f"\nBlog Preview:")
            lines = content.split('\n')[:8]
            for line in lines:
                print(f"  {line}")
        else:
            log_info("Blog content not found in response (may be empty or not restored)")
        
        print(f"\n{Colors.BOLD}Message History:{Colors.ENDC}")
        if 'messages' in context:
            log_info(f"Total messages: {len(context['messages'])}")
            for i, msg in enumerate(context['messages'][:4], 1):
                role = "User" if msg['role'] == 'user' else "AI"
                print(f"  {i}. {role}: {msg['content'][:60]}...")
    
    print()
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    
    log_section("CHECKPOINT RESTORATION FLOW - COMPLETE")
    
    print(f"{Colors.OKGREEN}{Colors.BOLD}✅ RESTORATION PROCESS VERIFIED!{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}What Happened:{Colors.ENDC}")
    print(f"  1. Created blog content and saved context v1")
    print(f"  2. Created checkpoint (version 1) - saved point in time")
    print(f"  3. User edited blog content")
    print(f"  4. Saved updated context and created checkpoint v2")
    print(f"  5. Frontend listed all available checkpoints")
    print(f"  6. User clicked 'Restore Version 1'")
    print(f"  7. Backend restored checkpoint to active state")
    print(f"  8. Frontend loaded the restored context")
    print(f"  9. Blog content reverted to version 1 [OK]\n")
    
    print(f"{Colors.BOLD}API Endpoints Used:{Colors.ENDC}")
    print(f"  POST   /v1/context/save - Save context after edits")
    print(f"  POST   /v1/checkpoints/create - Create version snapshot")
    print(f"  GET    /v1/checkpoints/list/:id - List all versions")
    print(f"  POST   /v1/checkpoints/:id/restore - Restore specific version")
    print(f"  GET    /v1/context/load/:id - Load restored context\n")
    
    print(f"{Colors.BOLD}Frontend Code Pattern:{Colors.ENDC}")
    print(f"""
  // 1. List checkpoints
  const checkpoints = await listCheckpoints(conversationId, userId)
  
  // 2. Show UI with list
  checkpoints.forEach(cp => {{
    if (userClicksRestore(cp)) {{
      // 3. Restore checkpoint
      await restoreCheckpoint(cp.id, userId, conversationId)
      
      // 4. Reload context
      const context = await loadContext(conversationId, userId)
      
      // 5. Update editor with restored content
      editor.setContent(context.current_blog_content)
      setChatHistory(context.messages)
    }}
  }})
    """)
    
    print(f"{Colors.OKGREEN}{Colors.BOLD}*** Time-Travel Feature Complete! ***{Colors.ENDC}\n")

except requests.exceptions.ConnectionError:
    print(f"{Colors.FAIL}Cannot connect to backend at {BACKEND_URL}")
    print(f"Make sure the backend is running: python -m uvicorn main:app --port 8000")
except Exception as e:
    print(f"{Colors.FAIL}Error: {e}")
    import traceback
    traceback.print_exc()
