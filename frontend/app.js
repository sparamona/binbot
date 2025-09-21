/**
 * BinBot Frontend Application
 * Handles session management, chat interface, and bin contents display
 */

class BinBotUI {
    constructor() {
        this.sessionId = null;
        this.currentBin = null;
        this.apiBase = window.location.origin;
        
        // DOM elements
        this.elements = {
            messageInput: document.getElementById('messageInput'),
            sendBtn: document.getElementById('sendBtn'),
            cameraBtn: document.getElementById('cameraBtn'),
            imageInput: document.getElementById('imageInput'),
            chatMessages: document.getElementById('chatMessages'),
            binTitle: document.getElementById('binTitle'),
            itemCount: document.getElementById('itemCount'),
            lastUpdated: document.getElementById('lastUpdated'),
            binContents: document.getElementById('binContents'),
            refreshBtn: document.getElementById('refreshBtn'),
            statusIndicator: document.getElementById('statusIndicator'),
            statusText: document.getElementById('statusText'),
            loadingOverlay: document.getElementById('loadingOverlay'),
            errorToast: document.getElementById('errorToast'),
            errorMessage: document.getElementById('errorMessage'),
            errorClose: document.getElementById('errorClose')
        };
        
        this.init();
    }

    async init() {
        console.log('🤖 Initializing BinBot UI...');
        
        try {
            await this.createSession();
            this.setupEventListeners();
            this.updateStatus('connected', 'Connected');
            console.log('✅ BinBot UI initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize BinBot UI:', error);
            this.updateStatus('error', 'Connection failed');
            this.showError('Failed to connect to BinBot. Please refresh the page.');
        }
    }

    async createSession() {
        console.log('🔄 Creating new session...');
        
        try {
            const response = await fetch(`${this.apiBase}/api/session`, {
                method: 'POST',
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error(`Session creation failed: ${response.status}`);
            }
            
            const data = await response.json();
            this.sessionId = data.session_id;
            console.log('✅ Session created:', this.sessionId);
            
        } catch (error) {
            console.error('❌ Session creation failed:', error);
            throw error;
        }
    }

    setupEventListeners() {
        // Send message on button click
        this.elements.sendBtn.addEventListener('click', () => this.handleSendMessage());
        
        // Send message on Enter key
        this.elements.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });
        
        // Camera button for image upload
        this.elements.cameraBtn.addEventListener('click', () => {
            this.elements.imageInput.click();
        });
        
