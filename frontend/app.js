/**
 * BinBot Frontend Application
 * Handles session management, chat interface, and bin contents display
 */

/**
 * Camera Manager - Handles camera access, permissions, and capture
 */
class CameraManager {
    constructor() {
        this.stream = null;
        this.hasPermission = false;
        this.isSupported = this.checkSupport();
        this.devices = [];
        this.currentDeviceId = null;
    }

    /**
     * Check if camera APIs are supported
     */
    checkSupport() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    }

    /**
     * Request camera permission and get available devices
     */
    async requestPermission() {
        if (!this.isSupported) {
            throw new Error('Camera is not supported in this browser');
        }

        try {
            // Request basic camera permission
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false
            });

            this.hasPermission = true;

            // Stop the permission test stream
            stream.getTracks().forEach(track => track.stop());

            // Get available camera devices
            await this.getDevices();

            return true;
        } catch (error) {
            this.hasPermission = false;
            throw this.handlePermissionError(error);
        }
    }

    /**
     * Get available camera devices
     */
    async getDevices() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            this.devices = devices.filter(device => device.kind === 'videoinput');

            // Set default device (prefer back camera on mobile)
            if (this.devices.length > 0 && !this.currentDeviceId) {
                const backCamera = this.devices.find(device =>
                    device.label.toLowerCase().includes('back') ||
                    device.label.toLowerCase().includes('rear')
                );
                this.currentDeviceId = backCamera ? backCamera.deviceId : this.devices[0].deviceId;
            }

            return this.devices;
        } catch (error) {
            console.error('Error getting camera devices:', error);
            return [];
        }
    }

    /**
     * Start camera stream
     */
    async startStream(deviceId = null) {
        if (!this.hasPermission) {
            await this.requestPermission();
        }

        try {
            const constraints = {
                video: {
                    deviceId: deviceId || this.currentDeviceId ?
                        { exact: deviceId || this.currentDeviceId } : true,
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                },
                audio: false
            };

            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            return this.stream;
        } catch (error) {
            throw this.handleStreamError(error);
        }
    }

    /**
     * Stop camera stream
     */
    stopStream() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }

    /**
     * Switch to different camera device
     */
    async switchDevice(deviceId) {
        this.stopStream();
        this.currentDeviceId = deviceId;
        return await this.startStream(deviceId);
    }

    /**
     * Handle permission errors
     */
    handlePermissionError(error) {
        switch (error.name) {
            case 'NotAllowedError':
                return new Error('Camera access denied. Please allow camera access and try again.');
            case 'NotFoundError':
                return new Error('No camera found on this device.');
            case 'NotSupportedError':
                return new Error('Camera is not supported in this browser.');
            case 'NotReadableError':
                return new Error('Camera is already in use by another application.');
            default:
                return new Error(`Camera error: ${error.message}`);
        }
    }

    /**
     * Handle stream errors
     */
    handleStreamError(error) {
        switch (error.name) {
            case 'OverconstrainedError':
                return new Error('Camera constraints could not be satisfied.');
            case 'NotReadableError':
                return new Error('Camera is already in use.');
            default:
                return this.handlePermissionError(error);
        }
    }

    /**
     * Get permission status
     */
    async getPermissionStatus() {
        if (!navigator.permissions) {
            return 'unknown';
        }

        try {
            const permission = await navigator.permissions.query({ name: 'camera' });
            return permission.state; // 'granted', 'denied', or 'prompt'
        } catch (error) {
            return 'unknown';
        }
    }
}

/**
 * Voice Manager - Handles microphone access and speech recognition
 */
class VoiceManager {
    constructor() {
        this.recognition = null;
        this.hasPermission = false;
        this.isSupported = this.checkSupport();
        this.isListening = false;
        this.currentLanguage = 'en-US';
        this.currentTranscript = '';
        this.finalTranscript = '';
        this.onResult = null;
        this.onFinalResult = null;
        this.onError = null;
    }

    /**
     * Check if voice APIs are supported
     */
    checkSupport() {
        const hasMediaDevices = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
        const hasSpeechRecognition = !!(window.SpeechRecognition || window.webkitSpeechRecognition);
        return hasMediaDevices && hasSpeechRecognition;
    }

