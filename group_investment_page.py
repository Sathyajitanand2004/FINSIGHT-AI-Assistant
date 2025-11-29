import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json
import time

# File paths for persistent storage
ROOMS_FILE = 'data/rooms_data.json'
MESSAGES_FILE = 'data/room_messages.json'
TRANSACTIONS_FILE = 'data/room_transactions.json'

def init_storage_files():
    """Initialize storage files if they don't exist"""
    os.makedirs('data', exist_ok=True)
    
    if not os.path.exists(ROOMS_FILE):
        default_rooms = {
            'Group Investment': {'members': {}, 'total_pool': 0},
            'Travel Plan': {'members': {}, 'total_pool': 0}
        }
        with open(ROOMS_FILE, 'w') as f:
            json.dump(default_rooms, f)
    
    if not os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'w') as f:
            json.dump({}, f)
    
    if not os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, 'w') as f:
            json.dump({}, f)

def load_rooms():
    """Load rooms data from file"""
    try:
        with open(ROOMS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {
            'Group Investment': {'members': {}, 'total_pool': 0},
            'Travel Plan': {'members': {}, 'total_pool': 0}
        }

def save_rooms(rooms_data):
    """Save rooms data to file"""
    with open(ROOMS_FILE, 'w') as f:
        json.dump(rooms_data, f, indent=2)

def load_messages(room_name):
    """Load messages for a specific room"""
    try:
        with open(MESSAGES_FILE, 'r') as f:
            all_messages = json.load(f)
            return all_messages.get(room_name, [])
    except:
        return []

def save_message(room_name, message):
    """Save a new message to the room"""
    try:
        with open(MESSAGES_FILE, 'r') as f:
            all_messages = json.load(f)
    except:
        all_messages = {}
    
    if room_name not in all_messages:
        all_messages[room_name] = []
    
    all_messages[room_name].append(message)
    
    # Keep only last 100 messages per room
    if len(all_messages[room_name]) > 100:
        all_messages[room_name] = all_messages[room_name][-100:]
    
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(all_messages, f, indent=2)

def load_transactions(room_name, user_id):
    """Load transactions for a specific room and user"""
    try:
        with open(TRANSACTIONS_FILE, 'r') as f:
            all_transactions = json.load(f)
            room_transactions = all_transactions.get(room_name, {})
            return room_transactions.get(user_id, [])
    except:
        return []

def save_transaction(room_name, user_id, transaction):
    """Save a transaction for a user in a room"""
    try:
        with open(TRANSACTIONS_FILE, 'r') as f:
            all_transactions = json.load(f)
    except:
        all_transactions = {}
    
    if room_name not in all_transactions:
        all_transactions[room_name] = {}
    
    if user_id not in all_transactions[room_name]:
        all_transactions[room_name][user_id] = []
    
    all_transactions[room_name][user_id].append(transaction)
    
    with open(TRANSACTIONS_FILE, 'w') as f:
        json.dump(all_transactions, f, indent=2)

def render_group_investment_page(user_id, DATA):
    """Render the Group Investment & Split page with real-time chat"""
    
    st.title("💰 Group Investment & Expense Split")
    st.markdown("Create rooms, chat with members in real-time, and split expenses or share profits!")
    
    # Initialize storage files
    init_storage_files()
    
    # Load rooms data
    rooms_data = load_rooms()
    
    # Get user name
    user_name = DATA['users'][DATA['users']['user_id'] == user_id]['name'].values[0]
    
    # Auto-refresh for real-time updates
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    # Room selection
    st.markdown("### 🏠 Select a Room")
    room_options = list(rooms_data.keys())
    selected_room = st.selectbox("Choose a room to join:", room_options, key="room_selector")
    
    st.markdown("---")
    
    # Check if user is already in the room
    room_members = rooms_data[selected_room].get('members', {})
    is_member = user_id in room_members
    
    if not is_member:
        # Entry form - Ask for contribution
        st.markdown(f"### 🚪 Join Room: *{selected_room}*")
        st.info(f"👋 Welcome {user_name}! Enter your contribution amount to join this room.")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            contribution = st.number_input(
                "Your Contribution Amount (₹):",
                min_value=0.0,
                step=100.0,
                key=f"contribution_{selected_room}"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✅ Join Room", use_container_width=True):
                if contribution > 0:
                    # Add user to room
                    rooms_data[selected_room]['members'][user_id] = {
                        'name': user_name,
                        'contribution': contribution
                    }
                    rooms_data[selected_room]['total_pool'] = rooms_data[selected_room].get('total_pool', 0) + contribution
                    save_rooms(rooms_data)
                    
                    # Add system message
                    system_msg = {
                        'user_id': 'system',
                        'name': 'System',
                        'message': f"🎉 {user_name} joined the room!",
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    save_message(selected_room, system_msg)
                    
                    st.success(f"✅ You joined {selected_room} with ₹{contribution:,.2f}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Please enter a valid contribution amount!")
    
    else:
        # User is a member - Show room interface
        room_data = rooms_data[selected_room]
        user_contribution = room_members[user_id]['contribution']
        
        # Calculate contribution percentage
        total_pool = room_data.get('total_pool', 0)
        contribution_percentage = (user_contribution / total_pool * 100) if total_pool > 0 else 0
        
        # Room Header
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Your Contribution", f"₹{user_contribution:,.2f}")
        with col2:
            st.metric("📊 Your Share", f"{contribution_percentage:.1f}%")
        with col3:
            st.metric("🏦 Total Pool", f"₹{total_pool:,.2f}")
        with col4:
            st.metric("👥 Members", f"{len(room_members)}")
        
        st.markdown("---")
        
        # Split tabs
        tab1, tab2, tab3 = st.tabs(["💬 Real-Time Chat", "💸 Split/Profit", "📜 Your Transactions"])
        
        # TAB 1: REAL-TIME CHAT
        with tab1:
            st.markdown("### 💬 Live Group Chat")
            
            # Auto-refresh button
            col_refresh, col_info = st.columns([1, 3])
            with col_refresh:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()
            with col_info:
                st.caption("💡 Messages update every 3 seconds automatically")
            
            # Display messages
            messages = load_messages(selected_room)
            
            # Create scrollable chat container
            chat_container = st.container()
            with chat_container:
                if messages:
                    # Show last 30 messages
                    for msg in messages[-30:]:
                        if msg['user_id'] == 'system':
                            st.info(f"🤖 {msg['message']}")
                        elif msg['user_id'] == user_id:
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                        padding: 12px; border-radius: 15px; margin: 8px 0; 
                                        text-align: right; color: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                                <strong>You</strong> <small style="opacity: 0.8;">({msg['timestamp']})</small><br>
                                <span style="font-size: 1.1em;">{msg['message']}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="background: #f0f2f6; padding: 12px; border-radius: 15px; 
                                        margin: 8px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                                <strong style="color: #1f77b4;">{msg['name']}</strong> 
                                <small style="color: #666;">({msg['timestamp']})</small><br>
                                <span style="font-size: 1.1em; color: #333;">{msg['message']}</span>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("💭 No messages yet. Start the conversation!")
            
            st.markdown("---")
            
            # Message input - using form for better UX
            with st.form(key=f"message_form_{selected_room}", clear_on_submit=True):
                col1, col2 = st.columns([5, 1])
                with col1:
                    new_message = st.text_input(
                        "Type your message:",
                        key=f"msg_input_{selected_room}",
                        placeholder="Type something...",
                        label_visibility="collapsed"
                    )
                with col2:
                    send_button = st.form_submit_button("📤 Send", use_container_width=True)
                
                if send_button and new_message.strip():
                    message_data = {
                        'user_id': user_id,
                        'name': user_name,
                        'message': new_message.strip(),
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    save_message(selected_room, message_data)
                    st.rerun()
        
        # TAB 2: SPLIT/PROFIT
        with tab2:
            st.markdown("### 💸 Split Expenses or Share Profits")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📉 Split Expense")
                st.caption("Deduct proportionally from all members")
                expense_amount = st.number_input("Total Expense Amount (₹):", min_value=0.0, step=50.0, key="expense_amt")
                expense_desc = st.text_input("Description:", placeholder="e.g., Hotel booking", key="expense_desc")
                
                if st.button("💳 Split Expense", use_container_width=True, type="primary"):
                    if expense_amount > 0 and expense_desc.strip():
                        split_success = split_expense(
                            selected_room, user_id, user_name, expense_amount, 
                            expense_desc, rooms_data
                        )
                        if split_success:
                            st.success(f"✅ Expense of ₹{expense_amount:,.2f} split successfully!")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.error("Please enter valid amount and description!")
            
            with col2:
                st.markdown("#### 📈 Share Profit")
                st.caption("Distribute proportionally to all members")
                profit_amount = st.number_input("Total Profit Amount (₹):", min_value=0.0, step=50.0, key="profit_amt")
                profit_desc = st.text_input("Description:", placeholder="e.g., Investment returns", key="profit_desc")
                
                if st.button("💰 Share Profit", use_container_width=True, type="secondary"):
                    if profit_amount > 0 and profit_desc.strip():
                        profit_success = share_profit(
                            selected_room, user_id, user_name, profit_amount,
                            profit_desc, rooms_data
                        )
                        if profit_success:
                            st.success(f"✅ Profit of ₹{profit_amount:,.2f} shared successfully!")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.error("Please enter valid amount and description!")
            
            st.markdown("---")
            st.markdown("### 👥 Room Members (Private View)")
            st.caption("⚠ You can only see your own contribution. Others' contributions are hidden for privacy.")
            
            members_data = []
            for member_id, member_info in room_members.items():
                if member_id == user_id:
                    members_data.append({
                        'Member': f"{member_info['name']} (You)",
                        'Contribution': f"₹{member_info['contribution']:,.2f}",
                        'Share %': f"{(member_info['contribution']/total_pool*100):.2f}%"
                    })
                else:
                    members_data.append({
                        'Member': member_info['name'],
                        'Contribution': '🔒 Hidden',
                        'Share %': '🔒 Hidden'
                    })
            
            st.dataframe(members_data, use_container_width=True, hide_index=True)
        
        # TAB 3: USER'S TRANSACTION HISTORY
        with tab3:
            st.markdown("### 📜 Your Recent Transactions")
            st.info("⚠ Only you can see your transactions. Other members cannot view this.")
            
            # Load transactions for this user in this room
            transactions = load_transactions(selected_room, user_id)
            
            if transactions:
                # Convert to DataFrame for display
                df = pd.DataFrame(transactions)
                
                # Format amounts
                df['your_share'] = df['your_share'].apply(lambda x: f"₹{x:,.2f}")
                df['total_amount'] = df['total_amount'].apply(lambda x: f"₹{x:,.2f}")
                
                # Rename columns
                df = df[['timestamp', 'type', 'description', 'your_share', 'total_amount']]
                df.columns = ['Date & Time', 'Type', 'Description', 'Your Share', 'Total Amount']
                
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Summary
                transactions_data = pd.DataFrame(transactions)
                total_expenses = transactions_data[transactions_data['type'] == 'expense']['your_share'].sum()
                total_profits = transactions_data[transactions_data['type'] == 'profit']['your_share'].sum()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📉 Total Expenses", f"₹{total_expenses:,.2f}")
                with col2:
                    st.metric("📈 Total Profits", f"₹{total_profits:,.2f}")
                with col3:
                    net = total_profits - total_expenses
                    st.metric("💰 Net Balance", f"₹{net:,.2f}", delta=f"{net:,.2f}")
            else:
                st.info("No transactions yet in this room.")
    
    # Auto-refresh mechanism (refresh every 3 seconds for real-time chat)
    time.sleep(0.1)
    if time.time() - st.session_state.last_refresh > 3:
        st.session_state.last_refresh = time.time()
        st.rerun()


def split_expense(room_name, user_id, user_name, expense_amount, description, rooms_data):
    """Split expense among room members based on their contribution percentage"""
    try:
        room_data = rooms_data[room_name]
        total_pool = room_data.get('total_pool', 0)
        members = room_data.get('members', {})
        
        if total_pool == 0:
            st.error("Cannot split expense: Total pool is zero!")
            return False
        
        # Calculate and save transaction for each member
        for member_id, member_info in members.items():
            contribution = member_info['contribution']
            percentage = contribution / total_pool
            member_share = expense_amount * percentage
            
            # Save transaction for this member
            transaction = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': 'expense',
                'description': description,
                'total_amount': expense_amount,
                'your_share': member_share,
                'percentage': percentage * 100
            }
            save_transaction(room_name, member_id, transaction)
        
        # Add system message to chat
        system_msg = {
            'user_id': 'system',
            'name': 'System',
            'message': f"💳 {user_name} split an expense: {description} (₹{expense_amount:,.2f})",
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_message(room_name, system_msg)
        
        return True
    except Exception as e:
        st.error(f"Error splitting expense: {e}")
        return False


def share_profit(room_name, user_id, user_name, profit_amount, description, rooms_data):
    """Share profit among room members based on their contribution percentage"""
    try:
        room_data = rooms_data[room_name]
        total_pool = room_data.get('total_pool', 0)
        members = room_data.get('members', {})
        
        if total_pool == 0:
            st.error("Cannot share profit: Total pool is zero!")
            return False
        
        # Calculate and save transaction for each member
        for member_id, member_info in members.items():
            contribution = member_info['contribution']
            percentage = contribution / total_pool
            member_profit = profit_amount * percentage
            
            # Save transaction for this member
            transaction = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': 'profit',
                'description': description,
                'total_amount': profit_amount,
                'your_share': member_profit,
                'percentage': percentage * 100
            }
            save_transaction(room_name, member_id, transaction)
        
        # Add system message to chat
        system_msg = {
            'user_id': 'system',
            'name': 'System',
            'message': f"💰 {user_name} shared a profit: {description} (₹{profit_amount:,.2f})",
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_message(room_name, system_msg)
        
        return True
    except Exception as e:
        st.error(f"Error sharing profit: {e}")
        return False