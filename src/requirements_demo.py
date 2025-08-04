#!/usr/bin/env python3
"""
Requirements Gathering System Demo with Built-in handoff_to_user and Knowledge Base Integration

This file demonstrates how to use the built-in handoff_to_user tool from strands_tools
for interactive requirements gathering across 5 key sections with human oversight,
enhanced with knowledge base integration for better responses.

Requirements Gathering Workflow:
1. Project Scope (gather input -> confirm -> continue)
2. User Stories (gather input -> confirm -> continue) 
3. Technical Constraints (gather input -> confirm -> continue)
4. Success Criteria (gather input -> confirm -> continue)
5. File Format Support (gather input -> confirm -> complete with break)

Key Features:
- Uses from strands_tools import handoff_to_user (built-in tool)
- Continue mode (breakout_of_loop=False) for ongoing interactions
- Break mode (breakout_of_loop=True) after final section to complete workflow
- Human oversight at each critical decision point
- Knowledge base integration for enhanced responses
- Systematic progression through all 5 requirements sections
- Enhanced with confidence evaluation and response validation tools

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
from strands import Agent
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

# Import custom tools
try:
    from tools.evaluate_confidence import evaluate_confidence
    from tools.validate_response import validate_response
    CUSTOM_TOOLS_AVAILABLE = True
except ImportError:
    CUSTOM_TOOLS_AVAILABLE = False
    # Create simple versions of the tools for demonstration
    def evaluate_confidence(response, section_name):
        """Simple confidence evaluation tool."""
        # Calculate a basic confidence score based on response length and complexity
        words = response.split()
        word_count = len(words)
        unique_words = len(set(words))
        
        # Basic heuristic: longer responses with more unique words are better
        if word_count < 20:
            confidence = 3.0
        elif word_count < 50:
            confidence = 5.0
        elif word_count < 100:
            confidence = 7.0
        else:
            confidence = 8.5
            
        # Adjust based on vocabulary richness
        if unique_words / max(1, word_count) > 0.7:
            confidence += 1.0
            
        # Cap at 10
        confidence = min(10.0, confidence)
        
        return {
            "confidence_score": confidence,
            "feedback": f"Response length: {word_count} words. Vocabulary richness: {unique_words / max(1, word_count):.2f}",
            "strengths": ["Good length" if word_count > 50 else "Response provided"],
            "weaknesses": ["Consider adding more detail" if word_count < 50 else ""],
            "section": section_name
        }
    
    def validate_response(response, requirements_type):
        """Simple response validation tool."""
        issues = []
        
        # Check for common issues based on requirements type
        if requirements_type.lower() == "project scope":
            if "goal" not in response.lower() and "objective" not in response.lower():
                issues.append("Missing clear project goals or objectives")
            if "user" not in response.lower():
                issues.append("Missing user information")
                
        elif requirements_type.lower() == "user stories":
            if "as a" not in response.lower():
                issues.append("Missing 'As a...' user story format")
            if "want to" not in response.lower() and "need to" not in response.lower():
                issues.append("Missing 'want to/need to' in user stories")
                
        elif requirements_type.lower() == "technical constraints":
            if "requirement" not in response.lower():
                issues.append("Missing specific technical requirements")
                
        elif requirements_type.lower() == "success criteria":
            if "measure" not in response.lower() and "metric" not in response.lower():
                issues.append("Missing measurable success criteria")
                
        elif requirements_type.lower() == "file format support":
            if "format" not in response.lower():
                issues.append("Missing file format specifications")
        
        return {
            "issues_found": len(issues) > 0,
            "issues": issues,
            "suggestions": ["Be more specific", "Add measurable criteria", "Include all required information"],
            "requirements_type": requirements_type
        }

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

def query_knowledge_base(query):
    """Tool to query the Amazon Bedrock Knowledge Base."""
    try:
        console.print(f"\n[bold cyan]Querying knowledge base for:[/bold cyan] {query}")
        console.print("[dim]Searching for relevant information...[/dim]")
        
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
            time.sleep(0.5)  # Simulate search time
            
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
            time.sleep(0.5)  # Simulate processing time
            
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
                time.sleep(0.2)  # Simulate processing time
            
            progress.update(search_task, completed=100)
            
        result_text = "\n".join(formatted_results)
        console.print(f"[green]Found {len(results)} relevant results in knowledge base.[/green]")
        
        # Display a preview of the results
        preview = "\n".join([f"[dim]- Source {i+1}: {result['content']['text'][:50]}...[/dim]" 
                            for i, result in enumerate(results)])
        console.print(f"[cyan]Knowledge Base Results Preview:[/cyan]\n{preview}")
        
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

def analyze_response(response, section_name):
    """Analyze a user response using the confidence evaluation tool."""
    if not CUSTOM_TOOLS_AVAILABLE and not 'evaluate_confidence' in globals():
        return None
        
    console.print(f"[cyan]Analyzing response for {section_name}...[/cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        analysis_task = progress.add_task("[cyan]Analyzing response quality...", total=100)
        
        # Simulate analysis time
        for i in range(5):
            time.sleep(0.2)
            progress.update(analysis_task, advance=20)
        
        # Perform the actual analysis
        result = evaluate_confidence(response, section_name)
        
    # Display the results
    confidence = result.get('confidence_score', 0)
    feedback = result.get('feedback', '')
    strengths = result.get('strengths', [])
    weaknesses = result.get('weaknesses', [])
    
    color = "green" if confidence >= 7.0 else "yellow" if confidence >= 5.0 else "red"
    
    console.print(f"\n[bold cyan]Response Analysis for {section_name}:[/bold cyan]")
    console.print(f"[bold {color}]Confidence Score: {confidence:.1f}/10[/bold {color}]")
    
    if feedback:
        console.print(f"[dim]{feedback}[/dim]")
    
    if strengths:
        console.print("[green]Strengths:[/green]")
        for strength in strengths:
            if strength:
                console.print(f"[green]✓ {strength}[/green]")
    
    if weaknesses:
        console.print("[yellow]Areas for Improvement:[/yellow]")
        for weakness in weaknesses:
            if weakness:
                console.print(f"[yellow]○ {weakness}[/yellow]")
    
    console.print()
    return result

def validate_user_response(response, requirements_type):
    """Validate a user response using the validation tool."""
    if not CUSTOM_TOOLS_AVAILABLE and not 'validate_response' in globals():
        return None
        
    console.print(f"[cyan]Validating response for {requirements_type}...[/cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        validation_task = progress.add_task("[cyan]Checking response completeness...", total=100)
        
        # Simulate validation time
        for i in range(3):
            time.sleep(0.2)
            progress.update(validation_task, advance=30)
        
        # Perform the actual validation
        result = validate_response(response, requirements_type)
        progress.update(validation_task, completed=100)
    
    # Display the results
    issues_found = result.get('issues_found', False)
    issues = result.get('issues', [])
    suggestions = result.get('suggestions', [])
    
    if issues_found:
        console.print("\n[bold yellow]Response Validation Issues:[/bold yellow]")
        for issue in issues:
            console.print(f"[yellow]! {issue}[/yellow]")
        
        if suggestions:
            console.print("\n[cyan]Suggestions for Improvement:[/cyan]")
            for suggestion in suggestions:
                console.print(f"[cyan]→ {suggestion}[/cyan]")
    else:
        console.print("\n[green]Response Validation: No issues found[/green]")
    
    console.print()
    return result

def gather_requirements(project_name=None, use_kb=False):
    """
    Main function to run the requirements gathering system.
    
    Args:
        project_name: Optional project name. If not provided, user will be prompted.
        use_kb: Whether to use knowledge base integration.
        
    Returns:
        Dictionary with complete requirements gathering results
    """
    global current_section
    
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
        
        # Set up tools list - always include handoff_to_user
        tools = [handoff_to_user]
        
        # Add knowledge base tool if enabled
        if use_kb:
            tools.append(query_knowledge_base)
            console.print(f"[cyan]Knowledge Base integration enabled (ID: {KNOWLEDGE_BASE_ID})[/cyan]")
        
        # Add custom tools if available
        if CUSTOM_TOOLS_AVAILABLE:
            tools.extend([evaluate_confidence, validate_response])
            console.print("[cyan]Enhanced tools loaded: confidence evaluation and response validation[/cyan]")
        
        # Create system prompt based on available tools
        kb_prompt_addition = """
