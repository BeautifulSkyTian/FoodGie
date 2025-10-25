import requests
import json
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime

# =================================================================
# IMPORTANT CONFIGURATION
# 1. Replace the placeholder below with your actual JSONBin.io Master Key.
# 2. To run the example, you may need to install the requests library: pip install requests
# =================================================================
MASTER_KEY = "$2a$10$1JnkDOp7Tc3LAEWBU2ecie3nZWb/4wHlADCzhV0L4xSD3lkjNSYuC"
BASE_URL = "https://api.jsonbin.io/v3/b"


# --- Utility Function for Expiry Date Sorting ---

def _parse_expiry_date(date_str: str) -> datetime:
    """Converts a DD/MM/YYYY string to a datetime object for sorting."""
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except (ValueError, TypeError):
        # If parsing fails, treat it as the maximum date (i.e., expire last)
        print(f"Warning: Could not parse date '{date_str}'. Treating as last to expire.")
        return datetime.max


# --- Core JSONBin Functions ---

def read_data_from_bin(bin_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the JSON data (the record dictionary containing "inventory")
    from a specified public bin.
    """
    url = f"{BASE_URL}/{bin_id}"
    print(f"\n-> Attempting to READ data from bin: {bin_id}")

    headers = {
        'Content-Type': 'application/json',
        'X-Master-Key': MASTER_KEY
    }

    response = requests.get(url, headers=headers)

    try:
        response.raise_for_status()
        result = response.json()
        print("   Success! Data retrieved.")
        return result.get('record')

    except requests.exceptions.HTTPError as err:
        print(f"   API Error occurred during read: {err}")
        return None
    except Exception as e:
        print(f"   An unexpected error occurred: {e}")
        return None


def store_data_to_bin(data: Dict[str, List[Dict[str, Any]]], bin_id: Optional[str] = None) -> Optional[str]:
    """
    Creates a new JSONBin or performs an ADDITIVE UPDATE (list merge) on an existing one.

    The merge logic retrieves the existing list of items and appends the new list
    to preserve unique entries.

    Args:
        data: The data to store/merge. Expected format: {"inventory": [list of food items]}.
        bin_id: The ID of an existing bin to update/merge. If None, a new bin is created.

    Returns:
        The ID of the newly created bin (if created), or None (if updated or failed).
    """
    if MASTER_KEY == "YOUR_MASTER_KEY_HERE":
        print("ERROR: Please update the MASTER_KEY variable with your actual key.")
        return None

    headers = {
        'Content-Type': 'application/json',
        'X-Master-Key': MASTER_KEY,
        'X-Bin-Private': 'false'
    }

    final_data_to_store = data

    if bin_id:
        # Case 1: ADDITIVE UPDATE (Read -> Merge -> Write)

        existing_data_wrapper = read_data_from_bin(bin_id)

        if existing_data_wrapper is None:
            print("   Failed to read existing data. Aborting merge update.")
            return None

        existing_inventory: List[Dict[str, Any]] = existing_data_wrapper.get("inventory", [])
        new_items: List[Dict[str, Any]] = data.get("inventory", [])

        # Core merge logic: extend the existing list with new items
        existing_inventory.extend(new_items)
        print(f"   MERGE: Added {len(new_items)} new item(s) to the inventory list.")

        final_data_to_store = {"inventory": existing_inventory}

        # WRITE the MERGED data back (PUT request)
        url = f"{BASE_URL}/{bin_id}"
        print(f"-> Attempting to WRITE merged data back to bin: {bin_id}")
        response = requests.put(url, headers=headers, data=json.dumps(final_data_to_store))

    else:
        # Case 2: CREATE new bin (POST request)
        url = BASE_URL
        print("-> Attempting to CREATE new bin.")
        response = requests.post(url, headers=headers, data=json.dumps(data))

    try:
        response.raise_for_status()
        result = response.json()

        if bin_id:
            print(f"   Success! Bin {bin_id} updated successfully with merged data.")
            return None
        else:
            new_id = result['metadata']['id']
            print(f"   Success! New bin created with ID: {new_id}")
            return new_id

    except requests.exceptions.HTTPError as err:
        print(f"   API Error occurred: {err}")
        return None
    except Exception as e:
        print(f"   An unexpected error occurred: {e}")
        return None


# --- NEW FUNCTION FOR CONSUMPTION ---

def consume_data_from_bin(bin_id: str, consumed_map: Dict[str, Any]) -> None:
    """
    Subtracts consumed amounts from the inventory, prioritizing items
    with the earliest expiry date (FIFO).

    Args:
        bin_id: The ID of the bin to update.
        consumed_map: A dictionary mapping food name to consumed amount (e.g., {"apple": 2}).
    """
    print("\n" + "#" * 60)
    print(f"STARTING CONSUMPTION LOGIC for bin: {bin_id}")
    print("#" * 60)

    # 1. READ existing data
    existing_data_wrapper = read_data_from_bin(bin_id)
    if existing_data_wrapper is None:
        print("Error: Could not retrieve data for consumption.")
        return

    # Get the mutable inventory list
    inventory: List[Dict[str, Any]] = existing_data_wrapper.get("inventory", [])

    # List to hold the items that will be kept (i.e., not fully consumed)
    updated_inventory = []

    # 2. Process Consumption for Each Item Type
    for item_name, amount_to_consume in consumed_map.items():
        if not (isinstance(amount_to_consume, (int, float)) and amount_to_consume > 0):
            print(f"Skipping consumption for '{item_name}': Invalid or non-positive amount.")
            continue

        print(f"Processing consumption for {amount_to_consume} unit(s) of '{item_name}'.")

        # a. Filter and Sort All Matching Items by Expiry Date
        matching_entries: List[Dict[str, Any]] = [
            item for item in inventory if item.get('name', '').lower() == item_name.lower()
        ]

        # Sort by earliest expiry date (using the custom parse function)
        matching_entries.sort(key=lambda item: _parse_expiry_date(item.get('expected_expiry_date', '')))

        current_consumed = amount_to_consume
        items_to_keep = []

        # b. Consume from the oldest item first
        for entry in matching_entries:
            if current_consumed <= 0:
                # No more to consume, keep this item and all subsequent items
                items_to_keep.append(entry)
                continue

            quantity = entry.get('quantity')

            # Skip entries with non-numerical or zero quantity
            if not isinstance(quantity, (int, float)) or quantity <= 0:
                items_to_keep.append(entry)
                continue

            # Consumption logic
            if quantity >= current_consumed:
                # Consumed amount is less than or equal to current entry quantity
                entry['quantity'] -= current_consumed
                current_consumed = 0

                if entry['quantity'] > 0:
                    items_to_keep.append(entry)

                print(f"   -> Consumed fully from entry. Remaining in inventory: {entry.get('quantity', 0)}.")
            else:
                # Consumed amount is GREATER than current entry quantity. Consume all of this entry.
                current_consumed -= quantity
                print(
                    f"   -> Fully consumed batch expiring {entry.get('expected_expiry_date')}. {current_consumed} left to consume.")

        # If any was left to consume, report it
        if current_consumed > 0:
            print(f"Warning: Could not find enough '{item_name}'. {current_consumed} units remain unconsumed.")

        # c. Update the main inventory list with the consumed items
        # Remove all old matching entries and add back the ones that were partially consumed/saved

        # Find items that were NOT consumed and add them to the list for keeping
        inventory = [
            item for item in inventory
            if item.get('name', '').lower() != item_name.lower() or item in items_to_keep
        ]

    # 3. WRITE the updated data back (using store_data_to_bin PUT logic)
    final_data_to_store = {"inventory": inventory}

    url = f"{BASE_URL}/{bin_id}"
    print("\n-> FINAL STEP: Writing updated inventory back.")

    headers = {
        'Content-Type': 'application/json',
        'X-Master-Key': MASTER_KEY
    }

    # We use requests.put directly here to avoid re-reading the data inside store_data_to_bin
    response = requests.put(url, headers=headers, data=json.dumps(final_data_to_store))

    try:
        response.raise_for_status()
        print(f"   Success! Bin {bin_id} updated after consumption.")
    except Exception as e:
        print(f"   Error during final update: {e}")

    print("#" * 60 + "\n")


# Example Usage
if __name__ == "__main__":

    # -----------------------------------------------------------
    # 1. CREATE INITIAL BIN with two batches of apples
    # -----------------------------------------------------------
    initial_inventory = {
        "inventory": [
            {  # APPLE BATCH 1 (EARLIER EXPIRY)
                "name": "apple",
                "type": "fruit",
                "quantity": 3,
                "expected_expiry_date": "15/11/2025",
                "calories": 95
            },
            {
                "name": "lettuce",
                "type": "vegetable",
                "quantity": 1,
                "expected_expiry_date": "02/11/2025",
                "calories": 50
            },
            {  # APPLE BATCH 2 (LATER EXPIRY)
                "name": "apple",
                "type": "fruit",
                "quantity": 4,
                "expected_expiry_date": "01/12/2025",
                "calories": 95
            }
        ]
    }

    print("--- 1. CREATING INITIAL INVENTORY ---")
    new_bin_id = store_data_to_bin(initial_inventory)

    # -----------------------------------------------------------
    # 2. PERFORM CONSUMPTION
    # Total apples: 3 (Batch 1) + 4 (Batch 2) = 7
    # We will consume 5 apples. The logic should prioritize Batch 1 (3 apples)
    # and then take the remaining 2 apples from Batch 2.
    # Expected result: Batch 1 removed, Batch 2 quantity reduced from 4 to 2.
    # -----------------------------------------------------------
    if new_bin_id:
        MY_BIN_ID = new_bin_id

        consumed = {
            "apple": 5,  # Consuming 5 apples total
            "lettuce": 0.5  # Consuming half a head of lettuce
        }

        consume_data_from_bin(MY_BIN_ID, consumed)

        # -----------------------------------------------------------
        # 3. READ THE FINAL DATA
        # -----------------------------------------------------------
        retrieved_final_data = read_data_from_bin(MY_BIN_ID)

        if retrieved_final_data:
            print("\n--- FINAL RETRIEVED INVENTORY ---")
            print("Expected: 1 lettuce entry (0.5 remaining), 1 apple entry (2 remaining).")
            print("---------------------------------")
            print(json.dumps(retrieved_final_data, indent=2))
            print("---------------------------------")
    else:
        print("\nCould not run consumption examples because the initial bin creation failed.")
