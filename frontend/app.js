class LoanChatApp {
    constructor() {
        this.sessionId = null;
        this.isLoading = false;
        
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.typingIndicator = document.getElementById('typingIndicator');
        
        this.init();
    }

    init() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        this.messageInput.addEventListener('input', () => {
            this.sendButton.disabled = !this.messageInput.value.trim();
        });

        this.startSession();
    }

    async startSession() {
        try {
            this.showTyping();
            
            const response = await fetch('/api/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to start session');
            }

            const data = await response.json();
            this.sessionId = data.session_id;
            
            this.hideTyping();
            this.addMessage('assistant', data.message);
            this.messageInput.focus();

        } catch (error) {
            console.error('Error starting session:', error);
            this.hideTyping();
            this.addMessage('assistant', 'Welcome to Horizon Finance! I apologize, but I\'m having trouble connecting. Please refresh the page to try again.');
        }
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || this.isLoading) return;

        this.addMessage('user', message);
        this.messageInput.value = '';
        this.sendButton.disabled = true;
        this.isLoading = true;
        this.showTyping();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    message: message
                })
            });

            if (!response.ok) {
                throw new Error('Failed to send message');
            }

            const data = await response.json();
            this.sessionId = data.session_id;

            this.hideTyping();
            this.addMessage('assistant', data.message, data.download_available, data.download_path);

        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTyping();
            this.addMessage('assistant', 'I apologize, but I encountered an issue processing your request. Please try again.');
        } finally {
            this.isLoading = false;
            this.messageInput.focus();
        }
    }

    addMessage(role, content, downloadAvailable = false, downloadPath = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const labelDiv = document.createElement('div');
        labelDiv.className = 'message-label';
        labelDiv.textContent = role === 'user' ? 'You' : 'Horizon Finance';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Format content to bold questions
        const formattedContent = this.formatMessageWithBoldQuestions(content);
        contentDiv.innerHTML = formattedContent;

        messageDiv.appendChild(labelDiv);
        messageDiv.appendChild(contentDiv);

        if (downloadAvailable && downloadPath) {
            const downloadBtn = document.createElement('a');
            downloadBtn.className = 'download-button';
            downloadBtn.href = downloadPath;
            downloadBtn.target = '_blank';
            downloadBtn.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <polyline points="7,10 12,15 17,10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Download Sanction Letter
            `;
            messageDiv.appendChild(downloadBtn);
        }

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showTyping() {
        this.typingIndicator.classList.add('active');
        this.scrollToBottom();
    }

    hideTyping() {
        this.typingIndicator.classList.remove('active');
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 50);
    }

    formatMessageWithBoldQuestions(content) {
        // Escape HTML first to prevent XSS
        let escaped = this.escapeHtml(content);
        
        // Split content into lines (preserving line breaks)
        const lines = escaped.split('\n');
        let formattedLines = [];
        
        for (let line of lines) {
            // Find the last sentence/question ending with ? in the line
            // This regex finds the last sentence that ends with ? (including the ?)
            const questionMatch = line.match(/([^.!?]*\?[^.!?]*)$/);
            
            if (questionMatch) {
                // Found a question at the end - bold only that part
                const questionPart = questionMatch[0];
                const beforeQuestion = line.slice(0, line.length - questionPart.length);
                
                if (beforeQuestion.trim()) {
                    // There's text before the question - keep it normal, bold only the question
                    formattedLines.push(`${beforeQuestion}<strong>${questionPart}</strong>`);
                } else {
                    // The entire line is the question - bold it
                    formattedLines.push(`<strong>${line}</strong>`);
                }
            } else {
                // No question mark found, look for question patterns
                const questionPatterns = [
                    /(Could you[^.!?\n]*\?)/gi,
                    /(Can you[^.!?\n]*\?)/gi,
                    /(Would you[^.!?\n]*\?)/gi,
                    /(How many[^.!?\n]*\?)/gi,
                    /(How much[^.!?\n]*\?)/gi,
                    /(What[^.!?\n]{5,}\?)/gi,
                    /(Which[^.!?\n]*\?)/gi,
                    /(Tell me[^.!?\n]*\?)/gi,
                    /(Please share[^.!?\n]*\?)/gi,
                    /(I need[^.!?\n]*\?)/gi
                ];
                
                let processedLine = line;
                let hasQuestion = false;
                
                questionPatterns.forEach(pattern => {
                    if (pattern.test(processedLine)) {
                        hasQuestion = true;
                        processedLine = processedLine.replace(pattern, (match) => {
                            // Only bold if it's a substantial question
                            if (match.trim().length > 10) {
                                return `<strong>${match}</strong>`;
                            }
                            return match;
                        });
                    }
                });
                
                formattedLines.push(processedLine);
            }
        }
        
        // Join lines with <br> tags
        return formattedLines.join('<br>');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new LoanChatApp();
});
