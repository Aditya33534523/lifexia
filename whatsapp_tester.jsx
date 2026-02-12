import React, { useState } from 'react';
import { Send, MessageSquare, Bell, CheckCircle, XCircle, Loader } from 'lucide-react';

export default function WhatsAppTester() {
  const [activeTab, setActiveTab] = useState('template');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  
  // Form states
  const [templateForm, setTemplateForm] = useState({
    to_number: '919824794027',
    template_name: 'hello_world',
    language_code: 'en_US'
  });
  
  const [textForm, setTextForm] = useState({
    to_number: '919824794027',
    message: 'Hello from LifeXia! 👋\n\nThis is a test message from your intelligent pharmacy assistant.'
  });
  
  const [reminderForm, setReminderForm] = useState({
    to_number: '919824794027',
    medication_name: 'Aspirin',
    dosage: '100mg',
    time: '8:00 AM'
  });

  const API_BASE = 'http://localhost:5000/api/whatsapp';

  const sendRequest = async (endpoint, data) => {
    setLoading(true);
    setResult(null);
    
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });
      
      const result = await response.json();
      setResult({
        success: response.ok,
        data: result,
        statusCode: response.status
      });
    } catch (error) {
      setResult({
        success: false,
        error: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const handleTemplateSubmit = (e) => {
    e.preventDefault();
    sendRequest('/send-template', templateForm);
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    sendRequest('/send-message', textForm);
  };

  const handleReminderSubmit = (e) => {
    e.preventDefault();
    sendRequest('/send-reminder', reminderForm);
  };

  const handleQuickSend = () => {
    sendRequest('/quick-send', {});
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-pink-500 to-red-500 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-8 mb-6 border border-white/20 shadow-2xl">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-16 h-16 bg-green-500 rounded-2xl flex items-center justify-center">
              <MessageSquare className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">LifeXia WhatsApp Tester</h1>
              <p className="text-white/80">Test your WhatsApp Business API integration</p>
            </div>
          </div>
          
          <button
            onClick={handleQuickSend}
            disabled={loading}
            className="w-full mt-4 bg-green-500 hover:bg-green-600 text-white font-semibold py-3 px-6 rounded-xl transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                Sending...
              </>
            ) : (
              <>
                <Send className="w-5 h-5" />
                Quick Send Test (hello_world)
              </>
            )}
          </button>
        </div>

        {/* Tabs */}
        <div className="bg-white/10 backdrop-blur-lg rounded-3xl border border-white/20 shadow-2xl overflow-hidden">
          <div className="flex border-b border-white/20">
            <button
              onClick={() => setActiveTab('template')}
              className={`flex-1 py-4 px-6 font-semibold transition-all ${
                activeTab === 'template'
                  ? 'bg-white/20 text-white'
                  : 'text-white/70 hover:bg-white/10'
              }`}
            >
              Template Message
            </button>
            <button
              onClick={() => setActiveTab('text')}
              className={`flex-1 py-4 px-6 font-semibold transition-all ${
                activeTab === 'text'
                  ? 'bg-white/20 text-white'
                  : 'text-white/70 hover:bg-white/10'
              }`}
            >
              Text Message
            </button>
            <button
              onClick={() => setActiveTab('reminder')}
              className={`flex-1 py-4 px-6 font-semibold transition-all ${
                activeTab === 'reminder'
                  ? 'bg-white/20 text-white'
                  : 'text-white/70 hover:bg-white/10'
              }`}
            >
              Medication Reminder
            </button>
          </div>

          <div className="p-8">
            {/* Template Form */}
            {activeTab === 'template' && (
              <form onSubmit={handleTemplateSubmit} className="space-y-6">
                <div>
                  <label className="block text-white font-semibold mb-2">Phone Number</label>
                  <input
                    type="text"
                    value={templateForm.to_number}
                    onChange={(e) => setTemplateForm({...templateForm, to_number: e.target.value})}
                    className="w-full px-4 py-3 rounded-xl bg-white/20 text-white placeholder-white/50 border border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50"
                    placeholder="919824794027"
                  />
                </div>
                
                <div>
                  <label className="block text-white font-semibold mb-2">Template Name</label>
                  <input
                    type="text"
                    value={templateForm.template_name}
                    onChange={(e) => setTemplateForm({...templateForm, template_name: e.target.value})}
                    className="w-full px-4 py-3 rounded-xl bg-white/20 text-white placeholder-white/50 border border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50"
                    placeholder="hello_world"
                  />
                </div>
                
                <div>
                  <label className="block text-white font-semibold mb-2">Language Code</label>
                  <input
                    type="text"
                    value={templateForm.language_code}
                    onChange={(e) => setTemplateForm({...templateForm, language_code: e.target.value})}
                    className="w-full px-4 py-3 rounded-xl bg-white/20 text-white placeholder-white/50 border border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50"
                    placeholder="en_US"
                  />
                </div>
                
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-white/20 hover:bg-white/30 text-white font-semibold py-3 px-6 rounded-xl transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <Loader className="w-5 h-5 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send className="w-5 h-5" />
                      Send Template
                    </>
                  )}
                </button>
              </form>
            )}

            {/* Text Message Form */}
            {activeTab === 'text' && (
              <form onSubmit={handleTextSubmit} className="space-y-6">
                <div>
                  <label className="block text-white font-semibold mb-2">Phone Number</label>
                  <input
                    type="text"
                    value={textForm.to_number}
                    onChange={(e) => setTextForm({...textForm, to_number: e.target.value})}
                    className="w-full px-4 py-3 rounded-xl bg-white/20 text-white placeholder-white/50 border border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50"
                    placeholder="919824794027"
                  />
                </div>
                
                <div>
                  <label className="block text-white font-semibold mb-2">Message</label>
                  <textarea
                    value={textForm.message}
                    onChange={(e) => setTextForm({...textForm, message: e.target.value})}
                    rows="6"
                    className="w-full px-4 py-3 rounded-xl bg-white/20 text-white placeholder-white/50 border border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50"
                    placeholder="Enter your message..."
                  />
                </div>
                
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-white/20 hover:bg-white/30 text-white font-semibold py-3 px-6 rounded-xl transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <Loader className="w-5 h-5 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send className="w-5 h-5" />
                      Send Message
                    </>
                  )}
                </button>
              </form>
            )}

            {/* Reminder Form */}
            {activeTab === 'reminder' && (
              <form onSubmit={handleReminderSubmit} className="space-y-6">
                <div>
                  <label className="block text-white font-semibold mb-2">Phone Number</label>
                  <input
                    type="text"
                    value={reminderForm.to_number}
                    onChange={(e) => setReminderForm({...reminderForm, to_number: e.target.value})}
                    className="w-full px-4 py-3 rounded-xl bg-white/20 text-white placeholder-white/50 border border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50"
                    placeholder="919824794027"
                  />
                </div>
                
                <div>
                  <label className="block text-white font-semibold mb-2">Medication Name</label>
                  <input
                    type="text"
                    value={reminderForm.medication_name}
                    onChange={(e) => setReminderForm({...reminderForm, medication_name: e.target.value})}
                    className="w-full px-4 py-3 rounded-xl bg-white/20 text-white placeholder-white/50 border border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50"
                    placeholder="Aspirin"
                  />
                </div>
                
                <div>
                  <label className="block text-white font-semibold mb-2">Dosage</label>
                  <input
                    type="text"
                    value={reminderForm.dosage}
                    onChange={(e) => setReminderForm({...reminderForm, dosage: e.target.value})}
                    className="w-full px-4 py-3 rounded-xl bg-white/20 text-white placeholder-white/50 border border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50"
                    placeholder="100mg"
                  />
                </div>
                
                <div>
                  <label className="block text-white font-semibold mb-2">Time</label>
                  <input
                    type="text"
                    value={reminderForm.time}
                    onChange={(e) => setReminderForm({...reminderForm, time: e.target.value})}
                    className="w-full px-4 py-3 rounded-xl bg-white/20 text-white placeholder-white/50 border border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50"
                    placeholder="8:00 AM"
                  />
                </div>
                
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-white/20 hover:bg-white/30 text-white font-semibold py-3 px-6 rounded-xl transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <Loader className="w-5 h-5 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Bell className="w-5 h-5" />
                      Send Reminder
                    </>
                  )}
                </button>
              </form>
            )}
          </div>
        </div>

        {/* Result Display */}
        {result && (
          <div className={`mt-6 bg-white/10 backdrop-blur-lg rounded-3xl p-8 border ${
            result.success ? 'border-green-500/50' : 'border-red-500/50'
          } shadow-2xl`}>
            <div className="flex items-center gap-3 mb-4">
              {result.success ? (
                <CheckCircle className="w-8 h-8 text-green-400" />
              ) : (
                <XCircle className="w-8 h-8 text-red-400" />
              )}
              <h3 className={`text-xl font-bold ${
                result.success ? 'text-green-400' : 'text-red-400'
              }`}>
                {result.success ? 'Success!' : 'Error'}
              </h3>
            </div>
            
            <div className="bg-black/30 rounded-xl p-4 overflow-auto">
              <pre className="text-white text-sm">
                {JSON.stringify(result.data || result.error, null, 2)}
              </pre>
            </div>
            
            {result.statusCode && (
              <p className="text-white/70 mt-3 text-sm">
                Status Code: {result.statusCode}
              </p>
            )}
          </div>
        )}

        {/* Instructions */}
        <div className="mt-6 bg-white/10 backdrop-blur-lg rounded-3xl p-8 border border-white/20 shadow-2xl">
          <h3 className="text-xl font-bold text-white mb-4">📝 Instructions</h3>
          <ul className="space-y-2 text-white/90 text-sm">
            <li>✅ Make sure your Flask server is running on http://localhost:5000</li>
            <li>✅ Phone numbers should be in format: 919824794027 (no + sign)</li>
            <li>⚠️ Template messages require approved templates in Meta Business Suite</li>
            <li>⚠️ Text messages only work within 24 hours of user initiating conversation</li>
            <li>💡 Use "Quick Send Test" to verify your setup with hello_world template</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
