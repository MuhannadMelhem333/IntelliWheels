/**
 * IntelliWheels Main Application
 * Modern, professional car catalog application
 */

import { 
    DOM, 
    showPage, 
    renderCarList, 
    populateFilters, 
    showCarInfoModal, 
    appendMessage, 
    appendListingAssistantMessage,
    resetListingAssistantChat,
    resetChatbotChat,
    createParticles, 
    showTypingIndicator, 
    hideTypingIndicator,
    showLoadingState,
    hideLoadingState,
    showError,
    showSuccess,
    refreshDOM
} from './ui.js';
import { 
    getCars, 
    getCar,
    createCar, 
    updateCar, 
    deleteCar, 
    getMakes, 
    getFavorites, 
    addFavorite, 
    removeFavorite,
    getMyListings,
    handleChatbotQuery,
    handleListingAssistantQuery,
    healthCheck,
    signup,
    login,
    logout,
    verifyAuth,
    getAuthToken,
    setAuthToken,
    getUserData,
    setUserData
} from './api.js';

// --- STATE MANAGEMENT ---
const GEMINI_API_KEY = "AIzaSyCwWNVISM0LuM7FNSnEDIbXWQE7-zH3unM"; // Replace with your API key
let allCars = [];
let favorites = [];
let currentFilters = {
    make: 'all',
    search: '',
    sort: 'default'
};
let isLoading = false;
let conversationHistory = []; // Store conversation history for chatbot
let listingAssistantHistory = []; // Store conversation history for listing assistant
let isAuthenticated = false; // Authentication state
let currentUser = null; // Current logged-in user
let abortController = null; // For canceling API requests

// Chat session management
let chatbotSessions = []; // Array of {id, title, history, createdAt, updatedAt}
let listingAssistantSessions = []; // Array of {id, title, history, createdAt, updatedAt}
let currentChatbotSessionId = null;
let currentListingAssistantSessionId = null;

// --- LOCALSTORAGE FUNCTIONS ---
const Storage = {
    getFavorites: () => JSON.parse(localStorage.getItem('carFavorites')) || [],
    saveFavorites: (favs) => localStorage.setItem('carFavorites', JSON.stringify(favs)),
    getChatbotSessions: () => JSON.parse(localStorage.getItem('chatbotSessions')) || [],
    saveChatbotSessions: (sessions) => localStorage.setItem('chatbotSessions', JSON.stringify(sessions)),
    getListingAssistantSessions: () => JSON.parse(localStorage.getItem('listingAssistantSessions')) || [],
    saveListingAssistantSessions: (sessions) => localStorage.setItem('listingAssistantSessions', JSON.stringify(sessions)),
};

// --- CHAT SESSION MANAGEMENT ---
function generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function createNewChatbotSession() {
    const sessionId = generateSessionId();
    const session = {
        id: sessionId,
        title: 'New Chat',
        history: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
    };
    chatbotSessions.unshift(session);
    Storage.saveChatbotSessions(chatbotSessions);
    currentChatbotSessionId = sessionId;
    conversationHistory = [];
    resetChatbotChat();
    renderChatbotChatList();
    return sessionId;
}

function createNewListingAssistantSession() {
    const sessionId = generateSessionId();
    const session = {
        id: sessionId,
        title: 'New Chat',
        history: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
    };
    listingAssistantSessions.unshift(session);
    Storage.saveListingAssistantSessions(listingAssistantSessions);
    currentListingAssistantSessionId = sessionId;
    listingAssistantHistory = [];
    resetListingAssistantChat();
    renderListingAssistantChatList();
    return sessionId;
}

function switchChatbotSession(sessionId) {
    const session = chatbotSessions.find(s => s.id === sessionId);
    if (!session) return;
    
    currentChatbotSessionId = sessionId;
    conversationHistory = session.history || [];
    
    // Render the conversation
    if (DOM.chatbotLog) {
        DOM.chatbotLog.innerHTML = '';
        conversationHistory.forEach(msg => {
            appendMessage(msg.text, msg.role === 'user' ? 'user' : 'bot');
        });
        if (conversationHistory.length === 0) {
            resetChatbotChat();
        }
    }
    
    renderChatbotChatList();
}

function switchListingAssistantSession(sessionId) {
    const session = listingAssistantSessions.find(s => s.id === sessionId);
    if (!session) return;
    
    currentListingAssistantSessionId = sessionId;
    listingAssistantHistory = session.history || [];
    
    // Render the conversation
    if (DOM.listingAssistantConversation) {
        DOM.listingAssistantConversation.innerHTML = '';
        if (listingAssistantHistory.length === 0) {
            // Show welcome card
            DOM.listingAssistantConversation.innerHTML = `
                <div class="listing-welcome-card">
                    <div class="listing-welcome-icon">🚗</div>
                    <h3 class="text-xl font-bold mb-2">Welcome to Listing Assistant</h3>
                    <p class="text-gray-400 mb-4">I can help you create and manage car listings through conversation.</p>
                    <div class="listing-features-grid">
                        <div class="listing-feature-card">
                            <div class="feature-icon">➕</div>
                            <h4 class="font-semibold">Create Listings</h4>
                            <p class="text-sm text-gray-400">Add new car listings by chatting</p>
                        </div>
                        <div class="listing-feature-card">
                            <div class="feature-icon">💰</div>
                            <h4 class="font-semibold">Price Suggestions</h4>
                            <p class="text-sm text-gray-400">Get market-based pricing advice</p>
                        </div>
                        <div class="listing-feature-card">
                            <div class="feature-icon">✏️</div>
                            <h4 class="font-semibold">Edit Listings</h4>
                            <p class="text-sm text-gray-400">Update existing listings easily</p>
                        </div>
                        <div class="listing-feature-card">
                            <div class="feature-icon">💬</div>
                            <h4 class="font-semibold">Ask Questions</h4>
                            <p class="text-sm text-gray-400">Get help with listing requirements</p>
                        </div>
                    </div>
                </div>
            `;
        } else {
            listingAssistantHistory.forEach(msg => {
                appendListingAssistantMessage(msg.text, msg.role === 'user' ? 'user' : 'bot');
            });
        }
    }
    
    renderListingAssistantChatList();
}

function deleteChatbotSession(sessionId) {
    chatbotSessions = chatbotSessions.filter(s => s.id !== sessionId);
    Storage.saveChatbotSessions(chatbotSessions);
    if (currentChatbotSessionId === sessionId) {
        if (chatbotSessions.length > 0) {
            switchChatbotSession(chatbotSessions[0].id);
        } else {
            createNewChatbotSession();
        }
    }
    renderChatbotChatList();
}

function deleteListingAssistantSession(sessionId) {
    listingAssistantSessions = listingAssistantSessions.filter(s => s.id !== sessionId);
    Storage.saveListingAssistantSessions(listingAssistantSessions);
    if (currentListingAssistantSessionId === sessionId) {
        if (listingAssistantSessions.length > 0) {
            switchListingAssistantSession(listingAssistantSessions[0].id);
        } else {
            createNewListingAssistantSession();
        }
    }
    renderListingAssistantChatList();
}

function updateChatbotSessionTitle(sessionId, title) {
    const session = chatbotSessions.find(s => s.id === sessionId);
    if (session) {
        session.title = title;
        session.updatedAt = new Date().toISOString();
        Storage.saveChatbotSessions(chatbotSessions);
        renderChatbotChatList();
    }
}

