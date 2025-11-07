// --- DOM Element Selection (Complete & Merged) ---
// Initialize DOM elements with null checks
function initializeDOM() {
    return {
        // Logo
        logoBtn: document.getElementById('logo-btn'),
        // Nav Buttons
        navButtons: {
            listings: document.getElementById('nav-listings'),
            reviews: document.getElementById('nav-reviews'),
            favorites: document.getElementById('nav-favorites'),
            chatbot: document.getElementById('nav-chatbot'),
            listingAssistant: document.getElementById('nav-listing-assistant'),
            analytics: document.getElementById('nav-analytics'),
            addListing: document.getElementById('nav-add-listing'),
        },
        // Page Containers
        pages: {
            login: document.getElementById('page-login'),
            signup: document.getElementById('page-signup'),
            listings: document.getElementById('page-listings'),
            reviews: document.getElementById('page-reviews'),
            favorites: document.getElementById('page-favorites'),
            chatbot: document.getElementById('page-chatbot'),
            listingAssistant: document.getElementById('page-listing-assistant'),
            analytics: document.getElementById('page-analytics'),
            addListing: document.getElementById('page-add-listing'),
        },
        // Auth Elements
        navAuthSection: document.getElementById('nav-auth-section'),
        navMainSection: document.getElementById('nav-main-section'),
        userNameDisplay: document.getElementById('user-name-display'),
        navLogout: document.getElementById('nav-logout'),
        loginForm: document.getElementById('login-form'),
        signupForm: document.getElementById('signup-form'),
        switchToSignup: document.getElementById('switch-to-signup'),
        switchToLogin: document.getElementById('switch-to-login'),
        loginError: document.getElementById('login-error'),
        signupError: document.getElementById('signup-error'),
        // Filter Controls
        searchInput: document.getElementById('search-input'),
        makeFilter: document.getElementById('make-filter'),
        sortFilter: document.getElementById('sort-filter'),
        // Content Containers
        listingsContainer: document.getElementById('listings-container'),
        reviewsContainer: document.getElementById('reviews-container'),
        favoritesContainer: document.getElementById('favorites-container'),
        // "Add Listing" Form
        addListingForm: document.getElementById('add-listing-form'),
        // Chatbot UI
        chatbotLog: document.getElementById('chatbot-log-fullscreen'),
        chatbotInput: document.getElementById('chatbot-input-fullscreen'),
        chatbotSendBtn: document.getElementById('chatbot-send-btn-fullscreen'),
        // Listing Assistant UI
        listingAssistantConversation: document.getElementById('listing-assistant-conversation'),
        listingAssistantInput: document.getElementById('listing-assistant-input'),
        listingAssistantSendBtn: document.getElementById('listing-assistant-send-btn'),
        listingAssistantNewChatBtn: document.getElementById('listing-assistant-new-chat-btn'),
        listingAssistantChatList: document.getElementById('listing-assistant-chat-list'),
        // Chatbot New Chat Button
        chatbotNewChatBtn: document.getElementById('chatbot-new-chat-btn'),
        chatbotChatList: document.getElementById('chatbot-chat-list'),
        // Car Details Modal
        carInfoModal: document.getElementById('car-info-modal'),
        carInfoContent: document.getElementById('car-info-content'),
        carInfoCloseBtn: document.getElementById('car-info-close-btn'),
    };
}

export const DOM = initializeDOM();

// Re-initialize DOM elements if needed (for dynamic content)
export function refreshDOM() {
    Object.assign(DOM, initializeDOM());
}

/**
 * Shows a specific page and hides others, updates nav button state.
 * Optimized for performance - minimal animations.
 * @param {string} pageId - The ID of the page to show.
 */
export function showPage(pageId) {
    // Hide all pages immediately (no animation delay for better performance)
    Object.values(DOM.pages).forEach(page => {
        if (page) {
            page.classList.add('hidden');
            page.style.opacity = '0';
            page.style.transform = 'translateY(20px)';
        }
    });
    
    // Show target page
    const targetPage = DOM.pages[pageId];
    if (targetPage) {
        targetPage.classList.remove('hidden');
        // Use requestAnimationFrame for smooth transition
        requestAnimationFrame(() => {
            if (targetPage) {
                targetPage.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                targetPage.style.opacity = '1';
                targetPage.style.transform = 'translateY(0)';
            }
        });
    } else {
        console.warn(`Page "${pageId}" not found in DOM.pages`);
    }
    
    // Update nav button states
    Object.values(DOM.navButtons).forEach(btn => {
        if (btn) {
            btn.classList.remove('active');
        }
    });
    
    // Set active state for current page button
    const buttonMap = {
        'listings': DOM.navButtons.listings,
        'reviews': DOM.navButtons.reviews,
        'favorites': DOM.navButtons.favorites,
        'chatbot': DOM.navButtons.chatbot,
        'listingAssistant': DOM.navButtons.listingAssistant,
        'analytics': DOM.navButtons.analytics,
        'addListing': DOM.navButtons.addListing
    };
    
    if (buttonMap[pageId]) {
        buttonMap[pageId]?.classList.add('active');
    }
}