    /**
     * Get permission status
     */
    async getPermissionStatus() {
        if (!navigator.permissions) {
            return 'unknown';
        }

        try {
            const permission = await navigator.permissions.query({ name: 'microphone' });
            return permission.state; // 'granted', 'denied', or 'prompt'
        } catch (error) {
            return 'unknown';
        }
    }

    /**
     * Request microphone permission
     */
    async requestPermission() {
        if (!this.isSupported) {
            throw new Error('Voice input is not supported in this browser');
        }

        try {
            // Request basic microphone permission
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: true,
                video: false
            });

            this.hasPermission = true;

            // Stop the permission test stream
            stream.getTracks().forEach(track => track.stop());

            return true;
        } catch (error) {
            this.hasPermission = false;
            console.error('Voice permission error:', error);
            throw new Error('Microphone access denied');
        }
    }

    /**
     * Initialize speech recognition
     */
    initializeSpeechRecognition() {
        if (!this.isSupported) {
            throw new Error('Speech recognition is not supported');
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();

        // Configure for conversational input
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = this.currentLanguage;
        this.recognition.maxAlternatives = 1;

        // Set up event handlers for conversational flow
        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }

            this.currentTranscript = interimTranscript;
            this.finalTranscript += finalTranscript;

            // Call result callback if set
            if (this.onResult) {
                this.onResult(this.finalTranscript + this.currentTranscript);
            }

            // If we have final results, trigger the final callback
            if (finalTranscript && this.onFinalResult) {
                this.onFinalResult(this.finalTranscript.trim());
            }
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            if (this.onError) {
                this.onError(event.error);
            }
        };

        this.recognition.onend = () => {
            this.isListening = false;
        };

        return this.recognition;
    }

    /**
     * Start listening for speech
     */
    async startListening() {
        if (!this.hasPermission) {
            await this.requestPermission();
        }

        if (!this.recognition) {
            this.initializeSpeechRecognition();
        }

        this.isListening = true;
        this.recognition.start();
    }

    /**
     * Stop listening for speech
     */
    stopListening() {
        if (this.recognition && this.isListening) {
            this.isListening = false;
            this.recognition.stop();
        }
    }

    /**
     * Reset transcript for new conversation
     */
    resetTranscript() {
        this.currentTranscript = '';
        this.finalTranscript = '';
    }

    /**
     * Set up conversational callbacks
     */
    setCallbacks(onResult, onFinalResult, onError) {
        this.onResult = onResult;
        this.onFinalResult = onFinalResult;
        this.onError = onError;
    }
}

class BinBotUI {
    constructor() {
        this.sessionId = null;
        this.currentBin = null;
        this.apiBase = window.location.origin;

        // Initialize camera manager
        this.cameraManager = new CameraManager();

        // Initialize voice manager
        this.voiceManager = new VoiceManager();

        // DOM elements
        this.elements = {
            messageInput: document.getElementById('messageInput'),
            sendBtn: document.getElementById('sendBtn'),
            cameraBtn: document.getElementById('cameraBtn'),
            voiceBtn: document.getElementById('voiceBtn'),
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
            this.handleCameraClick();
        });