function updateListingAssistantSessionTitle(sessionId, title) {
    const session = listingAssistantSessions.find(s => s.id === sessionId);
    if (session) {
        session.title = title;
        session.updatedAt = new Date().toISOString();
        Storage.saveListingAssistantSessions(listingAssistantSessions);
        renderListingAssistantChatList();
    }
}

function saveChatbotSession() {
    if (!currentChatbotSessionId) return;
    const session = chatbotSessions.find(s => s.id === currentChatbotSessionId);
    if (session) {
        session.history = conversationHistory;
        session.updatedAt = new Date().toISOString();
        // Update title from first user message if title is still "New Chat"
        if (session.title === 'New Chat' && conversationHistory.length > 0) {
            const firstUserMsg = conversationHistory.find(m => m.role === 'user');
            if (firstUserMsg) {
                session.title = firstUserMsg.text.substring(0, 50) + (firstUserMsg.text.length > 50 ? '...' : '');
            }
        }
        Storage.saveChatbotSessions(chatbotSessions);
        renderChatbotChatList();
    }
}

function saveListingAssistantSession() {
    if (!currentListingAssistantSessionId) return;
    const session = listingAssistantSessions.find(s => s.id === currentListingAssistantSessionId);
    if (session) {
        session.history = listingAssistantHistory;
        session.updatedAt = new Date().toISOString();
        // Update title from first user message if title is still "New Chat"
        if (session.title === 'New Chat' && listingAssistantHistory.length > 0) {
            const firstUserMsg = listingAssistantHistory.find(m => m.role === 'user');
            if (firstUserMsg) {
                session.title = firstUserMsg.text.substring(0, 50) + (firstUserMsg.text.length > 50 ? '...' : '');
            }
        }
        Storage.saveListingAssistantSessions(listingAssistantSessions);
        renderListingAssistantChatList();
    }
}

function renderChatbotChatList() {
    if (!DOM.chatbotChatList) return;
    
    if (chatbotSessions.length === 0) {
        DOM.chatbotChatList.innerHTML = '<p class="text-gray-400 text-sm text-center p-4">No chats yet. Start a new chat!</p>';
        return;
    }
    
    DOM.chatbotChatList.innerHTML = chatbotSessions.map(session => {
        const isActive = session.id === currentChatbotSessionId;
        const preview = session.history.length > 0 
            ? (session.history[session.history.length - 1].text || '').substring(0, 40) + '...'
            : 'No messages yet';
        const date = new Date(session.updatedAt).toLocaleDateString();
        
        return `
            <div class="chat-item ${isActive ? 'active' : ''}" data-session-id="${session.id}">
                <div class="chat-item-title">${session.title}</div>
                <div class="chat-item-preview">${preview}</div>
                <div class="chat-item-date">${date}</div>
                <button class="chat-item-delete" data-session-id="${session.id}" title="Delete chat">×</button>
            </div>
        `;
    }).join('');
    
    // Add click handlers
    DOM.chatbotChatList.querySelectorAll('.chat-item').forEach(item => {
        const sessionId = item.dataset.sessionId;
        item.addEventListener('click', (e) => {
            if (!e.target.classList.contains('chat-item-delete')) {
                switchChatbotSession(sessionId);
            }
        });
    });
    
    // Add delete handlers
    DOM.chatbotChatList.querySelectorAll('.chat-item-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (confirm('Are you sure you want to delete this chat?')) {
                deleteChatbotSession(btn.dataset.sessionId);
            }
        });
    });
}

function renderListingAssistantChatList() {
    if (!DOM.listingAssistantChatList) return;
    
    if (listingAssistantSessions.length === 0) {
        DOM.listingAssistantChatList.innerHTML = '<p class="text-gray-400 text-sm text-center p-4">No chats yet. Start a new chat!</p>';
        return;
    }
    
    DOM.listingAssistantChatList.innerHTML = listingAssistantSessions.map(session => {
        const isActive = session.id === currentListingAssistantSessionId;
        const preview = session.history.length > 0 
            ? (session.history[session.history.length - 1].text || '').substring(0, 40) + '...'
            : 'No messages yet';
        const date = new Date(session.updatedAt).toLocaleDateString();
        
        return `
            <div class="chat-item ${isActive ? 'active' : ''}" data-session-id="${session.id}">
                <div class="chat-item-title">${session.title}</div>
                <div class="chat-item-preview">${preview}</div>
                <div class="chat-item-date">${date}</div>
                <button class="chat-item-delete" data-session-id="${session.id}" title="Delete chat">×</button>
            </div>
        `;
    }).join('');
    
    // Add click handlers
    DOM.listingAssistantChatList.querySelectorAll('.chat-item').forEach(item => {
        const sessionId = item.dataset.sessionId;
        item.addEventListener('click', (e) => {
            if (!e.target.classList.contains('chat-item-delete')) {
                switchListingAssistantSession(sessionId);
            }
        });
    });
    
    // Add delete handlers
    DOM.listingAssistantChatList.querySelectorAll('.chat-item-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (confirm('Are you sure you want to delete this chat?')) {
                deleteListingAssistantSession(btn.dataset.sessionId);
            }
        });
    });
}

// --- API DATA FETCHING ---
async function fetchCarData() {
    try {
        showLoadingState(DOM.listingsContainer);
        const response = await getCars(currentFilters);
        
        if (response.success) {
            allCars = response.cars || [];
            return allCars;
        } else {
            throw new Error(response.error || 'Failed to fetch cars');
        }
    } catch (error) {
        console.error("Could not fetch car data:", error);
        showError(DOM.listingsContainer, "Could not load car listings. Please check if the backend server is running.");
        return [];
    } finally {
        hideLoadingState();
    }
}

async function fetchFavorites() {
    try {
        const response = await getFavorites();
        if (response.success) {
            favorites = response.cars.map(car => car.id);
            // Save to localStorage as backup
            Storage.saveFavorites(favorites);
            console.log(`Fetched ${favorites.length} favorites from server`);
            return favorites;
        } else {
            console.warn('Failed to fetch favorites from server:', response.error);
            // Fallback to localStorage only if API fails
            favorites = Storage.getFavorites();
            return favorites;
        }
    } catch (error) {
        console.error("Could not fetch favorites:", error);
        // Fallback to localStorage
        favorites = Storage.getFavorites();
        return favorites;
    }
}

async function loadMakes() {
    try {
        const response = await getMakes();
        if (response.success) {
            populateFilters(response.makes || []);
        }
    } catch (error) {
        console.error("Could not fetch makes:", error);
    }
}

