

import os
import pandas as pd
import json
from typing import Any, Dict, List, Annotated
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# ==================== CONFIGURATION ====================
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
USER_ID = "U002"  # Default user - can be changed

# Initialize LLM
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.1-8b-instant",
    temperature=0.7
)

# ==================== DATA LOADING ====================
def load_data():
    """Load CSV datasets"""
    try:
        transactions = pd.read_csv("data/finsight_transactions.csv")
        investments = pd.read_csv("data/finsight_investments.csv")
        calendar_events = pd.read_csv("data/finsight_calendar_events.csv")
        group_expenses = pd.read_csv("data/finsight_group_expenses.csv")
        user_goals = pd.read_csv("data/finsight_user_goals.csv")
        users = pd.read_csv("data/finsight_users.csv")
        
        return {
            "transactions": transactions,
            "investments": investments,
            "calendar_events": calendar_events,
            "group_expenses": group_expenses,
            "user_goals": user_goals,
            "users": users
        }
    except FileNotFoundError as e:
        print(f"Error loading data: {e}")
        return None

# Load data globally
DATA = load_data()

# ==================== TOOL DEFINITIONS ====================

@tool
def get_spending_by_category(user_id: str = USER_ID) -> Dict[str, Any]:
    """Get total spending breakdown by category for a specific user"""
    if DATA is None:
        return {"error": "Data not loaded"}
    
    user_transactions = DATA["transactions"][
        (DATA["transactions"]["user_id"] == user_id) & 
        (DATA["transactions"]["transaction_type"] == "debit")
    ]
    
    spending = user_transactions.groupby("category")["amount"].agg(["sum", "count"])
    spending = spending.sort_values("sum", ascending=False)
    
    return {
        "user_id": user_id,
        "spending_by_category": spending.to_dict("index"),
        "total_spending": float(user_transactions["amount"].sum())
    }

@tool
def get_highest_spending_category(user_id: str = USER_ID) -> Dict[str, Any]:
    """Identify the category with highest spending"""
    if DATA is None:
        return {"error": "Data not loaded"}
    
    user_transactions = DATA["transactions"][
        (DATA["transactions"]["user_id"] == user_id) & 
        (DATA["transactions"]["transaction_type"] == "debit")
    ]
    
    spending = user_transactions.groupby("category")["amount"].sum().sort_values(ascending=False)
    
    if spending.empty:
        return {"error": "No spending data found"}
    
    highest_category = spending.index[0]
    highest_amount = float(spending.iloc[0])
    
    return {
        "highest_spending_category": highest_category,
        "amount": highest_amount,
        "percentage_of_total": float((highest_amount / spending.sum()) * 100)
    }

@tool
def get_monthly_spending(user_id: str = USER_ID, month: int = None, year: int = None) -> Dict[str, Any]:
    """Get spending for a specific month"""
    if DATA is None:
        return {"error": "Data not loaded"}
    
    if month is None:
        month = datetime.now().month
    if year is None:
        year = datetime.now().year
    
    user_transactions = DATA["transactions"][
        (DATA["transactions"]["user_id"] == user_id) & 
        (DATA["transactions"]["month"] == month) &
        (DATA["transactions"]["year"] == year) &
        (DATA["transactions"]["transaction_type"] == "debit")
    ]
    
    monthly_spending = user_transactions.groupby("category")["amount"].sum()
    
    return {
        "month": month,
        "year": year,
        "spending_by_category": monthly_spending.to_dict(),
        "total_monthly_spending": float(user_transactions["amount"].sum()),
        "transaction_count": len(user_transactions)
    }

@tool
def get_income_vs_expenses(user_id: str = USER_ID) -> Dict[str, Any]:
    """Get total income vs expenses"""
    if DATA is None:
        return {"error": "Data not loaded"}
    
    user_data = DATA["transactions"][DATA["transactions"]["user_id"] == user_id]
    
    income = user_data[user_data["transaction_type"] == "credit"]["amount"].sum()
    expenses = user_data[user_data["transaction_type"] == "debit"]["amount"].sum()
    
    return {
        "total_income": float(income),
        "total_expenses": float(expenses),
        "net_balance": float(income - expenses),
        "expense_to_income_ratio": float((expenses / income) * 100) if income > 0 else 0
    }

