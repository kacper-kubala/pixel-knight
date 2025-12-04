/**
 * Pixel Knight - Frontend Application
 */

// ============================================
// Markdown Configuration
// ============================================

// Configure marked with highlight.js
if (typeof marked !== 'undefined') {
    marked.setOptions({
        highlight: function(code, lang) {
            if (typeof hljs !== 'undefined') {
                if (lang && hljs.getLanguage(lang)) {
                    try {
                        return hljs.highlight(code, { language: lang }).value;
                    } catch (e) {}
                }
                return hljs.highlightAuto(code).value;
            }
            return code;
        },
        breaks: true,
        gfm: true,
    });
}

// ============================================
// State Management
// ============================================

const state = {
    sessions: [],
    models: [],
    presets: [],
    providers: [],
    providerPresets: [],
    currentSession: null,
    searchProvider: 'duckduckgo',
    braveApiKey: '',
    searxngUrl: '',
    ragEnabled: false,
    ragFiles: [],
    isGenerating: false,
    searchEnabled: false,
};

// ============================================
// API Functions
// ============================================

const API = {
    async fetchModels() {
        try {
            const response = await fetch('/api/models');
            const data = await response.json();
            return data.models || [];
        } catch (error) {
            console.error('Error fetching models:', error);
            return [];
        }
    },

    async fetchSessions() {
        try {
            const response = await fetch('/api/sessions');
            const data = await response.json();
            return data.sessions || [];
        } catch (error) {
            console.error('Error fetching sessions:', error);
            return [];
        }
    },

    async createSession(name, model, temperature = 0.7, maxTokens = 2048, systemPrompt = "You are a helpful AI assistant.") {
        try {
            const response = await fetch('/api/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    name, 
                    model,
                    temperature,
                    max_tokens: maxTokens,
                    system_prompt: systemPrompt,
                }),
            });
            return await response.json();
        } catch (error) {
            console.error('Error creating session:', error);
            return null;
        }
    },

    async updateSession(sessionId, updates) {
        try {
            const response = await fetch(`/api/sessions/${sessionId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates),
            });
            return await response.json();
        } catch (error) {
            console.error('Error updating session:', error);
            return null;
        }
    },

    async deleteSession(sessionId) {
        try {
            await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
            return true;
        } catch (error) {
            console.error('Error deleting session:', error);
            return false;
        }
    },

    async autoNameSession(sessionId) {
        try {
            const response = await fetch(`/api/sessions/${sessionId}/auto-name`, { method: 'POST' });
            return await response.json();
        } catch (error) {
            console.error('Error auto-naming session:', error);
            return null;
        }
    },

    async regenerateResponse(sessionId, messageId) {
        try {
            const response = await fetch(`/api/chat/${sessionId}/regenerate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message_id: messageId }),
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to regenerate');
            }
            return await response.json();
        } catch (error) {
            console.error('Error regenerating response:', error);
            return null;
        }
    },

    async sendMessageStream(sessionId, message, model, enableSearch, enableRag, searchProvider, temperature, maxTokens, systemPrompt) {
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                message,
                model,
                enable_search: enableSearch,
                enable_rag: enableRag,
                search_provider: searchProvider,
                temperature,
                max_tokens: maxTokens,
                system_prompt: systemPrompt,
            }),
        });
        return response;
    },

    async getRagFiles() {
        try {
            const response = await fetch('/api/rag/files');
            const data = await response.json();
            return data.files || [];
        } catch (error) {
            console.error('Error fetching RAG files:', error);
            return [];
        }
    },

    async indexDirectory(path) {
        const response = await fetch('/api/rag/index', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ directory_path: path }),
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to index directory');
        }
        return await response.json();
    },

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/rag/upload', {
            method: 'POST',
            body: formData,
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to upload file');
        }
        return await response.json();
    },

    async summarizeYoutube(url) {
        const response = await fetch('/api/youtube/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to summarize video');
        }
        return await response.json();
    },

    async deepResearch(query, maxIterations = 5) {
        const response = await fetch('/api/research', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                query,
                max_iterations: maxIterations,
                search_provider: state.searchProvider,
            }),
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Research failed');
        }
        return await response.json();
    },

    async getUsage() {
        try {
            const response = await fetch('/api/usage');
            return await response.json();
        } catch (error) {
            console.error('Error fetching usage:', error);
            return null;
        }
    },

    async updateConfig(config) {
        const response = await fetch('/api/config', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config),
        });
        return await response.json();
    },

    async getConfig() {
        try {
            const response = await fetch('/api/config');
            return await response.json();
        } catch (error) {
            console.error('Error getting config:', error);
            return {};
        }
    },

    // Provider Management
    async getProviders() {
        try {
            const response = await fetch('/api/providers');
            const data = await response.json();
            return data.providers || [];
        } catch (error) {
            console.error('Error fetching providers:', error);
            return [];
        }
    },

    async getProviderPresets() {
        try {
            const response = await fetch('/api/providers/presets');
            const data = await response.json();
            return data.presets || [];
        } catch (error) {
            console.error('Error fetching provider presets:', error);
            return [];
        }
    },

    async addPresetProvider(presetKey, apiKey = '') {
        try {
            const response = await fetch(`/api/providers/preset/${presetKey}?api_key=${encodeURIComponent(apiKey)}`, {
                method: 'POST',
            });
            return await response.json();
        } catch (error) {
            console.error('Error adding preset provider:', error);
            return null;
        }
    },

    async addCustomProvider(name, type, apiBase, apiKey = '') {
        try {
            const params = new URLSearchParams({ name, provider_type: type, api_base: apiBase, api_key: apiKey });
            const response = await fetch(`/api/providers?${params}`, {
                method: 'POST',
            });
            return await response.json();
        } catch (error) {
            console.error('Error adding custom provider:', error);
            return null;
        }
    },

    async updateProvider(providerId, updates) {
        try {
            const params = new URLSearchParams();
            if (updates.name) params.append('name', updates.name);
            if (updates.api_base) params.append('api_base', updates.api_base);
            if (updates.api_key !== undefined) params.append('api_key', updates.api_key);
            if (updates.enabled !== undefined) params.append('enabled', updates.enabled);
            
            const response = await fetch(`/api/providers/${providerId}?${params}`, {
                method: 'PUT',
            });
            return await response.json();
        } catch (error) {
            console.error('Error updating provider:', error);
            return null;
        }
    },

    async deleteProvider(providerId) {
        try {
            await fetch(`/api/providers/${providerId}`, { method: 'DELETE' });
            return true;
        } catch (error) {
            console.error('Error deleting provider:', error);
            return false;
        }
    },

    async toggleProvider(providerId) {
        try {
            const response = await fetch(`/api/providers/${providerId}/toggle`, { method: 'POST' });
            return await response.json();
        } catch (error) {
            console.error('Error toggling provider:', error);
            return null;
        }
    },

    async testProvider(providerId) {
        try {
            const response = await fetch(`/api/providers/${providerId}/test`, { method: 'POST' });
            return await response.json();
        } catch (error) {
            console.error('Error testing provider:', error);
            return { success: false, error: error.message };
        }
    },

    async getPresets() {
        try {
            const response = await fetch('/api/presets');
            const data = await response.json();
            return data.presets || [];
        } catch (error) {
            console.error('Error fetching presets:', error);
            return [];
        }
    },

    async getPreset(presetId) {
        try {
            const response = await fetch(`/api/presets/${presetId}`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching preset:', error);
            return null;
        }
    },

    async editMessage(sessionId, messageId, content) {
        try {
            const response = await fetch(`/api/sessions/${sessionId}/messages/${messageId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content }),
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to edit message');
            }
            return await response.json();
        } catch (error) {
            console.error('Error editing message:', error);
            return null;
        }
    },

    async searchSessions(query) {
        try {
            const response = await fetch(`/api/sessions/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            return data.sessions || [];
        } catch (error) {
            console.error('Error searching sessions:', error);
            return [];
        }
    },

    async generateImage(prompt, size, quality, style) {
        const response = await fetch('/api/images/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, size, quality, style }),
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate image');
        }
        return await response.json();
    },

    async checkImageStatus() {
        try {
            const response = await fetch('/api/images/status');
            const data = await response.json();
            return data.configured || false;
        } catch (error) {
            return false;
        }
    },

    async compareChat(messages, model) {
        const response = await fetch('/api/compare/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages, model }),
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Comparison failed');
        }
        return await response.json();
    },
};

// ============================================
// UI Functions
// ============================================

const UI = {
    renderSessions() {
        const container = document.getElementById('sessionsList');
        if (!container) return;

        if (state.sessions.length === 0) {
            container.innerHTML = '<div class="empty-message">No sessions yet</div>';
            return;
        }

        container.innerHTML = state.sessions.map(session => `
            <div class="session-item ${state.currentSession?.id === session.id ? 'active' : ''}" 
                 data-id="${session.id}">
                <div class="session-info-item">
                    <span class="session-name-text">${this.escapeHtml(session.name)}</span>
                    <span class="session-meta">${session.model}</span>
                </div>
                <div class="session-actions">
                    <button class="btn-icon btn-delete-session" data-id="${session.id}" title="Delete">×</button>
                </div>
            </div>
        `).join('');

        container.querySelectorAll('.session-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.btn-delete-session')) {
                    this.selectSession(item.dataset.id);
                }
            });
        });

        container.querySelectorAll('.btn-delete-session').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteSession(btn.dataset.id);
            });
        });
    },

    renderModels() {
        const container = document.getElementById('modelsList');
        const select = document.getElementById('newSessionModel');
        
        if (container) {
            if (state.models.length === 0) {
                container.innerHTML = '<div class="empty-message">No models available. Configure API providers first.</div>';
            } else {
                // Group models by provider
                const grouped = {};
                state.models.forEach(model => {
                    const providerName = model.provider_name || 'Unknown';
                    if (!grouped[providerName]) grouped[providerName] = [];
                    grouped[providerName].push(model);
                });
                
                // Render grouped models
                container.innerHTML = Object.entries(grouped).map(([providerName, models]) => `
                    <div class="model-group">
                        <div class="model-group-header">${this.escapeHtml(providerName)}</div>
                        ${models.map(model => `
                            <div class="model-item">
                                <span class="model-name">${this.escapeHtml(model.name || model.id)}</span>
                                <button class="btn-chat" data-model="${model.id}">+ Chat</button>
                            </div>
                        `).join('')}
                    </div>
                `).join('');

                container.querySelectorAll('.btn-chat').forEach(btn => {
                    btn.addEventListener('click', () => {
                        this.createQuickSession(btn.dataset.model);
                    });
                });
            }
        }

        if (select) {
            // Group in select as well
            const grouped = {};
            state.models.forEach(model => {
                const providerName = model.provider_name || 'Unknown';
                if (!grouped[providerName]) grouped[providerName] = [];
                grouped[providerName].push(model);
            });
            
            select.innerHTML = Object.entries(grouped).map(([providerName, models]) => `
                <optgroup label="${this.escapeHtml(providerName)}">
                    ${models.map(model => 
                        `<option value="${model.id}">${this.escapeHtml(model.name || model.id)}</option>`
                    ).join('')}
                </optgroup>
            `).join('');
        }
    },

    renderMessages(messages) {
        const container = document.getElementById('chatMessages');
        if (!container) return;

        if (!messages || messages.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">◈</div>
                    <p>No messages yet. Start a conversation.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = messages.map((msg, idx) => this.renderMessage(msg, idx)).join('');
        container.scrollTop = container.scrollHeight;
        
        // Re-apply syntax highlighting
        if (typeof hljs !== 'undefined') {
            container.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }
    },

    renderMessage(msg, msgIndex = null) {
        const isUser = msg.role === 'user';
        const time = new Date(msg.timestamp).toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        let sourcesHtml = '';
        if (msg.sources && msg.sources.length > 0) {
            sourcesHtml = `
                <div class="message-sources">
                    <div class="sources-title">Sources:</div>
                    ${msg.sources.map(s => `
                        <a href="${this.escapeHtml(s.url)}" target="_blank" class="source-item">
                            ${this.escapeHtml(s.title)}
                        </a>
                    `).join('')}
                </div>
            `;
        }

        // Parse markdown for assistant messages, escape HTML for user messages
        let contentHtml;
        if (isUser) {
            contentHtml = this.escapeHtml(msg.content);
        } else {
            contentHtml = this.parseMarkdown(msg.content);
        }

        // Add message actions based on role
        let actionsHtml = '';
        if (isUser) {
            actionsHtml = `
                <div class="message-actions">
                    <button class="btn-msg-action" onclick="UI.editMessage('${msg.id}')" title="Edit">✏️</button>
                    <button class="btn-msg-action" onclick="UI.copyMessage('${msg.id}')" title="Copy">📋</button>
                </div>
            `;
        } else if (msgIndex !== null) {
            actionsHtml = `
                <div class="message-actions">
                    <button class="btn-msg-action" onclick="UI.copyMessage('${msg.id}')" title="Copy">📋</button>
                    <button class="btn-msg-action" onclick="UI.regenerateMessage('${msg.id}')" title="Regenerate">🔄</button>
                </div>
            `;
        }

        return `
            <div class="message ${isUser ? 'user' : 'assistant'}" data-msg-id="${msg.id}">
                <div class="message-avatar">${isUser ? '●' : '◈'}</div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-role">${isUser ? 'You' : state.currentSession?.model || 'Assistant'}</span>
                        <span class="message-time">${time}</span>
                        ${actionsHtml}
                    </div>
                    <div class="message-text markdown-body" id="msg-text-${msg.id}">${contentHtml}</div>
                    ${sourcesHtml}
                </div>
            </div>
        `;
    },

    parseMarkdown(text) {
        if (!text) return '';
        
        // Use marked if available, otherwise fallback to basic escaping
        if (typeof marked !== 'undefined') {
            try {
                return marked.parse(text);
            } catch (e) {
                console.error('Markdown parsing error:', e);
                return this.escapeHtml(text);
            }
        }
        return this.escapeHtml(text);
    },

    copyMessage(msgId) {
        const msg = state.currentSession?.messages.find(m => m.id === msgId);
        if (msg) {
            navigator.clipboard.writeText(msg.content);
        }
    },

    editMessage(msgId) {
        const msg = state.currentSession?.messages.find(m => m.id === msgId);
        if (!msg) return;
        
        const textDiv = document.getElementById(`msg-text-${msgId}`);
        if (!textDiv) return;
        
        // Check if already editing
        if (textDiv.querySelector('textarea')) return;
        
        // Store original content
        const originalContent = msg.content;
        
        // Create edit interface
        textDiv.innerHTML = `
            <div class="edit-message-container">
                <textarea class="edit-message-input" id="edit-input-${msgId}">${UI.escapeHtml(originalContent)}</textarea>
                <div class="edit-message-actions">
                    <button class="btn-small btn-primary" onclick="UI.saveEdit('${msgId}')">Save</button>
                    <button class="btn-small btn-secondary" onclick="UI.cancelEdit('${msgId}', '${encodeURIComponent(originalContent)}')">Cancel</button>
                </div>
            </div>
        `;
        
        // Focus the textarea
        document.getElementById(`edit-input-${msgId}`)?.focus();
    },

    async saveEdit(msgId) {
        const input = document.getElementById(`edit-input-${msgId}`);
        if (!input) return;
        
        const newContent = input.value.trim();
        if (!newContent) return;
        
        try {
            const result = await API.editMessage(state.currentSession.id, msgId, newContent);
            if (result) {
                // Update local state
                const msg = state.currentSession.messages.find(m => m.id === msgId);
                if (msg) {
                    msg.content = newContent;
                }
                
                // Refresh the message display
                const textDiv = document.getElementById(`msg-text-${msgId}`);
                if (textDiv) {
                    textDiv.innerHTML = this.escapeHtml(newContent);
                }
            }
        } catch (error) {
            console.error('Edit failed:', error);
            alert('Failed to save edit');
        }
    },

    cancelEdit(msgId, encodedOriginal) {
        const originalContent = decodeURIComponent(encodedOriginal);
        const textDiv = document.getElementById(`msg-text-${msgId}`);
        if (textDiv) {
            textDiv.innerHTML = this.escapeHtml(originalContent);
        }
    },

    async regenerateMessage(msgId) {
        if (state.isGenerating || !state.currentSession) return;
        
        // Find message index and trigger regeneration
        const msgIndex = state.currentSession.messages.findIndex(m => m.id === msgId);
        if (msgIndex === -1) return;
        
        // Call regenerate API
        try {
            state.isGenerating = true;
            document.getElementById('sendBtn').disabled = true;
            
            const response = await API.regenerateResponse(state.currentSession.id, msgId);
            if (response) {
                // Refresh session data
                const sessions = await API.fetchSessions();
                state.sessions = sessions;
                const session = sessions.find(s => s.id === state.currentSession.id);
                if (session) {
                    state.currentSession = session;
                    this.renderMessages(session.messages);
                }
            }
        } catch (error) {
            console.error('Regeneration error:', error);
        } finally {
            state.isGenerating = false;
            document.getElementById('sendBtn').disabled = false;
        }
    },

    renderPresets() {
        const select = document.getElementById('presetSelect');
        if (!select) return;

        select.innerHTML = '<option value="">-- Select a preset --</option>' + 
            state.presets.map(preset => `
                <option value="${preset.id}">${preset.icon} ${UI.escapeHtml(preset.name)}</option>
            `).join('');
    },

    renderSearchResults(results, query) {
        const container = document.getElementById('sessionsList');
        if (!container) return;

        if (results.length === 0) {
            container.innerHTML = `
                <div class="empty-sessions">
                    <p>No results for "${this.escapeHtml(query)}"</p>
                </div>
            `;
            return;
        }

        container.innerHTML = results.map(session => {
            const isActive = state.currentSession?.id === session.id;
            const messageCount = session.messages?.length || 0;
            const timeAgo = this.formatTimeAgo(new Date(session.updated_at));
            
            // Highlight matching text
            const highlightedName = session.name.replace(
                new RegExp(`(${this.escapeRegExp(query)})`, 'gi'),
                '<mark>$1</mark>'
            );
            
            return `
                <div class="session-item ${isActive ? 'active' : ''}" 
                     onclick="UI.selectSession('${session.id}')">
                    <div class="session-info">
                        <div class="session-name">${highlightedName}</div>
                        <div class="session-meta">${messageCount} msgs · ${timeAgo}</div>
                    </div>
                    <button class="btn-delete" onclick="event.stopPropagation(); UI.deleteSession('${session.id}')" title="Delete">×</button>
                </div>
            `;
        }).join('');
    },

    escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    },

    applyPreset(presetId) {
        const preset = state.presets.find(p => p.id === presetId);
        if (!preset) return;

        // Apply preset values to form fields
        const systemPromptField = document.getElementById('newSessionSystemPrompt') || 
                                  document.getElementById('sessionSystemPrompt');
        const tempField = document.getElementById('newSessionTemp') || 
                          document.getElementById('sessionTemp');
        const maxTokensField = document.getElementById('newSessionMaxTokens') || 
                               document.getElementById('sessionMaxTokens');
        
        if (systemPromptField) systemPromptField.value = preset.system_prompt;
        if (tempField) {
            tempField.value = preset.temperature;
            const tempValue = document.getElementById('tempValue');
            if (tempValue) tempValue.textContent = preset.temperature;
        }
        if (maxTokensField) maxTokensField.value = preset.max_tokens;
    },

    renderRagFiles() {
        const container = document.getElementById('ragFilesList');
        if (!container) return;

        if (state.ragFiles.length === 0) {
            container.innerHTML = '';
            return;
        }

        container.innerHTML = state.ragFiles.map(file => `
            <div class="rag-file-item">
                <span class="rag-file-name" title="${this.escapeHtml(file.path)}">
                    ${this.escapeHtml(file.path.split('/').pop())}
                </span>
                <span class="rag-file-size">${this.formatBytes(file.size)}</span>
            </div>
        `).join('');
    },

    renderUsageStats(usage) {
        const container = document.getElementById('usageStats');
        if (!container || !usage) return;

        container.innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${usage.sessions?.total_sessions || 0}</div>
                <div class="stat-label">Sessions</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${usage.sessions?.total_messages || 0}</div>
                <div class="stat-label">Messages</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${this.formatNumber(usage.sessions?.total_tokens || 0)}</div>
                <div class="stat-label">Total Tokens</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${usage.llm?.total_requests || 0}</div>
                <div class="stat-label">API Requests</div>
            </div>
        `;
    },

    async selectSession(sessionId) {
        const session = state.sessions.find(s => s.id === sessionId);
        if (!session) return;

        state.currentSession = session;
        document.getElementById('currentSessionName').textContent = session.name;
        
        // Update parameter display
        if (document.getElementById('sessionSystemPrompt')) {
            document.getElementById('sessionSystemPrompt').value = session.system_prompt || '';
        }
        if (document.getElementById('sessionTemp')) {
            document.getElementById('sessionTemp').value = session.temperature || 0.7;
            document.getElementById('tempValue').textContent = session.temperature || 0.7;
        }
        if (document.getElementById('sessionMaxTokens')) {
            document.getElementById('sessionMaxTokens').value = session.max_tokens || 2048;
        }
        
        this.renderSessions();
        this.renderMessages(session.messages);
    },

    async deleteSession(sessionId) {
        if (!confirm('Delete this session?')) return;
        
        if (await API.deleteSession(sessionId)) {
            state.sessions = state.sessions.filter(s => s.id !== sessionId);
            if (state.currentSession?.id === sessionId) {
                state.currentSession = state.sessions[0] || null;
                if (state.currentSession) {
                    document.getElementById('currentSessionName').textContent = state.currentSession.name;
                    this.renderMessages(state.currentSession.messages);
                } else {
                    document.getElementById('currentSessionName').textContent = 'No session selected';
                    this.renderMessages([]);
                }
            }
            this.renderSessions();
        }
    },

    async createQuickSession(modelId) {
        const timestamp = new Date().toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit'
        });
        const name = `Chat: ${modelId} ${timestamp}`;
        
        const session = await API.createSession(name, modelId);
        if (session) {
            state.sessions.unshift(session);
            state.currentSession = session;
            document.getElementById('currentSessionName').textContent = session.name;
            this.renderSessions();
            this.renderMessages([]);
        }
    },

    addMessageToUI(role, content, sources = null) {
        const msg = {
            id: Date.now().toString(),
            role,
            content,
            timestamp: new Date().toISOString(),
            sources,
        };

        if (state.currentSession) {
            state.currentSession.messages.push(msg);
        }

        const container = document.getElementById('chatMessages');
        if (!container) return;

        const emptyState = container.querySelector('.empty-state');
        if (emptyState) emptyState.remove();

        container.insertAdjacentHTML('beforeend', this.renderMessage(msg));
        container.scrollTop = container.scrollHeight;

        return msg;
    },

    showTypingIndicator() {
        const container = document.getElementById('chatMessages');
        if (!container) return;

        const indicator = document.createElement('div');
        indicator.id = 'typingIndicator';
        indicator.className = 'message assistant';
        indicator.innerHTML = `
            <div class="message-avatar">◈</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-role">${state.currentSession?.model || 'Assistant'}</span>
                </div>
                <div class="message-text">
                    <div class="analyzing-indicator">
                        <div class="analyzing-icon"></div>
                        <span>Analyzing sources...</span>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(indicator);
        container.scrollTop = container.scrollHeight;
    },

    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) indicator.remove();
    },

    updateTypingContent(content) {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            const textEl = indicator.querySelector('.message-text');
            if (textEl) {
                textEl.innerHTML = this.escapeHtml(content);
            }
        }
    },

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    },

    formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    },

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.classList.add('active');
    },

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.classList.remove('active');
    },

    toggleSidebar(side) {
        const container = document.getElementById('appContainer');
        const btn = document.getElementById(side === 'left' ? 'toggleLeftSidebar' : 'toggleRightSidebar');
        
        if (side === 'left') {
            container.classList.toggle('sidebar-left-hidden');
            btn.textContent = container.classList.contains('sidebar-left-hidden') ? '▶' : '◀';
        } else {
            container.classList.toggle('sidebar-right-hidden');
            btn.textContent = container.classList.contains('sidebar-right-hidden') ? '◀' : '▶';
        }
    },

    // Provider Management UI
    async renderProviders() {
        const container = document.getElementById('providersList');
        if (!container) return;

        if (state.providers.length === 0) {
            container.innerHTML = '<div class="empty-message">No providers configured</div>';
        } else {
            container.innerHTML = state.providers.map(provider => this.renderProviderItem(provider)).join('');
            this.attachProviderListeners();
        }
    },

    renderProviderItem(provider) {
        const icon = this.getProviderIcon(provider.type);
        const statusClass = provider.enabled ? 'online' : 'offline';
        
        return `
            <div class="provider-item ${provider.enabled ? '' : 'disabled'}" data-id="${provider.id}">
                <div class="provider-info">
                    <div class="provider-icon">${icon}</div>
                    <div class="provider-details">
                        <h4>${this.escapeHtml(provider.name)}</h4>
                        <div class="provider-meta">
                            <span class="provider-type-badge">${provider.type}</span>
                            <span><span class="status-indicator ${statusClass}"></span> ${provider.enabled ? 'Active' : 'Disabled'}</span>
                            ${provider.has_key ? '<span>🔑 Key set</span>' : '<span style="color: var(--warning)">⚠️ No key</span>'}
                            ${provider.models_count > 0 ? `<span>${provider.models_count} models</span>` : ''}
                        </div>
                    </div>
                </div>
                <div class="provider-actions">
                    <button class="btn-test" data-id="${provider.id}" title="Test connection">Test</button>
                    <button class="btn-toggle ${provider.enabled ? 'active' : ''}" data-id="${provider.id}" title="Toggle enabled">
                        ${provider.enabled ? 'ON' : 'OFF'}
                    </button>
                    <button class="btn-edit" data-id="${provider.id}" title="Edit provider">Edit</button>
                </div>
            </div>
        `;
    },

    getProviderIcon(type) {
        const icons = {
            'openai': '🤖',
            'anthropic': '🧠',
            'ollama': '🦙',
            'groq': '⚡',
            'xai': '𝕏',
            'together': '🤝',
            'mistral': '🌀',
            'openrouter': '🛤️',
            'custom': '⚙️',
        };
        return icons[type] || '🔌';
    },

    async renderProviderPresets() {
        const container = document.getElementById('presetProviders');
        if (!container) return;

        // Filter out already configured providers
        const configuredIds = state.providers.map(p => p.id);
        const availablePresets = state.providerPresets.filter(p => !configuredIds.includes(p.key));

        container.innerHTML = availablePresets.map(preset => `
            <button class="preset-btn" data-key="${preset.key}" title="${preset.api_base}">
                <span class="preset-icon">${this.getProviderIcon(preset.type)}</span>
                <span class="preset-name">${this.escapeHtml(preset.name)}</span>
            </button>
        `).join('') + `
            <button class="preset-btn" id="addCustomProviderBtn">
                <span class="preset-icon">➕</span>
                <span class="preset-name">Custom</span>
            </button>
        `;

        // Attach click listeners
        container.querySelectorAll('.preset-btn[data-key]').forEach(btn => {
            btn.addEventListener('click', () => this.showAddPresetDialog(btn.dataset.key));
        });

        document.getElementById('addCustomProviderBtn')?.addEventListener('click', () => {
            document.getElementById('customProviderForm')?.classList.remove('hidden');
        });
    },

    async showAddPresetDialog(presetKey) {
        const preset = state.providerPresets.find(p => p.key === presetKey);
        if (!preset) return;

        if (preset.requires_key) {
            const apiKey = prompt(`Enter API key for ${preset.name}:`);
            if (apiKey === null) return; // Cancelled
            await this.addProvider(presetKey, apiKey);
        } else {
            await this.addProvider(presetKey, '');
        }
    },

    async addProvider(presetKey, apiKey) {
        const result = await API.addPresetProvider(presetKey, apiKey);
        if (result?.provider) {
            state.providers = await API.getProviders();
            state.providerPresets = await API.getProviderPresets();
            this.renderProviders();
            this.renderProviderPresets();
            
            // Refresh models
            state.models = await API.fetchModels();
            this.renderModels();
        }
    },

    attachProviderListeners() {
        // Test buttons
        document.querySelectorAll('.provider-actions .btn-test').forEach(btn => {
            btn.addEventListener('click', async () => {
                const providerId = btn.dataset.id;
                btn.textContent = '...';
                btn.disabled = true;
                
                const result = await API.testProvider(providerId);
                
                if (result.success) {
                    btn.textContent = '✓';
                    btn.style.color = 'var(--success)';
                    
                    // Refresh providers to update model count
                    state.providers = await API.getProviders();
                    this.renderProviders();
                    
                    // Refresh models
                    state.models = await API.fetchModels();
                    this.renderModels();
                } else {
                    btn.textContent = '✗';
                    btn.style.color = 'var(--error)';
                    alert(`Test failed: ${result.error}`);
                }
                
                setTimeout(() => {
                    btn.textContent = 'Test';
                    btn.style.color = '';
                    btn.disabled = false;
                }, 2000);
            });
        });

        // Toggle buttons
        document.querySelectorAll('.provider-actions .btn-toggle').forEach(btn => {
            btn.addEventListener('click', async () => {
                const providerId = btn.dataset.id;
                const result = await API.toggleProvider(providerId);
                if (result !== null) {
                    state.providers = await API.getProviders();
                    this.renderProviders();
                    
                    // Refresh models
                    state.models = await API.fetchModels();
                    this.renderModels();
                }
            });
        });

        // Edit buttons
        document.querySelectorAll('.provider-actions .btn-edit').forEach(btn => {
            btn.addEventListener('click', () => {
                const providerId = btn.dataset.id;
                const provider = state.providers.find(p => p.id === providerId);
                if (provider) {
                    this.openEditProviderModal(provider);
                }
            });
        });
    },

    openEditProviderModal(provider) {
        document.getElementById('editProviderId').value = provider.id;
        document.getElementById('editProviderName').value = provider.name;
        document.getElementById('editProviderUrl').value = provider.api_base;
        document.getElementById('editProviderKey').value = '';
        
        this.showModal('editProviderModal');
    },

    async saveProviderEdit() {
        const providerId = document.getElementById('editProviderId').value;
        const name = document.getElementById('editProviderName').value;
        const apiBase = document.getElementById('editProviderUrl').value;
        const apiKey = document.getElementById('editProviderKey').value;

        const updates = { name, api_base: apiBase };
        if (apiKey) updates.api_key = apiKey;

        const result = await API.updateProvider(providerId, updates);
        if (result) {
            state.providers = await API.getProviders();
            this.renderProviders();
            this.hideModal('editProviderModal');
            
            // Refresh models
            state.models = await API.fetchModels();
            this.renderModels();
        }
    },

    async deleteProvider(providerId) {
        if (!confirm('Delete this provider?')) return;
        
        if (await API.deleteProvider(providerId)) {
            state.providers = await API.getProviders();
            state.providerPresets = await API.getProviderPresets();
            this.renderProviders();
            this.renderProviderPresets();
            
            // Refresh models
            state.models = await API.fetchModels();
            this.renderModels();
            
            this.hideModal('editProviderModal');
        }
    },
};

