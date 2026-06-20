# AI Open-Word Asset Factory Agent (Python)

This project is a Flask-based AI companion application that utilizes the **Google Agent Development Kit (ADK)**. It features An ecosystem that completely automates product placement, visual marketing campaigns, and ad variations for a brand based on real-time market trends.It bridges the gap between raw data metrics and creative production without human intervention.

## Project Overview

-   **Backend:** A Flask application (`app.py`) providing a web interface and a `/chat` API endpoint.
-   **AI Engine:** Powered by Google's Gemini models via the ADK.
-   **Agent Architecture:**
    -   `memory.py`: Implements a more advanced `Runner` with vector-based memory and specialized tools.
    -   `trendanalyst.py`: Trend Analyst (Agent A) - Scrapes web or social signals to see what visual styles (e.g., "minimalist pastel", "cyberpunk neon") are converting best this week.
    -   `productcopier.py` : Product Copier (Agent B) - Analyzes a raw user product image and creates a structural image-to-image mask or background removal strategy.
    -   `scenecompositer.py`: Scene Compositor (Agent C): Writes contextual backdrop prompts matching the Trend Analyst’s recommendations, passing them to a Flux or Midjourney API.
    -   `abvariantgenerator.py' : Modifies lighting, aspect ratios, and call-to-action overlays to create 5 distinct visual variants for marketing tests.
-   **Core Features:**
    -   **Guest Verification:** Follows a structured flow to verify identity.
    -   **Policy Search:** Uses vector similarity to search a knowledge base of compensation policies.
    -   **Long-Term Memory:** Employs `VectorMemoryService` with Gemini embeddings to remember past interactions across sessions.
    -   **Session Management:** Uses SQLite for persistent session storage.
-   **Frontend:** A modern web UI (`static/app.js`) to visualize image transition by each agent.

## Architecture & Technologies

-   **Framework:** Flask (Python)
-   **AI SDK:** `google-adk`, `google-genai`
-   **Models:** `gemini-2.5-flash` (Conversational), `text-embedding-004` (Embeddings)
-   **Database:** SQLite (`sessions.db`)
-   **Storage:** Local pickle file (`vector_memories.pkl`) for vector embeddings.
-   **Frontend:** Vanilla JavaScript, SpeechSynthesis API for voice.

## Getting Started

### Prerequisites

-   Python 3.10+
-   Google Cloud Project with Generative AI API enabled.
-   `gcloud` CLI authenticated.

### Installation

1.  **Environment Setup:**
    ```bash
    bash init.sh          # Set your Google Cloud Project ID
    source set_env.sh     # Export environment variables (Project ID, API Key, etc.)
    ```
2.  **Install Dependencies:**
    ```bash
    pip install flask google-adk google-genai numpy
    ```

### Running the Application

Start the Flask server:
```bash
python app.py
```
The application will be available at `http://127.0.0.1:5000`.

> **Note:** The `index.html` file appears to be missing from the `templates/` directory in the current workspace. Ensure it is restored to run the full web UI.

## Development Conventions

-   **Agent Definition:** Agents should be defined using ADK's `LlmAgent`.
-   **Tools:** Extend agent capabilities by adding functions to the `tools` list in `LlmAgent`. See `memory.py` for examples like `search_policies`.
-   **Memory:** Custom memory services should inherit from `BaseMemoryService`.
-   **Scripts:** Use `init.sh` and `set_env.sh` for consistent environment configuration.

## Key Files

-   `app.py`: Flask entry point and route definitions.
-   `memory.py`: Core ADK configuration including `Runner`, `MemoryService`, and `search_policies` tool.
-   `trendanalyst.py`: Trend Analyst (Agent A) - Scrapes web or social signals to see what visual styles (e.g., "minimalist pastel", "cyberpunk neon") are converting best this week.
-   `productcopier.py` : Product Copier (Agent B) - Analyzes a raw user product image and creates a structural image-to-image mask or background removal strategy.
-   `scenecompositer.py`: Scene Compositor (Agent C): Writes contextual backdrop prompts matching the Trend Analyst’s recommendations, passing them to a Flux or Midjourney API.
-   `abvariantgenerator.py' : Modifies lighting, aspect ratios, and call-to-action overlays to create 5 distinct visual variants for marketing tests.
-   `static/app.js`: Frontend logic for assets library interface and voice.
-   `init.sh` / `set_env.sh`: Project initialization and environment setup.

