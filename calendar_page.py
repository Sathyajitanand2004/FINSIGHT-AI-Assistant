import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
import plotly.graph_objects as go
from calendar import monthrange
from calendar_model_load import load_ml_models, predict_event_expense


# Custom CSS for interactive calendar
def apply_calendar_css():
    st.markdown("""
    <style>
    .calendar-day-clickable {
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        margin: 2px;
        min-height: 80px;
        border: 2px solid #e0e0e0;
    }
    .calendar-day-clickable:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        border-color: #667eea;
    }
    .prediction-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin: 1.5rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        animation: slideIn 0.5s ease;
    }
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .metric-box {
        background: rgba(255,255,255,0.15);
        padding: 1.2rem;
        border-radius: 10px;
        margin: 0.8rem 0;
        backdrop-filter: blur(10px);
        border-left: 4px solid #fff;
    }
    .recommendation-item {
        background: rgba(255,255,255,0.2);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.6rem 0;
        border-left: 4px solid #ffd700;
        transition: transform 0.2s;
    }
    .recommendation-item:hover {
        transform: translateX(5px);
    }
    .event-form-container {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        border: 2px dashed #667eea;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)


def render_calendar(user_id, DATA):
    """Render ML-powered interactive calendar with event marking"""
    
    apply_calendar_css()
    
    st.markdown('<h1 class="main-header">📅 AI-Powered Financial Calendar</h1>', unsafe_allow_html=True)
    
    # Load ML models (cached)
    models = load_ml_models()
    if models is None:
        st.error("⚠️ Failed to load ML models. Please train models first by running the training script.")
        return
    else:
        st.success("✅ AI Models Loaded Successfully")
    
    if DATA is None:
        st.error("⚠️ Data not loaded!")
        return
    
    # Initialize session state
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = None
    if 'event_predictions' not in st.session_state:
        st.session_state.event_predictions = {}
    if 'calendar_year' not in st.session_state:
        st.session_state.calendar_year = datetime.now().year
    if 'calendar_month' not in st.session_state:
        st.session_state.calendar_month = datetime.now().month
    
    # Filter user events
    user_events = DATA['calendar_events'][DATA['calendar_events']['user_id'] == user_id].copy()
    user_events['event_date'] = pd.to_datetime(user_events['event_date'])
    
    # Calendar controls
    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
    
    with col1:
        years = sorted(user_events['year'].unique().tolist())
        if not years or st.session_state.calendar_year not in years:
            years.append(st.session_state.calendar_year)
            years.sort()
        
        year_index = years.index(st.session_state.calendar_year) if st.session_state.calendar_year in years else len(years)-1
        selected_year = st.selectbox("Year", years, index=year_index, key='year_select')
        st.session_state.calendar_year = selected_year
    
    with col2:
        selected_month = st.selectbox("Month", range(1, 13), 
                                     format_func=lambda x: calendar.month_name[x],
                                     index=st.session_state.calendar_month - 1,
                                     key='month_select')
        st.session_state.calendar_month = selected_month
    
    with col3:
        if st.button("⬅️ Prev"):
            if st.session_state.calendar_month == 1:
                st.session_state.calendar_month = 12
                st.session_state.calendar_year -= 1
            else:
                st.session_state.calendar_month -= 1
            st.rerun()
    
    with col4:
        if st.button("Next ➡️"):
            if st.session_state.calendar_month == 12:
                st.session_state.calendar_month = 1
                st.session_state.calendar_year += 1
            else:
                st.session_state.calendar_month += 1
            st.rerun()
    
    with col5:
        if st.button("📍 Today"):
            st.session_state.calendar_month = datetime.now().month
            st.session_state.calendar_year = datetime.now().year
            st.session_state.selected_date = None
            st.rerun()
    
    st.markdown("---")
    
    # Add new event section
    with st.expander("➕ **Mark New Event on Calendar**", expanded=False):
        st.markdown('<div class="event-form-container">', unsafe_allow_html=True)
        
        with st.form("add_event_form", clear_on_submit=False):
            st.subheader("📝 Event Details")
            
            col1, col2 = st.columns(2)
            with col1:
                event_name = st.text_input("Event Name *", placeholder="e.g., Trip to Goa", key="event_name_input")
                event_date = st.date_input("Event Date *", 
                                          value=datetime(st.session_state.calendar_year, 
                                                       st.session_state.calendar_month, 1),
                                          key="event_date_input")
            with col2:
                event_type = st.selectbox("Event Type *", 
                                         ['Bill', 'Celebration', 'Travel', 'Healthcare', 
                                          'Shopping', 'Education', 'Maintenance', 'Financial'],
                                         key="event_type_input")
                predicted_expense = st.number_input("Your Estimated Expense (₹) *", 
                                                   min_value=100, 
                                                   max_value=1000000,
                                                   value=5000, 
                                                   step=500,
                                                   key="expense_input",
                                                   help="Enter a realistic amount between ₹100 and ₹10,00,000")
            
            st.markdown("**Required fields***")
            st.info("💡 The AI will compare your estimate with predicted actual cost and show risk level")
            
            submit_event = st.form_submit_button("🎯 Get AI Prediction & Mark Event", use_container_width=True)
            
            if submit_event:
                if not event_name:
                    st.error("❌ Please enter an event name!")
                elif predicted_expense < 100 or predicted_expense > 1000000:
                    st.error("❌ Please enter a realistic expense between ₹100 and ₹10,00,000")
                else:
                    event_year = event_date.year
                    event_month = event_date.month
                    
                    with st.spinner("🤖 AI is analyzing your event..."):
                        result = predict_event_expense(
                            models, user_id, event_name, event_type, 
                            event_year, event_month, predicted_expense
                        )
                    
                    if result['success']:
                        date_key = event_date.strftime("%Y-%m-%d")
                        st.session_state.event_predictions[date_key] = result
                        st.session_state.selected_date = event_date
                        
                        st.success(f"✅ Event '{event_name}' marked successfully!")
                        st.info("📊 Scroll down to see AI predictions and risk analysis")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ Prediction failed: {result.get('error', 'Unknown error')}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Display calendar
    st.subheader(f"📆 {calendar.month_name[st.session_state.calendar_month]} {st.session_state.calendar_year}")
    
    # Filter events for selected month
    month_events = user_events[
        (user_events['year'] == st.session_state.calendar_year) & 
        (user_events['month'] == st.session_state.calendar_month)
    ].sort_values('event_date')
    
    # Get calendar grid
    cal = calendar.monthcalendar(st.session_state.calendar_year, st.session_state.calendar_month)
    
    # Day headers
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    cols = st.columns(7)
    for i, day in enumerate(days):
        cols[i].markdown(f"<div style='text-align: center; font-weight: bold; padding: 10px;'>{day}</div>", 
                        unsafe_allow_html=True)
    
    # Render calendar days with BUDGET ACCURACY color logic
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown("")
            else:
                day_date = datetime(st.session_state.calendar_year, st.session_state.calendar_month, day)
                date_key = day_date.strftime("%Y-%m-%d")
                
                has_prediction = date_key in st.session_state.event_predictions
                day_events = month_events[month_events['event_date'].dt.day == day]
                
                if has_prediction:
                    pred = st.session_state.event_predictions[date_key]
                    
                    # Get amounts
                    try:
                        ai_expense = float(pred['ai_predicted_actual_expense'])
                        user_estimate = float(pred['user_estimated_expense'])
                    except (ValueError, KeyError):
                        ai_expense = 0
                        user_estimate = 0
                    
                    event_name = pred.get('event_name', 'Unknown Event')
                    
                    # Calculate budget difference
                    budget_diff = user_estimate - ai_expense
                    
                    # FIXED: Color based on budget accuracy
                    if user_estimate < ai_expense:
                        # User underestimated - GREEN (good, budget is safe)
                        bg_color = '#51cf66'
                        text_color = '#000000'
                        border_color = '#2b8a3e'
                        risk_level = 'Low Risk'
                        risk_icon = '✅'
                    elif abs(budget_diff) <= 1000:
                        # Close to AI prediction (±₹1000) - YELLOW (accurate)
                        bg_color = '#ffd93d'
                        text_color = '#000000'
                        border_color = '#fab005'
                        risk_level = 'Accurate'
                        risk_icon = '⚠️'
                    else:  # user_estimate > ai_expense + 1000
                        # User overestimated - RED (high risk of overspending)
                        bg_color = '#ff6b6b'
                        text_color = '#ffffff'
                        border_color = '#c92a2a'
                        risk_level = 'High Risk'
                        risk_icon = '🔴'
                    
                    display_html = f"""
                        <div style="background: linear-gradient(135deg, {bg_color} 0%, {bg_color}dd 100%); 
                                    padding: 12px; border-radius: 10px; 
                                    text-align: center; min-height: 85px; 
                                    border: 3px solid {border_color};
                                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                            <div style="font-size: 1.5rem; font-weight: 900; 
                                        color: {text_color}; 
                                        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{day}</div>
                            <div style="font-size: 0.7rem; margin-top: 4px; 
                                        color: {text_color}; font-weight: 700;
                                        text-shadow: 1px 1px 3px rgba(0,0,0,0.3);">
                                🎯 {event_name[:12]}
                            </div>
                            <div style="font-size: 0.8rem; font-weight: 900; 
                                        color: {text_color}; margin-top: 3px;
                                        text-shadow: 1px 1px 3px rgba(0,0,0,0.3);">
                                AI: ₹{ai_expense:,.0f}
                            </div>
                            <div style="font-size: 0.65rem; color: {text_color}; 
                                        font-weight: 600; opacity: 0.95;">{risk_icon} {risk_level}</div>
                        </div>
                    """
                    cols[i].markdown(display_html, unsafe_allow_html=True)
                    
                    if cols[i].button("📊 Details", key=f"btn_{date_key}", use_container_width=True):
                        st.session_state.selected_date = day_date
                        st.rerun()
                
                elif len(day_events) > 0:
                    total_expense = day_events['predicted_expense'].sum()
                    event_count = len(day_events)
                    
                    # For existing events without AI prediction, use absolute amount
                    if total_expense > 15000:
                        bg_color = '#ff6b6b'
                        text_color = '#ffffff'
                        border_color = '#c92a2a'
                    elif total_expense > 5000:
                        bg_color = '#ffd93d'
                        text_color = '#000000'
                        border_color = '#fab005'
                    else:
                        bg_color = '#51cf66'
                        text_color = '#000000'
                        border_color = '#2b8a3e'
                    
                    display_html = f"""
                        <div style="background-color: {bg_color}; padding: 12px; 
                                    border-radius: 10px; text-align: center; 
                                    min-height: 80px; border: 2px solid {border_color};
                                    box-shadow: 0 2px 6px rgba(0,0,0,0.15);">
                            <strong style="font-size: 1.4rem; color: {text_color}; 
                                         text-shadow: 1px 1px 3px rgba(0,0,0,0.2);">{day}</strong><br>
                            <small style="color: {text_color}; font-weight: 700; 
                                        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);">
                                {event_count} event{'s' if event_count != 1 else ''}
                            </small><br>
                            <small style="color: {text_color}; font-weight: 800; 
                                        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);">
                                ₹{total_expense:,.0f}
                            </small>
                        </div>
                    """
                    cols[i].markdown(display_html, unsafe_allow_html=True)
                else:
                    # Empty day
                    cols[i].markdown(f"""
                        <div style="background-color: #f8f9fa; padding: 15px; 
                                    border-radius: 8px; text-align: center; 
                                    min-height: 75px; border: 1px solid #dee2e6;">
                            <strong style="color: #495057; font-size: 1.3rem;">{day}</strong>
                        </div>
                    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Display AI prediction if date is selected
    if st.session_state.selected_date:
        date_key = st.session_state.selected_date.strftime("%Y-%m-%d")
        
        if date_key in st.session_state.event_predictions:
            result = st.session_state.event_predictions[date_key]
            
            st.markdown("## 🎯 AI-Powered Financial Analysis")
            
            # Header card
            st.markdown(f"""
            <div class="prediction-card">
                <h2 style="margin: 0;">📊 {result['event_name']}</h2>
                <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem;">
                    <strong>{result['event_type']}</strong> • 
                    {st.session_state.selected_date.strftime('%d %B %Y')} •
                    User: {result['user_id']}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            ai_predicted = result['ai_predicted_actual_expense']
            user_estimate = result['user_estimated_expense']
            budget_diff = user_estimate - ai_predicted
            
            with col1:
                st.metric("Your Estimate", f"₹{user_estimate:,.2f}")
            with col2:
                st.metric("AI Predicted", f"₹{ai_predicted:,.2f}")
            with col3:
                # Determine risk based on budget accuracy
                if user_estimate < ai_predicted:
                    risk_status = "✅ Low Risk"
                    risk_color = "normal"
                    risk_message = "Under budget - Safe estimate"
                elif abs(budget_diff) <= 1000:
                    risk_status = "⚠️ Accurate"
                    risk_color = "off"
                    risk_message = "Close to AI prediction"
                else:
                    risk_status = "🔴 High Risk"
                    risk_color = "inverse"
                    risk_message = "Over budget - Risk of overspending"
                
                st.metric("Risk Factor", risk_status)
            with col4:
                delta_label = f"₹{abs(budget_diff):,.0f} {'over' if budget_diff > 0 else 'under'}"
                st.metric("Budget Gap", delta_label, delta_color=risk_color)
            
            st.markdown("---")
            
            # Risk explanation
            if user_estimate < ai_predicted:
                st.success(f"✅ **Low Risk:** Your estimate is ₹{abs(budget_diff):,.2f} less than AI prediction. You have a safety buffer!")
            elif abs(budget_diff) <= 1000:
                st.info(f"⚠️ **Accurate Budget:** Your estimate is within ₹{abs(budget_diff):,.2f} of AI prediction. Well planned!")
            else:
                st.error(f"🔴 **High Risk:** Your estimate is ₹{budget_diff:,.2f} MORE than AI prediction. Risk of overspending!")
            
            # Detailed breakdown
            st.markdown("### 📋 Budget Accuracy Analysis")
            
            breakdown_text = f"""
📝 **Your Estimate:**        ₹{user_estimate:>12,.2f}
🤖 **AI Predicted Actual:**  ₹{ai_predicted:>12,.2f}
💰 **Budget Difference:**    ₹{budget_diff:>12,.2f} {'(Overestimate)' if budget_diff > 0 else '(Underestimate)'}
⚠️  **Risk Factor:**         {risk_status} - {risk_message}
💵 **Expense/Income:**       {result.get('expense_to_income_ratio', 0):>12.1f}%
"""
            st.code(breakdown_text, language=None)
            
            # Savings Plan
            st.markdown("### 💡 Personalized Savings Plan")
            
            total_savings = max(ai_predicted, 0)
            monthly_saving = result.get('recommended_monthly_saving', total_savings / 3)
            months_to_prepare = result.get('months_to_prepare', 3)
            
            st.markdown(f"""
            <div class="metric-box">
                • <strong>Total Savings Needed:</strong> ₹{total_savings:,.2f}<br>
                • <strong>Monthly Savings Target:</strong> ₹{monthly_saving:,.2f}<br>
                • <strong>Preparation Time:</strong> {months_to_prepare} months
            </div>
            """, unsafe_allow_html=True)
            
            # Recommendations
            st.markdown("### 📌 Smart Recommendations")
            
            recommendations = result.get('recommendations', [])
            if not recommendations:
                if user_estimate < ai_predicted:
                    recommendations = [
                        "Your estimate is conservative, which is good for budgeting",
                        "Consider setting aside the AI predicted amount to avoid shortfall",
                        "Track actual spending to refine future estimates"
                    ]
                elif abs(budget_diff) <= 1000:
                    recommendations = [
                        "Your estimate is very accurate!",
                        "Maintain this level of planning for future events",
                        "Consider creating a 10% buffer for unexpected costs"
                    ]
                else:
                    recommendations = [
                        "⚠️ Your estimate significantly exceeds AI prediction",
                        "Review your budget breakdown to identify overestimation",
                        "Consider the AI prediction as a more realistic baseline",
                        "Set aside the AI amount and keep excess as emergency fund"
                    ]
            
            for i, rec in enumerate(recommendations, 1):
                st.markdown(f"""
                <div class="recommendation-item">
                    <strong>{i}.</strong> {rec}
                </div>
                """, unsafe_allow_html=True)
            
            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("❌ Clear Selection", use_container_width=True):
                    st.session_state.selected_date = None
                    st.rerun()
            with col2:
                if st.button("🗑️ Delete Event", use_container_width=True):
                    del st.session_state.event_predictions[date_key]
                    st.session_state.selected_date = None
                    st.success("Event deleted!")
                    st.rerun()
        else:
            st.info("No AI prediction available for this date. Mark an event to get predictions!")
            if st.button("❌ Clear Selection"):
                st.session_state.selected_date = None
                st.rerun()
    
    # Summary section
    st.markdown("---")
    st.markdown("### 📊 Month Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    marked_events = [v for k, v in st.session_state.event_predictions.items() 
                    if datetime.strptime(k, "%Y-%m-%d").month == st.session_state.calendar_month]
    
    with col1:
        st.metric("Marked Events", len(marked_events))
    with col2:
        total_estimated = sum([e['user_estimated_expense'] for e in marked_events])
        st.metric("Total Estimated", f"₹{total_estimated:,.0f}")
    with col3:
        total_predicted = sum([e['ai_predicted_actual_expense'] for e in marked_events])
        st.metric("AI Predicted Total", f"₹{total_predicted:,.2f}")
    with col4:
        total_savings = sum([e.get('recommended_monthly_saving', 0) for e in marked_events])
        st.metric("Monthly Savings Needed", f"₹{total_savings:,.2f}")
    
    # Legend
    st.markdown("---")
    st.markdown("### 🎨 Calendar Color Guide")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style="background-color: #51cf66; padding: 10px; border-radius: 5px; 
                    text-align: center; border: 2px solid #2b8a3e;">
            <strong style="color: #000;">🟢 Green: Low Risk</strong><br>
            <small style="color: #000; font-weight: 600;">Your estimate < AI prediction<br>Safe budget, no overspending risk</small>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background-color: #ffd93d; padding: 10px; border-radius: 5px; 
                    text-align: center; border: 2px solid #fab005;">
            <strong style="color: #000;">🟡 Yellow: Accurate</strong><br>
            <small style="color: #000; font-weight: 600;">Within ±₹1,000 of AI prediction<br>Well-planned budget</small>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="background-color: #ff6b6b; padding: 10px; border-radius: 5px; 
                    text-align: center; border: 2px solid #c92a2a;">
            <strong style="color: #fff;">🔴 Red: High Risk</strong><br>
            <small style="color: #fff; font-weight: 600;">Your estimate > AI prediction<br>Risk of overspending!</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.info("💡 **How it works:** The AI compares your estimate with predicted actual cost. Green means you're conservative (safe), Yellow means accurate, Red means you might overspend!")
