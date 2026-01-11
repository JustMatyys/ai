#!/usr/bin/env python3
"""
Web Search Chatbot with Memory
Keeps track of your conversations and searches the web when needed.
"""

import os
import time
import re
import json
from datetime import datetime
from typing import List, Dict, Any
from ollama import Client
from ddgs import DDGS

client = Client()
model = ""
debug_mode = False
memory_file = "chatbot_memory.json"
conversation_history = []

system_default = """You are a helpful AI assistant with memory.
When the user says "exit", respond with: "Welcome back 😎"

You can reference past conversations and provide accurate info about current events.""".strip()

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def should_search_web(user_input):
    """Check if we need to search the web for this query."""
    user_input = user_input.lower()
    
    # Keywords that suggest we should search
    triggers = [
        "search", "news", "latest", "recent", "what happened", "what's new",
        "current", "today", "now", "happening", "update", "breaking",
        "ukraine", "war", "conflict", "russia", "covid", "pandemic", 
        "politics", "world news", "ces", "technology", "czech", "czechia", 
        "prague", "tv", "television", "channels", "media"
    ]
    
    for trigger in triggers:
        if trigger in user_input:
            return True
    
    # Check for recent years
    if re.search(r'\b(2023|2024|2025)\b', user_input):
        return True
    
    return False

def load_memory():
    """Load saved conversations."""
    global conversation_history
    try:
        if os.path.exists(memory_file):
            with open(memory_file, 'r', encoding='utf-8') as f:
                conversation_history = json.load(f)
            return True
    except Exception as e:
        print(f"Couldn't load memory: {e}")
    return False

