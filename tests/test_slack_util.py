import pytest
from unittest.mock import MagicMock, patch
from utils.slack_util import check_slack_token, get_todays_slack_urls
from freezegun import freeze_time
import os


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
def test_check_slack_token(mock_WebClient):
    # Arrange
    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client
    mock_response = {"ok": True}
    mock_client.auth_test.return_value = mock_response

    # Act
    check_slack_token()

    # Assert
    mock_WebClient.assert_any_call(token='SLACK_API_TOKEN')
    mock_client.auth_test.assert_called_once()
    assert mock_response["ok"]

    print('SLACK_API_TOKEN: ', os.environ.get('SLACK_API_TOKEN'))


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
def test_check_slack_token_invalid(mock_WebClient):
    # Arrange
    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client
    mock_response = {"ok": False}
    mock_client.auth_test.return_value = mock_response

    # Act
    check_slack_token()

    # Assert
    mock_WebClient.assert_any_call(token='SLACK_API_TOKEN')
    mock_client.auth_test.assert_called_once()
    assert not mock_response["ok"]

    print('SLACK_API_TOKEN: ', os.environ.get('SLACK_API_TOKEN'))


@patch.dict(os.environ, {'SLACK_API_TOKEN': 'SLACK_API_TOKEN'})
@patch('utils.slack_util.WebClient')
# Replace with the date corresponding to the 'ts' in your mock_response
@freeze_time("2022-01-03")
def test_get_todays_slack_urls(mock_WebClient):
    # Arrange
    mock_client = MagicMock()
    mock_WebClient.return_value = mock_client
    mock_response = {
        'messages': [
            {
                'ts': '1641234567.123456',
                'text': 'Check out this song: https://open.spotify.com/track/track1'
            },
            {
                'ts': '1641234567.123457',
                'text': 'Another song: https://open.spotify.com/track/track2'
            },
            {
                'ts': '1641234567.123458',
                'text': 'Not a Spotify link'
            }
        ]
    }
    mock_client.conversations_history.return_value = mock_response

    # Act
    result = get_todays_slack_urls()

    # Assert
    mock_WebClient.assert_any_call(token='SLACK_API_TOKEN')
    mock_client.conversations_history.assert_called_once_with(
        channel='CAB3JFSQN')
    assert len(result) == 2
    assert result[0] == {'track_id': 'track1',
                         'timestamp': '1641234567.123456'}
    assert result[1] == {'track_id': 'track2',
                         'timestamp': '1641234567.123457'}

    print('SLACK_API_TOKEN: ', os.environ.get('SLACK_API_TOKEN'))
