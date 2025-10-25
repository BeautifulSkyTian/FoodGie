from flask import Flask, request, render_template, jsonify
from google import genai
import os
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    prompt = "In json format, Tell me the calories of the food in the image? Assume everything was bought on October 21st, 2020, and was stored in the fridge. Give roughly how long it will last."
    image_url = request.form.get("image_url")
    image_file = request.files.get("image_file")

    print(f"DEBUG - Received image_url: {image_url}")
    print(f"DEBUG - Received image_file: {image_file}")

    parts = [{"text": prompt}]

    if image_url:
        print(f"DEBUG - Attempting to fetch URL: {image_url}")
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            print(
                f"DEBUG - Successfully fetched image, size: {len(response.content)} bytes"
            )
            parts.append(
                {"inline_data": {"mime_type": "image/jpeg", "data": response.content}}
            )
        except Exception as e:
            print(f"DEBUG - Failed to fetch image: {str(e)}")
            return jsonify({"error": f"Failed to fetch image: {str(e)}"}), 400

    elif image_file:
        print(f"DEBUG - Processing uploaded file: {image_file.filename}")
        parts.append(
            {
                "inline_data": {
                    "mime_type": image_file.mimetype,
                    "data": image_file.read(),
                }
            }
        )
    else:
        print("DEBUG - No image provided")
        return jsonify({"error": "No image provided"}), 400

    print("DEBUG - Sending to Gemini API")
    try:
        gemini_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[{"role": "user", "parts": parts}],
        )
        print(f"DEBUG - Gemini response received: {gemini_response.text[:100]}...")
        return jsonify({"response": gemini_response.text})
    except Exception as e:
        print(f"DEBUG - Gemini API error: {str(e)}")
        return jsonify({"error": f"Gemini API error: {str(e)}"}), 500


if __name__ == "__main__":
    # For iOS camera support, run with HTTPS
    # Generate self-signed certificate:
    # openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

    import os

    cert_path = "cert.pem"
    key_path = "key.pem"

    if os.path.exists(cert_path) and os.path.exists(key_path):
        # Run with HTTPS if certificates exist
        app.run(
            debug=True, ssl_context=(cert_path, key_path), host="0.0.0.0", port=5000
        )
    else:
        # Run without HTTPS (camera won't work on iOS)
        print(
            "\n⚠️  WARNING: Running without HTTPS. Camera will not work on iOS Safari."
        )
        print("To enable HTTPS, generate certificates with:")
        print(
            "openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365\n"
        )
        app.run(debug=True)