// --- FILTERING AND RENDERING ---
async function applyFiltersAndRender() {
    if (isLoading) return;
    
    // Cancel previous request if still pending
    if (abortController) {
        abortController.abort();
    }
    
    isLoading = true;
    abortController = new AbortController();
    
    try {
        if (DOM.listingsContainer) {
            showLoadingState(DOM.listingsContainer);
        }
        
        // Update filters
        const searchTerm = DOM.searchInput?.value?.trim() || '';
        const selectedMake = DOM.makeFilter?.value || 'all';
        const sortBy = DOM.sortFilter?.value || 'default';
        
        currentFilters = {
            make: selectedMake,
            search: searchTerm,
            sort: sortBy
        };
        
        // Import getCars with signal support
        const { getCars } = await import('./api.js');
        const response = await getCars(currentFilters, abortController.signal);
        
        // Check if request was cancelled
        if (response.error === 'Request cancelled') {
            return;
        }
        
        if (response.success) {
            allCars = response.cars || [];
            if (DOM.listingsContainer) {
                renderCarList(allCars, DOM.listingsContainer, favorites);
            }
        } else {
            console.error("Filter error:", response.error);
            // Use local data if available
            if (allCars.length > 0) {
                let filtered = [...allCars];
                
                if (searchTerm) {
                    filtered = filtered.filter(car => 
                        car.make?.toLowerCase().includes(searchTerm.toLowerCase()) || 
                        car.model?.toLowerCase().includes(searchTerm.toLowerCase())
                    );
                }
                
                if (selectedMake !== 'all') {
                    filtered = filtered.filter(car => car.make === selectedMake);
                }
                
                if (sortBy === 'price-asc') {
                    filtered.sort((a, b) => (a.price || 0) - (b.price || 0));
                } else if (sortBy === 'price-desc') {
                    filtered.sort((a, b) => (b.price || 0) - (a.price || 0));
                } else if (sortBy === 'rating-desc') {
                    filtered.sort((a, b) => (b.rating || 0) - (a.rating || 0));
                }
                
                if (DOM.listingsContainer) {
                    renderCarList(filtered, DOM.listingsContainer, favorites);
                }
            } else {
                if (DOM.listingsContainer) {
                    showError(DOM.listingsContainer, response.error || "Could not filter cars. Please try again.");
                }
            }
        }
    } catch (error) {
        if (error.name !== 'AbortError') {
            console.error("Filter error:", error);
            if (DOM.listingsContainer) {
                showError(DOM.listingsContainer, "Could not filter cars. Please try again.");
            }
        }
    } finally {
        hideLoadingState();
        isLoading = false;
    }
}

// --- FAVORITES MANAGEMENT ---
async function toggleFavorite(carId) {
    try {
        const carCardIcon = document.querySelector(`.favorite-btn[data-car-id="${carId}"]`);
        const isFavorited = favorites.includes(carId);
        
        let response;
        if (isFavorited) {
            // Remove from favorites
            response = await removeFavorite(carId);
            
            if (response.success) {
                favorites = favorites.filter(id => id !== carId);
                if (carCardIcon) carCardIcon.classList.remove('favorited');
                showSuccess('Removed from favorites');
            } else {
                throw new Error(response.error || 'Failed to remove favorite');
            }
        } else {
            // Add to favorites
            response = await addFavorite(carId);
            
            if (response.success) {
                favorites.push(carId);
                if (carCardIcon) carCardIcon.classList.add('favorited');
                showSuccess('Added to favorites');
            } else {
                throw new Error(response.error || 'Failed to add favorite');
            }
        }
        
        // Only update localStorage if API call succeeded
        Storage.saveFavorites(favorites);
        
        // Refresh favorites page if currently viewing it
        if (DOM.pages.favorites && !DOM.pages.favorites.classList.contains('hidden')) {
            await renderFavoritesPage();
        }
        
        // Update favorite buttons without full re-render for better performance
        if (DOM.pages.listings && !DOM.pages.listings.classList.contains('hidden')) {
            document.querySelectorAll('.favorite-btn').forEach(btn => {
                const btnCarId = parseInt(btn.dataset.carId);
                if (favorites.includes(btnCarId)) {
                    btn.classList.add('favorited');
                } else {
                    btn.classList.remove('favorited');
                }
            });
        }
    } catch (error) {
        console.error("Favorite toggle error:", error);
        showError(null, `Could not update favorites: ${error.message || 'Please try again.'}`);
        
        // Re-fetch favorites from server to sync state
        try {
            favorites = await fetchFavorites();
            // Re-render to show correct state
            if (DOM.pages.listings && !DOM.pages.listings.classList.contains('hidden')) {
                applyFiltersAndRender();
            }
        } catch (syncError) {
            console.error("Failed to sync favorites:", syncError);
        }
    }
}

async function renderFavoritesPage() {
    try {
        showLoadingState(DOM.favoritesContainer);
        const response = await getFavorites();
        
        if (response.success) {
            const favoriteCars = response.cars || [];
            renderCarList(favoriteCars, DOM.favoritesContainer, favorites);
        } else {
            // Fallback: filter from allCars
            const favoriteCars = allCars.filter(car => favorites.includes(car.id));
            renderCarList(favoriteCars, DOM.favoritesContainer, favorites);
        }
    } catch (error) {
        console.error("Could not fetch favorites:", error);
        const favoriteCars = allCars.filter(car => favorites.includes(car.id));
        renderCarList(favoriteCars, DOM.favoritesContainer, favorites);
    } finally {
        hideLoadingState();
    }
}

// --- CAR LISTING MANAGEMENT ---
async function handleAddListing(event) {
    event.preventDefault();
    
    if (isLoading) return;
    isLoading = true;
    
    try {
        const formData = new FormData(DOM.addListingForm);
        const newCar = {
            make: formData.get('make'),
            model: formData.get('model'),
            year: parseInt(formData.get('year')),
            price: parseFloat(formData.get('price')),
            currency: formData.get('currency'),
            image: formData.get('image'),
            imageUrls: [formData.get('image')],
            rating: parseFloat(formData.get('rating')),
            reviews: 0,
            specs: {
                bodyStyle: formData.get('bodyStyle') || 'Unknown',
                horsepower: parseInt(formData.get('horsepower')) || 0,
                engine: formData.get('engine') || 'N/A',
                fuelEconomy: formData.get('fuelEconomy') || 'N/A'
            }
        };

        const response = await createCar(newCar);
        
        if (response.success) {
            showSuccess('Car listing added successfully!');
            DOM.addListingForm.reset();
            
            // Refresh car list
            await fetchCarData();
            await loadMakes();
            applyFiltersAndRender();
            
            // Refresh my listings if it exists
            if (DOM.myListingsContainer) {
                await renderMyListingsPage();
            }
            
            showPage('listings');
        } else {
            throw new Error(response.error || 'Failed to add car');
        }
    } catch (error) {
        console.error("Add listing error:", error);
        showError(null, `Could not add car listing: ${error.message}`);
    } finally {
        isLoading = false;
    }
}

async function handleEditCar(carId, updates) {
    try {
        const response = await updateCar(carId, updates);
        if (response.success) {
            showSuccess('Car updated successfully!');
            await fetchCarData();
            applyFiltersAndRender();
            return true;
        } else {
            throw new Error(response.error || 'Failed to update car');
        }
    } catch (error) {
        console.error("Update error:", error);
        showError(null, `Could not update car: ${error.message}`);
        return false;
    }
}

