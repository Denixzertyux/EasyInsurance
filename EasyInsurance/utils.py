import PyPDF2
from google import generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime
import json

# Load environment variables
load_dotenv()

# Set your API key directly here (temporary solution)
GEMINI_API_KEY = "AIzaSyCQ-QFbsxP8qyyz0s_XcMEv75YIIUnkrLQ"  # Replace this with your actual API key

def extract_text_from_pdf(pdf_file):
    """
    Extract text from a PDF file
    """
    try:
        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Initialize text variable
        text = ""
        
        # Extract text from each page
        for page in pdf_reader.pages:
            text += page.extract_text()
            
        print("Successfully extracted text from PDF")
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        return None

def process_text_with_gemini(text):
    """
    Process extracted text using Gemini API to extract insurance details
    """
    try:
        # Configure Gemini API with the direct key
        print("Configuring Gemini API...")
        genai.configure(api_key=GEMINI_API_KEY)
        
        print("Initializing Gemini model...")
        # Initialize the model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Create the prompt
        prompt = f"""
        Extract the following information from this insurance document text. 
        Return the data in a JSON format with these exact keys:
        {{
            "insurance_id": "string",
            "expiry_date": "YYYY-MM-DD",
            "starting_date": "YYYY-MM-DD",
            "car_brand": "string",
            "car_model": "string",
            "VIN": "string"
        }}

        If any information is not found, use null for that field.
        Only return the JSON data, nothing else.

        Document text:
        {text}
        """
        
        print("Sending request to Gemini API...")
        # Generate response
        response = model.generate_content(prompt)
        
        print("Received response from Gemini API")
        # Return the response text
        return response.text
        
    except Exception as e:
        print(f"Error processing text with Gemini: {str(e)}")
        return None

def parse_insurance_data(gemini_response):
    """
    Parse the Gemini response into a dictionary of insurance data
    """
    try:
        print("Attempting to parse Gemini response...")
        # Try to parse the response as JSON
        try:
            # First, try to parse the response directly
            data = json.loads(gemini_response)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from the text
            # This handles cases where Gemini might add extra text
            start_idx = gemini_response.find('{')
            end_idx = gemini_response.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = gemini_response[start_idx:end_idx]
                data = json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")

        print("Successfully parsed JSON response")
        # Validate the data structure
        required_fields = ['insurance_id', 'expiry_date', 'starting_date', 'car_brand', 'car_model', 'VIN']
        for field in required_fields:
            if field not in data:
                data[field] = None

        # Validate date formats
        date_fields = ['expiry_date', 'starting_date']
        for field in date_fields:
            if data[field]:
                try:
                    datetime.strptime(data[field], '%Y-%m-%d')
                except ValueError:
                    data[field] = None

        print("Successfully validated and processed insurance data")
        return data

    except Exception as e:
        print(f"Error parsing insurance data: {str(e)}")
        return None