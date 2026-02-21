// frontend/static/js/broadcast.js - Advanced Multi-Template Broadcast
// FIXED: Proper template handling for Meta WhatsApp Business API
// FIXED: Uses hello_world template that's pre-approved on your Meta account

// Template Configurations
// Keys must match template names in Meta Business Manager
const TEMPLATE_CONFIGS = {
    'hello_world': {
        name: 'General Welcome (Pre-approved)',
        description: 'Standard Meta test template - works immediately',
        variables: [] // No variables needed for hello_world
    },
    'pharmacy_alert': {
        name: 'Emergency Alert',
        description: 'Must be approved in Meta Business Manager first',
        variables: [
            { id: 'v1', label: 'Medicine Name', placeholder: 'e.g., Ibuprofen' }
        ]
    },
    'med_reminder': {
        name: 'Medication Reminder',
        description: 'Must be approved in Meta Business Manager first',
        variables: [
            { id: 'v1', label: 'Medicine Name', placeholder: 'e.g., Paracetamol' },
            { id: 'v2', label: 'Dosage/Time', placeholder: 'e.g., 500mg after breakfast' }
        ]
    },
    'stock_update': {
        name: 'Stock Update',
        description: 'Must be approved in Meta Business Manager first',
        variables: [
            { id: 'v1', label: 'Medicine Name', placeholder: 'e.g., Amoxicillin' }
        ]
    },
    'safety_tip': {
        name: 'Safety Tip',
        description: 'Must be approved in Meta Business Manager first',
        variables: [
            { id: 'v1', label: 'Medicine Name', placeholder: 'e.g., Warfarin' },
            { id: 'v2', label: 'Interaction to Avoid', placeholder: 'e.g., Alcohol' }
        ]
    },
    'custom_text': {
        name: 'Custom Text (24h Window Only)',
        description: 'Only works if recipient messaged you in last 24 hours',
        variables: []
    }
};

function showBroadcastModal() {
    const modal = document.getElementById('broadcastModal');
    if (modal) {
        modal.classList.remove('hidden');
        document.getElementById('broadcastStatus').innerHTML = '';

        // Pre-fill admin number from env
        const numbersInput = document.getElementById('broadcastNumbers');
        if (numbersInput && !numbersInput.value.trim()) {
            numbersInput.value = '919824794027'; // Admin number from config
        }

        handleTemplateChange();
    }
}