/**
 * Populates filter dropdowns based on available car data or makes array.
 * @param {Array<Object>|Array<string>} data - The full list of car objects or array of makes.
 */
export function populateFilters(data) {
    let makes;
    if (Array.isArray(data) && data.length > 0) {
        if (typeof data[0] === 'string') {
            // It's an array of makes
            makes = data;
        } else {
            // It's an array of car objects
            makes = [...new Set(data.map(car => car.make))];
        }
    } else {
        makes = [];
    }
    
    DOM.makeFilter.innerHTML = '<option value="all">All Makes</option>';
    makes.sort().forEach(make => {
        const option = document.createElement('option');
        option.value = make;
        option.textContent = make;
        DOM.makeFilter.appendChild(option);
    });
}

/**
 * Generates the HTML for star ratings.
 * @param {number} rating - The rating value.
 * @returns {string} HTML string for the stars.
 */
function createStarRating(rating) {
    let stars = '';
    for (let i = 1; i <= 5; i++) {
        const starClass = i <= rating ? 'text-yellow-400' : 'text-gray-500';
        stars += `<svg class="w-5 h-5 ${starClass}" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>`;
    }
    return stars;
}

/**
 * Creates HTML for a car list item, including a favorite button.
 * @param {Object} car - The car data object.
 * @param {Array<string>} favorites - Array of favorited car IDs.
 * @returns {HTMLDivElement}
 */
function createCarListItem(car, favorites = []) {
    const card = document.createElement('div');
    card.className = 'car-list-item';
    const isFavorited = favorites.includes(car.id);
    const specs = car.specs || {};
    const imageUrl = car.image || 'https://via.placeholder.com/400x300?text=No+Image';

    card.innerHTML = `
        <img src="${imageUrl}" 
             alt="${car.make} ${car.model}" 
             class="car-list-img"
             loading="lazy"
             decoding="async"
             onerror="this.src='https://via.placeholder.com/400x300?text=Image+Error'">
        <div class="car-list-details">
            <div>
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <h3 class="text-2xl font-semibold text-white">${car.make} ${car.model}</h3>
                        <p class="text-gray-400">${car.year || 'N/A'} ${specs.bodyStyle ? `&bull; ${specs.bodyStyle}` : ''}</p>
                    </div>
                    <button class="favorite-btn ${isFavorited ? 'favorited' : ''}" data-car-id="${car.id}" aria-label="Favorite">
                        <svg class="w-7 h-7" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clip-rule="evenodd"></path>
                        </svg>
                    </button>
                </div>
                ${car.rating ? `
                    <div class="flex items-center gap-2 mt-2">
                        ${createStarRating(car.rating)}
                        <span class="text-yellow-400 font-bold">${car.rating.toFixed(1)}</span>
                        <span class="text-gray-400 text-sm">(${car.reviews || 0} reviews)</span>
                    </div>
                ` : ''}
                <p class="text-3xl font-bold text-blue-400 mt-4">${new Intl.NumberFormat().format(car.price || 0)} ${car.currency || 'AED'}</p>
            </div>
            <div class="mt-4 flex justify-end gap-2">
                <button class="details-button bg-blue-600 text-white py-2 px-5 rounded-lg hover:bg-blue-700 transition-colors" data-car-id="${car.id}">View Details</button>
            </div>
        </div>`;
    return card;
}

/**
 * Renders a list of cars to a specified container.
 * Optimized for smooth performance with batched animations.
 * @param {Array<Object>} carList - The cars to render.
 * @param {HTMLElement} container - The container element.
 * @param {Array<string>} favorites - Array of favorited car IDs.
 */
