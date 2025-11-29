import streamlit as st
import pandas as pd
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="FINSIGHT - AI Financial Companion",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

# Load data function
@st.cache_data
def load_data():
    """Load all CSV datasets"""
    try:
        data = {
            'users': pd.read_csv('data/finsight_users.csv'),
            'transactions': pd.read_csv('data/finsight_transactions.csv'),
            'investments': pd.read_csv('data/finsight_investments.csv'),
            'calendar_events': pd.read_csv('data/finsight_calendar_events.csv'),
            'group_expenses': pd.read_csv('data/finsight_group_expenses.csv'),
            'user_goals': pd.read_csv('data/finsight_user_goals.csv')
        }
        return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Load data
DATA = load_data()

def logout():
    """Logout function"""
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.rerun()

def login_page():
    """Login page with user selection"""
    st.markdown('<h1 class="main-header">🚀 Welcome to FINSIGHT</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Your AI-Powered Financial Companion</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("🔐 Select Your Account")
        
        if DATA is not None and 'users' in DATA:
            users_df = DATA['users']
            
            for idx, user in users_df.iterrows():
                with st.container():
                    col_a, col_b = st.columns([3, 1])
                    
                    with col_a:
                        st.markdown(f"""
                        <div style="background: #f0f2f6; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                            <h3 style="margin: 0; color: #1f77b4;">👤 {user['name']}</h3>
                            <p style="margin: 0.5rem 0 0 0; color: #666;">
                                <strong>ID:</strong> {user['user_id']} | 
                                <strong>Salary:</strong> ₹{user['monthly_salary']:,.0f} | 
                                <strong>Type:</strong> {user['spending_personality'].title()}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_b:
                        if st.button(f"Login", key=f"login_{user['user_id']}", use_container_width=True):
                            st.session_state.logged_in = True
                            st.session_state.user_id = user['user_id']
                            st.session_state.user_name = user['name']
                            st.rerun()
        else:
            st.error("Unable to load user data. Please check if CSV files exist.")

def main_app():
    """Main application after login"""
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user_name}")
        st.markdown(f"**ID:** {st.session_state.user_id}")
        st.markdown("---")
        
        # Navigation - ADDED "💰 Group Investment"
        page = st.radio(
            "Navigation",
            ["📊 Dashboard", "💬 AI Chatbot", "📅 Calendar", "💎 Investments", "💰 Group Investment", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            logout()
    
    # Page routing - ADDED GROUP INVESTMENT ROUTE
    if page == "📊 Dashboard":
        from dashboard import render_dashboard
        render_dashboard(st.session_state.user_id, DATA)
    elif page == "💬 AI Chatbot":
        from chatbot_ui import render_chatbot
        render_chatbot(st.session_state.user_id)
    elif page == "📅 Calendar":
        from calendar_page import render_calendar
        render_calendar(st.session_state.user_id, DATA)
    elif page == "💎 Investments":
        from investment_page import render_investment_page
        render_investment_page(st.session_state.user_id, DATA)
    # elif page == "👥 Group Split":
    #     from group_split_page import render_group_split_page
    #     render_group_split_page(st.session_state.user_id, DATA)
    elif page == "💰 Group Investment":
        from group_investment_page import render_group_investment_page
        render_group_investment_page(st.session_state.user_id, DATA)
    elif page == "⚙️ Settings":
        st.title("⚙️ Settings")
        st.info("Settings page - Coming soon!")

# Main execution
if __name__ == "__main__":
    if not st.session_state.logged_in:
        login_page()
    else:
        main_app()