Before answering questions or providing guidance, use the query_knowledge_base tool to search for relevant information.
Incorporate knowledge base information into your responses to provide more accurate and helpful guidance.
""" if use_kb else ""

        if CUSTOM_TOOLS_AVAILABLE:
            system_prompt = f"""You are a professional requirements gathering assistant for the project: {project_name}

Your task is to systematically collect requirements through 5 key sections:

1. PROJECT SCOPE: Ask about project objectives, main goals, and overall scope
2. USER STORIES: Collect user stories, use cases, and workflows  
3. TECHNICAL CONSTRAINTS: Gather technical requirements, platforms, and limitations
4. SUCCESS CRITERIA: Define success metrics and acceptance criteria
5. FILE FORMAT SUPPORT: Document required file formats and data specifications

{kb_prompt_addition}
For each section:
1. Ask clear, focused questions to gather information
2. Use the handoff_to_user tool with message="your question" and breakout_of_loop=False to get user input
3. After receiving input, use evaluate_confidence tool with response=user_input and section_name="Section Name" to assess quality
4. If confidence is low (below 7.0), use validate_response tool with response=user_input and requirements_type="section_type" to identify issues
5. If issues are found, ask follow-up questions to improve the response quality
6. When satisfied with the response quality, summarize and move to the next section