// ============================================
// Event Handlers
// ============================================

async function handleSendMessage() {
    if (state.isGenerating) return;

    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    if (!state.currentSession) {
        alert('Please select or create a session first');
        return;
    }

    input.value = '';
    input.style.height = 'auto';
    
    UI.addMessageToUI('user', message);
    
    state.isGenerating = true;
    document.getElementById('sendBtn').disabled = true;
    
    try {
        UI.showTypingIndicator();
        
        const response = await API.sendMessageStream(
            state.currentSession.id,
            message,
            state.currentSession.model,
            state.searchEnabled,
            state.ragEnabled,
            state.searchProvider,
            state.currentSession.temperature,
            state.currentSession.max_tokens,
            state.currentSession.system_prompt
        );

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullContent = '';
        let sources = null;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === 'sources') {
                            sources = data.data;
                        } else if (data.type === 'content') {
                            fullContent += data.data;
                            UI.updateTypingContent(fullContent);
                        } else if (data.type === 'done') {
                            UI.hideTypingIndicator();
                            UI.addMessageToUI('assistant', fullContent, sources);
                            
                            // Auto-name session after first message
                            if (state.currentSession.messages.length === 2 && 
                                state.currentSession.name.startsWith('Chat:')) {
                                const result = await API.autoNameSession(state.currentSession.id);
                                if (result?.name) {
                                    state.currentSession.name = result.name;
                                    document.getElementById('currentSessionName').textContent = result.name;
                                    UI.renderSessions();
                                }
                            }
                        }
                    } catch (e) {
                        // Skip invalid JSON
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error:', error);
        UI.hideTypingIndicator();
        UI.addMessageToUI('assistant', 'Error: Failed to get response. Please try again.');
    } finally {
        state.isGenerating = false;
        document.getElementById('sendBtn').disabled = false;
        state.searchEnabled = false;
        document.getElementById('researchBtn').classList.remove('active');
    }
}

