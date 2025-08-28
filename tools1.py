import json
import os
from typing import Dict
from livekit.agents import function_tool
import requests
from datetime import datetime, timezone
import time

sessions_data: Dict[str, Dict] = {}
MAX_SESSIONS = 100  # Prevent memory overflow


def _get_session_data(session_id: str) -> Dict:
    # Clean old sessions if we have too many
    if len(sessions_data) >= MAX_SESSIONS:
        oldest_session = min(sessions_data.keys())
        del sessions_data[oldest_session]
    
    if session_id not in sessions_data:
        sessions_data[session_id] = {
            "conversation_log": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    return sessions_data[session_id]


@function_tool()
async def log_message(session_id: str, speaker: str, text: str) -> str:
    """Log a message for a specific session."""
    if not text or not text.strip():
        return f"Empty message not logged for {session_id}"
    
    log = _get_session_data(session_id)["conversation_log"]
    message_entry = {
        "speaker": speaker,
        "text": text.strip(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    log.append(message_entry)
    
    print(f"[{session_id}] {speaker}: {text}")
    
    # Auto-save every 5 messages (more frequent to catch conversations)
    if len(log) % 5 == 0:
        print(f"Auto-saving session {session_id} (message count: {len(log)})")
        await save_session(session_id)
    
    return f"Logged {speaker} message for {session_id} (total messages: {len(log)})"


@function_tool()
async def save_session(session_id: str) -> str:
    """Save conversation log to JSON."""
    data = _get_session_data(session_id)
    
    # Create sessions directory if it doesn't exist
    os.makedirs("sessions", exist_ok=True)
    
    filename = f"sessions/session_{session_id}.json"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Session {session_id} saved to {filename}")
        return f"Session {session_id} saved successfully"
    except Exception as e:
        print(f"Failed to save session {session_id}: {e}")
        return f"Failed to save: {e}"


@function_tool()
async def get_conversation_history(session_id: str) -> str:
    """Return conversation history as text."""
    history = _get_session_data(session_id)["conversation_log"]
    if not history:
        return "No conversation history yet"
    
    # Return last 20 messages to avoid overwhelming the LLM
    recent_history = history[-20:]
    return "\n".join([f"{m['speaker']}: {m['text']}" for m in recent_history])


@function_tool()
async def internet_search(query: str) -> str:
    """
    Perform internet search using multiple sources with fallback options.
    Optimized for financial and real-time data queries.
    """
    
    def search_duckduckgo(query: str) -> str:
        """Primary search using DuckDuckGo"""
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Try different data sources from DuckDuckGo
            if data.get("AbstractText"):
                return f"Source: DuckDuckGo - {data['AbstractText']}"
            
            if data.get("Answer"):
                return f"Source: DuckDuckGo - {data['Answer']}"
            
            if data.get("RelatedTopics"):
                topics = [t.get("Text", "") for t in data["RelatedTopics"] if t.get("Text")]
                if topics:
                    result = " | ".join(topics[:2])  # Limit to 2 topics
                    return f"Source: DuckDuckGo - {result}"
            
            if data.get("Results"):
                results = [r.get("Text", "") for r in data["Results"] if r.get("Text")]
                if results:
                    return f"Source: DuckDuckGo - {results[0]}"
                    
            return None
            
        except Exception as e:
            print(f"DuckDuckGo search failed: {e}")
            return None
    
    def search_alternative(query: str) -> str:
        """Alternative search for financial data"""
        try:
            # For gold price queries, try a more specific approach
            if "gold" in query.lower() and ("price" in query.lower() or "rate" in query.lower()):
                return "Current gold prices fluctuate daily. Check reliable financial websites like Economic Times, MoneyControl, or your bank's rates for the most accurate pricing. Digital gold platforms typically update rates every few minutes during market hours."
            
            if "stock" in query.lower() or "market" in query.lower():
                return "Stock markets change throughout trading hours. For real-time data, check NSE, BSE, or financial news websites like Economic Times, CNBC, or Bloomberg."
            
            if "inflation" in query.lower():
                return "Inflation rates are published monthly by government statistics offices. In India, check RBI or Ministry of Statistics data for official figures."
                
            return None
            
        except Exception as e:
            print(f"Alternative search failed: {e}")
            return None
    
    # Rate limiting
    time.sleep(0.5)  # Simple rate limiting
    
    print(f"Searching for: {query}")
    
    # Try primary search first
    result = search_duckduckgo(query)
    if result:
        return result
    
    # Try alternative approach
    result = search_alternative(query)
    if result:
        return f"General guidance: {result}"
    
    # Final fallback
    return f"I couldn't find current data for '{query}'. For the most accurate and up-to-date information, I recommend checking reliable financial websites like Economic Times, MoneyControl, or official financial institutions."