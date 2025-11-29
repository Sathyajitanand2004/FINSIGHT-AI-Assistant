import pandas as pd
import numpy as np
import streamlit as st

class InvestmentRecommendationEngine:
    def __init__(self):
        self.investment_options = {
            'Fixed Deposit': {'risk': 1, 'min_amount': 5000, 'max_amount': 100000, 'expected_return': 0.07},
            'PPF': {'risk': 1, 'min_amount': 500, 'max_amount': 150000, 'expected_return': 0.075},
            'Debt Mutual Funds': {'risk': 2, 'min_amount': 1000, 'max_amount': 50000, 'expected_return': 0.09},
            'Balanced Mutual Funds': {'risk': 3, 'min_amount': 1000, 'max_amount': 75000, 'expected_return': 0.11},
            'Equity Mutual Funds': {'risk': 4, 'min_amount': 500, 'max_amount': 100000, 'expected_return': 0.14},
            'Stocks': {'risk': 5, 'min_amount': 5000, 'max_amount': 50000, 'expected_return': 0.16},
            'Gold ETF': {'risk': 3, 'min_amount': 1000, 'max_amount': 50000, 'expected_return': 0.10},
            'Real Estate Funds': {'risk': 4, 'min_amount': 10000, 'max_amount': 200000, 'expected_return': 0.12}
        }
        
        self.risk_profiles = {
            'low': {'max_risk': 2, 'equity_ratio': 0.2, 'debt_ratio': 0.8},
            'medium': {'max_risk': 3, 'equity_ratio': 0.5, 'debt_ratio': 0.5},
            'high': {'max_risk': 5, 'equity_ratio': 0.8, 'debt_ratio': 0.2}
        }
    
    def calculate_portfolio_score(self, user_data):
        """Score-based portfolio allocation using multi-criteria optimization"""
        risk_profile = user_data['risk_tolerance']
        available_savings = user_data['available_savings']
        goal_deadline_months = user_data.get('goal_deadline_months', 36)
        
        scores = {}
        for investment, details in self.investment_options.items():
            risk_score = self._calculate_risk_compatibility(details['risk'], risk_profile)
            return_score = details['expected_return'] / 0.16
            liquidity_score = self._calculate_liquidity_score(goal_deadline_months, details['risk'])
            affordability_score = self._calculate_affordability(
                available_savings, details['min_amount'], details['max_amount']
            )
            
            weights = self._get_priority_weights(risk_profile, goal_deadline_months)
            total_score = (
                weights['risk'] * risk_score +
                weights['return'] * return_score +
                weights['liquidity'] * liquidity_score +
                weights['affordability'] * affordability_score
            )
            
            scores[investment] = {
                'total_score': total_score,
                'details': details,
                'breakdown': {
                    'risk_score': risk_score,
                    'return_score': return_score,
                    'liquidity_score': liquidity_score,
                    'affordability_score': affordability_score
                }
            }
        
        return scores
    
    def _calculate_risk_compatibility(self, inv_risk, user_risk_profile):
        max_risk = self.risk_profiles[user_risk_profile]['max_risk']
        if inv_risk <= max_risk:
            return 1.0 - (max_risk - inv_risk) * 0.1
        else:
            return max(0, 1.0 - (inv_risk - max_risk) * 0.3)
    
    def _calculate_liquidity_score(self, goal_months, inv_risk):
        if goal_months <= 12:
            return 1.0 if inv_risk <= 2 else 0.3
        elif goal_months <= 60:
            return 1.0 if inv_risk <= 3 else 0.7
        else:
            return 1.0
    
    def _calculate_affordability(self, savings, min_amt, max_amt):
        if savings < min_amt:
            return 0.0
        elif savings > max_amt * 3:
            return 0.6
        elif min_amt <= savings <= max_amt:
            return 1.0
        else:
            return 0.8
    
    def _get_priority_weights(self, risk_profile, goal_months):
        if risk_profile == 'low':
            return {'risk': 0.5, 'return': 0.2, 'liquidity': 0.2, 'affordability': 0.1}
        elif risk_profile == 'high' and goal_months > 60:
            return {'risk': 0.2, 'return': 0.5, 'liquidity': 0.1, 'affordability': 0.2}
        else:
            return {'risk': 0.35, 'return': 0.35, 'liquidity': 0.2, 'affordability': 0.1}
    
    def recommend_portfolio(self, user_data):
        """Generate optimal portfolio using greedy allocation"""
        scores = self.calculate_portfolio_score(user_data)
        sorted_investments = sorted(
            scores.items(), 
            key=lambda x: x[1]['total_score'], 
            reverse=True
        )
        
        portfolio = []
        remaining = user_data['available_savings']
        
        for investment, score_data in sorted_investments:
            if remaining <= 0:
                break
            
            details = score_data['details']
            allocation = min(remaining * 0.4, details['max_amount'], remaining)
            
            if allocation >= details['min_amount']:
                portfolio.append({
                    'investment': investment,
                    'amount': allocation,
                    'percentage': (allocation / user_data['available_savings']) * 100,
                    'expected_return': details['expected_return'],
                    'risk_level': details['risk'],
                    'score': score_data['total_score'],
                    'score_breakdown': score_data['breakdown']
                })
                remaining -= allocation
        
        return portfolio


def calculate_available_savings(user_id, DATA):
    """Calculate available savings from transactions and investments"""
    try:
        # Get user transactions
        user_txns = DATA['transactions'][DATA['transactions']['user_id'] == user_id]
        
        # Calculate total income and expenses
        total_income = user_txns[user_txns['transaction_type'] == 'credit']['amount'].sum()
        total_expense = user_txns[user_txns['transaction_type'] == 'debit']['amount'].sum()
        
        # Get existing investments
        user_investments = DATA['investments'][DATA['investments']['user_id'] == user_id]
        total_invested = user_investments['amount_invested'].sum()
        
        # Calculate liquid savings (not invested)
        available_savings = total_income - total_expense - total_invested
        
        # Ensure minimum savings
        available_savings = max(available_savings, 5000)  # Minimum ₹5,000
        
        return round(available_savings, 2)
    except Exception as e:
        st.error(f"Error calculating savings: {e}")
        return 50000  # Default value
