class RecipeManager {
  constructor() {
    this.form = document.getElementById("recipe-form");
    this.recipesContainer = document.getElementById("recipes-container");
    this.loadingState = document.getElementById("loading");
    this.emptyState = document.getElementById("empty-state");
    this.calorieTracker = window.calorieTracker;

    // Wait for calorie tracker to be ready
    if (!this.calorieTracker) {
      console.warn('Calorie tracker not immediately available, waiting...');
      setTimeout(() => {
        this.calorieTracker = window.calorieTracker;
        this.displayCalorieSummary();
      }, 100);
    } else {
      this.displayCalorieSummary();
    }

    this.initEventListeners();
  }

  initEventListeners() {
    this.form.addEventListener("submit", (e) => this.handleSubmit(e));
  }

  displayCalorieSummary() {
    // Remove existing banner if present
    const existingBanner = document.querySelector('.calorie-summary-banner');
    if (existingBanner) {
      existingBanner.remove();
    }

    if (!this.calorieTracker) {
      console.warn('Calorie tracker not available for summary display');
      return;
    }

    const summary = this.calorieTracker.getSummary();
    const settings = JSON.parse(localStorage.getItem('foogie-settings') || '{}');
    
    // Only show if user has enabled calorie progress
    if (settings.showCalorieProgress === false) {
      console.log('Calorie progress display disabled in settings');
      return;
    }

    const summaryDiv = document.createElement("div");
    summaryDiv.className = "calorie-summary-banner";
    summaryDiv.innerHTML = `
      <div class="calorie-banner-content">
        <div class="calorie-stat">
          <span class="stat-label">Daily Goal</span>
          <span class="stat-value">${summary.goal} cal</span>
        </div>
        <div class="calorie-stat">
          <span class="stat-label">Consumed</span>
          <span class="stat-value ${summary.isOverGoal ? 'over-goal' : ''}">${summary.consumed} cal</span>
        </div>
        <div class="calorie-stat highlight">
          <span class="stat-label">Remaining</span>
          <span class="stat-value ${summary.isOverGoal ? 'over-goal' : ''}">${summary.remaining} cal</span>
        </div>
        <div class="calorie-stat">
          <span class="stat-label">Per Meal (${summary.mealsLeft} left)</span>
          <span class="stat-value">${summary.caloriesPerMeal} cal</span>
        </div>
      </div>
      <div class="calorie-progress-bar">
        <div class="progress-fill" style="width: ${Math.min(summary.percentConsumed, 100)}%"></div>
      </div>
    `;

    // Insert before the main card
    const mainCard = document.querySelector("main .card");
    if (mainCard) {
      mainCard.parentNode.insertBefore(summaryDiv, mainCard);
      console.log('Calorie summary banner displayed:', summary);
    }
  }

