// Language switching functionality
function setLanguage(language) {
    fetch(`/api/language/${language}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error setting language:', error);
    });
}

// Toast notification system
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// File upload drag and drop
function initializeFileUpload() {
    const fileInput = document.querySelector('input[type="file"]');
    if (!fileInput) return;
    
    const dropArea = fileInput.closest('.card-body') || fileInput.parentElement;
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    dropArea.addEventListener('drop', handleDrop, false);
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight(e) {
        dropArea.classList.add('border-primary', 'bg-light');
    }
    
    function unhighlight(e) {
        dropArea.classList.remove('border-primary', 'bg-light');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            // Trigger change event
            const event = new Event('change', { bubbles: true });
            fileInput.dispatchEvent(event);
        }
    }
}

// Chat functionality
class ChatManager {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.chatContainer = document.getElementById('chat-messages');
        this.messageForm = document.getElementById('chat-form');
        this.messageInput = document.getElementById('message-input');
        this.voiceButton = document.getElementById('voice-button');
        this.isRecording = false;
        this.mediaRecorder = null;
        
        console.log("ChatManager initialized with elements:", {
            chatContainer: this.chatContainer ? "Found" : "Not found",
            messageForm: this.messageForm ? "Found" : "Not found",
            messageInput: this.messageInput ? "Found" : "Not found",
            voiceButton: this.voiceButton ? "Found" : "Not found"
        });
        
        this.initializeChat();
    }
    
    initializeChat() {
        if (this.messageForm) {
            this.messageForm.addEventListener('submit', (e) => this.sendMessage(e));
        }
        
        if (this.voiceButton) {
            this.voiceButton.addEventListener('click', () => this.toggleVoiceRecording());
        }
        
        // Auto-scroll chat to bottom
        this.scrollToBottom();
    }
    
    async sendMessage(e) {
        e.preventDefault();
        
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Show loading indicator
        const sendButton = document.getElementById('send-button');
        const originalText = sendButton.innerHTML;
        sendButton.disabled = true;
        sendButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Sending...';
        
        // Add user message to UI immediately
        this.addMessageToUI(message, true);
        this.messageInput.value = '';
        this.scrollToBottom();
        
        try {
            console.log("Sending message:", message, "Session ID:", this.sessionId);
            
            const requestBody = {
                session_id: this.sessionId,
                message: message
            };
            console.log("Request body:", JSON.stringify(requestBody));
            
            const response = await fetch('/api/chat/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrf_token]').value
                },
                body: JSON.stringify(requestBody)
            });
            
            console.log("Response status:", response.status);
            const data = await response.json();
            console.log("Response data:", data);
            
            if (response.ok && data.assistant_message) {
                // Add assistant response
                this.addMessageToUI(data.assistant_message.content, false);
                this.scrollToBottom();
            } else {
                this.showError(data.error || 'Failed to send message. Please try again.');
                console.error("Error in chat response:", data);
            }
            
            // Reset button state
            sendButton.disabled = false;
            sendButton.innerHTML = originalText;
        } catch (error) {
            console.error("Chat error:", error);
            this.showError('Network error. Please try again.');
        }
    }
    
    async toggleVoiceRecording() {
        if (!this.isRecording) {
            await this.startRecording();
        } else {
            this.stopRecording();
        }
    }
    
    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = () => {
                this.sendVoiceMessage();
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            
            // Update UI
            this.voiceButton.innerHTML = '<i class="fas fa-stop"></i> Stop Recording';
            this.voiceButton.classList.remove('btn-outline-primary');
            this.voiceButton.classList.add('btn-danger');
            
        } catch (error) {
            this.showError('Microphone access denied or not available.');
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Update UI
            this.voiceButton.innerHTML = '<i class="fas fa-microphone"></i> Voice';
            this.voiceButton.classList.remove('btn-danger');
            this.voiceButton.classList.add('btn-outline-primary');
            
            // Stop all tracks
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    }
    
    async sendVoiceMessage() {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        formData.append('session_id', this.sessionId);
        formData.append('csrf_token', document.querySelector('[name=csrf_token]').value);
        
        try {
            const response = await fetch('/api/chat/voice', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Add transcribed message
                this.addMessageToUI(data.user_message.transcription, true, 'voice');
                // Add assistant response
                this.addMessageToUI(data.assistant_message.content, false);
                this.scrollToBottom();
            } else {
                this.showError(data.error || 'Failed to process voice message');
            }
        } catch (error) {
            console.error("Chat send error:", error);
            this.showError('Network error. Please try again.');
            
            // Reset button state
            sendButton.disabled = false;
            sendButton.innerHTML = originalText;
        }
    }
    
    addMessageToUI(content, isUser, type = 'text') {
        if (!this.chatContainer) {
            console.error("Chat container not found");
            return;
        }

        console.log("Adding message to UI:", { content, isUser, type });
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `d-flex mb-3 ${isUser ? 'justify-content-end' : 'justify-content-start'}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = `p-3 rounded ${isUser ? 'bg-primary text-white' : 'bg-light text-dark'}`;
        messageContent.style.maxWidth = '70%';
        
        if (type === 'voice' && isUser) {
            messageContent.innerHTML = `
                <small><i class="fas fa-microphone me-1"></i>Voice Message</small><br>
                ${content}
            `;
        } else {
            // Use innerHTML instead of textContent to preserve line breaks
            messageContent.innerHTML = content.replace(/\n/g, '<br>');
        }
        
        const timeEl = document.createElement('small');
        timeEl.className = 'opacity-75 d-block mt-1';
        timeEl.innerHTML = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        messageContent.appendChild(document.createElement('br'));
        messageContent.appendChild(timeEl);
        
        messageDiv.appendChild(messageContent);
        this.chatContainer.appendChild(messageDiv);
    }
    
    scrollToBottom() {
        if (this.chatContainer) {
            this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
        }
    }
    
    showError(message) {
        showToast(message, 'danger');
    }
}

