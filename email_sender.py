import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict

def _format_date(date_str: str) -> str:
    """
    Formatea la fecha para mostrar en el correo.
    
    Args:
        date_str (str): Fecha en formato YYYY-MM-DD.
        
    Returns:
        str: Fecha formateada.
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
    Genera un string con las fechas de los dividendos.
    Si hay hasta 3 fechas distintas, las lista. Si hay más, muestra un rango.
    
    Args:
        dividends (List[Dict]): Lista de dividendos.
        fallback_date (str): Fecha de respaldo en formato YYYY-MM-DD.
        
    Returns:
        str: String con la(s) fecha(s) formateada(s).
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
        return f"{formatted_dates[0]} al {formatted_dates[-1]}"


def send_dividend_email(dividends: List[Dict], date: str):
    """
    Envía un correo electrónico con los dividendos recibidos.
    
    Args:
        dividends (List[Dict]): Lista de dividendos.
        date (str): Fecha de referencia en formato YYYY-MM-DD, usada como fallback.
    """
    logger = logging.getLogger(__name__)
    
    if not dividends:
        logger.info("No hay dividendos para enviar")
        return
    
    try:
        # Configuración del correo desde variables de entorno
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('SENDER_EMAIL')
        recipient_email = os.getenv('RECIPIENT_EMAIL')

        # Usar credenciales específicas para la API de envío de correo
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        if not all([sender_email, smtp_username, smtp_password, recipient_email]):
            logger.error("Configuración de correo incompleta. Verifica las variables de entorno SENDER_EMAIL, RECIPIENT_EMAIL, SMTP_USERNAME y SMTP_PASSWORD.")
            return

        # Generar el string de fechas para el título
        dates_str = _get_dates_string(dividends, date)
        
        # Crear mensaje
        message = MIMEMultipart("alternative")
        message["Subject"] = f"💰 Dividendos del {dates_str}"
        message["From"] = sender_email
        message["To"] = recipient_email
        
        # Crear contenido HTML
        html_content = _create_html_content(dividends, dates_str)
        
        # Adjuntar contenido HTML
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Enviar correo
        logger.info(f"Enviando correo a {recipient_email}")
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
        
        logger.info("Correo enviado exitosamente")
        
    except Exception as e:
        logger.error(f"Error al enviar correo: {str(e)}")

def _create_html_content(dividends: List[Dict], dates_display_str: str) -> str:
    """
    Crea el contenido HTML para el correo electrónico.
    
    Args:
        dividends (List[Dict]): Lista de dividendos.
        dates_display_str (str): String con las fechas formateadas para mostrar.
        
    Returns:
        str: Contenido HTML formateado.
    """
    
    # --- Cálculo de totales y tasas de cambio ---
    total_gross_eur = 0
    total_tax_eur = 0
    total_net_eur = 0
    exchange_rates = {}  # Para almacenar las tasas de cambio únicas

    # Calcular totales en EUR y recopilar tasas de cambio
    for d in dividends:
        fx_rate = d.get('fxRateToBase', 1)
        total_gross_eur += abs(d['dividendo_bruto']) * fx_rate
        total_tax_eur += abs(d['tax']) * fx_rate
        total_net_eur += abs(d['netAmount']) * fx_rate
        
        # Guardar la tasa de cambio si no la tenemos ya
        currency = d.get('currency')
        if currency and currency not in exchange_rates:
            exchange_rates[currency] = fx_rate
            
    # Crear el string para el pie de página con todas las divisas
    rate_strings = [f"1 {cur} = €{rate:.4f}" for cur, rate in exchange_rates.items()]
    footer_rates_text = " • ".join(rate_strings) if rate_strings else "No se encontraron tipos de cambio."
    
    # --- Fin del cálculo ---

    # Crear filas de la tabla
    table_rows = ""
    for dividend in dividends:
        fx_rate = dividend.get('fxRateToBase', 1)
        gross_eur = abs(dividend['dividendo_bruto']) * fx_rate
        tax_eur = abs(dividend['tax']) * fx_rate
        net_eur = abs(dividend['netAmount']) * fx_rate
        
        # Determinar el símbolo de la divisa
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
                <h1 style="margin: 0; font-size: 28px; font-weight: 300;">💰 Resumen de Dividendos</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">{dates_display_str}</p>
            </div>
            
            <!-- Summary Cards (total consolidado en EUR) -->
            <div style="padding: 30px; background-color: #f8f9fc;">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;">
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #27ae60;">
                        <h3 style="margin: 0 0 10px 0; color: #2c3e50; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Dividendo Bruto</h3>
                        <p style="margin: 0; font-size: 24px; font-weight: 600; color: #27ae60;">€{total_gross_eur:.2f}</p>
                    </div>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #e74c3c;">
                        <h3 style="margin: 0 0 10px 0; color: #2c3e50; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Impuestos</h3>
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


# Ejemplo de uso para probar el script directamente
if __name__ == "__main__":
    # Configurar logging para ver la salida en consola
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # --- Datos de ejemplo con múltiples divisas y fechas ---
    # Descomenta y modifica según necesites probar
    
    # Caso 1: Una sola fecha
    # test_dividends = [
    #     {
    #         "ticker": "AAPL", "fecha": "2025-07-15", "dividendo_bruto": 50.00, "tax": -7.50,
    #         "netAmount": 42.50, "currency": "USD", "fxRateToBase": 0.9250, "description": "APPLE INC", "fee": 0
    #     }
    # ]
    # date_to_test = "2025-07-15"
    
    # Caso 2: Múltiples fechas (se listarán)
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
    
    # Caso 3: Muchas fechas (se mostrará un rango)
    # test_dividends = [
    #     {"ticker": "A", "fecha": "2025-07-15", "dividendo_bruto": 10, "tax": -1, "netAmount": 9, "currency": "USD", "fxRateToBase": 0.92, "description": "Agilent"},
    #     {"ticker": "B", "fecha": "2025-07-16", "dividendo_bruto": 10, "tax": -1, "netAmount": 9, "currency": "USD", "fxRateToBase": 0.92, "description": "Barnes Group"},
    #     {"ticker": "C", "fecha": "2025-07-17", "dividendo_bruto": 10, "tax": -1, "netAmount": 9, "currency": "USD", "fxRateToBase": 0.92, "description": "Citigroup"},
    #     {"ticker": "D", "fecha": "2025-07-18", "dividendo_bruto": 10, "tax": -1, "netAmount": 9, "currency": "USD", "fxRateToBase": 0.92, "description": "Dominion Energy"},
    # ]
    # date_to_test = "2025-07-18"

    
    # Asegúrate de tener un .env con las credenciales para probar el envío real
    # o la función se detendrá si no encuentra las variables.
    send_dividend_email(test_dividends, date_to_test)