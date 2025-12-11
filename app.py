import streamlit as st
import json
import os
import textwrap
import urllib.parse
import google.generativeai as genai
from streamlit_agraph import agraph, Node, Edge, Config

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Monarque Care Journey Navigator")

# --- CSS for Styling ---
st.markdown("""
<style>
    /* ADAPTIVE CARD STYLING */
    .deep-dive-card {
        background-color: var(--secondary-background-color);
        color: var(--text-color);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        height: 100%;
    }
    .deep-dive-card p {
        margin-bottom: 10px;
        line-height: 1.4;
        font-size: 0.95em;
    }
    .highlight-title {
        color: #10b981; /* Emerald Green for Monarque */
        font-weight: bold;
        font-size: 1.0em;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* FORCE GRAPH BACKGROUND */
    iframe {
        background-color: #0e1117 !important;
    }

    /* Button Tweaks */
    .stButton button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. State Management ---
if 'graph_data' not in st.session_state:
    st.session_state.graph_data = None
if 'token_usage' not in st.session_state:
    st.session_state.token_usage = 0
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

    # --- MONARQUE CAREGIVING PROMPT LOGIC ---
    system_instruction = f"""
    You are an Expert Caregiving Consultant for Monarque Solutions. 
    Your goal is to reduce cognitive load for employees facing a crisis by visualizing a clear path forward.
    
    CONTEXT:
    The user is an employee balancing work and a caregiving crisis. They are likely overwhelmed.
    
    USER INPUT SCENARIO: "{user_input}"
    
    TASK:
    1. CENTER NODE: The Caregiving Event (e.g., "Post-Stroke Recovery" or "Dementia Diagnosis").
    2. LAYER 1 (Immediate Actions): Identify 4-5 tactical, high-priority steps the employee must take RIGHT NOW (Medical, Legal, Logistical, or Workplace communication).
    3. LAYER 2 (Support Resources): For EACH Action, connect it to a specific RESOURCE.
       - Connect "Workplace Actions" to corporate benefits (e.g., "EAP Legal Services", "Flexible Work Policy", "FMLA/Leave").
       - Connect "Care Actions" to community resources (e.g., "Area Agency on Aging", "Alzheimer's Association", "Social Worker").

    OUTPUT JSON STRUCTURE:
    {{
        "center_node": {{
            "name": "Corrected Scenario Name",
            "type": "Crisis Event",
            "mission": "This is a high-stress moment. Here is your immediate roadmap to stabilize the situation.",
            "positive_news": "You are not alone. Resources exist to help you manage this.",
            "red_flags": "Watch out for caregiver burnout—prioritize your own sleep and legal paperwork early."
        }},
        "connections": [
            {{
                "name": "Immediate Action 1",
                "reason": "Why is this urgent?",
                "sub_connections": [
                    {{"name": "Specific Company/Community Resource", "reason": "How does this help?"}}
                ]
            }}
        ]
    }}
    """
    
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        with st.spinner(f"🔍 Mapping Support Ecosystem..."):
            response = model.generate_content(system_instruction)
        
        # Track Tokens & Cost
        input_tokens = len(system_instruction) / 4
        output_tokens = len(response.text) / 4
        st.session_state.token_usage += (input_tokens + output_tokens)
        st.session_state.session_cost += 0.003

        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
        
    except Exception as e:
        st.error(f"AI Analysis Error: {e}")
        return None

# --- 3. Sidebar Controls ---
with st.sidebar:
    st.title("Monarque Care Navigator")
    
    tab_main, tab_about, tab_model = st.tabs(["🧭 Navigation", "ℹ️ About", "🧠 Model Card"])
    
    # --- TAB 1: CONTROLS ---
    with tab_main:
        st.markdown("Map your journey from **Crisis** to **Stability**.")
        st.info("Enter your current situation below to generate a personalized support map.")
        
        st.divider()
        
        # --- INPUT: CRISIS CONTEXT ---
        user_scenario = st.text_input("What is happening?", 
            placeholder="e.g., Mom was just diagnosed with Dementia",
            help="Be specific. Examples: 'Father had a stroke', 'Spouse surgery recovery', 'Finding assisted living'.")
        
        st.divider()

        if st.button("🚀 Generate Support Map", type="primary", key="launch_btn"):
            if user_scenario:
                st.session_state.should_fetch = True
                st.session_state.graph_data = None 
                st.rerun()
            else:
                st.warning("Please describe your situation first.")

        if st.button("🗑️ Clear Map"):
            st.session_state.graph_data = None
            st.session_state.should_fetch = False
            st.rerun()
        
        st.divider()
        st.caption("Session Monitor")
        st.metric("Total Cost", f"${st.session_state.session_cost:.3f}", help="Calculated at ~$0.003 per query")

    # --- TAB 2: ABOUT ---
    with tab_about:
        st.subheader("Monarque Solutions")
        st.markdown("""
        **Transforming How We Work and Care.**
        
        We help organizations mitigate the economic and cultural impact of caregiving.
        
        * **Identify** at-risk populations.
        * **Educate** managers to lead with empathy.
        * **Support** employees with structured roadmaps.
        """)
        
        st.markdown("### 🌐 Connect")
        st.link_button("🏠 MonarqueSolutions.com", "https://www.monarquesolutions.com")
        
        st.divider()
        st.caption("Powered by DoubleLucky.ai")

    # --- TAB 3: MODEL CARD ---
    with tab_model:
        st.subheader("🧠 Model Card")
        st.caption("Transparency on how this tool works.")
        
        st.markdown("""
        **Project:** Care Journey Navigator  
        **Model Engine:** Google Gemini 1.5 Flash  
        **Purpose:** To map complex caregiving life events to actionable steps and available resources.

        #### 🎯 Intended Use
        * **User:** Employees balancing work & caregiving.
        * **Goal:** Reduce cognitive load during crisis.
        * **Output:** A 3-layer graph: Crisis $\\rightarrow$ Actions $\\rightarrow$ Resources.

        #### ⚙️ Logic
        The model acts as a **Care Consultant**, prioritizing:
        1.  **Immediate Safety/Legal needs** (Power of Attorney, Discharge Planning).
        2.  **Corporate Benefits** often overlooked (EAP, Leave, Flex Time).
        3.  **Community Support** (Non-profits, Government agencies).

        #### ⚠️ Advisory
        * **Not Medical/Legal Advice:** This tool provides *guidance*, not diagnosis or legal counsel.
        * **Verification:** Always verify benefit eligibility with your HR department.
        """)

# --- 4. Main Logic ---
if st.session_state.should_fetch and user_scenario:
    data = get_gemini_response(user_scenario)
    if data:
        st.session_state.graph_data = data
        st.session_state.should_fetch = False 
        st.rerun()

# --- 5. Layout Rendering ---
data = st.session_state.graph_data

if data:
    center_info = data['center_node']
    connections = data['connections']

    # --- CENTER COLUMN: Graph ---
    nodes = []
    edges = []
    node_ids = set()

    # Define High-Contrast Font
    high_contrast_font = {
        'color': 'white',
        'strokeWidth': 4,       
        'strokeColor': 'black'  
    }

    # Center Node (The Crisis) - RED/ORANGE for Urgency
    nodes.append(Node(
        id=center_info['name'], 
        label=center_info['name'], 
        size=45, 
        color="#FF4B4B", 
        font=high_contrast_font, 
        shape="dot"
    ))
    node_ids.add(center_info['name'])

    for item in connections:
        # Layer 1: Immediate Actions - BLUE for Clarity
        if item['name'] not in node_ids:
            nodes.append(Node(
                id=item['name'], 
                label=item['name'], 
                size=30, 
                color="#00C0F2", 
                font=high_contrast_font, 
                title=item['reason']
            ))
            node_ids.add(item['name'])
        
        edges.append(Edge(
            source=center_info['name'], 
            target=item['name'], 
            color="#808080",
            width=3
        ))

        # Layer 2: Resources - GREEN for Support/Relief
        if 'sub_connections' in item:
            for sub in item['sub_connections']:
                if sub['name'] not in node_ids:
                    nodes.append(Node(
                        id=sub['name'], 
                        label=sub['name'], 
                        size=20, 
                        color="#1DB954", 
                        font=high_contrast_font, 
                        title=f"Support Resource: {sub['reason']}",
                        shape="diamond"
                    ))
                    node_ids.add(sub['name'])
                
                edges.append(Edge(
                    source=item['name'], 
                    target=sub['name'], 
                    color="#404040", 
                    width=1,
                    dashes=True
                ))

    # Config
    config = Config(
        width=1200,
        height=600,
        directed=True, 
        physics=True, 
        hierarchical=False, 
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=True,
        backgroundColor="#0e1117" 
    )

    col_main, col_right = st.columns([3, 1])
    
    with col_main:
        st.subheader(f"Care Map: {center_info['name']}")
        st.info("💡 **Tip:** Click on the **Green Diamonds** to see how company benefits or community groups can help you with that specific task.")
        clicked_node = agraph(nodes=nodes, edges=edges, config=config)

    # --- RIGHT COLUMN: Details ---
    with col_right:
        st.subheader("📝 Action Details")
        
        selected_node_name = clicked_node if clicked_node else center_info['name']
        
        display_text = ""
        display_sub = ""
        
        if selected_node_name == center_info['name']:
            display_text = center_info['mission']
            display_sub = center_info['positive_news']
        else:
            found = False
            for c in connections:
                if c['name'] == selected_node_name:
                    display_text = c['reason']
                    display_sub = "Recommended Resources:"
                    for sub in c.get('sub_connections', []):
                        display_sub += f"\n- {sub['name']}"
                    found = True
                    break
                for sub in c.get('sub_connections', []):
                    if sub['name'] == selected_node_name:
                        display_text = sub['reason']
                        display_sub = f"Supports action: {c['name']}"
                        found = True
                        break
            if not found:
                display_text = "Node details not found."

        # Adaptive Card
        st.markdown(f"""
        <div class="deep-dive-card">
            <div class="highlight-title">{selected_node_name}</div>
            <p>{display_text}</p>
            <p><i>{display_sub}</i></p>
        </div>
        """, unsafe_allow_html=True)
            
        st.divider()
        if selected_node_name != center_info['name']:
            # Search logic tailored for Caregiving
            query = urllib.parse.quote(f"{selected_node_name} help and resources")
            st.link_button("🔎 Find Help (Google)", f"https://www.google.com/search?q={query}")

else:
    # Landing State
    st.markdown("""
    <div style="text-align: center; padding: 50px;">
        <h1>🧭 Welcome to the Care Journey Navigator</h1>
        <p>Caregiving is complex. We make the next step clear.</p>
        <p style="font-size: 0.9em; color: gray;">Enter your current situation on the left to generate a personalized support map.</p>
    </div>
    """, unsafe_allow_html=True)