export function renderCarList(carList, container, favorites = []) {
    if (!container) {
        console.error('Container not found for rendering');
        return;
    }
    
    if (!Array.isArray(carList)) {
        console.error('carList is not an array:', carList);
        container.innerHTML = `<p class="text-gray-400 text-center text-lg py-8">Error: Invalid car data.</p>`;
        return;
    }
    
    if (carList.length === 0) {
        container.innerHTML = `<p class="text-gray-400 text-center text-lg py-8">No cars found.</p>`;
        return;
    }
    
    // Use DocumentFragment for better performance
    const fragment = document.createDocumentFragment();
    
    // Batch create all cards first
    const cards = [];
    carList.forEach((car, index) => {
        try {
            const card = createCarListItem(car, favorites);
            if (card) {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                cards.push(card);
                fragment.appendChild(card);
            }
        } catch (error) {
            console.error(`Error rendering car ${index}:`, error, car);
        }
    });
    
    // Clear container once
    container.innerHTML = '';
    container.appendChild(fragment);
    
    // Batch animate all cards using requestAnimationFrame for smooth performance
    requestAnimationFrame(() => {
        // Animate all cards immediately for instant feedback, then stagger for visual appeal
        cards.forEach((card, index) => {
            // Small stagger for visual effect without performance hit
            setTimeout(() => {
                card.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, Math.min(index * 15, 200)); // Max 200ms total delay
        });
    });
}

/**
 * Sets up an observer to animate elements as they scroll into view.
 */
function setupScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    document.querySelectorAll('.car-list-item').forEach(item => observer.observe(item));
}

/**
 * Shows the Car Info Modal with data for the selected car.
 * @param {Object} car - The car object to display.
 */
export function showCarInfoModal(car) {
    const specs = car.specs || {};
    const engines = car.engines || [];
    const statistics = car.statistics || {};
    
    // Build engines HTML
    let enginesHtml = '';
    if (engines.length > 0) {
        enginesHtml = '<div class="mt-4"><h4 class="text-lg font-semibold text-gray-300 mb-2">Engine Options</h4>';
        engines.forEach((engine, idx) => {
            enginesHtml += `<div class="bg-gray-700 p-3 rounded-lg mb-2">`;
            Object.entries(engine).forEach(([key, value]) => {
                enginesHtml += `<div class="text-sm text-gray-300"><strong>${key}:</strong> ${value}</div>`;
            });
            enginesHtml += `</div>`;
        });
        enginesHtml += '</div>';
    }
    
    // Build statistics HTML
    let statsHtml = '';
    if (Object.keys(statistics).length > 0) {
        statsHtml = '<div class="mt-4"><h4 class="text-lg font-semibold text-gray-300 mb-2">Statistics</h4><div class="grid grid-cols-2 gap-2">';
        Object.entries(statistics).forEach(([key, value]) => {
            statsHtml += `<div class="text-sm text-gray-400"><strong>${key}:</strong> ${value}</div>`;
        });
        statsHtml += '</div></div>';
    }
    
    if (!DOM.carInfoModal || !DOM.carInfoContent) {
        console.error('Modal elements not found');
        return;
    }
    
    const content = `
        <div class="flex justify-between items-start mb-4">
            <div>
                <h2 class="text-3xl font-bold text-white mb-2">${car.make} ${car.model} ${car.year ? `(${car.year})` : ''}</h2>
                <p class="text-2xl font-bold text-blue-400">${new Intl.NumberFormat().format(car.price || 0)} ${car.currency || 'AED'}</p>
            </div>
        </div>
        <div class="mb-6">
            <img src="${car.image || 'https://via.placeholder.com/800x400?text=No+Image'}" 
                 alt="${car.make} ${car.model}" 
                 class="rounded-lg shadow-md w-full max-h-96 object-cover"
                 onerror="this.src='https://via.placeholder.com/800x400?text=Image+Not+Available'">
        </div>
        <h3 class="text-xl font-semibold text-gray-300 mb-4 border-b border-gray-600 pb-2">Specifications</h3>
        <div class="grid grid-cols-2 gap-4 text-gray-400 mb-6">
            <div><strong class="text-gray-300">Body Style:</strong> ${specs.bodyStyle || 'N/A'}</div>
            <div><strong class="text-gray-300">Engine:</strong> ${specs.engine || 'N/A'}</div>
            <div><strong class="text-gray-300">Horsepower:</strong> ${specs.horsepower || 0} hp</div>
            <div><strong class="text-gray-300">Fuel Economy:</strong> ${specs.fuelEconomy || 'N/A'}</div>
            ${Object.entries(specs).filter(([k]) => !['bodyStyle', 'engine', 'horsepower', 'fuelEconomy'].includes(k)).map(([key, value]) => 
                `<div><strong class="text-gray-300">${key}:</strong> ${value}</div>`
            ).join('')}
        </div>
        ${enginesHtml}
        ${statsHtml}
        ${car.rating ? `
            <div class="mt-6 flex items-center gap-2">
                ${createStarRating(car.rating)}
                <span class="text-yellow-400 font-bold text-xl">${car.rating.toFixed(1)}</span>
                <span class="text-gray-400">(${car.reviews || 0} reviews)</span>
            </div>
        ` : ''}`;
    
    DOM.carInfoContent.innerHTML = content;
    DOM.carInfoModal.classList.remove('hidden');
}

