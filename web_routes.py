# web_routes.py - Interface web para o agente IA (VERSÃO COM CORES E TEXTO ATUALIZADOS)

from flask import request, jsonify, render_template_string
from datetime import datetime
import logging
import traceback

# Importar sua função do agente
try:
    from app.agent_logic import gerar_resposta
except ImportError:
    # Função de fallback caso o módulo não exista
    def gerar_resposta(historico):
        return "Olá! Sou seu agente IA. Como posso ajudá-lo hoje?"

# Histórico de chat em memória para a interface web
web_chat_sessions = {}


def register_web_routes(app):
    """Registra as rotas da interface web no app Flask"""

    @app.route('/')
    def web_interface():
        """Serve a interface web do chat"""
        return render_template_string(WEB_CHAT_HTML)

    @app.route('/api/chat', methods=['POST'])
    def web_chat():
        """Endpoint para receber mensagens da interface web"""
        try:
            # Verificar se o request tem JSON
            if not request.is_json:
                return jsonify({'error': 'Content-Type deve ser application/json'}), 400

            data = request.get_json()
            if not data:
                return jsonify({'error': 'Dados JSON inválidos'}), 400

            user_message = data.get('message', '').strip()
            session_id = data.get('session_id', 'default')

            if not user_message:
                return jsonify({'error': 'Mensagem não pode estar vazia'}), 400

            # Log da mensagem recebida
            logging.info(f"Mensagem recebida na sessão {session_id}: {user_message[:100]}...")

            # Inicializar sessão se não existir
            if session_id not in web_chat_sessions:
                web_chat_sessions[session_id] = []

            # Adicionar mensagem do usuário ao histórico
            web_chat_sessions[session_id].append({
                'role': 'user',
                'content': user_message,
                'timestamp': datetime.now().isoformat()
            })

            # Preparar histórico no formato que sua função espera
            historico_para_agente = []
            for msg in web_chat_sessions[session_id]:
                historico_para_agente.append({
                    'role': msg['role'],
                    'content': msg['content']
                })

            # Chamar sua função do agente com tratamento de erro
            try:
                bot_response = gerar_resposta(historico_para_agente)
                if not bot_response:
                    bot_response = "Desculpe, não consegui gerar uma resposta. Tente novamente."
            except Exception as agent_error:
                logging.error(f"Erro na função do agente: {str(agent_error)}")
                bot_response = "Ocorreu um erro ao processar sua mensagem. Tente novamente."

            # Adicionar resposta do bot ao histórico
            web_chat_sessions[session_id].append({
                'role': 'assistant',
                'content': bot_response,
                'timestamp': datetime.now().isoformat()
            })

            # Manter apenas últimas 100 mensagens por sessão
            if len(web_chat_sessions[session_id]) > 100:
                web_chat_sessions[session_id] = web_chat_sessions[session_id][-100:]

            # Log da resposta
            logging.info(f"Resposta enviada para sessão {session_id}: {bot_response[:100]}...")

            return jsonify({
                'response': bot_response,
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            })

        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            logging.error(f"Erro no chat web: {error_msg}\nTraceback: {error_trace}")

            return jsonify({
                'error': f'Erro interno do servidor: {error_msg}',
                'status': 'error'
            }), 500

    @app.route('/api/history', methods=['GET'])
    def get_chat_history():
        """Retorna histórico da conversa"""
        try:
            session_id = request.args.get('session_id', 'default')

            if session_id not in web_chat_sessions:
                return jsonify({'history': [], 'total': 0})

            # Formatar histórico para o frontend
            formatted_history = []
            for msg in web_chat_sessions[session_id]:
                if msg['role'] == 'user':
                    formatted_history.append({
                        'user': msg['content'],
                        'timestamp': msg['timestamp']
                    })
                else:
                    formatted_history.append({
                        'bot': msg['content'],
                        'timestamp': msg['timestamp']
                    })

            return jsonify({
                'history': formatted_history,
                'total': len(formatted_history)
            })
        except Exception as e:
            logging.error(f"Erro ao obter histórico: {str(e)}")
            return jsonify({'error': 'Erro ao carregar histórico', 'history': [], 'total': 0}), 500

    @app.route('/api/clear', methods=['POST'])
    def clear_chat_history():
        """Limpa o histórico de conversas"""
        try:
            data = request.get_json() or {}
            session_id = data.get('session_id', 'default')

            if session_id in web_chat_sessions:
                web_chat_sessions[session_id] = []
                logging.info(f"Histórico da sessão {session_id} limpo")

            return jsonify({
                'message': 'Histórico limpo com sucesso',
                'status': 'success'
            })
        except Exception as e:
            logging.error(f"Erro ao limpar histórico: {str(e)}")
            return jsonify({'error': 'Erro ao limpar histórico', 'status': 'error'}), 500

    @app.route('/api/status', methods=['GET'])
    def get_status():
        """Endpoint de status da aplicação"""
        try:
            return jsonify({
                'status': 'online',
                'timestamp': datetime.now().isoformat(),
                'sessions_active': len(web_chat_sessions),
                'total_messages': sum(len(session) for session in web_chat_sessions.values())
            })
        except Exception as e:
            logging.error(f"Erro no status: {str(e)}")
            return jsonify({'status': 'error', 'error': str(e)}), 500

    # Endpoint adicional para debug
    @app.route('/api/debug', methods=['GET'])
    def debug_info():
        """Informações de debug da aplicação"""
        if app.debug:  # Só funciona em modo debug
            return jsonify({
                'sessions': list(web_chat_sessions.keys()),
                'total_sessions': len(web_chat_sessions),
                'flask_debug': app.debug,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': 'Debug não habilitado'}), 403


# HTML DA INTERFACE WEB - VERSÃO COM CORES E TEXTO ATUALIZADOS
WEB_CHAT_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Meu Agente IA</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🤖</text></svg>">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary-gradient: linear-gradient(135deg, #24a33c 0%, #1a7a2c 100%); /* Usando #24a33c e um tom mais escuro */
            --secondary-gradient: linear-gradient(135deg, #044cab 0%, #065979 100%); /* Cores da logo para o cabeçalho */
            --success-color: #89cc94; /* Cor de sucesso adaptada */
            --error-color: #dc3545; 
            --warning-color: #ffc107;
            --text-primary: #333;
            --text-secondary: #6c757d;
            --bg-primary: rgba(255, 255, 255, 0.95);
            --bg-secondary: #f8f9fa;
            --border-color: #ebeddc; /* Cor de borda adaptada */
            --shadow-light: 0 2px 10px rgba(0,0,0,0.1);
            --shadow-medium: 0 10px 30px rgba(0,0,0,0.15);
            --shadow-heavy: 0 25px 50px rgba(0,0,0,0.2);
            --border-radius: 20px;
            --border-radius-small: 12px;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #24a33c, #89cc94); /* Gradiente para o fundo */
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px;
        }

        .chat-container {
            width: 100%;
            max-width: 1000px;
            height: 95vh;
            background: var(--bg-primary);
            backdrop-filter: blur(15px);
            border-radius: var(--border-radius);
            box-shadow: var(--shadow-heavy);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
        }

        .chat-header {
            background: var(--secondary-gradient);
            color: white;
            padding: 25px;
            text-align: center;
            position: relative;
            box-shadow: var(--shadow-light);
        }

        .chat-title {
            font-size: 1.8em;
            font-weight: 700;
            margin-bottom: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }

        .chat-subtitle {
            font-size: 0.9em;
            opacity: 0.9;
        }

        .status-indicator {
            position: absolute;
            top: 20px;
            right: 20px;
            width: 12px;
            height: 12px;
            background: var(--success-color);
            border-radius: 50%;
            box-shadow: 0 0 10px rgba(40, 167, 69, 0.5);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.2); opacity: 0.7; }
            100% { transform: scale(1); opacity: 1; }
        }

        .chat-messages {
            flex: 1;
            padding: 25px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
            scroll-behavior: smooth;
        }

        .message {
            max-width: 80%;
            padding: 16px 22px;
            border-radius: var(--border-radius);
            word-wrap: break-word;
            line-height: 1.5;
            animation: slideIn 0.4s ease-out;
            position: relative;
            font-size: 15px;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .message.user {
            background: #24a33c; /* Cor de fundo para mensagens do usuário */
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 8px;
            box-shadow: var(--shadow-light);
        }

        .message.bot {
            background: white;
            color: var(--text-primary);
            align-self: flex-start;
            border: 1px solid var(--border-color);
            border-bottom-left-radius: 8px;
            box-shadow: var(--shadow-light);
        }

        .message.error {
            background: #fef2f2;
            color: var(--error-color);
            border: 1px solid #fecaca;
            align-self: center;
            text-align: center;
            border-radius: var(--border-radius-small);
            font-weight: 500;
        }

        .message-time {
            font-size: 11px;
            opacity: 0.7;
            margin-top: 8px;
            text-align: right;
        }

        .typing-indicator {
            display: none;
            align-self: flex-start;
            padding: 20px 22px;
            background: white;
            border-radius: var(--border-radius);
            border-bottom-left-radius: 8px;
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow-light);
        }

        .typing-dots {
            display: flex;
            gap: 6px;
            align-items: center;
        }

        .typing-dots span {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--text-secondary);
            animation: bounce 1.4s infinite ease-in-out;
        }

        .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
        .typing-dots span:nth-child(2) { animation-delay: -0.16s; }

        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }

        .chat-input-container {
            padding: 25px;
            background: rgba(248, 249, 250, 0.9);
            border-top: 1px solid var(--border-color);
        }

        .chat-input {
            display: flex;
            gap: 15px;
            align-items: flex-end;
        }

        .input-field {
            flex: 1;
            padding: 16px 20px;
            border: 2px solid var(--border-color);
            border-radius: 25px;
            font-size: 15px;
            outline: none;
            transition: all 0.3s ease;
            resize: none;
            min-height: 52px;
            max-height: 150px;
            font-family: inherit;
            line-height: 1.4;
        }

        .input-field:focus {
            border-color: #24a33c; /* Adapta a cor do foco */
            box-shadow: 0 0 0 4px rgba(36, 163, 60, 0.1);
        }

        .send-button {
            padding: 16px 28px;
            background: var(--primary-gradient);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 15px;
            font-weight: 600;
            transition: all 0.3s ease;
            min-width: 100px;
            height: 52px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .send-button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(36, 163, 60, 0.4); /* Adapta a sombra */
        }

        .send-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .status-bar {
            padding: 15px 25px;
            background: rgba(248, 249, 250, 0.9);
            border-top: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
            color: var(--text-secondary);
        }

        .clear-btn {
            color: var(--error-color);
            cursor: pointer;
            font-weight: 600;
            padding: 8px 12px;
            border-radius: 8px;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .clear-btn:hover {
            background-color: rgba(220, 53, 69, 0.1);
            color: #c82333;
        }

        .status-text {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 500;
        }

        /* Scrollbar personalizada */
        .chat-messages::-webkit-scrollbar {
            width: 8px;
        }

        .chat-messages::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 4px;
        }

        .chat-messages::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 4px;
        }

        .chat-messages::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8;
        }

        /* Loading spinner */
        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid #ffffff;
            border-top: 2px solid transparent;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Debug info */
        .debug-info {
            position: fixed;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            z-index: 1000;
            display: none;
            max-height: 300px; /* Limitar altura */
            overflow-y: auto; /* Adicionar scroll */
        }

        /* Responsividade */
        @media (max-width: 768px) {
            body {
                padding: 5px;
            }

            .chat-container {
                width: 100%;
                height: 100vh;
                border-radius: 0;
            }

            .message {
                max-width: 90%;
            }

            .chat-header {
                padding: 20px;
            }

            .chat-title {
                font-size: 1.4em;
            }

            .chat-messages {
                padding: 15px;
            }

            .chat-input-container {
                padding: 15px;
            }
        }

        @media (max-width: 480px) {
            .chat-title {
                font-size: 1.2em;
                flex-direction: column;
                gap: 8px;
            }

            .status-bar {
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }
        }

        /* Animações extras */
        .fade-in {
            animation: fadeIn 0.3s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="debug-info" id="debugInfo"></div>

    <div class="chat-container">
        <div class="chat-header">
            <div class="status-indicator"></div>
            <div class="chat-title">
                <span>🤖</span>
                <span>Meu Agente IA</span>
            </div>
            <div class="chat-subtitle">Assistente Inteligente - Automatize Mais</div> </div>

        <div class="chat-messages" id="chatMessages">
            <div class="message bot fade-in">
                👋 Olá! Sou seu agente IA inteligente. Posso ajudá-lo com diversas tarefas. Como posso ajudá-lo hoje?
            </div>
        </div>

        <div class="typing-indicator" id="typingIndicator">
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>

        <div class="chat-input-container">
            <div class="chat-input">
                <textarea id="messageInput" class="input-field" 
                          placeholder="Digite sua mensagem aqui... (Enter para enviar, Shift+Enter para nova linha)" 
                          rows="1"></textarea>
                <button id="sendButton" class="send-button">
                    <span id="sendText">Enviar</span>
                    <span id="sendIcon">📤</span>
                </button>
            </div>
        </div>

        <div class="status-bar">
            <span class="clear-btn" onclick="clearChat()">
                <span>🗑️</span>
                <span>Limpar conversa</span>
            </span>
            <span class="status-text">
                <span>⚡</span>
                <span id="statusText">Pronto</span>
            </span>
        </div>
    </div>

    <script>
        class ChatInterface {
            constructor() {
                this.chatMessages = document.getElementById('chatMessages');
                this.messageInput = document.getElementById('messageInput');
                this.sendButton = document.getElementById('sendButton');
                this.statusText = document.getElementById('statusText');
                this.typingIndicator = document.getElementById('typingIndicator');
                this.sendText = document.getElementById('sendText');
                this.sendIcon = document.getElementById('sendIcon');
                this.debugInfo = document.getElementById('debugInfo');

                // Estado interno
                this.isProcessing = false;
                this.retryCount = 0;
                this.maxRetries = 3;

                this.setupEventListeners();
                this.loadHistory();
                this.checkConnection();
                this.enableDebugMode();
            }

            setupEventListeners() {
                // Evento de clique para o botão de enviar
                this.sendButton.addEventListener('click', () => {
                    this.sendMessage();
                });

                // Evento de teclado para o campo de input
                this.messageInput.addEventListener('keydown', (e) => {
                    // Se a tecla Enter for pressionada e Shift NÃO estiver pressionado
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault(); // Impede a nova linha padrão no textarea
                        this.sendMessage(); // Envia a mensagem
                    }
                });

                // Auto-resize textarea
                this.messageInput.addEventListener('input', () => {
                    this.messageInput.style.height = 'auto';
                    this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 150) + 'px';
                });

                // Focus no input ao carregar
                setTimeout(() => {
                    this.messageInput.focus();
                }, 100);

                // Prevenir envio duplo com Ctrl+D
                document.addEventListener('keydown', (e) => {
                    if (e.ctrlKey && e.key === 'd') {
                        e.preventDefault();
                        this.toggleDebug();
                    }
                });
            }

            async sendMessage() {
                const message = this.messageInput.value.trim();
                if (!message || this.isProcessing) {
                    this.log('Tentativa de envio bloqueada: mensagem vazia ou processando');
                    return;
                }

                this.log(`Enviando mensagem: "${message}"`);

                // Adicionar mensagem do usuário
                this.addMessage(message, 'user');
                this.messageInput.value = '';
                this.messageInput.style.height = 'auto'; // Resetar altura após o envio

                // Mostrar indicador de digitação
                this.showTyping();
                this.setStatus('Processando...', '🤔');
                this.setButtonLoading(true);
                this.isProcessing = true;

                try {
                    this.log('Fazendo requisição para /api/chat');

                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        },
                        body: JSON.stringify({  
                            message: message,
                            session_id: 'default' // Usar uma session_id padrão para o frontend
                        })
                    });

                    this.log(`Resposta recebida - Status: ${response.status}`);

                    const data = await response.json();
                    this.log(`Dados da resposta:`, data);

                    this.hideTyping();

                    if (response.ok && data.status === 'success') {
                        this.addMessage(data.response, 'bot');
                        this.setStatus('Pronto', '⚡');
                        this.retryCount = 0;
                    } else {
                        const errorMsg = data.error || `Erro HTTP ${response.status}. Mensagem: ${data.message || 'Desconhecido'}`;
                        this.addMessage(`❌ ${errorMsg}`, 'error');
                        this.setStatus('Erro', '❌');
                    }

                } catch (error) {
                    this.log('Erro na requisição:', error);
                    this.hideTyping();

                    if (this.retryCount < this.maxRetries) {
                        this.retryCount++;
                        this.addMessage(`🔄 Tentativa ${this.retryCount}/${this.maxRetries}. Tentando novamente...`, 'error');
                        setTimeout(() => this.sendMessage(), 2000); // Tenta novamente após 2 segundos
                        return;
                    }

                    this.addMessage('🔌 Erro de conexão. Verifique sua internet e tente novamente.', 'error');
                    this.setStatus('Sem conexão', '🔌');
                } finally {
                    this.setButtonLoading(false);
                    this.isProcessing = false;
                    this.messageInput.focus();
                }
            }

            addMessage(content, type) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type} fade-in`;

                const contentDiv = document.createElement('div');
                contentDiv.textContent = content;
                messageDiv.appendChild(contentDiv);

                // Adicionar timestamp
                const timeDiv = document.createElement('div');
                timeDiv.className = 'message-time';
                timeDiv.textContent = new Date().toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'}); // Formato HH:MM
                messageDiv.appendChild(timeDiv);

                this.chatMessages.appendChild(messageDiv);
                this.scrollToBottom();

                this.log(`Mensagem adicionada - Tipo: ${type}, Conteúdo: ${content.substring(0, 50)}...`);
            }

            showTyping() {
                this.typingIndicator.style.display = 'block';
                this.scrollToBottom();
            }

            hideTyping() {
                this.typingIndicator.style.display = 'none';
            }

            setStatus(text, icon = '⚡') {
                this.statusText.innerHTML = `<span>${icon}</span><span>${text}</span>`;
            }

            setButtonLoading(loading) {
                this.sendButton.disabled = loading;
                if (loading) {
                    this.sendText.textContent = 'Enviando...';
                    this.sendIcon.innerHTML = '<div class="spinner"></div>';
                } else {
                    this.sendText.textContent = 'Enviar';
                    this.sendIcon.textContent = '📤';
                }
            }

            scrollToBottom() {
                setTimeout(() => {
                    this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
                }, 100);
            }

            async checkConnection() {
                try {
                    this.log('Verificando conexão...');
                    const response = await fetch('/api/status');
                    const data = await response.json();

                    if (response.ok && data.status === 'online') {
                        this.setStatus('Online', '🟢');
                        this.log('Conexão OK:', data);
                    } else {
                        this.setStatus('Instável', '🟡');
                        this.log('Conexão instável ou offline:', data);
                    }
                } catch (error) {
                    this.setStatus('Offline', '🔴');
                    this.log('Erro de conexão:', error);
                }
            }

            async loadHistory() {
                try {
                    this.log('Carregando histórico...');
                    // Adicione um timestamp para evitar cache do navegador na requisição do histórico
                    const response = await fetch(`/api/history?session_id=default&_=${new Date().getTime()}`);
                    const data = await response.json();

                    if (data.history && data.history.length > 0) {
                        this.chatMessages.innerHTML = ''; // Limpa a mensagem inicial
                        // Adiciona a mensagem de boas-vindas inicial novamente se o histórico não a tiver
                        if (!data.history.some(msg => msg.bot && msg.bot.includes('Olá! Sou seu agente IA inteligente'))) {
                            const welcomeMessage = document.createElement('div');
                            welcomeMessage.className = 'message bot fade-in';
                            welcomeMessage.innerHTML = '👋 Olá! Sou seu agente IA inteligente. Posso ajudá-lo com diversas tarefas. Como posso ajudá-lo hoje?';
                            this.chatMessages.appendChild(welcomeMessage);
                        }

                        data.history.forEach(item => {
                            if (item.user) {
                                this.addMessage(item.user, 'user');
                            }
                            if (item.bot) {
                                this.addMessage(item.bot, 'bot');
                            }
                        });

                        this.log(`Histórico carregado: ${data.history.length} mensagens`);
                    }
                } catch (error) {
                    this.log('Erro ao carregar histórico:', error);
                } finally {
                    this.scrollToBottom(); // Garante o scroll ao carregar
                }
            }

            enableDebugMode() {
                this.debugMode = window.location.search.includes('debug=true');
                if (this.debugMode) {
                    this.debugInfo.style.display = 'block';
                    this.log('Modo debug habilitado');
                }
            }

            toggleDebug() {
                this.debugMode = !this.debugMode;
                this.debugInfo.style.display = this.debugMode ? 'block' : 'none';
                this.log('Debug mode:', this.debugMode ? 'habilitado' : 'desabilitado');
                if (this.debugMode) {
                    this.debugInfo.innerHTML = ''; // Limpar logs ao ativar
                }
            }

            log(message, data = null) {
                const timestamp = new Date().toLocaleTimeString('pt-BR');
                const logMessage = `[${timestamp}] ${message}`;

                console.log(logMessage, data || '');

                if (this.debugMode && this.debugInfo) {
                    const logDiv = document.createElement('div');
                    logDiv.textContent = logMessage + (data ? JSON.stringify(data) : ''); // Incluir dados no log de debug
                    this.debugInfo.appendChild(logDiv);

                    // Manter apenas últimas 20 mensagens de debug
                    while (this.debugInfo.children.length > 20) {
                        this.debugInfo.removeChild(this.debugInfo.firstChild);
                    }

                    // Scroll para o final
                    this.debugInfo.scrollTop = this.debugInfo.scrollHeight;
                }
            }
        }

        async function clearChat() {
            if (confirm('🗑️ Tem certeza que deseja limpar toda a conversa?\\n\\nEsta ação não pode ser desfeita.')) {
                try {
                    console.log('Limpando conversa...');

                    const response = await fetch('/api/clear', { 
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ session_id: 'default' })
                    });

                    const data = await response.json();
                    console.log('Resposta do clear:', data);

                    if (response.ok && data.status === 'success') {
                        document.getElementById('chatMessages').innerHTML = 
                            '<div class="message bot fade-in">👋 Olá! Sou seu agente IA inteligente. Posso ajudá-lo com diversas tarefas. Como posso ajudá-lo hoje?</div>';
                        document.getElementById('statusText').innerHTML = '<span>✅</span><span>Conversa limpa</span>';
                        // Recarrega o histórico após a limpeza para ter a mensagem inicial
                        if (window.chatInterface) {
                            window.chatInterface.scrollToBottom();
                        }
                    } else {
                        document.getElementById('statusText').innerHTML = '<span>❌</span><span>Erro ao limpar</span>';
                    }
                } catch (error) {
                    console.error('Erro ao limpar:', error);
                    document.getElementById('statusText').innerHTML = '<span>🔌</span><span>Erro de conexão</span>';
                }
            }
        }

        // Função para testar a conexão
        async function testConnection() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                console.log('Status da conexão:', data);
                alert(`Status: ${data.status}\\nSessões ativas: ${data.sessions_active}\\nMensagens totais: ${data.total_messages || 0}`);
            } catch (error) {
                console.error('Erro no teste:', error);
                alert('Erro ao testar conexão: ' + error.message);
            }
        }

        // Função para testar envio de mensagem
        async function testMessage() {
            try {
                const testMsg = 'Teste de mensagem - ' + new Date().toLocaleTimeString();
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: testMsg,
                        session_id: 'test_debug' // Usar uma sessão diferente para o teste
                    })
                });

                const data = await response.json();
                console.log('Teste de mensagem:', data);
                alert('Teste enviado com sucesso!\\nResposta: ' + data.response);
            } catch (error) {
                console.error('Erro no teste:', error);
                alert('Erro no teste: ' + error.message);
            }
        }

        // Adicionar funções de teste ao console
        window.testConnection = testConnection;
        window.testMessage = testMessage;
        window.clearChat = clearChat; // Tornar clearChat global para onclick no HTML

        // Inicializar interface quando página carregar
        document.addEventListener('DOMContentLoaded', () => {
            console.log('Inicializando interface do chat...');
            window.chatInterface = new ChatInterface();

            // Instruções no console
            console.log('🤖 Chat Interface carregada!');
            console.log('💡 Comandos disponíveis:');
            console.log('    - testConnection(): Testa conexão com API');
            console.log('    - testMessage(): Envia mensagem de teste');
            console.log('    - Ctrl+D: Alternar modo debug');
            console.log('    - ?debug=true na URL: Habilitar debug');
        });

        // Tratamento de erros globais
        window.addEventListener('error', (event) => {
            console.error('Erro global:', event.error);
            if (window.chatInterface) {
                window.chatInterface.log('Erro JavaScript:', event.error.message);
            }
        });

        // Tratamento de erros de promessas não tratadas
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Promise rejeitada:', event.reason);
            if (window.chatInterface) {
                window.chatInterface.log('Promise rejeitada:', event.reason);
            }
        });
    </script>
</body>
</html>
"""