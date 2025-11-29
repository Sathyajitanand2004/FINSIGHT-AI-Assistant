import streamlit as st
import os
from datetime import datetime
from chatbot import build_agent_graph, DATA
from langchain_core.messages import HumanMessage, AIMessage

def render_chatbot(user_id):
    """Render ChatGPT-like chatbot interface"""
    
    # Custom CSS for chat interface
    st.markdown("""
        <style>
        .chat-container {
            height: 60vh;
            overflow-y: auto;
            padding: 1rem;
            border: 1px solid #ddd;
            border-radius: 10px;
            background-color: #f9f9f9;
            margin-bottom: 1rem;
        }
        .user-message {
            background-color: #007bff;
            color: white;
            padding: 0.8rem 1rem;
            border-radius: 15px 15px 0 15px;
            margin: 0.5rem 0;
            margin-left: 20%;
            text-align: right;
        }
        .ai-message {
            background-color: #e9ecef;
            color: #333;
            padding: 0.8rem 1rem;
            border-radius: 15px 15px 15px 0;
            margin: 0.5rem 0;
            margin-right: 20%;
        }
        .timestamp {
            font-size: 0.7rem;
            color: #666;
            margin-top: 0.3rem;
        }
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            text-align: center;
        }
        .stTextInput > div > div > input {
            border-radius: 20px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
        <div class="chat-header">
            <h1 style="margin: 0;">💬 FINSIGHT AI Assistant</h1>
            <p style="margin: 0.5rem 0 0 0;">Your intelligent financial companion</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for chat
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'agent_graph' not in st.session_state:
        st.session_state.agent_graph = build_agent_graph()
    
    # Sidebar with suggestions
    with st.sidebar:
        st.markdown("### 💡 Try asking:")
        suggestions = [
            "What's my spending by category?",
            "Show my highest spending category",
            "What's my monthly spending?",
            "Show my investment portfolio",
            "What are my upcoming events?",
            "Show my spending trends",
            "What's my savings rate?",
            "Show group expenses summary",
            "What are my financial goals?",
            "Show me my profile"
        ]
        
        for suggestion in suggestions:
            if st.button(suggestion, key=f"suggest_{suggestion}", use_container_width=True):
                st.session_state.user_input = suggestion
                st.rerun()
        
        st.markdown("---")
        
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    # Chat display area
    chat_container = st.container()
    
    with chat_container:
        if len(st.session_state.chat_history) == 0:
            st.info("👋 Hello! I'm your FINSIGHT AI assistant. Ask me anything about your finances!")
        else:
            # Display chat history
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.markdown(f"""
                        <div class="user-message">
                            <strong>You:</strong><br>{message['content']}
                            <div class="timestamp">{message['timestamp']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="ai-message">
                            <strong>🤖 FINSIGHT:</strong><br>{message['content']}
                            <div class="timestamp">{message['timestamp']}</div>
                        </div>
                    """, unsafe_allow_html=True)
    
    # Input area at bottom
    st.markdown("---")
    
    col1, col2 = st.columns([6, 1])
    
    with col1:
        user_input = st.text_input(
            "Type your message...",
            key="chat_input",
            placeholder="Ask me about your finances...",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("Send 📤", use_container_width=True)
    
    # Check if there's input from sidebar suggestions
    if 'user_input' in st.session_state and st.session_state.user_input:
        user_input = st.session_state.user_input
        st.session_state.user_input = None
        send_button = True
    
    # Process input
    if send_button and user_input:
        # Add user message to history
        timestamp = datetime.now().strftime("%I:%M %p")
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input,
            'timestamp': timestamp
        })
        
        # Create messages list for agent
        messages = []
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                messages.append(HumanMessage(content=msg['content']))
            else:
                messages.append(AIMessage(content=msg['content']))
        
        # Show spinner while processing
        with st.spinner("🤔 Thinking..."):
            try:
                # Run agent
                state = {
                    "messages": messages,
                    "user_id": user_id
                }
                
                result = st.session_state.agent_graph.invoke(state)
                
                # Extract AI response
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    ai_response = last_message.content
                    
                    # Add AI response to history
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': ai_response,
                        'timestamp': datetime.now().strftime("%I:%M %p")
                    })
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': error_msg,
                    'timestamp': datetime.now().strftime("%I:%M %p")
                })
        
        # Rerun to show new messages
        st.rerun()
    
    # Display some stats in expander
    with st.expander("📊 Chat Statistics"):
        total_messages = len(st.session_state.chat_history)
        user_messages = len([m for m in st.session_state.chat_history if m['role'] == 'user'])
        ai_messages = len([m for m in st.session_state.chat_history if m['role'] == 'assistant'])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Messages", total_messages)
        col2.metric("Your Messages", user_messages)
        col3.metric("AI Responses", ai_messages)