        // Handle image selection
        this.elements.imageInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleImageUpload(e.target.files[0]);
            }
        });
        
        // Refresh bin contents
        this.elements.refreshBtn.addEventListener('click', () => {
            if (this.currentBin) {
                this.refreshBinContents(this.currentBin);
            }
        });
        
        // Close error toast
        this.elements.errorClose.addEventListener('click', () => {
            this.hideError();
        });
        
        // Auto-hide error toast after 5 seconds
        let errorTimeout;
        this.elements.errorToast.addEventListener('transitionend', () => {
            if (this.elements.errorToast.classList.contains('show')) {
                clearTimeout(errorTimeout);
                errorTimeout = setTimeout(() => this.hideError(), 5000);
            }
        });
    }

    async handleSendMessage() {
        const message = this.elements.messageInput.value.trim();
        if (!message) return;
        
        // Clear input and disable send button
        this.elements.messageInput.value = '';
        this.elements.sendBtn.disabled = true;
        
        // Add user message to chat
        this.addMessage(message, true);
        
        try {
            // Show typing indicator instead of loading overlay for better UX
            this.showTypingIndicator();

            const response = await fetch(`${this.apiBase}/api/chat/command`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ message })
            });

            if (!response.ok) {
                throw new Error(`Chat request failed: ${response.status}`);
            }

            const data = await response.json();

            // Hide typing indicator before showing response
            this.hideTypingIndicator();

            // Add bot response to chat
            this.addMessage(data.response, false);

            // Check if the response includes current_bin information
            if (data.current_bin && data.current_bin !== this.currentBin) {
                console.log(`🎯 Server reported bin change: ${this.currentBin} → ${data.current_bin}`);
                this.currentBin = data.current_bin;
                await this.refreshBinContents(data.current_bin);
            } else if (data.current_bin) {
                // Refresh current bin contents even if bin didn't change (items may have been added/removed)
                await this.refreshBinContents(data.current_bin);
            }

        } catch (error) {
            console.error('❌ Chat request failed:', error);
            this.hideTypingIndicator();
            this.addMessage('Sorry, I encountered an error processing your request. Please try again.', false);
            this.showError('Failed to send message. Please try again.');
        } finally {
            this.elements.sendBtn.disabled = false;
            this.elements.messageInput.focus();
        }
    }

    async handleImageUpload(file) {
        if (!file.type.startsWith('image/')) {
            this.showError('Please select a valid image file.');
            return;
        }
        
        if (file.size > 10 * 1024 * 1024) { // 10MB limit
            this.showError('Image file is too large. Please select a file under 10MB.');
            return;
        }
        
        try {
            this.showLoading('Analyzing image...');
            
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`${this.apiBase}/api/chat/image`, {
                method: 'POST',
                credentials: 'include',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Image upload failed: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Add image upload message to chat
            this.addImageMessage(file.name, data.analyzed_items);

            // Note: Image upload doesn't change current_bin, so no bin update needed
            // The user will need to explicitly add items to a bin via chat
            
        } catch (error) {
            console.error('❌ Image upload failed:', error);
            this.showError('Failed to analyze image. Please try again.');
        } finally {
            this.hideLoading();
            // Clear the file input
            this.elements.imageInput.value = '';
        }
    }





    // Add typing indicator
    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'bot-message typing-indicator';
        typingDiv.id = 'typingIndicator';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = `
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;

        typingDiv.appendChild(contentDiv);
        this.elements.chatMessages.appendChild(typingDiv);
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    async refreshBinContents(binId) {
        if (!binId) return;

        try {
            console.log(`🔄 Refreshing contents for bin ${binId}...`);

            // Use the direct inventory API to get bin contents
            const response = await fetch(`${this.apiBase}/api/inventory/bin/${binId}`, {
                method: 'GET',
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                console.log(`✅ Retrieved ${data.items?.length || 0} items for bin ${binId}`);
                this.updateBinDisplay(binId, data.items || []);
            } else {
                console.warn(`⚠️ API request failed with status ${response.status}`);
                this.showBinErrorState(binId, 'Failed to load bin contents');
            }
        } catch (error) {
            console.error('❌ Failed to refresh bin contents:', error);
            this.showBinErrorState(binId, 'Connection error');
        }
    }

    showBinErrorState(binId, errorMessage) {
        this.elements.binTitle.textContent = `Bin ${binId}`;
        this.elements.itemCount.textContent = 'Error loading';
        this.elements.lastUpdated.textContent = '';

        // Clear existing contents and show error
        this.elements.binContents.innerHTML = '';

        const errorDiv = document.createElement('div');
        errorDiv.className = 'empty-bin-message';
        errorDiv.innerHTML = `
            <div class="empty-icon">⚠️</div>
            <p>Failed to load bin contents</p>
            <p class="empty-hint">${errorMessage}</p>
        `;
        this.elements.binContents.appendChild(errorDiv);
    }

    updateBinDisplay(binId, items) {
        this.currentBin = binId;
        this.elements.binTitle.textContent = `Bin ${binId}`;
        this.elements.itemCount.textContent = `${items.length} item${items.length !== 1 ? 's' : ''}`;
        this.elements.lastUpdated.textContent = `Updated ${new Date().toLocaleTimeString()}`;

        // Clear existing contents
        this.elements.binContents.innerHTML = '';

        if (items.length === 0) {
            const emptyDiv = document.createElement('div');
            emptyDiv.className = 'empty-bin-message';
            emptyDiv.innerHTML = `
                <div class="empty-icon">📦</div>
                <p>Bin ${binId} is empty</p>
                <p class="empty-hint">Add items to this bin to see them here</p>
            `;
            this.elements.binContents.appendChild(emptyDiv);
            return;
        }

        // Display items
        items.forEach(item => {
            const itemDiv = this.createItemElement(item);
            this.elements.binContents.appendChild(itemDiv);
        });
    }

    createItemElement(item) {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'item';

        const headerDiv = document.createElement('div');
        headerDiv.className = 'item-header';

        const nameSpan = document.createElement('span');
        nameSpan.className = 'item-name';
        nameSpan.textContent = item.name;

        const idSpan = document.createElement('span');
        idSpan.className = 'item-id';
        idSpan.textContent = item.id ? item.id.substring(0, 8) + '...' : '';

        headerDiv.appendChild(nameSpan);
        headerDiv.appendChild(idSpan);

        itemDiv.appendChild(headerDiv);

        if (item.description) {
            const descDiv = document.createElement('div');
            descDiv.className = 'item-description';
            descDiv.textContent = item.description;
            itemDiv.appendChild(descDiv);
        }

        const metaDiv = document.createElement('div');
        metaDiv.className = 'item-meta';

        const dateSpan = document.createElement('span');
        if (item.created_at) {
            const date = new Date(item.created_at);
            dateSpan.textContent = date.toLocaleDateString();
        }

        metaDiv.appendChild(dateSpan);

        // Add image if available
        if (item.image_id || (item.images && item.images.length > 0)) {
            const imageId = item.image_id || item.images[0];
            const img = document.createElement('img');
            img.className = 'item-image';
            img.src = `${this.apiBase}/images/${imageId}`;
            img.alt = item.name;
            img.onerror = () => {
                img.style.display = 'none';
            };
            metaDiv.appendChild(img);
        }

        itemDiv.appendChild(metaDiv);

        return itemDiv;
    }

    addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'user-message' : 'bot-message';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(contentDiv);
        this.elements.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    addImageMessage(fileName, analyzedItems) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'user-message';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // Create image preview section
        const imageSection = document.createElement('div');
        imageSection.style.marginBottom = '0.75rem';

        const imageHeader = document.createElement('div');
        imageHeader.style.fontWeight = '500';
        imageHeader.style.marginBottom = '0.5rem';
        imageHeader.textContent = `📷 Uploaded: ${fileName}`;

        imageSection.appendChild(imageHeader);
        contentDiv.appendChild(imageSection);

        // Add analyzed items section
        if (analyzedItems && analyzedItems.length > 0) {
            const itemsSection = document.createElement('div');

            const itemsHeader = document.createElement('div');
            itemsHeader.style.fontWeight = '500';
            itemsHeader.style.marginBottom = '0.5rem';
            itemsHeader.textContent = 'Detected items:';
            itemsSection.appendChild(itemsHeader);

            const itemsList = document.createElement('ul');
            itemsList.style.margin = '0';
            itemsList.style.paddingLeft = '1.25rem';

            analyzedItems.forEach(item => {
                const listItem = document.createElement('li');
                listItem.style.marginBottom = '0.25rem';

                let itemText = item.name;
                if (item.description && item.description !== item.name) {
                    itemText += ` - ${item.description}`;
                }
                listItem.textContent = itemText;
                itemsList.appendChild(listItem);
            });

            itemsSection.appendChild(itemsList);
            contentDiv.appendChild(itemsSection);
        } else {
            const noItemsDiv = document.createElement('div');
            noItemsDiv.style.color = 'rgba(255, 255, 255, 0.8)';
            noItemsDiv.style.fontStyle = 'italic';
            noItemsDiv.textContent = 'No items detected in the image.';
            contentDiv.appendChild(noItemsDiv);
        }

        messageDiv.appendChild(contentDiv);
        this.elements.chatMessages.appendChild(messageDiv);

        // Scroll to bottom
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    updateStatus(status, text) {
        this.elements.statusIndicator.className = `status-indicator ${status}`;
        this.elements.statusText.textContent = text;
    }

    showLoading(text = 'Processing...') {
        this.elements.loadingOverlay.querySelector('.loading-text').textContent = text;
        this.elements.loadingOverlay.classList.add('show');
    }

    hideLoading() {
        this.elements.loadingOverlay.classList.remove('show');
    }

    showError(message) {
        this.elements.errorMessage.textContent = message;
        this.elements.errorToast.classList.add('show');
    }

    hideError() {
        this.elements.errorToast.classList.remove('show');
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.binBot = new BinBotUI();
});

// Handle page unload to clean up session
window.addEventListener('beforeunload', () => {
    if (window.binBot && window.binBot.sessionId) {
        // Send session cleanup request (fire and forget)
        navigator.sendBeacon(`${window.location.origin}/api/session/${window.binBot.sessionId}`, 
            JSON.stringify({ method: 'DELETE' }));
    }
});
