"""data"""

import requests
import json
from typing import Optional, Dict, Any

# =================================================================
# IMPORTANT CONFIGURATION
# 1. Replace the placeholder below with your actual JSONBin.io Master Key.
# 2. To run the example, you may need to install the requests library: pip install requests
# =================================================================
MASTER_KEY = "$2a$10$1JnkDOp7Tc3LAEWBU2ecie3nZWb/4wHlADCzhV0L4xSD3lkjNSYuC"
BASE_URL = "https://api.jsonbin.io/v3/b"

PROMPT = ("In json format, for every food item in the image, provide the following data: "
          "type(e.g. protein, vegetable, fruit, etc.), "
          "quantity (number if possible, or weight for unquantifiable objects), "
          "expected expiry date in DD/MM/YYYY format, calories."
          "Assume everything was bought on the day this request is made and is stored in the fridge."
          "Store all food items in a single dictionary, and create a dictionary for each item. For example, "
          "json{'apples': {'type': 'fruit', 'quantity': 3, ...}}")

def store_data_to_bin(data: Dict[str, Any], bin_id: Optional[str] = None) -> Optional[str]:
    """
    Creates a new JSONBin or updates an existing one.

    Args:
        data: The JSON data (as a Python dictionary) to store.
        bin_id: The ID of an existing bin to update. If None, a new bin is created.

    Returns:
        The ID of the newly created bin (if created), or None (if updated or failed).
    """
    if MASTER_KEY == "YOUR_MASTER_KEY_HERE":
        print("ERROR: Please update the MASTER_KEY variable with your actual key.")
        return None

    headers = {
        'Content-Type': 'application/json',
        'X-Master-Key': MASTER_KEY,
        # Set the data to be public (accessible via GET without the key)
        'X-Bin-Private': 'false'
    }

    if bin_id:
        # Case 1: UPDATE existing bin (PUT request)
        url = f"{BASE_URL}/{bin_id}"
        print(f"-> Attempting to UPDATE existing bin: {bin_id}")
        response = requests.put(url, headers=headers, data=json.dumps(data))
    else:
        # Case 2: CREATE new bin (POST request)
        url = BASE_URL
        print("-> Attempting to CREATE new bin.")
        response = requests.post(url, headers=headers, data=json.dumps(data))

    try:
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        result = response.json()

        if bin_id:
            print(f"   Success! Bin {bin_id} updated successfully.")
            return None  # No new ID generated for an update
        else:
            new_id = result['metadata']['id']
            print(f"   Success! New bin created with ID: {new_id}")
            return new_id

    except requests.exceptions.HTTPError as err:
        print(f"   API Error occurred: {err}")
        print(f"   Response: {response.text}")
        return None
    except Exception as e:
        print(f"   An unexpected error occurred: {e}")
        return None


def read_data_from_bin(bin_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the JSON data from a specified public bin.

    Args:
        bin_id: The ID of the bin to read.

    Returns:
        The data as a Python dictionary, or None if the request fails.
    """
    url = f"{BASE_URL}/{bin_id}"
    print(f"\n-> Attempting to READ data from bin: {bin_id}")

    # Note: For public bins, the Master Key is typically not required for GET requests
    # unless the bin was created as private.
    headers = {
        'Content-Type': 'application/json',
        'X-Master-Key': MASTER_KEY
    }

    response = requests.get(url, headers=headers)

    try:
        response.raise_for_status()  # Raise an exception for bad status codes
        result = response.json()
        print("   Success! Data retrieved.")
        # The actual data content is usually nested under the 'record' key in the response
        return result.get('record')

    except requests.exceptions.HTTPError as err:
        print(f"   API Error occurred during read: {err}")
        print(f"   Response: {response.text}")
        return None
    except Exception as e:
        print(f"   An unexpected error occurred: {e}")
        return None


# Example Usage
if __name__ == "__main__":

    # -----------------------------------------------------------
    # 1. CREATE A NEW BIN
    # -----------------------------------------------------------
    initial_data = {
        "photo_id": "P_20240115_001",
        "timestamp": "2024-01-15T10:00:00Z",
        "food_items": [
            {"name": "salad", "confidence": 0.95},
            {"name": "chicken breast", "confidence": 0.88}
        ]
    }

    # Pass bin_id=None to create a new bin
    new_bin_id = store_data_to_bin(initial_data)

    # -----------------------------------------------------------
    # 2. READ THE DATA FROM THE NEW BIN
    # -----------------------------------------------------------
    if new_bin_id:
        # Save the new ID for later use
        MY_BIN_ID = new_bin_id

        retrieved_data = read_data_from_bin(MY_BIN_ID)

        if retrieved_data:
            print("\n--- Retrieved Data ---")
            print(json.dumps(retrieved_data, indent=2))
            print("----------------------")

        # -----------------------------------------------------------
        # 3. UPDATE THE EXISTING BIN
        # -----------------------------------------------------------
        updated_data = {
            "photo_id": "P_20240115_002",
            "timestamp": "2024-01-15T14:30:00Z",
            "food_items": [
                {"name": "pizza slice", "confidence": 0.99},
                {"name": "soda", "confidence": 0.75}
            ]
        }

        # Pass the MY_BIN_ID to update the existing bin
        store_data_to_bin(updated_data, bin_id=MY_BIN_ID)

        # -----------------------------------------------------------
        # 4. READ THE UPDATED DATA
        # -----------------------------------------------------------
        retrieved_updated_data = read_data_from_bin(MY_BIN_ID)

        if retrieved_updated_data:
            print("\n--- Retrieved Data After Update ---")
            print(json.dumps(retrieved_updated_data, indent=2))
            print("-----------------------------------")
    else:
        print("\nCould not run read/update examples because the initial bin creation failed.")
