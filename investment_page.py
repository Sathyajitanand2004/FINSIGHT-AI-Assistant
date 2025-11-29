import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from pathlib import Path
from investment_advisor import InvestmentRecommendationEngine, calculate_available_savings
import os
import json

# Ensure models directory exists
HISTORY_FILE = "models/investment_suggestion_history.csv"
Path("models").mkdir(parents=True, exist_ok=True)

def save_recommendation_to_history(user_id, user_data, portfolio):
    """Save investment recommendation to CSV history"""
    try:
        # Prepare recommendation data
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create row for each investment in portfolio
        history_records = []
        
        for inv in portfolio:
            record = {
                'user_id': user_id,
                'timestamp': timestamp,
                'date': datetime.now().strftime("%Y-%m-%d"),
                'time': datetime.now().strftime("%H:%M:%S"),
                'user_name': user_data['name'],
                'risk_tolerance': user_data['risk_tolerance'],
                'total_capital': user_data['available_savings'],
                'goal_months': user_data['goal_deadline_months'],
                'investment_name': inv['investment'],
                'allocated_amount': inv['amount'],
                'allocation_percentage': inv['percentage'],
                'risk_level': inv['risk_level'],
                'expected_return_rate': inv['expected_return'],
                'expected_annual_gain': inv['amount'] * inv['expected_return'],
                'suitability_score': inv['score']
            }
            history_records.append(record)
        
        # Create DataFrame
        new_df = pd.DataFrame(history_records)
        
        # Append to existing file or create new
        if os.path.exists(HISTORY_FILE):
            existing_df = pd.read_csv(HISTORY_FILE)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df.to_csv(HISTORY_FILE, index=False)
        else:
            new_df.to_csv(HISTORY_FILE, index=False)
        
        return True
    except Exception as e:
        st.error(f"Error saving recommendation: {e}")
        return False

def load_user_recommendation_history(user_id):
    """Load recommendation history for specific user"""
    try:
        if os.path.exists(HISTORY_FILE):
            df = pd.read_csv(HISTORY_FILE)
            user_history = df[df['user_id'] == user_id].copy()
            return user_history
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading history: {e}")
        return pd.DataFrame()

def get_unique_recommendations(user_id):
    """Get list of unique recommendation timestamps for user"""
    try:
        if os.path.exists(HISTORY_FILE):
            df = pd.read_csv(HISTORY_FILE)
            user_df = df[df['user_id'] == user_id]
            return user_df['timestamp'].unique()
        else:
            return []
    except Exception as e:
        return []

