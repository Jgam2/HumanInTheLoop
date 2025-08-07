#!/usr/bin/env python3
"""
Requirements Gathering System Demo with Built-in handoff_to_user and Knowledge Base Integration

This file demonstrates how to use the built-in handoff_to_user tool from strands_tools for interactive 
requirements gathering across 5 key sections with human oversight, enhanced with knowledge base integration 
for better responses.

Requirements Gathering Workflow:
1. Project Scope (ask specific question -> get input)
2. User Stories (ask specific question -> get input)
3. Technical Constraints (ask specific question -> get input)
4. Success Criteria (ask specific question -> get input)
5. File Format Support (ask specific question -> get input)
6. Additional Information (ask if user wants to add anything -> get input)
7. Validate and Calculate Confidence Score
8. Generate Requirements Document
9. Ask for User Review
10. Save to DynamoDB

Key Features:
- Uses from strands_tools import handoff_to_user (built-in tool)
- Streamlined process with specific questions for each section
- Human oversight at each critical decision point
- Knowledge base integration for enhanced responses
- Systematic progression through all 5 requirements sections
- Enhanced with LLM-powered evaluation and validation tools

Usage:
python requirements_demo.py
python requirements_demo.py --demo
python requirements_demo.py --help
python requirements_demo.py --kb KNOWLEDGE_BASE_ID
"""

import os
import logging
import json
import boto3
from botocore.exceptions import ClientError
from strands import Agent, tool
from strands_tools import handoff_to_user
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
from rich.table import Table
import sys
import time
from datetime import datetime
import traceback
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize console for rich output
console = Console()

# AWS Configuration
AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "I3RO432NC8")  # Default KB ID

# Global variables for tracking progress
SECTIONS = [
    "PROJECT SCOPE",
    "USER STORIES",
    "TECHNICAL CONSTRAINTS",
    "SUCCESS CRITERIA",
    "FILE FORMAT SUPPORT"
]
current_section = 0
responses = {}

# Define specialized agent tools
@tool
def evaluate_confidence(response: str, section_name: str) -> str:
    """
    Evaluates the confidence level of a user's response for a requirements section.
    
    Args:
        response: The user's response text to evaluate
        section_name: The name of the requirements section being evaluated
        
    Returns:
        Evaluation with confidence score, strengths, and areas for improvement
    """
    try:
        console.print(f"[cyan]Analyzing response quality for {section_name}...[/cyan]")
        
        # Create a specialized agent for evaluation
        eval_agent = Agent(
            system_prompt=f"""You are an expert requirements analyst evaluating the quality of a response for '{section_name}'.
Analyze the response for:
1. Relevance - Does it address the '{section_name}' requirements?
2. Completeness - Does it provide sufficient information?
3. Quality - Is the information specific, clear, and actionable?

Provide:
1. A confidence score from 0-10 based on relevance and quality (NOT length)
2. 2-3 key strengths
3. 2-3 areas for improvement

Format your response with "Confidence Score: X/10" on the first line.
Focus on content quality, not quantity. Be concise."""
        )
        
        # Call the agent to evaluate the response
        evaluation = eval_agent(f"Evaluate this {section_name} response: {response}")
        
        console.print(f"[green]Analysis complete.[/green]")
        return str(evaluation)
    except Exception as e:
        console.print(f"[yellow]Error in evaluation: {str(e)}. Using default confidence score.[/yellow]")
        return f"Confidence Score: 7.0/10\n\nError occurred during evaluation: {str(e)}"

@tool
def validate_response(response: str, section_name: str) -> str:
    """
    Validates a user's response for a requirements section and identifies specific issues.
    
    Args:
        response: The user's response text to validate
        section_name: The name of the requirements section being validated
        
    Returns:
        List of issues found in the response
    """
    try:
        console.print(f"[cyan]Validating response for {section_name}...[/cyan]")
        
        # Create a specialized agent for validation
        validation_agent = Agent(
            system_prompt=f"""You are an expert requirements validator identifying gaps in '{section_name}' requirements.
Analyze for:
1. Missing critical information
2. Ambiguities or vague statements
3. Non-measurable requirements

Provide a list of 2-3 specific issues found. Be concise and actionable.
Format your response as a numbered list."""
        )
        
        # Call the agent to validate the response
        validation = validation_agent(f"Identify issues in this {section_name} response: {response}")
        
        console.print(f"[green]Validation complete.[/green]")
        return str(validation)
    except Exception as e:
        console.print(f"[yellow]Error in validation: {str(e)}. No issues to report.[/yellow]")
        return f"No critical issues found.\n\nError occurred during validation: {str(e)}"

