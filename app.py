import streamlit as st
import json
import os
import urllib.parse
import google.generativeai as genai
from streamlit_react_flow import react_flow

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Monarque Care Navigator")

# --- CSS for Styling ---
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #FAFAFA;
    }
    .highlight-title {
        color: #10b981; /* Emerald Green */
        font-weight: bold;
    }
    .stButton button {
        width: 100%;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. State Management ---
if 'flow_state' not in st.session_state:
    st.session_state.flow_state = None
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
    The user is an employee in a caregiving crisis. 
    USER INPUT: "{user_input}"
    
    TASK:
    Generate a hierarchical care plan.
    1. ROOT: The Core Issue (e.g., "Stroke Recovery").
    2. PHASES: 3 Distinct Phases (e.g., Immediate, Short Term, Long Term).
    3. ACTIONS: 2-3 Specific Actions per Phase.
    4. RESOURCES: 1 Resource per Action (Company Benefit or Community Resource).

    OUTPUT JSON STRUCTURE:
    {{
        "root_node": "Name of Crisis",
        "phases": [
            {{
                "name": "Phase 1: Stabilization",
                "actions": [
                    {{
                        "task": "Secure Medical Power of Attorney",
                        "resource": "EAP Legal Services"
                    }},
                    {{
                        "task": "Notify Manager",
                        "resource": "HR Leave Policy"
                    }}
                ]
            }},
            {{
                "name": "Phase 2: Care Setup",
                "actions": [
                    {{
                        "task": "Find Rehab Facility",
                        "resource": "Local Agency on Aging"
                    }}
                ]
            }}
        ]
    }}
    """
    
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        with st.spinner(f"🔍 Designing your Care Map..."):
            response = model.generate_content(system_instruction)
        
        st.session_state.session_cost += 0.003
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
        
    except Exception as e:
        st.error(f"AI Analysis Error: {e}")
        return None

def build_react_flow_elements(ai_data):
    """
    Translates AI JSON into React Flow Nodes & Edges with auto-layout.
    Layout Strategy: Top-Down Tree
    - Root at (0,0)
    - Phases in a row below Root
    - Actions in columns below Phases
    """
    elements = []
    
    # 1. Root Node (The Crisis)
    root_id = "root"
    elements.append({
        "id": root_id,
        "type": "input",
        "data": {"label": ai_data['root_node']},
        "position": {"x": 400, "y": 0},
        "style": {
            "background": "#FF4B4B", 
            "color": "white", 
            "width": 200, 
            "fontWeight": "bold",
            "borderRadius": "10px",
            "border": "none"
        }
    })

    # Layout Configuration
    phase_y = 150
    action_y_start = 300
    action_y_gap = 120
    phase_x_start = 0
    phase_x_gap = 300

    # 2. Phases & Actions
    for p_idx, phase in enumerate(ai_data['phases']):
        phase_id = f"phase_{p_idx}"
        p_x = phase_x_start + (p_idx * phase_x_gap)
        
        # Add Phase Node
        elements.append({
            "id": phase_id,
            "data": {"label": phase['name']},
            "position": {"x": p_x, "y": phase_y},
            "style": {
                "background": "#10b981", # Monarque Green
                "color": "white", 
                "width": 220,
                "borderRadius": "5px",
                "border": "1px solid #fff"
            }
        })
        
        # Edge from Root -> Phase
        elements.append({
            "id": f"e_root_{phase_id}",
            "source": root_id,
            "target": phase_id,
            "animated": True,
            "style": {"stroke": "#888"}
        })

        # Add Action Nodes
        for a_idx, action in enumerate(phase['actions']):
            action_id = f"action_{p_idx}_{a_idx}"
            a_y = action_y_start + (a_idx * action_y_gap)
            
            # Action Node
            label_text = f"☐ {action['task']}\n(Resource: {action['resource']})"
            elements.append({
                "id": action_id,
                "data": {"label": label_text},
                "position": {"x": p_x, "y": a_y},
                "style": {
                    "background": "#1e293b", # Dark Slate
                    "color": "#cbd5e1",
                    "width": 220,
                    "fontSize": "12px",
                    "border": "1px solid #3b82f6" # Blue border
                }
            })
            
            # Edge from Phase -> Action
            elements.append({
                "id": f"e_{phase_id}_{action_id}",
                "source": phase_id,
                "target": action_id,
                "type": "smoothstep",
                "style": {"stroke": "#555"}
            })

    return elements

# --- 3. Sidebar Controls ---
with st.sidebar:
    st.title("Monarque Care Map")
    st.markdown("Interactive Roadmap Generator")
    st.divider()
    
    # Input
    user_scenario = st.text_area("Situation:", 
        height=100,
        placeholder="e.g. My partner was hospitalized for a heart condition.",
        help="Describe the crisis to generate a map.")
    
    if st.button("🚀 Map My Journey", type="primary"):
        if user_scenario:
            st.session_state.should_fetch = True
            st.session_state.flow_state = None 
            st.rerun()
        else:
            st.warning("Please describe the situation.")

    if st.button("🗑️ Clear"):
        st.session_state.flow_state = None
        st.session_state.should_fetch = False
        st.rerun()
        
    st.divider()
    st.markdown("### 🌐 Monarque Solutions")
    st.link_button("MonarqueSolutions.com", "https://www.monarquesolutions.com")
    st.caption(f"Session Cost: ${st.session_state.session_cost:.3f}")

# --- 4. Main Logic ---
if st.session_state.should_fetch and user_scenario:
    data = get_gemini_response(user_scenario)
    if data:
        st.session_state.flow_state = data
        st.session_state.should_fetch = False 
        st.rerun()

# --- 5. Layout Rendering ---
if st.session_state.flow_state:
    ai_data = st.session_state.flow_state
    
    st.subheader(f"Strategy: {ai_data['root_node']}")
    st.caption("Review your personalized care strategy below. Zoom and drag to explore.")
    
    # Build Elements
    elements = build_react_flow_elements(ai_data)
    
    # Render React Flow
    # We set a distinct styling for the flow container
    flowStyles = {
        "height": "600px", 
        "width": "100%", 
        "borderRadius": "10px",
        "backgroundColor": "#000000"
    }
    
    react_flow("care_map", elements=elements, flow_styles=flowStyles)
    
    st.success("Plan Generated. Focus on Phase 1.")

else:
    # Landing State
    st.markdown("""
    <div style="text-align: center; padding: 60px;">
        <h1 style="color:#10b981;">🧭 Monarque Care Navigator</h1>
        <p style="font-size: 1.2em; color: #cbd5e1;">
            Visualize your path from crisis to stability.
        </p>
        <p style="font-size: 0.9em; color: gray; margin-top: 20px;">
            Enter your situation in the sidebar to generate a dynamic process map.
        </p>
    </div>
    """, unsafe_allow_html=True)
