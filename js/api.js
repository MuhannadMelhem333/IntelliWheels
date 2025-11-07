/**
 * API Client for IntelliWheels
 * Handles all API communication with the backend
 */

const API_BASE_URL = 'http://localhost:5000/api';
const USER_SESSION = localStorage.getItem('userSession') || `session-${Date.now()}`;

// Initialize user session
if (!localStorage.getItem('userSession')) {
    localStorage.setItem('userSession', USER_SESSION);
}

/**
 * Generic API request handler
 */
async function apiRequest(endpoint, options = {}) {
    try {
        const url = `${API_BASE_URL}${endpoint}`;
        console.log('API Request:', url, options.method || 'GET');
        
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            let errorData;
            try {
                errorData = JSON.parse(errorText);
            } catch {
                errorData = { error: errorText || `HTTP error! status: ${response.status}` };
            }
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API Error:', error);
        // Return error response instead of throwing
        return {
            success: false,
            error: error.message || 'Network error occurred'
        };
    }
}

/**
 * Get all cars with optional filters
 */
export async function getCars(filters = {}) {
    const params = new URLSearchParams();
    
    if (filters.make) params.append('make', filters.make);
    if (filters.search) params.append('search', filters.search);
    if (filters.sort) params.append('sort', filters.sort);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.offset) params.append('offset', filters.offset);
    
    const queryString = params.toString();
    const endpoint = `/cars${queryString ? `?${queryString}` : ''}`;
    
    return await apiRequest(endpoint);
}

/**
 * Get a single car by ID
 */
export async function getCar(carId) {
    return await apiRequest(`/cars/${carId}`);
}

/**
 * Create a new car listing
 */
export async function createCar(carData) {
    return await apiRequest('/cars', {
        method: 'POST',
        body: JSON.stringify(carData)
    });
}

/**
 * Update an existing car
 */
export async function updateCar(carId, updates) {
    return await apiRequest(`/cars/${carId}`, {
        method: 'PATCH',
        body: JSON.stringify(updates)
    });
}

/**
 * Delete a car
 */
export async function deleteCar(carId) {
    return await apiRequest(`/cars/${carId}`, {
        method: 'DELETE'
    });
}

/**
 * Get all unique makes
 */
export async function getMakes() {
    return await apiRequest('/makes');
}

/**
 * Get user's favorite cars
 */
export async function getFavorites() {
    return await apiRequest(`/favorites?session=${USER_SESSION}`);
}

/**
 * Add a car to favorites
 */
export async function addFavorite(carId) {
    return await apiRequest('/favorites', {
        method: 'POST',
        body: JSON.stringify({
            car_id: carId,
            session: USER_SESSION
        })
    });
}

/**
 * Remove a car from favorites
 */
export async function removeFavorite(carId) {
    return await apiRequest(`/favorites/${carId}?session=${USER_SESSION}`, {
        method: 'DELETE'
    });
}

/**
 * Send a message to the AI chatbot
 * @param {string} query - The user's message
 * @param {string} apiKey - The Gemini API key
 * @param {Array} history - Conversation history array with {role: 'user'|'bot', text: string}
 */
export async function handleChatbotQuery(query, apiKey, history = []) {
    if (!apiKey || apiKey.trim() === '' || apiKey === 'YOUR_GEMINI_API_KEY_HERE') {
        return "Error: API key is missing. Please add your Gemini API key to enable the chatbot.";
    }

    try {
        console.log('Sending chatbot query:', query);
        console.log('Conversation history length:', history.length);
        const response = await apiRequest('/chatbot', {
            method: 'POST',
            body: JSON.stringify({
                query: query,
                api_key: apiKey,
                history: history, // Send conversation history
                session: USER_SESSION // Send session id for server-side memory
            })
        });

        console.log('Chatbot response:', response);

        if (response.success) {
            return response.response || "I'm sorry, I couldn't generate a response.";
        } else {
            // Return the error message from the backend
            return `Error: ${response.error || "I couldn't generate a response. Please try again."}`;
        }
    } catch (error) {
        console.error('Chatbot error:', error);
        return `Error: An error occurred while processing your request. ${error.message || 'Please try again later.'}`;
    }
}

/**
 * Health check
 */
export async function healthCheck() {
    try {
        return await apiRequest('/health');
    } catch (error) {
        return { success: false, error: 'Backend not available' };
    }
}