/**
 * Adds the animated particles to the chatbot background.
 */
export function createParticles() {
    const bg = document.getElementById('chatbot-animation-bg');
    if (!bg) return;
    const particleCount = 30;
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        const size = Math.random() * 150 + 50;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.bottom = `0px`;
        particle.style.animationDuration = `${Math.random() * 20 + 10}s`;
        particle.style.animationDelay = `${Math.random() * 10}s`;
        particle.style.opacity = Math.random() * 0.5 + 0.1;
        bg.appendChild(particle);
    }
    
}

/**
 * Adds a message to the listing assistant log
 * @param {string} message - The text content of the message
 * @param {string} sender - The sender ('user' or 'bot')
 * @param {Object} listingData - Optional structured listing data
 * @param {string} actionType - Optional action type (create_listing, update_listing)
 */
export function appendListingAssistantMessage(message, sender, listingData = null, actionType = null) {
    if (!DOM.listingAssistantConversation) {
        console.warn('Listing assistant conversation container not found');
        return;
    }
    
    // Remove welcome card if it exists
    const welcomeCard = DOM.listingAssistantConversation.querySelector('.listing-welcome-card');
    if (welcomeCard) {
        welcomeCard.remove();
    }
    
    const messageEl = document.createElement('div');
    const avatarName = sender === 'user' ? 'You' : 'AI';
    messageEl.className = `listing-message-card ${sender}`;
    
    let actionButtons = '';
    if (sender === 'bot' && listingData && actionType === 'create_listing') {
        actionButtons = `
            <div class="mt-4 p-4 bg-blue-900 bg-opacity-30 rounded-lg border border-blue-500">
                <h4 class="text-white font-semibold mb-2">📋 Listing Summary</h4>
                <div class="text-sm text-gray-300 space-y-1">
                    ${listingData.make ? `<p><strong>Make:</strong> ${listingData.make}</p>` : ''}
                    ${listingData.model ? `<p><strong>Model:</strong> ${listingData.model}</p>` : ''}
                    ${listingData.year ? `<p><strong>Year:</strong> ${listingData.year}</p>` : ''}
                    ${listingData.price ? `<p><strong>Price:</strong> ${listingData.price} ${listingData.currency || 'AED'}</p>` : ''}
                </div>
                <button class="mt-3 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors create-listing-btn" data-listing-data='${JSON.stringify(listingData)}'>
                    Create Listing
                </button>
            </div>
        `;
    }
    
    messageEl.innerHTML = `
        <div class="listing-message-header">
            <div class="listing-message-avatar">${avatarName.charAt(0)}</div>
            <div class="listing-message-author">${avatarName}</div>
        </div>
        <div class="listing-message-content">
            <p>${message}</p>
            ${actionButtons}
        </div>
    `;
    
    DOM.listingAssistantConversation.appendChild(messageEl);
    DOM.listingAssistantConversation.scrollTop = DOM.listingAssistantConversation.scrollHeight;
    
    // Add click handler for create listing button
    if (actionButtons) {
        const createBtn = messageEl.querySelector('.create-listing-btn');
        if (createBtn) {
            createBtn.addEventListener('click', async () => {
                const data = JSON.parse(createBtn.dataset.listingData);
                // This will be handled in main.js
                if (window.handleCreateListingFromAssistant) {
                    await window.handleCreateListingFromAssistant(data);
                }
            });
        }
    }
}

/**
 * Clears the listing assistant chat and resets to welcome message
 */
export function resetListingAssistantChat() {
    if (!DOM.listingAssistantConversation) return;
    
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
}

/**
 * Clears the chatbot chat and resets to welcome message
 */
