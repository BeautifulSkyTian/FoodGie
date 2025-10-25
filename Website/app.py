from flask import Flask, request, render_template, jsonify
from google import genai
import os
from dotenv import load_dotenv
import requests
import data

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# id for the json bin. Stores all data.
BIN_ID = '68fd49ac43b1c97be980cfb7'

# id for testing only, contains garbage.
TEST_BIN_ID = '68fd3d3c43b1c97be980b98b'

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    prompt = """In python dictionary format, give me the following info for each food item in the image: name, type (e.g. protein/fruit/vegetable),
    quantity(number if possible, or weight. Return this as an integer, even weight),
    expected_expiry_date (assume the date is bought on the day, and the item is put in a fridge).
    and calories. Format: {
            "inventory": [
                {
                    "name": "orange",
                    "type": "fruit",
                    "quantity": 6,
                    "expected_expiry_date": "18/11/2025",
                    "calories": 62
                },
                { # GROUND BEEF BATCH 2 (Later Expiry, New Quantity)
                    "name": "ground beef",
                    "type": "protein",
                    "quantity": 500.0,
                    "expected_expiry_date": "20/11/2025",
                    "calories": 1250
                }
            ]
        }"""
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

    gemini_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[{"role": "user", "parts": parts}],
    )
    print(gemini_response.text)

    # change TEST_BIN_ID to BIN_ID for actual use
    data.store_data_to_bin(data.parse_gemini_inventory_output(gemini_response.text), TEST_BIN_ID)

    return jsonify({"response": gemini_response.text})


if __name__ == "__main__":
    app.run(debug=True)
    
