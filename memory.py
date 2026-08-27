import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from google.adk import Runner
from google.adk.agents import LlmAgent 
from google.adk.models import LlmResponse
from google.adk.memory import BaseMemoryService
from google.adk.memory.base_memory_service import SearchMemoryResponse
from google.adk.sessions import Session, InMemorySessionService
from google.genai import Client
from trendanalyst import get_trend_analyst
from productcopier import get_product_copier
from scenecompositer import get_scene_compositer
from abvariantgenerator import get_ab_variant_generator
from typing import Optional 
from google.adk.agents.callback_context import CallbackContext

# Model configurations
EMBEDDING_MODEL = "text-embedding-004"
CONVERSATIONAL_MODEL = "gemini-2.5-flash"

class VectorMemoryService(BaseMemoryService):
    """
    Simple vector-based memory service using local pickle storage and Gemini embeddings.
    """
    def __init__(self, storage_path: str = "vector_memories.pkl"):
        self.storage_path = storage_path
        self.memories: List[Dict[str, Any]] = []
        self._load()
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.client = Client(api_key=api_key)

    def _load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'rb') as f:
                self.memories = pickle.load(f)

    def _save(self):
        with open(self.storage_path, 'wb') as f:
            pickle.dump(self.memories, f)

    async def add_session_to_memory(self, session: Session) -> None:
        """Required abstract method for ADK 2.1.0"""
        # Simple implementation: embed and save the last turn's text
        print(f" Add session to memory {session.id}")
        if not session.history:
            return
            
        last_event = session.history[-1]
        # In ADK, events usually have a 'text' or 'content' attribute
        text_to_embed = getattr(last_event, 'text', str(last_event))
        
        embedding = self.client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text_to_embed
        ).embeddings[0].values
        
        self.memories.append({
            "text": text_to_embed,
            "embedding": embedding,
            "metadata": {"session_id": session.id}
        })
        self._save()

    async def search_memory(self, app_name: str, user_id: str, query: str) -> SearchMemoryResponse:
        """Required abstract method for ADK 2.1.0"""
        print(f" {app_name} - {user_id} - Searching memory for query: {query}")
        if not self.memories:
            return SearchMemoryResponse(memories=[])
            
        query_embedding = self.client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=query
        ).embeddings[0].values
        
        scores = []
        for m in self.memories:
            score = np.dot(query_embedding, m["embedding"])
            scores.append((score, m["text"]))
            
        scores.sort(key=lambda x: x[0], reverse=True)
        # Assuming SearchMemoryResponse expects a list of memory strings or similar
        return SearchMemoryResponse(memories=[s[1] for s in scores[:5]])

def search_policies(query: str) -> str:
    """
    Search a knowledge base of compensation policies.
    """
    return "Policy search result for: " + query

def track_token_usage(callback_context: CallbackContext, llm_response: LlmResponse) ->Optional[LlmResponse]:
    """
    Hook that fires automatically after every LLM call inside the agent loop.
    """
    agent_name = callback_context.agent_name
    print(f"[Callback] After model call for agent: {agent_name}")
    try:
        # 1. Primary: Check 'usage_metadata' attribute (Standard for Gemini ADK)
        usage = getattr(llm_response, 'usage_metadata', None)

        # 2. Secondary: Check 'usage' attribute (Common in LiteLLM backends)
        if not usage:
            usage = getattr(llm_response, 'usage', None)

        # 3. Fallback: Search inside metadata if it exists
        metadata = getattr(llm_response, 'metadata', {}) or {}
        model_response = metadata.get("model_response") if isinstance(metadata, dict) else None
        
        if not usage and model_response:
            if hasattr(model_response, 'usage_metadata'):
                usage = model_response.usage_metadata
            elif isinstance(model_response, dict):
                usage = model_response.get("usage_metadata") or model_response.get("usage")
        
        if not usage:
            usage = metadata.get("usage_metadata") or metadata.get("usage")

        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0

        if usage:
            if hasattr(usage, 'prompt_token_count'): # SDK Object style (Gemini)
                prompt_tokens = getattr(usage, 'prompt_token_count', 0)
                completion_tokens = getattr(usage, 'candidates_token_count', 0)
                total_tokens = getattr(usage, 'total_token_count', 0)
            elif isinstance(usage, dict): # Dictionary style fallback
                prompt_tokens = usage.get("prompt_token_count") or usage.get("prompt_tokens") or 0
                completion_tokens = usage.get("candidates_token_count") or usage.get("completion_tokens") or 0
                total_tokens = usage.get("total_token_count") or usage.get("total_tokens") or 0
        
        # Alternative Way: Manual Estimation if telemetry is missing
        if total_tokens == 0:
            # Count tokens in the generated response parts
            if llm_response.content and llm_response.content.parts:
                for part in llm_response.content.parts:
                    if part.text:
                        # Gemini heuristic: ~4 characters per token
                        completion_tokens += len(part.text) // 4
            
            # Note: Prompt tokens cannot be easily calculated here without the original prompt.
            # You can call client.models.count_tokens() if you have the prompt string.
            total_tokens = prompt_tokens + completion_tokens
            if total_tokens > 0:
                print(f"[Callback] Usage estimated via heuristic (Metadata was missing)")


        if total_tokens > 0:
            # Pricing for Gemini 2.5 Flash tier (Approximated)
            # Input: $0.075 per 1 million tokens | Output: $0.30 per 1 million tokens
            cost_input = (prompt_tokens / 1_000_000) * 0.075
            cost_output = (completion_tokens / 1_000_000) * 0.30
            total_cost = cost_input + cost_output

            print(f"\n--- [LlmAgent Token Hook] ---")
            print(f"Agent: {agent_name}")
            print(f"Prompt Input: {prompt_tokens} tokens (${cost_input:.6f})")
            print(f"Completion Output: {completion_tokens} tokens (${cost_output:.6f})")
            print(f"Total Call Tokens: {total_tokens} tokens")
            print(f"Estimated Cost: ${total_cost:.6f}")
            print(f"-----------------------------\n")
        else:
            print(f"[Callback] No usage telemetry found for agent: {agent_name}")

    except Exception as e:
        print(f"Error reading usage telemetry: {e}")
        
    return llm_response

def create_runner() -> Runner:
    """
    Creates and configures the ADK Runner with agents and tools.
    """
    memory_service = VectorMemoryService()
    session_service = InMemorySessionService()
    
    # Define specialized agents
    trend_agent = get_trend_analyst()
    product_agent = get_product_copier()
    scene_agent = get_scene_compositer()
    ab_agent = get_ab_variant_generator()
    
    # Define the main orchestrator agent
    main_agent = LlmAgent(
        name="Orchestrator",
        model=CONVERSATIONAL_MODEL,
        instruction="""You are the Orchestrator of the Ad Visualizer platform. 
        Your goal is to coordinate the following agents to automate ad creation:
        1. Trend Analyst: Identifies visual trends.
        2. Product Copier: Analyzes product images and handles masking.
        3. Scene Compositor: Generates backdrop prompts based on trends.
        4. A/B Variant Generator: Creates multiple variations for testing.
        
        Always follow the workflow: Trend Analyst -> Product Copier -> Scene Compositor -> A/B Variant Generator.
        Resetrict token usage below 400.
        """,
        sub_agents=[trend_agent, product_agent, scene_agent, ab_agent],
        tools=[search_policies], 
        after_model_callback=track_token_usage # Binds the token hook
    )
    
    return Runner(
        app_name="AdVisualizer",
        agent=main_agent,
        session_service=session_service,
        memory_service=memory_service,
        auto_create_session=True
    )
