// frontend/static/js/broadcast.js - Advanced Multi-Template Broadcast

// Template Configurations
// NOTE: keys must match template names in Meta Business Manager
const TEMPLATE_CONFIGS = {
    'hello_world': {
        name: 'General Welcome',
        variables: [] // No variables needed
    },
    'pharmacy_alert': {
        name: 'Emergency Alert',
        variables: [
            { id: 'v1', label: 'Medicine Name', placeholder: 'e.g., Ibuprofen' }
        ]
    },
    'med_reminder': {
        name: 'Medication Reminder',
        variables: [
            { id: 'v1', label: 'Medicine Name', placeholder: 'e.g., Paracetamol' },
            { id: 'v2', label: 'Dosage/Time', placeholder: 'e.g., 500mg after breakfast' }
        ]
    },
    'stock_update': {
        name: 'Stock Update',
        variables: [
            { id: 'v1', label: 'Medicine Name', placeholder: 'e.g., Amoxicillin' }
        ]
    },
    'safety_tip': {
        name: 'Safety Tip',
        variables: [
            { id: 'v1', label: 'Medicine Name', placeholder: 'e.g., Warfarin' },
            { id: 'v2', label: 'Interaction to Avoid', placeholder: 'e.g., Alcohol' }
        ]
    },
    'custom_text': {
        name: 'Custom Text (24h Window Only)',
        variables: []
    }
};

function showBroadcastModal() {
    const modal = document.getElementById('broadcastModal');
    if (modal) {
        modal.classList.remove('hidden');
        document.getElementById('broadcastStatus').innerHTML = '';

        // Reset inputs if needed? Keeping them might be handled better
        // But let's trigger change to ensure UI is consistent
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

    // Clear previous inputs
    varContainer.innerHTML = '';

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
    }
}

async function handleBroadcast() {
    const selector = document.getElementById('templateSelector');
    const template = selector.value;
    const numbersInput = document.getElementById('broadcastNumbers').value.trim();
    const statusDiv = document.getElementById('broadcastStatus');
    // Try to find the button more robustly or just add an ID to it if possible, but selector is fine
    // Assuming the button calls this function
    const sendButton = document.querySelector('button[onclick="handleBroadcast()"]');

    if (!numbersInput) {
        statusDiv.innerHTML = '<p class="text-red-400">Please provide recipient numbers.</p>';
        return;
    }

    const numbers = numbersInput.split(',').map(n => n.trim()).filter(n => n.length > 0);
    if (numbers.length === 0) {
        statusDiv.innerHTML = '<p class="text-red-400">Please provide valid recipient numbers.</p>';
        return;
    }

    let payload = {
        numbers: numbers
    };

    if (template === 'custom_text') {
        const message = document.getElementById('broadcastMessage').value.trim();
        if (!message) {
            statusDiv.innerHTML = '<p class="text-red-400">Please enter a message for custom text.</p>';
            return;
        }
        payload.message = message;
    } else {
        payload.template_name = template;

        // Extract variables if any
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
                    statusDiv.innerHTML = `<p class="text-red-400">Please fill in ${v.label}.</p>`;
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
    statusDiv.innerHTML = '<p class="text-white/70 animate-pulse">Sending broadcast...</p>';
    if (sendButton) sendButton.disabled = true;

    try {
        console.log('Sending Broadcast Payload:', payload);

        // Define API_BASE if not defined (fallback)
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
        console.log('Broadcast Response:', data);

        if (response.ok) {
            statusDiv.innerHTML = `<p class="text-green-400">Broadcast sent successfully to ${numbers.length} recipients.</p>`;
            setTimeout(() => {
                closeBroadcastModal();
                if (sendButton) sendButton.disabled = false;
                statusDiv.innerHTML = '';
            }, 2000);
        } else {
            statusDiv.innerHTML = `<p class="text-red-400">Error: ${data.error || 'Failed to send broadcast'}</p>`;
            if (sendButton) sendButton.disabled = false;
        }
    } catch (error) {
        console.error('Broadcast error:', error);
        statusDiv.innerHTML = '<p class="text-red-400">Connection error. Please try again. Check console for details.</p>';
        if (sendButton) sendButton.disabled = false;
    }
}

// Ensure handleTemplateChange is called on load if specific elements exist
document.addEventListener('DOMContentLoaded', () => {
    const selector = document.getElementById('templateSelector');
    if (selector) {
        selector.addEventListener('change', handleTemplateChange);
        handleTemplateChange();
    }
});
