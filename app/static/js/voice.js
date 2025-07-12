/**
 * Voice Recording Functionality
 * This file handles recording audio from the user's microphone,
 * sending it to the server for processing, and displaying the response.
 */

let mediaRecorder;
let audioChunks = [];
let isRecording = false;

// Debug logging function
function logVoiceDebug(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}`;
    console.log(`[Voice Debug] ${logMessage}`);
    
    // Also send logs to server for debugging
    try {
        fetch('/api/debug_log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                source: 'voice_js', 
                message: logMessage,
                userAgent: navigator.userAgent,
                timestamp: timestamp
            })
        }).catch(e => console.error('Failed to send debug log:', e));
    } catch (e) {
        console.error('Error sending debug log:', e);
    }
}

// Check if browser supports audio recording
function browserSupportsAudio() {
    const isSupported = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    logVoiceDebug(`Browser audio support: ${isSupported}`);
    return isSupported;
}

// Initialize voice recording functionality
function initVoiceRecording() {
    logVoiceDebug('Initializing voice recording functionality');
    const voiceButton = document.getElementById('voice-button');
    if (!voiceButton) {
        logVoiceDebug('Voice button not found in DOM');
        return;
    }
    
    if (!browserSupportsAudio()) {
        logVoiceDebug('Browser does not support audio recording');
        voiceButton.disabled = true;
        voiceButton.title = 'Ваш браузер не поддерживает запись аудио';
        return;
    }
    
    logVoiceDebug('Adding click event listener to voice button');
    // Change to click event for modal
    voiceButton.addEventListener('click', function() {
        logVoiceDebug('Voice button clicked');
        showVoiceModal();
    });
    
    // Set up modal buttons
    const startRecButton = document.getElementById('start-recording');
    if (startRecButton) {
        logVoiceDebug('Adding click event listener to start recording button');
        startRecButton.addEventListener('click', startRecording);
    } else {
        logVoiceDebug('Start recording button not found');
    }
    
    const stopRecButton = document.getElementById('stop-recording');
    if (stopRecButton) {
        logVoiceDebug('Adding click event listener to stop recording button');
        stopRecButton.addEventListener('click', stopRecording);
    } else {
        logVoiceDebug('Stop recording button not found');
    }
}

// Show voice recording modal
function showVoiceModal() {
    logVoiceDebug('Showing voice modal');
    // Create modal if it doesn't exist
    if (!document.getElementById('voice-modal')) {
        logVoiceDebug('Voice modal not found, creating it');
        createVoiceModal();
    }
    
    // Show the modal
    try {
        const modalElement = document.getElementById('voice-modal');
        if (!modalElement) {
            logVoiceDebug('Error: Modal element not found after creation');
            return;
        }
        
        const voiceModal = new bootstrap.Modal(modalElement);
        logVoiceDebug('Displaying voice modal');
        voiceModal.show();
    } catch (error) {
        logVoiceDebug(`Error showing modal: ${error.message}`);
        console.error('Error showing voice modal:', error);
    }
}

// Create voice recording modal
function createVoiceModal() {
    logVoiceDebug('Creating voice modal');
    const modalHTML = `
    <div class="modal fade" id="voice-modal" tabindex="-1" aria-labelledby="voiceModalLabel" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="voiceModalLabel">Голосовое сообщение</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body text-center">
            <div id="voice-status" class="mb-3">Нажмите кнопку для начала записи</div>
            <div id="recording-time" class="display-4 mb-3">00:00</div>
            <div id="recording-animation" class="mb-3 d-none">
              <div class="spinner-grow text-danger" role="status">
                <span class="visually-hidden">Запись...</span>
              </div>
            </div>
          </div>
          <div class="modal-footer justify-content-center">
            <button type="button" id="start-recording" class="btn btn-primary">
              <i class="fas fa-microphone"></i> Начать запись
            </button>
            <button type="button" id="stop-recording" class="btn btn-danger d-none">
              <i class="fas fa-stop"></i> Остановить запись
            </button>
          </div>
        </div>
      </div>
    </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

