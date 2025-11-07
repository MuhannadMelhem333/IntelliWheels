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
    createParticles, 
    showTypingIndicator, 
    hideTypingIndicator,
    showLoadingState,
    hideLoadingState,
    showError,
    showSuccess
} from './ui.js';
import { 
    getCars, 
    createCar, 
    updateCar, 
    deleteCar, 
    getMakes, 
    getFavorites, 
    addFavorite, 
    removeFavorite, 
    handleChatbotQuery,
    healthCheck
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

// --- LOCALSTORAGE FUNCTIONS ---
const Storage = {
    getFavorites: () => JSON.parse(localStorage.getItem('carFavorites')) || [],
    saveFavorites: (favs) => localStorage.setItem('carFavorites', JSON.stringify(favs)),
};

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
            Storage.saveFavorites(favorites);
            return favorites;
        }
    } catch (error) {
        console.error("Could not fetch favorites:", error);
        // Fallback to localStorage
        favorites = Storage.getFavorites();
    }
    return favorites;
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
    isLoading = true;
    
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
        
        const response = await getCars(currentFilters);
        
        if (response.success) {
            allCars = response.cars || [];
            console.log(`Rendering ${allCars.length} cars`);
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
                showError(DOM.listingsContainer, response.error || "Could not filter cars. Please try again.");
            }
        }
    } catch (error) {
        console.error("Filter error:", error);
        showError(DOM.listingsContainer, "Could not filter cars. Please try again.");
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
        
        if (isFavorited) {
            await removeFavorite(carId);
            favorites = favorites.filter(id => id !== carId);
            carCardIcon?.classList.remove('favorited');
            showSuccess('Removed from favorites');
        } else {
            await addFavorite(carId);
            favorites.push(carId);
            carCardIcon?.classList.add('favorited');
            showSuccess('Added to favorites');
        }
        
        Storage.saveFavorites(favorites);
        
        if (!DOM.pages.favorites.classList.contains('hidden')) {
            renderFavoritesPage();
        }
    } catch (error) {
        console.error("Favorite toggle error:", error);
        showError(null, "Could not update favorites. Please try again.");
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
    if (!confirm('Are you sure you want to delete this car listing?')) {
        return;
    }
    
    try {
        const response = await deleteCar(carId);
        if (response.success) {
            showSuccess('Car deleted successfully!');
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

// --- CHATBOT HANDLING ---
async function handleChatSubmit() {
    const message = DOM.chatbotInput.value.trim();
    if (!message || isLoading) return;

    appendMessage(message, 'user');
    
    // Add user message to conversation history
    conversationHistory.push({ role: 'user', text: message });
    
    DOM.chatbotInput.value = '';
    showTypingIndicator();
    isLoading = true;

    try {
        console.log('Submitting chat message with API key:', GEMINI_API_KEY ? 'Present' : 'Missing');
        const responseText = await handleChatbotQuery(message, GEMINI_API_KEY, conversationHistory);
        hideTypingIndicator();
        
        // Check if response starts with "Error:" and handle it
        if (responseText && responseText.startsWith('Error:')) {
            appendMessage(responseText, 'bot');
            showError(null, responseText);
        } else {
            appendMessage(responseText || "I'm sorry, I couldn't generate a response.", 'bot');
            // Add bot response to conversation history
            conversationHistory.push({ role: 'bot', text: responseText });
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

// --- EVENT LISTENERS ---
function setupEventListeners() {
    // Logo Button
    DOM.logoBtn.addEventListener('click', () => {
        applyFiltersAndRender();
        showPage('listings');
    });

    // Navigation
    DOM.navButtons.listings.addEventListener('click', async () => {
        showPage('listings');
        await applyFiltersAndRender();
    });
    
    DOM.navButtons.reviews.addEventListener('click', async () => {
        showPage('reviews');
        await renderReviewsPage();
    });
    
    DOM.navButtons.favorites.addEventListener('click', async () => {
        showPage('favorites');
        await renderFavoritesPage();
    });
    
    DOM.navButtons.chatbot.addEventListener('click', () => showPage('chatbot'));
    DOM.navButtons.addListing.addEventListener('click', () => showPage('addListing'));

    // Form Submission
    DOM.addListingForm.addEventListener('submit', handleAddListing);

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
            const car = allCars.find(c => c.id === carId);
            if (car) {
                // TODO: Implement edit modal
                alert('Edit functionality coming soon!');
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

    // Filters
    DOM.searchInput.addEventListener('input', debounce(applyFiltersAndRender, 300));
    DOM.makeFilter.addEventListener('change', applyFiltersAndRender);
    DOM.sortFilter.addEventListener('change', applyFiltersAndRender);

    // Chatbot
    DOM.chatbotSendBtn.addEventListener('click', handleChatSubmit);
    DOM.chatbotInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') handleChatSubmit();
    });

    // Modal
    DOM.carInfoCloseBtn.addEventListener('click', () => DOM.carInfoModal.classList.add('hidden'));
    DOM.carInfoModal.addEventListener('click', (event) => {
        if (event.target === DOM.carInfoModal) DOM.carInfoModal.classList.add('hidden');
    });
}

// --- UTILITY FUNCTIONS ---
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// --- INITIALIZATION ---
async function init() {
    console.log('🚀 IntelliWheels Initializing...');
    
    // Wait for DOM to be fully ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
        return;
    }
    
    // Check if DOM elements exist
    if (!DOM.listingsContainer || !DOM.searchInput || !DOM.makeFilter) {
        console.error('DOM elements not found!');
        setTimeout(init, 100);
        return;
    }
    
    // Setup event listeners first
    setupEventListeners();
    showPage('listings');
    createParticles();
    
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
    
    // Load favorites
    try {
        favorites = await fetchFavorites();
        console.log(`Loaded ${favorites.length} favorites`);
    } catch (error) {
        console.error('Failed to load favorites:', error);
        favorites = Storage.getFavorites();
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
    
    console.log('✅ IntelliWheels Ready!');
}

// Start initialization
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(init, 0);
} else {
    document.addEventListener('DOMContentLoaded', init);
}
