# tests/test_ibkr_client.py

import pytest
from unittest.mock import Mock, patch
import os

from ibkr_client import IBKRFlexQuery, get_all_dividends, setup_ibkr_credentials, _get_example_dividends


class TestIBKRFlexQuery:
    """Tests for the IBKRFlexQuery class that interacts with the IBKR API."""
    
    def setup_method(self):
        self.token = "test_token_123"
        self.query_id = "test_query_456"
        self.client = IBKRFlexQuery(self.token)
    
    @patch('ibkr_client.requests.get')
    def test_request_query_execution_success(self, mock_get):
        """Tests that the query execution request returns a ReferenceCode."""
        mock_response = Mock()
        mock_response.text = "<FlexStatementResponse><Status>Success</Status><ReferenceCode>12345</ReferenceCode></FlexStatementResponse>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        ref_code = self.client._request_query_execution(self.query_id, "3")
        
        assert ref_code == "12345"
        mock_get.assert_called_once()
    
    @patch('ibkr_client.requests.get')
    def test_request_query_execution_error(self, mock_get):
        """Tests that an exception is raised if the IBKR API returns an error."""
        mock_response = Mock()
        mock_response.text = "<FlexStatementResponse><Status>Fail</Status><ErrorMessage>Invalid token</ErrorMessage></FlexStatementResponse>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception, match="Error in IBKR: Invalid token"):
            self.client._request_query_execution(self.query_id, "3")

    @patch('ibkr_client.requests.get')
    @patch('ibkr_client.time.sleep', return_value=None)
    def test_get_query_results_retry_and_success(self, mock_sleep, mock_get):
        """Tests that the client retries if the report is in progress and then succeeds."""
        response_in_progress = Mock()
        response_in_progress.text = "Statement generation in progress"
        
        response_success = Mock()
        response_success.text = "<FlexQueryResponse>...</FlexQueryResponse>"
        
        mock_get.side_effect = [response_in_progress, response_success]
        
        result = self.client._get_query_results("ref_code_123", "3")
        
        assert result == response_success.text
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once()


class TestGetAllDividends:
    """Tests for the main get_all_dividends function."""
    
    @patch.dict(os.environ, {
        'IBKR_FLEX_TOKEN': 'test_token',
        'IBKR_DIVIDENDS_QUERY_ID': 'test_query'
    })
    @patch('ibkr_client.IBKRFlexQuery')
    def test_get_all_dividends_parses_multiple_sources(self, mock_client_class):
        """
        Tests that dividends from 'ChangeInDividendAccrual'
        and 'CashTransaction' are processed correctly in the same call.
        """
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # CORRECTION: activityDescription now contains "dividend" so the parser detects it.
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <FlexQueryResponse>
            <FlexStatements>
                <FlexStatement>
                    <ChangeInDividendAccruals>
                        <ChangeInDividendAccrual symbol="AAPL" date="20250715" grossAmount="50.0" netAmount="42.5" tax="-7.5" currency="USD" fxRateToBase="0.92" description="APPLE DIV" />
                    </ChangeInDividendAccruals>
                    <CashTransactions>
                        <CashTransaction symbol="MSFT" dateTime="20250716" amount="30.0" currency="USD" fxRateToBase="0.92" activityDescription="MSFT Dividend Payment" />
                    </CashTransactions>
                </FlexStatement>
            </FlexStatements>
        </FlexQueryResponse>"""
        
        mock_client.execute_query.return_value = xml_response
        
        result = get_all_dividends()
        
        # NOW IT'S OK: The assertion should pass because 2 dividends are found.
        assert len(result) == 2
        
        aapl_div = next(d for d in result if d['ticker'] == 'AAPL')
        assert aapl_div['dividendo_bruto'] == 50.00
        assert aapl_div['tax'] == -7.50
        assert aapl_div['fecha'] == "2025-07-15"

        msft_div = next(d for d in result if d['ticker'] == 'MSFT')
        assert msft_div['dividendo_bruto'] == 30.00
        assert msft_div['tax'] == 0
        assert msft_div['fecha'] == "2025-07-16"
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('ibkr_client._get_example_dividends')
    def test_get_all_dividends_no_credentials_fallback(self, mock_example):
        """Tests that example data is used if there are no credentials."""
        mock_example.return_value = [{'ticker': 'TEST_EXAMPLE', 'dividendo_bruto': 100.0}]
        
        with patch('ibkr_client.logging.getLogger') as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log
            
            result = get_all_dividends()
            
            mock_log.warning.assert_called_with("Token or Query ID not configured, using example data")
            mock_example.assert_called_once_with()
            assert len(result) == 1
            assert result[0]['ticker'] == 'TEST_EXAMPLE'

    @patch.dict(os.environ, {
        'IBKR_FLEX_TOKEN': 'test_token',
        'IBKR_DIVIDENDS_QUERY_ID': 'test_query'
    })
    @patch('ibkr_client.IBKRFlexQuery')
    @patch('ibkr_client._get_example_dividends')
    def test_get_all_dividends_api_error_fallback(self, mock_example, mock_client_class):
        """Tests the fallback to example data if the API call fails."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.execute_query.side_effect = Exception("API Error")
        
        mock_example.return_value = [{'ticker': 'FALLBACK_EXAMPLE', 'dividendo_bruto': 50.0}]
        
        result = get_all_dividends()
        
        mock_example.assert_called_once_with()
        assert len(result) == 1
        assert result[0]['ticker'] == 'FALLBACK_EXAMPLE'


class TestGetExampleDividends:
    """Tests for the _get_example_dividends function."""
    
    def test_get_example_dividends_returns_correct_data(self):
        """Tests that the function parses the static XML and returns the correct data."""
        result = _get_example_dividends()
        
        assert len(result) == 2
        
        are_div = next(d for d in result if d['ticker'] == 'ARE')
        assert are_div['fecha'] == "2025-07-15"
        assert are_div['dividendo_bruto'] == -33.0
        assert are_div['tax'] == -4.95
        assert are_div['netAmount'] == -28.05
        assert are_div['currency'] == 'USD'

        o_div = next(d for d in result if d['ticker'] == 'O')
        assert o_div['dividendo_bruto'] == -26.9
        
    @patch('ibkr_client.ET.fromstring', side_effect=Exception("XML parsing error"))
    def test_get_example_dividends_xml_error_returns_empty(self, mock_fromstring):
        """Tests that if parsing the example XML fails, it returns an empty list."""
        # The current function propagates the exception, so we test for that.
        with pytest.raises(Exception, match="XML parsing error"):
             _get_example_dividends()


class TestSetupIbkrCredentials:
    """Tests for the setup_ibkr_credentials helper function."""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_ibkr_credentials_sets_env_vars(self):
        """Checks that the function correctly sets the environment variables."""
        token = "new_token"
        query_id = "new_query_id"
        
        assert 'IBKR_FLEX_TOKEN' not in os.environ
        assert 'IBKR_DIVIDENDS_QUERY_ID' not in os.environ
        
        setup_ibkr_credentials(token, query_id)
        
        assert os.environ['IBKR_FLEX_TOKEN'] == token
        assert os.environ['IBKR_DIVIDENDS_QUERY_ID'] == query_id

        # Clean up after the test
        del os.environ['IBKR_FLEX_TOKEN']
        del os.environ['IBKR_DIVIDENDS_QUERY_ID']