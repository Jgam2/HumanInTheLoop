# Strands Human-in-the-Loop Functionality with Knowledge Base Integration

This repository demonstrates advanced human-in-the-loop AI workflows using the Strands framework, with integration to Amazon Bedrock Knowledge Base for enhanced responses.

## Features

- **Interactive Human-in-the-Loop Workflows**: Using the `handoff_to_user` tool to create collaborative AI experiences
- **Agents as Tools Pattern**: Specialized agents for evaluation, validation, and document generation
- **Knowledge Base Integration**: Leveraging Amazon Bedrock Knowledge Base for retrieval-augmented generation
- **Requirements Gathering System**: A complete example application for collecting project requirements
- **Streamlined Process**: Efficient workflow with focused questions and comprehensive validation
- **Rich Console Interface**: Beautiful formatting with progress tracking and visual feedback
- **DynamoDB Integration**: Optional storage of requirements documents in AWS DynamoDB

## Getting Started

### Prerequisites

- Python 3.10+
- AWS account with Bedrock access
- Configured AWS credentials
- Strands framework and tools

### Installation

1. Clone this repository:
```bash
git clone https://github.com/Jgam2/HumanInTheLoop.git
cd HumanInTheLoop

Create and activate a virtual environment:
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate

Install dependencies:
pip install -r requirements.txt
```

#### Configure your AWS credentials:

## Set environment variables
```bash
# Windows
set AWS_ACCESS_KEY_ID=your_access_key
set AWS_SECRET_ACCESS_KEY=your_secret_key
set AWS_REGION=ap-southeast-2

# Linux/Mac
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=ap-southeast-2
```

### Running the Examples

### Requirements Gathering System
This example demonstrates a structured requirements gathering process with human-in-the-loop interactions:
```bash
python src/requirements_demo.py
```
#### Options:
```bash
--demo: Run with a sample project
--help: Show usage information
--kb: Enable knowledge base integration
--kb YOUR_KB_ID: Use a specific knowledge base ID
```
### Knowledge Base Integration

The system can be enhanced with Amazon Bedrock Knowledge Base integration:
```bash
python src/requirements_demo.py --kb
```

#### This will:

- Query the knowledge base for relevant information
- Incorporate domain knowledge into questions and suggestions
- Provide more informed guidance based on best practices
- Enhance the quality of the requirements document

### How It Works

### Human-in-the-Loop Pattern
The system uses the handoff_to_user tool in two modes
##### Continue Mode (breakout_of_loop=False):
- Agent pauses execution and prompts the user
- Agent waits for user input
- After receiving input, agent CONTINUES processing
- Used for the first 5 requirements sections and review

##### Break Mode (breakout_of_loop=True):
- Agent pauses execution and prompts the user
- Agent waits for user input
- After receiving input, agent STOPS execution completely
- Used for the additional information section to complete input gathering

###### This creates a structured, section-by-section requirements gathering process with human oversight at each critical decision point.


### Agents as Tools Pattern
#### The system implements the "Agents as Tools" architectural pattern:
- **Main Orchestrator Agent**: Handles user interaction and coordinates the overall process
- **Evaluation Agent**: Specialized agent for assessing response quality and confidence
- **Validation Agent**: Specialized agent for identifying issues in responses
- **Document Generation Agent**: Specialized agent for creating the final requirements document

#### This approach provides:
- Separation of concerns with focused expertise
- Improved response quality through specialized analysis
- Modular architecture that's easy to extend
- Clear delegation of tasks to the most appropriate agent

#### Requirements Gathering Workflow
- **Project Scope**: Collect project objectives, main goals, and overall scope
- **User Stories**: Gather user stories, use cases, and workflows
- **Technical Constraints**: Document technical requirements, platforms, and limitations
- **Success Criteria**: Define success metrics and acceptance criteria
- **File Format Support**: Specify required file formats and data specifications
- **Additional Information**: Ask if the user wants to add anything else
- **Validation and Confidence Scoring**: Evaluate the quality of all responses
- **Document Generation**: Create a comprehensive requirements document
- **User Review**: Allow the user to review and request changes
- **Storage**: Save locally and optionally to DynamoDB

#### Enhanced Tools
##### The system includes several specialized tools:
- **handoff_to_user**: Enables interactive user input collection
- **evaluate_confidence**: Specialized agent for evaluating response quality
- **validate_response**: Specialized agent for identifying issues in responses
- **generate_requirements_doc**: Specialized agent for document generation
- **query_knowledge_base**: Retrieves relevant information from knowledge base


#### Project Structure
```bash
├── src/
│   ├── requirements_demo.py
│   └── kb_chatbot_example.py
├── tests/
│   ├── __init__.py
│   └── test_kb_handoff.py
├── .gitignore
├── README.md
└── requirements.txt
```

#### Output Files

- The system generates a comprehensive requirements document:
- requirements_YYYYMMDD_HHMMSS.md - Markdown file with all gathered requirements
- Includes executive summary, detailed sections, and confidence scores
- Optional storage in DynamoDB for persistence and sharing

#### Tips for Best Results
- Provide detailed responses to initial questions
- Be specific about technical requirements and constraints
- Include concrete examples and use cases
- Add any additional information when prompted
- Review the generated document carefully before finalizing

#### Extending the System
##### You can extend the system by:
- Adding new specialized agent tools
- Enhancing the knowledge base with domain-specific information
- Modifying the system prompt to focus on different types of requirements
- Adding new sections to the requirements gathering process
- Implementing additional output formats (JSON, HTML, etc.)

#### Troubleshooting
##### AWS Credentials
- If you encounter AWS authentication issues:
- Verify your credentials are correctly set up in:

##### Environment variables
```bash
~/.aws/credentials file
```
#### AWS CLI configuration
###### Ensure your IAM user/role has appropriate permissions for:
- Bedrock model invocation
- Knowledge base access
- DynamoDB operations

### Strands Framework Issues

##### If you encounter issues with the Strands framework:
Verify you have the correct version installed:
```bash
pip show strands
```
##### Check for any error messages in the console output

###### Try reinstalling the package:
```bash
pip uninstall strands
pip install strands
```
##### Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

##### License
This project is licensed under the MIT License - see the LICENSE file for details.


