import streamlit as st
import json
import os
import urllib.parse
import google.generativeai as genai

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Monarque Care Wizard")

# --- CSS for Styling ---
st.markdown("""
<style>
    /* Wizard Styling */
    .step-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: #10b981; /* Emerald Green */
        margin-top: 20px;
        margin-bottom: 10px;
        border-bottom: 1px solid #333;
        padding-bottom: 5px;
    }
    .resource-box {
        background-color: #1e293b; /* Dark Slate */
        border-left: 4px solid #3b82f6; /* Blue Accent */
        padding: 15px;
        border-radius: 5px;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .resource-title {
        font-weight: bold;
        color: #e2e8f0;
        margin-bottom: 5px;
    }
    .resource-desc {
        font-size: 0.9em;
        color: #cbd5e1;
    }
    /* Button Tweaks */
    .stButton button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. State Management ---
if 'wizard_data' not in st.session_state:
    st.session_state.wizard_data = None
if 'session_cost' not in st.session_state:
    st.session_state.session_cost = 0.0
if 'should_fetch' not in st.session_state:
    st.session_state.should_fetch = False

# --- 2. Google Gemini Setup ---
def get_gemini_response(user_input):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        st.error("⚠️ GEMINI_API_KEY not found! Check your Streamlit Secrets.")
        return None

    genai.configure(api_key=api_key)

    system_instruction = f"""
    You are an Expert Caregiving Consultant for Monarque Solutions. 
    
    CONTEXT:
    The user is an employee balancing work and a caregiving crisis. They are overwhelmed.
    USER INPUT: "{user_input}"
    
    TASK:
    Generate a step-by-step "Care Action Plan".
    1. SUMMARY: A reassuring 1-sentence overview of the situation.
    2. STEPS: Identify 4-5 distinct "Phases" or "Priorities" (e.g., Immediate Medical, Legal/Finance, Workplace, Self-Care).
    3. ACTIONS: Under each phase, list specific tactical steps and connect them to Monarque/Corporate resources.

    OUTPUT JSON STRUCTURE:
    {{
        "title": "Care Plan: [Scenario Name]",
        "summary": "Reassuring overview text...",
        "steps": [
            {{
                "phase": "Phase 1: Immediate Stabilization",
                "emoji": "🚨",
                "actions": [
                    {{
                        "task": "Secure Medical Power of Attorney",
                        "details": "You need legal authority to make decisions. Do not wait.",
                        "resource": "Benefit: EAP Legal Services (Free 30-min consult)"
                    }},
                    {{
                        "task": "Notify your Manager",
                        "details": "Send a brief email. You do not need to share medical details yet.",
                        "resource": "Template: Monarque 'Crisis Notification' Script"
                    }}
                ]
            }}
        ]
    }}
    """
    
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        with st.spinner(f"🔍 Generating Step-by-Step Plan..."):
            response = model.generate_content(system_instruction)
        
        st.session_state.session_cost += 0.003
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
        
    except Exception as e:
        st.error(f"AI Analysis Error: {e}")
        return None

# --- 3. Sidebar Controls ---
with st.sidebar:
    st.title("Monarque Care Wizard")
    st.markdown("Your step-by-step guide through crisis.")
    
    st.divider()
    
    # Input
    user_scenario = st.text_area("Describe your situation:", 
        height=100,
        placeholder="e.g., My father had a stroke and is being discharged tomorrow. I don't know what to do.",
        help="The more specific you are, the better the plan.")
    
    if st.button("🚀 Create Action Plan", type="primary"):
        if user_scenario:
            st.session_state.should_fetch = True
            st.session_state.wizard_data = None 
            st.rerun()
        else:
            st.warning("Please describe your situation first.")

    if st.button("🗑️ Clear Plan"):
        st.session_state.wizard_data = None
        st.session_state.should_fetch = False
        st.rerun()
        
    st.divider()
    st.markdown("### 🌐 Monarque Solutions")
    st.caption("Transforming How We Work and Care.")
    st.link_button("Visit Website", "https://www.monarquesolutions.com")

# --- 4. Main Logic ---
if st.session_state.should_fetch and user_scenario:
    data = get_gemini_response(user_scenario)
    if data:
        st.session_state.wizard_data = data
        st.session_state.should_fetch = False 
        st.rerun()

# --- 5. Layout Rendering (Wizard View) ---
data = st.session_state.wizard_data

if data:
    # Header Section
    st.title(data['title'])
    st.info(f"💡 **Advisor Note:** {data['summary']}")
    st.markdown("---")

    # Step-by-Step Loop
    for step in data['steps']:
        # We use an expander for each "Phase" to keep it clean
        with st.expander(f"{step['emoji']} {step['phase']}", expanded=True):
            
            for action in step['actions']:
                # Custom HTML container for each action item
                st.markdown(f"""
                <div class="resource-box">
                    <div class="resource-title">☐ {action['task']}</div>
                    <div class="resource-desc">{action['details']}</div>
                    <div style="margin-top:8px; font-size:0.85em; color:#10b981;">
                        <strong>⚡ Recommended Resource:</strong> {action['resource']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Dynamic "Find Help" button for each specific task
                col1, col2 = st.columns([4, 1])
                with col2:
                    query = urllib.parse.quote(f"{action['task']} resources")
                    st.link_button("🔎 Search", f"https://www.google.com/search?q={query}")

    # Footer / Next Steps
    st.markdown("---")
    st.success("You have a plan. Focus on Phase 1 today. Everything else can wait.")

else:
    # Landing State
    st.markdown("""
    <div style="text-align: center; padding: 60px;">
        <h1>📋 Ready to regain control?</h1>
        <p style="font-size: 1.2em; color: #cbd5e1;">
            Caregiving is overwhelming when you look at the whole mountain.<br>
            We help you focus on just the next step.
        </p>
        <p style="font-size: 0.9em; color: gray; margin-top: 20px;">
            Describe your situation on the left to generate a personalized checklist.
        </p>
    </div>
    """, unsafe_allow_html=True)
