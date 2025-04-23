import os
import streamlit as st
import tempfile
import pandas as pd
from PIL import Image
from openai_utils import grade_essay, batch_grade_essays
from export_utils import export_to_csv, export_to_pdf

# Set page configuration
st.set_page_config(
    page_title="Essay Grading App",
    page_icon="📝",
    layout="wide"
)

# Initialize session state variables
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

if 'grading_results' not in st.session_state:
    st.session_state.grading_results = []

if 'batch_summary' not in st.session_state:
    st.session_state.batch_summary = None

if 'temp_files' not in st.session_state:
    st.session_state.temp_files = []

# Function to clean up temporary files
def cleanup_temp_files():
    for file_path in st.session_state.temp_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            st.warning(f"Failed to remove temporary file {file_path}: {str(e)}")
    st.session_state.temp_files = []

# App title and description
st.title("Handwritten Essay Grading App")
st.markdown("Upload handwritten essays and get AI-generated grades based on customizable rubric criteria.")

# Create tabs for Single Essay and Batch Processing
tab1, tab2 = st.tabs(["Single Essay", "Batch Processing"])

# Sidebar for common configuration
with st.sidebar:
    st.header("Grading Configuration")
    
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
        st.warning("🔍 **Very Strict**: ChatGPT straight up Dick mode. It will murder your essay.")
    elif grading_leniency <= 4:
        st.info("🔎 **Strict**: ChatGPT will maintain high standards and be super strict with limited top grades.")
    elif grading_leniency <= 6:
        st.info("⚖️ **Balanced**: Will evaluate objectively using the full scoring range.")
    elif grading_leniency <= 8:
        st.success("🌟 **Lenient**: Will add some leniency to scores and focus more on strengths than weaknesses.")
    else:
        st.success("✨ **Very Lenient**: Will add a lot of leniency to scores, primarily focus on positives, and rarely give low grades.")
    
    # Assignment instructions text area
    st.subheader("Assignment Instructions")
    assignment_instructions = st.text_area(
        "Enter the assignment instructions or prompt given to students",
        height=150,
        help="These instructions will be provided to the AI to better understand the context of the essay.",
        placeholder="Example: Write a 500-word argumentative essay discussing the impact of social media on modern society. Include at least three main arguments supported by evidence."
    )
    
    # Rubric Configuration Section
    st.header("Rubric Configuration")
    st.info("Configure the criteria used to grade the essay. Each criterion should include a name and description.")
    
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

# Single Essay Tab
with tab1:
    col1, col2 = st.columns([1, 1])
    
    # Upload and display section
    with col1:
        st.header("Upload Essay")
        
        uploaded_file = st.file_uploader("Choose an image of a handwritten essay", type=["jpg", "jpeg", "png"], key="single_uploader")
        student_name = st.text_input("Student Name (optional)", key="single_student_name")
        
        if uploaded_file is not None:
            # Create a temporary file for the uploaded image
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_path = temp_file.name
                # Add to the list of temporary files to clean up later
                st.session_state.temp_files.append(temp_path)
            
            # Display the uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption=f"Uploaded Essay{f' - {student_name}' if student_name else ''}", use_column_width=True)
            
            # Grade button
            if st.button("Grade Essay", key="single_grade_button"):
                with st.spinner("Analyzing essay..."):
                    # Call the OpenAI API to grade the essay
                    result = grade_essay(
                        temp_path, 
                        st.session_state.rubric_criteria, 
                        assignment_instructions, 
                        grade_level,
                        grading_leniency
                    )
                    
                    # Add student name if provided
                    result["student_name"] = student_name if student_name else "Unnamed Student"
                    result["file_name"] = uploaded_file.name
                    result["status"] = "success"
                    
                    # Store the result in session state for display
                    st.session_state.current_result = result
    
    # Result display section
    with col2:
        st.header("Grading Results")
        
        if 'current_result' in st.session_state:
            if st.session_state.current_result["student_name"]:
                st.subheader(f"Student: {st.session_state.current_result['student_name']}")
            
            st.markdown("### AI Feedback")
            st.write(st.session_state.current_result["grading_result"])
            
            # Display token usage and cost information
            with st.expander("📊 Token Usage and Cost", expanded=False):
                st.code(st.session_state.current_result["cost_summary"], language="")
            
            # Export options for single essay
            st.markdown("### Export Options")
            export_col1, export_col2 = st.columns(2)
            
            # Create a list with the single result for export functions
            single_result_list = [st.session_state.current_result]
            
            # Assignment info for PDF
            assignment_info = {
                'title': 'Essay Assessment',
                'instructions': assignment_instructions,
                'grade_level': grade_level
            }
            
            with export_col1:
                csv_link = export_to_csv(single_result_list)
                st.markdown(csv_link, unsafe_allow_html=True)
                
            with export_col2:
                pdf_link = export_to_pdf(single_result_list, assignment_info)
                st.markdown(pdf_link, unsafe_allow_html=True)
        else:
            st.info("Upload an essay and click 'Grade Essay' to see results here.")

