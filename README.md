# IBKR Dividend Email Notifier

Este servicio automatizado se conecta a la API Flex Web Service de Interactive Brokers (IBKR) para obtener un informe de los dividendos recibidos, genera un resumen detallado en formato HTML y lo envía por correo electrónico.

## Características

- **Conexión con IBKR**: Utiliza el Flex Web Service de IBKR para obtener datos de dividendos de forma segura.
- **Análisis Completo**: Extrae información tanto de `ChangeInDividendAccrual` (dividendos devengados) como de `CashTransaction` (dividendos pagados en efectivo).
- **Informe HTML Profesional**: Genera un correo electrónico visualmente atractivo y fácil de leer con:
  - Un resumen de los totales (bruto, impuestos, neto) consolidados en EUR.
  - Una tabla detallada con cada dividendo, mostrando los importes tanto en su divisa original como en EUR.
  - Manejo de múltiples divisas y visualización de los tipos de cambio utilizados.
- **Alta Configuración**: Toda la configuración (credenciales de API, SMTP) se gestiona a través de un archivo `.env` para mayor seguridad y facilidad de mantenimiento.
- **Logging Integrado**: Registra la actividad del servicio en la consola y en un archivo (`logs/dividend_service.log`) para facilitar la depuración.
- **Probado con Pytest**: Incluye una suite de tests para asegurar la fiabilidad del código.

## Vista Previa del Email

El correo generado tiene un diseño limpio y moderno. Incluye:

1.  **Cabecera**: Con el título "Resumen de Dividendos" y el rango de fechas correspondiente.
2.  **Tarjetas de Resumen**: Muestran el total de dividendo bruto, impuestos y dividendo neto, todo consolidado en Euros.
3.  **Tabla Detallada**: Una tabla con cada dividendo recibido, especificando el Ticker, la Empresa, y los desgloses de Bruto, Impuestos y Neto tanto en la moneda original (USD, GBP, etc.) como su equivalente en EUR.
4.  **Pie de Página**: Indica el número total de dividendos procesados y los tipos de cambio aplicados en el informe.

## Instalación

1.  **Clona el repositorio:**

    ```bash
    git clone https://github.com/tu-usuario/IbkrTelegramMessageDividendos.git
    cd IbkrTelegramMessageDividendos
    ```

2.  **Crea y activa un entorno virtual (recomendado):**

    ```bash
    python -m venv venv
    ```

    - **En Windows:**
      ```bash
      venv\Scripts\activate
      ```
    - **En macOS/Linux:**
      ```bash
      source venv/bin/activate
      ```

3.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuración

Para que el servicio funcione, es crucial configurar correctamente las variables de entorno.

1.  **Crea un archivo `.env`** en la raíz del proyecto.

2.  **Añade y configura las siguientes variables en tu archivo `.env`:**

    ```env
    #--- Credenciales de Interactive Brokers ---#
    # Tu token del Flex Web Service de IBKR
    IBKR_FLEX_TOKEN="TU_TOKEN_AQUI"
    # El ID de tu Flex Query para dividendos
    IBKR_DIVIDENDS_QUERY_ID="TU_ID_DE_QUERY_AQUI"

    #--- Configuración de Email (SMTP) ---#
    # Servidor SMTP de tu proveedor de correo (ej. smtp.gmail.com)
    SMTP_SERVER="smtp.gmail.com"
    # Puerto SMTP (587 para TLS es lo más común)
    SMTP_PORT="587"
    # Email desde el que se enviarán los correos
    SENDER_EMAIL="tu_email@gmail.com"
    # Usuario para la autenticación SMTP (suele ser el mismo email)
    SMTP_USERNAME="tu_email@gmail.com"
    # Contraseña de tu email o, preferiblemente, una contraseña de aplicación
    SMTP_PASSWORD="TU_CONTRASENA_DE_APLICACION"
    # Email que recibirá el informe
    RECIPIENT_EMAIL="email_destinatario@dominio.com"
    ```

### ¿Cómo obtener las credenciales de IBKR?

1.  **`IBKR_FLEX_TOKEN`**:

    - Inicia sesión en **Gestión de Cuenta** (Account Management) en la web de Interactive Brokers.
    - Ve a **Configuración > Informes de Cuenta > Servicio Web Flex** (Settings > Account Reporting > Flex Web Service).
    - Activa el servicio y genera un nuevo token. Copia el token de 256 caracteres.

2.  **`IBKR_DIVIDENDS_QUERY_ID`**:
    - En la misma sección de **Informes de Cuenta**, ve a **Consultas Flex** (Flex Queries).
    - Crea una nueva **Consulta Flex de Actividad** (Activity Flex Query).
    - En la sección **"Cambios en los Dividendos Devengados"** (`Change in Dividend Accruals`), selecciona los campos: `date`, `symbol`, `description`, `grossAmount`, `tax`, `netAmount`, `currency`, `fxRateToBase`.
    - En la sección **"Transacciones en Efectivo"** (`Cash Transactions`), selecciona los campos: `dateTime`, `symbol`, `description`, `amount`, `currency`, `fxRateToBase`, `activityDescription`.
    - Guarda la consulta y copia el número de ID que se le asigna.

> **¡Importante!** Si usas Gmail, se recomienda encarecidamente generar una **"Contraseña de Aplicación"** en la configuración de seguridad de tu cuenta de Google y usarla como `SMTP_PASSWORD` en lugar de tu contraseña principal.

## Uso

Para ejecutar el servicio manualmente, simplemente corre el script principal:

```bash
python main.py
```

Esto ejecutará el proceso completo: obtendrá los datos de dividendos de IBKR, generará el informe y enviará el correo electrónico.

### Automatización (Cron Job)

Para que el script se ejecute automáticamente todos los días, puedes configurarlo como un `cron job` en Linux/macOS.

1.  Abre el editor de crontab:
    ```bash
    crontab -e
    ```
2.  Añade una línea para ejecutar el script a una hora determinada (por ejemplo, a las 8 AM todos los días), asegurándote de usar rutas absolutas:
    ```cron
    # m h  dom mon dow   command
    0 8 * * * /ruta/absoluta/a/tu/venv/bin/python /ruta/absoluta/a/tu/proyecto/main.py >> /ruta/absoluta/a/tu/proyecto/logs/cron.log 2>&1
    ```
    Esto ejecuta el script y redirige cualquier salida o error a un archivo de log específico para el cron job.

## Ejecución de Tests

El proyecto incluye tests para validar la lógica del cliente de IBKR y del generador de correos. Para ejecutarlos:

```bash
pytest -v
```