// Start recording audio
function startRecording() {
    logVoiceDebug('Start recording function called');
    
    if (isRecording) {
        logVoiceDebug('Already recording, ignoring start request');
        return;
    }
    
    const containerElement = document.querySelector('.container');
    if (!containerElement) {
        logVoiceDebug('Container element not found');
        showToast('Ошибка: Контейнер не найден', 'danger');
        return;
    }
    
    const sessionId = containerElement.getAttribute('data-session-id');
    logVoiceDebug(`Session ID found: ${sessionId}`);
    
    const startRecButton = document.getElementById('start-recording');
    const stopRecButton = document.getElementById('stop-recording');
    const voiceStatus = document.getElementById('voice-status');
    const recordingAnimation = document.getElementById('recording-animation');
    
    if (!sessionId) {
        logVoiceDebug('No session ID found');
        showToast('Ошибка: Сессия чата не найдена', 'danger');
        return;
    }
    
    logVoiceDebug('Requesting microphone access');
    // Check if user already gave microphone permissions
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            logVoiceDebug('Microphone access granted');
            isRecording = true;
            audioChunks = [];
            
            // Update UI
            if (startRecButton) {
                startRecButton.classList.add('d-none');
                logVoiceDebug('Start button hidden');
            }
            if (stopRecButton) {
                stopRecButton.classList.remove('d-none');
                logVoiceDebug('Stop button shown');
            }
            if (voiceStatus) {
                voiceStatus.innerText = 'Запись голосового сообщения...';
                logVoiceDebug('Status updated to recording');
            }
            if (recordingAnimation) {
                recordingAnimation.classList.remove('d-none');
                logVoiceDebug('Animation shown');
            }
            
            // Start recording time counter
            startRecordingTimer();
            logVoiceDebug('Recording timer started');
            
            // Create media recorder
            logVoiceDebug('Creating MediaRecorder');
            try {
                mediaRecorder = new MediaRecorder(stream);
                
                mediaRecorder.addEventListener('dataavailable', event => {
                    logVoiceDebug(`Data available event received, size: ${event.data.size}`);
                    audioChunks.push(event.data);
                });
                
                logVoiceDebug('Starting media recorder');
                mediaRecorder.start();
                logVoiceDebug('Media recorder started successfully');
            } catch (error) {
                logVoiceDebug(`Error creating MediaRecorder: ${error.message}`);
                console.error('MediaRecorder error:', error);
                if (voiceStatus) voiceStatus.innerText = 'Ошибка создания MediaRecorder';
            }
        })
        .catch(error => {
            logVoiceDebug(`Microphone access error: ${error.message}`);
            console.error('Error accessing microphone:', error);
            if (voiceStatus) voiceStatus.innerText = 'Не удалось получить доступ к микрофону';
            showToast('Не удалось получить доступ к микрофону', 'danger');
        });
}

// Recording timer variables
let recordingInterval = null;
let recordingSeconds = 0;

// Start recording timer
function startRecordingTimer() {
    recordingSeconds = 0;
    updateRecordingTime();
    recordingInterval = setInterval(() => {
        recordingSeconds++;
        updateRecordingTime();
    }, 1000);
}