async function handleCreateSession() {
    const nameInput = document.getElementById('newSessionName');
    const modelSelect = document.getElementById('newSessionModel');
    const tempInput = document.getElementById('newSessionTemp');
    const maxTokensInput = document.getElementById('newSessionMaxTokens');
    const systemPromptInput = document.getElementById('newSessionSystemPrompt');
    
    const name = nameInput.value.trim() || `Session ${Date.now()}`;
    const model = modelSelect.value;
    const temperature = parseFloat(tempInput.value) || 0.7;
    const maxTokens = parseInt(maxTokensInput.value) || 2048;
    const systemPrompt = systemPromptInput.value || "You are a helpful AI assistant.";
    
    if (!model) {
        alert('Please select a model');
        return;
    }
    
    const session = await API.createSession(name, model, temperature, maxTokens, systemPrompt);
    if (session) {
        state.sessions.unshift(session);
        state.currentSession = session;
        document.getElementById('currentSessionName').textContent = session.name;
        UI.renderSessions();
        UI.renderMessages([]);
        UI.hideModal('newSessionModal');
        nameInput.value = '';
        systemPromptInput.value = "You are a helpful AI assistant.";
        tempInput.value = "0.7";
        maxTokensInput.value = "2048";
    }
}

async function handleSaveParams() {
    if (!state.currentSession) return;
    
    const systemPrompt = document.getElementById('sessionSystemPrompt').value;
    const temperature = parseFloat(document.getElementById('sessionTemp').value);
    const maxTokens = parseInt(document.getElementById('sessionMaxTokens').value);
    
    const updated = await API.updateSession(state.currentSession.id, {
        system_prompt: systemPrompt,
        temperature,
        max_tokens: maxTokens,
    });
    
    if (updated) {
        state.currentSession.system_prompt = systemPrompt;
        state.currentSession.temperature = temperature;
        state.currentSession.max_tokens = maxTokens;
        UI.hideModal('paramsModal');
    }
}