@tool
def get_investment_portfolio(user_id: str = USER_ID) -> Dict[str, Any]:
    """Get investment portfolio details"""
    if DATA is None:
        return {"error": "Data not loaded"}
    
    user_investments = DATA["investments"][DATA["investments"]["user_id"] == user_id]
    
    portfolio = user_investments.groupby("investment_type").agg({
        "amount_invested": "sum",
        "current_value": "sum",
        "roi_percentage": "mean"
    })
    
    return {
        "total_invested": float(user_investments["amount_invested"].sum()),
        "current_portfolio_value": float(user_investments["current_value"].sum()),
        "total_gain": float(user_investments["current_value"].sum() - user_investments["amount_invested"].sum()),
        "portfolio_breakdown": portfolio.to_dict("index"),
        "average_roi": float(user_investments["roi_percentage"].mean())
    }

@tool
def get_upcoming_events(user_id: str = USER_ID, days: int = 30) -> Dict[str, Any]:
    """Get upcoming calendar events and their predicted expenses"""
    if DATA is None:
        return {"error": "Data not loaded"}
    
    today = datetime.now()
    future_date = today + timedelta(days=days)
    
    user_events = DATA["calendar_events"][
        (DATA["calendar_events"]["user_id"] == user_id)
    ]
    
    events = []
    for _, event in user_events.iterrows():
        event_date = datetime.strptime(event["event_date"], "%Y-%m-%d")
        if today <= event_date <= future_date:
            events.append({
                "event_name": event["event_name"],
                "event_type": event["event_type"],
                "date": event["event_date"],
                "predicted_expense": float(event["predicted_expense"])
            })
    
    return {
        "upcoming_events": events,
        "total_predicted_expense": sum([e["predicted_expense"] for e in events]),
        "event_count": len(events)
    }

@tool
def get_spending_trends(user_id: str = USER_ID, months: int = 6) -> Dict[str, Any]:
    """Get spending trends over past months"""
    if DATA is None:
        return {"error": "Data not loaded"}
    
    user_transactions = DATA["transactions"][
        (DATA["transactions"]["user_id"] == user_id) & 
        (DATA["transactions"]["transaction_type"] == "debit")
    ]
    
    monthly_totals = user_transactions.groupby(["year", "month"])["amount"].sum()
    
    trends = []
    for (year, month), amount in monthly_totals.tail(months).items():
        trends.append({
            "month": f"{year}-{month:02d}",
            "total_spending": float(amount)
        })
    
    return {
        "spending_trends": trends,
        "average_monthly_spending": float(monthly_totals.tail(months).mean()),
        "highest_month": float(monthly_totals.tail(months).max()),
        "lowest_month": float(monthly_totals.tail(months).min())
    }

@tool
def get_savings_rate(user_id: str = USER_ID) -> Dict[str, Any]:
    """Calculate savings rate"""
    if DATA is None:
        return {"error": "Data not loaded"}
    
    user_data = DATA["transactions"][DATA["transactions"]["user_id"] == user_id]
    
    income = user_data[user_data["transaction_type"] == "credit"]["amount"].sum()
    expenses = user_data[user_data["transaction_type"] == "debit"]["amount"].sum()
    savings = income - expenses
    
    return {
        "total_income": float(income),
        "total_expenses": float(expenses),
        "total_savings": float(savings),
        "savings_rate": float((savings / income) * 100) if income > 0 else 0,
        "savings_per_month": float(savings / 60) if income > 0 else 0  # Approximate months
    }

@tool
def get_group_expenses_summary(user_id: str = USER_ID) -> Dict[str, Any]:
    """Get group expense summary"""
    if DATA is None:
        return {"error": "Data not loaded"}
    
    user_group_expenses = DATA["group_expenses"][DATA["group_expenses"]["user_id"] == user_id]
    
    paid = user_group_expenses[user_group_expenses["paid_status"] == "Paid"]
    pending = user_group_expenses[user_group_expenses["paid_status"] == "Pending"]
    
    return {
        "total_group_expenses": float(user_group_expenses["user_share"].sum()),
        "amount_paid": float(paid["user_share"].sum()),
        "amount_pending": float(pending["user_share"].sum()),
        "expenses_by_type": user_group_expenses.groupby("expense_name")["user_share"].sum().to_dict(),
        "pending_count": len(pending)
    }

