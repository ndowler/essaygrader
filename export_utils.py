import os
import re
import csv
import base64
import pandas as pd
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def extract_scores(grading_results):
    """Extract scores from the grading results text using regex pattern matching."""
    scores = []
    for result in grading_results:
        student_name = result.get("student_name", "Unnamed Student")
        grading_text = result.get("grading_result", "")
        
        # Create a dictionary for each student with default scores
        student_data = {
            "Student Name": student_name,
            "Feedback": grading_text,
            "Total Score": "N/A"
        }
        
        # Add this student's data to the list
        scores.append(student_data)
    
    return scores

def create_csv_string(grading_results):
    """Create a CSV string from the grading results."""
    scores = extract_scores(grading_results)
    
    # Create a CSV string
    output = io.StringIO()
    fieldnames = ["Student Name", "Total Score", "Feedback"]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for score in scores:
        writer.writerow({
            "Student Name": score["Student Name"],
            "Total Score": score["Total Score"],
            "Feedback": score["Feedback"]
        })
    
    return output.getvalue()

def generate_pdf(grading_results, assignment_info):
    """Generate a PDF file with the grading results."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=16,
        spaceAfter=12
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    # Build document content
    elements = []
    
    # Add report title
    title = assignment_info.get('title', 'Essay Assessment Report')
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 12))
    
    # Add date
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elements.append(Paragraph(f"Generated on: {date_str}", normal_style))
    elements.append(Spacer(1, 12))
    
    # Add assignment details
    elements.append(Paragraph("Assignment Details:", header_style))
    instructions = assignment_info.get('instructions', 'No instructions provided')
    grade_level = assignment_info.get('grade_level', 'Not specified')
    
    elements.append(Paragraph(f"<b>Grade Level:</b> {grade_level}", normal_style))
    elements.append(Paragraph(f"<b>Instructions:</b> {instructions}", normal_style))
    elements.append(Spacer(1, 20))
    
    # Add student results
    elements.append(Paragraph("Grading Results:", header_style))
    elements.append(Spacer(1, 10))
    
    for i, result in enumerate(grading_results):
        student_name = result.get("student_name", f"Student {i+1}")
        feedback = result.get("grading_result", "No feedback provided")
        
        elements.append(Paragraph(f"<b>Student:</b> {student_name}", normal_style))
        elements.append(Paragraph("<b>Feedback:</b>", normal_style))
        
        # Split feedback into paragraphs for better readability
        feedback_lines = feedback.split('\n')
        for line in feedback_lines:
            if line.strip():
                elements.append(Paragraph(line, normal_style))
        
        elements.append(Spacer(1, 20))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer.getvalue()

def get_download_link(content, filename, text):
    """
    Generate a download link for the given content.
    
    Args:
        content: The content as bytes or string
        filename: The name for the download file
        text: The text to display for the download link
        
    Returns:
        HTML string with the download link
    """
    if isinstance(content, str):
        content = content.encode()
    
    b64 = base64.b64encode(content).decode()
    href = f'<a href="data:file/octet-stream;base64,{b64}" download="{filename}">{text}</a>'
    return href

def export_to_csv(grading_results):
    """Export grading results to CSV and return a download link."""
    if not grading_results:
        return "No results to export"
    
    csv_string = create_csv_string(grading_results)
    
    # Create a download link
    b64 = base64.b64encode(csv_string.encode()).decode()
    filename = f"grading_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    href = f'<a href="data:text/csv;base64,{b64}" download="{filename}">Download CSV</a>'
    
    return href

def export_to_pdf(grading_results, assignment_info):
    """Export grading results to PDF and return a download link."""
    if not grading_results:
        return "No results to export"
    
    pdf_bytes = generate_pdf(grading_results, assignment_info)
    
    # Create a download link
    b64 = base64.b64encode(pdf_bytes).decode()
    filename = f"grading_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download PDF</a>'
    
    return href 