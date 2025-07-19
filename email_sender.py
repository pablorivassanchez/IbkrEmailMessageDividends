import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict

def _format_date(date_str: str) -> str:
    """
    Formats the date for display in the email.
    
    Args:
        date_str (str): Date in YYYY-MM-DD format.
        
    Returns:
        str: Formatted date.
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        months = [
            'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]
        return f"{date_obj.day} de {months[date_obj.month - 1]} de {date_obj.year}"
    except (ValueError, IndexError):
        return date_str

def _get_dates_string(dividends: List[Dict], fallback_date: str) -> str:
    """
    Generates a string with the dividend dates.
    If there are up to 3 distinct dates, it lists them. If more, it shows a range.
    
    Args:
        dividends (List[Dict]): List of dividends.
        fallback_date (str): Fallback date in YYYY-MM-DD format.
        
    Returns:
        str: String with the formatted date(s).
    """
    if not dividends:
        return _format_date(fallback_date)
        
    dividend_dates = sorted(list(set(d.get('fecha') for d in dividends if d.get('fecha'))))
    
    if not dividend_dates:
        return _format_date(fallback_date)
    
    formatted_dates = [_format_date(d) for d in dividend_dates]

    if len(formatted_dates) == 1:
        return formatted_dates[0]
    elif len(formatted_dates) <= 3:
        return ", ".join(formatted_dates)
    else:
        return f"{formatted_dates[0]} to {formatted_dates[-1]}"


def send_dividend_email(dividends: List[Dict], date: str):
    """
    Sends an email with the received dividends.

    Args:
        dividends (List[Dict]): List of dividends.
        date (str): Reference date in YYYY-MM-DD format, used as a fallback.
    """
    logger = logging.getLogger(__name__)
    
    if not dividends:
        logger.info("No dividends to send")
        return
    
    try:
        # Email configuration from environment variables
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('SENDER_EMAIL')
        recipient_email = os.getenv('RECIPIENT_EMAIL')

        # Use specific credentials for the email sending API
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        if not all([sender_email, smtp_username, smtp_password, recipient_email]):
            logger.error("Email configuration is incomplete. Check SENDER_EMAIL, RECIPIENT_EMAIL, SMTP_USERNAME, and SMTP_PASSWORD environment variables.")
            return

        # Generate the date string for the title
        dates_str = _get_dates_string(dividends, date)
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"💰 Dividendos del {dates_str}"
        message["From"] = sender_email
        message["To"] = recipient_email
        
        # Create HTML content
        html_content = _create_html_content(dividends, dates_str)
        
        # Attach HTML content
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Send email
        logger.info(f"Sending email to {recipient_email}")
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
        
        logger.info("Email sent successfully")
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")

def _create_html_content(dividends: List[Dict], dates_display_str: str) -> str:
    """
    Creates the HTML content for the email.

    Args:
        dividends (List[Dict]): List of dividends.
        dates_display_str (str): String with formatted dates to display.

    Returns:
        str: Formatted HTML content.
    """
    
    # --- Calculation of totals and exchange rates ---
    total_gross_eur = 0
    total_tax_eur = 0
    total_net_eur = 0
    exchange_rates = {}  # To store unique exchange rates

    # Calculate totals in EUR and collect exchange rates
    for d in dividends:
        fx_rate = d.get('fxRateToBase', 1)
        total_gross_eur += abs(d['dividendo_bruto']) * fx_rate
        total_tax_eur += abs(d['tax']) * fx_rate
        total_net_eur += abs(d['netAmount']) * fx_rate
        
        # Save the exchange rate if we don't have it already
        currency = d.get('currency')
        if currency and currency not in exchange_rates:
            exchange_rates[currency] = fx_rate
            
    # Create the footer string with all currencies
    rate_strings = [f"1 {cur} = €{rate:.4f}" for cur, rate in exchange_rates.items()]
    footer_rates_text = " • ".join(rate_strings) if rate_strings else "No se encontraron tipos de cambio."
    
    # --- End of calculation ---

    # Create table rows
    table_rows = ""
    for dividend in dividends:
        fx_rate = dividend.get('fxRateToBase', 1)
        gross_eur = abs(dividend['dividendo_bruto']) * fx_rate
        tax_eur = abs(dividend['tax']) * fx_rate
        net_eur = abs(dividend['netAmount']) * fx_rate
        
        # Determine the currency symbol
        currency_symbol = "$" if dividend.get("currency") == "USD" else dividend.get("currency", "")
        
        table_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50;">
                {dividend['ticker']}
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; font-size: 12px; color: #7f8c8d; max-width: 200px;">
                {dividend['description']}
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: right; font-weight: 600; color: #27ae60;">
                {currency_symbol}{abs(dividend['dividendo_bruto']):.2f}<br>
                <span style="font-size: 12px; color: #7f8c8d;">€{gross_eur:.2f}</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: right; color: #e74c3c;">
                {currency_symbol}{abs(dividend['tax']):.2f}<br>
                <span style="font-size: 12px; color: #7f8c8d;">€{tax_eur:.2f}</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: right; font-weight: 600; color: #2980b9;">
                {currency_symbol}{abs(dividend['netAmount']):.2f}<br>
                <span style="font-size: 12px; color: #7f8c8d;">€{net_eur:.2f}</span>
            </td>
        </tr>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Resumen de Dividendos</title>
    </head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f7fa;">
        <div style="max-width: 800px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden;">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center;">
                <h1 style="margin: 0; font-size: 28px; font-weight: 300;">💰 Dividend Summary</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">{dates_display_str}</p>
            </div>
            
            <!-- Summary Cards (consolidated total in EUR) -->
            <div style="padding: 30px; background-color: #f8f9fc;">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;">
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #27ae60;">
                        <h3 style="margin: 0 0 10px 0; color: #2c3e50; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Gross Dividend</h3>
                        <p style="margin: 0; font-size: 24px; font-weight: 600; color: #27ae60;">€{total_gross_eur:.2f}</p>
                    </div>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #e74c3c;">
                        <h3 style="margin: 0 0 10px 0; color: #2c3e50; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Taxes</h3>
                        <p style="margin: 0; font-size: 24px; font-weight: 600; color: #e74c3c;">€{total_tax_eur:.2f}</p>
                    </div>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #2980b9;">
                        <h3 style="margin: 0 0 10px 0; color: #2c3e50; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Dividendo Neto</h3>
                        <p style="margin: 0; font-size: 24px; font-weight: 600; color: #2980b9;">€{total_net_eur:.2f}</p>
                    </div>
                    
                </div>
            </div>
            
            <!-- Detailed Table -->
            <div style="padding: 0 30px 30px 30px;">
                <h2 style="color: #2c3e50; margin: 0 0 20px 0; font-size: 20px; font-weight: 600;">Detalle por Acción</h2>
                
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <thead>
                            <tr style="background: #f8f9fc;">
                                <th style="padding: 15px 12px; text-align: left; font-weight: 600; color: #2c3e50; border-bottom: 2px solid #e0e0e0;">Ticker</th>
                                <th style="padding: 15px 12px; text-align: left; font-weight: 600; color: #2c3e50; border-bottom: 2px solid #e0e0e0;">Empresa</th>
                                <th style="padding: 15px 12px; text-align: right; font-weight: 600; color: #2c3e50; border-bottom: 2px solid #e0e0e0;">Dividendo Bruto</th>
                                <th style="padding: 15px 12px; text-align: right; font-weight: 600; color: #2c3e50; border-bottom: 2px solid #e0e0e0;">Impuestos</th>
                                <th style="padding: 15px 12px; text-align: right; font-weight: 600; color: #2c3e50; border-bottom: 2px solid #e0e0e0;">Dividendo Neto</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="background: #f8f9fc; padding: 20px; text-align: center; border-top: 1px solid #e0e0e0;">
                <p style="margin: 0; color: #7f8c8d; font-size: 14px;">
                    📊 Reporte generado automáticamente • {len(dividends)} dividendos recibidos
                </p>
                 <p style="margin: 5px 0 0 0; color: #7f8c8d; font-size: 12px;">
                    {footer_rates_text}
                </p>
            </div>
            
        </div>
    </body>
    </html>
    """
    
    return html_content


