"""
FINSIGHT Dashboard Module

Renders the main dashboard UI with KPIs, charts, and financial insights based on dataset.py schema.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
from dateutil.relativedelta import relativedelta

def render_dashboard(user_id, data):
    """
    Main dashboard rendering function.
    
    Args:
        user_id (str): The current user's ID
        data (dict): Dictionary containing all dataframes
    """
    # Check if data is available
    if data is None:
        st.error("Unable to load financial data. Please check if CSV files exist.")
        return
    
    # Try to get data frames
    try:
        # Load user data
        if 'users' in data and not data['users'].empty:
            users_df = data['users']
        else:
            st.error("User data not available")
            return
            
        # Load transactions data
        if 'transactions' in data and not data['transactions'].empty:
            transactions_df = data['transactions']
        else:
            st.error("Transaction data not available")
            return
            
        # Load calendar events data (if available)
        calendar_df = data.get('calendar_events')
        
        # Load ML features data (if available)
        ml_df = None
            
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return
    
    # Get user data
    user_data = get_user_data(user_id, users_df)
    
    # Filter and prepare datasets for the user
    transactions_df = filter_user_transactions(user_id, transactions_df)
    
    # Page header with user greeting
    st.markdown(f"# Welcome back, {user_data['name']}! 👋")
    st.markdown("Your financial insights dashboard is ready.")
    
    # Display KPI metrics at the top
    render_kpi_summary(user_id, transactions_df, user_data)
    
    # Main dashboard sections in tabs
    tab1, tab2, tab3 = st.tabs(["Financial Overview", "Spending Analysis", "Income Analysis"])
    
    with tab1:
        render_financial_overview(user_id, transactions_df, user_data)
    
    with tab2:
        render_spending_analysis(user_id, transactions_df)
    
    with tab3:
        render_income_analysis(user_id, transactions_df, user_data)
    
    # Display calendar events if available
    if calendar_df is not None and not calendar_df.empty:
        calendar_df = filter_user_calendar(user_id, calendar_df)
        if not calendar_df.empty:
            st.markdown("### Upcoming Events & Expenses")
            render_upcoming_events(user_id, calendar_df, user_data)

def get_user_data(user_id, users_df):
    """Get user profile data."""
    try:
        user_row = users_df[users_df['user_id'] == user_id]
        if len(user_row) == 0:
            return {
                "name": "User",
                "avg_monthly_income": 50000,
                "risk_tolerance": "medium"
            }
            
        # Convert to dictionary
        user_dict = user_row.iloc[0].to_dict()
        
        # Handle different column names
        if 'avg_monthly_income' not in user_dict and 'monthly_salary' in user_dict:
            user_dict['avg_monthly_income'] = user_dict['monthly_salary']
            
        return user_dict
    except Exception as e:
        st.warning(f"Error getting user data: {e}")
        return {
            "name": "User",
            "avg_monthly_income": 50000,
            "risk_tolerance": "medium"
        }

def filter_user_transactions(user_id, transactions_df):
    """Filter transactions for user_id."""
    try:
        # Filter for the user
        df = transactions_df[transactions_df['user_id'] == user_id].copy()
        
        # Convert date to datetime if it's not already
        if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
            
        # Add month and year columns for analysis
        if 'date' in df.columns:
            df['month'] = df['date'].dt.month
            df['year'] = df['date'].dt.year
            df['month_year'] = df['date'].dt.strftime('%b %Y')
            
        # Add abs_amount for easier calculations
        if 'amount' in df.columns:
            df['abs_amount'] = df['amount'].abs()
            
        return df
    except Exception as e:
        st.warning(f"Error processing transactions: {e}")
        return pd.DataFrame()

def filter_user_calendar(user_id, calendar_df):
    """Filter calendar events for user_id."""
    try:
        # Filter for the user
        df = calendar_df[calendar_df['user_id'] == user_id].copy()
        
        # Convert date to datetime if it's not already
        if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
            
        return df
    except Exception as e:
        st.warning(f"Error processing calendar events: {e}")
        return pd.DataFrame()

def render_kpi_summary(user_id, transactions_df, user_data):
    """Render the KPI metrics at the top of the dashboard."""
    
    if transactions_df.empty:
        st.warning("No transaction data available for KPIs.")
        return
    
    try:
        # Calculate current month's data
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Filter for current month
        if 'month' in transactions_df.columns and 'year' in transactions_df.columns:
            current_month_transactions = transactions_df[
                (transactions_df['month'] == current_month) & 
                (transactions_df['year'] == current_year)
            ]
            
            last_month = (datetime.now() - relativedelta(months=1)).month
            last_month_year = (datetime.now() - relativedelta(months=1)).year
            
            last_month_transactions = transactions_df[
                (transactions_df['month'] == last_month) & 
                (transactions_df['year'] == last_month_year)
            ]
        else:
            # If month/year columns don't exist, just use all transactions
            current_month_transactions = transactions_df
            last_month_transactions = pd.DataFrame()
        
        # Calculate KPIs
        total_income = current_month_transactions[current_month_transactions['amount'] > 0]['amount'].sum()
        total_expense = abs(current_month_transactions[current_month_transactions['amount'] < 0]['amount'].sum())
        
        # Calculate expense change percentage if we have last month data
        if not last_month_transactions.empty:
            last_month_expense = abs(last_month_transactions[last_month_transactions['amount'] < 0]['amount'].sum())
            expense_change_pct = ((total_expense - last_month_expense) / last_month_expense * 100) if last_month_expense > 0 else 0
        else:
            expense_change_pct = 0
        
        # Net cashflow
        net_cashflow = total_income - total_expense
        
        # Savings rate (income - expenses) / income
        savings_rate = ((total_income - total_expense) / total_income * 100) if total_income > 0 else 0
        
        # Create KPI cards in a 4-column layout
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>Month's Income</h3>
                <h2>₹{:,.0f}</h2>
            </div>
            """.format(total_income), unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>Month's Expenses</h3>
                <h2>₹{:,.0f}</h2>
                <p>{:+.1f}% vs last month</p>
            </div>
            """.format(total_expense, expense_change_pct), unsafe_allow_html=True)
            
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>Net Cashflow</h3>
                <h2>₹{:,.0f}</h2>
                <p>Savings Rate: {:.1f}%</p>
            </div>
            """.format(net_cashflow, savings_rate), unsafe_allow_html=True)
            
        with col4:
            monthly_income = user_data.get('avg_monthly_income', 0)
            st.markdown("""
            <div class="metric-card">
                <h3>Monthly Income</h3>
                <h2>₹{:,.0f}</h2>
                <p>Average Monthly</p>
            </div>
            """.format(monthly_income), unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error rendering KPI summary: {e}")

def render_financial_overview(user_id, transactions_df, user_data):
    """Render financial overview section with income/expense trends."""
    
    st.subheader("Income & Expense Trends")
    
    if transactions_df.empty:
        st.info("No transaction data available for financial overview.")
        return
    
    try:
        # Monthly income and expenses trend
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Aggregate data by month
            monthly_agg = transactions_df.copy()
            
            # Create month-year field for sorting
            if 'month_year' in monthly_agg.columns and 'month' in monthly_agg.columns and 'year' in monthly_agg.columns:
                # Create a datetime column for proper sorting
                monthly_agg['month_year_dt'] = pd.to_datetime(monthly_agg[['year', 'month']].assign(day=1))
                
                # Group by month and calculate income and expenses
                monthly_summary = monthly_agg.groupby('month_year').agg(
                    income=('amount', lambda x: x[x > 0].sum()),
                    expenses=('amount', lambda x: x[x < 0].sum() * -1),
                    net=('amount', 'sum')
                ).reset_index()
                
                # Sort by actual date
                month_order = monthly_agg.sort_values('month_year_dt')['month_year'].unique()
                
                # Only show last 12 months for clarity
                if len(month_order) > 12:
                    month_order = month_order[-12:]
                    monthly_summary = monthly_summary[monthly_summary['month_year'].isin(month_order)]
                
                # Create Plotly figure
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=monthly_summary['month_year'],
                    y=monthly_summary['income'],
                    name='Income',
                    marker_color='#72b7b2'
                ))
                
                fig.add_trace(go.Bar(
                    x=monthly_summary['month_year'],
                    y=monthly_summary['expenses'],
                    name='Expenses',
                    marker_color='#f67280'
                ))
                
                fig.add_trace(go.Scatter(
                    x=monthly_summary['month_year'],
                    y=monthly_summary['net'],
                    name='Net Cashflow',
                    mode='lines+markers',
                    line=dict(color='#355c7d', width=3)
                ))
                
                fig.update_layout(
                    barmode='group',
                    title='Monthly Income vs Expenses',
                    xaxis=dict(
                        title='Month',
                        categoryorder='array',
                        categoryarray=month_order
                    ),
                    yaxis=dict(title='Amount (₹)'),
                    hovermode='x unified',
                    legend=dict(
                        orientation='h',
                        yanchor='bottom',
                        y=1.02,
                        xanchor='right',
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Monthly data not available for chart.")
        
        with col2:
            # Calculate financial health indicators
            avg_monthly_income = user_data.get('avg_monthly_income', 0)
            
            # Calculate total income and expenses
            total_income = transactions_df[transactions_df['amount'] > 0]['amount'].sum()
            total_expenses = abs(transactions_df[transactions_df['amount'] < 0]['amount'].sum())
            total_net = total_income - total_expenses
            
            # Savings rate
            savings_rate = (total_net / total_income * 100) if total_income > 0 else 0
            
            # Financial Stability Score (simple version)
            # Scale from 0-100 based on savings rate
            stability_score = min(100, max(0, savings_rate * 1.5))
            
            # Create a gauge chart for financial stability
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=stability_score,
                title={'text': "Financial Stability Score"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#4b6cb7"},
                    'steps': [
                        {'range': [0, 30], 'color': '#f67280'},
                        {'range': [30, 70], 'color': '#ffb84d'},
                        {'range': [70, 100], 'color': '#72b7b2'}
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 4},
                        'thickness': 0.75,
                        'value': stability_score
                    }
                }
            ))
            
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)
            
            # Financial summary stats
            st.markdown("""
            ### Financial Summary
            
            **Overall Totals:**
            * Total Income: ₹{:,.0f}
            * Total Expenses: ₹{:,.0f}
            * Net Cashflow: ₹{:,.0f}
            
            **Savings Rate:** {:.1f}%
            """.format(
                total_income, total_expenses, total_net, savings_rate
            ))
    except Exception as e:
        st.error(f"Error rendering financial overview: {e}")
    
    # Income Sources & Top Expense Categories
    try:
        st.subheader("Income Sources & Top Expense Categories")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Income by source (merchant for income transactions)
            income_df = transactions_df[transactions_df['amount'] > 0].copy()
            
            if income_df.empty:
                st.info("No income data available.")
            else:
                income_by_source = income_df.groupby('merchant').agg(
                    total_amount=('amount', 'sum'),
                    count=('amount', 'count')
                ).reset_index().sort_values('total_amount', ascending=False).head(5)
                
                # Create figure
                fig = px.bar(
                    income_by_source,
                    x='merchant',
                    y='total_amount',
                    title="Top Income Sources",
                    labels={'merchant': 'Source', 'total_amount': 'Amount (₹)'},
                    color_discrete_sequence=px.colors.sequential.Blues_r
                )
                
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Expenses by category
            expense_df = transactions_df[transactions_df['amount'] < 0].copy()
            
            if expense_df.empty:
                st.info("No expense data available.")
            else:
                expense_by_category = expense_df.groupby('category').agg(
                    total_amount=('abs_amount', 'sum'),
                    count=('amount', 'count')
                ).reset_index().sort_values('total_amount', ascending=False).head(5)
                
                # Create figure
                fig = px.bar(
                    expense_by_category,
                    x='category',
                    y='total_amount',
                    title="Top Expense Categories",
                    labels={'category': 'Category', 'total_amount': 'Amount (₹)'},
                    color_discrete_sequence=px.colors.sequential.Reds_r
                )
                
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error rendering income/expense categories: {e}")

