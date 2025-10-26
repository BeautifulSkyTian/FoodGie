// Calorie Tracker Module
class CalorieTracker {
  constructor() {
    this.storageKey = 'foogie-calorie-log';
    this.settings = this.loadSettings();
    this.initializeDailyLog();
  }

  loadSettings() {
    const settings = JSON.parse(localStorage.getItem('foogie-settings') || '{}');
    return {
      dailyCalories: parseInt(settings.dailyCalories) || 2000,
      dailyMeals: parseInt(settings.dailyMeals) || 3,
      showCalorieProgress: settings.showCalorieProgress !== false
    };
  }

  initializeDailyLog() {
    const today = new Date().toDateString();
    const log = this.getLog();

    // Reset log if it's a new day
    if (log.date !== today) {
      this.resetLog();
    }
  }

  getLog() {
    const log = JSON.parse(localStorage.getItem(this.storageKey) || 'null');
    if (!log) {
      return this.createNewLog();
    }
    return log;
  }

  createNewLog() {
    const newLog = {
      date: new Date().toDateString(),
      meals: [],
      totalCalories: 0,
      totalProtein: 0,
      totalCarbs: 0,
      totalFats: 0
    };
    this.saveLog(newLog);
    return newLog;
  }

  saveLog(log) {
    localStorage.setItem(this.storageKey, JSON.stringify(log));
  }

  resetLog() {
    const newLog = this.createNewLog();
    return newLog;
  }

  async logMeal(name, calories, nutritionData = {}) {
    const log = this.getLog();
    
    const meal = {
      name: name,
      calories: calories,
      protein: nutritionData.protein || 0,
      carbs: nutritionData.carbs || 0,
      fats: nutritionData.fats || 0,
      servings: nutritionData.servings || 1,
      timestamp: new Date().toISOString()
    };

    log.meals.push(meal);
    log.totalCalories += calories;
    log.totalProtein += meal.protein;
    log.totalCarbs += meal.carbs;
    log.totalFats += meal.fats;

    this.saveLog(log);

    // Send to server for tracking
    try {
      await fetch('/api/calorie-tracker', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          calories: calories,
          recipe_name: name
        })
      });
    } catch (error) {
      console.error('Failed to sync with server:', error);
    }

    return meal;
  }

  getRemainingCalories() {
    const log = this.getLog();
    return this.settings.dailyCalories - log.totalCalories;
  }

  getConsumedCalories() {
    const log = this.getLog();
    return log.totalCalories;
  }

  getMealsLeft() {
    const log = this.getLog();
    const mealsEaten = log.meals.length;
    return Math.max(0, this.settings.dailyMeals - mealsEaten);
  }

  getCaloriesPerMeal() {
    const remaining = this.getRemainingCalories();
    const mealsLeft = this.getMealsLeft();
    
    if (mealsLeft === 0) return 0;
    return Math.max(0, Math.round(remaining / mealsLeft));
  }

  getSummary() {
    const log = this.getLog();
    const remaining = this.getRemainingCalories();
    const mealsLeft = this.getMealsLeft();
    const caloriesPerMeal = this.getCaloriesPerMeal();
    const percentConsumed = (log.totalCalories / this.settings.dailyCalories) * 100;

    return {
      goal: this.settings.dailyCalories,
      consumed: log.totalCalories,
      remaining: remaining,
      mealsLeft: mealsLeft,
      caloriesPerMeal: caloriesPerMeal,
      percentConsumed: Math.round(percentConsumed),
      isOverGoal: remaining < 0,
      meals: log.meals,
      nutrition: {
        protein: log.totalProtein,
        carbs: log.totalCarbs,
        fats: log.totalFats
      }
    };
  }

  getTodaysMeals() {
    const log = this.getLog();
    return log.meals;
  }

  deleteMeal(index) {
    const log = this.getLog();
    if (index >= 0 && index < log.meals.length) {
      const meal = log.meals[index];
      
      log.totalCalories -= meal.calories;
      log.totalProtein -= meal.protein;
      log.totalCarbs -= meal.carbs;
      log.totalFats -= meal.fats;
      
      log.meals.splice(index, 1);
      
      this.saveLog(log);
      return true;
    }
    return false;
  }

  updateSettings(newSettings) {
    this.settings = {
      dailyCalories: parseInt(newSettings.dailyCalories) || this.settings.dailyCalories,
      dailyMeals: parseInt(newSettings.dailyMeals) || this.settings.dailyMeals,
      showCalorieProgress: newSettings.showCalorieProgress !== false
    };
  }
}

// Initialize global calorie tracker
window.calorieTracker = new CalorieTracker();