# Example of use to test the script directly
if __name__ == "__main__":
    # Configure logging to see console output
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # --- Example data with multiple currencies and dates ---
    # Uncomment and modify as needed for testing
    
    # Case 1: Single date
    # test_dividends = [
    #     {
    #         "ticker": "AAPL", "fecha": "2025-07-15", "dividendo_bruto": 50.00, "tax": -7.50,
    #         "netAmount": 42.50, "currency": "USD", "fxRateToBase": 0.9250, "description": "APPLE INC", "fee": 0
    #     }
    # ]
    # date_to_test = "2025-07-15"
    
    # Case 2: Multiple dates (will be listed)
    test_dividends = [
        {
            "ticker": "AAPL", "fecha": "2025-07-15", "dividendo_bruto": 50.00, "tax": -7.50,
            "netAmount": 42.50, "currency": "USD", "fxRateToBase": 0.9250, "description": "APPLE INC", "fee": 0
        },
        {
            "ticker": "HSBC", "fecha": "2025-07-16", "dividendo_bruto": 40.00, "tax": -10.00,
            "netAmount": 30.00, "currency": "GBP", "fxRateToBase": 1.1780, "description": "HSBC HOLDINGS PLC", "fee": 0
        }
    ]
    date_to_test = "2025-07-16"
    
    # Case 3: Many dates (a range will be shown)
    # test_dividends = [
    #     {"ticker": "A", "fecha": "2025-07-15", "dividendo_bruto": 10, "tax": -1, "netAmount": 9, "currency": "USD", "fxRateToBase": 0.92, "description": "Agilent"},
    #     {"ticker": "B", "fecha": "2025-07-16", "dividendo_bruto": 10, "tax": -1, "netAmount": 9, "currency": "USD", "fxRateToBase": 0.92, "description": "Barnes Group"},
    #     {"ticker": "C", "fecha": "2025-07-17", "dividendo_bruto": 10, "tax": -1, "netAmount": 9, "currency": "USD", "fxRateToBase": 0.92, "description": "Citigroup"},
    #     {"ticker": "D", "fecha": "2025-07-18", "dividendo_bruto": 10, "tax": -1, "netAmount": 9, "currency": "USD", "fxRateToBase": 0.92, "description": "Dominion Energy"},
    # ]
    # date_to_test = "2025-07-18"

    
    # Make sure you have a .env file with credentials to test the actual sending
    # or the function will stop if it doesn't find the variables.
    send_dividend_email(test_dividends, date_to_test)