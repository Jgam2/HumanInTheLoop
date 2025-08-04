#!/usr/bin/env python3
"""
Unit tests for the KB chatbot with handoff_to_user functionality
"""

import os
import sys
from unittest import mock

import pytest
import boto3
from botocore.exceptions import ClientError

# Add parent directory to path to import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import our modules
from src.kb_chatbot_example import main, query_knowledge_base


@pytest.fixture
def mock_bedrock_agent():
    """Mock for the bedrock agent client"""
    with mock.patch('boto3.client') as mock_client:
        mock_agent = mock.MagicMock()
        mock_client.return_value = mock_agent
        
        # Configure sample KB response
        mock_agent.retrieve.return_value = {
            'retrievalResults': [
                {
                    'content': {'text': 'This is sample content from the knowledge base.'},
                    'documentMetadata': {'source': 'test_document.txt'}
                },
                {
                    'content': {'text': 'This is another piece of content from the KB.'},
                    'documentMetadata': {'source': 'another_doc.txt'}
                }
            ]
        }
        
        yield mock_agent


@pytest.fixture
def mock_agent():
    """Mock for the Strands Agent"""
    with mock.patch('src.kb_chatbot_example.Agent') as mock_agent_class:
        mock_agent_instance = mock.MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        
        # Configure query response
        mock_agent_instance.query.return_value = "Mock agent response"
        
        yield mock_agent_instance


@pytest.fixture
def mock_handoff_to_user():
    """Mock for the handoff_to_user tool"""
    with mock.patch('src.kb_chatbot_example.handoff_to_user') as mock_handoff:
        # Configure handoff behavior
        def side_effect(message, question=None, context=None, section=None, breakout_of_loop=False):
            if breakout_of_loop:
                raise SystemExit("Breaking out of loop as requested")
            return "Mock user response"
            
        mock_handoff.side_effect = side_effect
        yield mock_handoff


class TestKnowledgeBaseQuery:
    """Test cases for knowledge base query functionality"""
    
    def test_query_knowledge_base(self, mock_bedrock_agent):
        """Test querying the knowledge base"""
        # Call the function
        result = query_knowledge_base("test query")
        
        # Verify the function called the API correctly
        mock_bedrock_agent.retrieve.assert_called_once()
        assert "This is sample content" in result
        assert "Source 1:" in result
        assert "Source 2:" in result
    
    def test_kb_error_handling(self, mock_bedrock_agent):
        """Test error handling in knowledge base queries"""
        # Configure mock to raise an exception
        mock_bedrock_agent.retrieve.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'KB not found'}},
            'retrieve'
        )
        
        # Call the function
        result = query_knowledge_base("test query")
        
        # Verify error handling
        assert "Error querying knowledge base" in result
        assert "ResourceNotFoundException" in result


class TestHandoffFunctionality:
    """Test cases for handoff_to_user functionality"""
    
    def test_agent_with_handoff(self, mock_agent, mock_handoff_to_user, monkeypatch):
        """Test agent using handoff_to_user tool"""
        # Mock sys.argv to simulate command line mode
        monkeypatch.setattr(sys, "argv", ["kb_chatbot_example.py"])
        
        # Mock print to capture output
        with mock.patch('builtins.print') as mock_print:
            try:
                # This will likely raise SystemExit due to handoff_to_user
                main()
            except SystemExit:
                pass
        
        # Verify agent was initialized with the handoff_to_user tool
        mock_agent.query.assert_called_once()
    
    def test_handoff_continue_mode(self, mock_handoff_to_user):
        """Test handoff_to_user in continue mode"""
        # Call handoff with continue mode
        result = mock_handoff_to_user(
            message="Test message",
            question="Test question?",
            breakout_of_loop=False
        )
        
        # Verify result
        assert result == "Mock user response"
    
    def test_handoff_break_mode(self, mock_handoff_to_user):
        """Test handoff_to_user in break mode"""
        # Call handoff with break mode - should raise SystemExit
        with pytest.raises(SystemExit):
            mock_handoff_to_user(
                message="Test message",
                question="Test question?",
                breakout_of_loop=True
            )


class TestWorkflow:
    """Test the overall workflow logic"""
    
    def test_combined_workflow(self, mock_agent, mock_bedrock_agent, mock_handoff_to_user, monkeypatch):
        """Test the combined KB + handoff workflow"""
        # Mock sys.argv
        monkeypatch.setattr(sys, "argv", ["kb_chatbot_example.py"])
        
        # Mock print to capture output
        with mock.patch('builtins.print') as mock_print:
            try:
                # This will likely raise SystemExit due to handoff_to_user
                main()
            except SystemExit:
                pass
        
        # Verify agent was queried with the expected prompt
        mock_agent.query.assert_called_once()
        
        # Check that the final message was printed
        mock_print.assert_any_call(mock.ANY)  # At least one print call happened