async function handleDeleteCar(carId) {
    if (!confirm('Are you sure you want to delete this car listing? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await deleteCar(carId);
        if (response.success) {
            showSuccess('Car listing deleted successfully!');
            
            // Refresh my listings page if currently viewing
            if (DOM.pages.myListings && !DOM.pages.myListings.classList.contains('hidden')) {
                await renderMyListingsPage();
            }
            
            // Also refresh main listings
            await fetchCarData();
            applyFiltersAndRender();
        } else {
            throw new Error(response.error || 'Failed to delete car');
        }
    } catch (error) {
        console.error("Delete error:", error);
        showError(null, `Could not delete car: ${error.message}`);
    }
}

// --- AUTHENTICATION MANAGEMENT ---
async function checkAuthentication() {
    const token = getAuthToken();
    if (!token) {
        return false;
    }
    
    try {
        const response = await verifyAuth();
        if (response.success && response.authenticated) {
            isAuthenticated = true;
            currentUser = response.user;
            setUserData(response.user);
            updateAuthUI();
            return true;
        } else {
            setAuthToken(null);
            setUserData(null);
            isAuthenticated = false;
            currentUser = null;
            updateAuthUI();
            return false;
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        setAuthToken(null);
        setUserData(null);
        isAuthenticated = false;
        currentUser = null;
        updateAuthUI();
        return false;
    }
}

function updateAuthUI() {
    if (isAuthenticated && currentUser) {
        // Show main navigation, hide auth section
        if (DOM.navMainSection) DOM.navMainSection.classList.remove('hidden');
        if (DOM.navAuthSection) {
            DOM.navAuthSection.classList.remove('hidden');
            if (DOM.userNameDisplay) {
                DOM.userNameDisplay.textContent = `Welcome, ${currentUser.username}`;
                DOM.userNameDisplay.classList.remove('hidden');
            }
            if (DOM.navLogout) DOM.navLogout.classList.remove('hidden');
        }
    } else {
        // Hide main navigation, show auth section
        if (DOM.navMainSection) DOM.navMainSection.classList.add('hidden');
        if (DOM.navAuthSection) {
            if (DOM.userNameDisplay) DOM.userNameDisplay.classList.add('hidden');
            if (DOM.navLogout) DOM.navLogout.classList.add('hidden');
        }
    }
}

async function handleLogin(event) {
    console.log('handleLogin called!', event);
    event.preventDefault();
    event.stopPropagation();
    
    if (isLoading) {
        console.log('Already loading, ignoring...');
        return;
    }
    
    const username = DOM.loginForm.querySelector('#login-username').value.trim();
    const password = DOM.loginForm.querySelector('#login-password').value;
    
    console.log('Login attempt:', { username, passwordLength: password.length });
    
    if (!username || !password) {
        console.log('Validation failed: missing fields');
        showAuthError('login-error', 'Please fill in all fields');
        return;
    }
    
    isLoading = true;
    hideAuthError('login-error');
    
    // Show loading state
    const submitBtn = DOM.loginForm.querySelector('button[type="submit"]');
    const originalText = submitBtn?.textContent;
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Logging in...';
    }
    
    try {
        console.log('Attempting login for:', username);
        const response = await login(username, password);
        console.log('Login response:', response);
        
        if (response.success) {
            setAuthToken(response.token);
            setUserData(response.user);
            isAuthenticated = true;
            currentUser = response.user;
            
            // Clear old localStorage favorites (they might be from a different user)
            localStorage.removeItem('carFavorites');
            favorites = [];
            
            updateAuthUI();
            showSuccess('Login successful!');
            showPage('listings');
            
            // Initialize app and load favorites from server
            await initApp();
        } else {
            const errorMsg = response.error || 'Login failed';
            console.error('Login failed:', errorMsg);
            showAuthError('login-error', errorMsg);
        }
    } catch (error) {
        console.error('Login error:', error);
        const errorMsg = error.message || 'Login failed. Please check if the backend server is running.';
        showAuthError('login-error', errorMsg);
        
        // Check if it's a network error
        if (error.message && error.message.includes('fetch')) {
            showAuthError('login-error', 'Cannot connect to server. Make sure Flask backend is running (python app.py)');
        }
    } finally {
        isLoading = false;
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText || 'Login';
        }
    }
}

async function handleSignup(event) {
    event.preventDefault();
    if (isLoading) return;
    
    const username = DOM.signupForm.querySelector('#signup-username').value.trim();
    const email = DOM.signupForm.querySelector('#signup-email').value.trim();
    const password = DOM.signupForm.querySelector('#signup-password').value;
    const passwordConfirm = DOM.signupForm.querySelector('#signup-password-confirm').value;
    
    if (!username || !email || !password || !passwordConfirm) {
        showAuthError('signup-error', 'Please fill in all fields');
        return;
    }
    
    if (password !== passwordConfirm) {
        showAuthError('signup-error', 'Passwords do not match');
        return;
    }
    
    if (password.length < 6) {
        showAuthError('signup-error', 'Password must be at least 6 characters');
        return;
    }
    
    isLoading = true;
    hideAuthError('signup-error');
    
    // Show loading state
    const submitBtn = DOM.signupForm.querySelector('button[type="submit"]');
    const originalText = submitBtn?.textContent;
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating account...';
    }
    
    try {
        console.log('Attempting signup for:', username, email);
        const response = await signup(username, email, password);
        console.log('Signup response:', response);
        
        if (response.success) {
            setAuthToken(response.token);
            setUserData(response.user);
            isAuthenticated = true;
            currentUser = response.user;
            
            // Clear old localStorage favorites (they might be from a different user)
            localStorage.removeItem('carFavorites');
            favorites = [];
            
            updateAuthUI();
            showSuccess('Account created successfully!');
            showPage('listings');
            
            // Initialize app and load favorites from server
            await initApp();
        } else {
            const errorMsg = response.error || 'Signup failed';
            console.error('Signup failed:', errorMsg);
            showAuthError('signup-error', errorMsg);
        }
    } catch (error) {
        console.error('Signup error:', error);
        const errorMsg = error.message || 'Signup failed. Please check if the backend server is running.';
        showAuthError('signup-error', errorMsg);
        
        // Check if it's a network error
        if (error.message && error.message.includes('fetch')) {
            showAuthError('signup-error', 'Cannot connect to server. Make sure Flask backend is running (python app.py)');
        }
    } finally {
        isLoading = false;
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText || 'Sign Up';
        }
    }
}

async function handleLogout() {
    try {
        await logout();
        isAuthenticated = false;
        currentUser = null;
        
        // Clear favorites from localStorage and memory
        localStorage.removeItem('carFavorites');
        favorites = [];
        conversationHistory = [];
        
        updateAuthUI();
        showPage('login');
        showSuccess('Logged out successfully');
    } catch (error) {
        console.error('Logout error:', error);
    }
}

function showAuthError(elementId, message) {
    const errorEl = document.getElementById(elementId);
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.classList.remove('hidden');
        errorEl.classList.add('show');
    }
}

function hideAuthError(elementId) {
    const errorEl = document.getElementById(elementId);
    if (errorEl) {
        errorEl.classList.add('hidden');
        errorEl.classList.remove('show');
    }
}

function requireAuth() {
    if (!isAuthenticated) {
        showPage('login');
        return false;
    }
    return true;
}

