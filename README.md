# Handwritten Essay Grading App

A simple Streamlit application that uses OpenAI's Vision API to grade handwritten essays based on customizable rubric criteria.

## Features

- Upload images of handwritten essays
- Customize grading rubrics with different criteria and weights
- Enter assignment instructions to provide context for grading
- Specify student grade level to set appropriate expectations
- Adjust grading leniency to control strictness of evaluation
- Get AI-powered grades and feedback based on your rubric
- Simple and intuitive user interface

## Requirements

- Python 3.7+
- OpenAI API key with access to GPT-4 Vision

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your OpenAI API key:
   
   Create a `.env` file in the project root with:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
   
   Or set it as an environment variable:
   ```
   export OPENAI_API_KEY=your_api_key_here  # Unix/macOS
   set OPENAI_API_KEY=your_api_key_here     # Windows Command Prompt
   $env:OPENAI_API_KEY="your_api_key_here"  # Windows PowerShell
   ```

## Usage

1. Start the application:
   ```
   streamlit run app.py
   ```

2. Open your web browser and go to `http://localhost:8501`

3. Enter the assignment instructions to provide context for the AI grader

4. Select the student's grade level in the sidebar

5. Adjust the grading leniency slider to control how strictly the essay is graded

6. Configure your rubric criteria in the sidebar

7. Upload an image of a handwritten essay

8. Click "Grade Essay" to get AI-powered feedback

## Limitations

- The application currently supports only one essay at a time
- Image quality affects the accuracy of text recognition
- Relies on OpenAI's GPT-4 Vision API (requires API credits)

## Future Improvements

- Batch processing of multiple essays
- Export results to CSV or PDF
- More advanced rubric configuration options
- Integration with learning management systems 