// Update recording time display
function updateRecordingTime() {
    const recordingTime = document.getElementById('recording-time');
    if (recordingTime) {
        const minutes = Math.floor(recordingSeconds / 60);
        const seconds = recordingSeconds % 60;
        recordingTime.innerText = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
}

// Stop recording and send audio to server
function stopRecording() {
    logVoiceDebug('Stop recording function called');
    
    if (!isRecording) {
        logVoiceDebug('Not recording, ignoring stop request');
        return;
    }
    
    const startRecButton = document.getElementById('start-recording');
    const stopRecButton = document.getElementById('stop-recording');
    const voiceStatus = document.getElementById('voice-status');
    const recordingAnimation = document.getElementById('recording-animation');
    
    // Stop timer
    if (recordingInterval) {
        clearInterval(recordingInterval);
        recordingInterval = null;
        logVoiceDebug('Recording timer stopped');
    }
    
    // Update UI
    if (voiceStatus) {
        voiceStatus.innerText = 'Обработка записи...';
        logVoiceDebug('Status updated to processing');
    }
    if (recordingAnimation) {
        recordingAnimation.classList.add('d-none');
        logVoiceDebug('Animation hidden');
    }
    
    logVoiceDebug('Adding stop event listener to MediaRecorder');
    try {
        // Stop media recorder
        if (!mediaRecorder) {
            logVoiceDebug('Error: MediaRecorder is null');
            return;
        }
        
        mediaRecorder.addEventListener('stop', () => {
            logVoiceDebug('MediaRecorder stop event fired');
            sendAudioToServer();
        });
        
        logVoiceDebug('Stopping MediaRecorder');
        mediaRecorder.stop();
        logVoiceDebug('MediaRecorder stopped successfully');
        isRecording = false;
    } catch (error) {
        logVoiceDebug(`Error stopping MediaRecorder: ${error.message}`);
        console.error('Error stopping recording:', error);
    }
    
    // Hide modal after a short delay
    logVoiceDebug('Scheduling modal hide');
    setTimeout(() => {
        try {
            const modalElement = document.getElementById('voice-modal');
            if (!modalElement) {
                logVoiceDebug('Modal element not found for hiding');
                return;
            }
            
            const voiceModal = bootstrap.Modal.getInstance(modalElement);
            if (voiceModal) {
                voiceModal.hide();
                logVoiceDebug('Modal hidden');
            } else {
                logVoiceDebug('Modal instance not found');
            }
            
            // Reset UI for next recording
            if (startRecButton) {
                startRecButton.classList.remove('d-none');
                logVoiceDebug('Start button restored');
            }
            if (stopRecButton) {
                stopRecButton.classList.add('d-none');
                logVoiceDebug('Stop button hidden');
            }
            if (voiceStatus) {
                voiceStatus.innerText = 'Нажмите кнопку для начала записи';
                logVoiceDebug('Status reset');
            }
            
            const timeElement = document.getElementById('recording-time');
            if (timeElement) {
                timeElement.innerText = '00:00';
                logVoiceDebug('Timer reset');
            }
        } catch (error) {
            logVoiceDebug(`Error hiding modal: ${error.message}`);
            console.error('Error hiding modal:', error);
        }
    }, 1000);
}

// Send recorded audio to server
function sendAudioToServer() {
    logVoiceDebug('Send audio to server function called');
    
    const containerElement = document.querySelector('.container');
    if (!containerElement) {
        logVoiceDebug('Container element not found');
        showToast('Ошибка: Контейнер не найден', 'danger');
        return;
    }
    
    const sessionId = containerElement.getAttribute('data-session-id');
    const language = document.documentElement.lang || 'en';
    
    logVoiceDebug(`Session ID: ${sessionId}, Language: ${language}`);
    logVoiceDebug(`Audio chunks: ${audioChunks.length}, Types: ${audioChunks.map(chunk => chunk.type).join(', ')}`);
    logVoiceDebug(`Browser info: ${navigator.userAgent}`);
    
    // Create audio blob
    try {
        // Log audio chunks details
        audioChunks.forEach((chunk, index) => {
            logVoiceDebug(`Audio chunk ${index} type: ${chunk.type}, size: ${chunk.size} bytes`);
        });
        
        // Try to use codec from the first chunk if available
        let mimeType = 'audio/webm';
        if (audioChunks.length > 0 && audioChunks[0].type) {
            mimeType = audioChunks[0].type;
            logVoiceDebug(`Using mime type from first chunk: ${mimeType}`);
        } else {
            logVoiceDebug(`Using default mime type: ${mimeType}`);
        }
        
        const audioBlob = new Blob(audioChunks, { type: mimeType });
        logVoiceDebug(`Audio blob created, size: ${audioBlob.size} bytes, type: ${audioBlob.type}`);
        
        // Check if audio is too short
        if (audioBlob.size < 1000) {
            logVoiceDebug(`Audio too short (${audioBlob.size} bytes), ignoring`);
            showToast('Запись слишком короткая', 'warning');
            return;
        }
        
        // Show loading indicator
        showLoadingIndicator();
        logVoiceDebug('Loading indicator shown');
        
        // Create form data
        const formData = new FormData();
        
        // Add a random filename with correct extension based on mime type
        let extension = 'webm';
        if (mimeType.includes('ogg')) extension = 'ogg';
        else if (mimeType.includes('mp3')) extension = 'mp3';
        else if (mimeType.includes('wav')) extension = 'wav';
        
        const randomFilename = `recording_${Date.now()}.${extension}`;
        logVoiceDebug(`Generated random filename: ${randomFilename}`);
        
        formData.append('audio', audioBlob, randomFilename);
        formData.append('session_id', sessionId);
        formData.append('language', language);
        
        logVoiceDebug(`FormData created with filename: ${randomFilename}`);
        logVoiceDebug(`Sending audio to server with session ID: ${sessionId}`);
        
        // Send audio to server
        logVoiceDebug('Starting fetch request to /api/send_voice_message');
        fetch('/api/send_voice_message', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            logVoiceDebug(`Server response status: ${response.status} ${response.statusText}`);
            logVoiceDebug(`Response headers: ${JSON.stringify(Object.fromEntries([...response.headers]))}`);
            if (!response.ok) {
                logVoiceDebug(`Server returned error status: ${response.status}`);
                throw new Error(`Server responded with status: ${response.status}`);
            }
            return response.json().catch(e => {
                logVoiceDebug(`Error parsing JSON from response: ${e.message}`);
                throw new Error('Invalid JSON in response');
            });
        })
        .then(data => {
            // Hide loading indicator
            hideLoadingIndicator();
            logVoiceDebug(`Server response data received: ${JSON.stringify(data)}`);
            
            if (data.error) {
                logVoiceDebug(`Error from server: ${data.error}`);
                showToast(data.error, 'danger');
                return;
            }
            
            if (!data.transcript && !data.success) {
                logVoiceDebug('No transcript or success field in response');
                showToast('Сервер не вернул транскрипцию', 'danger');
                return;
            }
            
            // Add user message to chat
            const transcript = data.transcript || '';
            logVoiceDebug(`Transcript received: ${transcript}`);
            addMessageToChat(transcript, true, true);
            
            // Add assistant response to chat
            if (data.response) {
                logVoiceDebug(`Response received (first 100 chars): ${data.response.substring(0, 100)}...`);
                addMessageToChat(data.response, false, false);
            } else {
                logVoiceDebug('No response field in server data');
            }
            
            // Scroll to bottom
            scrollChatToBottom();
            logVoiceDebug('Voice message processing completed successfully');
        })
        .catch(error => {
            logVoiceDebug(`Fetch error: ${error.message}`);
            if (error.stack) {
                logVoiceDebug(`Error stack: ${error.stack}`);
            }
            hideLoadingIndicator();
            console.error('Error sending audio:', error);
            showToast(`Ошибка отправки аудио: ${error.message}`, 'danger');
        });
    } catch (error) {
        logVoiceDebug(`Error creating or sending audio blob: ${error.message}`);
        hideLoadingIndicator();
        showToast('Ошибка обработки аудио', 'danger');
    }
}

