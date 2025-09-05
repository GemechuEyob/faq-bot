class FAQBotUI {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000/v1';
        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupChatInterface();
        this.setupKnowledgeBase();
    }

    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        const pages = document.querySelectorAll('.page');

        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetPage = link.dataset.page;

                navLinks.forEach(l => l.classList.remove('active'));
                pages.forEach(p => p.classList.remove('active'));

                link.classList.add('active');
                document.getElementById(`${targetPage}-page`).classList.add('active');
            });
        });
    }

    setupChatInterface() {
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-button');
        const chatMessages = document.getElementById('chat-messages');

        const sendMessage = async () => {
            const query = chatInput.value.trim();
            if (!query) return;

            chatInput.value = '';
            sendButton.disabled = true;

            this.addMessage(query, 'user');

            try {
                const response = await fetch(`${this.apiBaseUrl}/bot`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ query })
                });

                const data = await response.json();

                if (response.ok) {
                    this.addMessage(data.response || data.message || 'No response received', 'bot');
                } else {
                    this.addMessage(`Error: ${data.detail || data.message || 'Unknown error occurred'}`, 'bot');
                }
            } catch (error) {
                this.addMessage(`Connection error: ${error.message}`, 'bot');
            } finally {
                sendButton.disabled = false;
                chatInput.focus();
            }
        };

        sendButton.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        chatInput.focus();
    }

    addMessage(content, sender) {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = `<strong>${sender === 'user' ? 'You' : 'Bot'}:</strong> ${this.escapeHtml(content)}`;
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    setupKnowledgeBase() {
        this.apiKey = 'test'; // Default API key
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.totalItems = 0;
        this.searchQuery = '';
        
        this.setupAddArticleModal();
        this.setupSearch();
        this.setupPagination();
        this.loadArticles();
    }

    setupAddArticleModal() {
        const addBtn = document.getElementById('add-article-btn');
        const modal = document.getElementById('add-article-modal');
        const closeModal = modal.querySelector('.close-modal');
        const cancelBtn = modal.querySelector('.cancel-btn');
        const form = document.getElementById('add-article-form');

        // Show modal
        addBtn.addEventListener('click', () => {
            modal.style.display = 'block';
        });

        // Hide modal
        const hideModal = () => {
            modal.style.display = 'none';
            form.reset();
        };

        closeModal.addEventListener('click', hideModal);
        cancelBtn.addEventListener('click', hideModal);

        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                hideModal();
            }
        });

        // Handle form submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const url = document.getElementById('article-url').value.trim();
            if (!url) return;

            const statusEl = document.getElementById('status-message');
            this.showStatus(statusEl, 'Adding article to knowledge base...', 'loading');

            try {
                const response = await fetch(`${this.apiBaseUrl}/scrape`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-API-Key': this.apiKey
                    },
                    body: JSON.stringify({ urls: [url] })
                });

                const data = await response.json();

                if (response.ok) {
                    this.showStatus(statusEl, 'Article successfully added!', 'success');
                    hideModal();
                    this.loadArticles();
                } else {
                    this.showStatus(statusEl, `Error: ${data.detail || data.message || 'Unknown error occurred'}`, 'error');
                }
            } catch (error) {
                this.showStatus(statusEl, `Connection error: ${error.message}`, 'error');
            }
        });
    }

    setupSearch() {
        const searchBtn = document.getElementById('search-btn');
        const searchInput = document.getElementById('search-input');

        const performSearch = () => {
            this.searchQuery = searchInput.value.trim();
            this.currentPage = 1;
            this.loadArticles();
        };

        searchBtn.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }

    setupPagination() {
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');

        prevBtn.addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.loadArticles();
            }
        });

        nextBtn.addEventListener('click', () => {
            const maxPage = Math.ceil(this.totalItems / this.itemsPerPage);
            if (this.currentPage < maxPage) {
                this.currentPage++;
                this.loadArticles();
            }
        });
    }

    async loadArticles() {
        const statusEl = document.getElementById('status-message');
        const tableBody = document.getElementById('articles-table-body');

        this.showStatus(statusEl, 'Loading articles...', 'loading');

        try {
            const offset = (this.currentPage - 1) * this.itemsPerPage;
            const params = new URLSearchParams({
                limit: this.itemsPerPage.toString(),
                offset: offset.toString()
            });

            if (this.searchQuery) {
                params.append('search', this.searchQuery);
            }

            const response = await fetch(`${this.apiBaseUrl}/data?${params}`, {
                method: 'GET',
                headers: {
                    'X-API-Key': this.apiKey
                }
            });

            const data = await response.json();

            if (response.ok) {
                this.displayArticles(data);
                this.updatePagination(data.length);
                statusEl.style.display = 'none';
            } else {
                this.showStatus(statusEl, `Error: ${data.detail || data.message || 'Unknown error occurred'}`, 'error');
                this.displayEmptyState();
            }
        } catch (error) {
            this.showStatus(statusEl, `Connection error: ${error.message}`, 'error');
            this.displayEmptyState();
        }
    }

    displayArticles(articles) {
        const tableBody = document.getElementById('articles-table-body');

        if (!articles || articles.length === 0) {
            this.displayEmptyState();
            return;
        }

        const articlesHtml = articles.map(article => `
            <tr>
                <td>
                    <div class="article-title" title="${this.escapeHtml(article.title || 'Untitled')}">
                        ${this.escapeHtml(article.title || 'Untitled')}
                    </div>
                </td>
                <td>
                    <div class="article-url" title="${this.escapeHtml(article.url || article.source || 'No URL')}">
                        ${this.escapeHtml(article.url || article.source || 'No URL')}
                    </div>
                </td>
                <td>
                    <div class="article-content">
                        ${this.escapeHtml(article.content || article.text || 'No content')}
                    </div>
                </td>
                <td>
                    <div class="article-actions">
                        <button class="action-btn delete-btn" onclick="app.deleteArticle('${article.id || ''}')">Delete</button>
                    </div>
                </td>
            </tr>
        `).join('');

        tableBody.innerHTML = articlesHtml;
    }

    displayEmptyState() {
        const tableBody = document.getElementById('articles-table-body');
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" class="empty-state">
                    <div class="empty-state-icon">📚</div>
                    <div>No articles found in the knowledge base</div>
                    ${this.searchQuery ? '<div style="margin-top: 8px; font-size: 14px;">Try a different search term</div>' : ''}
                </td>
            </tr>
        `;
    }

    updatePagination(currentItems) {
        this.totalItems = currentItems; // This is a simplified approach - in real apps, you'd get total from API
        const maxPage = Math.ceil(this.totalItems / this.itemsPerPage);
        
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');
        const paginationInfo = document.getElementById('pagination-info');
        const pageNumbers = document.getElementById('page-numbers');

        prevBtn.disabled = this.currentPage <= 1;
        nextBtn.disabled = this.currentPage >= maxPage;

        const startItem = (this.currentPage - 1) * this.itemsPerPage + 1;
        const endItem = Math.min(startItem + currentItems - 1, this.totalItems);
        paginationInfo.textContent = `Showing ${startItem}-${endItem} of ${this.totalItems} articles`;

        // Generate page numbers (simplified)
        let pagesHtml = '';
        for (let i = Math.max(1, this.currentPage - 2); i <= Math.min(maxPage, this.currentPage + 2); i++) {
            pagesHtml += `<button class="page-number ${i === this.currentPage ? 'active' : ''}" onclick="app.goToPage(${i})">${i}</button>`;
        }
        pageNumbers.innerHTML = pagesHtml;
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadArticles();
    }

    async deleteArticle(articleId) {
        if (!articleId) return;
        
        if (!confirm('Are you sure you want to delete this article?')) {
            return;
        }

        const statusEl = document.getElementById('status-message');
        this.showStatus(statusEl, 'Deleting article...', 'loading');

        try {
            const response = await fetch(`${this.apiBaseUrl}/data/${articleId}`, {
                method: 'DELETE',
                headers: {
                    'X-API-Key': this.apiKey
                }
            });

            if (response.ok) {
                this.showStatus(statusEl, 'Article deleted successfully!', 'success');
                this.loadArticles();
            } else {
                const data = await response.json();
                this.showStatus(statusEl, `Error: ${data.detail || data.message || 'Failed to delete article'}`, 'error');
            }
        } catch (error) {
            this.showStatus(statusEl, `Connection error: ${error.message}`, 'error');
        }
    }

    showStatus(element, message, type) {
        element.textContent = message;
        element.className = `status-message ${type}`;
        element.style.display = 'block';

        if (type === 'success' || type === 'error') {
            setTimeout(() => {
                element.style.display = 'none';
            }, 5000);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

let app; // Global reference for onclick handlers

document.addEventListener('DOMContentLoaded', () => {
    app = new FAQBotUI();
});