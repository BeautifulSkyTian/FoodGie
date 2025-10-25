from google import genai
from google.genai import types

import requests

# The client gets the API key from the environment variable `GEMINI_API_KEY`.

image_path = "https://goo.gle/instrument-img"
image_bytes = requests.get(image_path).content
image = types.Part.from_bytes(
  data=image_bytes, mime_type="image/jpeg"
)

client = genai.Client(api_key = "AIzaSyAIw8tv1i_xCvy6njP1jRv-YP5dhK6hRfg")

response = client.models.generate_content(
    model="gemini-2.5-flash", 
    contents=["What is this image?", image],
)
print(response.text)