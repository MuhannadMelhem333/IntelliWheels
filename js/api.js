/**
 * API Client for IntelliWheels
 * Handles all API communication with the backend
 */

const API_BASE_URL = 'http://localhost:5000/api';
const USER_SESSION = localStorage.getItem('userSession') || `session-${Date.now()}`;
const AUTH_TOKEN_KEY = 'authToken';
const USER_DATA_KEY = 'userData';

// Initialize user session
if (!localStorage.getItem('userSession')) {
    localStorage.setItem('userSession', USER_SESSION);
}

/**
 * Get authentication token from localStorage
 */
export function getAuthToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * Set authentication token
 */
export function setAuthToken(token) {
    if (token) {
        localStorage.setItem(AUTH_TOKEN_KEY, token);
    } else {
        localStorage.removeItem(AUTH_TOKEN_KEY);
    }
}

/**
 * Get user data from localStorage
 */
export function getUserData() {
    const data = localStorage.getItem(USER_DATA_KEY);
    return data ? JSON.parse(data) : null;
}

/**
 * Set user data
 */
export function setUserData(user) {
    if (user) {
        localStorage.setItem(USER_DATA_KEY, JSON.stringify(user));
    } else {
        localStorage.removeItem(USER_DATA_KEY);
    }
}

/**
 * Generic API request handler with authentication and cancellation support
 */
async function apiRequest(endpoint, options = {}, signal = null) {
    try {
        const url = `${API_BASE_URL}${endpoint}`;
        const token = getAuthToken();
        
        const headers = {
            ...options.headers
        };
        
        // Only set Content-Type for requests with a body
        if (options.body) {
            headers['Content-Type'] = 'application/json';
        }
        
        // Add auth token if available
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const fetchOptions = {
            ...options,
            headers,
            signal // Add abort signal for cancellation
        };
        
        const response = await fetch(url, fetchOptions);
        
        if (!response.ok) {
            const errorText = await response.text();
            let errorData;
            try {
                errorData = JSON.parse(errorText);
            } catch {
                errorData = { error: errorText || `HTTP error! status: ${response.status}` };
            }
            
            // Handle authentication errors
            if (response.status === 401) {
                // Clear auth data and redirect to login
                setAuthToken(null);
                setUserData(null);
                if (window.location.pathname !== '/') {
                    window.location.href = '/';
                }
            }
            
            // Return error response with proper structure
            return {
                success: false,
                error: errorData.error || errorData.message || errorText || `HTTP error! status: ${response.status}`
            };
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        // Handle abort errors gracefully
        if (error.name === 'AbortError') {
            return {
                success: false,
                error: 'Request cancelled'
            };
        }
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
export async function getCars(filters = {}, signal = null) {
    const params = new URLSearchParams();
    
    if (filters.make) params.append('make', filters.make);
    if (filters.search) params.append('search', filters.search);
    if (filters.sort) params.append('sort', filters.sort);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.offset) params.append('offset', filters.offset);
    
    const queryString = params.toString();
    const endpoint = `/cars${queryString ? `?${queryString}` : ''}`;
    
    return await apiRequest(endpoint, {}, signal);
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
    return await apiRequest('/favorites');
}

/**
 * Add a car to favorites
 */
export async function addFavorite(carId) {
    return await apiRequest('/favorites', {
        method: 'POST',
        body: JSON.stringify({
            car_id: carId
        })
    });
}

/**
 * Remove a car from favorites
 */
export async function removeFavorite(carId) {
    return await apiRequest(`/favorites/${carId}`, {
        method: 'DELETE'
    });
}

/**
 * Send a message to the AI chatbot
 * @param {string} query - The user's message
 * @param {string} apiKey - The Gemini API key
 * @param {Array} history - Conversation history array with {role: 'user'|'bot', text: string}
 * @returns {Promise<Object>} Response object with {success, response, intent, relevant_car_ids, error}
 */
export async function handleChatbotQuery(query, apiKey, history = []) {
    if (!apiKey || apiKey.trim() === '' || apiKey === 'YOUR_GEMINI_API_KEY_HERE') {
        return {
            success: false,
            response: "Error: API key is missing. Please add your Gemini API key to enable the chatbot.",
            error: "API key missing"
        };
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
                session: USER_SESSION // User session
            })
        });

        console.log('Chatbot response:', response);

        if (response.success) {
            return {
                success: true,
                response: response.response || "I'm sorry, I couldn't generate a response.",
                intent: response.intent || 'general',
                relevant_car_ids: response.relevant_car_ids || []
            };
        } else {
            return {
                success: false,
                response: `Error: ${response.error || "I couldn't generate a response. Please try again."}`,
                error: response.error
            };
        }
    } catch (error) {
        console.error('Chatbot error:', error);
        return {
            success: false,
            response: `Error: An error occurred while processing your request. ${error.message || 'Please try again later.'}`,
            error: error.message
        };
    }
}