        // Voice button for voice input
        this.elements.voiceBtn.addEventListener('click', () => {
            this.handleVoiceClick();
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
            if (data.current_bin) {
                // Handle bin change (including null -> bin case)
                if (data.current_bin !== this.currentBin) {
                    console.log(`🎯 Bin changed: ${this.currentBin} → ${data.current_bin}`);
                    this.currentBin = data.current_bin;
                    await this.refreshBinContents(data.current_bin);
                } else {
                    // Refresh current bin contents even if bin didn't change (items may have been added/removed)
                    await this.refreshBinContents(data.current_bin);
                }
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
    /**
     * Handle camera button click - default to camera capture with fallback options
     */
    async handleCameraClick() {
        // Check if camera is supported
        if (!this.cameraManager.isSupported) {
            // No camera support - go directly to file upload
            this.elements.imageInput.click();
            return;
        }

        // Check current permission status
        const permissionStatus = await this.cameraManager.getPermissionStatus();

        if (permissionStatus === 'denied') {
            this.showCameraPermissionDenied();
            return;
        }

        // Default to camera capture - try to open camera directly
        try {
            await this.openCameraCapture();
        } catch (error) {
            // If camera fails, show fallback options
            console.warn('Camera failed to open, showing fallback options:', error);
            this.showCameraFallbackOptions(error.message);
        }
    }

    /**
     * Show camera options modal
     */
    showCameraOptions(options) {
        const modal = document.createElement('div');
        modal.className = 'camera-modal';
        modal.innerHTML = `
            <div class="camera-modal-content">
                <div class="camera-modal-header">
                    <h3>📷 Add Image</h3>
                    <button class="camera-modal-close">&times;</button>
                </div>
                <div class="camera-modal-body">
                    ${options.includes('file') ? `
                        <button class="camera-option-btn" data-action="file">
                            📁 Choose from Files
                        </button>
                    ` : ''}
                    ${options.includes('camera') ? `
                        <button class="camera-option-btn" data-action="camera">
                            📷 Take Photo
                        </button>
                    ` : ''}
                </div>
            </div>
        `;

        // Add event listeners
        modal.querySelector('.camera-modal-close').addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });

        modal.querySelectorAll('.camera-option-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.dataset.action;
                document.body.removeChild(modal);

                if (action === 'file') {
                    this.elements.imageInput.click();
                } else if (action === 'camera') {
                    this.openCameraCapture();
                }
            });
        });

        document.body.appendChild(modal);
    }

    /**
     * Show camera permission denied message
     */
    showCameraPermissionDenied() {
        const modal = document.createElement('div');
        modal.className = 'camera-modal';
        modal.innerHTML = `
            <div class="camera-modal-content">
                <div class="camera-modal-header">
                    <h3>📷 Camera Access</h3>
                    <button class="camera-modal-close">&times;</button>
                </div>
                <div class="camera-modal-body">
                    <p>Camera access has been denied. To use the camera:</p>
                    <ol>
                        <li>Click the camera icon in your browser's address bar</li>
                        <li>Select "Allow" for camera access</li>
                        <li>Refresh the page</li>
                    </ol>
                    <p>Or you can still upload images from your files:</p>
                    <button class="camera-option-btn" data-action="file">
                        📁 Choose from Files
                    </button>
                </div>
            </div>
        `;

        // Add event listeners
        modal.querySelector('.camera-modal-close').addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });

        const fileBtn = modal.querySelector('[data-action="file"]');
        if (fileBtn) {
            fileBtn.addEventListener('click', () => {
                document.body.removeChild(modal);
                this.elements.imageInput.click();
            });
        }

        document.body.appendChild(modal);
    }

    /**
     * Show fallback options when camera fails to open
     */
    showCameraFallbackOptions(errorMessage) {
        const modal = document.createElement('div');
        modal.className = 'camera-modal';
        modal.innerHTML = `
            <div class="camera-modal-content">
                <div class="camera-modal-header">
                    <h3>📷 Camera Unavailable</h3>
                    <button class="camera-modal-close">&times;</button>
                </div>
                <div class="camera-modal-body">
                    <p><strong>Camera Error:</strong> ${errorMessage}</p>
                    <p>You can still add images by uploading from your files:</p>
                    <button class="camera-option-btn" data-action="file">
                        📁 Choose from Files
                    </button>
                    <p style="margin-top: 1rem; font-size: 0.8125rem; color: #6b7280;">
                        To use the camera, try refreshing the page or check your camera permissions.
                    </p>
                </div>
            </div>
        `;

        // Add event listeners
        modal.querySelector('.camera-modal-close').addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });

        const fileBtn = modal.querySelector('[data-action="file"]');
        fileBtn.addEventListener('click', () => {
            document.body.removeChild(modal);
            this.elements.imageInput.click();
        });

        document.body.appendChild(modal);
    }

    /**
     * Open camera capture interface with live preview
     */
    async openCameraCapture() {
        try {
            this.showLoading('Starting camera...');

            // Request permission and start camera stream
            const stream = await this.cameraManager.startStream();
            this.hideLoading();

            // Create and show camera preview modal
            this.showCameraPreview(stream);

        } catch (error) {
            this.hideLoading();
            this.showError(error.message);
        }
    }

    /**
     * Show camera preview modal with live video feed
     */
    showCameraPreview(stream) {
        const modal = document.createElement('div');
        modal.className = 'camera-preview-modal';
        modal.innerHTML = `
            <div class="camera-preview-content">
                <div class="camera-preview-header">
                    <div class="camera-header-content">
                        <h3>📷 Take Photo</h3>
                        <p class="camera-subtitle">Position your items and click capture</p>
                    </div>
                    <button class="camera-preview-close">&times;</button>
                </div>
                <div class="camera-preview-body">
                    <div class="camera-video-container">
                        <video id="cameraPreview" autoplay playsinline muted></video>
                        <div class="camera-overlay">
                            <div class="camera-frame"></div>
                        </div>
                    </div>
                    <div class="camera-controls">
                        <div class="camera-device-selector" style="display: none;">
                            <select id="cameraDeviceSelect">
                                <option value="">Select Camera</option>
                            </select>
                        </div>
                        <div class="camera-actions">
                            <button class="camera-action-btn camera-switch-btn" id="cameraSwitchBtn" title="Switch Camera">
                                🔄
                            </button>
                            <button class="camera-action-btn camera-capture-btn" id="cameraCaptureBtn" title="Take Photo">
                                📷
                            </button>
                            <button class="camera-action-btn camera-file-btn" id="cameraFileBtn" title="Choose File Instead">
                                📁
                            </button>
                            <button class="camera-action-btn camera-cancel-btn" id="cameraCancelBtn" title="Cancel">
                                ❌
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Get video element and set stream
        const video = modal.querySelector('#cameraPreview');
        video.srcObject = stream;

        // Populate device selector if multiple cameras available
        this.populateCameraDeviceSelector(modal);

        // Add event listeners
        this.setupCameraPreviewEventListeners(modal, video);

        // Add to DOM
        document.body.appendChild(modal);

        // Focus on capture button for keyboard accessibility
        modal.querySelector('#cameraCaptureBtn').focus();
    }

    /**
     * Populate camera device selector dropdown
     */
    async populateCameraDeviceSelector(modal) {
        const deviceSelect = modal.querySelector('#cameraDeviceSelect');
        const deviceContainer = modal.querySelector('.camera-device-selector');

        if (this.cameraManager.devices.length > 1) {
            // Show device selector if multiple cameras available
            deviceContainer.style.display = 'block';

            // Clear existing options except the first one
            deviceSelect.innerHTML = '<option value="">Select Camera</option>';

            // Add device options
            this.cameraManager.devices.forEach(device => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.textContent = device.label || `Camera ${device.deviceId.substring(0, 8)}...`;
                option.selected = device.deviceId === this.cameraManager.currentDeviceId;
                deviceSelect.appendChild(option);
            });
        }
    }

    /**
     * Setup event listeners for camera preview modal
     */
    setupCameraPreviewEventListeners(modal, video) {
        const closeBtn = modal.querySelector('.camera-preview-close');
        const cancelBtn = modal.querySelector('#cameraCancelBtn');
        const captureBtn = modal.querySelector('#cameraCaptureBtn');
        const switchBtn = modal.querySelector('#cameraSwitchBtn');
        const fileBtn = modal.querySelector('#cameraFileBtn');
        const deviceSelect = modal.querySelector('#cameraDeviceSelect');

        // Close modal function
        const closeModal = () => {
            this.cameraManager.stopStream();
            document.body.removeChild(modal);
        };

        // Close button events
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);

        // Click outside to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });

        // Keyboard events
        modal.addEventListener('keydown', (e) => {
            switch (e.key) {
                case 'Escape':
                    closeModal();
                    break;
                case 'Enter':
                case ' ':
                    if (e.target === captureBtn) {
                        e.preventDefault();
                        this.capturePhoto(video, modal);
                    }
                    break;
            }
        });

        // Capture photo
        captureBtn.addEventListener('click', () => {
            this.capturePhoto(video, modal);
        });

        // Choose file instead of camera
        fileBtn.addEventListener('click', () => {
            closeModal();
            this.elements.imageInput.click();
        });

        // Switch camera (for mobile devices with front/back cameras)
        switchBtn.addEventListener('click', async () => {
            await this.switchCamera(modal, video);
        });

        // Device selector change
        deviceSelect.addEventListener('change', async (e) => {
            if (e.target.value) {
                await this.switchToDevice(e.target.value, modal, video);
            }
        });

        // Hide switch button if only one camera
        if (this.cameraManager.devices.length <= 1) {
            switchBtn.style.display = 'none';
        }
    }
    /**
     * Capture photo from video stream
     */
    async capturePhoto(video, modal) {
        try {
            // Create canvas to capture frame
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');

            // Set canvas dimensions to match video
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;

            // Draw current video frame to canvas
            context.drawImage(video, 0, 0, canvas.width, canvas.height);

            // Convert canvas to blob with high quality JPEG
            canvas.toBlob(async (blob) => {
                if (blob) {
                    // Create file from blob
                    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                    const file = new File([blob], `camera-capture-${timestamp}.jpg`, {
                        type: 'image/jpeg',
                        lastModified: Date.now()
                    });

                    // Close camera modal
                    this.cameraManager.stopStream();
                    document.body.removeChild(modal);

                    // Process the captured image
                    await this.handleImageUpload(file);
                } else {
                    this.showError('Failed to capture photo. Please try again.');
                }
            }, 'image/jpeg', 0.9);

        } catch (error) {
            console.error('Photo capture error:', error);
            this.showError('Failed to capture photo. Please try again.');
        }
    }

    /**
     * Switch to next available camera
     */
    async switchCamera(modal, video) {
        try {
            const currentIndex = this.cameraManager.devices.findIndex(
                device => device.deviceId === this.cameraManager.currentDeviceId
            );

            const nextIndex = (currentIndex + 1) % this.cameraManager.devices.length;
            const nextDevice = this.cameraManager.devices[nextIndex];

            await this.switchToDevice(nextDevice.deviceId, modal, video);

        } catch (error) {
            console.error('Camera switch error:', error);
            this.showError('Failed to switch camera. Please try again.');
        }
    }

    /**
     * Switch to specific camera device
     */
    async switchToDevice(deviceId, modal, video) {
        try {
            // Show loading state
            const captureBtn = modal.querySelector('#cameraCaptureBtn');
            const switchBtn = modal.querySelector('#cameraSwitchBtn');

            captureBtn.disabled = true;
            switchBtn.disabled = true;

            // Switch camera stream
            const newStream = await this.cameraManager.switchDevice(deviceId);
            video.srcObject = newStream;

            // Update device selector
            const deviceSelect = modal.querySelector('#cameraDeviceSelect');
            deviceSelect.value = deviceId;

            // Re-enable controls
            captureBtn.disabled = false;
            switchBtn.disabled = false;

        } catch (error) {
            console.error('Device switch error:', error);
            this.showError('Failed to switch to selected camera.');

            // Re-enable controls
            const captureBtn = modal.querySelector('#cameraCaptureBtn');
            const switchBtn = modal.querySelector('#cameraSwitchBtn');
            captureBtn.disabled = false;
            switchBtn.disabled = false;
        }
    }
    /**
     * Handle voice button click - toggle voice input on/off
     */
    async handleVoiceClick() {
        if (!this.voiceManager.isSupported) {
            this.showError('Voice input is not supported in this browser');
            return;
        }

        if (this.voiceManager.isListening) {
            // Stop listening
            this.stopVoiceInput();
        } else {
            // Start listening
            await this.startVoiceInput();
        }
    }

    /**
     * Start voice input and set up conversational flow
     */
    async startVoiceInput() {
        try {
            // Set up callbacks for conversational flow
            this.voiceManager.setCallbacks(
                (transcript) => {
                    // Update input field with current transcript
                    this.elements.messageInput.value = transcript;
                },
                (finalTranscript) => {
                    // Send final transcript to chat
                    if (finalTranscript.trim()) {
                        this.elements.messageInput.value = finalTranscript.trim();
                        this.handleSendMessage();
                        this.voiceManager.resetTranscript();
                    }
                },
                (error) => {
                    console.error('Voice recognition error:', error);
                    this.showError('Voice recognition failed. Please try again.');
                    this.stopVoiceInput();
                }
            );

            // Start listening
            await this.voiceManager.startListening();

            // Update UI
            this.elements.voiceBtn.classList.add('listening');
            this.elements.voiceBtn.title = 'Stop Voice Input';

        } catch (error) {
            console.error('Failed to start voice input:', error);
            this.showError(error.message);
        }
    }

    /**
     * Stop voice input
     */
    stopVoiceInput() {
        this.voiceManager.stopListening();

        // Update UI
        this.elements.voiceBtn.classList.remove('listening');
        this.elements.voiceBtn.title = 'Voice Input';

        // Clear any partial transcript
        if (!this.elements.messageInput.value.trim()) {
            this.elements.messageInput.value = '';
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
