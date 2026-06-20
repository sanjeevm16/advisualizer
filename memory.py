import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from google.adk import Runner
from google.adk.agents import LlmAgent
from google.adk.memory import BaseMemoryService
from google.adk.memory.base_memory_service import SearchMemoryResponse
from google.adk.sessions import Session, InMemorySessionService
from google.genai import Client
from trendanalyst import get_trend_analyst
from productcopier import get_product_copier
from scenecompositer import get_scene_compositer
from abvariantgenerator import get_ab_variant_generator

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
        
        Always follow the workflow: Trend Analysis -> Product Analysis -> Scene Composition -> Variant Generation.
        """,
        sub_agents=[trend_agent, product_agent, scene_agent, ab_agent],
        tools=[search_policies]
    )
    
    return Runner(
        app_name="AdVisualizer",
        agent=main_agent,
        session_service=session_service,
        memory_service=memory_service,
        auto_create_session=True
    )