def save_memory():
    """Save conversations to disk."""
    try:
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(conversation_history, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Couldn't save memory: {e}")
        return False

def add_to_memory(role, content):
    """Add a message to the conversation history."""
    global conversation_history
    message = {
        "timestamp": datetime.now().isoformat(),
        "role": role,
        "content": content
    }
    conversation_history.append(message)
    
    # Keep last 50 messages to avoid huge files
    if len(conversation_history) > 50:
        conversation_history = conversation_history[-50:]
    
    save_memory()

def get_memory_context():
    """Format recent conversation history for the AI."""
    if not conversation_history:
        return "No previous conversation history."
    
    recent = conversation_history[-10:]
    lines = ["CONVERSATION HISTORY:"]
    
    for msg in recent:
        role = "Human" if msg['role'] == 'user' else "Assistant"
        lines.append(f"{role}: {msg['content']}")
    
    return "\n".join(lines)

def clear_memory():
    """Wipe conversation history."""
    global conversation_history
    conversation_history = []
    if os.path.exists(memory_file):
        os.remove(memory_file)

def clean_search_query(user_input):
    """Turn user input into a good search query."""
    # Remove common filler words
    user_input = re.sub(r'\b(search|look up|find|google|what is|who is)\b', 
                       '', user_input, flags=re.IGNORECASE)
    user_input = re.sub(r'[^\w\s]', ' ', user_input)
    user_input = re.sub(r'\s+', ' ', user_input).strip()
    
    # Handle specific topics better
    if "ukraine" in user_input.lower():
        return "Ukraine war Russia conflict latest news"
    elif "ces" in user_input.lower():
        return "CES 2025 technology announcements"
    elif "covid" in user_input.lower():
        return "COVID-19 latest news updates"
    elif any(w in user_input.lower() for w in ["czech", "czechia", "prague"]):
        return "Czechia Czech Republic latest news"
    elif any(w in user_input.lower() for w in ["tv", "television", "channels"]):
        return "Czech Republic TV news channels outlets"
    
    # Add "latest news" if not already there
    if not any(w in user_input.lower() for w in ["news", "latest", "recent"]):
        user_input += " latest news"
    
    return user_input[:80]

def search_tv_outlets():
    """Search specifically for Czech TV outlets."""
    queries = [
        "Czech Republic TV news channels",
        "Czech television news outlets",
        "CT Czech TV news",
        "Nova TV Czech Republic",
        "Prima TV Czech news"
    ]
    
    results = []
    for query in queries:
        try:
            with DDGS() as ddgs:
                results.extend(list(ddgs.text(query, max_results=10)))
        except:
            continue
    
    return results

def search_topic(topic):
    """Search based on the topic type."""
    # Special handling for TV/media queries
    if any(w in topic.lower() for w in ["tv", "television", "channels"]):
        return search_tv_outlets()
    
    # Build query list based on topic
    queries = []
    if "ukraine" in topic.lower():
        queries = ["Ukraine war news", "Russia Ukraine conflict"]
    elif "ces" in topic.lower():
        queries = ["CES 2025 technology news"]
    elif "covid" in topic.lower():
        queries = ["COVID-19 news updates"]
    elif any(w in topic.lower() for w in ["czech", "czechia"]):
        queries = ["Czech Republic news", "Czechia latest news"]
    else:
        queries = [topic]
    
    # Run searches
    results = []
    for query in queries:
        try:
            with DDGS() as ddgs:
                results.extend(list(ddgs.text(query, max_results=10)))
        except:
            continue
    
    # Remove duplicates
    seen = set()
    unique = []
    for r in results:
        url = r.get('href', '')
        if url and url not in seen:
            seen.add(url)
            unique.append(r)
    
    return unique

def extract_info(results):
    """Pull out useful information from search results."""
    info = {
        'headlines': [],
        'key_points': [],
        'dates': []
    }
    
    for result in results:
        title = result.get('title', '')
        body = result.get('body', '')
        text = f"{title} {body}".strip()
        
        if title:
            info['headlines'].append(title)
        
        # Grab relevant sentences
        sentences = re.split(r'[.!?]+', text)
        for sent in sentences:
            sent = sent.strip()
            if len(sent) > 30 and any(kw in sent.lower() for kw in 
                ['tv', 'channel', 'media', 'news', 'announce', 'report']):
                info['key_points'].append(sent)
        
        # Pull out dates
        dates = re.findall(
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+202[0-9]\b', 
            text, re.IGNORECASE
        )
        info['dates'].extend(dates)
    
    # Remove dupes and limit
    for key in info:
        info[key] = list(set(info[key]))[:10]
    
    return info

def format_results(query, info):
    """Format search results nicely."""
    lines = []
    lines.append("=" * 60)
    lines.append(f"WEB SEARCH: {query.upper()}")
    lines.append("=" * 60)
    lines.append("")
    
    if info['headlines']:
        lines.append("HEADLINES:")
        for i, h in enumerate(info['headlines'][:8], 1):
            lines.append(f"{i}. {h}")
        lines.append("")
    
    if info['key_points']:
        lines.append("KEY INFORMATION:")
        for point in info['key_points'][:6]:
            point = re.sub(r'\s+', ' ', point).strip()
            if len(point) > 200:
                point = point[:200] + "..."
            lines.append(f"• {point}")
        lines.append("")
    
    if info['dates']:
        lines.append("DATES:")
        for date in info['dates'][:5]:
            lines.append(f"• {date}")
        lines.append("")
    
    lines.append("=" * 60)
    lines.append("Use this info to answer. Be specific and clear.")
    lines.append("=" * 60)
    
    return "\n".join(lines)

def clean_text(text):
    """Remove weird characters that mess up output."""
    if not text:
        return ""
    
    # Strip out problematic chars
    text = re.sub(r'[^\w\s\.\,\!\?\:\;\-\(\)\"\'\/\\\[\]\{\}]', '', text)
    text = re.sub(r'[*|#@&~`^%+=<>{}]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('||', ' ').replace('**', ' ').replace('//', ' ')
    
    return text.strip()

def do_search(query):
    """Run a web search and format results."""
    try:
        if debug_mode:
            print(f"\n[Searching: {query}]\n")
        
        results = search_topic(query)
        
        if not results:
            return f"No results for: {query}"
        
        info = extract_info(results)
        formatted = format_results(query, info)
        
        return formatted
        
    except Exception as e:
        return f"Search failed: {e}"

def startup():
    global model, system_default, debug_mode, conversation_history

    clear()
    print("=" * 45)
    print("Web Search Chatbot with Memory")
    print("=" * 45)
    print("1. Minimax M2 (Cloud)")
    print("2. GPT-OSS 120b (Cloud)")
    print("3. DeepSeek-v3.1 671b (Cloud)")
    print("4. Qwen3-Coder 480b (Cloud)")
    print("Q/q. Exit")
    print("")
    print('Type "default" for custom instructions')
    print('Type "debug" to toggle debug mode')
    print('Type "memory" to view history')
    print('Type "clear" to clear memory')
    print("")

    # Load previous conversations
    loaded = load_memory()
    if loaded and conversation_history:
        print(f"✅ Loaded {len(conversation_history)} messages")
        print(f"💬 Last: {conversation_history[-1]['content'][:50]}...")
    else:
        print("💬 Starting fresh")
    print("")

    while True:
        choice = input("Choose option: ").strip().lower()
        if choice == "1":
            model = "minimax-m2:cloud"
            break
        elif choice == "2":
            model = "gpt-oss:120b-cloud"
            break
        elif choice == "3":
            model = "deepseek-v3.1:671b-cloud"
            break
        elif choice == "4":
            model = "qwen3-coder:480b-cloud"
            break
        elif choice == "default":
            clear()
            print("Enter new system instruction:")
            system_default = input("> ").strip()
            clear()
            continue
        elif choice == "debug":
            debug_mode = not debug_mode
            print(f"Debug: {'ON' if debug_mode else 'OFF'}")
            time.sleep(1)
            clear()
            continue
        elif choice == "memory":
            if conversation_history:
                print("\n📚 HISTORY:")
                print("-" * 40)
                for i, msg in enumerate(conversation_history[-10:], 1):
                    icon = "👤" if msg['role'] == 'user' else "🤖"
                    print(f"{i}. {icon} {msg['content']}")
                print("-" * 40)
            else:
                print("📚 No history yet")
            print("\nPress Enter...")
            input()
            clear()
            continue
        elif choice == "clear":
            clear_memory()
            print("🗑️ Memory cleared")
            time.sleep(1)
            clear()
            continue
        elif choice in ("q", "qq"):
            save_memory()
            exit(0)
        else:
            print("Invalid choice")
            time.sleep(1)
            clear()
    
    clear()
    print(f"✅ Model: {model}")
    print(f"🔧 Debug: {'ON' if debug_mode else 'OFF'}")
    print(f"💾 Memory: {len(conversation_history)} messages")
    print()

def chat():
    global model, system_default, debug_mode, conversation_history

    while True:
        try:
            user_input = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Bye!")
            save_memory()
            return

        if user_input.lower() == "exit":
            save_memory()
            startup()
            continue

        add_to_memory('user', user_input)

        needs_search = should_search_web(user_input)
        
        if needs_search:
            query = clean_search_query(user_input)
            if query:
                search_data = do_search(query)
                
                if debug_mode:
                    print(search_data)
                    print("\n" + "=" * 60 + "\n")
                
                memory = get_memory_context()
                
                messages = [
                    {"role": "user", "content": user_input},
                    {"role": "system", "content": system_default},
                    {"role": "system", "content": memory},
                    {"role": "system", "content": search_data},
                    {"role": "system", "content": "Answer based on the search results and history. Be clear and focus on facts."}
                ]
                
                print("🤖 Response:")
                print("-" * 40)
                
                try:
                    full_response = ""
                    for chunk in client.chat(model, messages=messages, stream=True):
                        text = chunk['message']['content']
                        clean = clean_text(text)
                        if clean.strip():
                            print(clean, end="", flush=True)
                        full_response += text
                    
                    if full_response.strip():
                        add_to_memory('assistant', full_response.strip())
                    
                    print("\n")
                except Exception as e:
                    print(f"\n❌ Error: {e}")
        else:
            # Regular chat without search
            memory = get_memory_context()
            
            messages = [
                {"role": "user", "content": user_input},
                {"role": "system", "content": system_default},
                {"role": "system", "content": memory}
            ]
            
            print("🤖 Response:")
            print("-" * 40)
            
            try:
                full_response = ""
                for chunk in client.chat(model, messages=messages, stream=True):
                    text = chunk['message']['content']
                    clean = clean_text(text)
                    if clean.strip():
                        print(clean, end="", flush=True)
                    full_response += text
                
                if full_response.strip():
                    add_to_memory('assistant', full_response.strip())
                
                print("\n")
            except Exception as e:
                print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    startup()
    chat()