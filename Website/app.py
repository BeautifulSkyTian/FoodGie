from flask import Flask, request, render_template, jsonify
from google import genai
import os
from dotenv import load_dotenv
import requests
import data
from datetime import datetime


today_date = datetime.now().strftime("%d/%m/%Y")

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# id for the json bin. Stores all data.
BIN_ID = "68fd49ac43b1c97be980cfb7"

# id for testing only, contains garbage.
TEST_BIN_ID = "68fd3d3c43b1c97be980b98b"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/settings")
def settings():
    return render_template("settings.html")


@app.route("/fridge")
def fridge():
    return render_template("fridge.html")


@app.route("/api/fridge/<bin_id>")
def get_fridge_data(bin_id):
    fridge_data = data.read_data_from_bin(bin_id)
    if fridge_data:
        return jsonify(fridge_data)
    else:
        return jsonify({"error": "Failed to retrieve fridge data"}), 500


@app.route("/api/fridge/<bin_id>", methods=["PUT"])
def update_fridge_data(bin_id):
    updated_data = request.json

    url = f"{data.BASE_URL}/{bin_id}"
    headers = {"Content-Type": "application/json", "X-Master-Key": data.MASTER_KEY}

    response = requests.put(url, headers=headers, data=json.dumps(updated_data))

    try:
        response.raise_for_status()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/analyze", methods=["POST"])
def analyze():
    prompt = f"""Analyze this food image and return the data as a Python dictionary. Follow these guidelines carefully:

    CRITICAL FORMATTING RULES:
    - Return ONLY valid JSON format within a Python dictionary structure
    - Use the exact field names and structure shown in the example
    - All numerical values must be integers (no decimals, no quotes)

    DATA REQUIREMENTS:

    1. NAME: Use common food names (e.g., "coca cola" not "Coca-Cola 330ml can")

    2. TYPE: Choose from: "fruit", "vegetable", "protein", "grains", "dairy", "beverage", "snacks", "condiments"

    3. QUANTITY AND UNITS:
    - quantity: Always an integer number
    - unit: Choose from these exact options:
        * "items" - for individual pieces (fruits, vegetables, packaged items)
        * "grams" - for meat, cheese, bulk foods
        * "containers" - for bottles, cans, cartons, packages
        * "eggs" - specifically for eggs

    RULES:
    - For SOLID items: count individual pieces → unit: "items" (e.g., 6 apples)
    - For LIQUIDS/BEVERAGES: count containers → unit: "containers" (e.g., 2 bottles of soda)
    - For MEAT/PROTEINS: use grams → unit: "grams" (e.g., 500g chicken)
    - For EGGS: use count → unit: "eggs" (e.g., 12 eggs)
    - NEVER use volume measurements (no ml, liters, cups, etc.)

    4. EXPIRY DATE: 
    - **TODAY'S DATE IS: {today_date} - USE THIS AS PURCHASE DATE**
    - Calculate expiry dates based on TODAY being the purchase date
    - Assume refrigerator storage for perishable items
    - Use DD/MM/YYYY format
    - Research realistic shelf life for each food type:
        * Fresh fruits: 3-7 days from today
        * Fresh vegetables: 5-10 days from today  
        * Raw meat/fish: 2-3 days from today
        * Dairy: 7-14 days from today
        * Beverages: 30-180 days from today
        * Packaged snacks: 90-365 days from today

    5. NUTRITION (per entire quantity shown):
    - calories: total calories for the quantity shown
    - carbs: total carbohydrates in grams
    - fats: total fat in grams  
    - protein: total protein in grams
    - All values must be integers representing the TOTAL for the quantity

    UNIT SPECIFIC EXAMPLES:
    - 6 apples → quantity: 6, unit: "items"
    - 2 bottles of milk → quantity: 2, unit: "containers" 
    - 500g chicken → quantity: 500, unit: "grams"
    - 12 eggs → quantity: 12, unit: "eggs"
    - 1 can of soda → quantity: 1, unit: "containers"
    - 3 bananas → quantity: 3, unit: "items"

    EXAMPLE OUTPUT FORMAT:
    {{
        "inventory": [
            {{
                "name": "orange",
                "type": "fruit", 
                "quantity": 6,
                "unit": "items",
                "expected_expiry_date": "{today_date}",
                "calories": 372,
                "carbs": 93,
                "fats": 0,
                "protein": 0
            }},
            {{
                "name": "coca cola", 
                "type": "beverage",
                "quantity": 4,
                "unit": "containers",
                "expected_expiry_date": "15/12/2025",
                "calories": 560,
                "carbs": 140,
                "fats": 0,
                "protein": 0
            }},
            {{
                "name": "chicken breast",
                "type": "protein",
                "quantity": 500,
                "unit": "grams",
                "expected_expiry_date": "05/12/2024",
                "calories": 825,
                "carbs": 0,
                "fats": 18,
                "protein": 100
            }},
            {{
                "name": "eggs",
                "type": "protein", 
                "quantity": 12,
                "unit": "eggs",
                "expected_expiry_date": "25/11/2024",
                "calories": 840,
                "carbs": 0,
                "fats": 60,
                "protein": 72
            }}
        ]
    }}

    IMPORTANT: 
    - Today's purchase date is {today_date} - calculate all expiry dates from this date
    - Be realistic with expiry dates based on common food shelf life
    - Ensure dates are chronologically logical (expiry dates must be AFTER today)
    - Use the exact unit values: "items", "grams", "containers", or "eggs" """
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
    data.store_data_to_bin(
        data.parse_gemini_inventory_output(gemini_response.text), TEST_BIN_ID
    )

    return jsonify({"response": gemini_response.text})


if __name__ == "__main__":
    app.run(debug=True)
