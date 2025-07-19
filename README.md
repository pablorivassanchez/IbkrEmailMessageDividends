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

### Automatización con GitHub Actions

Para automatizar la ejecución del script diariamente usando GitHub Actions, sigue estos pasos:

#### 1. Estructura del Proyecto

Asegúrate de que tu repositorio tenga esta estructura:

```
tu-repositorio/
├── .github/
│   └── workflows/
│       └── dividendos.yml
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

#### 2. Crear el Workflow

Crea el archivo `.github/workflows/dividendos.yml` con el siguiente contenido:

```yaml
name: Dividendos IBKR Daily

on:
  schedule:
    # Ejecutar todos los días a las 08:00 UTC (09:00 CET/10:00 CEST)
    - cron: '0 8 * * *'
  workflow_dispatch:  # Permite ejecución manual

jobs:
  run-dividendos:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        
    - name: Run dividendos script
      env:
        IBKR_FLEX_TOKEN: ${{ secrets.IBKR_FLEX_TOKEN }}
        IBKR_DIVIDENDS_QUERY_ID: ${{ secrets.IBKR_DIVIDENDS_QUERY_ID }}
        SMTP_SERVER: ${{ secrets.SMTP_SERVER }}
        SMTP_PORT: ${{ secrets.SMTP_PORT }}
        SENDER_EMAIL: ${{ secrets.SENDER_EMAIL }}
        SMTP_USERNAME: ${{ secrets.SMTP_USERNAME }}
        SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
        RECIPIENT_EMAIL: ${{ secrets.RECIPIENT_EMAIL }}
      run: |
        python main.py
        
    - name: Upload logs
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: dividendos-logs
        path: |
          logs/*.log
          *.log
        retention-days: 7
```

#### 3. Configurar Secrets

Para mantener tus credenciales seguras, debes configurar GitHub Secrets:

1. Ve a tu repositorio en GitHub
2. Navega a **Settings** → **Secrets and variables** → **Actions**
3. Haz clic en **"New repository secret"** y añade los siguientes secrets:

| Secret Name | Descripción |
|-------------|-------------|
| `IBKR_FLEX_TOKEN` | Tu token del Flex Web Service de IBKR |
| `IBKR_DIVIDENDS_QUERY_ID` | El ID de tu Flex Query para dividendos |
| `SMTP_SERVER` | Servidor SMTP (ej: smtp.gmail.com) |
| `SMTP_PORT` | Puerto SMTP (ej: 587) |
| `SENDER_EMAIL` | Email desde el que se enviarán los correos |
| `SMTP_USERNAME` | Usuario para autenticación SMTP |
| `SMTP_PASSWORD` | Contraseña de email o contraseña de aplicación |
| `RECIPIENT_EMAIL` | Email que recibirá el informe |

#### 4. Personalizar el Horario

El workflow está configurado para ejecutarse diariamente a las 08:00 UTC. Para cambiar el horario, modifica la línea del cron:

```yaml
# Formato: 'minuto hora día mes día_semana'
# Ejemplos:
- cron: '0 8 * * *'     # Diario a las 08:00 UTC
- cron: '30 7 * * 1-5'  # Días laborables a las 07:30 UTC
- cron: '0 9 * * 1'     # Solo los lunes a las 09:00 UTC
```

**Conversión de horarios:**
- Para España: UTC+1 (invierno) / UTC+2 (verano)
- Si quieres ejecución a las 09:00 española, usa `'0 8 * * *'` (invierno) o `'0 7 * * *'` (verano)

#### 5. Ventajas de GitHub Actions

✅ **Gratuito**: 2,000 minutos/mes para repositorios públicos
✅ **Sin restricciones de red**: Acceso completo a internet (sin problemas con IBKR)
✅ **Ejecución confiable**: Infraestructura robusta de GitHub
✅ **Logs detallados**: Historial completo de ejecuciones
✅ **Ejecución manual**: Botón para ejecutar cuando necesites
✅ **Notificaciones**: Emails automáticos si falla la ejecución

#### 6. Probar el Workflow

Una vez configurado:

1. Haz push de los cambios a tu repositorio
2. Ve a la pestaña **Actions** en GitHub
3. Selecciona tu workflow "Dividendos IBKR Daily"
4. Haz clic en **"Run workflow"** para probarlo manualmente
5. Revisa los logs para verificar que funciona correctamente

#### 7. Monitoreo y Logs

- Los logs se guardan automáticamente como artifacts en GitHub
- Se conservan durante 7 días
- Puedes descargarlos desde la pestaña Actions → tu ejecución → Artifacts
- GitHub te notificará por email si el workflow falla

#### 8. Consideraciones Importantes

⚠️ **Repositorios inactivos**: GitHub puede pausar workflows en repos sin actividad durante 60 días
⚠️ **Límites de tiempo**: Cada job tiene un límite de 6 horas
⚠️ **Retrasos**: Los workflows programados pueden tener hasta 15 minutos de retraso en horarios pico

#### Migración desde Cron Job Local

Si actualmente usas un cron job local, GitHub Actions ofrece:
- Mayor confiabilidad (no depende de que tu máquina esté encendida)
- Mejor mantenimiento (historial de ejecuciones)
- Notificaciones automáticas de errores
- Acceso desde cualquier lugar
