import logging
import os
import time
import requests
import xml.etree.ElementTree as ET

class IBKRFlexQuery:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://gdcdyn.interactivebrokers.com/Universal/servlet"
    
    def execute_query(self, query_id, version="3"):
        reference_code = self._request_query_execution(query_id, version)
        if not reference_code:
            raise Exception("Error requesting query execution")
        return self._get_query_results(reference_code, version)
    
    def _request_query_execution(self, query_id, version):
        url = f"{self.base_url}/FlexStatementService.SendRequest"
        params = {
            't': self.token,
            'q': query_id,
            'v': version
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            root = ET.fromstring(response.text)
            if root.find('.//ErrorMessage') is not None:
                raise Exception(f"Error in IBKR: {root.find('.//ErrorMessage').text}")
            reference_code = root.find('.//ReferenceCode')
            if reference_code is not None:
                return reference_code.text
            raise Exception("No reference code received")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request error: {e}")
    
    def _get_query_results(self, reference_code, version, max_attempts=30):
        url = f"{self.base_url}/FlexStatementService.GetStatement"
        params = {
            't': self.token,
            'q': reference_code,
            'v': version
        }
        for attempt in range(max_attempts):
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                if "Statement generation in progress" in response.text:
                    time.sleep(2)
                    continue
                root = ET.fromstring(response.text)
                if root.find('.//ErrorMessage') is not None:
                    raise Exception(f"Error in IBKR: {root.find('.//ErrorMessage').text}")
                return response.text
            except requests.exceptions.RequestException as e:
                raise Exception(f"Request error: {e}")
        raise Exception("Timeout: Statement was not generated in the expected time")

def get_all_dividends() -> list:
    """Gets all dividends from the IBKR Flex Query, without filtering by date"""
    logger = logging.getLogger(__name__)
    logger.info("Querying ALL dividends from IBKR API")
    
    try:
        TOKEN = os.getenv('IBKR_FLEX_TOKEN')
        QUERY_ID = os.getenv('IBKR_DIVIDENDS_QUERY_ID')
        
        if not TOKEN or not QUERY_ID:
            logger.warning("Token or Query ID not configured, using example data")
            return _get_example_dividends()
        
        client = IBKRFlexQuery(TOKEN)
        xml_data = client.execute_query(QUERY_ID)
        root = ET.fromstring(xml_data)
        dividends = []

        for accrual in root.findall(".//ChangeInDividendAccrual"):
            accrual_date = accrual.get("date")
            formatted_date = f"{accrual_date[:4]}-{accrual_date[4:6]}-{accrual_date[6:8]}" if accrual_date else ""
            dividend = {
                "ticker": accrual.get("symbol"),
                "fecha": formatted_date,
                "dividendo_bruto": abs(float(accrual.get("grossAmount", 0))),
                "tax": float(accrual.get("tax", 0)),
                "currency": accrual.get("currency"),
                "fxRateToBase": float(accrual.get("fxRateToBase", 1)),
                "description": accrual.get("description", ""),
                "exDate": accrual.get("exDate", ""),
                "payDate": accrual.get("payDate", ""),
                "fee": abs(float(accrual.get("fee", 0))),
                "netAmount": abs(float(accrual.get("netAmount", 0)))
            }
            dividends.append(dividend)

        # Also include dividends from CashTransaction (if they exist)
        for cash_txn in root.findall(".//CashTransaction"):
            activity_description = cash_txn.get("activityDescription", "")
            if "dividend" in activity_description.lower():
                txn_date = cash_txn.get("dateTime", "")
                formatted_date = f"{txn_date[:4]}-{txn_date[4:6]}-{txn_date[6:8]}" if txn_date else ""
                dividend = {
                    "ticker": cash_txn.get("symbol", ""),
                    "fecha": formatted_date,
                    "dividendo_bruto": abs(float(cash_txn.get("amount", 0))),
                    "tax": 0,
                    "currency": cash_txn.get("currency", ""),
                    "fxRateToBase": abs(float(cash_txn.get("fxRateToBase", 1))),
                    "description": activity_description,
                    "exDate": "",
                    "payDate": formatted_date,
                    "fee": 0,
                    "netAmount": abs(float(cash_txn.get("amount", 0)))
                }
                dividends.append(dividend)

        logger.info(f"Found {len(dividends)} dividends in total")
        return dividends

    except Exception as e:
        logger.error(f"Error getting dividends from IBKR: {str(e)}")
        return _get_example_dividends()

def _get_example_dividends() -> list:
    logger = logging.getLogger(__name__)
    logger.info("Using example data")
    xml_data = """
    <FlexQueryResponse queryName="Daily Dividends" type="AF">
        <FlexStatements count="1">
            <FlexStatement accountId="" fromDate="20250715" toDate="20250715" period="LastBusinessDay" whenGenerated="20250716;210552">
                <ChangeInDividendAccruals>
                    <ChangeInDividendAccrual currency="USD" fxRateToBase="0.86192" symbol="ARE" description="ALEXANDRIA REAL ESTATE EQUIT" date="20250715" exDate="20250630" payDate="20250715" tax="-4.95" fee="0" grossAmount="-33" netAmount="-28.05" />
                    <ChangeInDividendAccrual currency="USD" fxRateToBase="0.86192" symbol="O" description="REALTY INCOME CORP" date="20250715" exDate="20250701" payDate="20250715" tax="-4.04" fee="0" grossAmount="-26.9" netAmount="-22.86" />
                </ChangeInDividendAccruals>
            </FlexStatement>
        </FlexStatements>
    </FlexQueryResponse>
    """
    root = ET.fromstring(xml_data)
    dividends = []

    for accrual in root.findall(".//ChangeInDividendAccrual"):
        dividend = {
            "ticker": accrual.get("symbol"),
            "fecha": "2025-07-15",
            "dividendo_bruto": float(accrual.get("grossAmount")),
            "tax": float(accrual.get("tax")),
            "currency": accrual.get("currency"),
            "fxRateToBase": float(accrual.get("fxRateToBase")),
            "description": accrual.get("description", ""),
            "exDate": accrual.get("exDate", ""),
            "payDate": accrual.get("payDate", ""),
            "fee": float(accrual.get("fee", 0)),
            "netAmount": float(accrual.get("netAmount", 0))
        }
        dividends.append(dividend)
    return dividends

def setup_ibkr_credentials(token: str, query_id: str):
    os.environ['IBKR_FLEX_TOKEN'] = token
    os.environ['IBKR_DIVIDENDS_QUERY_ID'] = query_id