def render_investment_page(user_id, DATA):
    """Render investment recommendation page with history"""
    
    st.markdown('<h1 class="main-header">💎 AI Investment Advisor</h1>', unsafe_allow_html=True)
    st.markdown("Get personalized investment recommendations based on your financial profile and market risk")
    
    # Custom CSS
    st.markdown("""
    <style>
    .investment-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    .metric-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .recommendation-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 5px solid #667eea;
    }
    .history-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #28a745;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if DATA is None:
        st.error("⚠️ Unable to load data. Please check CSV files.")
        return
    
    # Get user information
    user_info = DATA['users'][DATA['users']['user_id'] == user_id].iloc[0]
    
    # Calculate available savings
    available_savings = calculate_available_savings(user_id, DATA)
    
    # Tab navigation
    tab1, tab2 = st.tabs(["🎯 Get New Recommendation", "📜 Recommendation History"])
    
    # ============================================================================
    # TAB 1: NEW RECOMMENDATION
    # ============================================================================
    with tab1:
        st.markdown("---")
        
        # Display current financial status
        st.subheader("📊 Your Financial Profile")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Monthly Salary", f"₹{user_info['monthly_salary']:,.0f}")
        with col2:
            st.metric("Savings Rate", f"{user_info['savings_rate']*100:.0f}%")
        with col3:
            st.metric("Risk Profile", user_info['risk_tolerance'].title())
        with col4:
            st.metric("Available Savings", f"₹{available_savings:,.0f}")
        
        st.markdown("---")
        
        # Investment Recommendation Form
        st.subheader("🎯 Get Personalized Investment Recommendations")
        
        with st.form("investment_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Investment Preferences")
                
                risk_tolerance = st.selectbox(
                    "Risk Tolerance",
                    options=['low', 'medium', 'high'],
                    index=['low', 'medium', 'high'].index(user_info['risk_tolerance']),
                    help="Your comfort level with investment risk"
                )
                
                custom_savings = st.number_input(
                    "Available Capital for Investment (₹)",
                    min_value=5000,
                    max_value=10000000,
                    value=int(available_savings),
                    step=5000,
                    help="Amount you want to invest"
                )
            
            with col2:
                st.markdown("#### Investment Goals")
                
                goal_deadline_months = st.slider(
                    "Investment Horizon (months)",
                    min_value=6,
                    max_value=240,
                    value=36,
                    step=6,
                    help="How long do you plan to invest?"
                )
                
                goal_name = st.text_input(
                    "Investment Goal (Optional)",
                    placeholder="e.g., House Down Payment, Retirement",
                    help="What are you investing for?"
                )
            
            # Market risk indicator
            st.markdown("---")
            st.markdown("#### 📈 Current Market Conditions")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info("**Equity Market:** Moderate Volatility")
            with col2:
                st.success("**Debt Market:** Stable")
            with col3:
                st.warning("**Gold:** High Demand")
            
            submit_button = st.form_submit_button("🎯 Generate Investment Recommendations", use_container_width=True)
        
        # Generate recommendations on submit
        if submit_button:
            with st.spinner("🤖 AI is analyzing market conditions and your profile..."):
                # Prepare user data
                user_data = {
                    'name': user_info['name'],
                    'risk_tolerance': risk_tolerance,
                    'available_savings': custom_savings,
                    'monthly_income': user_info['monthly_salary'],
                    'goal_deadline_months': goal_deadline_months,
                    'spending_personality': user_info['spending_personality']
                }
                
                # Get recommendations
                engine = InvestmentRecommendationEngine()
                portfolio = engine.recommend_portfolio(user_data)
                
                # Save to history
                if save_recommendation_to_history(user_id, user_data, portfolio):
                    st.success("✅ Recommendation saved to history!")
                
                # Store in session state
                st.session_state.portfolio = portfolio
                st.session_state.user_data = user_data
                st.success("✅ Investment recommendations generated successfully!")
        
        # Display recommendations if available
        if 'portfolio' in st.session_state and st.session_state.portfolio:
            portfolio = st.session_state.portfolio
            user_data = st.session_state.user_data
            
            st.markdown("---")
            st.markdown("## 🎯 Your Personalized Investment Portfolio")
            
            # Portfolio Summary
            total_expected_return = sum([inv['amount'] * inv['expected_return'] for inv in portfolio])
            weighted_risk = sum([inv['risk_level'] * (inv['percentage'] / 100) for inv in portfolio])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Capital", f"₹{user_data['available_savings']:,.0f}")
            with col2:
                st.metric("Expected Annual Return", f"₹{total_expected_return:,.0f}")
            with col3:
                st.metric("Return Rate", f"{(total_expected_return/user_data['available_savings'])*100:.2f}%")
            with col4:
                st.metric("Portfolio Risk", f"{weighted_risk:.1f}/5")
            
            # Portfolio Visualization
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 Portfolio Allocation")
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=[inv['investment'] for inv in portfolio],
                    values=[inv['percentage'] for inv in portfolio],
                    hole=0.4,
                    marker=dict(colors=px.colors.qualitative.Set3)
                )])
                fig_pie.update_layout(title="Investment Distribution", height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.markdown("### 📈 Risk-Return Analysis")
                
                fig_scatter = go.Figure()
                fig_scatter.add_trace(go.Scatter(
                    x=[inv['risk_level'] for inv in portfolio],
                    y=[inv['expected_return']*100 for inv in portfolio],
                    mode='markers+text',
                    text=[inv['investment'] for inv in portfolio],
                    textposition="top center",
                    marker=dict(
                        size=[inv['percentage'] for inv in portfolio],
                        color=[inv['percentage'] for inv in portfolio],
                        colorscale='Viridis',
                        showscale=True
                    )
                ))
                fig_scatter.update_layout(
                    title="Risk vs Return Profile",
                    xaxis_title="Risk Level",
                    yaxis_title="Expected Return (%)",
                    height=400
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Detailed Recommendations Table
            st.markdown("---")
            st.markdown("### 💼 Detailed Investment Breakdown")
            
            # Create detailed table
            table_data = []
            for inv in portfolio:
                table_data.append({
                    'Investment': inv['investment'],
                    'Amount (₹)': f"₹{inv['amount']:,.0f}",
                    'Allocation (%)': f"{inv['percentage']:.1f}%",
                    'Risk Level': f"{inv['risk_level']}/5",
                    'Expected Return': f"{inv['expected_return']*100:.1f}%",
                    'Annual Gain (₹)': f"₹{inv['amount'] * inv['expected_return']:,.0f}",
                    'Score': f"{inv['score']:.3f}"
                })
            
            df_table = pd.DataFrame(table_data)
            st.dataframe(df_table, use_container_width=True, hide_index=True)
            
            # Export Options
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                csv = df_table.to_csv(index=False)
                st.download_button(
                    label="📥 Download Portfolio Report (CSV)",
                    data=csv,
                    file_name=f"investment_portfolio_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                if st.button("🔄 Start Fresh", use_container_width=True):
                    del st.session_state.portfolio
                    del st.session_state.user_data
                    st.rerun()
    
    # ============================================================================
    # TAB 2: RECOMMENDATION HISTORY
    # ============================================================================
    with tab2:
        st.markdown("---")
        st.subheader("📜 Your Investment Recommendation History")
        
        # Load user history
        user_history = load_user_recommendation_history(user_id)
        
        if len(user_history) == 0:
            st.info("No recommendation history found. Generate your first recommendation in the 'Get New Recommendation' tab!")
        else:
            # Get unique timestamps
            unique_timestamps = user_history['timestamp'].unique()
            
            st.markdown(f"**Total Recommendations:** {len(unique_timestamps)}")
            
            # Filter options
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_timestamp = st.selectbox(
                    "Select Recommendation to View",
                    options=sorted(unique_timestamps, reverse=True),
                    format_func=lambda x: f"📅 {x}"
                )
            with col2:
                if st.button("🗑️ Clear History", use_container_width=True):
                    if os.path.exists(HISTORY_FILE):
                        df = pd.read_csv(HISTORY_FILE)
                        df = df[df['user_id'] != user_id]
                        df.to_csv(HISTORY_FILE, index=False)
                        st.success("History cleared!")
                        st.rerun()
            
            if selected_timestamp:
                # Filter data for selected timestamp
                selected_data = user_history[user_history['timestamp'] == selected_timestamp].copy()
                
                st.markdown("---")
                st.markdown(f"### 📊 Recommendation from {selected_timestamp}")
                
                # Display summary metrics
                total_capital = selected_data['total_capital'].iloc[0]
                total_gain = selected_data['expected_annual_gain'].sum()
                risk_profile = selected_data['risk_tolerance'].iloc[0]
                goal_months = selected_data['goal_months'].iloc[0]
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Capital", f"₹{total_capital:,.0f}")
                with col2:
                    st.metric("Expected Return", f"₹{total_gain:,.0f}")
                with col3:
                    st.metric("Return Rate", f"{(total_gain/total_capital)*100:.2f}%")
                with col4:
                    st.metric("Risk Profile", risk_profile.title())
                
                st.markdown("---")
                
                # Display portfolio table
                st.markdown("#### 💼 Portfolio Breakdown")
                
                display_df = selected_data[[
                    'investment_name', 'allocated_amount', 'allocation_percentage',
                    'risk_level', 'expected_return_rate', 'expected_annual_gain', 'suitability_score'
                ]].copy()
                
                display_df.columns = [
                    'Investment', 'Amount (₹)', 'Allocation (%)',
                    'Risk', 'Return Rate', 'Annual Gain (₹)', 'Score'
                ]
                
                # Format columns
                display_df['Amount (₹)'] = display_df['Amount (₹)'].apply(lambda x: f"₹{x:,.0f}")
                display_df['Allocation (%)'] = display_df['Allocation (%)'].apply(lambda x: f"{x:.1f}%")
                display_df['Risk'] = display_df['Risk'].apply(lambda x: f"{x}/5")
                display_df['Return Rate'] = display_df['Return Rate'].apply(lambda x: f"{x*100:.1f}%")
                display_df['Annual Gain (₹)'] = display_df['Annual Gain (₹)'].apply(lambda x: f"₹{x:,.0f}")
                display_df['Score'] = display_df['Score'].apply(lambda x: f"{x:.3f}")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Visualization of historical recommendation
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📊 Allocation Distribution")
                    fig = go.Figure(data=[go.Pie(
                        labels=selected_data['investment_name'],
                        values=selected_data['allocation_percentage'],
                        hole=0.3
                    )])
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("#### 📈 Risk-Return Profile")
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=selected_data['investment_name'],
                        y=selected_data['expected_return_rate']*100,
                        marker_color=selected_data['risk_level'],
                        marker_colorscale='RdYlGn_r',
                        text=[f"{r:.1f}%" for r in selected_data['expected_return_rate']*100],
                        textposition='auto'
                    ))
                    fig.update_layout(
                        xaxis_title="Investment",
                        yaxis_title="Expected Return (%)",
                        height=350,
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Download historical recommendation
                st.markdown("---")
                csv_download = selected_data.to_csv(index=False)
                st.download_button(
                    label="📥 Download This Recommendation (CSV)",
                    data=csv_download,
                    file_name=f"investment_history_{user_id}_{selected_timestamp.replace(':', '').replace(' ', '_')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            # All history comparison
            st.markdown("---")
            st.markdown("### 📈 Historical Trends")
            
            if len(unique_timestamps) > 1:
                # Group by timestamp and calculate metrics
                history_trends = user_history.groupby('timestamp').agg({
                    'total_capital': 'first',
                    'expected_annual_gain': 'sum'
                }).reset_index()
                
                history_trends['return_rate'] = (history_trends['expected_annual_gain'] / history_trends['total_capital']) * 100
                
                # Line chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=history_trends['timestamp'],
                    y=history_trends['return_rate'],
                    mode='lines+markers',
                    name='Portfolio Return Rate',
                    line=dict(color='#667eea', width=3),
                    marker=dict(size=10)
                ))
                fig.update_layout(
                    title="Portfolio Return Rate Over Time",
                    xaxis_title="Date",
                    yaxis_title="Return Rate (%)",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Generate more recommendations to see trend analysis!")