// --- LISTING ASSISTANT HANDLING ---
async function handleListingAssistantSubmit(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    if (!requireAuth()) return;
    
    const message = DOM.listingAssistantInput?.value?.trim();
    if (!message || isLoading || !DOM.listingAssistantInput) return;

    if (DOM.pages.listingAssistant.classList.contains('hidden')) {
        showPage('listingAssistant');
    }

    await appendListingAssistantMessage(message, 'user');
    
    listingAssistantHistory.push({ role: 'user', text: message });
    
    // Create session if doesn't exist
    if (!currentListingAssistantSessionId) {
        createNewListingAssistantSession();
    }
    
    DOM.listingAssistantInput.value = '';
    showTypingIndicator(DOM.listingAssistantConversation);
    isLoading = true;

    try {
        const response = await handleListingAssistantQuery(message, GEMINI_API_KEY, listingAssistantHistory);
        hideTypingIndicator(DOM.listingAssistantConversation);
        
        if (!response.success) {
            let errorMessage = response.error || response.response || "I'm sorry, I couldn't generate a response.";
            appendListingAssistantMessage(errorMessage, 'bot');
            showError(null, errorMessage);
        } else {
            appendListingAssistantMessage(
                response.response, 
                'bot', 
                response.listing_data, 
                response.action_type
            );
            
            listingAssistantHistory.push({ role: 'bot', text: response.response });
            
            if (listingAssistantHistory.length > 20) {
                listingAssistantHistory = listingAssistantHistory.slice(-20);
            }
            
            // Save session
            saveListingAssistantSession();
        }
    } catch (error) {
        hideTypingIndicator(DOM.listingAssistantConversation);
        const errorMsg = `I'm sorry, I encountered an error: ${error.message || 'Unknown error'}. Please try again later.`;
        appendListingAssistantMessage(errorMsg, 'bot');
        console.error("Listing assistant error:", error);
        showError(null, errorMsg);
    } finally {
        isLoading = false;
    }
}

// Handle creating listing from assistant
window.handleCreateListingFromAssistant = async function(listingData) {
    if (isLoading) return;
    isLoading = true;
    
    try {
        // Normalize the data structure
        const carData = {
            make: listingData.make,
            model: listingData.model,
            year: listingData.year ? parseInt(listingData.year) : null,
            price: listingData.price ? parseFloat(listingData.price) : null,
            currency: listingData.currency || 'AED',
            image: listingData.image || listingData.image_url || '',
            imageUrls: listingData.imageUrls || (listingData.image ? [listingData.image] : []),
            rating: listingData.rating ? parseFloat(listingData.rating) : 0.0,
            reviews: 0,
            specs: {
                bodyStyle: listingData.bodyStyle || listingData.specs?.bodyStyle || 'Unknown',
                horsepower: listingData.horsepower || listingData.specs?.horsepower || 0,
                engine: listingData.engine || listingData.specs?.engine || 'N/A',
                fuelEconomy: listingData.fuelEconomy || listingData.specs?.fuelEconomy || 'N/A'
            }
        };

        const response = await createCar(carData);
        
        if (response.success) {
            showSuccess('Car listing created successfully!');
            appendListingAssistantMessage(
                `✅ Great! I've successfully created your listing for ${carData.make} ${carData.model}. You can view it in the Listings page.`,
                'bot'
            );
            
            // Refresh car list
            await fetchCarData();
            await loadMakes();
            applyFiltersAndRender();
            
            // Refresh my listings if it exists
            if (DOM.myListingsContainer) {
                await renderMyListingsPage();
            }
        } else {
            throw new Error(response.error || 'Failed to create listing');
        }
    } catch (error) {
        console.error("Create listing from assistant error:", error);
        appendListingAssistantMessage(
            `❌ Sorry, I couldn't create the listing: ${error.message}. Please try again or use the manual form.`,
            'bot'
        );
        showError(null, `Could not create listing: ${error.message}`);
    } finally {
        isLoading = false;
    }
};

// --- CHATBOT HANDLING ---
async function handleChatSubmit(event) {
    // Prevent any default form submission behavior
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    if (!requireAuth()) return;
    
    const message = DOM.chatbotInput?.value?.trim();
    if (!message || isLoading || !DOM.chatbotInput) return;

    // Ensure we're on the chatbot page
    if (DOM.pages.chatbot.classList.contains('hidden')) {
        showPage('chatbot');
    }

    await appendMessage(message, 'user');
    
    // Add user message to conversation history
    conversationHistory.push({ role: 'user', text: message });
    
    // Create session if doesn't exist
    if (!currentChatbotSessionId) {
        createNewChatbotSession();
    }
    
    DOM.chatbotInput.value = '';
    showTypingIndicator();
    isLoading = true;

    try {
        console.log('Submitting chat message with API key:', GEMINI_API_KEY ? 'Present' : 'Missing');
        const response = await handleChatbotQuery(message, GEMINI_API_KEY, conversationHistory);
        hideTypingIndicator();
        
        if (!response.success) {
            // Handle error responses
            let errorMessage = response.error || response.response || "I'm sorry, I couldn't generate a response.";
            
            // Check for quota exceeded error
            if (errorMessage.includes('quota') || errorMessage.includes('quota exceeded')) {
                errorMessage = "⚠️ API Quota Exceeded\n\nThe Gemini API quota has been exceeded. Please:\n\n• Wait a few minutes and try again\n• Check your API key usage limits\n• Consider upgrading your API plan if needed\n\nYou can still browse the car listings and use other features.";
            } else if (errorMessage.includes('API key') || errorMessage.includes('authentication')) {
                errorMessage = "⚠️ API Key Error\n\nThere's an issue with the API key. Please check your Gemini API key configuration.";
            } else if (errorMessage.includes('safety') || errorMessage.includes('blocked')) {
                errorMessage = "⚠️ Content Blocked\n\nYour query was blocked by safety filters. Please try rephrasing your question.";
            }
            
            appendMessage(errorMessage, 'bot');
            showError(null, errorMessage);
        } else if (response.response && response.response.startsWith('Error:')) {
            appendMessage(response.response, 'bot');
            showError(null, response.response);
        } else {
            // Display bot response with message ID for rating
            const messageId = response.message_id || null;
            appendMessage(response.response, 'bot', response.relevant_car_ids || [], messageId);
            
            // Add bot response to conversation history
            conversationHistory.push({ role: 'bot', text: response.response });
            
            // Limit conversation history to prevent memory issues
            if (conversationHistory.length > 20) {
                conversationHistory = conversationHistory.slice(-20);
            }
            
            // Save session
            saveChatbotSession();
            
            // Log intent for debugging
            if (response.intent) {
                console.log('Detected intent:', response.intent);
            }
        }
    } catch (error) {
        hideTypingIndicator();
        const errorMsg = `I'm sorry, I encountered an error: ${error.message || 'Unknown error'}. Please try again later.`;
        appendMessage(errorMsg, 'bot');
        console.error("Chatbot error:", error);
        showError(null, errorMsg);
    } finally {
        isLoading = false;
    }
}

