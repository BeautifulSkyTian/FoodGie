from flask import Flask, request, render_template, jsonify
from google import genai
import os
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# id for the json bin. Stores all data.
BIN_ID = '68fd3db7d0ea881f40bbb460'

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    prompt = "In json format, Tell me the calories of the food in the image? Assume everything was bought on October 21st, 2020, and was stored in the fridge. Give roughly how long it will last."
    image_url = request.form.get("image_url")
    image_file = request.files.get("image_file")

    parts = [{"text": prompt}]

    if image_url:
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            parts.append(
                {"inline_data": {"mime_type": "image/jpeg", "data": response.content}}
            )
        except Exception as e:
            return jsonify({"error": f"Failed to fetch image: {str(e)}"}), 400

    elif image_file:
        parts.append(
            {
                "inline_data": {
                    "mime_type": image_file.mimetype,
                    "data": image_file.read(),
                }
            }
        )
    else:
        return jsonify({"error": "No image provided"}), 400

    gemini_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[{"role": "user", "parts": parts}],
    )

    return jsonify({"response": gemini_response.text})


if __name__ == "__main__":
    app.run(debug=True)