function closeBroadcastModal() {
    const modal = document.getElementById('broadcastModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function handleTemplateChange() {
    const selector = document.getElementById('templateSelector');
    if (!selector) return;

    const template = selector.value;
    const varContainer = document.getElementById('templateVariablesContainer');
    const msgContainer = document.getElementById('customMessageContainer');
    const statusDiv = document.getElementById('broadcastStatus');

    // Clear previous
    varContainer.innerHTML = '';
    if (statusDiv) statusDiv.innerHTML = '';

    if (template === 'custom_text') {
        varContainer.classList.add('hidden');
        msgContainer.classList.remove('hidden');
    } else {
        msgContainer.classList.add('hidden');
        const config = TEMPLATE_CONFIGS[template];

        if (config && config.variables.length > 0) {
            varContainer.classList.remove('hidden');
            config.variables.forEach(v => {
                const div = document.createElement('div');
                div.className = 'mb-2';
                div.innerHTML = `
                    <label class="block text-white/90 text-sm font-medium mb-1">${v.label}</label>
                    <input type="text" id="var_${v.id}" 
                        class="w-full px-4 py-2 glassmorphism rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/50" 
                        placeholder="${v.placeholder}">
                `;
                varContainer.appendChild(div);
            });
        } else {
            varContainer.classList.add('hidden');
        }

        // Show description/info for selected template
        if (config && template !== 'hello_world') {
            const infoDiv = document.createElement('div');
            infoDiv.className = 'mt-1';
            infoDiv.innerHTML = `<p class="text-white/40 text-[10px]">ℹ️ ${config.description}</p>`;
            varContainer.appendChild(infoDiv);
            varContainer.classList.remove('hidden');
        }
    }
}

async function handleBroadcast() {
    const selector = document.getElementById('templateSelector');
    const template = selector.value;
    const numbersInput = document.getElementById('broadcastNumbers').value.trim();
    const statusDiv = document.getElementById('broadcastStatus');
    const sendButton = document.querySelector('button[onclick="handleBroadcast()"]');

    if (!numbersInput) {
        statusDiv.innerHTML = '<p class="text-red-400">⚠️ Please provide recipient numbers.</p>';
        return;
    }

    const numbers = numbersInput.split(',').map(n => n.trim()).filter(n => n.length > 0);
    if (numbers.length === 0) {
        statusDiv.innerHTML = '<p class="text-red-400">⚠️ Please provide valid recipient numbers.</p>';
        return;
    }

    let payload = {
        numbers: numbers
    };

    if (template === 'custom_text') {
        const message = document.getElementById('broadcastMessage').value.trim();
        if (!message) {
            statusDiv.innerHTML = '<p class="text-red-400">⚠️ Please enter a message for custom text.</p>';
            return;
        }
        payload.message = message;
    } else {
        payload.template_name = template;

        // Extract template variables if any
        const config = TEMPLATE_CONFIGS[template];
        if (config && config.variables.length > 0) {
            const components = [{
                type: 'body',
                parameters: []
            }];

            let missing = false;
            for (const v of config.variables) {
                const input = document.getElementById(`var_${v.id}`);
                const val = input ? input.value.trim() : '';

                if (!val) {
                    statusDiv.innerHTML = `<p class="text-red-400">⚠️ Please fill in "${v.label}".</p>`;
                    missing = true;
                    break;
                }

                components[0].parameters.push({
                    type: 'text',
                    text: val
                });
            }
            if (missing) return;

            payload.components = components;
        }
    }

    // UI Feedback
    statusDiv.innerHTML = `
        <div class="flex items-center gap-2">
            <div class="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white"></div>
            <p class="text-white/70">Sending broadcast to ${numbers.length} recipient(s)...</p>
        </div>
    `;
    if (sendButton) sendButton.disabled = true;

    try {
        console.log('📤 Sending Broadcast Payload:', JSON.stringify(payload, null, 2));

        const baseUrl = (typeof API_BASE !== 'undefined') ? API_BASE : '/api';

        const response = await fetch(`${baseUrl}/whatsapp/broadcast`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('lifexia_token')}`
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        console.log('📥 Broadcast Response:', data);

        if (response.ok && data.success) {
            const result = data.broadcast_result || {};
            const sentCount = result.sent || 0;
            const failedCount = result.failed || 0;
            const totalCount = result.total || numbers.length;

            let statusHtml = `<p class="text-green-400">✅ Broadcast sent successfully! (${sentCount}/${totalCount} delivered)</p>`;

            if (failedCount > 0 && result.errors && result.errors.length > 0) {
                statusHtml += `<p class="text-yellow-400 text-xs mt-1">⚠️ ${failedCount} failed:</p>`;
                result.errors.forEach(err => {
                    statusHtml += `<p class="text-red-300 text-xs ml-2">• ${err.number}: ${err.error_message || err.error || 'Unknown error'}</p>`;
                });
            }

            statusDiv.innerHTML = statusHtml;

            setTimeout(() => {
                closeBroadcastModal();
                if (sendButton) sendButton.disabled = false;
                statusDiv.innerHTML = '';
            }, 3000);
        } else {
            statusDiv.innerHTML = `<p class="text-red-400">❌ Error: ${data.error || 'Failed to send broadcast'}</p>`;
            if (sendButton) sendButton.disabled = false;
        }
    } catch (error) {
        console.error('Broadcast error:', error);
        statusDiv.innerHTML = '<p class="text-red-400">❌ Connection error. Please check your network and try again.</p>';
        if (sendButton) sendButton.disabled = false;
    }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    const selector = document.getElementById('templateSelector');
    if (selector) {
        selector.addEventListener('change', handleTemplateChange);
        handleTemplateChange();
    }
});