// Excel file viewer
class ExcelViewer {
    constructor(fileId) {
        this.fileId = fileId;
        this.currentSheet = null;
        this.currentPage = 1;
        this.perPage = 100;
        
        this.initializeViewer();
    }
    
    initializeViewer() {
        this.loadFileData();
        
        // Sheet navigation
        document.querySelectorAll('.sheet-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchSheet(tab.dataset.sheet);
            });
        });
        
        // Pagination
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('page-btn')) {
                e.preventDefault();
                this.currentPage = parseInt(e.target.dataset.page);
                this.loadFileData();
            }
        });
    }
    
    async loadFileData(sheet = null) {
        const params = new URLSearchParams({
            page: this.currentPage,
            per_page: this.perPage
        });
        
        if (sheet) {
            params.append('sheet', sheet);
            this.currentSheet = sheet;
        }
        
        try {
            const response = await fetch(`/api/files/${this.fileId}/data?${params}`);
            const data = await response.json();
            
            if (response.ok) {
                this.renderTable(data);
                this.renderPagination(data);
            } else {
                this.showError(data.error || 'Failed to load file data');
            }
        } catch (error) {
            this.showError('Network error loading file data.');
        }
    }
    
    renderTable(data) {
        const tableContainer = document.getElementById('excel-table');
        if (!tableContainer) return;
        
        let html = '<div class="table-responsive"><table class="table table-sm table-striped">';
        
        // Header
        html += '<thead class="table-dark"><tr>';
        data.columns.forEach(col => {
            html += `<th>${col}</th>`;
        });
        html += '</tr></thead>';
        
        // Body
        html += '<tbody>';
        data.data.forEach(row => {
            html += '<tr>';
            data.columns.forEach(col => {
                html += `<td>${row[col] || ''}</td>`;
            });
            html += '</tr>';
        });
        html += '</tbody></table></div>';
        
        tableContainer.innerHTML = html;
    }
    
    renderPagination(data) {
        const paginationContainer = document.getElementById('pagination');
        if (!paginationContainer) return;
        
        const totalPages = Math.ceil(data.total_rows / this.perPage);
        
        let html = '<nav><ul class="pagination justify-content-center">';
        
        // Previous
        html += `<li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                    <a class="page-link page-btn" data-page="${this.currentPage - 1}">Previous</a>
                 </li>`;
        
        // Pages
        for (let i = Math.max(1, this.currentPage - 2); i <= Math.min(totalPages, this.currentPage + 2); i++) {
            html += `<li class="page-item ${i === this.currentPage ? 'active' : ''}">
                        <a class="page-link page-btn" data-page="${i}">${i}</a>
                     </li>`;
        }
        
        // Next
        html += `<li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
                    <a class="page-link page-btn" data-page="${this.currentPage + 1}">Next</a>
                 </li>`;
        
        html += '</ul></nav>';
        
        paginationContainer.innerHTML = html;
    }
    
    switchSheet(sheetName) {
        this.currentPage = 1;
        this.loadFileData(sheetName);
        
        // Update active tab
        document.querySelectorAll('.sheet-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-sheet="${sheetName}"]`).classList.add('active');
    }
    
    showError(message) {
        showToast(message, 'danger');
    }
}

// Initialize components when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize file upload drag and drop
    initializeFileUpload();
    
    // Initialize chat if on chat page
    const chatContainer = document.getElementById('chat-messages');
    if (chatContainer) {
        const sessionId = document.querySelector('[name="session_id"]')?.value;
        if (sessionId) {
            new ChatManager(sessionId);
        }
    }
    
    // Initialize Excel viewer if on file view page
    const excelTable = document.getElementById('excel-table');
    if (excelTable) {
        const fileId = document.querySelector('[data-file-id]')?.dataset.fileId;
        if (fileId) {
            new ExcelViewer(fileId);
        }
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Auto-logout on token expiration
function checkAuthStatus() {
    fetch('/api/auth/status', {
        method: 'GET',
        credentials: 'same-origin'
    })
    .then(response => {
        if (response.status === 401) {
            showToast('Session expired. Please log in again.', 'warning');
            setTimeout(() => {
                window.location.href = '/auth/login';
            }, 2000);
        }
    })
    .catch(error => {
        // Ignore network errors for auth check
    });
}

// Check auth status every 5 minutes
setInterval(checkAuthStatus, 5 * 60 * 1000);
