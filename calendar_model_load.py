import joblib
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
import os

@st.cache_resource
def load_ml_models():
    """Load all pre-trained models and encoders (cached for performance)"""
    try:
        models = {
            'event_predictor': joblib.load('models/event_expense_predictor.pkl'),
            'savings_recommender': joblib.load('models/savings_recommender.pkl'),
            'le_user': joblib.load('models/le_user.pkl'),
            'le_event_name': joblib.load('models/le_event_name.pkl'),
            'le_event_type': joblib.load('models/le_event_type.pkl'),
            'le_personality': joblib.load('models/le_personality.pkl'),
            'le_risk': joblib.load('models/le_risk.pkl'),
            'le_urgency': joblib.load('models/le_urgency.pkl'),
            'feature_cols_event': joblib.load('models/feature_cols_event.pkl'),
            'feature_cols_savings': joblib.load('models/feature_cols_savings.pkl'),
            'users_reference': joblib.load('models/users_reference.pkl')
        }
        return models
    except Exception as e:
        st.error(f"⚠️ Error loading models: {e}")
        return None

@st.cache_data
def load_transaction_data():
    """Load transaction data for historical analysis (cached)"""
    try:
        return pd.read_csv('data/finsight_transactions.csv')
    except Exception as e:
        st.warning(f"Transaction data not found: {e}")
        return None

def predict_event_expense(models, user_id, event_name, event_type, year, month, predicted_expense):
    """
    Predict actual expense and recommend savings using pre-trained models
    
    Parameters:
    -----------
    models : dict - Loaded ML models and encoders
    user_id : str - User ID (e.g., 'U001')
    event_name : str - Event name
    event_type : str - Event type
    year : int - Year extracted from calendar
    month : int - Month extracted from calendar (1-12)
    predicted_expense : float - User's estimated expense
    
    Returns:
    --------
    dict - Complete analysis with predictions and recommendations
    """
    try:
        # Get user profile
        users_df = models['users_reference']
        user_profile = users_df[users_df['user_id'] == user_id]
        
        if len(user_profile) == 0:
            return {'success': False, 'error': f'User {user_id} not found'}
        
        user_profile = user_profile.iloc[0]
        
        # Get user's historical average
        transactions_df = load_transaction_data()
        if transactions_df is not None:
            user_txns = transactions_df[
                (transactions_df['user_id'] == user_id) & 
                (transactions_df['transaction_type'] == 'debit')
            ]
            user_avg = user_txns['amount'].mean() if len(user_txns) > 0 else predicted_expense
        else:
            user_avg = predicted_expense
        
        # Handle unseen labels with try-except
        try:
            user_enc = models['le_user'].transform([user_id])[0]
        except:
            # Use a default encoding for unknown users
            user_enc = 0
            
        try:
            event_type_enc = models['le_event_type'].transform([event_type])[0]
        except:
            event_type_enc = 0
            
        try:
            personality_enc = models['le_personality'].transform([user_profile['spending_personality']])[0]
        except:
            personality_enc = 0
            
        try:
            risk_enc = models['le_risk'].transform([user_profile['risk_tolerance']])[0]
        except:
            risk_enc = 0
        
        # Calculate time-based features
        quarter = (month - 1) // 3 + 1
        is_festive = 1 if month in [10, 11, 12, 1] else 0
        is_summer = 1 if month in [5, 6] else 0
        day_of_week = 3  # Assume mid-week
        is_weekend = 0
        is_recurring = 0
        
        # MODEL 1: Predict actual expense
        features_event = pd.DataFrame([[
            user_enc, event_type_enc, year, month, quarter,
            day_of_week, is_weekend, is_festive, is_summer,
            predicted_expense, user_profile['monthly_salary'], user_profile['savings_rate'],
            personality_enc, risk_enc, user_avg, is_recurring
        ]], columns=models['feature_cols_event'])
        
        actual_expense_predicted = models['event_predictor'].predict(features_event)[0]
        actual_expense_predicted = max(actual_expense_predicted, 0)
        
        # MODEL 2: Recommend savings
        expense_to_income = actual_expense_predicted / user_profile['monthly_salary']
        expense_vs_predicted = actual_expense_predicted / (predicted_expense + 1)
        
        features_savings = pd.DataFrame([[
            user_enc, event_type_enc, year, month,
            predicted_expense, actual_expense_predicted, 
            user_profile['monthly_salary'], user_profile['savings_rate'],
            personality_enc, risk_enc, is_festive, is_summer,
            expense_to_income, expense_vs_predicted
        ]], columns=models['feature_cols_savings'])
        
        monthly_savings_needed = models['savings_recommender'].predict(features_savings)[0]
        monthly_savings_needed = max(monthly_savings_needed, 0)
        
        # Calculate insights
        budget_gap = actual_expense_predicted - predicted_expense
        total_savings_needed = max(budget_gap, 0)
        months_to_save = 3
        
        # Determine urgency and color
        if expense_to_income > 0.5:
            urgency = 'High'
            urgency_msg = "⚠️ This event may significantly impact your budget!"
            color = "#ff4444"  # Red
        elif expense_to_income > 0.3:
            urgency = 'Medium'
            urgency_msg = "⚡ Moderate financial planning needed"
            color = "#ffaa00"  # Orange
        else:
            urgency = 'Low'
            urgency_msg = "✅ Manageable within your budget"
            color = "#44ff44"  # Green
        
        # Generate recommendations
        recommendations = []
        
        if budget_gap > 0:
            recommendations.append(f"Start saving ₹{monthly_savings_needed:.0f} per month")
            recommendations.append(f"Reduce discretionary spending by ₹{(budget_gap/3):.0f}/month")
            
            # Category-specific advice
            if event_type == 'Travel':
                recommendations.append("Consider budget-friendly accommodation options")
                recommendations.append("Book tickets in advance for better deals")
            elif event_type == 'Celebration':
                recommendations.append("Plan a budget for gifts and dining")
                recommendations.append("Share costs with other participants")
            elif event_type == 'Shopping':
                recommendations.append("Create a priority list before shopping")
                recommendations.append("Look for discounts and festive offers")
            elif event_type == 'Bill':
                recommendations.append("Set up auto-pay to avoid late fees")
                recommendations.append("Review subscription services")
            elif event_type == 'Healthcare':
                recommendations.append("Check if insurance covers part of the expense")
                recommendations.append("Compare prices at different providers")
        else:
            recommendations.append("Your budget estimate is realistic!")
            recommendations.append("Keep some buffer for unexpected costs")
        
        # Personality-based advice
        if user_profile['spending_personality'] == 'impulsive':
            recommendations.append("⚠️ Avoid impulse purchases during this event")
        elif user_profile['spending_personality'] == 'frugal':
            recommendations.append("💡 You're naturally good at saving - stay on track!")
        
        return {
            'success': True,
            'user_id': user_id,
            'event_name': event_name,
            'event_type': event_type,
            'year': year,
            'month': month,
            'user_estimated_expense': predicted_expense,
            'ai_predicted_actual_expense': round(actual_expense_predicted, 2),
            'budget_gap': round(budget_gap, 2),
            'urgency': urgency,
            'urgency_message': urgency_msg,
            'color': color,
            'total_savings_needed': round(total_savings_needed, 2),
            'recommended_monthly_saving': round(monthly_savings_needed, 2),
            'months_to_prepare': months_to_save,
            'expense_to_income_ratio': round(expense_to_income * 100, 1),
            'recommendations': recommendations
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
