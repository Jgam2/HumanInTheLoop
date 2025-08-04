#!/usr/bin/env python3
"""
Response Validation Tool for Requirements Gathering

This tool uses the LLM to validate user responses and suggest improvements.
"""

from strands import Agent

def validate_response(response, requirements_type):
    """
    Validate a user response and identify issues or suggest improvements.
    
    Args:
        response (str): The user's response to validate
        requirements_type (str): The type of requirements being validated
        
    Returns:
        Dict containing validation results
    """
    # Create a temporary agent to validate the response
    validation_agent = Agent(
        system_prompt=f"""You are an expert requirements validator for {requirements_type} requirements.
        
        Analyze the user's response and identify:
        1. Any missing critical information
        2. Areas that need clarification
        3. Specific questions to ask to improve the response
        
        Return your analysis as a JSON object with these keys:
        - issues_found: boolean
        - missing_elements: list of strings
        - clarification_needed: list of strings
        - follow_up_questions: list of strings
        """
    )
    
    # Have the LLM validate the response
    validation = validation_agent.query(
        f"Please validate this {requirements_type} requirements response:\n\n{response}"
    )
    
    # The LLM should return a JSON object, but we'll handle it as a string
    # In a production system, you'd want to parse this properly
    return validation 