@tool
def get_financial_goals(user_id: str = USER_ID) -> Dict[str, Any]:
    """Get financial goals status"""
    if DATA is None:
        return {"error": "Data not loaded"}
    
    user_goals = DATA["user_goals"][DATA["user_goals"]["user_id"] == user_id]
    
    goals_list = []
    for _, goal in user_goals.iterrows():
        goals_list.append({
            "goal_name": goal["goal_name"],
            "target_amount": float(goal["target_amount"]),
            "current_savings": float(goal["current_savings"]),
            "progress_percentage": float(goal["progress_percentage"]),
            "deadline": goal["deadline"],
            "status": goal["status"]
        })
    
    return {
        "total_goals": len(user_goals),
        "goals": goals_list,
        "total_target": float(user_goals["target_amount"].sum()),
        "total_saved": float(user_goals["current_savings"].sum()),
        "overall_progress": float((user_goals["current_savings"].sum() / user_goals["target_amount"].sum()) * 100) if len(user_goals) > 0 else 0
    }

@tool
def get_user_profile(user_id: str = USER_ID) -> Dict[str, Any]:
    """Get user profile information"""
    if DATA is None:
        return {"error": "Data not loaded"}
    
    user = DATA["users"][DATA["users"]["user_id"] == user_id]
    
    if user.empty:
        return {"error": "User not found"}
    
    user_data = user.iloc[0]
    
    return {
        "user_id": user_data["user_id"],
        "name": user_data["name"],
        "monthly_salary": float(user_data["monthly_salary"]),
        "savings_rate": float(user_data["savings_rate"]),
        "spending_personality": user_data["spending_personality"],
        "risk_tolerance": user_data["risk_tolerance"]
    }

@tool
def search_events_by_date(date: str = None, user_id: str = USER_ID) -> Dict[str, Any]:
    """Search for events on a specific date (format: YYYY-MM-DD). If no date provided, returns all events."""
    if DATA is None:
        return {"error": "Data not loaded"}
    
    user_events = DATA["calendar_events"][DATA["calendar_events"]["user_id"] == user_id]
    
    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}
        
        user_events = user_events[user_events["event_date"] == date]
    
    if user_events.empty:
        return {
            "date": date or "all",
            "events": [],
            "message": f"No events found" + (f" on {date}" if date else "")
        }
    
    events = []
    for _, event in user_events.iterrows():
        events.append({
            "event_name": event["event_name"],
            "event_type": event["event_type"],
            "event_date": event["event_date"],
            "predicted_expense": float(event["predicted_expense"]),
            "is_recurring": event["is_recurring"]
        })
    
    return {
        "event_count": len(events),
        "events": events,
        "total_predicted_expense": float(user_events["predicted_expense"].sum())
    }

@tool
def search_shopping_transactions(user_id: str = USER_ID, year: int = None) -> Dict[str, Any]:
    """Get all shopping transaction dates. Optionally filter by year (e.g., 2024)"""
    if DATA is None:
        return {"error": "Data not loaded"}
    
    shopping_txns = DATA["transactions"][
        (DATA["transactions"]["user_id"] == user_id) &
        (DATA["transactions"]["category"] == "Shopping") &
        (DATA["transactions"]["transaction_type"] == "debit")
    ]
    
    if year:
        shopping_txns = shopping_txns[shopping_txns["year"] == year]
    
    if shopping_txns.empty:
        return {
            "message": f"No shopping transactions found" + (f" in {year}" if year else ""),
            "dates": [],
            "total_spent": 0
        }
    
    # Group by date
    dates_list = shopping_txns.groupby("date").agg({
        "amount": ["sum", "count"]
    }).reset_index()
    
    dates_data = []
    for _, row in dates_list.iterrows():
        dates_data.append({
            "date": row["date"],
            "transaction_count": int(row[("amount", "count")]),
            "total_amount": float(row[("amount", "sum")])
        })
    
    return {
        "year": year or "all years",
        "total_shopping_dates": len(dates_data),
        "shopping_dates": dates_data,
        "total_shopping_spent": float(shopping_txns["amount"].sum())
    }

