"""
Simulador de procesamiento de pagos
PBI-30: Sistema de Pago para Boletos

Este módulo simula el procesamiento de pagos con tarjetas de crédito/débito.
NO procesa pagos reales. Es solo para propósitos de demostración.
"""

import time
import random
import string
import logging
from datetime import datetime
from decimal import Decimal
from django.conf import settings

logger = logging.getLogger(__name__)


def generar_numero_transaccion():
    """
    Genera un número único de transacción
    Formato: TXN-YYYYMMDDHHMMSS-XXXXXX (aleatorio)
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"TXN-{timestamp}-{random_str}"


def validar_numero_tarjeta(numero):
    """
    Valida formato básico de número de tarjeta
    Elimina espacios y guiones, verifica que solo sean dígitos
    """
    numero_limpio = numero.replace(' ', '').replace('-', '')
    if not numero_limpio.isdigit():
        return False, "El número de tarjeta debe contener solo dígitos"
    
    if len(numero_limpio) not in [15, 16]:
        return False, "El número de tarjeta debe tener 15 o 16 dígitos"
    
    return True, numero_limpio


def validar_fecha_expiracion(mes, anio):
    """
    Valida que la tarjeta no esté vencida
    mes: int (1-12)
    anio: int (YY o YYYY)
    """
    try:
        mes = int(mes)
        anio = int(anio)
        
        # Convertir año de 2 dígitos a 4
        if anio < 100:
            anio += 2000
        
        if mes < 1 or mes > 12:
            return False, "El mes debe estar entre 01 y 12"
        
        # Comparar con fecha actual
        ahora = datetime.now()
        if anio < ahora.year:
            return False, "La tarjeta está vencida"
        elif anio == ahora.year and mes < ahora.month:
            return False, "La tarjeta está vencida"
        
        return True, None
    except ValueError:
        return False, "Formato de fecha inválido"


def validar_cvv(cvv, numero_tarjeta):
    """
    Valida el CVV según el tipo de tarjeta
    Amex: 4 dígitos, otras: 3 dígitos
    """
    cvv_str = str(cvv)
    if not cvv_str.isdigit():
        return False, "El CVV debe contener solo dígitos"
    
    # American Express comienza con 34 o 37 y tiene CVV de 4 dígitos
    es_amex = numero_tarjeta.startswith(('34', '37'))
    longitud_esperada = 4 if es_amex else 3
    
    if len(cvv_str) != longitud_esperada:
        return False, f"El CVV debe tener {longitud_esperada} dígitos"
    
    return True, None


def simular_pago(datos_tarjeta, monto):
    """
    Simula el procesamiento de un pago con tarjeta
    
    Args:
        datos_tarjeta (dict): {
            'numero': str,
            'mes_expiracion': int,
            'anio_expiracion': int,
            'cvv': str,
            'nombre_titular': str
        }
        monto (Decimal): Monto a cobrar
    
    Returns:
        dict: {
            'success': bool,
            'transaction_id': str or None,
            'error_code': str or None,
            'error_message': str or None,
            'timestamp': datetime,
            'amount': Decimal
        }
    """
    
    # Validar monto
    if monto <= 0:
        return {
            'exitoso': False,
            'numero_transaccion': None,
            'numero_tarjeta_enmascarado': '',
            'tipo_tarjeta': '',
            'error_code': 'INVALID_AMOUNT',
            'error_message': 'El monto debe ser mayor a cero',
            'timestamp': datetime.now(),
            'amount': monto
        }
    
    # Validar número de tarjeta
    valido, resultado = validar_numero_tarjeta(datos_tarjeta['numero'])
    if not valido:
        return {
            'exitoso': False,
            'numero_transaccion': None,
            'numero_tarjeta_enmascarado': '',
            'tipo_tarjeta': '',
            'error_code': 'INVALID_CARD_NUMBER',
            'error_message': resultado,
            'timestamp': datetime.now(),
            'amount': monto
        }
    
    numero_limpio = resultado
    
    # Validar fecha de expiración
    valido, error = validar_fecha_expiracion(
        datos_tarjeta['mes_expiracion'],
        datos_tarjeta['anio_expiracion']
    )
    if not valido:
        return {
            'exitoso': False,
            'numero_transaccion': None,
            'numero_tarjeta_enmascarado': '',
            'tipo_tarjeta': '',
            'error_code': 'EXPIRED_CARD',
            'error_message': error,
            'timestamp': datetime.now(),
            'amount': monto
        }
    
    # Validar CVV
    valido, error = validar_cvv(datos_tarjeta['cvv'], numero_limpio)
    if not valido:
        return {
            'exitoso': False,
            'numero_transaccion': None,
            'numero_tarjeta_enmascarado': '',
            'tipo_tarjeta': '',
            'error_code': 'INVALID_CVV',
            'error_message': error,
            'timestamp': datetime.now(),
            'amount': monto
        }
    
    # Simular delay de procesamiento (2-4 segundos)
    tiempo_procesamiento = random.uniform(2, 4)
    logger.info(f"Simulando procesamiento de pago por ${monto}...")
    time.sleep(tiempo_procesamiento)
    
    # Obtener tasa de éxito configurada (default 90%)
    tasa_exito = getattr(settings, 'PAYMENT_SUCCESS_RATE', 0.9)
    
    # Decidir si el pago es exitoso o falla (aleatorio)
    es_exitoso = random.random() < tasa_exito
    
    # Obtener tipo de tarjeta y enmascarar número
    tipo_tarjeta = obtener_tipo_tarjeta(numero_limpio)
    numero_enmascarado = enmascarar_numero_tarjeta(numero_limpio)
    
    if es_exitoso:
        # Pago exitoso
        numero_transaccion = generar_numero_transaccion()
        logger.info(f"✅ Pago exitoso - Transacción: {numero_transaccion}")
        
        return {
            'exitoso': True,
            'numero_transaccion': numero_transaccion,
            'numero_tarjeta_enmascarado': numero_enmascarado,
            'tipo_tarjeta': tipo_tarjeta,
            'error_code': None,
            'error_message': None,
            'timestamp': datetime.now(),
            'amount': monto
        }
    else:
        # Pago rechazado - elegir error aleatorio
        errores_posibles = [
            ('INSUFFICIENT_FUNDS', 'Fondos insuficientes en la tarjeta'),
            ('CARD_DECLINED', 'Tarjeta rechazada por el banco emisor'),
            ('NETWORK_ERROR', 'Error de conexión temporal. Por favor intente nuevamente'),
            ('FRAUD_SUSPECTED', 'Transacción bloqueada por sospecha de fraude'),
            ('INVALID_CVV', 'CVV incorrecto'),
        ]
        
        error_code, error_message = random.choice(errores_posibles)
        logger.warning(f"❌ Pago rechazado - Motivo: {error_message}")
        
        return {
            'exitoso': False,
            'numero_transaccion': None,
            'numero_tarjeta_enmascarado': numero_enmascarado,
            'tipo_tarjeta': tipo_tarjeta,
            'error_code': error_code,
            'error_message': error_message,
            'timestamp': datetime.now(),
            'amount': monto
        }


def obtener_tipo_tarjeta(numero):
    """
    Detecta el tipo de tarjeta según los primeros dígitos
    
    Returns:
        str: 'VISA', 'MASTERCARD', 'AMEX', 'DISCOVER', 'UNKNOWN'
    """
    numero_limpio = numero.replace(' ', '').replace('-', '')
    
    if numero_limpio.startswith('4'):
        return 'VISA'
    elif numero_limpio.startswith(('51', '52', '53', '54', '55')):
        return 'MASTERCARD'
    elif numero_limpio.startswith(('34', '37')):
        return 'AMEX'
    elif numero_limpio.startswith('6011'):
        return 'DISCOVER'
    else:
        return 'UNKNOWN'


def enmascarar_numero_tarjeta(numero):
    """
    Enmascara el número de tarjeta mostrando solo los últimos 4 dígitos
    
    Args:
        numero (str): Número completo de tarjeta
    
    Returns:
        str: Número enmascarado (ej: "**** **** **** 1234")
    """
    numero_limpio = numero.replace(' ', '').replace('-', '')
    ultimos_4 = numero_limpio[-4:]
    return f"**** **** **** {ultimos_4}"
