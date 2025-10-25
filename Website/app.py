from flask import Flask, request, render_template, jsonify
from google import genai
import os
from dotenv import load_dotenv
import requests  # <-- new import

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    prompt = request.form.get("prompt", "Describe this image in plain english and do not give me JSON format.")
    image_url = request.form.get("image_url")
    image_file = request.files.get("image_file")

    parts = [{"text": prompt}]

    if image_url:
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": response.content
                }
            })
        except Exception as e:
            return jsonify({"error": f"Failed to fetch image: {str(e)}"}), 400

    elif image_file:
        parts.append({
            "inline_data": {
                "mime_type": image_file.mimetype,
                "data": image_file.read()
            }
        })
    else:
        return jsonify({"error": "No image provided"}), 400

    gemini_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[{"role": "user", "parts": parts}],
    )

    return jsonify({"response": gemini_response.text})

if __name__ == "__main__":
    app.run(debug=True)
