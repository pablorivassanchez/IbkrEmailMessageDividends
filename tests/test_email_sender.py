# tests/test_email_sender.py

import pytest
from unittest.mock import Mock, patch
import os
from bs4 import BeautifulSoup

# Importar las funciones a testear desde el módulo de la aplicación
from email_sender import send_dividend_email, _create_html_content, _get_dates_string


class TestSendDividendEmail:
    """Tests para la función principal send_dividend_email."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        self.sample_dividends = [
            {
                "ticker": "AAPL", "fecha": "2025-07-15", "dividendo_bruto": 50.00, "tax": -7.50,
                "currency": "USD", "fxRateToBase": 0.92, "description": "APPLE INC", "netAmount": 42.50
            },
            {
                "ticker": "MSFT", "fecha": "2025-07-15", "dividendo_bruto": 30.00, "tax": -4.50,
                "currency": "USD", "fxRateToBase": 0.92, "description": "MICROSOFT CORP", "netAmount": 25.50
            }
        ]
        self.test_date = "2025-07-15"

    def test_send_dividend_email_empty_dividends(self):
        """Verifica que no se envíe correo si la lista de dividendos está vacía."""
        with patch('email_sender.logging.getLogger') as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            send_dividend_email([], self.test_date)

            mock_log.info.assert_called_with("No hay dividendos para enviar")

    @patch.dict(os.environ, {}, clear=True)
    def test_send_dividend_email_missing_config(self):
        """Verifica que se registre un error si faltan variables de entorno."""
        with patch('email_sender.logging.getLogger') as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            send_dividend_email(self.sample_dividends, self.test_date)

            expected_error_msg = "Configuración de correo incompleta. Verifica las variables de entorno SENDER_EMAIL, RECIPIENT_EMAIL, SMTP_USERNAME y SMTP_PASSWORD."
            mock_log.error.assert_called_with(expected_error_msg)

    @patch.dict(os.environ, {
        'SMTP_SERVER': 'smtp.test.com',
        'SMTP_PORT': '587',
        'SENDER_EMAIL': 'sender@test.com',
        'RECIPIENT_EMAIL': 'recipient@test.com',
        'SMTP_USERNAME': 'user_test',
        'SMTP_PASSWORD': 'password123'
    })
    @patch('email_sender.smtplib.SMTP')
    def test_send_dividend_email_success(self, mock_smtp):
        """Prueba un envío de correo exitoso de principio a fin."""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        with patch('email_sender.logging.getLogger') as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            send_dividend_email(self.sample_dividends, self.test_date)

            mock_smtp.assert_called_once_with('smtp.test.com', 587)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with('user_test', 'password123')
            mock_server.send_message.assert_called_once()

            sent_message = mock_server.send_message.call_args[0][0]
            expected_subject = "💰 Dividendos del 15 de Julio de 2025"
            assert sent_message['Subject'] == expected_subject

            mock_log.info.assert_any_call("Enviando correo a recipient@test.com")
            mock_log.info.assert_any_call("Correo enviado exitosamente")

    @patch.dict(os.environ, {
        'SMTP_SERVER': 'smtp.test.com',
        'SMTP_PORT': '587',
        'SENDER_EMAIL': 'sender@test.com',
        'RECIPIENT_EMAIL': 'recipient@test.com',
        'SMTP_USERNAME': 'user_test',
        'SMTP_PASSWORD': 'password123'
    })
    @patch('email_sender.smtplib.SMTP')
    def test_send_dividend_email_smtp_error(self, mock_smtp):
        """Prueba el manejo de errores si la conexión SMTP falla."""
        mock_smtp.side_effect = Exception("SMTP connection failed")

        with patch('email_sender.logging.getLogger') as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            send_dividend_email(self.sample_dividends, self.test_date)

            mock_log.error.assert_called_with("Error al enviar correo: SMTP connection failed")

    @patch.dict(os.environ, {
        'SENDER_EMAIL': 'sender@test.com',
        'RECIPIENT_EMAIL': 'recipient@test.com',
        'SMTP_USERNAME': 'user_test',
        'SMTP_PASSWORD': 'password123'
    })
    @patch('email_sender.smtplib.SMTP')
    def test_send_dividend_email_default_smtp_config(self, mock_smtp):
        """Prueba que se usen el servidor y puerto SMTP por defecto si no se especifican."""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        with patch('email_sender.logging.getLogger') as mock_logger:
            mock_logger.return_value = Mock()
            send_dividend_email(self.sample_dividends, self.test_date)
            mock_smtp.assert_called_once_with('smtp.gmail.com', 587)


class TestCreateHtmlContent:
    """Tests para la función _create_html_content que genera el cuerpo del correo."""
    
    def setup_method(self):
        """Configuración con datos de ejemplo para los tests de HTML."""
        self.sample_dividends = [
            {
                "ticker": "AAPL", "fecha": "2025-07-15", "dividendo_bruto": 50.00, "tax": -7.50,
                "netAmount": 42.50, "currency": "USD", "fxRateToBase": 0.92, "description": "APPLE INC"
            },
            {
                "ticker": "HSBC", "fecha": "2025-07-16", "dividendo_bruto": 40.00, "tax": -10.00,
                "netAmount": 30.00, "currency": "GBP", "fxRateToBase": 1.17, "description": "HSBC HOLDINGS PLC"
            }
        ]
        # CORRECCIÓN: Se define self.test_date para que esté disponible en la clase.
        self.test_date = "2025-07-16"
        self.dates_str = _get_dates_string(self.sample_dividends, self.test_date)

    def test_create_html_content_structure(self):
        """Verifica que la estructura básica del HTML (header, body, etc.) sea correcta."""
        result = _create_html_content(self.sample_dividends, self.dates_str)
        soup = BeautifulSoup(result, "html.parser")

        assert soup.find("html") is not None
        assert soup.find("head") is not None
        assert soup.find("body") is not None
        assert "💰 Resumen de Dividendos" in soup.find("h1").get_text()
        assert "15 de Julio de 2025, 16 de Julio de 2025" in soup.get_text()

    def test_create_html_content_calculations(self):
        """Verifica que los totales (bruto, neto, impuestos) en EUR se calculen y muestren correctamente."""
        result = _create_html_content(self.sample_dividends, self.dates_str)
        soup = BeautifulSoup(result, "html.parser")

        # Bruto: (50 * 0.92) + (40 * 1.17) = 46 + 46.8 = 92.80
        # Impuestos: (7.50 * 0.92) + (10.00 * 1.17) = 6.9 + 11.7 = 18.60
        # Neto: (42.50 * 0.92) + (30.00 * 1.17) = 39.1 + 35.1 = 74.20
        
        text = soup.get_text()
        assert "€92.80" in text
        assert "€18.60" in text
        assert "€74.20" in text
        assert "1 USD = €0.9200" in text
        assert "1 GBP = €1.1700" in text

    def test_create_html_content_table_rows(self):
        """Verifica que la tabla de detalles contenga las filas correctas para cada dividendo."""
        result = _create_html_content(self.sample_dividends, self.dates_str)
        soup = BeautifulSoup(result, "html.parser")
        
        table = soup.find("table")
        rows = table.find("tbody").find_all("tr")
        assert len(rows) == 2

        row1_text = rows[0].get_text()
        assert "AAPL" in row1_text
        assert "APPLE INC" in row1_text
        assert "$50.00" in row1_text
        assert "€46.00" in row1_text
        assert "$7.50" in row1_text
        assert "€6.90" in row1_text
        assert "$42.50" in row1_text
        assert "€39.10" in row1_text

        row2_text = rows[1].get_text()
        assert "HSBC" in row2_text
        assert "GBP40.00" in row2_text
        assert "€46.80" in row2_text

    def test_create_html_content_footer(self):
        """Verifica que el pie de página muestre el recuento correcto de dividendos."""
        one_dividend = [self.sample_dividends[0]]
        date_str = _get_dates_string(one_dividend, self.test_date)
        result = _create_html_content(one_dividend, date_str)
        text = BeautifulSoup(result, "html.parser").get_text()

        assert "1 dividendos recibidos" in text