export function resetChatbotChat() {
    if (!DOM.chatbotLog) return;
    
    DOM.chatbotLog.innerHTML = `
        <div class="message-container bot-message initial-bot-message" data-message-id="welcome">
            <div class="avatar">AI</div>
            <div class="message-content">
                <p>Welcome to the IntelliWheels AI Assistant. How can I help you today?</p>
            </div>
            <div class="message-rating hidden">
                <span class="text-xs text-gray-400 mr-2">Rate this response:</span>
                <button class="rating-btn" data-rating="1" title="Poor">⭐</button>
                <button class="rating-btn" data-rating="2" title="Fair">⭐</button>
                <button class="rating-btn" data-rating="3" title="Good">⭐</button>
                <button class="rating-btn" data-rating="4" title="Very Good">⭐</button>
                <button class="rating-btn" data-rating="5" title="Excellent">⭐</button>
            </div>
        </div>
    `;
}

/**
 * Adds a new message to the chatbot log with the new professional design.
 * @param {string} message - The text content of the message.
 * @param {string} sender - The sender ('user' or 'bot').
 * @param {Array<number>} carIds - Optional array of car IDs to display as recommendations.
 */
export async function appendMessage(message, sender, carIds = [], messageId = null) {
    if (!DOM.chatbotLog) {
        console.warn('Chatbot log container not found');
        return;
    }
    
    const messageEl = document.createElement('div');
    const avatarName = sender === 'user' ? 'You' : 'AI';
    messageEl.className = `message-container ${sender}-message`;
    if (messageId) {
        messageEl.setAttribute('data-message-id', messageId);
    }

    let carRecommendationsHtml = '';
    const carDataMap = new Map();
    
    if (sender === 'bot' && carIds && carIds.length > 0) {
        // Fetch car details and create recommendation cards
        const { getCar } = await import('./api.js');
        
        carRecommendationsHtml = '<div class="car-recommendations mt-4 space-y-2">';
        carRecommendationsHtml += '<p class="text-sm text-gray-400 font-semibold mb-2">💡 Recommended Cars:</p>';
        
        // Fetch all cars in parallel
        const carPromises = carIds.slice(0, 3).map(async (carId) => {
            try {
                const carResponse = await getCar(carId);
                if (carResponse.success && carResponse.car) {
                    return carResponse.car;
                }
            } catch (error) {
                console.error(`Error fetching car ${carId}:`, error);
            }
            return null;
        });
        
        const cars = await Promise.all(carPromises);
        
        for (const car of cars) {
            if (car) {
                carDataMap.set(car.id, car);
                carRecommendationsHtml += `
                    <div class="car-recommendation-card bg-gray-800 bg-opacity-50 rounded-lg p-3 border border-gray-700 hover:border-blue-500 transition-colors cursor-pointer" data-car-id="${car.id}">
                        <div class="flex items-center gap-3">
                            ${car.image ? `<img src="${car.image}" alt="${car.make} ${car.model}" class="w-16 h-16 object-cover rounded" onerror="this.style.display='none'">` : ''}
                            <div class="flex-1">
                                <h4 class="text-white font-semibold">${car.make} ${car.model} ${car.year ? `(${car.year})` : ''}</h4>
                                <p class="text-blue-400 font-bold">${new Intl.NumberFormat().format(car.price || 0)} ${car.currency || 'AED'}</p>
                                ${car.rating > 0 ? `<p class="text-yellow-400 text-sm">⭐ ${car.rating.toFixed(1)} (${car.reviews || 0} reviews)</p>` : ''}
                            </div>
                            <button class="text-blue-400 hover:text-blue-300 text-sm font-semibold">View →</button>
                        </div>
                    </div>
                `;
            }
        }
        
        carRecommendationsHtml += '</div>';
    }

    messageEl.innerHTML = `
        <div class="avatar">${avatarName}</div>
        <div class="message-content">
            <p>${message}</p>
            ${carRecommendationsHtml}
        </div>
        ${sender === 'bot' && messageId ? `
        <div class="message-rating">
            <span class="text-xs text-gray-400 mr-2">Rate this response:</span>
            <button class="rating-btn" data-rating="1" data-message-id="${messageId}" title="Poor">⭐</button>
            <button class="rating-btn" data-rating="2" data-message-id="${messageId}" title="Fair">⭐</button>
            <button class="rating-btn" data-rating="3" data-message-id="${messageId}" title="Good">⭐</button>
            <button class="rating-btn" data-rating="4" data-message-id="${messageId}" title="Very Good">⭐</button>
            <button class="rating-btn" data-rating="5" data-message-id="${messageId}" title="Excellent">⭐</button>
        </div>
        ` : ''}
    `;
    DOM.chatbotLog.appendChild(messageEl);
    DOM.chatbotLog.scrollTop = DOM.chatbotLog.scrollHeight;
    
    // Add click handlers for car recommendation cards
    if (carIds && carIds.length > 0 && carDataMap.size > 0) {
        const cards = messageEl.querySelectorAll('.car-recommendation-card');
        cards.forEach(card => {
            card.addEventListener('click', async () => {
                const carId = parseInt(card.dataset.carId);
                const car = carDataMap.get(carId);
                if (car) {
                    // Use the showCarInfoModal function from the current module
                    showCarInfoModal(car);
                } else {
                    // Fallback: fetch car if not in map
                    const { getCar } = await import('./api.js');
                    try {
                        const response = await getCar(carId);
                        if (response.success && response.car) {
                            showCarInfoModal(response.car);
                        }
                    } catch (error) {
                        console.error('Error loading car details:', error);
                    }
                }
            });
        });
    }
    
    // Add rating button handlers for bot messages
    if (sender === 'bot' && messageId) {
        const ratingButtons = messageEl.querySelectorAll('.rating-btn');
        ratingButtons.forEach(btn => {
            btn.addEventListener('click', async () => {
                const rating = parseInt(btn.dataset.rating);
                const msgId = btn.dataset.messageId;
                
                // Disable all rating buttons
                ratingButtons.forEach(b => {
                    b.disabled = true;
                    b.style.opacity = '0.5';
                });
                
                // Highlight selected rating
                for (let i = 1; i <= rating; i++) {
                    const btnToHighlight = messageEl.querySelector(`.rating-btn[data-rating="${i}"]`);
                    if (btnToHighlight) {
                        btnToHighlight.style.color = '#fbbf24'; // Yellow
                    }
                }
                
                // Submit rating
                try {
                    const { rateChatbotResponse } = await import('./api.js');
                    await rateChatbotResponse(msgId, rating);
                } catch (error) {
                    console.error('Error rating message:', error);
                }
            });
        });
    }
}