// --- ANALYTICS PAGE ---
async function renderAnalyticsPage() {
    const container = document.getElementById('analytics-container');
    if (!container) return;
    
    try {
        container.innerHTML = `
            <div class="loading-container">
                <div class="spinner"></div>
                <p class="text-gray-400 mt-4">Analyzing data...</p>
            </div>
        `;
        
        const { getAnalyticsInsights } = await import('./api.js');
        const response = await getAnalyticsInsights();
        
        if (!response.success) {
            throw new Error(response.error || 'Failed to load analytics');
        }
        
        const insights = response.insights;
        
        container.innerHTML = `
            <div class="space-y-6">
                <!-- Summary Cards -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div class="analytics-card">
                        <h3 class="text-sm text-gray-400 mb-1">Total Cars</h3>
                        <p class="text-3xl font-bold text-white">${insights.summary.total_cars}</p>
                    </div>
                    <div class="analytics-card">
                        <h3 class="text-sm text-gray-400 mb-1">Total Makes</h3>
                        <p class="text-3xl font-bold text-white">${insights.summary.total_makes}</p>
                    </div>
                    <div class="analytics-card">
                        <h3 class="text-sm text-gray-400 mb-1">Avg Price</h3>
                        <p class="text-3xl font-bold text-white">${new Intl.NumberFormat().format(insights.summary.average_price)}</p>
                    </div>
                    <div class="analytics-card">
                        <h3 class="text-sm text-gray-400 mb-1">Avg Rating</h3>
                        <p class="text-3xl font-bold text-white">${insights.summary.average_rating.toFixed(1)} ⭐</p>
                    </div>
                </div>
                
                <!-- AI Insights -->
                <div class="analytics-card">
                    <h2 class="text-2xl font-bold text-white mb-4">🤖 AI-Powered Insights</h2>
                    <div class="prose prose-invert max-w-none">
                        <div class="text-gray-300 whitespace-pre-line">${insights.ai_insights || 'AI insights unavailable'}</div>
                    </div>
                </div>
                
                <!-- Top Makes -->
                <div class="analytics-card">
                    <h2 class="text-2xl font-bold text-white mb-4">Top Makes</h2>
                    <div class="space-y-2">
                        ${insights.top_makes.map((item, index) => `
                            <div class="flex items-center justify-between p-3 bg-gray-800 bg-opacity-50 rounded-lg">
                                <span class="text-white font-semibold">${index + 1}. ${item.make}</span>
                                <span class="text-blue-400 font-bold">${item.count} cars</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <!-- Price Distribution -->
                <div class="analytics-card">
                    <h2 class="text-2xl font-bold text-white mb-4">Price Distribution</h2>
                    <div class="space-y-2">
                        ${Object.entries(insights.price_distribution).map(([range, count]) => `
                            <div class="flex items-center justify-between p-3 bg-gray-800 bg-opacity-50 rounded-lg">
                                <span class="text-white">${range}</span>
                                <span class="text-blue-400 font-bold">${count} cars</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <!-- Top Rated Cars -->
                <div class="analytics-card">
                    <h2 class="text-2xl font-bold text-white mb-4">Top Rated Cars</h2>
                    <div class="space-y-2">
                        ${insights.top_rated_cars.map((car, index) => `
                            <div class="flex items-center justify-between p-3 bg-gray-800 bg-opacity-50 rounded-lg hover:bg-opacity-70 cursor-pointer" data-car-id="${car.id}">
                                <div>
                                    <span class="text-white font-semibold">${index + 1}. ${car.make} ${car.model}</span>
                                    <span class="text-yellow-400 ml-2">⭐ ${car.rating.toFixed(1)}</span>
                                </div>
                                <span class="text-blue-400 font-bold">${new Intl.NumberFormat().format(car.price)}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
        // Add click handlers for top rated cars
        container.querySelectorAll('[data-car-id]').forEach(el => {
            el.addEventListener('click', async () => {
                const carId = parseInt(el.dataset.carId);
                const { getCar } = await import('./api.js');
                try {
                    const carResponse = await getCar(carId);
                    if (carResponse.success && carResponse.car) {
                        showCarInfoModal(carResponse.car);
                    }
                } catch (error) {
                    console.error('Error loading car:', error);
                }
            });
        });
    } catch (error) {
        console.error('Error rendering analytics:', error);
        const container = document.getElementById('analytics-container');
        if (container) {
            container.innerHTML = `
                <div class="error-container">
                    <div class="error-icon">⚠️</div>
                    <h3 class="text-xl font-bold text-white mb-2">Failed to Load Analytics</h3>
                    <p class="text-gray-400">${error.message || 'An error occurred'}</p>
                </div>
            `;
        }
    }
}

// --- REVIEWS PAGE ---
async function renderReviewsPage() {
    try {
        showLoadingState(DOM.reviewsContainer);
        const response = await getCars({ sort: 'rating-desc', limit: 50 });
        
        if (response.success) {
            const topRatedCars = response.cars || [];
            renderCarList(topRatedCars, DOM.reviewsContainer, favorites);
        } else {
            throw new Error(response.error || 'Failed to fetch reviews');
        }
    } catch (error) {
        console.error("Could not fetch reviews:", error);
        showError(DOM.reviewsContainer, "Could not load top rated vehicles.");
    } finally {
        hideLoadingState();
    }
}

// --- MY LISTINGS PAGE ---
async function renderMyListingsPage() {
    try {
        showLoadingState(DOM.myListingsContainer);
        const response = await getMyListings();
        
        if (response.success) {
            const myCars = response.cars || [];
            if (myCars.length === 0) {
                DOM.myListingsContainer.innerHTML = `
                    <div class="text-center py-12">
                        <div class="text-6xl mb-4">🚗</div>
                        <h3 class="text-xl font-bold text-white mb-2">No Listings Yet</h3>
                        <p class="text-gray-400 mb-6">You haven't created any listings yet. Start by adding your first car!</p>
                        <button id="go-to-add-listing" class="bg-blue-600 text-white py-2 px-6 rounded-lg hover:bg-blue-700 transition-colors">
                            Add Your First Listing
                        </button>
                    </div>
                `;
                const btn = document.getElementById('go-to-add-listing');
                if (btn) {
                    btn.addEventListener('click', () => showPage('addListing'));
                }
            } else {
                renderCarList(myCars, DOM.myListingsContainer, [], true); // true = show edit/delete buttons
            }
        } else {
            throw new Error(response.error || 'Failed to fetch my listings');
        }
    } catch (error) {
        console.error("Could not fetch my listings:", error);
        showError(DOM.myListingsContainer, "Could not load your listings.");
    } finally {
        hideLoadingState();
    }
}

// --- EDIT LISTING ---
function showEditListingModal(car) {
    if (!DOM.editListingModal || !DOM.editListingForm) return;
    
    // Populate form with car data
    document.getElementById('edit-car-id').value = car.id;
    document.getElementById('edit-make').value = car.make || '';
    document.getElementById('edit-model').value = car.model || '';
    document.getElementById('edit-year').value = car.year || '';
    document.getElementById('edit-price').value = car.price || '';
    document.getElementById('edit-currency').value = car.currency || 'AED';
    document.getElementById('edit-rating').value = car.rating || 0;
    document.getElementById('edit-image').value = car.image || '';
    
    const specs = car.specs || {};
    document.getElementById('edit-bodyStyle').value = specs.bodyStyle || '';
    document.getElementById('edit-horsepower').value = specs.horsepower || '';
    document.getElementById('edit-engine').value = specs.engine || '';
    document.getElementById('edit-fuelEconomy').value = specs.fuelEconomy || '';
    
    DOM.editListingModal.classList.remove('hidden');
}

function hideEditListingModal() {
    if (DOM.editListingModal) {
        DOM.editListingModal.classList.add('hidden');
        if (DOM.editListingForm) {
            DOM.editListingForm.reset();
        }
    }
}

async function handleEditListing(event) {
    event.preventDefault();
    
    if (isLoading) return;
    isLoading = true;
    
    try {
        const carId = parseInt(document.getElementById('edit-car-id').value);
        const imageUrl = document.getElementById('edit-image').value;
        const updates = {
            make: document.getElementById('edit-make').value,
            model: document.getElementById('edit-model').value,
            year: document.getElementById('edit-year').value ? parseInt(document.getElementById('edit-year').value) : null,
            price: document.getElementById('edit-price').value ? parseFloat(document.getElementById('edit-price').value) : null,
            currency: document.getElementById('edit-currency').value || 'AED',
            image_url: imageUrl,
            image: imageUrl, // Also include 'image' field for compatibility
            rating: document.getElementById('edit-rating').value ? parseFloat(document.getElementById('edit-rating').value) : null,
            specs: {
                bodyStyle: document.getElementById('edit-bodyStyle').value || 'Unknown',
                horsepower: document.getElementById('edit-horsepower').value ? parseInt(document.getElementById('edit-horsepower').value) : 0,
                engine: document.getElementById('edit-engine').value || 'N/A',
                fuelEconomy: document.getElementById('edit-fuelEconomy').value || 'N/A'
            }
        };
        
        const response = await updateCar(carId, updates);
        
        if (response.success) {
            showSuccess('Listing updated successfully!');
            hideEditListingModal();
            
            // Refresh my listings page
            await renderMyListingsPage();
            
            // Also refresh main listings if currently viewing
            if (DOM.pages.listings && !DOM.pages.listings.classList.contains('hidden')) {
                await fetchCarData();
                applyFiltersAndRender();
            }
        } else {
            throw new Error(response.error || 'Failed to update listing');
        }
    } catch (error) {
        console.error("Edit listing error:", error);
        showError(null, `Could not update listing: ${error.message}`);
    } finally {
        isLoading = false;
    }
}

// --- EVENT LISTENERS ---
function setupEventListeners() {
    console.log('Setting up event listeners...');
    console.log('DOM.loginForm:', DOM.loginForm);
    console.log('DOM.signupForm:', DOM.signupForm);
    
    // Authentication
    if (DOM.loginForm) {
        console.log('Adding login form listener');
        DOM.loginForm.addEventListener('submit', handleLogin);
    } else {
        console.error('DOM.loginForm is null! Form not found.');
    }
    
    if (DOM.signupForm) {
        console.log('Adding signup form listener');
        DOM.signupForm.addEventListener('submit', handleSignup);
    } else {
        console.error('DOM.signupForm is null! Form not found.');
    }
    
    if (DOM.switchToSignup) {
        DOM.switchToSignup.addEventListener('click', () => showPage('signup'));
    }
    if (DOM.switchToLogin) {
        DOM.switchToLogin.addEventListener('click', () => showPage('login'));
    }
    if (DOM.navLogout) {
        DOM.navLogout.addEventListener('click', handleLogout);
    }
    
    // Logo Button
    if (DOM.logoBtn) {
        DOM.logoBtn.addEventListener('click', () => {
            if (isAuthenticated) {
                applyFiltersAndRender();
                showPage('listings');
            } else {
                showPage('login');
            }
        });
    }

    // Navigation (only if authenticated)
    if (DOM.navButtons.listings) {
        DOM.navButtons.listings.addEventListener('click', async () => {
            if (!requireAuth()) return;
            showPage('listings');
            await applyFiltersAndRender();
        });
    }
    
    if (DOM.navButtons.reviews) {
        DOM.navButtons.reviews.addEventListener('click', async () => {
            if (!requireAuth()) return;
            showPage('reviews');
            await renderReviewsPage();
        });
    }
    
    if (DOM.navButtons.favorites) {
        DOM.navButtons.favorites.addEventListener('click', async () => {
            if (!requireAuth()) return;
            showPage('favorites');
            await renderFavoritesPage();
        });
    }
    
    if (DOM.navButtons.myListings) {
        DOM.navButtons.myListings.addEventListener('click', async () => {
            if (!requireAuth()) return;
            showPage('myListings');
            await renderMyListingsPage();
        });
    }
    
    if (DOM.navButtons.chatbot) {
        DOM.navButtons.chatbot.addEventListener('click', () => {
            if (!requireAuth()) return;
            showPage('chatbot');
            renderChatbotChatList();
        });
    }
    
    if (DOM.navButtons.listingAssistant) {
        DOM.navButtons.listingAssistant.addEventListener('click', () => {
            if (!requireAuth()) return;
            showPage('listingAssistant');
            renderListingAssistantChatList();
        });
    }
    
    if (DOM.navButtons.analytics) {
        DOM.navButtons.analytics.addEventListener('click', async () => {
            if (!requireAuth()) return;
            showPage('analytics');
            await renderAnalyticsPage();
        });
    }
    
    if (DOM.navButtons.addListing) {
        DOM.navButtons.addListing.addEventListener('click', () => {
            if (!requireAuth()) return;
            showPage('addListing');
        });
    }

    // Form Submission
    if (DOM.addListingForm) {
        DOM.addListingForm.addEventListener('submit', (e) => {
            if (!requireAuth()) {
                e.preventDefault();
                return;
            }
            handleAddListing(e);
        });
    }

    // Event Delegation for Favorite, Details, Edit, Delete Buttons
    document.body.addEventListener('click', async (event) => {
        // Favorite button
        const favoriteBtn = event.target.closest('.favorite-btn');
        if (favoriteBtn && favoriteBtn.dataset.carId) {
            event.preventDefault();
            event.stopPropagation();
            await toggleFavorite(parseInt(favoriteBtn.dataset.carId));
            return;
        }
        
        // Details button
        const detailsBtn = event.target.closest('.details-button');
        if (detailsBtn && detailsBtn.dataset.carId) {
            event.preventDefault();
            event.stopPropagation();
            const carId = parseInt(detailsBtn.dataset.carId);
            try {
                const response = await getCar(carId);
                if (response.success && response.car) {
                    showCarInfoModal(response.car);
                } else {
                    // Fallback to local data
                    const car = allCars.find(c => c.id === carId);
                    if (car) {
                        showCarInfoModal(car);
                    } else {
                        showError(null, 'Car not found');
                    }
                }
            } catch (error) {
                console.error('Error fetching car:', error);
                // Fallback to local data
                const car = allCars.find(c => c.id === carId);
                if (car) {
                    showCarInfoModal(car);
                } else {
                    showError(null, 'Could not load car details');
                }
            }
            return;
        }
        
        // Edit button
        const editBtn = event.target.closest('.edit-button');
        if (editBtn && editBtn.dataset.carId) {
            event.preventDefault();
            event.stopPropagation();
            const carId = parseInt(editBtn.dataset.carId);
            try {
                const response = await getCar(carId);
                if (response.success && response.car) {
                    showEditListingModal(response.car);
                } else {
                    showError(null, 'Could not load car details for editing');
                }
            } catch (error) {
                console.error('Error loading car for editing:', error);
                showError(null, 'Could not load car details for editing');
            }
            return;
        }
        
        // Delete button
        const deleteBtn = event.target.closest('.delete-button');
        if (deleteBtn && deleteBtn.dataset.carId) {
            event.preventDefault();
            event.stopPropagation();
            const carId = parseInt(deleteBtn.dataset.carId);
            await handleDeleteCar(carId);
            return;
        }
    });

    // Filters - optimized debouncing
    if (DOM.searchInput) {
        DOM.searchInput.addEventListener('input', debounce(applyFiltersAndRender, 400));
    }
    if (DOM.makeFilter) {
        DOM.makeFilter.addEventListener('change', debounce(applyFiltersAndRender, 200));
    }
    if (DOM.sortFilter) {
        DOM.sortFilter.addEventListener('change', debounce(applyFiltersAndRender, 200));
    }

    // Chatbot
    if (DOM.chatbotSendBtn) {
        DOM.chatbotSendBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            handleChatSubmit(e);
        });
    }
    if (DOM.chatbotInput) {
        DOM.chatbotInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                event.stopPropagation();
                handleChatSubmit(event);
            }
        });
    }

    // Listing Assistant
    if (DOM.listingAssistantSendBtn) {
        DOM.listingAssistantSendBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            handleListingAssistantSubmit(e);
        });
    }
    if (DOM.listingAssistantInput) {
        DOM.listingAssistantInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                event.stopPropagation();
                handleListingAssistantSubmit(event);
            }
        });
    }
    if (DOM.listingAssistantNewChatBtn) {
        DOM.listingAssistantNewChatBtn.addEventListener('click', () => {
            if (!requireAuth()) return;
            createNewListingAssistantSession();
            showSuccess('Started a new chat');
        });
    }

    // Chatbot New Chat
    if (DOM.chatbotNewChatBtn) {
        DOM.chatbotNewChatBtn.addEventListener('click', () => {
            if (!requireAuth()) return;
            createNewChatbotSession();
            showSuccess('Started a new chat');
        });
    }

    // Modal
    if (DOM.carInfoCloseBtn) {
        DOM.carInfoCloseBtn.addEventListener('click', () => {
            if (DOM.carInfoModal) DOM.carInfoModal.classList.add('hidden');
        });
    }
    if (DOM.carInfoModal) {
        DOM.carInfoModal.addEventListener('click', (event) => {
            if (event.target === DOM.carInfoModal) DOM.carInfoModal.classList.add('hidden');
        });
    }
    
    // Edit Listing Modal
    if (DOM.editListingForm) {
        DOM.editListingForm.addEventListener('submit', handleEditListing);
    }
    if (DOM.editListingCancelBtn) {
        DOM.editListingCancelBtn.addEventListener('click', hideEditListingModal);
    }
    if (DOM.editListingModal) {
        DOM.editListingModal.addEventListener('click', (event) => {
            if (event.target === DOM.editListingModal) hideEditListingModal();
        });
    }
}