Use handoff_to_user with breakout_of_loop=False for sections 1-4, and breakout_of_loop=True for section 5.

Be thorough, professional, and ask clarifying questions when needed. 
Provide a comprehensive summary at the end covering all gathered requirements."""
        else:
            # Original system prompt if custom tools aren't available
            system_prompt = f"""You are a professional requirements gathering assistant for the project: {project_name}

Your task is to systematically collect requirements through 5 key sections:

1. PROJECT SCOPE: Ask about project objectives, main goals, and overall scope
2. USER STORIES: Collect user stories, use cases, and workflows  
3. TECHNICAL CONSTRAINTS: Gather technical requirements, platforms, and limitations
4. SUCCESS CRITERIA: Define success metrics and acceptance criteria
5. FILE FORMAT SUPPORT: Document required file formats and data specifications

{kb_prompt_addition}
For each section:
- Ask clear, focused questions to gather information
- Use the handoff_to_user tool with message="your question" and breakout_of_loop=False for sections 1-4
- Use the handoff_to_user tool with message="final summary" and breakout_of_loop=True for section 5 to complete

Be thorough, professional, and ask clarifying questions when needed. 
Provide a comprehensive summary at the end covering all gathered requirements."""
        
        # Create agent with tools
        console.print("[cyan]Initializing requirements gathering agent...[/cyan]")
        agent = Agent(
            tools=tools,
            system_prompt=system_prompt
        )
        
        # Start the requirements gathering process
        console.print("\n[bold cyan]Starting the requirements gathering process...[/bold cyan]")
        display_section_progress()
        
        # Start the conversation with the agent
        initial_prompt = f"Please start gathering requirements for the project '{project_name}'. Begin with the first section: Project Scope."
        
        # If using KB, add a suggestion to search for similar projects
        if use_kb:
            initial_prompt += f" Before asking questions, search the knowledge base for information about similar projects or best practices for requirements gathering."
        
        # Run the agent
        console.print("[cyan]Sending initial prompt to agent...[/cyan]")
        
        # Create a dictionary to store all responses
        all_responses = {
            "project_name": project_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sections": {}
        }
        
        # Process each section
        try:
            # Call the agent with the initial prompt
            response = agent(initial_prompt)
            console.print(f"\n{response}")
            
            # The agent will handle the conversation flow using handoff_to_user
            # We'll collect the responses and analyze them after each section
            
            # Wait for the agent to complete
            console.print("\n[cyan]Agent is processing requirements gathering...[/cyan]")
            console.print("[dim]The agent will guide you through each section and ask for your input.[/dim]")
            console.print("[dim]Please respond to the agent's questions when prompted.[/dim]")
            
            # Monitor for section completion
            while current_section < len(SECTIONS):
                # The agent will handle the conversation flow
                # This is just a placeholder for monitoring progress
                time.sleep(1)
                
                # In a real implementation, we would track the agent's progress
                # and update current_section accordingly
                
            # Generate timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"requirements_{timestamp}.md"
            
            # Collect all responses from the agent
            all_sections = {}
            for section in SECTIONS:
                if section in responses:
                    all_sections[section] = responses[section]
            
            # Create a comprehensive requirements document
            console.print(f"[cyan]Generating requirements document...[/cyan]")
            
            # Save the requirements to a file
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# Requirements Document: {project_name}\n\n")
                f.write(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                
                if use_kb:
                    f.write(f"*Enhanced with Knowledge Base: {KNOWLEDGE_BASE_ID}*\n\n")
                
                f.write("## Executive Summary\n\n")
                f.write("This document outlines the requirements gathered for the project through an interactive AI-assisted process.\n\n")
                
                # Write each section
                for i, section in enumerate(SECTIONS):
                    f.write(f"## {i+1}. {section}\n\n")
                    if section in all_sections:
                        f.write(f"{all_sections[section]}\n\n")
                    else:
                        f.write("*No information provided for this section.*\n\n")
                
                # Add metadata
                f.write("## Metadata\n\n")
                f.write(f"- **Project Name**: {project_name}\n")
                f.write(f"- **Date Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"- **Sections Completed**: {len(all_sections)}/{len(SECTIONS)}\n")
                if use_kb:
                    f.write(f"- **Knowledge Base Enhanced**: Yes (ID: {KNOWLEDGE_BASE_ID})\n")
            
            console.print(f"\n[green]Requirements document saved as: {filename}[/green]")
            
            return {
                "status": "success",
                "project_name": project_name,
                "saved_filename": filename,
                "requirements_text": str(response),
                "statistics": {
                    "sections_processed": len(SECTIONS),
                    "total_responses": len(all_sections),
                    "timestamp": timestamp,
                    "kb_enhanced": use_kb
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
        "python requirements_demo.py              # Interactive mode - prompts for project name\n"
        "python requirements_demo.py --demo       # Demo mode with sample project\n"
        "python requirements_demo.py --help       # Show this help message\n"
        "python requirements_demo.py --kb         # Use with knowledge base integration\n"
        "python requirements_demo.py --kb ID      # Use with specific knowledge base ID\n"
        "python requirements_demo.py --demo --kb  # Demo with knowledge base integration\n"
        "```\n\n"
        "## Environment Variables:\n"
        "```bash\n"
        "AWS_REGION            # AWS region for knowledge base (default: ap-southeast-2)\n"
        "KNOWLEDGE_BASE_ID     # ID of the knowledge base to use\n"
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
        "## Expected Flow:\n"
        "1. Project Setup: Enter project name and overview\n"
        "2. Section-by-Section Gathering: Go through 5 requirement sections\n"
        "3. AI Analysis: Each response is analyzed for completeness and clarity\n"
        "4. Smart Follow-ups: System asks clarifying questions for low-confidence responses\n"
        "5. Document Generation: Creates comprehensive requirements document\n"
        "6. File Output: Saves final document as markdown file\n\n"
    )
    
    # Add information about tools
    if CUSTOM_TOOLS_AVAILABLE:
        usage_text += (
            "## Tools Used:\n"
            "1. handoff_to_user: Enables interactive user input collection\n"
            "2. evaluate_confidence: Analyzes response quality and confidence\n"
            "3. validate_response: Identifies issues and suggests improvements\n"
        )
        if 'query_knowledge_base' in globals():
            usage_text += "4. query_knowledge_base: Retrieves information from knowledge base\n\n"
        else:
            usage_text += "\n"
    else:
        usage_text += (
            "## Tools Used:\n"
            "1. handoff_to_user: Enables interactive user input collection\n"
        )
        if 'query_knowledge_base' in globals():
            usage_text += "2. query_knowledge_base: Retrieves information from knowledge base\n"
        usage_text += "   (Additional tools available if you add evaluate_confidence.py and validate_response.py to tools folder)\n\n"
    
    usage_text += (
        "## handoff_to_user Tool Workflow:\n"
        "The system uses two modes of the handoff_to_user tool:\n\n"
        "1. CONTINUE MODE (breakout_of_loop=False):\n"
        "   - Agent requests user input for each section\n"
        "   - Agent waits for response\n"
        "   - Agent continues execution with the user's input\n"
        "   - Used for the first 4 sections to gather information\n\n"
        "2. BREAK MODE (breakout_of_loop=True):\n"
        "   - Used in the final section\n"
        "   - Agent provides summary and final output\n"
        "   - Agent stops execution completely\n"
        "   - Control returns to the main program\n\n"
        "This creates a structured, section-by-section requirements gathering process\n"
        "with human oversight at each critical decision point.\n\n"
        "## Knowledge Base Integration:\n"
        "When enabled, the system will:\n"
        "1. Query the knowledge base for relevant information\n"
        "2. Incorporate domain knowledge into questions and suggestions\n"
        "3. Provide more informed guidance based on best practices\n"
        "4. Enhance the quality of the requirements document\n\n"
        "## Output Files:\n"
        "- requirements_YYYYMMDD_HHMMSS.md - Main requirements document\n"
        "- Console output with rich formatting and analysis results\n\n"
        "## Tips for Best Results:\n"
        "- Provide detailed responses to initial questions\n"
        "- Be specific about technical requirements and constraints\n"
        "- Include concrete examples and use cases\n"
        "- Answer follow-up questions to improve confidence scores\n"
        "- Review generated document for accuracy and completeness"
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
    handoff_text.append("   - Agent pauses execution and prompts the user\n", style="green")
    handoff_text.append("   - Agent waits for user input\n", style="green")
    handoff_text.append("   - After receiving input, agent CONTINUES processing\n", style="green")
    handoff_text.append("   - Used for the first 4 requirements sections\n\n", style="green")
    
    handoff_text.append("2. BREAK MODE (breakout_of_loop=True):\n", style="bold yellow")
    handoff_text.append("   - Agent pauses execution and prompts the user\n", style="yellow")
    handoff_text.append("   - Agent waits for user input\n", style="yellow")
    handoff_text.append("   - After receiving input, agent STOPS execution completely\n", style="yellow")
    handoff_text.append("   - Used for the final (5th) section to complete the process\n\n", style="yellow")
    
    handoff_text.append("The workflow follows this pattern:\n", style="white")
    handoff_text.append("Start -> Section 1 -> handoff(continue) -> Section 2 -> handoff(continue) -> \n", style="cyan")
    handoff_text.append("Section 3 -> handoff(continue) -> Section 4 -> handoff(continue) -> \n", style="cyan")
    handoff_text.append("Section 5 -> handoff(break) -> End\n\n", style="cyan")
    
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
    if not CUSTOM_TOOLS_AVAILABLE:
        console.print(Panel(
            "[yellow]Enhanced tools not available. Add evaluate_confidence.py and validate_response.py to your tools folder to enable enhanced functionality.[/yellow]",
            title="Tools Not Found",
            border_style="yellow"
        ))
        return
        
    tools_text = Text()
    tools_text.append("REQUIREMENTS GATHERING TOOLS\n\n", style="bold blue")
    
    # Confidence Evaluation Tool
    tools_text.append("1. CONFIDENCE EVALUATION TOOL\n", style="bold green")
    tools_text.append("   Purpose: Analyzes user responses to determine completeness and quality\n", style="green")
    tools_text.append("   Input: User response text and section name\n", style="green")
    tools_text.append("   Output: Confidence score (0-10) and specific feedback\n", style="green")
    tools_text.append("   When Used: After collecting each section's requirements\n\n", style="green")
    
    # Response Validation Tool
    tools_text.append("2. RESPONSE VALIDATION TOOL\n", style="bold yellow")
    tools_text.append("   Purpose: Identifies specific issues in low-confidence responses\n", style="yellow")
    tools_text.append("   Input: User response and requirements type\n", style="yellow")
    tools_text.append("   Output: List of issues and improvement suggestions\n", style="yellow")
    tools_text.append("   When Used: When confidence score is below threshold (7.0)\n\n", style="yellow")
    
    # Knowledge Base Tool (if available)
    if 'query_knowledge_base' in globals():
        tools_text.append("3. KNOWLEDGE BASE TOOL\n", style="bold blue")
        tools_text.append("   Purpose: Retrieves relevant information from knowledge base\n", style="blue")
        tools_text.append("   Input: Query text to search for in the knowledge base\n", style="blue")
        tools_text.append("   Output: Relevant information from the knowledge base\n", style="blue")
        tools_text.append("   When Used: Before asking questions or providing guidance\n\n", style="blue")
    
    # Enhanced Workflow
    tools_text.append("ENHANCED WORKFLOW:\n", style="bold white")
    tools_text.append("1. Agent asks question via handoff_to_user\n", style="white")
    tools_text.append("2. User provides response\n", style="white")
    tools_text.append("3. Agent evaluates confidence using evaluate_confidence tool\n", style="white")
    tools_text.append("4. If confidence is low, agent validates using validate_response tool\n", style="white")
    tools_text.append("5. Agent asks follow-up questions based on validation results\n", style="white")
    tools_text.append("6. Process repeats until high-quality requirements are gathered\n\n", style="white")
    
    tools_text.append("This creates an intelligent requirements gathering process that actively\n", style="cyan")
    tools_text.append("improves response quality through targeted follow-up questions.", style="cyan")
    
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
    kb_text.append(f"   {KNOWLEDGE_BASE_ID}\n\n", style="green")
    
    kb_text.append("AWS REGION:\n", style="bold green")
    kb_text.append(f"   {AWS_REGION}\n\n", style="green")
    
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
            if use_kb:
                print_kb_info()
            if CUSTOM_TOOLS_AVAILABLE:
                print_tools_info()  # Only show tools info if available
            time.sleep(2)  # Give user time to read the info
            result = demo_with_sample_project(use_kb=use_kb)
        elif use_kb:
            print_handoff_info()
            print_kb_info()
            if CUSTOM_TOOLS_AVAILABLE:
                print_tools_info()
            time.sleep(2)
            result = gather_requirements(use_kb=use_kb)
        else:
            console.print(f"[red]Unknown argument: {' '.join(sys.argv[1:])}[/red]")
            console.print("Use --help for usage information")
            return
    else:
        # Interactive mode
        print_handoff_info()
        if CUSTOM_TOOLS_AVAILABLE:
            print_tools_info()  # Only show tools info if available
        time.sleep(2)  # Give user time to read the info
        result = gather_requirements(use_kb=False)
    
    # Print final result summary
    if result.get("status") == "success":
        console.print(f"\n[bold green]Requirements gathering completed successfully![/bold green]")
        console.print(f"[green]Project: {result.get('project_name', 'Unknown')}[/green]")
        console.print(f"[green]Document: {result.get('saved_filename', 'Not saved')}[/green]")
        console.print(f"[green]Sections: {result.get('statistics', {}).get('sections_processed', 0)}[/green]")
        console.print(f"[green]Responses: {result.get('statistics', {}).get('total_responses', 0)}[/green]")
        if result.get('statistics', {}).get('kb_enhanced', False):
            console.print(f"[green]Knowledge Base Enhanced: Yes[/green]")
    elif result.get("status") == "interrupted":
        console.print(f"\n[yellow]Session was interrupted but partial data may be available.[/yellow]")
    else:
        console.print(f"\n[red]Requirements gathering failed.[/red]")
        if "error" in result:
            console.print(f"[red]Error: {result['error']}[/red]")
    
    console.print(f"\n[dim]Thank you for using the Requirements Gathering System![/dim]")


if __name__ == "__main__":
    main()