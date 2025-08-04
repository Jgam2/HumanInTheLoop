#!/usr/bin/env python3
"""
Knowledge Base Chatbot Example with handoff_to_user functionality

This example demonstrates:
1. Integration with Amazon Bedrock Knowledge Base
2. Human-in-the-loop interactions using handoff_to_user
"""

import logging
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS Configuration
AWS_REGION = "ap-southeast-2"  # Update to match your KB region
KNOWLEDGE_BASE_ID = "I3RO432NC8"  # From the URL you provided

# Try to import the real Strands packages
try:
    from strands_agents import Agent
    from strands_agents_tools import handoff_to_user
    USING_MOCK = False
    logger.info("Using actual Strands packages")
except ImportError:
    logger.warning("Strands packages not found. Using mock implementation for demonstration.")
    USING_MOCK = True
    
    # Mock implementation of handoff_to_user
    def handoff_to_user(message, question=None, context=None, section=None, breakout_of_loop=False):
        """Mock implementation of handoff_to_user tool"""
        print("\n🤝 AGENT REQUESTING USER HANDOFF")
        print("=" * 50)
        print(f"\nQUESTION:\n{question or 'What would you like to do?'}")
        
        if context:
            print(f"\nCONTEXT:\n{context}")
            
        print("\nPlease provide your response below:")
        user_response = input("> ")
        
        if breakout_of_loop:
            print("\nHandoff complete. Agent execution stopped.")
            raise SystemExit("Breaking out of loop as requested")
            
        return user_response
    
    # Mock implementation of Agent
    class Agent:
        """Mock Agent class for demonstration purposes"""
        def __init__(self, tools=None, system_prompt=None):
            self.tools = tools or []
            self.system_prompt = system_prompt
            print(f"Mock Agent initialized with {len(tools)} tools")
            print(f"System prompt: {system_prompt[:100]}...")
            
        def query(self, user_input):
            """Mock query method"""
            print(f"\nProcessing query: {user_input[:50]}...")
            
            # Simulate using the knowledge base
            print("\nSearching knowledge base...")
            kb_results = None
            
            for tool in self.tools:
                if tool.__name__ == 'query_knowledge_base':
                    kb_results = tool("example query")
                    print(f"\nKnowledge base results:\n{kb_results[:200]}...")
                    break
            
            # Simulate first handoff (continue mode)
            print("\nNow I'll demonstrate handoff with continue mode...")
            for tool in self.tools:
                if tool.__name__ == 'handoff_to_user':
                    clarification = tool(
                        message="Asking for clarification",
                        question="What specific information would you like to know?",
                        context="I found some information but need more details to provide a targeted response.",
                        breakout_of_loop=False
                    )
                    print(f"\nUser provided clarification: {clarification}")
                    break
            
            # Simulate processing the clarification
            print("\nProcessing your clarification...")
            print("Generating a response based on your input...")
            
            # Simulate final handoff (break mode)
            print("\nNow I'll demonstrate handoff with break mode...")
            try:
                for tool in self.tools:
                    if tool.__name__ == 'handoff_to_user':
                        final_input = tool(
                            message="Final handoff",
                            question="Is there anything else you'd like to know?",
                            context="I've provided information based on your request. We can continue or conclude our conversation.",
                            breakout_of_loop=True
                        )
                        # This won't be reached due to SystemExit
                        print(f"\nUser provided final input: {final_input}")
                        break
            except SystemExit:
                pass
                
            return "Thank you for using the Knowledge Base Chatbot with Human Handoff!"

# Define the knowledge base query tool at module level
def query_knowledge_base(query):
    """Tool to query the Amazon Bedrock Knowledge Base."""
    try:
        logger.info(f"Querying knowledge base with: {query}")
        
        # Initialize the Bedrock client
        bedrock_agent_client = boto3.client('bedrock-agent', region_name=AWS_REGION)
        
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
        
        # Process results
        results = response.get('retrievalResults', [])
        if not results:
            return "No information found in the knowledge base."
            
        # Format results
        formatted_results = []
        for i, result in enumerate(results, 1):
            content = result.get('content', {}).get('text', 'No content')
            formatted_results.append(f"Source {i}:\n{content}\n")
            
        return "\n".join(formatted_results)
        
    except ClientError as e:
        logger.error(f"Error querying knowledge base: {str(e)}")
        return f"Error querying knowledge base: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        if USING_MOCK:
            # Return mock data for demonstration
            return """
Source 1:
This is sample content from the knowledge base about artificial intelligence and machine learning.
Machine learning is a branch of artificial intelligence that focuses on building systems that learn from data.

Source 2:
Knowledge bases are structured repositories of information that can be queried to retrieve relevant data.
They are commonly used in AI systems to provide factual grounding and reduce hallucinations.

Source 3:
Human-in-the-loop AI combines the strengths of human intelligence with artificial intelligence.
This approach is particularly valuable for complex decision-making processes and sensitive domains.
"""
        else:
            return f"Error querying knowledge base: {str(e)}"

def main():
    """Main function to run the KB chatbot with handoff capability."""
    print("Starting Knowledge Base Chatbot with Human Handoff...")
    print("=" * 50)
    
    # Initialize agent with handoff_to_user and knowledge base tools
    agent = Agent(
        tools=[handoff_to_user, query_knowledge_base],
        system_prompt="""You are a helpful assistant with access to a knowledge base.

        When answering questions:
        1. First use the query_knowledge_base tool to search for relevant information
        2. If the knowledge base has the answer, respond based on that information
        3. If the knowledge base doesn't have enough information, ask the user for clarification
           (use handoff_to_user with breakout_of_loop=False)
        4. For complex requests beyond your capabilities, hand off to a human
           (use handoff_to_user with breakout_of_loop=True)
        
        Use handoff_to_user appropriately to demonstrate both modes."""
    )
    
    try:
        # Start the conversation
        print("\nStarting agent conversation...")
        print("Note: The agent will use the knowledge base and demonstrate handoff modes:")
        print("  - Continue mode (breakout_of_loop=False): Gets input, keeps running")
        print("  - Complete mode (breakout_of_loop=True): Gets input, stops execution")
        print("=" * 50)
        
        # The agent will handle the conversation flow
        response = agent.query(
            """Please demonstrate how you can:
            1. Answer a question using the knowledge base
            2. Ask for clarification if needed (use handoff with breakout_of_loop=False)
            3. Hand off to a human for complex requests (use handoff with breakout_of_loop=True)"""
        )
        
        print(f"\nFinal agent response: {response}")
        
    except KeyboardInterrupt:
        print("\nConversation interrupted by user")
    except Exception as e:
        print(f"\nError occurred: {e}")
    
    print("\nChatbot example completed!")

if __name__ == "__main__":
    main()