async function handleIndexDirectory() {
    const input = document.getElementById('ragPathInput');
    const path = input.value.trim();
    
    if (!path) {
        alert('Please enter a directory path');
        return;
    }
    
    try {
        const result = await API.indexDirectory(path);
        alert(`Indexed ${result.files_indexed} files`);
        input.value = '';
        state.ragFiles = await API.getRagFiles();
        UI.renderRagFiles();
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function handleFileUpload(files) {
    for (const file of files) {
        try {
            await API.uploadFile(file);
        } catch (error) {
            alert(`Error uploading ${file.name}: ${error.message}`);
        }
    }
    state.ragFiles = await API.getRagFiles();
    UI.renderRagFiles();
}

async function handleYoutubeSummarize() {
    const urlInput = document.getElementById('youtubeUrl');
    const url = urlInput.value.trim();
    
    if (!url) {
        alert('Please enter a YouTube URL');
        return;
    }
    
    if (!state.currentSession) {
        alert('Please select or create a session first');
        return;
    }
    
    UI.hideModal('youtubeModal');
    UI.addMessageToUI('user', `Summarize this YouTube video: ${url}`);
    
    state.isGenerating = true;
    UI.showTypingIndicator();
    
    try {
        const result = await API.summarizeYoutube(url);
        UI.hideTypingIndicator();
        
        const response = `**${result.title}**\nBy: ${result.author}\n\n${result.summary}`;
        UI.addMessageToUI('assistant', response, [{
            title: result.title,
            url: `https://www.youtube.com/watch?v=${result.video_id}`,
            snippet: `Video by ${result.author}`,
        }]);
    } catch (error) {
        UI.hideTypingIndicator();
        UI.addMessageToUI('assistant', `Error: ${error.message}`);
    } finally {
        state.isGenerating = false;
        urlInput.value = '';
    }
}

async function handleDeepResearch() {
    const queryInput = document.getElementById('researchQuery');
    const iterationsInput = document.getElementById('researchIterations');
    const progressDiv = document.getElementById('researchProgress');
    const progressFill = document.getElementById('progressFill');
    const progressStatus = document.getElementById('progressStatus');
    
    const query = queryInput.value.trim();
    const iterations = parseInt(iterationsInput.value) || 5;
    
    if (!query) {
        alert('Please enter a research query');
        return;
    }
    
    if (!state.currentSession) {
        alert('Please select or create a session first');
        return;
    }
    
    // Show progress
    progressDiv.style.display = 'block';
    progressFill.style.width = '0%';
    progressStatus.textContent = 'Starting research...';
    
    try {
        const result = await API.deepResearch(query, iterations);
        
        UI.hideModal('deepResearchModal');
        progressDiv.style.display = 'none';
        
        UI.addMessageToUI('user', `Deep Research: ${query}`);
        UI.addMessageToUI('assistant', result.summary, result.sources.slice(0, 10));
        
    } catch (error) {
        progressStatus.textContent = `Error: ${error.message}`;
        setTimeout(() => {
            progressDiv.style.display = 'none';
        }, 3000);
    }
    
    queryInput.value = '';
}

async function handleGenerateImage() {
    const promptInput = document.getElementById('imagePrompt');
    const sizeSelect = document.getElementById('imageSize');
    const qualitySelect = document.getElementById('imageQuality');
    const styleSelect = document.getElementById('imageStyle');
    const generatingDiv = document.getElementById('imageGenerating');
    
    const prompt = promptInput.value.trim();
    
    if (!prompt) {
        alert('Please enter an image prompt');
        return;
    }
    
    if (!state.currentSession) {
        alert('Please select or create a session first');
        return;
    }
    
    // Show generating status
    generatingDiv.style.display = 'flex';
    
    try {
        const result = await API.generateImage(
            prompt,
            sizeSelect.value,
            qualitySelect.value,
            styleSelect.value
        );
        
        UI.hideModal('imageModal');
        generatingDiv.style.display = 'none';
        
        // Add to chat
        UI.addMessageToUI('user', `Generate image: ${prompt}`);
        
        // Create image message
        const imageContent = `![Generated Image](${result.url})\n\n**Prompt used:** ${result.revised_prompt}`;
        UI.addMessageToUI('assistant', imageContent);
        
    } catch (error) {
        generatingDiv.style.display = 'none';
        alert(`Error generating image: ${error.message}`);
    } finally {
        promptInput.value = '';
    }
}

function startEditingSessionName() {
    if (!state.currentSession) return;
    
    const nameSpan = document.getElementById('currentSessionName');
    const currentName = state.currentSession.name;
    
    // Replace span with input
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'session-name-input';
    input.value = currentName;
    input.id = 'sessionNameInput';
    
    nameSpan.replaceWith(input);
    input.focus();
    input.select();
    
    // Save on enter or blur
    const saveNewName = async () => {
        const newName = input.value.trim();
        if (newName && newName !== currentName) {
            await API.updateSession(state.currentSession.id, { name: newName });
            state.currentSession.name = newName;
            UI.renderSessions();
        }
        
        // Restore the span
        const newSpan = document.createElement('span');
        newSpan.className = 'session-name';
        newSpan.id = 'currentSessionName';
        newSpan.title = 'Click to edit';
        newSpan.textContent = state.currentSession.name;
        newSpan.addEventListener('click', () => {
            if (state.currentSession) startEditingSessionName();
        });
        input.replaceWith(newSpan);
    };
    
    input.addEventListener('blur', saveNewName);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            input.blur();
        } else if (e.key === 'Escape') {
            input.value = currentName; // Reset to original
            input.blur();
        }
    });
}