// Add message to chat interface
function addMessageToChat(content, isUser, isVoice) {
    const chatMessages = document.getElementById('chat-messages');
    const messageContainer = document.createElement('div');
    messageContainer.className = `d-flex mb-3 ${isUser ? 'justify-content-end' : 'justify-content-start'}`;
    
    const now = new Date();
    const time = now.getHours().toString().padStart(2, '0') + ':' + 
                now.getMinutes().toString().padStart(2, '0');
    
    messageContainer.innerHTML = `
        <div class="p-3 rounded ${isUser ? 'bg-primary text-white' : 'bg-light text-dark'}" style="max-width: 70%;">
            ${isVoice && isUser ? '<small><i class="fas fa-microphone me-1"></i>Голосовое сообщение</small><br>' : ''}
            ${content}
            <br><small class="opacity-75">${time}</small>
        </div>
    `;
    
    chatMessages.appendChild(messageContainer);
}

// Show loading indicator
function showLoadingIndicator() {
    const chatForm = document.getElementById('chat-form');
    const sendButton = document.getElementById('send-button');
    const voiceButton = document.getElementById('voice-button');
    
    if (sendButton) sendButton.disabled = true;
    if (voiceButton) voiceButton.disabled = true;
    
    // Create loading spinner if it doesn't exist
    if (!document.getElementById('loading-indicator')) {
        const loadingIndicator = document.createElement('div');
        loadingIndicator.id = 'loading-indicator';
        loadingIndicator.className = 'text-center my-3';
        loadingIndicator.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2 text-muted">Обработка голосового сообщения...</p>
        `;
        
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.appendChild(loadingIndicator);
        scrollChatToBottom();
    }
}

// Hide loading indicator
function hideLoadingIndicator() {
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.remove();
    }
    
    const sendButton = document.getElementById('send-button');
    const voiceButton = document.getElementById('voice-button');
    
    if (sendButton) sendButton.disabled = false;
    if (voiceButton) voiceButton.disabled = false;
}

// Scroll chat to bottom
function scrollChatToBottom() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initVoiceRecording();
});