  async handleSubmit(e) {
    e.preventDefault();

    const formData = new FormData(this.form);
    
    // Get target calories per meal - ensure we're using the tracker correctly
    let targetCaloriesPerMeal = 500; // Default fallback
    
    if (this.calorieTracker) {
      const summary = this.calorieTracker.getSummary();
      targetCaloriesPerMeal = summary.caloriesPerMeal || 500;
      console.log('Using target calories per meal:', targetCaloriesPerMeal, 'from summary:', summary);
    } else {
      console.warn('Calorie tracker not available, using default target calories');
    }

    const requestData = {
      num_recipes: parseInt(formData.get("num_recipes")),
      dietary_restrictions: formData.get("dietary_restrictions").trim(),
      cuisine_preference: formData.get("cuisine_preference").trim(),
      target_calories_per_meal: targetCaloriesPerMeal
    };

    console.log('Sending recipe request:', requestData);

    this.showLoading();

    try {
      const response = await fetch("/api/generate-recipes", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(requestData)
      });

      const data = await response.json();

      if (!response.ok) {
        if (data.error && (data.error.includes("No inventory") || data.error.includes("empty"))) {
          this.showEmptyState();
          return;
        }
        throw new Error(data.error || "Failed to generate recipes");
      }

      if (!data.recipes || data.recipes.length === 0) {
        this.showEmptyState();
        return;
      }

      this.renderRecipes(data.recipes);
    } catch (error) {
      console.error("Error generating recipes:", error);
      this.hideLoading();
      this.recipesContainer.innerHTML = `
        <div class="result error">
          <p><strong>Error:</strong> ${error.message}</p>
        </div>
      `;
    }
  }

  renderRecipes(recipes) {
    this.hideLoading();
    this.emptyState.classList.add("hidden");
    this.recipesContainer.innerHTML = "";

    recipes.forEach((recipe, index) => {
      const recipeCard = this.createRecipeCard(recipe, index);
      this.recipesContainer.appendChild(recipeCard);
    });

    // Smooth scroll to recipes
    this.recipesContainer.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  createRecipeCard(recipe, index) {
    const div = document.createElement("div");
    const urgency = recipe.urgency || "low";
    div.className = `recipe-card urgency-${urgency}`;

    // Format inventory items
    const inventoryItems = recipe.inventory_items_used || [];
    const additionalItems = recipe.additional_ingredients || [];
    const foodTypes = recipe.food_types_used || [];
    const nutrition = recipe.nutrition_per_serving || {};
    const servings = recipe.servings || 1;
    const totalCalories = (nutrition.calories || 0) * servings;

    // Calculate if this fits in remaining calories
    const remaining = this.calorieTracker ? this.calorieTracker.getRemainingCalories() : null;
    const fitsInBudget = remaining === null || totalCalories <= remaining;

    console.log(`Recipe "${recipe.name}": ${totalCalories} cal, Remaining: ${remaining}, Fits: ${fitsInBudget}`);

    div.innerHTML = `
      <div class="recipe-header">
        <div>
          <h3 class="recipe-title">${recipe.name || `Recipe ${index + 1}`}</h3>
          <div class="recipe-meta">
            <span class="meta-badge">
              <span>⏱️</span>
              ${recipe.cooking_time || "N/A"}
            </span>
            <span class="meta-badge">
              <span>🍽️</span>
              ${servings} serving${servings !== 1 ? 's' : ''}
            </span>
            ${foodTypes.length > 0 ? `
              <span class="meta-badge">
                <span>🎯</span>
                ${foodTypes.join(", ")}
              </span>
            ` : ''}
            ${recipe.inventory_only ? `
              <span class="meta-badge inventory-only-badge">
                <span>🏠</span>
                Fridge Only
              </span>
            ` : ''}
            ${remaining !== null ? `
              <span class="meta-badge ${fitsInBudget ? 'fits-budget' : 'over-budget'}">
                <span>${fitsInBudget ? '✅' : '⚠️'}</span>
                ${fitsInBudget ? 'Fits budget' : 'Over budget'}
              </span>
            ` : ''}
          </div>
        </div>
        <div class="urgency-section">
          <span class="urgency-badge ${urgency}">
            ${urgency === "high" ? "⚠️ Use Soon" : urgency === "medium" ? "📅 This Week" : "✅ Fresh"}
          </span>
          ${recipe.urgency_reason ? `
            <p class="urgency-reason">${this.escapeHtml(recipe.urgency_reason)}</p>
          ` : ''}
        </div>
      </div>

      ${Object.keys(nutrition).length > 0 ? `
        <div class="recipe-section">
          <h4 class="section-title">
            <span>📊</span>
            Nutrition (per serving)
          </h4>
          <div class="nutrition-grid">
            <div class="nutrition-item">
              <span class="nutrition-icon">🔥</span>
              <div class="nutrition-details">
                <span class="nutrition-value">${nutrition.calories || 0}</span>
                <span class="nutrition-label">Calories</span>
              </div>
            </div>
            <div class="nutrition-item">
              <span class="nutrition-icon">🥩</span>
              <div class="nutrition-details">
                <span class="nutrition-value">${nutrition.protein || 0}g</span>
                <span class="nutrition-label">Protein</span>
              </div>
            </div>
            <div class="nutrition-item">
              <span class="nutrition-icon">🌾</span>
              <div class="nutrition-details">
                <span class="nutrition-value">${nutrition.carbs || 0}g</span>
                <span class="nutrition-label">Carbs</span>
              </div>
            </div>
            <div class="nutrition-item">
              <span class="nutrition-icon">🥑</span>
              <div class="nutrition-details">
                <span class="nutrition-value">${nutrition.fats || 0}g</span>
                <span class="nutrition-label">Fats</span>
              </div>
            </div>
          </div>
          <div class="total-calories-banner">
            <strong>Total for all servings:</strong> ${totalCalories} calories
          </div>
        </div>
      ` : ''}

      <div class="recipe-section">
        <h4 class="section-title">
          <span>🥘</span>
          Ingredients
        </h4>
        <div class="ingredients-grid">
          ${inventoryItems.length > 0 ? `
            <div class="ingredient-group">
              <h4>From Your Fridge</h4>
              <ul class="ingredient-list">
                ${inventoryItems.map(item => `
                  <li class="from-inventory">${this.escapeHtml(item)}</li>
                `).join("")}
              </ul>
            </div>
          ` : ""}
          
          ${additionalItems.length > 0 ? `
            <div class="ingredient-group">
              <h4>Additional Items</h4>
              <ul class="ingredient-list">
                ${additionalItems.map(item => `
                  <li>${this.escapeHtml(item)}</li>
                `).join("")}
              </ul>
            </div>
          ` : ""}
        </div>
      </div>

      <div class="recipe-section">
        <h4 class="section-title">
          <span>👨‍🍳</span>
          Instructions
        </h4>
        <ol class="instructions-list">
          ${(recipe.instructions || []).map(step => `
            <li>${this.escapeHtml(step)}</li>
          `).join("")}
        </ol>
      </div>

      <div class="recipe-actions">
        <button class="btn btn-primary use-recipe-btn" data-recipe-index="${index}">
          <span>✅</span> I Made This! (Log ${totalCalories} cal)
        </button>
      </div>
    `;

    // Add event listener to the use button
    const useBtn = div.querySelector('.use-recipe-btn');
    useBtn.addEventListener('click', () => this.handleUseRecipe(recipe, totalCalories, div));

    return div;
  }

  async handleUseRecipe(recipe, totalCalories, cardElement) {
    if (!this.calorieTracker) {
      alert('Calorie tracking is not available');
      console.error('Calorie tracker not available when trying to log meal');
      return;
    }

    const nutrition = recipe.nutrition_per_serving || {};
    const servings = recipe.servings || 1;

    console.log('Logging meal:', {
      name: recipe.name,
      totalCalories,
      nutrition: {
        protein: (nutrition.protein || 0) * servings,
        carbs: (nutrition.carbs || 0) * servings,
        fats: (nutrition.fats || 0) * servings,
        servings
      }
    });

    // Log the meal
    try {
      await this.calorieTracker.logMeal(recipe.name, totalCalories, {
        protein: (nutrition.protein || 0) * servings,
        carbs: (nutrition.carbs || 0) * servings,
        fats: (nutrition.fats || 0) * servings,
        servings: servings
      });

      // Update the card to show it's been used
      cardElement.classList.add('recipe-used');
      const useBtn = cardElement.querySelector('.use-recipe-btn');
      useBtn.innerHTML = '<span>✅</span> Logged!';
      useBtn.disabled = true;

      // Show success message
      const summary = this.calorieTracker.getSummary();
      const message = document.createElement('div');
      message.className = 'result success';
      message.style.marginTop = '1rem';
      message.innerHTML = `
        <p><strong>Meal logged successfully!</strong></p>
        <p>Remaining today: ${summary.remaining} calories (${summary.mealsLeft} meals left = ~${summary.caloriesPerMeal} cal/meal)</p>
      `;
      cardElement.appendChild(message);

      console.log('Meal logged successfully. New summary:', summary);

      // Refresh the calorie summary banner
      this.displayCalorieSummary();

      // Scroll to top to see updated summary
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (error) {
      console.error('Error logging meal:', error);
      alert('Failed to log meal. Please try again.');
    }
  }

  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  showLoading() {
    this.loadingState.classList.remove("hidden");
    this.recipesContainer.innerHTML = "";
    this.emptyState.classList.add("hidden");
  }

  hideLoading() {
    this.loadingState.classList.add("hidden");
  }

  showEmptyState() {
    this.hideLoading();
    this.recipesContainer.innerHTML = "";
    this.emptyState.classList.remove("hidden");
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM loaded, initializing recipe manager');
  window.recipeManager = new RecipeManager();
});