@tool
def generate_requirements_doc(project_name: str, requirements_data: str) -> str:
    """
    Generate a requirements document in Markdown format.
    
    Args:
        project_name: The name of the project
        requirements_data: JSON string containing all requirements data
        
    Returns:
        Markdown formatted requirements document
    """
    try:
        console.print(f"[cyan]Generating requirements document for {project_name}...[/cyan]")
        
        # Create a specialized agent for document generation
        doc_agent = Agent(
            system_prompt=f"""You are a requirements document generator for project: {project_name}
Create a professional Markdown-formatted requirements document based on the collected information.
Include all sections with clear headings, bullet points for clarity, and proper formatting.
Be comprehensive but concise. Include an executive summary at the beginning.
Focus only on creating a requirements document. Do not include any code or implementation details."""
        )
        
        # Call the agent to generate the document
        document = doc_agent(f"Generate a requirements document in Markdown format based on this information:\n\n{requirements_data}")
        
        console.print(f"[green]Document generation complete.[/green]")
        return str(document)
    except Exception as e:
        console.print(f"[yellow]Error in document generation: {str(e)}.[/yellow]")
        return f"Error occurred during document generation: {str(e)}"

def query_knowledge_base(query):
    """Tool to query the Amazon Bedrock Knowledge Base."""
    try:
        console.print(f"\n[bold cyan]Querying knowledge base for:[/bold cyan] {query}")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            search_task = progress.add_task("[cyan]Searching knowledge base...", total=100)

            # Initialize the Bedrock client
            bedrock_agent_client = boto3.client('bedrock-agent', region_name=AWS_REGION)

            # Update progress
            progress.update(search_task, advance=30)

            # Call the Bedrock Knowledge Base API
            response = bedrock_agent_client.retrieve(
                knowledgeBaseId=KNOWLEDGE_BASE_ID,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 3,
                        'overrideSearchType': 'HYBRID'
                    }
                }
            )

            # Update progress
            progress.update(search_task, advance=40)

            # Process results
            results = response.get('retrievalResults', [])
            if not results:
                progress.update(search_task, completed=100)
                console.print("[yellow]No information found in the knowledge base.[/yellow]")
                return "No information found in the knowledge base for this query."

            # Format results
            formatted_results = []
            for i, result in enumerate(results, 1):
                content = result.get('content', {}).get('text', 'No content')
                source = "Unknown source"
                
                # Try to extract source from metadata
                if 'documentMetadata' in result:
                    metadata = result['documentMetadata']
                    if 'source' in metadata:
                        source = metadata['source']
                    elif 'location' in metadata:
                        source = metadata['location']
                
                formatted_results.append(f"Source {i} ({source}):\n{content}\n")
                progress.update(search_task, advance=10)

            progress.update(search_task, completed=100)
            result_text = "\n".join(formatted_results)
            console.print(f"[green]Found {len(results)} relevant results in knowledge base.[/green]")
            return result_text

    except ClientError as e:
        error_msg = f"Error querying knowledge base: {str(e)}"
        logger.error(error_msg)
        console.print(f"[red]{error_msg}[/red]")
        return error_msg
    except Exception as e:
        error_msg = f"Error querying knowledge base: {str(e)}"
        logger.error(error_msg)
        console.print(f"[red]{error_msg}[/red]")
        return error_msg

def display_section_progress():
    """Display progress through the requirements gathering sections."""
    global current_section
    console.print("\n[bold cyan]Requirements Gathering Progress:[/bold cyan]")
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Status", style="bold")
    table.add_column("Section")

    for i, section in enumerate(SECTIONS):
        if i < current_section:
            status = "[green]✓[/green]"
        elif i == current_section:
            status = "[yellow]►[/yellow]"
        else:
            status = "[dim]○[/dim]"
        table.add_row(status, f"Section {i+1}: {section}")

    console.print(table)
    console.print(f"\n[cyan]Progress: {current_section}/{len(SECTIONS)} sections completed[/cyan]\n")

def extract_confidence_score(evaluation_text):
    """Extract confidence score from evaluation text."""
    # Handle dictionary result
    if isinstance(evaluation_text, dict):
        # Try to extract from content if it's a tool result
        if "content" in evaluation_text and isinstance(evaluation_text["content"], list):
            evaluation_text = evaluation_text["content"][0]["text"]
        else:
            # Default if we can't extract text
            return 7.0
    
    # Extract the confidence score using regex
    score_pattern = r"(?:confidence|score):\s*(\d+(?:\.\d+)?)"
    score_match = re.search(score_pattern, evaluation_text.lower())
    
    # If no match, try to find any number out of 10
    if not score_match:
        score_pattern = r"(\d+(?:\.\d+)?)/10"
        score_match = re.search(score_pattern, evaluation_text.lower())
    
    # Default if no score found
    confidence_score = float(score_match.group(1)) if score_match else 7.0
    
    # Ensure score is within bounds
    return max(0.0, min(10.0, confidence_score))