function handleVoiceInput() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        alert('Voice input not supported in this browser. Try Chrome or Edge.');
        return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    
    const voiceBtn = document.getElementById('voiceBtn');
    voiceBtn.classList.add('active');
    voiceBtn.textContent = '🔴';
    
    recognition.start();
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        const messageInput = document.getElementById('messageInput');
        messageInput.value += transcript;
        messageInput.focus();
    };
    
    recognition.onend = () => {
        voiceBtn.classList.remove('active');
        voiceBtn.textContent = '🎤';
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        voiceBtn.classList.remove('active');
        voiceBtn.textContent = '🎤';
        
        if (event.error === 'not-allowed') {
            alert('Microphone access denied. Please allow microphone access and try again.');
        }
    };
}

async function handleModelCompare() {
    const prompt = document.getElementById('comparePrompt').value.trim();
    const modelA = document.getElementById('compareModelA').value;
    const modelB = document.getElementById('compareModelB').value;
    
    if (!prompt) {
        alert('Please enter a prompt');
        return;
    }
    
    // Show results area
    const resultsDiv = document.getElementById('compareResults');
    resultsDiv.style.display = 'grid';
    
    // Update headers
    document.getElementById('compareHeaderA').textContent = modelA;
    document.getElementById('compareHeaderB').textContent = modelB;
    
    // Show spinners
    document.getElementById('spinnerA').style.display = 'block';
    document.getElementById('spinnerB').style.display = 'block';
    
    // Clear previous responses
    document.getElementById('compareResponseA').innerHTML = 'Generating...';
    document.getElementById('compareResponseB').innerHTML = 'Generating...';
    
    // Run both requests in parallel
    const messages = [{ role: 'user', content: prompt }];
    
    try {
        const [responseA, responseB] = await Promise.all([
            API.compareChat(messages, modelA),
            API.compareChat(messages, modelB),
        ]);
        
        // Display responses with markdown
        document.getElementById('compareResponseA').innerHTML = UI.parseMarkdown(responseA.content);
        document.getElementById('compareResponseB').innerHTML = UI.parseMarkdown(responseB.content);
        
    } catch (error) {
        console.error('Comparison error:', error);
    } finally {
        document.getElementById('spinnerA').style.display = 'none';
        document.getElementById('spinnerB').style.display = 'none';
    }
}

