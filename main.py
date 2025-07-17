import logging
from datetime import datetime
from ibkr_client import get_all_dividends
from email_sender import send_dividend_email
from logger import setup_logger
from dotenv import load_dotenv
import os

# Cargar .env desde el directorio donde está main.py
env_path = os.path.join(os.path.dirname(__file__), '.env')
# Añade override=True para asegurar que los valores del .env se usen siempre
load_dotenv(dotenv_path=env_path, override=True)

def main():
    setup_logger()
    logger = logging.getLogger(__name__)
    logger.info("Iniciando servicio de dividendos")

    try:
        today = datetime.now().strftime("%Y-%m-%d")  # Formato esperado por la función de email
        
        # Obtener todos los dividendos desde IBKR
        dividends = get_all_dividends()
        logger.info(f"Obtenidos {len(dividends)} dividendos desde IBKR")

        if dividends:
            send_dividend_email(dividends, today)
            logger.info("Correo de dividendos enviado correctamente")
        else:
            logger.info("No se encontraron dividendos en el XML. No se envía correo.")
            
    except Exception as e:
        logger.error(f"Error en el servicio de dividendos: {str(e)}")

if __name__ == "__main__":
    main()