// --- UTILITY FUNCTIONS ---
function debounce(func, wait) {
    let timeout;
    let lastCallTime = 0;
    return function executedFunction(...args) {
        const now = Date.now();
        const timeSinceLastCall = now - lastCallTime;
        
        // If called recently, extend the timeout
        if (timeSinceLastCall < wait) {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                lastCallTime = Date.now();
                func(...args);
            }, wait - timeSinceLastCall);
        } else {
            // Call immediately if enough time has passed
            clearTimeout(timeout);
            lastCallTime = now;
            func(...args);
        }
    };
}

// --- INITIALIZATION ---
async function initApp() {
    // Load favorites from server first (user-specific)
    try {
        favorites = await fetchFavorites();
        console.log(`Loaded ${favorites.length} favorites from server`);
    } catch (error) {
        console.error('Failed to load favorites:', error);
        favorites = [];
    }
    
    // Load makes for filter
    try {
        await loadMakes();
    } catch (error) {
        console.error('Failed to load makes:', error);
    }
    
    // Load initial car data
    try {
        const cars = await fetchCarData();
        console.log(`Loaded ${cars.length} cars`);
        
        if (cars.length > 0) {
            // Render cars with favorites loaded
            applyFiltersAndRender();
            // Load reviews page
            await renderReviewsPage();
        } else {
            console.warn('No cars found in database');
            showError(DOM.listingsContainer, 'No cars found. Please run the data ingestion script: python ingest_excel_to_db.py');
        }
    } catch (error) {
        console.error('Failed to load cars:', error);
        showError(DOM.listingsContainer, `Failed to load cars: ${error.message}`);
    }
}