def gather_requirements(project_name=None, use_kb=False):
    """
    Main function to run the requirements gathering system.

    Args:
        project_name: Optional project name. If not provided, user will be prompted.
        use_kb: Whether to use knowledge base integration.

    Returns:
        Dictionary with complete requirements gathering results
    """
    global current_section, responses

    # Reset global state for new run
    current_section = 0
    responses = {}

    try:
        # Display welcome banner
        welcome_text = Text()
        welcome_text.append("REQUIREMENTS GATHERING SYSTEM\n", style="bold blue")
        welcome_text.append("Interactive AI-Powered Requirements Collection\n\n", style="cyan")
        welcome_text.append("This system will guide you through:\n", style="white")
        welcome_text.append("* Project Scope Definition\n", style="green")
        welcome_text.append("* User Stories & Workflows\n", style="green")
        welcome_text.append("* Technical Constraints\n", style="green")
        welcome_text.append("* Success Criteria & Metrics\n", style="green")
        welcome_text.append("* File Formats & Data Specs\n", style="green")

        features_text = "Features: AI Analysis, Smart Follow-ups, Rich Output, Document Generation"
        if use_kb:
            features_text += ", Knowledge Base Integration"
        welcome_text.append(f"\n{features_text}", style="dim")

        console.print(Panel(
            welcome_text,
            title="Welcome",
            title_align="center",
            border_style="blue",
            padding=(1, 2)
        ))

        # Get project name if not provided
        if not project_name:
            console.print("\n[bold cyan]Let's start by naming your project:[/bold cyan]")
            project_name = input("Project name: ").strip()
            if not project_name:
                project_name = "Unnamed Project"
                console.print(f"[yellow]Using default name: {project_name}[/yellow]")

        console.print(f"\n[green]Starting requirements gathering for: {project_name}[/green]\n")

        # Set up tools list
        tools = [handoff_to_user, evaluate_confidence, validate_response, generate_requirements_doc]

        # Add knowledge base tool if enabled
        if use_kb:
            tools.append(query_knowledge_base)
            console.print(f"[cyan]Knowledge Base integration enabled (ID: {KNOWLEDGE_BASE_ID})[/cyan]")

        # Create a simple, direct system prompt
        kb_prompt_addition = """
Before asking questions, use the query_knowledge_base tool to search for relevant information.
""" if use_kb else ""

        system_prompt = f"""You are a requirements gathering assistant for project: {project_name}

Your task is to collect requirements through these 5 specific sections:
1. PROJECT SCOPE: Project objectives, goals, scope
2. USER STORIES: User stories, use cases, workflows
3. TECHNICAL CONSTRAINTS: Technical requirements, platforms, limitations
4. SUCCESS CRITERIA: Success metrics and acceptance criteria
5. FILE FORMAT SUPPORT: Required file formats and data specifications

Follow this exact process:
1. Ask ONE specific question for each section, one at a time
2. Use handoff_to_user to collect the user's response for each question
3. After collecting all 5 responses, ask if the user wants to add anything else to any section
4. If yes, collect additional input using handoff_to_user
5. After collecting all information, use evaluate_confidence tool to assess each section
6. For sections with low confidence, use validate_response tool to identify issues
7. Use generate_requirements_doc tool to create a Markdown requirements document
8. Ask the user to review the document before saving

{kb_prompt_addition}

Be direct and concise in your questions. For each section, ask a focused question that will help gather comprehensive information.
"""

        # Create agent with tools
        console.print("[cyan]Initializing requirements gathering agent...[/cyan]")
        agent = Agent(
            tools=tools,
            system_prompt=system_prompt
        )

        # Start the requirements gathering process
        console.print("\n[bold cyan]Starting the requirements gathering process...[/bold cyan]")
        display_section_progress()

        # Define specific questions for each section
        section_questions = [
            "What are the main objectives, goals, and scope of this project?",
            "What are the key user stories, use cases, and workflows for this project?",
            "What technical constraints, platform requirements, and limitations should be considered?",
            "What are the success criteria and acceptance metrics for this project?",
            "What file formats and data specifications need to be supported by this project?"
        ]

        # Collect responses for each section
        for i, section in enumerate(SECTIONS):
            current_section = i
            display_section_progress()
            
            # Query knowledge base if enabled
            kb_info = ""
            if use_kb:
                kb_info = query_knowledge_base(f"best practices for {section.lower()} in software projects")
                console.print(f"\n[dim]Knowledge base information for {section}:[/dim]\n{kb_info}\n")
            
            # Ask the question for this section
            console.print(f"\n[bold cyan]Section {i+1}: {section}[/bold cyan]")
            
            # Prepare prompt for the agent
            if use_kb:
                prompt = f"Based on this knowledge base information: {kb_info}\n\nAsk the user about {section}: {section_questions[i]}"
            else:
                prompt = f"Ask the user about {section}: {section_questions[i]}"
            
            # Get agent's formulation of the question
            question = agent(prompt)
            console.print(f"\n{question}")
            
            # Use handoff_to_user to get the response
            # This is the correct way to use the tool through the agent
            response = agent.tool.handoff_to_user(
                message=f"Please provide your input for {section}:",
                breakout_of_loop=False
            )
            
            # Extract the user response from the tool result
            user_text = response["content"][0]["text"]
            # Remove the "User response received: " prefix if present
            if "User response received: " in user_text:
                user_text = user_text.replace("User response received: ", "")
            
            # Store the response
            responses[section] = user_text
            
            # Provide brief acknowledgment
            console.print(f"[green]Response for {section} recorded.[/green]")
        
        # Ask if the user wants to add anything else
        console.print("\n[bold cyan]Additional Information[/bold cyan]")
        additional_question = agent("Ask the user if they want to add anything else to any section.")
        console.print(f"\n{additional_question}")
        
        # Use handoff_to_user with breakout_of_loop=True to end the input gathering phase
        additional_response = agent.tool.handoff_to_user(
            message="Do you want to add anything else to any section? If yes, please specify the section and provide the additional information:",
            breakout_of_loop=True
        )
        
        # Process additional information if provided
        additional_text = additional_response["content"][0]["text"]
        if "User response received: " in additional_text:
            additional_text = additional_text.replace("User response received: ", "")
            
        if additional_text.lower() not in ["no", "n", "none", ""]:
            console.print("[green]Processing additional information...[/green]")
            
            # Create a prompt to categorize the additional information
            categorize_prompt = f"""Categorize this additional information into the appropriate section(s) from these options: {', '.join(SECTIONS)}

Additional information: {additional_text}

Return only the section name in uppercase, followed by a colon, and then the cleaned information.
Example: "PROJECT SCOPE: Additional information about project scope."
If information applies to multiple sections, return multiple sections separated by newlines."""
            
            # Use the main agent to categorize the information
            categorized_info = agent(categorize_prompt)
            
            # Process the categorized information
            import re
            section_pattern = re.compile(r"(PROJECT SCOPE|USER STORIES|TECHNICAL CONSTRAINTS|SUCCESS CRITERIA|FILE FORMAT SUPPORT):\s*(.*?)(?=(?:PROJECT SCOPE|USER STORIES|TECHNICAL CONSTRAINTS|SUCCESS CRITERIA|FILE FORMAT SUPPORT):|$)", re.DOTALL)
            matches = section_pattern.findall(str(categorized_info))
            
            for section, info in matches:
                if section in responses:
                    responses[section] += f"\n\nAdditional Information:\n{info.strip()}"
                    console.print(f"[green]Added information to {section}[/green]")
        
        # Now that we have all responses, evaluate confidence and validate
        console.print("\n[bold cyan]Evaluating Requirements Quality[/bold cyan]")
        
        confidence_scores = {}
        validation_issues = {}
        
        for section, response in responses.items():
            # Use the evaluate_confidence tool
            console.print(f"[cyan]Analyzing response quality for {section}...[/cyan]")
            evaluation_result = agent.tool.evaluate_confidence(
                response=response,
                section_name=section
            )
            
            # Extract confidence score
            confidence_score = extract_confidence_score(evaluation_result)
            confidence_scores[section] = confidence_score
            
            console.print(f"[green]Confidence score for {section}: {confidence_score:.1f}/10[/green]")
            
            # Validate responses with low confidence
            if confidence_score < 7.0:
                console.print(f"[yellow]Low confidence for {section}. Validating response...[/yellow]")
                
                validation_result = agent.tool.validate_response(
                    response=response,
                    section_name=section
                )
                
                validation_issues[section] = validation_result
                console.print(f"[yellow]Issues found in {section}:[/yellow]")
                console.print(f"[yellow]{validation_result}[/yellow]")
        
        # Calculate overall confidence
        overall_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
        console.print(f"\n[bold]Overall Requirements Quality: {overall_confidence:.1f}/10[/bold]")
        
        # Prepare the requirements data for document generation
        requirements_data = f"Project Name: {project_name}\n\n"
        for section, response in responses.items():
            requirements_data += f"{section}:\n{response}\n\n"
            
        # Add confidence scores to the input
        requirements_data += "Confidence Scores:\n"
        for section, score in confidence_scores.items():
            requirements_data += f"{section}: {score:.1f}/10\n"
        
        # Generate the requirements document using the specialized tool
        console.print("\n[bold cyan]Generating Requirements Document[/bold cyan]")
        requirements_doc = agent.tool.generate_requirements_doc(
            project_name=project_name,
            requirements_data=requirements_data
        )
        
        # Display the document for review
        console.print("\n[bold green]Requirements Document Draft:[/bold green]")
        console.print(Panel(requirements_doc, title="Requirements Document", border_style="green"))
        
        # Ask for user review
        review_response = agent.tool.handoff_to_user(
            message="Please review the requirements document. Would you like to make any changes? If yes, please specify what changes you'd like to make:",
            breakout_of_loop=True
        )
        
        # Process review feedback if provided
        final_doc = requirements_doc
        review_text = review_response["content"][0]["text"]
        if "User response received: " in review_text:
            review_text = review_text.replace("User response received: ", "")
            
        if review_text.lower() not in ["no", "n", "none", "", "looks good", "approved"]:
            console.print("[green]Processing review feedback...[/green]")
            
            # Update the document based on feedback
            update_prompt = f"""Original document:

{requirements_doc}

User feedback:
{review_text}

Please update the document based on this feedback. Maintain the Markdown format and document structure.
"""
            # Use the main agent to update the document
            final_doc = agent(update_prompt)
            
            console.print("\n[bold green]Updated Requirements Document:[/bold green]")
            console.print(Panel(str(final_doc), title="Updated Requirements Document", border_style="green"))
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"requirements_{timestamp}.md"
        
        # Save the requirements to a file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(str(final_doc))
        
        console.print(f"\n[green]Requirements document saved as: {filename}[/green]")
        
        # Save to DynamoDB if configured
        try:
            # Ask if user wants to save to DynamoDB
            save_to_db_response = agent.tool.handoff_to_user(
                message="Would you like to save this requirements document to DynamoDB? (yes/no)",
                breakout_of_loop=True
            )
            
            save_to_db_text = save_to_db_response["content"][0]["text"]
            if "User response received: " in save_to_db_text:
                save_to_db_text = save_to_db_text.replace("User response received: ", "")
                
            if save_to_db_text.lower() in ["yes", "y", "sure", "ok"]:
                console.print("[cyan]Saving to DynamoDB...[/cyan]")
                
                # Initialize DynamoDB client
                dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
                table_name = "RequirementsDocuments"
                
                # Check if table exists, create if not
                try:
                    table = dynamodb.Table(table_name)
                    table.table_status  # This will raise an exception if the table doesn't exist
                except:
                    console.print("[yellow]Table does not exist. Creating new table...[/yellow]")
                    table = dynamodb.create_table(
                        TableName=table_name,
                        KeySchema=[
                            {'AttributeName': 'project_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                        ],
                        AttributeDefinitions=[
                            {'AttributeName': 'project_id', 'AttributeType': 'S'},
                            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                        ],
                        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                    )
                    # Wait for table creation
                    table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
                
                # Save to DynamoDB
                project_id = project_name.lower().replace(" ", "_")
                item = {
                    'project_id': project_id,
                    'timestamp': timestamp,
                    'project_name': project_name,
                    'document': str(final_doc),
                    'confidence_score': overall_confidence,
                    'sections': {section: {'content': content, 'confidence': confidence_scores.get(section, 0)} 
                                for section, content in responses.items()}
                }
                
                table.put_item(Item=item)
                console.print("[green]Successfully saved to DynamoDB![/green]")
            else:
                console.print("[yellow]Document not saved to DynamoDB.[/yellow]")
        
        except Exception as e:
            console.print(f"[red]Error saving to DynamoDB: {str(e)}[/red]")
            console.print("[yellow]Continuing with local file save only.[/yellow]")
        
        return {
            "status": "success",
            "project_name": project_name,
            "saved_filename": filename,
            "statistics": {
                "sections_processed": len(SECTIONS),
                "total_responses": len(responses),
                "timestamp": timestamp,
                "kb_enhanced": use_kb,
                "overall_confidence": overall_confidence
            }
        }
        
    except KeyboardInterrupt:
        console.print("\n\n[red]Requirements gathering interrupted by user.[/red]")
        console.print("[dim]Partial results may have been saved.[/dim]")
        return {"status": "interrupted", "message": "Session interrupted by user"}
    
    except Exception as e:
        console.print(f"\n\n[red]An error occurred during requirements gathering:[/red]")
        console.print(f"[red]{str(e)}[/red]")
        console.print(f"\n[dim]Traceback:\n{traceback.format_exc()}[/dim]")
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}

def demo_with_sample_project(use_kb=False):
    """
    Demo function that runs requirements gathering for a sample project.
    Useful for testing the system.

    Args:
        use_kb: Whether to use knowledge base integration.
    """
    kb_text = " with Knowledge Base Integration" if use_kb else ""
    console.print(Panel(
        f"[bold yellow]DEMO MODE{kb_text}[/bold yellow]\n\nThis will run the requirements gathering system "
        f"for a sample 'Task Management App' project.\n\nYou can provide real responses to see "
        f"how the system works, or use sample responses for testing.",
        title="Demo Mode",
        border_style="yellow"
    ))
    return gather_requirements("Task Management App Demo", use_kb=use_kb)

def print_usage():
    """Print usage information for the demo script."""
    usage_text = (
        "\n# Requirements Gathering System Usage\n\n"
        "## Command Line Usage:\n"
        "```bash\n"
        "python requirements_demo.py # Interactive mode - prompts for project name\n"
        "python requirements_demo.py --demo # Demo mode with sample project\n"
        "python requirements_demo.py --help # Show this help message\n"
        "python requirements_demo.py --kb # Use with knowledge base integration\n"
        "python requirements_demo.py --kb ID # Use with specific knowledge base ID\n"
        "python requirements_demo.py --demo --kb # Demo with knowledge base integration\n"
        "```\n\n"
        "## Environment Variables:\n"
        "```bash\n"
        "AWS_REGION # AWS region for knowledge base (default: ap-southeast-2)\n"
        "KNOWLEDGE_BASE_ID # ID of the knowledge base to use\n"
        "```\n\n"
        "## Programmatic Usage:\n"
        "```python\n"
        "from requirements_demo import gather_requirements\n\n"
        "# Interactive mode\n"
        "result = gather_requirements()\n\n"
        "# With specific project name\n"
        "result = gather_requirements(\"My Awesome Project\")\n\n"
        "# With knowledge base integration\n"
        "result = gather_requirements(\"My Awesome Project\", use_kb=True)\n\n"
        "# Check results\n"
        "if result[\"status\"] == \"success\":\n"
        "    print(f\"Document saved: {result['saved_filename']}\")\n"
        "else:\n"
        "    print(f\"Error: {result.get('error', 'Unknown error')}\")\n"
        "```\n\n"
    )

    # Add information about tools
    usage_text += (
        "## Tools Used:\n"
        "1. handoff_to_user: Enables interactive user input collection\n"
        "2. evaluate_confidence: Specialized agent for evaluating response quality\n"
        "3. validate_response: Specialized agent for identifying issues in responses\n"
        "4. generate_requirements_doc: Specialized agent for document generation\n"
        "5. query_knowledge_base: Retrieves information from knowledge base\n\n"
        "## Streamlined Requirements Gathering Process:\n\n"
        "1. Ask 5 specific questions (one for each section)\n"
        "2. Ask if user wants to add anything else\n"
        "3. Validate and calculate confidence score using specialized agents\n"
        "4. Generate requirements document using a specialized document agent\n"
        "5. Ask for user review\n"
        "6. Save to file and optionally to DynamoDB\n\n"
    )
    
    console.print(Panel(
        usage_text,
        title="Usage Guide",
        border_style="green"
    ))

def print_handoff_info():
    """Print information about the handoff_to_user tool workflow."""
    handoff_text = Text()
    handoff_text.append("HANDOFF_TO_USER TOOL WORKFLOW\n\n", style="bold magenta")
    handoff_text.append("This demo showcases two critical modes of the handoff_to_user tool:\n\n", style="white")
    handoff_text.append("1. CONTINUE MODE (breakout_of_loop=False):\n", style="bold green")
    handoff_text.append(" - Agent pauses execution and prompts the user\n", style="green")
    handoff_text.append(" - Agent waits for user input\n", style="green")
    handoff_text.append(" - After receiving input, agent CONTINUES processing\n", style="green")
    handoff_text.append(" - Used for the first 5 requirements sections and review\n\n", style="green")
    handoff_text.append("2. BREAK MODE (breakout_of_loop=True):\n", style="bold yellow")
    handoff_text.append(" - Agent pauses execution and prompts the user\n", style="yellow")
    handoff_text.append(" - Agent waits for user input\n", style="yellow")
    handoff_text.append(" - After receiving input, agent STOPS execution completely\n", style="yellow")
    handoff_text.append(" - Used for the additional information section to complete input gathering\n\n", style="yellow")
    handoff_text.append("The workflow follows this pattern:\n", style="white")
    handoff_text.append("Start -> Section 1 -> handoff(continue) -> Section 2 -> handoff(continue) -> \n", style="cyan")
    handoff_text.append("Section 3 -> handoff(continue) -> Section 4 -> handoff(continue) -> \n", style="cyan")
    handoff_text.append("Section 5 -> handoff(continue) -> Additional Info -> handoff(break) -> \n", style="cyan")
    handoff_text.append("Validation -> Document Generation -> Review -> handoff(continue) -> Save\n\n", style="cyan")
    handoff_text.append("This creates a structured, section-by-section requirements gathering process\n", style="white")
    handoff_text.append("with human oversight at each critical decision point.", style="white")
    console.print(Panel(
        handoff_text,
        title="handoff_to_user Tool Workflow",
        title_align="center",
        border_style="magenta",
        padding=(1, 2)
    ))

def print_tools_info():
    """Print information about the additional tools."""
    tools_text = Text()
    tools_text.append("REQUIREMENTS GATHERING TOOLS\n\n", style="bold blue")
    
    # handoff_to_user Tool
    tools_text.append("1. HANDOFF_TO_USER TOOL\n", style="bold green")
    tools_text.append(" Purpose: Enables interactive user input collection\n", style="green")
    tools_text.append(" Usage: agent.tool.handoff_to_user(message=\"...\", breakout_of_loop=False/True)\n", style="green")
    tools_text.append(" When Used: For collecting user input at each step of the process\n\n", style="green")
    
    # evaluate_confidence Tool
    tools_text.append("2. EVALUATE_CONFIDENCE TOOL\n", style="bold yellow")
    tools_text.append(" Purpose: Specialized agent for evaluating response quality\n", style="yellow")
    tools_text.append(" Usage: agent.tool.evaluate_confidence(response=\"...\", section_name=\"...\")\n", style="yellow")
    tools_text.append(" When Used: After collecting all responses to assess quality\n\n", style="yellow")
    
    # validate_response Tool
    tools_text.append("3. VALIDATE_RESPONSE TOOL\n", style="bold blue")
    tools_text.append(" Purpose: Specialized agent for identifying issues in responses\n", style="blue")
    tools_text.append(" Usage: agent.tool.validate_response(response=\"...\", section_name=\"...\")\n", style="blue")
    tools_text.append(" When Used: For responses with low confidence scores\n\n", style="blue")
    
    # generate_requirements_doc Tool
    tools_text.append("4. GENERATE_REQUIREMENTS_DOC TOOL\n", style="bold green")
    tools_text.append(" Purpose: Specialized agent for document generation\n", style="green")
    tools_text.append(" Usage: agent.tool.generate_requirements_doc(project_name=\"...\", requirements_data=\"...\")\n", style="green")
    tools_text.append(" When Used: After validation to create the final document\n\n", style="green")
    
    # Knowledge Base Tool
    tools_text.append("5. KNOWLEDGE BASE TOOL\n", style="bold yellow")
    tools_text.append(" Purpose: Retrieves relevant information from knowledge base\n", style="yellow")
    tools_text.append(" Input: Query text to search for in the knowledge base\n", style="yellow")
    tools_text.append(" Output: Relevant information from the knowledge base\n", style="yellow")
    tools_text.append(" When Used: Before asking questions or providing guidance\n\n", style="yellow")
    
    # Enhanced Workflow
    tools_text.append("AGENTS AS TOOLS PATTERN:\n", style="bold white")
    tools_text.append("This system uses the 'Agents as Tools' pattern where specialized agents are wrapped\n", style="white")
    tools_text.append("as callable functions that can be used by the main orchestrator agent. Each specialized\n", style="white")
    tools_text.append("agent has a focused area of responsibility and expertise:\n\n", style="white")
    tools_text.append("1. Main Agent: Orchestrates the overall requirements gathering process\n", style="cyan")
    tools_text.append("2. Evaluation Agent: Analyzes response quality and provides confidence scores\n", style="cyan")
    tools_text.append("3. Validation Agent: Identifies specific issues in low-quality responses\n", style="cyan")
    tools_text.append("4. Document Generation Agent: Creates the final requirements document\n\n", style="cyan")
    
    tools_text.append("This creates an efficient requirements gathering process that leverages\n", style="white")
    tools_text.append("specialized expertise for each task while maintaining a cohesive workflow.", style="white")
    
    console.print(Panel(
        tools_text,
        title="Enhanced Requirements Tools",
        title_align="center",
        border_style="blue",
        padding=(1, 2)
    ))

def print_kb_info():
    """Print information about the knowledge base integration."""
    kb_text = Text()
    kb_text.append("KNOWLEDGE BASE INTEGRATION\n\n", style="bold blue")
    kb_text.append("This system is enhanced with Amazon Bedrock Knowledge Base integration:\n\n", style="white")
    kb_text.append("KNOWLEDGE BASE ID:\n", style="bold green")
    kb_text.append(f" {KNOWLEDGE_BASE_ID}\n\n", style="green")
    kb_text.append("AWS REGION:\n", style="bold green")
    kb_text.append(f" {AWS_REGION}\n\n", style="green")
    kb_text.append("HOW IT WORKS:\n", style="bold white")
    kb_text.append("1. The agent queries the knowledge base for relevant information\n", style="white")
    kb_text.append("2. Knowledge is incorporated into questions and suggestions\n", style="white")
    kb_text.append("3. Requirements are enhanced with domain expertise\n", style="white")
    kb_text.append("4. The final document includes best practices and standards\n\n", style="white")
    kb_text.append("This creates a more informed requirements gathering process that leverages\n", style="cyan")
    kb_text.append("existing knowledge and best practices in your domain.", style="cyan")
    console.print(Panel(
        kb_text,
        title="Knowledge Base Integration",
        title_align="center",
        border_style="blue",
        padding=(1, 2)
    ))

def main():
    """Main entry point for the requirements gathering demo."""
    # Check for knowledge base flag
    use_kb = False
    custom_kb_id = None
    
    # Process command line arguments
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] in ["--kb", "-k"]:
            use_kb = True
            # Check if next argument is a KB ID
            if i + 1 < len(args) and not args[i+1].startswith("-"):
                custom_kb_id = args[i+1]
                i += 1  # Skip the next argument since we've processed it
        i += 1
    
    # Update KB ID if provided
    global KNOWLEDGE_BASE_ID
    if custom_kb_id:
        KNOWLEDGE_BASE_ID = custom_kb_id
        console.print(f"[cyan]Using custom Knowledge Base ID: {KNOWLEDGE_BASE_ID}[/cyan]")
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        if "--help" in sys.argv or "-h" in sys.argv:
            print_usage()
            return
        elif "--demo" in sys.argv or "-d" in sys.argv:
            print_handoff_info()
            print_tools_info()
            if use_kb:
                print_kb_info()
            time.sleep(1)  # Give user time to read the info
            result = demo_with_sample_project(use_kb=use_kb)
        elif use_kb:
            print_handoff_info()
            print_tools_info()
            print_kb_info()
            time.sleep(1)
            result = gather_requirements(use_kb=use_kb)
        else:
            console.print(f"[red]Unknown argument: {' '.join(sys.argv[1:])}[/red]")
            console.print("Use --help for usage information")
            return
    else:
        # Interactive mode
        print_handoff_info()
        print_tools_info()
        time.sleep(1)  # Give user time to read the info
        result = gather_requirements(use_kb=False)
    
    # Print final result summary
    if result.get("status") == "success":
        console.print(f"\n[bold green]Requirements gathering completed successfully![/bold green]")
        console.print(f"[green]Project: {result.get('project_name', 'Unknown')}[/green]")
        console.print(f"[green]Document: {result.get('saved_filename', 'Not saved')}[/green]")
        console.print(f"[green]Sections: {result.get('statistics', {}).get('sections_processed', 0)}[/green]")
        console.print(f"[green]Responses: {result.get('statistics', {}).get('total_responses', 0)}[/green]")
        console.print(f"[green]Overall Confidence: {result.get('statistics', {}).get('overall_confidence', 0):.1f}/10[/green]")
        if result.get('statistics', {}).get('kb_enhanced', False):
            console.print(f"[green]Knowledge Base Enhanced: Yes[/green]")
    elif result.get("status") == "interrupted":
        console.print(f"\n[yellow]Session was interrupted but partial data may be available.[/yellow]")
    else:
        console.print(f"\n[red]Requirements gathering failed.[/red]")
        if "error" in result:
            console.print(f"[red]Error: {result['error']}[/red]")
    
    console.print(f"\n[dim]Thank you for using the Requirements Gathering System![/dim]")

    # Explicitly exit to ensure the process doesn't continue
    sys.exit(0)

if __name__ == "__main__":
    main()