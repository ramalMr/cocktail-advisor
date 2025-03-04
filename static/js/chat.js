class CocktailChat {
    constructor() {
        this.initialize();
        this.bindEvents();
    }

    initialize() {
        // Initialize DOM elements
        this.elements = {
            chatForm: document.getElementById('chat-form'),
            chatMessages: document.getElementById('chat-messages'),
            messageInput: document.getElementById('message'),
            preferencesModal: document.getElementById('preferences-modal'),
            editPreferencesBtn: document.getElementById('edit-preferences'),
            closePreferencesBtn: document.getElementById('close-preferences'),
            preferencesForm: document.getElementById('preferences-form'),
            typingIndicator: document.getElementById('typing-indicator'),
            favIngredientsInput: document.getElementById('favorite-ingredients-input'),
            favIngredientsTags: document.getElementById('favorite-ingredients-tags'),
            allergiesInput: document.getElementById('allergies-input'),
            allergiesTags: document.getElementById('allergies-tags')
        };

        // Initialize state
        this.state = {
            preferences: {
                favoriteIngredients: [],
                allergies: []
            },
            isProcessing: false
        };

        // Load initial data
        this.loadUserPreferences();
    }

    bindEvents() {
        // Chat form submission
        this.elements.chatForm.addEventListener('submit', (e) => this.handleChatSubmit(e));

        // Preferences modal
        this.elements.editPreferencesBtn.addEventListener('click', () => this.openPreferencesModal());
        this.elements.closePreferencesBtn.addEventListener('click', () => this.closePreferencesModal());
        this.elements.preferencesForm.addEventListener('submit', (e) => this.handlePreferencesSubmit(e));

        // Preference inputs
        this.elements.favIngredientsInput.addEventListener('keydown', (e) => this.handleTagInput(e, 'favoriteIngredients'));
        this.elements.allergiesInput.addEventListener('keydown', (e) => this.handleTagInput(e, 'allergies'));
    }

    async handleChatSubmit(e) {
        e.preventDefault();
        if (this.state.isProcessing) return;

        const message = this.elements.messageInput.value.trim();
        if (!message) return;

        this.appendMessage('user', message);
        this.elements.messageInput.value = '';
        this.elements.typingIndicator.classList.remove('hidden');
        this.state.isProcessing = true;

        try {
            const response = await this.sendMessage(message);
            this.appendMessage('assistant', response.message);
            
            if (response.cocktails) {
                this.updateRecommendations(response.cocktails);
            }
        } catch (error) {
            this.appendMessage('system', 'Error: Could not send message. Please try again.');
            console.error('Chat error:', error);
        } finally {
            this.elements.typingIndicator.classList.add('hidden');
            this.state.isProcessing = false;
        }
    }

    async sendMessage(message) {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `message=${encodeURIComponent(message)}&user_id=ramalMr`
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    appendMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);
        
        // Add sender icon and label
        const headerDiv = document.createElement('div');
        headerDiv.classList.add('flex', 'items-center', 'mb-2');
        
        const icon = document.createElement('i');
        icon.classList.add('fas', sender === 'user' ? 'fa-user' : 'fa-robot', 'mr-2');
        icon.classList.add(sender === 'user' ? 'text-purple-600' : 'text-blue-600');
        
        const senderLabel = document.createElement('span');
        senderLabel.classList.add('text-sm', 'text-gray-500');
        senderLabel.textContent = sender.charAt(0).toUpperCase() + sender.slice(1);
        
        headerDiv.appendChild(icon);
        headerDiv.appendChild(senderLabel);
        
        // Add message content
        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');
        contentDiv.textContent = text;
        
        messageDiv.appendChild(headerDiv);
        messageDiv.appendChild(contentDiv);
        
        this.elements.chatMessages.appendChild(messageDiv);
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    async loadUserPreferences() {
        try {
            const response = await fetch('/api/preferences?user_id=ramalMr');
            const preferences = await response.json();
            
            this.state.preferences = preferences;
            this.updatePreferencesDisplay();
        } catch (error) {
            console.error('Error loading preferences:', error);
        }
    }

    updatePreferencesDisplay() {
        const preferencesList = document.getElementById('preferences-list');
        preferencesList.innerHTML = '';

        // Add favorite ingredients section
        if (this.state.preferences.favoriteIngredients.length > 0) {
            const section = this.createPreferenceSection(
                'Favorite Ingredients',
                this.state.preferences.favoriteIngredients
            );
            preferencesList.appendChild(section);
        }

        // Add allergies section
        if (this.state.preferences.allergies.length > 0) {
            const section = this.createPreferenceSection(
                'Allergies',
                this.state.preferences.allergies
            );
            preferencesList.appendChild(section);
        }
    }

    createPreferenceSection(title, items) {
        const section = document.createElement('div');
        section.classList.add('mb-4');

        const titleEl = document.createElement('h3');
        titleEl.classList.add('text-sm', 'font-medium', 'text-gray-700', 'mb-2');
        titleEl.textContent = title;

        const tagsDiv = document.createElement('div');
        tagsDiv.classList.add('flex', 'flex-wrap', 'gap-2');

        items.forEach(item => {
            const tag = document.createElement('span');
            tag.classList.add('preference-tag');
            tag.textContent = item;
            tagsDiv.appendChild(tag);
        });

        section.appendChild(titleEl);
        section.appendChild(tagsDiv);
        return section;
    }

    updateRecommendations(cocktails) {
        const recommendationsDiv = document.getElementById('recent-recommendations');
        recommendationsDiv.innerHTML = '';

        cocktails.forEach(cocktail => {
            const card = this.createCocktailCard(cocktail);
            recommendationsDiv.appendChild(card);
        });
    }

    createCocktailCard(cocktail) {
        const card = document.createElement('div');
        card.classList.add('cocktail-card');

        const title = document.createElement('h3');
        title.textContent = cocktail.name;

        const ingredients = document.createElement('div');
        ingredients.classList.add('ingredients');
        ingredients.textContent = cocktail.ingredients
            .map(i => i.measure ? `${i.measure} ${i.name}` : i.name)
            .join(', ');

        const instructions = document.createElement('div');
        instructions.classList.add('instructions');
        instructions.textContent = cocktail.instructions;

        card.appendChild(title);
        card.appendChild(ingredients);
        card.appendChild(instructions);

        return card;
    }

    handleTagInput(e, type) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const input = e.target;
            const value = input.value.trim();

            if (value) {
                this.addTag(value, type);
                input.value = '';
            }
        }
    }

    addTag(value, type) {
        const tagsContainer = type === 'favoriteIngredients' 
            ? this.elements.favIngredientsTags 
            : this.elements.allergiesTags;

        const tag = document.createElement('div');
        tag.classList.add('preference-tag');
        
        const text = document.createElement('span');
        text.textContent = value;
        
        const removeBtn = document.createElement('button');
        removeBtn.innerHTML = '<i class="fas fa-times"></i>';
        removeBtn.addEventListener('click', () => tag.remove());
        
        tag.appendChild(text);
        tag.appendChild(removeBtn);
        tagsContainer.appendChild(tag);
    }

    openPreferencesModal() {
        this.elements.preferencesModal.classList.remove('hidden');
    }

    closePreferencesModal() {
        this.elements.preferencesModal.classList.add('hidden');
    }

    async handlePreferencesSubmit(e) {
        e.preventDefault();

        const favoriteIngredients = Array.from(
            this.elements.favIngredientsTags.querySelectorAll('.preference-tag')
        ).map(tag => tag.firstChild.textContent);

        const allergies = Array.from(
            this.elements.allergiesTags.querySelectorAll('.preference-tag')
        ).map(tag => tag.firstChild.textContent);

        try {
            await fetch('/api/preferences', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: 'ramalMr',
                    favorite_ingredients: favoriteIngredients,
                    allergies: allergies
                })
            });

            this.state.preferences = {
                favoriteIngredients,
                allergies
            };

            this.updatePreferencesDisplay();
            this.closePreferencesModal();
            
            this.appendMessage(
                'system',
                'Preferences updated successfully! Would you like some new recommendations?'
            );
        } catch (error) {
            console.error('Error updating preferences:', error);
            this.appendMessage('system', 'Error updating preferences. Please try again.');
        }
    }
}

// Initialize chat when document is ready
document.addEventListener('DOMContentLoaded', () => {
    window.cocktailChat = new CocktailChat();
});