# ==================== LANGGRAPH STATE ====================

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str

# ==================== AGENT SETUP ====================

tools = [
    get_spending_by_category,
    get_highest_spending_category,
    get_monthly_spending,
    get_income_vs_expenses,
    get_investment_portfolio,
    get_upcoming_events,
    get_spending_trends,
    get_savings_rate,
    get_group_expenses_summary,
    get_financial_goals,
    get_user_profile,
    search_events_by_date,
    search_shopping_transactions
]

def create_system_prompt(user_id: str):
    """Create a dynamic system prompt with user context"""
    return f"""You are FINSIGHT, an intelligent AI financial advisor chatbot. You help users understand their spending patterns, investments, goals, and provide personalized financial insights.

Current User ID: {user_id}

Your capabilities:
1. Analyze spending patterns by category
2. Provide income vs expense analysis
3. Track investments and portfolio performance
4. Monitor upcoming expenses and events
5. Calculate savings rates and trends
6. Manage group expenses
7. Track financial goals progress
8. Identify spending anomalies and provide recommendations

Guidelines:
- Always use the available tools to fetch real data before answering
- Provide specific, actionable insights
- Format numbers with rupee symbol (₹) for Indian currency
- Be friendly, professional, and helpful
- Suggest optimization opportunities when relevant
- Explain complex financial concepts simply
- When user asks a general question, try to relate it to their personal financial data

Remember: Your goal is to empower users to make smarter financial decisions."""

def should_use_tools(state: AgentState) -> bool:
    """Determine if tools should be used"""
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage):
        return "tool_calls" in last_message.additional_kwargs
    return True

def call_tools(state: AgentState):
    """Execute tool calls"""
    last_message = state["messages"][-1]
    tool_calls = last_message.additional_kwargs.get("tool_calls", [])
    
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call["function"]["name"]
        tool_input = json.loads(tool_call["function"]["arguments"])
        
        # Ensure user_id is set
        if "user_id" not in tool_input:
            tool_input["user_id"] = state["user_id"]
        
        # Execute tool
        tool = next((t for t in tools if t.name == tool_name), None)
        if tool:
            result = tool.invoke(tool_input)
            results.append({
                "tool_name": tool_name,
                "result": result
            })
    
    # Format results as message
    tool_results_msg = f"Tool Results:\n{json.dumps(results, indent=2)}"
    return {"messages": [HumanMessage(content=tool_results_msg)]}

def agent_node(state: AgentState):
    """Main agent node"""
    user_id = state["user_id"]
    messages = state["messages"]
    
    # Create system prompt
    system_prompt = create_system_prompt(user_id)
    
    # Prepare messages with system context
    full_messages = [SystemMessage(content=system_prompt)] + messages
    
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # Get response from LLM
    response = llm_with_tools.invoke(full_messages)
    
    return {"messages": [response]}

# ==================== BUILD GRAPH ====================

def build_agent_graph():
    """Build the LangGraph agent"""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", call_tools)
    
    # Add edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_use_tools,
        {
            True: "tools",
            False: END
        }
    )
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()

# ==================== CHATBOT INTERFACE ====================

def run_chatbot(user_id: str = USER_ID):
    """Run the chatbot"""
    graph = build_agent_graph()
    
    print(f"\n{'='*60}")
    print(f"FINSIGHT AI Financial Chatbot")
    print(f"User ID: {user_id}")
    print(f"{'='*60}\n")
    print("Type 'exit' to quit\n")
    
    messages = []
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        messages.append(HumanMessage(content=user_input))
        
        # Run agent
        state = {
            "messages": messages,
            "user_id": user_id
        }
        
        result = graph.invoke(state)
        
        # Extract and display response
        last_message = result["messages"][-1]
        if isinstance(last_message, AIMessage):
            print(f"\nFINSIGHT: {last_message.content}\n")
            messages = result["messages"]

# ==================== MAIN ====================

# if __name__ == "__main__":
#     # Test chatbot with default user U001
#     run_chatbot(USER_ID)