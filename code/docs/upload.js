// frontend/static/js/upload.js - File Upload Functionality

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validate file size (10MB max)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showNotification('File size exceeds 10MB limit', 'error');
        event.target.value = '';
        return;
    }
    
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
        showNotification('Please upload an image (JPG, PNG, GIF) or PDF file', 'error');
        event.target.value = '';
        return;
    }
    
    // Show upload message
    addMessage('user', `📎 Uploading: ${file.name} (${formatFileSize(file.size)})`);
    showLoading();
    
    // Create FormData
    const formData = new FormData();
    formData.append('image', file);
    formData.append('user_email', currentUser.email);
    formData.append('session_id', currentSessionId || '');
    
    try {
        const response = await fetch(`${API_BASE}/upload/image`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('lifexia_token')}`
            },
            body: formData
        });
        
        const data = await response.json();
        
        hideLoading();
        
        if (response.ok) {
            // Show extracted text if available
            let responseText = '✅ Image uploaded and analyzed successfully!\n\n';
            
            if (data.extracted_text) {
                responseText += `**Extracted Text:**\n${data.extracted_text}\n\n`;
            }
            
            if (data.ai_response) {
                responseText += `**Analysis:**\n${data.ai_response}`;
            }
            
            addMessage('bot', responseText);
            
            // Update session ID if new
            if (data.session_id && !currentSessionId) {
                currentSessionId = data.session_id;
            }
            
            showNotification('Image processed successfully', 'success');
        } else {
            addMessage('bot', 'Sorry, I had trouble processing your image. Please make sure it\'s clear and try again.');
            showNotification(data.error || 'Upload failed', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        hideLoading();
        addMessage('bot', 'Upload failed due to connection error. Please try again.');
        showNotification('Upload failed', 'error');
    }
    
    // Clear file input
    event.target.value = '';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Drag and drop support
document.addEventListener('DOMContentLoaded', () => {
    const messagesArea = document.getElementById('messagesArea');
    
    if (messagesArea) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            messagesArea.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        // Highlight drop area
        ['dragenter', 'dragover'].forEach(eventName => {
            messagesArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            messagesArea.addEventListener(eventName, unhighlight, false);
        });
        
        // Handle dropped files
        messagesArea.addEventListener('drop', handleDrop, false);
    }
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    document.getElementById('messagesArea').classList.add('border-4', 'border-white', 'border-dashed');
}

function unhighlight(e) {
    document.getElementById('messagesArea').classList.remove('border-4', 'border-white', 'border-dashed');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (files.length > 0) {
        const file = files[0];
        const fileInput = document.getElementById('fileInput');
        
        // Create a new FileList-like object
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;
        
        // Trigger upload
        handleFileUpload({ target: fileInput });
    }
}