/**
 * Rate a chatbot response
 * @param {string} messageId - The message ID to rate
 * @param {number} rating - Rating from 1 to 5
 * @param {string} feedback - Optional feedback text
 * @returns {Promise<Object>} Response object
 */
export async function rateChatbotResponse(messageId, rating, feedback = '') {
    return await apiRequest('/chatbot/rate', {
        method: 'POST',
        body: JSON.stringify({
            message_id: messageId,
            rating: rating,
            feedback: feedback
        })
    });
}

/**
 * Get AI-powered analytics insights (personalized)
 * @param {string} filter - Filter type: 'all', 'my', or 'favorites'
 * @returns {Promise<Object>} Analytics insights
 */
export async function getAnalyticsInsights(filter = 'all') {
    return await apiRequest(`/analytics/insights?filter=${filter}`, {
        method: 'GET'
    });
}

/**
 * Get user profile
 * @returns {Promise<Object>} User profile
 */
export async function getProfile() {
    return await apiRequest('/profile', {
        method: 'GET'
    });
}

/**
 * Update user profile
 * @param {Object} updates - Profile updates (username, email, password, current_password)
 * @returns {Promise<Object>} Update result
 */
export async function updateProfile(updates) {
    return await apiRequest('/profile', {
        method: 'PATCH',
        body: JSON.stringify(updates)
    });
}

/**
 * Get chatbot statistics
 * @returns {Promise<Object>} Chatbot stats
 */
export async function getChatbotStats() {
    return await apiRequest('/chatbot/stats', {
        method: 'GET'
    });
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

/**
 * User signup
 */
export async function signup(username, email, password) {
    return await apiRequest('/auth/signup', {
        method: 'POST',
        body: JSON.stringify({
            username,
            email,
            password
        })
    });
}

/**
 * User login
 */
export async function login(username, password) {
    return await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({
            username,
            password
        })
    });
}

/**
 * User logout
 */
export async function logout() {
    const token = getAuthToken();
    if (token) {
        await apiRequest('/auth/logout', {
            method: 'POST',
            body: JSON.stringify({ token })
        });
    }
    setAuthToken(null);
    setUserData(null);
}

/**
 * Verify authentication session
 */
export async function verifyAuth() {
    return await apiRequest('/auth/verify');
}

/**
 * Get user's own listings
 */
export async function getMyListings() {
    return await apiRequest('/my-listings');
}

/**
 * Send a message to the AI Listing Assistant
 * @param {string} query - The user's message
 * @param {string} apiKey - The Gemini API key
 * @param {Array} history - Conversation history array with {role: 'user'|'bot', text: string}
 * @returns {Promise<Object>} Response object with {success, response, action_type, listing_data, error}
 */
export async function handleListingAssistantQuery(query, apiKey, history = []) {
    if (!apiKey || apiKey.trim() === '' || apiKey === 'YOUR_GEMINI_API_KEY_HERE') {
        return {
            success: false,
            response: "Error: API key is missing. Please add your Gemini API key to enable the listing assistant.",
            error: "API key missing"
        };
    }

    try {
        console.log('Sending listing assistant query:', query);
        const response = await apiRequest('/listing-assistant', {
            method: 'POST',
            body: JSON.stringify({
                query: query,
                api_key: apiKey,
                history: history,
                session: USER_SESSION
            })
        });

        console.log('Listing assistant response:', response);

        if (response.success) {
            return {
                success: true,
                response: response.response || "I'm sorry, I couldn't generate a response.",
                action_type: response.action_type || null,
                listing_data: response.listing_data || null,
                message_id: response.message_id || null
            };
        } else {
            return {
                success: false,
                response: `Error: ${response.error || "I couldn't generate a response. Please try again."}`,
                error: response.error
            };
        }
    } catch (error) {
        console.error('Listing assistant error:', error);
        return {
            success: false,
            response: `Error: An error occurred while processing your request. ${error.message || 'Please try again later.'}`,
            error: error.message
        };
    }
}