def render_spending_analysis(user_id, transactions_df):
    """Render spending analysis section with detailed breakdowns."""
    
    if transactions_df.empty:
        st.info("No transaction data available for spending analysis.")
        return
    
    try:
        # Filter for expense transactions
        expense_df = transactions_df[transactions_df['amount'] < 0].copy()
        
        if expense_df.empty:
            st.info("No expense data available for analysis.")
            return
        
        # Time period selector
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("### Spending Breakdown & Analysis")
            
        with col2:
            # Get unique year-months from data
            if 'month_year' in expense_df.columns:
                time_options = sorted(expense_df['month_year'].unique())
                
                # Default to most recent month
                default_idx = len(time_options) - 1 if time_options else 0
                selected_period = st.selectbox(
                    "Select Time Period:",
                    options=time_options,
                    index=min(default_idx, len(time_options) - 1) if time_options else 0
                )
                
                # Filter data for selected period
                period_data = expense_df[expense_df['month_year'] == selected_period].copy()
            else:
                st.warning("Month-year data not available for filtering.")
                period_data = expense_df
        
        if period_data.empty:
            st.info(f"No expense data available for the selected period.")
            return
        
        # Spending insights section
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Category distribution pie chart
            category_totals = period_data.groupby('category').agg(
                total=('abs_amount', 'sum')
            ).reset_index().sort_values('total', ascending=False)
            
            # Calculate percentage of total
            total_spend = category_totals['total'].sum()
            category_totals['percentage'] = (category_totals['total'] / total_spend * 100)
            
            # Create pie chart
            fig = px.pie(
                category_totals,
                values='total',
                names='category',
                title=f"Spending by Category",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            
            fig.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Spending insights
            st.markdown("### Spending Insights")
            
            st.markdown(f"**Total Spent:** ₹{total_spend:,.0f}")
            
            # Top merchants
            if 'merchant' in period_data.columns:
                top_merchants = period_data.groupby('merchant').agg(
                    total=('abs_amount', 'sum'),
                    count=('amount', 'count')
                ).sort_values('total', ascending=False).head(3).reset_index()
                
                st.markdown("**Top Merchants:**")
                for _, row in top_merchants.iterrows():
                    st.markdown(f"- {row['merchant']}: ₹{row['total']:,.0f} ({row['count']} transactions)")
        
        # Daily spending pattern
        if 'date' in period_data.columns:
            st.subheader("Daily Spending Pattern")
            
            # Group by date
            daily_spending = period_data.groupby(period_data['date'].dt.date).agg(
                total=('abs_amount', 'sum'),
                count=('amount', 'count')
            ).reset_index()
            
            # Create time series
            fig = px.line(
                daily_spending,
                x='date',
                y='total',
                markers=True,
                labels={'date': 'Date', 'total': 'Daily Spend (₹)'},
                title='Daily Spending Pattern'
            )
            
            # Add transaction count as hover data
            fig.update_traces(
                hovertemplate='<b>%{x}</b><br>₹%{y:,.0f}<br>Transactions: %{customdata}',
                customdata=daily_spending['count']
            )
            
            fig.update_layout(xaxis_tickformat='%d %b')
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error rendering spending analysis: {e}")

def render_income_analysis(user_id, transactions_df, user_data):
    """Render income analysis section."""
    
    if transactions_df.empty:
        st.info("No transaction data available for income analysis.")
        return
    
    try:
        # Filter for income transactions
        income_df = transactions_df[transactions_df['amount'] > 0].copy()
        
        if income_df.empty:
            st.info("No income data available for analysis.")
            return
            
        # Income Sources Breakdown
        st.subheader("Income Sources Breakdown")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Category distribution pie chart for income
            category_totals = income_df.groupby('category').agg(
                total=('amount', 'sum')
            ).reset_index().sort_values('total', ascending=False)
            
            # Create pie chart
            fig = px.pie(
                category_totals,
                values='total',
                names='category',
                title=f"Income by Category",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            fig.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top income sources
            if 'merchant' in income_df.columns:
                top_sources = income_df.groupby('merchant').agg(
                    total=('amount', 'sum'),
                    count=('amount', 'count')
                ).sort_values('total', ascending=False).head(5).reset_index()
                
                # Create bar chart
                fig = px.bar(
                    top_sources,
                    y='merchant',
                    x='total',
                    title="Top Income Sources",
                    labels={'merchant': 'Source', 'total': 'Amount (₹)'},
                    orientation='h',
                    color='total',
                    color_continuous_scale='Blues'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
        # Monthly income trend
        if 'month_year' in income_df.columns and 'date' in income_df.columns:
            st.subheader("Monthly Income Trend")
            
            # Group by month
            monthly_income = income_df.groupby('month_year').agg(
                total=('amount', 'sum'),
                count=('amount', 'count')
            ).reset_index()
            
            # Add date for proper sorting
            monthly_income['date'] = pd.to_datetime(monthly_income['month_year'], format='%b %Y')
            monthly_income = monthly_income.sort_values('date')
            
            # Create line chart
            fig = px.line(
                monthly_income,
                x='month_year',
                y='total',
                markers=True,
                labels={'month_year': 'Month', 'total': 'Income (₹)'},
                title='Monthly Income Trend'
            )
            
            # Add average monthly income from user profile
            avg_monthly_income = user_data.get('avg_monthly_income', 0)
            if avg_monthly_income > 0:
                fig.add_hline(
                    y=avg_monthly_income,
                    line_dash="dash",
                    line_color="green",
                    annotation_text="Average Monthly Income",
                    annotation_position="top right"
                )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Monthly Income vs Avg Income
            st.subheader("Income Stability Analysis")
            
            # Calculate statistics
            avg_actual_income = monthly_income['total'].mean()
            income_stability = (1 - (monthly_income['total'].std() / monthly_income['total'].mean())) * 100 if monthly_income['total'].mean() > 0 else 0
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Average Monthly Income",
                    f"₹{avg_actual_income:,.2f}",
                    delta=f"{(avg_actual_income - avg_monthly_income) / avg_monthly_income * 100:.1f}% vs Expected" if avg_monthly_income > 0 else None
                )
                
            with col2:
                st.metric(
                    "Income Stability",
                    f"{income_stability:.1f}%",
                    delta="Higher is more stable"
                )
    except Exception as e:
        st.error(f"Error rendering income analysis: {e}")

def render_upcoming_events(user_id, calendar_df, user_data):
    """Render upcoming calendar events."""
    
    if calendar_df.empty:
        st.info("No calendar data available.")
        return
    
    try:
        # Filter for upcoming events
        today = datetime.now().date()
        upcoming_events = calendar_df[calendar_df['date'].dt.date >= today].sort_values('date')
        
        if upcoming_events.empty:
            st.info("No upcoming events found.")
            return
            
        # Display upcoming events
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # List of upcoming events
            st.subheader("Upcoming Events")
            
            for _, event in upcoming_events.head(5).iterrows():
                date_str = event['date'].strftime("%d %b %Y")
                title = event.get('title', 'Event')
                event_type = event.get('event_type', 'Event')
                cost = event.get('estimated_cost', 0)
                
                # Determine a color based on event type
                color = "#3498db" if event_type == "Meeting" else ("#e74c3c" if event_type == "Bill" else "#f39c12")
                
                st.markdown(f"""
                <div style="
                    background-color: rgba({color[1:3]}, {color[3:5]}, {color[5:]}, 0.1);
                    padding: 15px;
                    border-radius: 5px;
                    border-left: 5px solid {color};
                    margin-bottom: 10px;
                ">
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <h4 style="margin: 0;">{title}</h4>
                            <p style="margin: 5px 0; color: #666;">{date_str} • {event_type}</p>
                        </div>
                        <div style="text-align: right; font-weight: bold;">
                            ₹{cost:,.2f}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            # Summary statistics
            total_upcoming_cost = upcoming_events['estimated_cost'].sum()
            event_count = len(upcoming_events)
            
            st.metric(
                "Total Upcoming Expenses",
                f"₹{total_upcoming_cost:,.2f}",
                delta=f"{event_count} events"
            )
            
            # Event Type Breakdown
            event_types = upcoming_events['event_type'].value_counts()
            
            st.markdown("#### Event Types")
            
            for event_type, count in event_types.items():
                st.markdown(f"- {event_type}: {count}")
            
        # Events Calendar View
        st.subheader("Calendar View")
        
        # Group events by date
        events_by_date = upcoming_events.groupby(upcoming_events['date'].dt.date).agg(
            count=('title', 'count'),
            cost=('estimated_cost', 'sum')
        ).reset_index()
        
        # Create heatmap-like calendar view
        fig = px.scatter(
            events_by_date,
            x=events_by_date['date'],
            y=['Events'] * len(events_by_date),
            size='count',
            color='cost',
            hover_name='date',
            hover_data={
                'date': True,
                'y': False,
                'count': True,
                'cost': ':.2f'
            },
            color_continuous_scale='Viridis',
            title='Upcoming Events Calendar'
        )
        
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='',
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error rendering upcoming events: {e}")