/**
 * Shows the bot typing indicator.
 * @param {HTMLElement} container - Optional container element (defaults to chatbot log)
 */
export function showTypingIndicator(container = null) {
    const targetContainer = container || DOM.chatbotLog || DOM.listingAssistantLog;
    if (!targetContainer) return;
    
    if (targetContainer.querySelector('#typing-indicator')) return;
    const typingEl = document.createElement('div');
    typingEl.id = 'typing-indicator';
    typingEl.className = 'message-container bot-message typing-indicator';
    typingEl.innerHTML = `
        <div class="avatar">AI</div>
        <div class="message-content">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    targetContainer.appendChild(typingEl);
    targetContainer.scrollTop = targetContainer.scrollHeight;
}

/**
 * Hides the bot typing indicator.
 * @param {HTMLElement} container - Optional container element (defaults to chatbot log)
 */
export function hideTypingIndicator(container = null) {
    const targetContainer = container || DOM.chatbotLog || DOM.listingAssistantLog;
    if (!targetContainer) return;
    
    const typingEl = targetContainer.querySelector('#typing-indicator');
    if (typingEl) {
        typingEl.remove();
    }
}

/**
 * Shows loading state in a container
 */
export function showLoadingState(container) {
    if (!container) return;
    const loadingHtml = `
        <div class="loading-container">
            <div class="spinner"></div>
            <p class="text-gray-400 mt-4">Loading...</p>
        </div>
    `;
    container.innerHTML = loadingHtml;
}

/**
 * Hides loading state
 */
export function hideLoadingState() {
    // Loading state is cleared when content is rendered
}

/**
 * Shows error message
 */
export function showError(container, message) {
    if (container) {
        container.innerHTML = `
            <div class="error-container">
                <div class="error-icon">⚠️</div>
                <p class="text-red-400 text-lg">${message}</p>
            </div>
        `;
    } else {
        // Show toast notification
        showToast(message, 'error');
    }
}

/**
 * Shows success message
 */
export function showSuccess(message) {
    showToast(message, 'success');
}

/**
 * Shows toast notification
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // Add entrance animation
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // Auto-remove after delay with exit animation
    setTimeout(() => {
        toast.classList.remove('show');
        toast.style.transition = 'transform 0.4s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.4s ease';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}
