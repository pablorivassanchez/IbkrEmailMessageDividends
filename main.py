import logging
from datetime import datetime
from ibkr_client import get_all_dividends
from email_sender import send_dividend_email
from logger import setup_logger
from dotenv import load_dotenv
import os

# Load .env from the directory where main.py is located
env_path = os.path.join(os.path.dirname(__file__), '.env')
# Add override=True to ensure that the values from the .env file are always used
load_dotenv(dotenv_path=env_path, override=True)

def main():
    setup_logger()
    logger = logging.getLogger(__name__)
    logger.info("Starting dividend service")

    try:
        today = datetime.now().strftime("%Y-%m-%d")  # Expected format by the email function
        
        # Get all dividends from IBKR
        dividends = get_all_dividends()
        logger.info(f"Obtained {len(dividends)} dividends from IBKR")

        if dividends:
            send_dividend_email(dividends, today)
            logger.info("Dividend email sent successfully")
        else:
            logger.info("No dividends found in XML. No email sent.")
            
    except Exception as e:
        logger.error(f"Error in dividend service: {str(e)}")

if __name__ == "__main__":
    main()