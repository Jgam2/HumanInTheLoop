# Human-in-the-Loop with Knowledge Base Integration

This repository demonstrates advanced human-in-the-loop AI workflows using the Strands framework, with integration to Amazon Bedrock Knowledge Base for enhanced responses.

## Features

- **Interactive Human-in-the-Loop Workflows**: Using the `handoff_to_user` tool to create collaborative AI experiences
- **Knowledge Base Integration**: Leveraging Amazon Bedrock Knowledge Base for retrieval-augmented generation
- **Requirements Gathering System**: A complete example application for collecting project requirements
- **Custom Tools**: Confidence evaluation and response validation tools for enhanced interactions
- **Rich Console Interface**: Beautiful formatting with progress tracking and visual feedback
- **Comprehensive Documentation**: Detailed output with analysis and validation results

## Getting Started

### Prerequisites

- Python 3.10+
- AWS account with Bedrock access
- Configured AWS credentials
- Strands framework and tools

### Installation

1. Clone this repository:
git clone https://github.com/Jgam2/HumanInTheLoop.git cd HumanInTheLoop


2. Create and activate a virtual environment:
Windows
python -m venv venv venv\Scripts\activate

Linux/Mac
python -m venv venv source venv/bin/activate


3. Install dependencies:
pip install -r requirements.txt


4. Configure your AWS credentials:
Set environment variables
Windows
set AWS_ACCESS_KEY_ID=your_access_key set AWS_SECRET_ACCESS_KEY=your_secret_key set AWS_REGION=ap-southeast-2

Linux/Mac
export AWS_ACCESS_KEY_ID=your_access_key export AWS_SECRET_ACCESS_KEY=your_secret_key export AWS_REGION=ap-southeast-2


## Running the Examples

### Requirements Gathering System

This example demonstrates a structured requirements gathering process with human-in-the-loop interactions:

python src/requirements_demo.py


Options:
- `--demo`: Run with a sample project
- `--help`: Show usage information
- `--kb`: Enable knowledge base integration
- `--kb YOUR_KB_ID`: Use a specific knowledge base ID

### Knowledge Base Integration

The system can be enhanced with Amazon Bedrock Knowledge Base integration:

python src/requirements_demo.py --kb


This will:
1. Query the knowledge base for relevant information
2. Incorporate domain knowledge into questions and suggestions
3. Provide more informed guidance based on best practices
4. Enhance the quality of the requirements document

## How It Works

### Human-in-the-Loop Pattern

The system uses the `handoff_to_user` tool in two modes:

1. **Continue Mode** (`breakout_of_loop=False`): 
   - Agent pauses execution and prompts the user
   - Agent waits for user input
   - After receiving input, agent CONTINUES processing
   - Used for the first 4 requirements sections

2. **Break Mode** (`breakout_of_loop=True`):
   - Agent pauses execution and prompts the user
   - Agent waits for user input
   - After receiving input, agent STOPS execution completely
   - Used for the final section to complete the process

This creates a structured, section-by-section requirements gathering process with human oversight at each critical decision point.

### Requirements Gathering Workflow

1. **Project Scope**: Collect project objectives, main goals, and overall scope
2. **User Stories**: Gather user stories, use cases, and workflows
3. **Technical Constraints**: Document technical requirements, platforms, and limitations
4. **Success Criteria**: Define success metrics and acceptance criteria
5. **File Format Support**: Specify required file formats and data specifications

For each section:
- Agent asks clear, focused questions
- User provides detailed responses
- Agent analyzes response quality and completeness
- Agent asks follow-up questions if needed
- Agent summarizes and moves to the next section

### Enhanced Tools

The system includes optional enhanced tools:

1. **Confidence Evaluation**: Analyzes response quality and provides a confidence score
2. **Response Validation**: Identifies issues and suggests improvements
3. **Knowledge Base Integration**: Retrieves relevant information from a knowledge base

## Project Structure

. ├── src/ # Source code │ ├── tools/ # Custom tools │ │ ├── init.py │ │ ├── evaluate_confidence.py │ │ └── validate_response.py │ ├── requirements_demo.py │ └── kb_chatbot_example.py ├── tests/ # Test files │ ├── init.py │ └── test_kb_handoff.py ├── .gitignore ├── README.md └── requirements.txt


## Output Files

The system generates a comprehensive requirements document:
- `requirements_YYYYMMDD_HHMMSS.md` - Markdown file with all gathered requirements
- Includes metadata, section summaries, and analysis results

## Tips for Best Results

- Provide detailed responses to initial questions
- Be specific about technical requirements and constraints
- Include concrete examples and use cases
- Answer follow-up questions to improve confidence scores
- Review generated document for accuracy and completeness

## Extending the System

You can extend the system by:

1. Adding new custom tools in the `tools/` directory
2. Enhancing the knowledge base with domain-specific information
3. Modifying the system prompt to focus on different types of requirements
4. Adding new sections to the requirements gathering process
5. Implementing additional output formats (JSON, HTML, etc.)

## Troubleshooting

### AWS Credentials

If you encounter AWS authentication issues:

1. Verify your credentials are correctly set up in:
   - Environment variables
   - `~/.aws/credentials` file
   - AWS CLI configuration

2. Ensure your IAM user/role has appropriate permissions for:
   - Bedrock model invocation
   - Knowledge base access
   - OpenSearch operations

### Strands Framework Issues

If you encounter issues with the Strands framework:

1. Verify you have the correct version installed:
pip show strands


2. Check for any error messages in the console output

3. Try reinstalling the package:
pip uninstall strands pip install strands


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.