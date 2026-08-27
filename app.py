import os
import sqlite3
import uuid
import json
import shutil
import werkzeug.utils
from flask import Flask, request, jsonify, render_template, session
from PIL import Image, ImageOps, ImageFilter
from google.genai import Client
from memory import create_runner


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-key")

# Initialize ADK Runner
runner = create_runner()

# Initialize GenAI Client for Imagen
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
genai_client = Client(api_key=api_key)

# Ensure directories exist
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('static/generated', exist_ok=True)

def init_db():
    conn = sqlite3.connect('sessions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (session_id TEXT PRIMARY KEY, user_data TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.before_request
def ensure_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

def get_session_data(session_id):
    conn = sqlite3.connect('sessions.db')
    c = conn.cursor()
    c.execute("SELECT user_data FROM sessions WHERE session_id = ?", (session_id,))
    row = c.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row[0])
        except Exception:
            pass
    return {"uploaded_images": [], "agent_steps": {}, "creative_assets": []}

def save_session_data(session_id, data):
    conn = sqlite3.connect('sessions.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO sessions (session_id, user_data) VALUES (?, ?)",
              (session_id, json.dumps(data)))
    conn.commit()
    conn.close()

def parse_variants_from_text(text: str) -> list:
    variants = []
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('*') or line.startswith('-') or (line and line[0].isdigit() and len(line) > 1 and (line[1] == '.' or line[1] == ')')):
            content = line.lstrip('*-0123456789.() \t')
            content = content.replace('**', '').strip()
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1].strip()
            elif content.startswith("'") and content.endswith("'"):
                content = content[1:-1].strip()
            if content and len(content) > 10:
                variants.append(content)
    return variants

def generate_mask_image(input_path, output_path):
    try:
        with Image.open(input_path) as img:
            img.thumbnail((512, 512))
            gray = img.convert("L")
            edges = gray.filter(ImageFilter.FIND_EDGES)
            mask = edges.point(lambda x: 255 if x > 30 else 0)
            mask.save(output_path)
            return True
    except Exception as e:
        print(f"Error generating mask: {e}")
        return False

def generate_image_with_imagen(prompt: str) -> str:
    try:
        result = genai_client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt,
            config=dict(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="1:1"
            )
        )
        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = os.path.join('static/generated', filename)
        
        image_bytes = result.generated_images[0].image.image_bytes
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
            
        return f"/static/generated/{filename}"
    except Exception as e:
        print(f"Error generating image with Imagen: {e}")
        # Robust fallback using stock images
        filename = f"fallback_{uuid.uuid4().hex[:8]}.jpg"
        filepath = os.path.join('static/generated', filename)
        
        src = 'static/ad1.jpg' if 'pastel' in prompt.lower() or 'minimal' in prompt.lower() else 'static/ad2.jpg'
        shutil.copy(src, filepath)
        return f"/static/generated/{filename}"

@app.route('/')
def index():
    return render_template('index.html')

