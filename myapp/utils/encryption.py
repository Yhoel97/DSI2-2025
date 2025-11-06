"""
Utilidad para encriptar y desencriptar datos sensibles
Utiliza Fernet (criptografía simétrica) de la librería cryptography
"""

from cryptography.fernet import Fernet
from django.conf import settings
import base64
import hashlib
import json


def get_encryption_key():
    """
    Obtiene la clave de encriptación desde settings.
    Si no existe, genera una basada en SECRET_KEY (solo para desarrollo/simulación).
    En producción real, usar variable de entorno independiente.
    """
    # Usar SECRET_KEY de Django como base para generar clave Fernet
    # IMPORTANTE: En producción real, usar una clave independiente en variable de entorno
    secret = settings.SECRET_KEY.encode()
    
    # Generar clave Fernet válida (32 bytes en base64)
    key_bytes = hashlib.sha256(secret).digest()
    key = base64.urlsafe_b64encode(key_bytes)
    
    return key


def encrypt_data(data: str) -> str:
    """
    Encripta una cadena de texto.
    
    Args:
        data (str): Texto plano a encriptar
        
    Returns:
        str: Texto encriptado en formato base64
    """
    if not data:
        return ""
    
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        
        # Encriptar y convertir a string
        encrypted_bytes = fernet.encrypt(data.encode())
        encrypted_string = encrypted_bytes.decode()
        
        return encrypted_string
    except Exception as e:
        # En caso de error, loguear y retornar vacío
        print(f"Error al encriptar datos: {str(e)}")
        return ""


def decrypt_data(encrypted_data: str) -> str:
    """
    Desencripta una cadena de texto encriptada.
    
    Args:
        encrypted_data (str): Texto encriptado en formato base64
        
    Returns:
        str: Texto plano desencriptado
    """
    if not encrypted_data:
        return ""
    
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        
        # Desencriptar
        decrypted_bytes = fernet.decrypt(encrypted_data.encode())
        decrypted_string = decrypted_bytes.decode()
        
        return decrypted_string
    except Exception as e:
        # En caso de error, loguear y retornar vacío
        print(f"Error al desencriptar datos: {str(e)}")
        return ""


def encrypt_card_data(numero_tarjeta: str, cvv: str = None) -> dict:
    """
    Encripta datos de tarjeta y retorna información procesada.
    
    Args:
        numero_tarjeta (str): Número completo de la tarjeta
        cvv (str): CVV de la tarjeta (opcional, normalmente NO se guarda)
        
    Returns:
        dict: Diccionario con datos procesados {
            'ultimos_4': str,
            'datos_encriptados': str (solo si se necesita guardar algo adicional)
        }
    """
    # Limpiar número de tarjeta (quitar espacios y guiones)
    numero_limpio = ''.join(filter(str.isdigit, numero_tarjeta))
    
    # Extraer últimos 4 dígitos (estos se guardan en texto plano)
    ultimos_4 = numero_limpio[-4:] if len(numero_limpio) >= 4 else numero_limpio
    
    # IMPORTANTE: Por seguridad y cumplimiento PCI DSS, NO guardamos:
    # - El número completo de tarjeta
    # - El CVV (nunca debe almacenarse)
    
    # Si en el futuro se necesita guardar algún dato adicional encriptado:
    # datos_encriptados = encrypt_data(f"algun_dato_adicional")
    
    return {
        'ultimos_4': ultimos_4,
        'datos_encriptados': None  # Por ahora, no guardamos datos encriptados adicionales
    }


def get_card_type(numero_tarjeta: str) -> str:
    """
    Detecta el tipo de tarjeta basado en el número.
    
    Args:
        numero_tarjeta (str): Número de la tarjeta
        
    Returns:
        str: Tipo de tarjeta ('VISA', 'MASTERCARD', 'AMEX', 'OTRO')
    """
    # Limpiar número
    numero = ''.join(filter(str.isdigit, numero_tarjeta))
    
    if not numero:
        return 'OTRO'
    
    # Detectar por prefijos
    if numero.startswith('4'):
        return 'VISA'
    elif numero.startswith(('51', '52', '53', '54', '55', '22', '27')):
        return 'MASTERCARD'
    elif numero.startswith(('34', '37')):
        return 'AMEX'
    elif numero.startswith('6011') or numero.startswith('65'):
        return 'DISCOVER'
    else:
        return 'OTRO'


def encrypt_card_data_full(numero_tarjeta: str, nombre_titular: str, fecha_expiracion: str) -> str:
    """
    Encripta todos los datos sensibles de una tarjeta.
    
    Args:
        numero_tarjeta (str): Número completo de la tarjeta
        nombre_titular (str): Nombre del titular
        fecha_expiracion (str): Fecha de expiración (MM/YY)
        
    Returns:
        str: Datos encriptados en formato JSON encriptado
    """
    datos = {
        'numero_tarjeta': numero_tarjeta,
        'nombre_titular': nombre_titular,
        'fecha_expiracion': fecha_expiracion
    }
    
    # Convertir a JSON y encriptar
    json_datos = json.dumps(datos)
    return encrypt_data(json_datos)


def decrypt_card_data(encrypted_json: str) -> dict:
    """
    Desencripta los datos completos de una tarjeta guardada.
    
    Args:
        encrypted_json (str): JSON encriptado con los datos de la tarjeta
        
    Returns:
        dict: Diccionario con los datos desencriptados {
            'numero_tarjeta': str,
            'nombre_titular': str,
            'fecha_expiracion': str
        }
    """
    if not encrypted_json:
        return {}
    
    try:
        # Desencriptar el JSON
        json_datos = decrypt_data(encrypted_json)
        
        # Convertir JSON a diccionario
        datos = json.loads(json_datos)
        return datos
    except Exception as e:
        print(f"Error al desencriptar datos de tarjeta: {str(e)}")
        return {}
