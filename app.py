import os
import streamlit as st
import tempfile
from PIL import Image
from openai_utils import grade_essay

# Set page configuration
st.set_page_config(
    page_title="Essay Grading App",
    page_icon="📝",
    layout="wide"
)

# App title and description
st.title("Handwritten Essay Grading App")
st.markdown("Upload a handwritten essay and set rubric criteria to get an AI-generated grade.")

# Initialize session state for rubric criteria
if 'rubric_criteria' not in st.session_state:
    st.session_state.rubric_criteria = {
        "Content (0-30)": "Evaluate the depth, relevance, and accuracy of the essay content.",
        "Organization (0-20)": "Assess structure, flow, and logical progression of ideas.",
        "Language & Style (0-20)": "Assess clarity, vocabulary, sentence variety, and tone.",
        "Grammar & Mechanics (0-20)": "Evaluate grammar, spelling, punctuation, and adherence to writing conventions.",
        "Critical Thinking (0-10)": "Assess analytical depth, originality, and insights."
    }

if 'criteria_count' not in st.session_state:
    st.session_state.criteria_count = len(st.session_state.rubric_criteria)

# Sidebar for rubric configuration
with st.sidebar:
    st.header("Rubric Configuration")
    st.info("Configure the criteria used to grade the essay. Each criterion should include a name and description.")
    
    # Grade level selector
    st.subheader("Student Grade Level")
    grade_options = [
        "Elementary School (K-2)",
        "Elementary School (3-5)", 
        "Middle School (6-8)", 
        "High School (9-10)", 
        "High School (11-12)", 
        "College Freshman/Sophomore",
        "College Junior/Senior", 
        "Graduate Level"
    ]
    grade_level = st.selectbox(
        "Select the student's grade level",
        options=grade_options,
        help="This helps the AI adjust expectations based on the educational level."
    )
    
    # Grading leniency slider
    st.subheader("Grading Leniency")
    grading_leniency = st.slider(
        "How lenient should the grading be?",
        min_value=1,
        max_value=10,
        value=5,
        help="1 = Very strict (harsh grading), 10 = Very lenient (generous grading)"
    )
    
    # Show explanation of current leniency level
    if grading_leniency <= 2:
        st.warning("🔍 **Very Strict**: Will deeply analyze the essay, focus on weaknesses, and be extremely critical.")
    elif grading_leniency <= 4:
        st.info("🔎 **Strict**: Will maintain high standards with limited top grades.")
    elif grading_leniency <= 6:
        st.info("⚖️ **Balanced**: Will evaluate objectively using the full scoring range.")
    elif grading_leniency <= 8:
        st.success("🌟 **Lenient**: Will add 5-15% to scores and focus more on strengths than weaknesses.")
    else:
        st.success("✨ **Very Lenient**: Will add 15-25% to scores, primarily focus on positives, and rarely give low grades.")
    
    # Add or remove criteria buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add Criterion"):
            st.session_state.criteria_count += 1
            st.session_state.rubric_criteria[f"New Criterion {st.session_state.criteria_count} (0-10)"] = "Description"
    with col2:
        if st.button("Remove Last"):
            if st.session_state.criteria_count > 1:
                last_key = list(st.session_state.rubric_criteria.keys())[-1]
                del st.session_state.rubric_criteria[last_key]
                st.session_state.criteria_count -= 1
    
    # Display and edit criteria
    st.subheader("Current Criteria")
    
    # Create a copy to avoid modifying the dictionary during iteration
    current_criteria = dict(st.session_state.rubric_criteria)
    
    for idx, (criterion, description) in enumerate(current_criteria.items()):
        with st.expander(f"{criterion}", expanded=False):
            new_criterion = st.text_input(f"Criterion Name #{idx+1}", criterion, key=f"crit_{idx}")
            new_description = st.text_area(f"Description #{idx+1}", description, key=f"desc_{idx}")
            
            if new_criterion != criterion:
                # Update the key
                st.session_state.rubric_criteria[new_criterion] = st.session_state.rubric_criteria.pop(criterion)
                
            # Update the description
            st.session_state.rubric_criteria[new_criterion] = new_description

# Main content area
col1, col2 = st.columns([1, 1])

# Upload and display section
with col1:
    st.header("Upload Essay")
    
    # Assignment instructions text area
    st.subheader("Assignment Instructions")
    assignment_instructions = st.text_area(
        "Enter the assignment instructions or prompt given to students",
        height=150,
        help="These instructions will be provided to the AI to better understand the context of the essay.",
        placeholder="Example: Write a 500-word argumentative essay discussing the impact of social media on modern society. Include at least three main arguments supported by evidence."
    )
    
    uploaded_file = st.file_uploader("Choose an image of a handwritten essay", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        # Create a temporary file for the uploaded image
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_path = temp_file.name
        
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Essay", use_column_width=True)
        
        # Grade button
        if st.button("Grade Essay"):
            with st.spinner("Analyzing essay..."):
                # Call the OpenAI API to grade the essay
                result = grade_essay(
                    temp_path, 
                    st.session_state.rubric_criteria, 
                    assignment_instructions, 
                    grade_level,
                    grading_leniency
                )
                
                # Store the result in session state for display
                st.session_state.grading_result = result["grading_result"]
                st.session_state.cost_summary = result["cost_summary"]

# Result display section
with col2:
    st.header("Grading Results")
    
    if 'grading_result' in st.session_state:
        st.markdown("### AI Feedback")
        st.write(st.session_state.grading_result)
        
        # Display token usage and cost information
        if 'cost_summary' in st.session_state:
            with st.expander("📊 Token Usage and Cost", expanded=False):
                st.code(st.session_state.cost_summary, language="")
    else:
        st.info("Upload an essay and click 'Grade Essay' to see results here.")

# Add sample instructions
st.markdown("---")
st.markdown("""
### Instructions:
1. Enter the assignment instructions to provide context
2. Select the student's grade level in the sidebar
3. Adjust the grading leniency slider in the sidebar
4. Configure your rubric criteria in the sidebar
5. Upload a clear image of a handwritten essay
6. Click "Grade Essay" to get AI-powered feedback

The AI will analyze the handwritten content and grade it according to your custom rubric.
""")

# Add info about API key requirement
st.sidebar.markdown("---")
st.sidebar.warning("This app requires an OpenAI API key with access to the Vision model (GPT-4 Vision). Set your key as an environment variable named `OPENAI_API_KEY` or in a `.env` file.")

# Add token usage information in sidebar
st.sidebar.markdown("---")
st.sidebar.info("📊 Token usage and cost information is available in the results panel after grading.")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit and OpenAI GPT-4o Vision") 