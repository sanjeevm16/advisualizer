# AI Open-Word Asset Factory (Ad Visualizer)

An ecosystem that completely automates product placement, visual marketing campaigns, and ad variations for a brand based on real-time market trends. It bridges the gap between raw data metrics and creative production without human intervention using Google's **Agent Development Kit (ADK)** and Google GenAI SDK.

---

## 🌟 Key Features

1. **Multi-Agent Orchestrated Workflows**:
   * **Orchestrator Agent**: Delegates and coordinates the workflow sequentially:
     ```mermaid
     graph LR
         TA["Trend Analyst"] --> PC["Product Copier"] --> SC["Scene Compositor"] --> VG["Variant Generator"]
     ```
   * **Trend Analyst**: Identifies converting visual styles based on simulated web/social category indicators.
   * **Product Copier**: Analyzes uploaded product images and implements background matting/masking strategies.
   * **Scene Compositor**: Formulates detailed backdrop generation prompts.
   * **A/B Variant Generator**: Produces 3–5 distinct visual variant prompts altering aspect ratios, lighting conditions, and Call-to-Action (CTA) overlays.
2. **Session Image Upload & Pillow Masking**:
   * Supports dragging, dropping, or selecting raw product images.
   * Runs an automatic Pillow (`PIL`) edge detection pipeline on the backend to immediately output high-contrast structural masks for product segmentation.
3. **Interactive Agent Workspace**:
   * A dedicated panel that breaks down the active strategy, prompt, and task details of each agent.
   * Connects to **Vertex AI Imagen 3** (`imagen-3.0-generate-002`) to generate and display style/backdrop/variant images directly within the agent cards.
4. **SQLite Session Persistence**:
   * Uses SQLite (`sessions.db`) to persist uploaded product files, parsed agent steps, and generated creative assets, ensuring users can refresh and resume sessions seamlessly.
5. **Vocal UI Controls**:
   * Built-in Web Speech API integration supporting Speech-to-Text (STT) mic capture and Text-to-Speech (TTS) voice synthesis for read-back replies.
6. **Semantic Memory**:
   * Uses `VectorMemoryService` powered by `text-embedding-004` to retrieve past interactions and relevant context on a session basis.

---

## 🛠️ Tech Stack & Architecture

* **Backend**: Flask (Python 3.10+)
* **AI Orchestration & SDK**: `google-adk`, `google-genai`
* **Models**:
  * Conversational / Orchestrator: `gemini-2.5-flash`
  * Text Embeddings: `text-embedding-004`
  * Image Generation: `imagen-3.0-generate-002`
* **Databases & Storage**: SQLite (`sessions.db`), Local serialization (`vector_memories.pkl`)
* **Frontend**: HTML5, Vanilla JavaScript, Vanilla CSS (Outfit & Plus Jakarta Sans typography)

For detailed architectural schematics and sequencing diagrams, review the [architecture.md](file:///home/devstar9515/way-back-home/advisualizer/architecture.md) file.

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* Google Cloud Project with Generative AI API enabled.
* `gcloud` CLI authenticated on the machine.

### Installation
1. Install project dependencies:
   ```bash
   pip install flask google-adk google-genai numpy Pillow
   ```
2. Configure the Google Cloud environment by writing your active project ID to `~/project_id.txt` (e.g. `io-extended26sna-9515`).

### Running the Application
1. Source the environment variables:
   ```bash
   source set_env.sh
   ```
   *Note: Sourcing `set_env.sh` automatically logs in to your active gcloud profile, exports your project configurations, and sets `GOOGLE_GENAI_USE_VERTEXAI="TRUE"` to use Vertex AI application default credentials.*

2. Start the Flask application:
   ```bash
   python3 app.py
   ```
3. Open `http://127.0.0.1:5000` in your web browser.

---

## 📂 Key Files

* [app.py](file:///home/devstar9515/way-back-home/advisualizer/app.py): Main Flask entry point containing `/upload`, `/chat`, `/generate_agent_image`, and `/session_state` endpoints.
* [memory.py](file:///home/devstar9515/way-back-home/advisualizer/memory.py): Configurations for the ADK `Runner`, custom `VectorMemoryService`, and memory database initializations.
* [architecture.md](file:///home/devstar9515/way-back-home/advisualizer/architecture.md): Diagrams and walkthroughs detailing the system design.
* [templates/index.html](file:///home/devstar9515/way-back-home/advisualizer/templates/index.html): Dashboard frontend structure featuring modern glassmorphism panels.
* [static/app.js](file:///home/devstar9515/way-back-home/advisualizer/static/app.js): Client-side event controller handling uploads, state reloads, and generation triggers.
* [static/style.css](file:///home/devstar9515/way-back-home/advisualizer/static/style.css): Custom stylesheet providing Outfit & Plus Jakarta Sans typography, neon glow states, and transition animations.