# Batch Processing Tab
with tab2:
    st.header("Batch Process Multiple Essays")
    
    # Instructions for batch upload
    st.markdown("""
    ### Batch Upload Instructions:
    1. Upload multiple handwritten essay images using the file uploader below
    2. Enter student names (optional) in the text area (one name per line)
    3. All essays will be graded using the same assignment instructions, grade level, and rubric criteria
    4. Click "Process Batch" to analyze all essays
    """)
    
    # Batch file uploader
    uploaded_files = st.file_uploader(
        "Choose multiple essay images", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True,
        key="batch_uploader"
    )
    
    # Student names input
    student_names_input = st.text_area(
        "Enter student names (one per line, leave blank to use filenames)",
        height=100,
        placeholder="John Doe\nJane Smith\n...",
        help="Enter one student name per line. The order should match your uploaded files."
    )
    
    # Parse student names
    student_names = [name.strip() for name in student_names_input.split('\n') if name.strip()]
    
    # Show files and names in a table if available
    if uploaded_files:
        # If no student names or not enough names, use filenames
        while len(student_names) < len(uploaded_files):
            student_names.append("")
        
        # Truncate if too many names
        student_names = student_names[:len(uploaded_files)]
        
        # Create a dataframe to display files and names
        file_data = []
        for i, file in enumerate(uploaded_files):
            name = student_names[i] if student_names[i] else f"Unnamed Student {i+1}"
            file_data.append({
                "Index": i+1,
                "Filename": file.name,
                "Student Name": name,
                "Size": f"{file.size / 1024:.1f} KB"
            })
        
        st.write(f"**{len(uploaded_files)} files ready for processing:**")
        st.dataframe(pd.DataFrame(file_data), use_container_width=True)
        
        # Process batch button
        if st.button("Process Batch", key="batch_process_button"):
            if len(uploaded_files) > 0:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Create temporary files for the batch
                image_paths = []
                final_student_names = []
                
                for i, uploaded_file in enumerate(uploaded_files):
                    # Update progress for file preparation
                    progress_value = i / (len(uploaded_files) * 2)  # Half progress for prep
                    progress_bar.progress(progress_value)
                    status_text.text(f"Preparing file {i+1}/{len(uploaded_files)}: {uploaded_file.name}")
                    
                    # Create temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                        temp_file.write(uploaded_file.getvalue())
                        image_paths.append(temp_file.name)
                        st.session_state.temp_files.append(temp_file.name)
                    
                    # Get student name
                    name = student_names[i] if i < len(student_names) and student_names[i] else f"Student {i+1}"
                    final_student_names.append(name)
                
                # Process the batch
                with st.spinner(f"Processing {len(uploaded_files)} essays... This may take several minutes"):
                    # Call the batch processing function
                    results, batch_summary = batch_grade_essays(
                        image_paths,
                        final_student_names,
                        st.session_state.rubric_criteria,
                        assignment_instructions,
                        grade_level,
                        grading_leniency
                    )
                    
                    # Update progress as each file is processed
                    for i in range(len(results)):
                        progress_value = 0.5 + ((i + 1) / (len(uploaded_files) * 2))  # Second half progress
                        progress_bar.progress(progress_value)
                        status_text.text(f"Processed {i+1}/{len(uploaded_files)} essays")
                
                # Store results and summary
                st.session_state.grading_results = results
                st.session_state.batch_summary = batch_summary
                
                # Complete progress
                progress_bar.progress(1.0)
                status_text.text(f"Completed processing {len(uploaded_files)} essays!")
    
    # Display batch results if available
    if 'grading_results' in st.session_state and st.session_state.grading_results:
        st.header("Batch Results")
        
        # Display batch summary
        if st.session_state.batch_summary:
            with st.expander("📊 Batch Summary", expanded=True):
                summary = st.session_state.batch_summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Essays", summary["total_essays"])
                with col2:
                    st.metric("Successful", summary["successful_essays"])
                with col3:
                    st.metric("Failed", summary["failed_essays"])
                
                st.write(f"**Total Cost:** {summary['total_cost']}")
                st.write(f"**Total Time:** {summary['total_execution_time']}")
                st.write(f"**Average Time Per Essay:** {summary['average_time_per_essay']}")
        
        # Display individual results in tabs
        result_tabs = st.tabs([
            f"{result['student_name']} ({os.path.basename(result['file_name'])})" 
            for result in st.session_state.grading_results
        ])
        
        for i, (tab, result) in enumerate(zip(result_tabs, st.session_state.grading_results)):
            with tab:
                # Display success or error message
                if result["status"] == "success":
                    st.markdown("### AI Feedback")
                    st.write(result["grading_result"])
                    
                    with st.expander("📊 Token Usage and Cost", expanded=False):
                        st.code(result["cost_summary"], language="")
                else:
                    st.error(f"Failed to process this essay: {result['error_message']}")
        
        # Export buttons
        st.markdown("### Export Options")
        
        # Assignment info for PDF
        assignment_info = {
            'title': 'Batch Essay Assessment',
            'instructions': assignment_instructions,
            'grade_level': grade_level
        }
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Clear Batch Results"):
                st.session_state.grading_results = []
                st.session_state.batch_summary = None
                cleanup_temp_files()
                st.experimental_rerun()
        
        with col2:
            csv_link = export_to_csv(st.session_state.grading_results)
            st.markdown(csv_link, unsafe_allow_html=True)
            
        with col3:
            pdf_link = export_to_pdf(st.session_state.grading_results, assignment_info)
            st.markdown(pdf_link, unsafe_allow_html=True)

# Add info about API key requirement
st.sidebar.markdown("---")
st.sidebar.warning("This app requires an OpenAI API key with access to the Vision model (GPT-4 Vision). Set your key as an environment variable named `OPENAI_API_KEY` or in a `.env` file.")

# Add token usage information in sidebar
st.sidebar.markdown("---")
st.sidebar.info("📊 Token usage and cost information is available in the results panel after grading.")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit and OpenAI GPT-4o Vision") 