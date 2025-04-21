import os
import base64
import json
import logging
import tiktoken
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api_usage.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("openai_usage")

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Token pricing constants
INPUT_TOKEN_PRICE_PER_MILLION = 1.10  # $1.10 per million tokens
OUTPUT_TOKEN_PRICE_PER_MILLION = 4.40  # $4.40 per million tokens

def count_tokens(text, model="gpt-4o"):
    """Count the number of tokens in the text"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Error counting tokens: {e}. Using approximation instead.")
        # Fallback to approximation (avg 4 chars per token)
        return len(text) // 4

def estimate_image_tokens(image_size_bytes):
    """Estimate tokens for an image based on size"""
    # OpenAI's documentation suggests roughly 85 tokens per 512x512 image
    # We'll use a simplified approximation based on file size
    # This is a rough estimate and may not be accurate for all images
    base_tokens = 85
    size_factor = image_size_bytes / (100 * 1024)  # Normalized by 100KB
    return int(base_tokens * size_factor) + base_tokens

def log_api_usage(input_tokens, output_tokens, model, function_name=""):
    """Log API usage and calculate costs"""
    input_cost = (input_tokens / 1_000_000) * INPUT_TOKEN_PRICE_PER_MILLION
    output_cost = (output_tokens / 1_000_000) * OUTPUT_TOKEN_PRICE_PER_MILLION
    total_cost = input_cost + output_cost
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "function": function_name,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost": f"${input_cost:.6f}",
        "output_cost": f"${output_cost:.6f}",
        "total_cost": f"${total_cost:.6f}"
    }
    
    logger.info(json.dumps(log_entry))
    
    return log_entry

def encode_image(image_path):
    """Convert image to base64 encoding"""
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        image_size = len(image_data)
        encoded = base64.b64encode(image_data).decode('utf-8')
        logger.info(f"Encoded image {image_path} (size: {image_size/1024:.2f} KB)")
        return encoded, image_size

def grade_essay(image_path, rubric_criteria, assignment_instructions="", grade_level="", grading_leniency=5):
    """
    Grade an essay using OpenAI's Vision model
    
    Args:
        image_path: Path to the handwritten essay image
        rubric_criteria: Dictionary containing rubric criteria and their descriptions
        assignment_instructions: Optional text describing the assignment instructions
        grade_level: Educational grade level of the student (e.g., "5th Grade", "9th Grade", etc.)
        grading_leniency: Integer from 1-10 indicating how lenient to be (1=very strict, 10=very lenient)
    
    Returns:
        Dictionary containing grades and feedback
    """
    # Start recording function usage
    function_start_time = datetime.now()
    
    # Encode image
    base64_image, image_size = encode_image(image_path)
    
    # Construct the prompt with assignment instructions and rubric criteria
    prompt = "You are an experienced essay grader with expertise in teaching across all educational levels. Grade the handwritten essay in the image based on the following information:\n\n"
    
    # Add detailed grade level expectations
    if grade_level:
        prompt += f"GRADE LEVEL: {grade_level}\n"
        
        # Add specific expectations based on grade level
        if "Elementary School (K-2)" in grade_level:
            prompt += "GRADE LEVEL EXPECTATIONS:\n"
            prompt += "- Simple sentence structure with basic vocabulary\n"
            prompt += "- Basic understanding of beginning, middle, and end\n"
            prompt += "- Emerging spelling and grammar skills\n"
            prompt += "- Simple ideas expressed clearly\n"
            prompt += "- Basic handwriting development\n"
            prompt += "DO NOT expect complex vocabulary, perfect spelling, advanced grammar, or sophisticated reasoning\n\n"
        
        elif "Elementary School (3-5)" in grade_level:
            prompt += "GRADE LEVEL EXPECTATIONS:\n"
            prompt += "- Complete sentences and developing paragraphs\n"
            prompt += "- Basic organizational structure\n"
            prompt += "- Growing vocabulary with some descriptive language\n"
            prompt += "- Developing understanding of punctuation and grammar\n"
            prompt += "- Simple but logical supporting details\n"
            prompt += "DO NOT expect sophisticated arguments, complex sentence structures, perfect grammar, or advanced analysis\n\n"
        
        elif "Middle School (6-8)" in grade_level:
            prompt += "GRADE LEVEL EXPECTATIONS:\n"
            prompt += "- Clear paragraph structure with topic sentences\n"
            prompt += "- Developing thesis statements\n"
            prompt += "- Introduction to argumentative writing\n"
            prompt += "- More varied vocabulary and sentence structures\n"
            prompt += "- Basic citations or evidence\n"
            prompt += "DO NOT expect college-level reasoning, sophisticated syntax, perfect consistency, or advanced rhetorical strategies\n\n"
        
        elif "High School (9-10)" in grade_level:
            prompt += "GRADE LEVEL EXPECTATIONS:\n"
            prompt += "- Clear thesis statements\n"
            prompt += "- Structured essays with introduction, body, conclusion\n"
            prompt += "- Developing analytical thinking\n"
            prompt += "- Use of textual evidence and basic citations\n"
            prompt += "- More varied rhetorical strategies\n"
            prompt += "DO NOT expect undergraduate-level analysis, perfect grammar, or highly sophisticated arguments\n\n"
        
        elif "High School (11-12)" in grade_level:
            prompt += "GRADE LEVEL EXPECTATIONS:\n"
            prompt += "- Well-developed thesis statements\n"
            prompt += "- Logical organization with effective transitions\n"
            prompt += "- More sophisticated analysis and arguments\n"
            prompt += "- Understanding of rhetorical strategies\n"
            prompt += "- Stronger evidence and citations\n"
            prompt += "DO NOT expect college-level writing proficiency, perfect mechanics, or graduate-level critical thinking\n\n"
        
        elif "College Freshman/Sophomore" in grade_level:
            prompt += "GRADE LEVEL EXPECTATIONS:\n"
            prompt += "- Clear, analytical thesis statements\n"
            prompt += "- Well-organized essays with effective transitions\n"
            prompt += "- Critical thinking and analysis\n"
            prompt += "- Integration of sources and proper citations\n"
            prompt += "- Command of academic writing conventions\n"
            prompt += "DO NOT expect graduate-level sophistication, perfect mechanics, or professional-level insights\n\n"
        
        elif "College Junior/Senior" in grade_level:
            prompt += "GRADE LEVEL EXPECTATIONS:\n"
            prompt += "- Sophisticated thesis statements\n"
            prompt += "- Advanced critical thinking and analysis\n"
            prompt += "- Strong command of academic writing conventions\n"
            prompt += "- Well-integrated research and citations\n"
            prompt += "- Awareness of disciplinary conventions\n"
            prompt += "DO NOT expect graduate-level mastery or professional publication quality\n\n"
        
        elif "Graduate Level" in grade_level:
            prompt += "GRADE LEVEL EXPECTATIONS:\n"
            prompt += "- Sophisticated and original thesis statements\n"
            prompt += "- Advanced research integration\n"
            prompt += "- Mastery of academic writing conventions\n"
            prompt += "- Advanced critical analysis and synthesis\n"
            prompt += "- Disciplinary expertise and awareness\n"
            prompt += "Hold to high academic standards while recognizing this is still student work\n\n"
        
        else:
            # Generic grade level expectations if none of the specific ones match
            prompt += "Consider age-appropriate expectations for this educational level.\n\n"
    
    # Add grading leniency instruction with specific guidance on score adjustment
    if grading_leniency <= 2:  # Very strict
        prompt += "GRADING APPROACH: VERY STRICT\n"
        prompt += "- Be extremely critical in your assessment and deduct points for even minor issues\n"
        prompt += "- For each criterion, score in the lower 30-40% of the possible range when there are any flaws\n"
        prompt += "- For letter grades, consider an A to be nearly unattainable and reserve B grades only for exceptional work\n"
        prompt += "- Apply the highest possible standards and focus primarily on weaknesses\n"
        prompt += "- Deduct 15-25% from what you would normally score the essay\n\n"
    elif grading_leniency <= 4:  # Strict
        prompt += "GRADING APPROACH: STRICT\n"
        prompt += "- Be quite critical in your assessment and emphasize areas for improvement\n" 
        prompt += "- For each criterion, score in the lower 40-50% of the possible range when there are flaws\n"
        prompt += "- Hold the student to high standards and be sparing with top scores\n"
        prompt += "- Deduct 5-15% from what you would normally score the essay\n\n"
    elif grading_leniency <= 6:  # Balanced
        prompt += "GRADING APPROACH: BALANCED\n"
        prompt += "- Use a balanced approach that considers both strengths and weaknesses equally\n"
        prompt += "- For each criterion, use the full scoring range appropriately, scoring in the middle 50-70% of the possible range when there are some strengths\n"
        prompt += "- Evaluate the essay objectively against the rubric criteria without bias towards strictness or leniency\n\n"
    elif grading_leniency <= 8:  # Lenient
        prompt += "GRADING APPROACH: LENIENT\n"
        prompt += "- Be generous in your assessment and focus more on strengths than weaknesses\n"
        prompt += "- For each criterion, score in the upper 70-100% of the possible range when there are some strengths\n"
        prompt += "- Give the student the benefit of the doubt in ambiguous cases\n"
        prompt += "- Add 5-15% to what you would normally score the essay\n\n"
    else:  # Very lenient
        prompt += "GRADING APPROACH: VERY LENIENT\n"
        prompt += "- Be extremely generous and primarily focus on the positive aspects of the work\n"
        prompt += "- For each criterion, score in the upper 70-80% of the possible range as long as basic requirements are met\n"
        prompt += "- For letter grades, avoid grades below a C unless requirements are completely missed\n"
        prompt += "- Highlight even small successes and minimize criticism of weaknesses\n"
        prompt += "- Add 15-25% to what you would normally score the essay\n\n"
    
    # Add assignment instructions if provided
    if assignment_instructions:
        prompt += f"ASSIGNMENT INSTRUCTIONS:\n{assignment_instructions}\n\n"
    
    prompt += "RUBRIC CRITERIA:\n"
    for criterion, description in rubric_criteria.items():
        prompt += f"- {criterion}: {description}\n"
    
    prompt += "\nFor each criterion, provide a score and brief explanation. Also provide an overall grade and summary feedback. IMPORTANT: Both the grade level AND leniency level should significantly influence your grading. First, adjust your baseline expectations according to the student's educational level (do not expect college-level work from elementary students), then apply the leniency adjustment to that grade-appropriate baseline. Your feedback should be appropriate for the student's educational level in both content and tone."
    
    # Count tokens in the prompt text
    text_tokens = count_tokens(prompt)
    estimated_image_tokens = estimate_image_tokens(image_size)
    total_input_tokens = text_tokens + estimated_image_tokens
    
    model = "o4-mini-2025-04-16"
    logger.info(f"Starting API call: text_tokens={text_tokens}, estimated_image_tokens={estimated_image_tokens}")
    
    # Call OpenAI API
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        #max_completion_tokens
    )
    
    output_text = response.choices[0].message.content
    output_tokens = count_tokens(output_text)
    
    # Log token usage and cost
    usage_data = log_api_usage(
        input_tokens=total_input_tokens,
        output_tokens=output_tokens,
        model=model,
        function_name="grade_essay"
    )
    
    # Create a formatted cost summary to display to the user
    execution_time = (datetime.now() - function_start_time).total_seconds()
    cost_summary = f"""
    Token Usage Summary:
    - Input tokens: {total_input_tokens:,} (includes text and image) - Cost: {usage_data['input_cost']}
    - Output tokens: {output_tokens:,} - Cost: {usage_data['output_cost']}
    - Total estimated cost: {usage_data['total_cost']}
    - Execution time: {execution_time:.2f} seconds
    """
    logger.info(cost_summary)
    
    # Return both the grading result and the cost summary
    return {
        "grading_result": output_text,
        "cost_summary": cost_summary
    } 