function handleSearchProviderChange() {
    const provider = document.querySelector('input[name="searchProvider"]:checked')?.value || 'duckduckgo';
    
    document.getElementById('braveKeyGroup').style.display = provider === 'brave' ? 'block' : 'none';
    document.getElementById('searxngUrlGroup').style.display = provider === 'searxng' ? 'block' : 'none';
}

async function handleSaveSearchSettings() {
    const provider = document.querySelector('input[name="searchProvider"]:checked')?.value || 'duckduckgo';
    const braveKey = document.getElementById('braveApiKey').value;
    const searxngUrl = document.getElementById('searxngUrl').value;
    
    state.searchProvider = provider;
    state.braveApiKey = braveKey;
    state.searxngUrl = searxngUrl;
    
    await API.updateConfig({
        brave_api_key: braveKey,
        searxng_url: searxngUrl,
    });
    
    UI.hideModal('searchSettingsModal');
}

async function handleSaveApiSettings() {
    const apiBase = document.getElementById('apiBaseUrl').value;
    const apiKey = document.getElementById('apiKeyInput').value;
    
    await API.updateConfig({
        api_base: apiBase,
        api_key: apiKey,
    });
    
    // Reload models
    state.models = await API.fetchModels();
    UI.renderModels();
    
    UI.hideModal('apiSettingsModal');
}