async function init() {
    console.log('🚀 IntelliWheels Initializing...');
    
    // Wait for DOM to be fully ready
    if (document.readyState === 'loading') {
        console.log('DOM still loading, waiting...');
        document.addEventListener('DOMContentLoaded', init);
        return;
    }
    
    console.log('DOM is ready, checking elements...');
    
    // Refresh DOM elements to ensure they're all available
    refreshDOM();
    
    // Load chat sessions from localStorage
    chatbotSessions = Storage.getChatbotSessions();
    listingAssistantSessions = Storage.getListingAssistantSessions();
    
    // Create initial sessions if none exist
    if (chatbotSessions.length === 0) {
        createNewChatbotSession();
    } else {
        currentChatbotSessionId = chatbotSessions[0].id;
        conversationHistory = chatbotSessions[0].history || [];
        renderChatbotChatList();
        // Render conversation if history exists
        if (conversationHistory.length > 0 && DOM.chatbotLog) {
            DOM.chatbotLog.innerHTML = '';
            conversationHistory.forEach(msg => {
                appendMessage(msg.text, msg.role === 'user' ? 'user' : 'bot');
            });
        }
    }
    
    if (listingAssistantSessions.length === 0) {
        createNewListingAssistantSession();
    } else {
        currentListingAssistantSessionId = listingAssistantSessions[0].id;
        listingAssistantHistory = listingAssistantSessions[0].history || [];
        renderListingAssistantChatList();
        // Render conversation if history exists
        if (listingAssistantHistory.length > 0 && DOM.listingAssistantConversation) {
            DOM.listingAssistantConversation.innerHTML = '';
            listingAssistantHistory.forEach(msg => {
                appendListingAssistantMessage(msg.text, msg.role === 'user' ? 'user' : 'bot');
            });
        }
    }
    
    // Check if DOM elements exist
    console.log('Checking DOM elements:');
    console.log('- listingsContainer:', DOM.listingsContainer);
    console.log('- searchInput:', DOM.searchInput);
    console.log('- makeFilter:', DOM.makeFilter);
    console.log('- loginForm:', DOM.loginForm);
    console.log('- signupForm:', DOM.signupForm);
    
    if (!DOM.listingsContainer || !DOM.searchInput || !DOM.makeFilter) {
        console.error('Some DOM elements not found! Retrying...');
        setTimeout(init, 100);
        return;
    }
    
    // Setup event listeners first
    console.log('Setting up event listeners...');
    setupEventListeners();
    createParticles();
    
    // Check authentication first
    const authenticated = await checkAuthentication();
    
    if (authenticated) {
        // User is authenticated, show main app
        updateAuthUI();
        showPage('listings');
        
        // Clear any old localStorage favorites (they might be from a different user or outdated)
        localStorage.removeItem('carFavorites');
        favorites = [];
        
        // Check backend health
        try {
            const health = await healthCheck();
            if (!health.success) {
                console.warn('Backend not available:', health.error);
                showError(null, '⚠️ Backend server not available. Please start the Flask server (python app.py)');
            } else {
                console.log('✅ Backend is healthy');
            }
        } catch (error) {
            console.warn('Health check failed:', error);
        }
        
        // Initialize app data (will load favorites from server)
        await initApp();
        
        console.log('✅ IntelliWheels Ready!');
    } else {
        // User not authenticated, show login page
        updateAuthUI();
        showPage('login');
        console.log('🔒 Please login to access IntelliWheels');
    }
}

// Make functions available globally
window.showCarInfoModal = showCarInfoModal;
window.showPage = showPage;

// Start initialization
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    console.log('Document ready, starting init...');
    setTimeout(init, 0);
} else {
    console.log('Waiting for DOMContentLoaded...');
    document.addEventListener('DOMContentLoaded', init);
}
