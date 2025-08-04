#!/usr/bin/env python3
"""
Confidence Evaluation Tool for Requirements Gathering

This tool uses the LLM to evaluate the quality of user responses
rather than using hardcoded logic.
"""

from strands import Agent

def evaluate_confidence(response, section_name):
    """
    Evaluate the confidence level in a user's requirements response using LLM.
    
    Args:
        response (str): The user's response text to evaluate
        section_name (str): The section being evaluated (e.g., "Project Scope")
        
    Returns:
        Dict containing evaluation results
    """
    # Create a temporary agent to evaluate the response
    evaluation_agent = Agent(
        system_prompt=f"""You are an expert requirements analyst.
        
        Evaluate the quality and completeness of the user's response for the "{section_name}" section.
        
        Provide:
        1. A confidence score from 0-10 (where 10 is excellent)
        2. Brief feedback explaining the score
        3. 1-3 key strengths of the response
        4. 1-3 areas for improvement
        
        Return your evaluation as a JSON object with these keys:
        - confidence_score: float
        - feedback: string
        - strengths: list of strings
        - weaknesses: list of strings
        - section: string (the section name)
        """
    )
    
    # Have the LLM evaluate the response
    evaluation = evaluation_agent.query(
        f"Please evaluate this response for the '{section_name}' section:\n\n{response}"
    )
    
    # The LLM should return a JSON object, but we'll handle it as a string
    # In a production system, you'd want to parse this properly
    return evaluation 
