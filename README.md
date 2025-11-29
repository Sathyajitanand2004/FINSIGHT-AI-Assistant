#  FINSIGHT – AI-Driven Context-Aware Financial Ecosystem

FINSIGHT is an **AI-driven financial companion** designed to revolutionize how individuals and groups understand, plan, and manage their money.  
It combines **predictive analytics, behavioral insights, calendar-aware forecasting, group expense fairness, and an AI chatbot** into one unified intelligent finance system.

An AI-driven financial companion that predicts expenses, analyzes spending patterns, and provides personalized budgeting and investment recommendations.  
Enabled proactive budgeting through calendar-based expense prediction and real-time financial insights.

---

##  Project Structure

```

FINSIGHT-AI-Assistant/
│── app.py
│── chatbot.py
│── chatbot_ui.py
│── calendar_page.py
│── calendar_model_load.py
│── dashboard.py
│── investment_page.py
│── investment_advisor.py
│── group_investment_page.py
│── data/
│── models/
│── .env
│── .gitignore
│── requirements.txt
│── README.md

````

---

##  Clone This Repository

Use the command below to pull the project:

```bash
git clone https://github.com/Sathyajitanand2004/FINSIGHT-AI-Assistant.git
````

Then move into the project folder:

```bash
cd FINSIGHT-AI-Assistant
```

---

##  Environment Setup

Create a `.env` file in the project root with:

```
GROQ_API_KEY=your_api_key_here
```

Make sure to replace `your_api_key_here` with the actual key.

---

##  Install Dependencies

All required libraries are in `requirements.txt`.

Install them using:

```bash
pip install -r requirements.txt
```

### **requirements.txt**

```
streamlit
pandas
numpy
plotly
python-dotenv
langchain
langchain-core
langchain-groq
langgraph
joblib
python-dateutil
typing_extensions
```

---

##  Run the Application

Start the Streamlit app:

```bash
python -m streamlit run app.py
```

Then open the URL shown in your terminal (usually: [http://localhost:8501](http://localhost:8501))

---

##  Key Features



###  1. **Interactive Financial Dashboard**
Built with Streamlit to visualize:
- Cash flow  
- Spending patterns  
- Forecast trends  
- Group financial activities  


---

###  2. **AI Chat Assistant (LangChain + LangGraph)**
A conversational LLM-powered assistant that:
- Answers finance-related queries  
- Provides personalized insights  
- Manages model outputs and real-time reasoning  
- Acts as your intelligent **Financial Coach**  


---

###  3. **Calendar-Based Expense Prediction (XGBoost Model)**
- Integrates user-selected dates, categories, and budget history  
- Predicts estimated spending with **~90% accuracy**  
- Labels budgets as **Good / Moderate / Bad**  
- Helps users prepare for upcoming financial events 

---

###  4. **Investment Portfolio Tracker**
- Tracks investments  
- Provides insights using AI-driven recommendations  
- Aligns suggestions with user liquidity & behavior  

---

###  5. **FairSplit – Collaborative Group Expense Manager**
A public shared “undi” room where:
- Participants add money  
- Split expenses fairly  
- Chat & collaborate  
- Uses **Explainable AI** for fairness scoring  


---

###  6. **Behavioral & Context-Aware Financial Analysis**
FINSIGHT uses:
- Spending behavior  
- Event context  
- Past financial patterns  
- Emotional/behavioral cues  
to generate proactive alerts and suggestions.  

---



##  Future Scope

According to the project vision roadmap (Page 8 of slides):

* Advanced AI engine for contextual forecasting
* Gamified financial coaching
* Real-time banking & fintech integrations
* Blockchain-enabled secure transactions
* Global expansion + B2B licensing model

---

##  Team – COLOSSAL CODERS

* Sathyajitanand V
* Dakxin Shaswath Haran Y
* S Goutham
* Darshan P

---

## ⭐ If you found this project useful, consider starring the repository!