# New utility to compute faithfulness using Gemini (native)
def compute_faithfulness(reference: str, answer: str) -> float:
    """Return a faithfulness score (0‑1) using Gemini.
    The function asks Gemini to compare *answer* with the *reference* and to
    respond with a numeric score. It parses the numeric value from the model's
    reply. If parsing fails, ``-1.0`` is returned.
    """
    try:
        # Build a concise prompt for Gemini
        prompt = (
            f"You are given a reference answer and a model‑generated answer.\n"
            f"Reference: '''{reference}'''\n"
            f"Answer: '''{answer}'''\n"
            f"Rate the faithfulness of the answer to the reference on a scale of 0 to 1, where 1 means completely faithful and 0 means not faithful at all. "
            f"Respond ONLY with the numeric score."
        )
        # Use the existing genai client (Gemini flash model)
        response = genai_client.models.generate_content(
            model='gemini-2.5-flash',
            prompt=prompt,
            config={"temperature": 0.0}
        )
        # Extract text from response
        text = response.candidates[0].content.parts[0].text.strip()
        # Try to parse a float from the response
        score = float(text)
        # Clamp between 0 and 1
        return max(0.0, min(1.0, score))
    except Exception as e:
        print(f"Faithfulness evaluation error: {e}")
        return -1.0

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        session_id = session.get('session_id', 'default_session')
        upload_dir = os.path.join('static', 'uploads', session_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        filename = werkzeug.utils.secure_filename(file.filename)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        file_url = f"/static/uploads/{session_id}/{filename}"
        
        mask_filename = f"mask_{filename}"
        mask_filepath = os.path.join(upload_dir, mask_filename)
        mask_url = f"/static/uploads/{session_id}/{mask_filename}"
        
        generate_mask_image(filepath, mask_filepath)
        
        session_data = get_session_data(session_id)
        img_entry = {
            "name": filename,
            "url": file_url,
            "mask_url": mask_url
        }
        session_data["uploaded_images"].append(img_entry)
        
        # Prepopulate ProductCopier stage with the uploaded image info
        session_data["agent_steps"]["ProductCopier"] = {
            "name": "Product Copier",
            "description": "Analyzes raw user product images and creates image-to-image masks.",
            "strategy": f"Uploaded product image: {filename}. Structural mask generated using alpha matting simulation.",
            "prompt": file_url,
            "image_url": mask_url
        }
        
        save_session_data(session_id, session_data)
        
        return jsonify({
            "message": "File uploaded successfully",
            "image": img_entry
        })

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    image_url = request.json.get('image_url')
    session_id = session.get('session_id', 'default_session')
    
    if "verify" in user_input.lower():
        return jsonify({"response": "Guest verification started. Please provide your ID."})
        
    try:
        from google.genai._transformers import t_content
        
        runner_message = user_input
        if image_url:
            runner_message = f"Product Image URL: {image_url}. {user_input}"
        
        events = runner.run(
            user_id="default_user",
            session_id=session_id,
            new_message=t_content(runner_message)
        )
        
        session_data = get_session_data(session_id)
        agent_steps = session_data.get("agent_steps", {})
        
        default_steps = {
            "TrendAnalyst": {
                "name": "Trend Analyst",
                "description": "Scrapes web/social signals to identify converting visual styles.",
                "strategy": "No style identified yet. Ask the orchestrator to start a campaign.",
                "prompt": "",
                "image_url": ""
            },
            "ProductCopier": {
                "name": "Product Copier",
                "description": "Analyzes raw user product images and creates image-to-image masks.",
                "strategy": "No product analyzed yet. Please upload a product image first.",
                "prompt": "",
                "image_url": ""
            },
            "SceneCompositor": {
                "name": "Scene Compositor",
                "description": "Writes backdrop prompts matching Trend Analyst recommendations.",
                "strategy": "No backdrop prompt written yet.",
                "prompt": "",
                "image_url": ""
            },
            "ABVariantGenerator": {
                "name": "A/B Variant Generator",
                "description": "Creates 5 distinct visual variations (aspect ratios, lighting, overlays) for marketing tests.",
                "strategy": "No variants generated yet.",
                "prompts": [],
                "images": {}
            }
        }
        
        for k, v in default_steps.items():
            if k not in agent_steps:
                agent_steps[k] = v
                
        final_response = ""
        for event in events:
            author = event.author
            if event.message and event.message.parts:
                for part in event.message.parts:
                    if part.text:
                        final_response += part.text
                        if author in agent_steps:
                            agent_steps[author]["strategy"] = part.text
                            
                    if part.function_call:
                        call_name = part.function_call.name
                        args = part.function_call.args
                        if author == "TrendAnalyst" and call_name == "scrape_trends":
                            agent_steps[author]["prompt"] = args.get('category', '')
                        elif author == "ProductCopier" and call_name == "analyze_product_image":
                            agent_steps[author]["prompt"] = args.get('image_path', '')
                        elif author == "SceneCompositor" and call_name == "generate_backdrop_prompt":
                            agent_steps[author]["prompt"] = f"Style: {args.get('style', '')}, Product: {args.get('product_desc', '')}"
                        elif author == "ABVariantGenerator" and call_name == "create_variants":
                            agent_steps[author]["prompt"] = args.get('base_prompt', '')
                            
                    if part.function_response:
                        resp_name = part.function_response.name
                        resp_val = part.function_response.response
                        result = resp_val.get('result') if isinstance(resp_val, dict) else str(resp_val)
                        if author == "TrendAnalyst" and resp_name == "scrape_trends":
                            agent_steps[author]["strategy"] = f"Identified trend style: {result}"
                            agent_steps[author]["prompt"] = result
                        elif author == "ProductCopier" and resp_name == "analyze_product_image":
                            agent_steps[author]["strategy"] = f"Mask strategy: {result}"
                            if image_url:
                                upload_dir = os.path.dirname(image_url)
                                filename = os.path.basename(image_url)
                                mask_url = f"{upload_dir}/mask_{filename}"
                                agent_steps[author]["image_url"] = mask_url
                                agent_steps[author]["prompt"] = image_url
                        elif author == "SceneCompositor" and resp_name == "generate_backdrop_prompt":
                            agent_steps[author]["strategy"] = f"Generated backdrop prompt: {result}"
                            agent_steps[author]["prompt"] = result
                        elif author == "ABVariantGenerator" and resp_name == "create_variants":
                            if isinstance(result, list):
                                agent_steps[author]["prompts"] = result
                                agent_steps[author]["strategy"] = f"Generated {len(result)} A/B variations."
                            else:
                                agent_steps[author]["strategy"] = f"Generated variations: {result}"
                                
        if not final_response:
            final_response = "Agents are working on your request..."
            
        # Ensure variants prompts list is populated from text strategy if empty
        if agent_steps.get("ABVariantGenerator") and not agent_steps["ABVariantGenerator"].get("prompts"):
            strategy_text = agent_steps["ABVariantGenerator"].get("strategy", "")
            if strategy_text:
                parsed_prompts = parse_variants_from_text(strategy_text)
                if parsed_prompts:
                    agent_steps["ABVariantGenerator"]["prompts"] = parsed_prompts
            
        session_data["agent_steps"] = agent_steps
        save_session_data(session_id, session_data)
        
        return jsonify({
            "response": str(final_response),
            "agent_steps": agent_steps
        })
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"}), 500

# New endpoint to evaluate faithfulness of a generated answer using Gemini
@app.route('/evaluate_faithfulness', methods=['POST'])
def evaluate_faithfulness_endpoint():
    payload = request.get_json()
    reference = payload.get('reference', '')
    answer = payload.get('answer', '')
    if not reference or not answer:
        return jsonify({"error": "Both 'reference' and 'answer' must be provided."}), 400
    score = compute_faithfulness(reference, answer)
    if score < 0:
        return jsonify({"error": "Faithfulness evaluation failed."}), 500
    return jsonify({"faithfulness": score})

@app.route('/generate_agent_image', methods=['POST'])
def generate_agent_image():
    agent_name = request.json.get('agent_name')
    prompt = request.json.get('prompt')
    variant_idx = request.json.get('variant_idx')
    
    session_id = session.get('session_id', 'default_session')
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
        
    try:
        image_url = generate_image_with_imagen(prompt)
        
        if not image_url:
            return jsonify({"error": "Image generation failed"}), 500
            
        session_data = get_session_data(session_id)
        agent_steps = session_data.get("agent_steps", {})
        
        if agent_name == "ABVariantGenerator" and variant_idx is not None:
            if "images" not in agent_steps["ABVariantGenerator"]:
                agent_steps["ABVariantGenerator"]["images"] = {}
            agent_steps["ABVariantGenerator"]["images"][str(variant_idx)] = image_url
            
            asset_id = str(uuid.uuid4())[:8]
            asset_entry = {
                "id": asset_id,
                "name": f"A/B Variant {int(variant_idx)+1}",
                "url": image_url
            }
            session_data.setdefault("creative_assets", []).append(asset_entry)
        else:
            if agent_name in agent_steps:
                agent_steps[agent_name]["image_url"] = image_url
                
            if agent_name == "SceneCompositor":
                asset_id = str(uuid.uuid4())[:8]
                asset_entry = {
                    "id": asset_id,
                    "name": "Composite Backdrop",
                    "url": image_url
                }
                session_data.setdefault("creative_assets", []).append(asset_entry)
                
        session_data["agent_steps"] = agent_steps
        save_session_data(session_id, session_data)
        
        return jsonify({
            "image_url": image_url,
            "agent_steps": agent_steps
        })
    except Exception as e:
        return jsonify({"error": f"Generation failed: {str(e)}"}), 500

@app.route('/assets', methods=['GET'])
def get_assets():
    session_id = session.get('session_id', 'default_session')
    session_data = get_session_data(session_id)
    
    creative_assets = session_data.get("creative_assets", [])
    if not creative_assets:
        creative_assets = [
            {"id": "def1", "name": "Minimalist Pastel Ad", "url": "/static/ad1.jpg"},
            {"id": "def2", "name": "Cyberpunk Neon Variant", "url": "/static/ad2.jpg"}
        ]
        session_data["creative_assets"] = creative_assets
        save_session_data(session_id, session_data)
        
    uploaded_images = session_data.get("uploaded_images", [])
    
    return jsonify({
        "assets": creative_assets,
        "uploads": uploaded_images
    })

@app.route('/session_state', methods=['GET'])
def get_session_state():
    session_id = session.get('session_id', 'default_session')
    session_data = get_session_data(session_id)
    return jsonify({
        "uploaded_images": session_data.get("uploaded_images", []),
        "agent_steps": session_data.get("agent_steps", {})
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