// ============================================
// Initialization
// ============================================

async function init() {
    // Load initial data
    const [models, sessions, ragFiles, config, presets, providers, providerPresets] = await Promise.all([
        API.fetchModels(),
        API.fetchSessions(),
        API.getRagFiles(),
        API.getConfig(),
        API.getPresets(),
        API.getProviders(),
        API.getProviderPresets(),
    ]);
    
    state.models = models;
    state.sessions = sessions;
    state.ragFiles = ragFiles;
    state.presets = presets;
    state.providers = providers;
    state.providerPresets = providerPresets;
    
    // Render UI
    UI.renderModels();
    UI.renderSessions();
    UI.renderRagFiles();
    UI.renderPresets();
    
    // Select first session if available
    if (state.sessions.length > 0) {
        UI.selectSession(state.sessions[0].id);
    }
    
    // Setup event listeners
    setupEventListeners();
}

function setupEventListeners() {
    // Send message
    document.getElementById('sendBtn')?.addEventListener('click', handleSendMessage);
    
    document.getElementById('messageInput')?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
    
    // Auto-resize textarea
    document.getElementById('messageInput')?.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
    });
    
    // New session
    document.getElementById('newSessionBtn')?.addEventListener('click', () => UI.showModal('newSessionModal'));
    document.getElementById('createSession')?.addEventListener('click', handleCreateSession);
    document.getElementById('cancelNewSession')?.addEventListener('click', () => UI.hideModal('newSessionModal'));
    document.getElementById('closeNewSessionModal')?.addEventListener('click', () => UI.hideModal('newSessionModal'));
    
    // Session search
    let searchTimeout;
    document.getElementById('sessionSearch')?.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (!query) {
            // Reset to all sessions
            UI.renderSessions();
            return;
        }
        
        searchTimeout = setTimeout(async () => {
            const results = await API.searchSessions(query);
            UI.renderSearchResults(results, query);
        }, 300);
    });
    
    // Preset selector
    document.getElementById('presetSelect')?.addEventListener('change', function() {
        if (this.value) {
            UI.applyPreset(this.value);
        }
    });
    
    // Auto-name session
    document.getElementById('autoNameBtn')?.addEventListener('click', async () => {
        if (!state.currentSession || state.currentSession.messages.length === 0) return;
        const result = await API.autoNameSession(state.currentSession.id);
        if (result?.name) {
            state.currentSession.name = result.name;
            document.getElementById('currentSessionName').textContent = result.name;
            UI.renderSessions();
        }
    });
    
    // Edit session name
    document.getElementById('editNameBtn')?.addEventListener('click', () => {
        if (!state.currentSession) return;
        startEditingSessionName();
    });
    
    document.getElementById('currentSessionName')?.addEventListener('click', () => {
        if (!state.currentSession) return;
        startEditingSessionName();
    });
    
    // Parameters modal
    document.getElementById('paramsBtn')?.addEventListener('click', () => {
        if (state.currentSession) {
            document.getElementById('sessionSystemPrompt').value = state.currentSession.system_prompt || '';
            document.getElementById('sessionTemp').value = state.currentSession.temperature || 0.7;
            document.getElementById('tempValue').textContent = state.currentSession.temperature || 0.7;
            document.getElementById('sessionMaxTokens').value = state.currentSession.max_tokens || 2048;
        }
        UI.showModal('paramsModal');
    });
    document.getElementById('saveParams')?.addEventListener('click', handleSaveParams);
    document.getElementById('cancelParams')?.addEventListener('click', () => UI.hideModal('paramsModal'));
    document.getElementById('closeParamsModal')?.addEventListener('click', () => UI.hideModal('paramsModal'));
    
    // Temperature slider
    document.getElementById('sessionTemp')?.addEventListener('input', function() {
        document.getElementById('tempValue').textContent = this.value;
    });
    
    // Search settings
    document.getElementById('searchSettingsBtn')?.addEventListener('click', () => UI.showModal('searchSettingsModal'));
    document.getElementById('saveSearchSettings')?.addEventListener('click', handleSaveSearchSettings);
    document.getElementById('cancelSearchSettings')?.addEventListener('click', () => UI.hideModal('searchSettingsModal'));
    document.getElementById('closeSearchModal')?.addEventListener('click', () => UI.hideModal('searchSettingsModal'));
    
    document.querySelectorAll('input[name="searchProvider"]').forEach(radio => {
        radio.addEventListener('change', handleSearchProviderChange);
    });
    
    // API Providers management
    document.getElementById('apiSettingsBtn')?.addEventListener('click', async () => {
        // Load providers when opening modal
        state.providers = await API.getProviders();
        state.providerPresets = await API.getProviderPresets();
        UI.renderProviders();
        UI.renderProviderPresets();
        UI.showModal('apiSettingsModal');
    });
    document.getElementById('closeApiModal')?.addEventListener('click', () => UI.hideModal('apiSettingsModal'));
    document.getElementById('closeProvidersBtn')?.addEventListener('click', () => UI.hideModal('apiSettingsModal'));
    
    // Custom provider form
    document.getElementById('cancelCustomProvider')?.addEventListener('click', () => {
        document.getElementById('customProviderForm')?.classList.add('hidden');
    });
    document.getElementById('saveCustomProvider')?.addEventListener('click', async () => {
        const name = document.getElementById('customProviderName').value;
        const apiBase = document.getElementById('customProviderUrl').value;
        const apiKey = document.getElementById('customProviderKey').value;
        
        if (!name || !apiBase) {
            alert('Please provide name and API URL');
            return;
        }
        
        const result = await API.addCustomProvider(name, 'custom', apiBase, apiKey);
        if (result?.provider) {
            state.providers = await API.getProviders();
            UI.renderProviders();
            document.getElementById('customProviderForm')?.classList.add('hidden');
            document.getElementById('customProviderName').value = '';
            document.getElementById('customProviderUrl').value = '';
            document.getElementById('customProviderKey').value = '';
            
            // Refresh models
            state.models = await API.fetchModels();
            UI.renderModels();
        }
    });
    
    // Edit provider modal
    document.getElementById('closeEditProviderModal')?.addEventListener('click', () => UI.hideModal('editProviderModal'));
    document.getElementById('cancelEditProvider')?.addEventListener('click', () => UI.hideModal('editProviderModal'));
    document.getElementById('saveEditProvider')?.addEventListener('click', () => UI.saveProviderEdit());
    document.getElementById('deleteProviderBtn')?.addEventListener('click', () => {
        const providerId = document.getElementById('editProviderId').value;
        UI.deleteProvider(providerId);
    });
    
    // RAG
    document.getElementById('ragToggle')?.addEventListener('change', function() {
        state.ragEnabled = this.checked;
    });
    document.getElementById('addRagBtn')?.addEventListener('click', handleIndexDirectory);
    
    // File upload
    document.getElementById('uploadBtn')?.addEventListener('click', () => {
        document.getElementById('fileUpload').click();
    });
    document.getElementById('fileUpload')?.addEventListener('change', function() {
        if (this.files.length > 0) {
            handleFileUpload(this.files);
            this.value = '';
        }
    });
    
    // Research button
    document.getElementById('researchBtn')?.addEventListener('click', function() {
        state.searchEnabled = !state.searchEnabled;
        this.classList.toggle('active', state.searchEnabled);
    });
    
    // Deep research
    document.getElementById('deepResearchBtn')?.addEventListener('click', () => UI.showModal('deepResearchModal'));
    document.getElementById('startDeepResearch')?.addEventListener('click', handleDeepResearch);
    document.getElementById('cancelDeepResearch')?.addEventListener('click', () => UI.hideModal('deepResearchModal'));
    document.getElementById('closeDeepResearchModal')?.addEventListener('click', () => UI.hideModal('deepResearchModal'));
    
    // YouTube
    document.getElementById('youtubeBtn')?.addEventListener('click', () => UI.showModal('youtubeModal'));
    document.getElementById('summarizeYoutube')?.addEventListener('click', handleYoutubeSummarize);
    document.getElementById('cancelYoutube')?.addEventListener('click', () => UI.hideModal('youtubeModal'));
    document.getElementById('closeYoutubeModal')?.addEventListener('click', () => UI.hideModal('youtubeModal'));
    
    // Image generation
    document.getElementById('imageBtn')?.addEventListener('click', async () => {
        const isConfigured = await API.checkImageStatus();
        if (!isConfigured) {
            alert('Image generation not configured. Set OPENAI_DALLE_KEY in .env');
            return;
        }
        UI.showModal('imageModal');
    });
    document.getElementById('generateImage')?.addEventListener('click', handleGenerateImage);
    document.getElementById('cancelImage')?.addEventListener('click', () => UI.hideModal('imageModal'));
    document.getElementById('closeImageModal')?.addEventListener('click', () => UI.hideModal('imageModal'));
    
    // Voice input
    document.getElementById('voiceBtn')?.addEventListener('click', handleVoiceInput);
    
    // Usage stats
    document.getElementById('usageBtn')?.addEventListener('click', async () => {
        const usage = await API.getUsage();
        UI.renderUsageStats(usage);
        UI.showModal('usageModal');
    });
    document.getElementById('closeUsageModal')?.addEventListener('click', () => UI.hideModal('usageModal'));
    document.getElementById('closeUsageBtn')?.addEventListener('click', () => UI.hideModal('usageModal'));
    
    // Model comparison
    document.getElementById('compareBtn')?.addEventListener('click', () => {
        // Populate model dropdowns
        const modelA = document.getElementById('compareModelA');
        const modelB = document.getElementById('compareModelB');
        if (modelA && modelB) {
            modelA.innerHTML = state.models.map(m => 
                `<option value="${m.id}">${UI.escapeHtml(m.id)}</option>`
            ).join('');
            modelB.innerHTML = state.models.map(m => 
                `<option value="${m.id}">${UI.escapeHtml(m.id)}</option>`
            ).join('');
            // Select second model by default if available
            if (state.models.length > 1) {
                modelB.selectedIndex = 1;
            }
        }
        document.getElementById('compareResults').style.display = 'none';
        UI.showModal('compareModal');
    });
    document.getElementById('startCompare')?.addEventListener('click', handleModelCompare);
    document.getElementById('cancelCompare')?.addEventListener('click', () => UI.hideModal('compareModal'));
    document.getElementById('closeCompareModal')?.addEventListener('click', () => UI.hideModal('compareModal'));
    
    // Shortcuts modal
    document.getElementById('closeShortcutsModal')?.addEventListener('click', () => UI.hideModal('shortcutsModal'));
    document.getElementById('closeShortcutsBtn')?.addEventListener('click', () => UI.hideModal('shortcutsModal'));
    
    // Sidebar toggles
    document.getElementById('toggleLeftSidebar')?.addEventListener('click', () => UI.toggleSidebar('left'));
    document.getElementById('toggleRightSidebar')?.addEventListener('click', () => UI.toggleSidebar('right'));
    
    // Copy all
    document.getElementById('copyAllBtn')?.addEventListener('click', () => {
        if (state.currentSession) {
            const text = state.currentSession.messages.map(m => 
                `${m.role.toUpperCase()}: ${m.content}`
            ).join('\n\n');
            navigator.clipboard.writeText(text);
        }
    });
    
    // Export buttons
    document.getElementById('exportMdBtn')?.addEventListener('click', () => {
        if (state.currentSession) {
            window.location.href = `/api/sessions/${state.currentSession.id}/export?format=md`;
        }
    });
    
    document.getElementById('exportJsonBtn')?.addEventListener('click', () => {
        if (state.currentSession) {
            window.location.href = `/api/sessions/${state.currentSession.id}/export?format=json`;
        }
    });
    
    // Close modals on background click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
    
    // Global keyboard shortcuts
    setupKeyboardShortcuts();
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Check if we're in an input/textarea
        const isInputFocused = ['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName);
        
        // Escape - close any open modal
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.modal.active');
            if (activeModal) {
                activeModal.classList.remove('active');
                e.preventDefault();
                return;
            }
        }
        
        // Ctrl+Enter or Cmd+Enter - send message (works in textarea too)
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            handleSendMessage();
            return;
        }
        
        // Don't process shortcuts if input is focused
        if (isInputFocused) return;
        
        // Ctrl+N or Cmd+N - new session
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            UI.showModal('newSessionModal');
            return;
        }
        
        // Ctrl+K or Cmd+K - focus search/input
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            document.getElementById('messageInput')?.focus();
            return;
        }
        
        // Ctrl+B or Cmd+B - toggle left sidebar
        if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
            e.preventDefault();
            UI.toggleSidebar('left');
            return;
        }
        
        // ? - show shortcuts help
        if (e.key === '?') {
            e.preventDefault();
            UI.showModal('shortcutsModal');
            return;
        }
        
        // Number keys 1-9 - switch to session
        if (e.key >= '1' && e.key <= '9' && !e.ctrlKey && !e.metaKey) {
            const sessionIndex = parseInt(e.key) - 1;
            if (state.sessions[sessionIndex]) {
                UI.selectSession(state.sessions[sessionIndex].id);
            }
        }
    });
}

// Start the app
document.addEventListener('DOMContentLoaded', init);
