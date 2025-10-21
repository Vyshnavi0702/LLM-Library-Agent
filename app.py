import os
from dotenv import load_dotenv
import streamlit as st
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, Tool, AgentType

# Load environment variables from .env file
load_dotenv()

# --- Configuration and Initialization ---
# Ensure API Key is loaded
if "GOOGLE_API_KEY" not in os.environ:
    st.error("GOOGLE_API_KEY not found. Please ensure it is set in your .env file.")
    st.stop()


# Sample book database
books_db = {
    "Atomic Habits": {
        "author": "James Clear",
        "available": True,
        "location": {"floor": 1, "row": 3, "column": 5},
        "tags": ["self-help", "productivity"]
    },
    "Deep Work": {
        "author": "Cal Newport",
        "available": True,
        "location": {"floor": 2, "row": 1, "column": 2},
        "tags": ["focus", "career", "productivity"]
    },
    "Sapiens": {
        "author": "Yuval Noah Harari",
        "available": False,
        "location": {"floor": 1, "row": 2, "column": 4},
        "tags": ["history", "anthropology"]
    }
}

# Sample user loan data
user_loans = {
    "alekhya": [
        {"title": "Sapiens", "due_date": "2025-07-20"},
        {"title": "Atomic Habits", "due_date": "2025-07-25"}
    ],
    "suresh": [
        {"title": "Deep Work", "due_date": "2025-07-28"}
    ]
}

# Sample user preferences
user_interests = {
    "alekhya": ["history", "self-help"],
    "suresh": ["focus", "career"]
}

# Tool 1: Book search
def search_books(title: str) -> str:
    """Use to check book availability and location by title."""
    for book_title, book_info in books_db.items():
        if book_title.lower() == title.lower():
            if book_info["available"]:
                loc = book_info["location"]
                return (
                    f"📖 The book '{book_title}' is available.\n"
                    f"📍 Location → Floor {loc['floor']}, Row {loc['row']}, Column {loc['column']}."
                )
            else:
                return f"❌ The book '{book_title}' is currently unavailable."
    return f"🔍 No book titled '{title}' was found in the library."

# Tool 2: Recommendations
def get_recommendations(username: str) -> str:
    """Use to get book suggestions based on user interests. Input is username."""
    interests = user_interests.get(username.lower())
    if not interests:
        return f"🙁 No preference data found for user '{username}'."
    recs = []
    for title, info in books_db.items():
        # Check if book tags match user interests
        if any(tag in interests for tag in info.get("tags", [])):
            recs.append(f"- {title} by {info['author']}")
            
    if not recs:
        return f"📚 No recommendations available for {username}."
        
    return f"📌 Recommended books for {username}:\n" + "\n".join(recs)

# Tool 3: Fine calculator
def calculate_fine(username: str) -> str:
    """Use to calculate overdue fine for a user. Input is username."""
    today = datetime.today().date()
    total_fine = 0
    fines = []
    
    for loan in user_loans.get(username.lower(), []):
        try:
            due = datetime.strptime(loan["due_date"], "%Y-%m-%d").date()
            if today > due:
                days_overdue = (today - due).days
                fine = days_overdue * 5 # ₹5 per day
                total_fine += fine
                fines.append(f"🔻 {loan['title']} is overdue by {days_overdue} days → ₹{fine}")
        except ValueError:
            # Skip if date format is wrong
            continue
            
    if not fines:
        return f"✅ No overdue books for {username}."
        
    return f"⚠ Overdue books for {username}:\n" + "\n".join(fines) + f"\n\n💰 Total Fine: ₹{total_fine}"

# Tool 4: Due date reminders
def get_due_reminders(username: str) -> str:
    """Use to get reminders for books due soon. Input is username."""
    today = datetime.today().date()
    reminders = []
    
    for loan in user_loans.get(username.lower(), []):
        try:
            due = datetime.strptime(loan["due_date"], "%Y-%m-%d").date()
            days_left = (due - today).days
            if 0 <= days_left <= 3: # Due today or within 3 days
                reminders.append(f"⏰ {loan['title']} is due in {days_left} day(s) on {due}")
        except ValueError:
            continue
            
    if not reminders:
        return f"✅ No upcoming due dates for {username}."
        
    return f"🔔 Due date reminders for {username}:\n" + "\n".join(reminders)

# Register tools
tools = [
    Tool(name="SearchBooksTool", func=search_books, description="Use to check book availability and location by title."),
    Tool(name="GetRecommendations", func=get_recommendations, description="Use to get book suggestions based on user interests. Input is username."),
    Tool(name="CalculateFine", func=calculate_fine, description="Use to calculate overdue fine for a user. Input is username."),
    Tool(name="GetDueReminders", func=get_due_reminders, description="Use to get reminders for books due soon. Input is username.")
]

# Gemini LLM Initialization
llm = ChatGoogleGenerativeAI(
    model="models/gemini-1.5-pro-002",
    temperature=0.3,
)

# LangChain Agent Setup
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={
        "prefix": '''
You are LibroGenie – a smart college library assistant.
You can help with:

- Book search and location
- Personalized recommendations (based on user interests)
- Fine calculation for overdue books
- Reminding users of upcoming due dates

Always use the appropriate tool. Follow this reasoning structure:

Question: <user's question>
Thought: What tool should I use?
Action: <tool name>
Action Input: <input like book title or username>
Observation: <tool output>
Final Answer: <copy tool output exactly>

Begin!
'''
    }
)

# Streamlit UI
st.set_page_config(page_title="Library Assistant", page_icon="📚")
st.title("📚 Library Assistant with Gemini AI")
st.markdown("Try asking about: `Where is Atomic Habits?`, `What are Alekhya's fines?`, or `Suggest books for Suresh.`")


query = st.text_input("Ask a question (e.g., book location, recommendations, fine, due dates):")

if query:
    with st.spinner("Thinking..."):
        try:
            response = agent.run(query)
            st.success(response)
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")