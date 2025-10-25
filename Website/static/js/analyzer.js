// Analyzer module - handles form submission and API communication
class FoodAnalyzer {
  constructor() {
    this.form = document.getElementById("analyze-form");
    this.resultDiv = document.getElementById("result");
    this.fileInput = document.getElementById("image_file");
    this.fileLabel = this.fileInput.nextElementSibling.querySelector('.file-input-text');
    
    this.initEventListeners();
  }

  initEventListeners() {
    this.form.addEventListener("submit", (e) => this.handleSubmit(e));
    
    // Update file input label when file is selected
    this.fileInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        this.fileLabel.textContent = e.target.files[0].name;
      } else {
        this.fileLabel.textContent = "Choose file...";
      }
    });

    // Listen for camera events
    window.addEventListener('photoCapture', (e) => {
      this.showMessage(e.detail.message, 'success');
    });

    window.addEventListener('photoRetake', () => {
      this.clearMessage();
    });
  }

  async handleSubmit(e) {
    e.preventDefault();

    const formData = new FormData();
    
    // Priority: captured photo > uploaded file > URL
    const capturedBlob = camera.getCapturedBlob();
    const urlValue = this.form.elements.image_url.value.trim();
    
    if (capturedBlob) {
      formData.append("image_file", capturedBlob, "camera-capture.jpg");
      console.log("Using captured photo");
    } else if (this.fileInput.files[0]) {
      formData.append("image_file", this.fileInput.files[0]);
      console.log("Using uploaded file");
    } else if (urlValue) {
      formData.append("image_url", urlValue);
      console.log("Using URL:", urlValue);
    } else {
      this.showMessage("Please provide an image (upload, URL, or camera)", 'error');
      return;
    }

    this.showMessage("⏳ Analyzing image...", 'loading');

    try {
      const res = await fetch("/analyze", {
        method: "POST",
        body: formData
      });

      console.log("Response status:", res.status);
      console.log("Response headers:", res.headers.get('content-type'));
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const responseText = await res.text();
      console.log("Raw response text:", responseText);
      
      const data = JSON.parse(responseText);
      console.log("Parsed data:", data);
      console.log("data.response exists:", !!data.response);
      console.log("data.response value:", data.response);
      
      if (data.response) {
        const formattedResponse = this.formatResponse(data.response);
        console.log("Formatted response:", formattedResponse);
        this.showMessage(`💬 <strong>Gemini says:</strong><br>${formattedResponse}`, 'success');
      } else if (data.error) {
        this.showMessage(`Error: ${data.error}`, 'error');
      } else {
        this.showMessage(`Error: Unexpected response format`, 'error');
      }
    } catch (error) {
      console.error("Analysis error:", error);
      this.showMessage(`Error: ${error.message}`, 'error');
    }
  }

  formatResponse(response) {
    // Try to parse and format JSON response nicely
    try {
      // Extract JSON from markdown code blocks or plain text
      const jsonMatch = response.match(/```json\s*([\s\S]*?)\s*```/);
      let jsonStr;
      
      if (jsonMatch && jsonMatch[1]) {
        jsonStr = jsonMatch[1].trim();
      } else {
        // Try to find JSON object directly
        const directMatch = response.match(/\{[\s\S]*\}/);
        if (directMatch) {
          jsonStr = directMatch[0];
        }
      }
      
      if (jsonStr) {
        console.log("Extracted JSON string:", jsonStr);
        const parsed = JSON.parse(jsonStr);
        console.log("Parsed JSON object:", parsed);
        
        let formatted = '<div style="text-align: left; margin-top: 0.5rem;">';
        
        // Check if response has nested food items (like "bananas": {...})
        const keys = Object.keys(parsed);
        let foodData = parsed;
        
        // If the first key looks like a food item, use that nested object
        if (keys.length === 1 && typeof parsed[keys[0]] === 'object') {
          const potentialFoodKey = keys[0];
          if (!['calories', 'food', 'items', 'total_calories'].includes(potentialFoodKey)) {
            foodData = parsed[potentialFoodKey];
            formatted += `<div style="margin-bottom: 0.5rem;"><strong>🍌 Food:</strong> ${potentialFoodKey}`;
            if (foodData.quantity) {
              formatted += ` (${foodData.quantity}${foodData.unit ? ' ' + foodData.unit : ''})`;
            }
            formatted += `</div>`;
          }
        }
        
        // Handle top-level food property
        if (parsed.food) {
          formatted += `<div style="margin-bottom: 0.5rem;"><strong>🍌 Food:</strong> ${parsed.food}`;
          if (parsed.quantity) {
            formatted += ` (${parsed.quantity}${parsed.unit ? ' ' + parsed.unit : ''})`;
          }
          formatted += `</div>`;
        }
        
        // Type
        if (foodData.type) {
          formatted += `<div style="margin-bottom: 0.5rem;"><strong>📦 Type:</strong> ${foodData.type}</div>`;
        }
        
        // Calories
        if (foodData.calories_per_banana || foodData.calories_per_item || parsed.calories_per_banana || parsed.calories_per_item) {
          const caloriesPer = foodData.calories_per_banana || foodData.calories_per_item || parsed.calories_per_banana || parsed.calories_per_item;
          formatted += `<div style="margin-bottom: 0.5rem;"><strong>🔥 Calories per item:</strong> ${caloriesPer}</div>`;
        }
        
        if (foodData.total_calories || foodData.calories || parsed.total_calories || parsed.calories) {
          const totalCal = foodData.total_calories || foodData.calories || parsed.total_calories || parsed.calories;
          formatted += `<div style="margin-bottom: 0.5rem;"><strong>🔥 Calories:</strong> ${totalCal}</div>`;
        }
        
        // Freshness/Expiry
        if (foodData.expected_expiry_date || foodData.expiry_date || parsed.expected_expiry_date || parsed.expiry_date) {
          const expiry = foodData.expected_expiry_date || foodData.expiry_date || parsed.expected_expiry_date || parsed.expiry_date;
          formatted += `<div style="margin-bottom: 0.5rem;"><strong>⏰ Expected Expiry:</strong> ${expiry}</div>`;
        }
        
        if (foodData.estimated_shelf_life || foodData.freshness || foodData.shelf_life || parsed.estimated_shelf_life || parsed.freshness || parsed.shelf_life) {
          const freshness = foodData.estimated_shelf_life || foodData.freshness || foodData.shelf_life || parsed.estimated_shelf_life || parsed.freshness || parsed.shelf_life;
          formatted += `<div style="margin-bottom: 0.5rem;"><strong>📅 Shelf Life:</strong> ${freshness}</div>`;
        }
        
        // Storage
        if (foodData.storage || parsed.storage) {
          formatted += `<div style="margin-bottom: 0.5rem;"><strong>🧊 Storage:</strong> ${foodData.storage || parsed.storage}</div>`;
        }
        
        // Purchase date
        if (foodData.purchase_date || parsed.purchase_date) {
          formatted += `<div style="margin-bottom: 0.5rem;"><strong>📆 Purchase Date:</strong> ${foodData.purchase_date || parsed.purchase_date}</div>`;
        }
        
        // Items array
        if (parsed.items && Array.isArray(parsed.items)) {
          formatted += '<div style="margin-top: 0.5rem;"><strong>Items:</strong><ul style="margin: 0.25rem 0 0 1.5rem;">';
          parsed.items.forEach(item => {
            formatted += `<li>${typeof item === 'object' ? JSON.stringify(item) : item}</li>`;
          });
          formatted += '</ul></div>';
        }
        
        formatted += '</div>';
        console.log("Final formatted HTML:", formatted);
        return formatted;
      }
    } catch (e) {
      console.log("JSON parsing failed:", e);
    }
    
    // If not JSON or parsing failed, return formatted text
    return response.replace(/\n/g, '<br>');
  }

  showMessage(message, type = 'loading') {
    this.resultDiv.innerHTML = `<p>${message}</p>`;
    this.resultDiv.className = `result ${type}`;
  }

  clearMessage() {
    this.resultDiv.innerHTML = '';
    this.resultDiv.className = 'result';
  }
}

// Initialize analyzer when DOM is ready
const analyzer = new FoodAnalyzer();
