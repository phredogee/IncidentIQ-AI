import pytest
from unittest.mock import patch, MagicMock
from src.summarizer import generate_executive_summary

@patch('src.summarizer.OpenAI')
def test_generate_executive_summary_success(mock_openai_class):
    # Mock the nested client.chat.completions.create() structure
    mock_client = MagicMock()
    mock_response = MagicMock()
    
    # Configure the mock payload return structure to mimic OpenAI/DeepSeek
    mock_message = MagicMock()
    mock_message.content = "This is a successful mock DeepSeek summary of operational incidents."
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_class.return_value = mock_client
    
    # Execute test
    result = generate_executive_summary('[{"ticket_id": "INC001", "description": "Server Down"}]')
    
    assert "mock DeepSeek summary" in result
    mock_client.chat.completions.create.assert_called_once()
