# Plan de Implementación: PBI-27 y PBI-30

## Análisis del Sistema Actual

### Estado Actual del Flujo de Reservas

**Pantalla `asientos.html`:**
- Permite seleccionar función, asientos, aplicar cupón
- Recopila datos del cliente (nombre, apellido, email)
- Muestra resumen con subtotal, descuento y total
- Al confirmar, genera reserva y envía PDF por correo

**Backend `views.py` - función `asientos()`:**
- Calcula precios según formato de sala (2D, 3D, IMAX)
- Aplica descuentos de cupones
- Crea registro en modelo `Reserva`
- Genera PDF del ticket
- Envía email con confirmación
- NO procesa pago real (solo reserva)

**Modelo `Reserva`:**
- Campos: pelicula, cliente, email, formato, sala, horario, asientos, cantidad_boletos, precio_total, estado, fecha_reserva, codigo_reserva, usado
- Estado por defecto: 'RESERVADO'
- No tiene campos relacionados con pago

### Limitaciones Identificadas
1. No existe proceso de pago
2. No hay modelo para métodos de pago
3. No hay validación de pago completado
4. Estado 'RESERVADO' no indica si fue pagado
5. No hay almacenamiento de información de tarjetas/cuentas digitales

---

## PBI-30: Sistema de Pago para Boletos

### Objetivo
Implementar un flujo de pago completo donde el usuario pueda pagar su boleto y confirmar la reserva.

### 1. Modificaciones al Modelo de Datos

#### 1.1 Crear nuevo modelo `Pago`
- Campo: reserva (ForeignKey a Reserva)
- Campo: monto (DecimalField)
- Campo: metodo_pago (CharField con choices: 'TARJETA', 'CUENTA_DIGITAL')
- Campo: estado_pago (CharField con choices: 'PENDIENTE', 'APROBADO', 'RECHAZADO', 'REEMBOLSADO')
- Campo: fecha_pago (DateTimeField)
- Campo: numero_transaccion (CharField, unique)
- Campo: detalles_pago (JSONField para guardar info adicional)
- Campo: metodo_pago_guardado (ForeignKey opcional a MetodoPago)

#### 1.2 Modificar modelo `Reserva`
- Agregar campo: pago_completado (BooleanField, default=False)
- Agregar campo: fecha_pago (DateTimeField, null=True, blank=True)
- Modificar lógica del campo `estado`: distinguir entre 'RESERVADO' (sin pagar) y 'CONFIRMADO' (pagado)

#### 1.3 Crear migraciones
- Ejecutar `python manage.py makemigrations`
- Ejecutar `python manage.py migrate`

### 2. Modificar Pantalla Existente de Asientos

#### 2.1 Modificar template `asientos.html`
- Agregar nueva sección después del resumen de orden: "Método de Pago"
- Si usuario autenticado y tiene métodos guardados:
  - Subsección: "Métodos de pago guardados"
  - Mostrar cards o lista de métodos guardados (radio buttons)
  - Cada método muestra: tipo, últimos 4 dígitos/email, alias
  - Campo CVV adicional (solo visible al seleccionar método con tarjeta)
  - Link: "Administrar métodos de pago" (abre en nueva pestaña o modal)
- Subsección: "Pagar con nueva tarjeta"
  - Radio button: "Usar nueva tarjeta"
  - Formulario con campos:
    - Número de tarjeta (input con formato automático)
    - Fecha de expiración (MM/YY)
    - CVV (3-4 dígitos)
    - Nombre del titular
  - Si usuario autenticado:
    - Checkbox: "Guardar esta tarjeta para futuras compras"
    - Input opcional: "Alias para esta tarjeta" (ej: "Visa Personal")
- Si usuario NO autenticado:
  - Solo mostrar formulario de nueva tarjeta
  - Mensaje informativo: "Inicia sesión para guardar tus métodos de pago"
- Botón "Confirmar Reserva y Pagar" (reemplaza el actual "Confirmar Reserva")
- Indicador de carga durante procesamiento del pago

#### 2.2 Modificar CSS `asientos.css`
#### 3.1 Modificar vista `asientos(request, pelicula_id)` - INTEGRACIÓN DE PAGO
- Mantener toda la lógica actual de selección de asientos y cálculo de precios
- Al confirmar reserva (botón "Confirmar Reserva y Pagar"):
  - Validar que se seleccionó un método de pago
  - **Caso 1: Usuario autenticado y seleccionó método guardado**
    - Obtener método guardado de la BD: `MetodoPago.objects.get(id=metodo_id, usuario=request.user)`
    - Validar CVV ingresado (si es tarjeta)
    - Desencriptar datos del método
    - Procesar pago con datos guardados
  - **Caso 2: Usuario usa nueva tarjeta**
    - Validar campos de tarjeta (número, fecha exp, CVV, titular)
    - Procesar pago con datos nuevos
    - Si checkbox "guardar tarjeta" está marcado Y usuario autenticado:
      - Crear registro en MetodoPago con datos encriptados
      - Guardar solo últimos 4 dígitos visibles
      - Usar alias proporcionado o generar automático
  - **Caso 3: Usuario no autenticado**
    - Procesar pago con datos de tarjeta ingresados
    - No guardar método (no hay usuario)
  - Crear registro en modelo `Pago` con estado 'PENDIENTE'
  - Llamar función de procesamiento de pago (simulación o pasarela real)
  - **Si pago exitoso:**
    - Actualizar Pago: estado='APROBADO', numero_transaccion=generado
    - Crear Reserva: estado='CONFIRMADO', pago_completado=True, fecha_pago=ahora
    - Registrar en modelo Venta
    - Generar PDF del ticket con marca "PAGADO"
    - Enviar email con ticket adjunto
    - Mostrar mensaje de éxito con código de reserva
    - Opción: ofrecer descarga inmediata del PDF
#### 3.2 Crear función auxiliar `procesar_pago_tarjeta(datos_tarjeta, monto)`
- Función que procesa el pago mediante **SIMULACIÓN**
- Parámetros: diccionario con datos de tarjeta, monto a cobrar
- Validaciones internas de la función:
  - Verificar que el monto es mayor a 0
  - Validar formato de número de tarjeta (algoritmo de Luhn opcional)
  - Validar que la fecha de expiración no ha pasado
  - Validar longitud de CVV (3 o 4 dígitos según tipo de tarjeta)
- **Lógica de simulación:**
  - Generar número de transacción aleatorio: 8-12 caracteres alfanuméricos (formato: TXN-XXXXXXXX)
  - Simular delay de procesamiento: sleep(2-3 segundos) para dar sensación de procesamiento real
  - Retornar éxito en 90% de casos, fallo en 10% (aleatorio para testing de manejo de errores)
  - Mensajes de error simulados:
    - "Fondos insuficientes"
    - "Tarjeta rechazada por el banco"
    - "Error de conexión con el procesador"
    - "Tarjeta expirada"
  - Registrar en logs: fecha, monto, resultado (éxito/fallo), número de transacción
- Retornar: diccionario con {success: bool, transaction_id: str, error_message: str, timestamp: datetime} "Confirmar Reserva"):
  - Crear registro en Reserva con estado='RESERVADO' y pago_completado=False
  - NO generar PDF ni enviar email todavía
  - NO registrar en Venta aún
  - Redirigir a vista de pago: `redirect('procesar_pago', reserva_id=reserva.id)`
- Eliminar lógica de generación de PDF y envío de email de esta vista

#### 3.3 Crear vista `pago_exitoso(request, reserva_id)`
- Mostrar pantalla de confirmación
- Mostrar resumen de la compra
- Mostrar código de reserva y número de transacción
- Botón para descargar ticket PDF
- Botón para enviar ticket por email nuevamente
- Botón para volver al inicio

#### 3.4 Crear vista `pago_fallido(request, reserva_id)`
- Mostrar mensaje de error
- Explicar razón del rechazo
- Botón para reintentar pago
- Botón para cancelar reserva

### 4. Formularios

#### 4.1 Crear `PagoForm` en `forms.py`
- Campo: metodo_pago (ChoiceField: 'TARJETA', 'CUENTA_DIGITAL')
- Campo: usar_metodo_guardado (BooleanField, required=False)
- Campo: metodo_guardado_id (IntegerField, required=False)
- Campo: guardar_metodo (BooleanField, required=False)
- Campos para tarjeta: numero_tarjeta, fecha_expiracion, cvv, nombre_titular
- Campos para cuenta digital: tipo_cuenta, email_cuenta
- Método clean() para validar según método seleccionado
- Método clean_numero_tarjeta() para validar formato (algoritmo de Luhn opcional)
- Método clean_cvv() para validar 3-4 dígitos
- Método clean_fecha_expiracion() para validar formato MM/YY y que no esté vencida

### 5. Sistema de Simulación de Pago

#### 5.1 Implementar función `simular_pago()`
- Ubicación: crear archivo `utils/payment_simulator.py`
- Función principal que simula el procesamiento de pago
- Validaciones previas:
  - Verificar que monto > 0
  - Verificar que datos de tarjeta estén completos
  - Validar formato básico de número de tarjeta
  - Validar fecha de expiración no vencida
- **Lógica de simulación:**
  - Generar ID de transacción único: formato `TXN-{timestamp}-{random_string}`
  - Simular tiempo de procesamiento: `time.sleep(random.uniform(2, 4))` segundos
  - Probabilidad de éxito/fallo configurable:
    - 90% éxito
    - 10% fallo aleatorio
  - Tipos de error simulados (aleatorio):
    - "INSUFFICIENT_FUNDS" → "Fondos insuficientes"
    - "CARD_DECLINED" → "Tarjeta rechazada por el banco"
    - "NETWORK_ERROR" → "Error de conexión temporal"
    - "EXPIRED_CARD" → "Tarjeta expirada"
    - "INVALID_CVV" → "CVV incorrecto"
- Logging de transacciones:
  - Registrar todas las transacciones (éxito y fallo) en log
  - Datos a registrar: timestamp, monto, resultado, transaction_id, últimos 4 dígitos
- Retornar diccionario estandarizado:
  ```python
  {
      'success': bool,
      'transaction_id': str,
      'error_code': str or None,
      'error_message': str or None,
      'timestamp': datetime,
      'amount': Decimal
  }
  ```

#### 5.2 Configuración en settings.py
- Agregar constante: `PAYMENT_MODE = 'SIMULATION'`
- Agregar configuración: `PAYMENT_SUCCESS_RATE = 0.9` (90% de éxito)
- Comentar que en futuro se puede cambiar a `PAYMENT_MODE = 'STRIPE'` o similar
- Mantener la arquitectura preparada para futura integración real

### 7. JavaScript para Interactividad en Asientos

#### 7.1 Crear o modificar `asientos.js`
- Función para validar número de tarjeta en tiempo real
  - Aplicar formato automático (espacios cada 4 dígitos)
  - Detectar tipo de tarjeta (Visa, Mastercard, Amex) por prefijo
  - Mostrar icono correspondiente
  - Validar longitud según tipo (16 o 15 dígitos)
- Función para validar fecha de expiración
  - Formato automático MM/YY
  - Validar que no esté vencida
  - Validar formato correcto (mes 01-12)
- Función para validar CVV
  - Solo números
  - Longitud según tipo de tarjeta (3 o 4 dígitos)
- Mostrar/ocultar sección de "guardar tarjeta"
  - Solo visible si usuario está autenticado
  - Toggle de checkbox
- Mostrar/ocultar campo CVV adicional
  - Si selecciona método guardado con tarjeta: mostrar campo CVV
  - Si selecciona método de cuenta digital: ocultar CVV
- Función para alternar entre "método guardado" y "nueva tarjeta"
  - Al seleccionar método guardado: deshabilitar campos de nueva tarjeta
  - Al seleccionar nueva tarjeta: habilitar campos y limpiar selección de guardados
- Indicador de procesamiento de pago
  - Mostrar spinner y mensaje "Procesando pago..."
  - Deshabilitar botón de confirmar durante procesamiento
  - Prevenir múltiples envíos del formulario
- Validación completa antes de enviar formulario
  - Verificar que todos los campos requeridos estén llenos
  - Mostrar mensajes de error específicos por campo
- Token CSRF en formularios
- Rate limiting para prevenir ataques de fuerza bruta

#### 6.2 Encriptación (si se guardan datos sensibles)
- Usar django-cryptography o similar para encriptar datos de tarjetas
- Nunca guardar el número completo de tarjeta (solo últimos 4 dígitos)
- Considerar cumplimiento PCI DSS si se procesan tarjetas directamente

### 7. URLs

#### 7.1 Agregar en `urls.py`
- `path('pago/<int:reserva_id>/', views.procesar_pago, name='procesar_pago')`
- `path('pago/exitoso/<int:reserva_id>/', views.pago_exitoso, name='pago_exitoso')`
- `path('pago/fallido/<int:reserva_id>/', views.pago_fallido, name='pago_fallido')`

### 8. Testing

#### 8.1 Casos de prueba a implementar
- Pago exitoso con tarjeta nueva
- Pago exitoso con método guardado
- Pago rechazado por datos inválidos
- Pago rechazado por error de pasarela
- Timeout en procesamiento
- Intento de pagar reserva ya pagada
- Intento de pagar reserva inexistente
- Validación de monto manipulado

### 9. Experiencia de Usuario

#### 9.1 Mensajes informativos
- Indicador de procesamiento: "Procesando tu pago, por favor espera..."
- Mensaje de éxito: "¡Pago exitoso! Tu reserva ha sido confirmada"
- Mensaje de error con razón específica
- Confirmación visual clara de pago completado

#### 9.2 Feedback visual
- Barra de progreso durante procesamiento
- Iconos de éxito/error
- Cambio de color en resumen de orden al confirmar
- Animaciones suaves en transiciones

---

## PBI-27: Métodos de Pago Guardados

### Objetivo
Permitir a usuarios autenticados guardar sus métodos de pago para futuras compras.

### 1. Modificaciones al Modelo de Datos

#### 1.1 Crear modelo `MetodoPago`
- Campo: usuario (ForeignKey a User)
- Campo: tipo (CharField con choices: 'TARJETA', 'CUENTA_DIGITAL')
- Campo: alias (CharField, ej: "Visa Personal", "PayPal Principal")
- Campo: es_predeterminado (BooleanField, default=False)
- Campo: activo (BooleanField, default=True)
- Campo: fecha_creacion (DateTimeField, auto_now_add=True)
- Campo: fecha_actualizacion (DateTimeField, auto_now=True)
- Campos específicos para tarjetas:
  - ultimos_4_digitos (CharField, length=4)
  - tipo_tarjeta (CharField: 'VISA', 'MASTERCARD', 'AMEX', etc.)
  - mes_expiracion (IntegerField)
  - anio_expiracion (IntegerField)
  - nombre_titular (CharField)
- Campos específicos para cuentas digitales:
  - tipo_cuenta (CharField: 'PAYPAL', 'STRIPE', 'OTRO')
  - email_cuenta (EmailField)
- Campo: datos_encriptados (TextField, para información sensible encriptada)
- Meta: unique_together = ['usuario', 'alias']

#### 1.2 Crear migraciones
- Ejecutar `python manage.py makemigrations`
- Ejecutar `python manage.py migrate`

### 2. Crear Pantalla de Gestión de Métodos de Pago

#### 2.1 Crear template `mis_metodos_pago.html`
- Sección: Lista de métodos guardados
  - Card por cada método mostrando:
    - Icono según tipo (tarjeta/cuenta digital)
    - Alias del método
    - Detalles resumidos (últimos 4 dígitos, tipo tarjeta, email cuenta)
    - Fecha de expiración (si aplica)
    - Badge "Predeterminado" si corresponde
    - Botones: "Editar", "Eliminar", "Marcar como predeterminado"
- Sección: Agregar nuevo método
  - Botón "+ Agregar Método de Pago"
  - Modal o página separada con formulario
- Mensaje si no hay métodos guardados: "No tienes métodos de pago guardados"
- Navegación: breadcrumb o botón de retorno

#### 2.2 Crear CSS `metodos_pago.css`
- Diseño de cards responsivo
- Estilos para iconos de tipos de pago
- Animaciones de hover en cards
- Estilos para modales
- Badge de método predeterminado
- Estados de botones (editar, eliminar)

#### 2.3 Crear template `agregar_metodo_pago.html`
- Formulario similar al de pago pero enfocado en guardar
- Selección de tipo de método
- Campos dinámicos según tipo
- Campo: alias personalizado
- Checkbox: marcar como predeterminado
- Botones: "Guardar", "Cancelar"

#### 2.4 Crear template `editar_metodo_pago.html`
- Formulario pre-llenado con datos actuales (excepto CVV)
- Permitir cambiar alias
- Permitir cambiar si es predeterminado
- NO mostrar/editar datos encriptados (número completo de tarjeta)
- Solo permitir actualizar fecha de expiración (tarjetas)
- Botones: "Actualizar", "Cancelar"

### 3. Lógica de Backend

#### 3.1 Crear vista `mis_metodos_pago(request)` (requiere login)
- Decorador: @login_required
- Obtener todos los métodos del usuario: `MetodoPago.objects.filter(usuario=request.user, activo=True)`
- Ordenar: predeterminado primero, luego por fecha de creación desc
- Renderizar template con lista de métodos

#### 3.2 Crear vista `agregar_metodo_pago(request)` (requiere login)
- Decorador: @login_required
- Si GET: renderizar formulario vacío
- Si POST:
  - Validar formulario
  - Si es válido:
    - Encriptar datos sensibles
    - Crear registro en MetodoPago
    - Si es marcado como predeterminado: desmarcar otros métodos del usuario
    - Mensaje de éxito: "Método de pago guardado exitosamente"
    - Redirigir a `mis_metodos_pago`
  - Si inválido:
    - Mostrar errores en formulario

#### 3.3 Crear vista `editar_metodo_pago(request, metodo_id)` (requiere login)
- Decorador: @login_required
- Verificar que el método pertenece al usuario: `get_object_or_404(MetodoPago, id=metodo_id, usuario=request.user)`
- Si GET: renderizar formulario con datos actuales
- Si POST:
  - Validar formulario
  - Actualizar campos permitidos (alias, es_predeterminado, fecha_expiracion)
  - Si cambió a predeterminado: desmarcar otros
  - Mensaje de éxito: "Método actualizado"
  - Redirigir a `mis_metodos_pago`

#### 3.4 Crear vista `eliminar_metodo_pago(request, metodo_id)` (requiere login)
- Decorador: @login_required
- Verificar que el método pertenece al usuario
- Si GET: mostrar confirmación
- Si POST:
  - Marcar como inactivo (soft delete): `metodo.activo = False`
  - O eliminar permanentemente: `metodo.delete()`
  - Si era predeterminado y quedan otros: marcar el más reciente como predeterminado
  - Mensaje de éxito: "Método eliminado"
  - Redirigir a `mis_metodos_pago`

#### 3.5 Crear vista `marcar_predeterminado(request, metodo_id)` (requiere login)
- Decorador: @login_required
- Verificar que el método pertenece al usuario
- Desmarcar todos los métodos del usuario: `MetodoPago.objects.filter(usuario=request.user).update(es_predeterminado=False)`
- Marcar el seleccionado: `metodo.es_predeterminado = True`
- Mensaje de éxito: "Método predeterminado actualizado"
- Redirigir a `mis_metodos_pago`

#### 3.6 Modificar vista `procesar_pago(request, reserva_id)`
- Agregar lógica condicional:
  - Si usuario autenticado:
    - Cargar métodos guardados: `metodos = MetodoPago.objects.filter(usuario=request.user, activo=True)`
    - Pasar al contexto del template de pago
    - Si selecciona método guardado:
      - Cargar datos del método (desencriptar si es necesario)
      - Pre-llenar formulario (excepto CVV, siempre requerido)
      - Procesar pago con datos guardados
  - Si usuario no autenticado o elige nuevo método:
    - Flujo normal de pago con datos nuevos
    - Si checkbox "guardar método" está marcado y usuario autenticado:
      - Guardar en MetodoPago después de pago exitoso

### 4. Formularios

#### 4.1 Crear `MetodoPagoForm` en `forms.py`
- Campo: tipo (ChoiceField: 'TARJETA', 'CUENTA_DIGITAL')
### 6. Integración de Métodos Guardados en Asientos

#### 6.1 Modificar contexto de vista `asientos(request, pelicula_id)`
- Si usuario está autenticado:
  - Consultar métodos guardados: `MetodoPago.objects.filter(usuario=request.user, activo=True).order_by('-es_predeterminado', '-fecha_creacion')`
  - Agregar al contexto: `'metodos_guardados': metodos`
  - Agregar al contexto: `'tiene_metodos_guardados': metodos.exists()`
  - Identificar método predeterminado para pre-selección
- Si usuario no autenticado:
  - Agregar al contexto: `'metodos_guardados': None`
  - Agregar al contexto: `'tiene_metodos_guardados': False`

#### 6.2 Lógica de renderizado condicional en template
- Usar `{% if user.is_authenticated and tiene_metodos_guardados %}`
- Iterar sobre métodos guardados: `{% for metodo in metodos_guardados %}`
- Mostrar información según tipo:
  - Si es tarjeta: tipo_tarjeta + "****" + ultimos_4_digitos
  - Si es cuenta digital: tipo_cuenta + email_cuenta
- Marcar método predeterminado como checked en radio button
- Template tags para formateo:
  - Crear filter personalizado para enmascarar número de tarjeta
  - Crear filter para mostrar icono según tipo de tarjetase64
  - Función `decrypt_data(encrypted_data)`: desencripta y retorna datos originales
### 7. URLs para Gestión de Métodos

#### 7.1 Agregar en `urls.py`
- `path('mis-metodos-pago/', views.mis_metodos_pago, name='mis_metodos_pago')`
- `path('metodos-pago/agregar/', views.agregar_metodo_pago, name='agregar_metodo_pago')`
- `path('metodos-pago/editar/<int:metodo_id>/', views.editar_metodo_pago, name='editar_metodo_pago')`
- `path('metodos-pago/eliminar/<int:metodo_id>/', views.eliminar_metodo_pago, name='eliminar_metodo_pago')`
- `path('metodos-pago/predeterminado/<int:metodo_id>/', views.marcar_predeterminado, name='marcar_predeterminado')`
- Nota: NO se necesitan URLs de pago separadas (pago_exitoso, pago_fallido) ya que todo se maneja en asientos.html
### 8. Navegación y Acceso a Gestión de Métodos

#### 8.1 Agregar enlaces en navegación principal
- En template base o navbar (solo si está autenticado):
  - Link: "Mis Métodos de Pago"
  - Icono de tarjeta o billetera (Font Awesome: fa-credit-card)
  - Ubicación sugerida: menú desplegable de usuario
- En template `asientos.html` (dentro de sección de métodos guardados):
  - Link pequeño: "Administrar métodos de pago"
  - Abre en nueva pestaña o modal
  - Icono de engranaje o editar
### 6. Mostrar Métodos en Pantalla de Pago

#### 6.1 Modificar template `pago.html`
- Si usuario autenticado y tiene métodos guardados:
  - Sección: "Métodos de pago guardados"
  - Radio buttons o cards seleccionables por cada método
  - Mostrar datos resumidos de cada método
  - Destacar método predeterminado (pre-seleccionado)
### Fase 1: Base del Sistema de Pago Integrado (PBI-30)
1. Crear modelo `Pago` y modificar modelo `Reserva`
2. Crear migraciones y aplicarlas
3. Crear archivo `utils/payment_simulator.py` con función `simular_pago()`
6. Modificar template `asientos.html`:es de simulación (PAYMENT_MODE, PAYMENT_SUCCESS_RATE)
5. Crear función auxiliar `procesar_pago_tarjeta()` que use el simulador
  - Checkbox: "Guardar este método para futuras compras"
- Si usuario no autenticado:
  - Solo mostrar formulario de nuevo método
7. Modificar CSS `asientos.css`: guardar tus métodos de pago"

#### 6.2 JavaScript para interactividad
- Mostrar/ocultar formulario según selección (método guardado vs nuevo)
- Validación en tiempo real de campos
8. Modificar JavaScript `asientos.js`: de método
- Pre-llenar datos si selecciona método guardado (excepto CVV)

### 7. URLs

#### 7.1 Agregar en `urls.py`
9. Modificar vista `asientos()`:is_metodos_pago, name='mis_metodos_pago')`
- `path('metodos-pago/agregar/', views.agregar_metodo_pago, name='agregar_metodo_pago')`
- `path('metodos-pago/editar/<int:metodo_id>/', views.editar_metodo_pago, name='editar_metodo_pago')`
- `path('metodos-pago/eliminar/<int:metodo_id>/', views.eliminar_metodo_pago, name='eliminar_metodo_pago')`
- `path('metodos-pago/predeterminado/<int:metodo_id>/', views.marcar_predeterminado, name='marcar_predeterminado')`
## Orden de Implementación Recomendado (ACTUALIZADO)

### Fase 1: Base del Sistema de Pago Integrado (PBI-30)
10. Testing básico del flujo de pago:
    - Pago exitoso con simulación
    - Pago fallido con diferentes errores simulados
    - Validación de campos de tarjeta
    - Manejo de errores y excepciones
    - Verificar creación de registros (Pago, Reserva, Venta)
    - Verificar generación de PDF y envío de email

### Fase 2: Sistema de Métodos de Pago Guardados (PBI-27)
11. Crear modelo `MetodoPago` (con campos para tarjetas y encriptación)
12. Crear migraciones y aplicarlas
15. Crear CSS `metodos_pago.css`:ptación en `utils/encryption.py`
14. Crear templates de gestión: CVV, titular
   - Checkbox "Guardar tarjeta" (si usuario autenticado)
5. Modificar CSS `asientos.css`:
   - Estilos para sección de pago
16. Implementar vistas CRUD de métodos:
   - Iconos de tipos de tarjeta
   - Indicador de procesamiento
6. Modificar JavaScript `asientos.js`:
   - Validación de campos de tarjeta
   - Formato automático de número de tarjeta
17. Crear formulario `MetodoPagoForm` en `forms.py`
18. Agregar URLs de gestión de métodos
19. Testing de CRUD de métodos:
    - Crear método de pago
    - Editar método existente
    - Eliminar método (soft delete)
    - Marcar como predeterminado
    - Validar seguridad (solo acceso a propios métodos)

### Fase 3: Integración de Métodos Guardados con Pago
20. Modificar template `asientos.html`:
21. Modificar contexto de vista `asientos()`:
   - Llamar función de procesamiento
   - Manejar éxito/fallo en la misma pantalla
   - Crear Reserva solo si pago exitoso
22. Modificar lógica de procesamiento en vista `asientos()`:
8. Testing básico del flujo de pago

### Fase 2: Sistema de Métodos de Pago Guardados (PBI-27)
9. Crear modelo `MetodoPago` (con campos para tarjetas y encriptación)
23. Modificar JavaScript `asientos.js`:
11. Implementar utilidad de encriptación en `utils/encryption.py`
12. Crear templates de gestión:
    - `mis_metodos_pago.html` (listar métodos)
24. Agregar enlaces de navegación a gestión de métodos:ar)
    - `editar_metodo_pago.html` (formulario para editar)
    - Modal de confirmación para eliminar
25. Testing de integración completa:
    - Cards de métodos guardados
    - Formularios de agregar/editar
    - Badge de método predeterminado
    - Iconos y estados
14. Implementar vistas CRUD de métodos:
### Fase 4: Mejoras, Seguridad y Testing Final
26. Implementar validaciones de seguridad:
    - `editar_metodo_pago()` - Actualizar
    - `eliminar_metodo_pago()` - Eliminar (soft delete)
    - `marcar_predeterminado()` - Cambiar predeterminado
27. Implementar auditoría:doPagoForm` en `forms.py`
16. Agregar URLs de gestión de métodos
17. Testing de CRUD de métodos
28. Tarea de expiración de tarjetas:
### Fase 3: Integración de Métodos Guardados con Pago
18. Modificar template `asientos.html`:
29. Testing exhaustivo de seguridad:entos()`:
    - Cargar métodos guardados del usuario
    - Pasar al template
    - Identificar método predeterminado
20. Modificar lógica de procesamiento en vista `asientos()`:
    - Detectar si usa método guardado o nuevo
    - Si usa guardado: cargar y desencriptar datos
    - Si usa nuevo con checkbox marcado: guardar en MetodoPago después de pago exitoso
    - Validar CVV en ambos casos
30. Documentación de usuario:entos.js`:
    - Toggle entre secciones de métodos guardados y nueva tarjeta
    - Mostrar/ocultar campo CVV según selección
31. Deploy a producción:
    - Verificar configuración de PAYMENT_MODE en producción
    - Confirmar que sistema de simulación funciona correctamente
    - Monitorear logs de transacciones simuladas
    - Documentar que el sistema usa simulación (no procesamiento real)

---

## Nota Importante sobre Simulación

**El sistema completo utilizará SIMULACIÓN de pagos en todos los ambientes (desarrollo y producción).**

- No se procesarán pagos reales
- No se integrará con pasarelas de pago externas (Stripe, PayPal, etc.)
- Todos los pagos serán simulados con probabilidad configurable de éxito/fallo
- Los números de transacción serán generados internamente
- La arquitectura está diseñada para facilitar futura integración real si se requiere
- Se debe informar claramente a los usuarios que es un sistema de demostración

**Ventajas de usar simulación:**
- No requiere cuentas ni API keys de servicios externos
- No hay costos de transacción
- Control total sobre escenarios de prueba
- Simplifica testing y debugging
- Reduce complejidad del despliegueional de campos
22. Agregar enlaces de navegación a gestión de métodos:
    - En navbar (menú de usuario)
    - En pantalla de asientos (link pequeño)
23. Testing de integración completa:
    - Pago con método guardado
    - Pago con nueva tarjeta y guardar
    - Pago con nueva tarjeta sin guardar
    - Usuario no autenticado (solo nueva tarjeta)

### Fase 4: Mejoras, Seguridad y Producción
24. Implementar validaciones de seguridad:
    - Verificar que usuario solo accede a sus métodos
    - Rate limiting en endpoints
    - Validación de monto en backend
25. Implementar auditoría:
    - Logs de pagos procesados
    - Logs de cambios en métodos de pago
26. Tarea de expiración de tarjetas:
    - Script periódico (cron o Celery)
    - Notificación a usuarios con tarjetas por expirar
27. (Opcional) Integrar pasarela de pago real:
    - Investigar Stripe/PayPal/MercadoPago
    - Reemplazar simulación con integración real
    - Configurar webhooks
    - Testing en ambiente sandbox
28. Testing exhaustivo de seguridad:
    - Intentos de acceso no autorizado
    - Validación de datos sensibles
    - Prevención de fraude
29. Documentación de usuario:
    - Guía de uso de métodos de pago
    - FAQ sobre seguridad
30. Deploy a producción
- Crear modelo `LogMetodoPago`:
  - Usuario, acción (CREADO, EDITADO, ELIMINADO, USADO), fecha, IP
  - Útil para soporte y seguridad

---

## Orden de Implementación Recomendado

### Fase 1: Base del Sistema de Pago (PBI-30)
1. Crear modelo `Pago` y modificar `Reserva`
2. Crear migraciones y aplicarlas
3. Crear template y CSS de `pago.html`
4. Implementar vista `procesar_pago()` con simulación
5. Modificar vista `asientos()` para redirigir a pago
6. Crear vistas de éxito y fallo
7. Agregar URLs
8. Testing básico

### Fase 2: Métodos de Pago Guardados (PBI-27)
9. Crear modelo `MetodoPago`
10. Crear migraciones y aplicarlas
11. Implementar encriptación (utils)
12. Crear templates de gestión de métodos
13. Crear CSS de métodos de pago
14. Implementar vistas CRUD de métodos
15. Crear formularios de métodos
16. Agregar URLs de métodos
17. Testing de gestión de métodos

### Fase 3: Integración Completa
18. Modificar template `pago.html` para mostrar métodos guardados
19. Modificar vista `procesar_pago()` para manejar métodos guardados
20. Agregar JavaScript de interactividad en pago
21. Implementar guardado automático de método después de pago (si checkbox marcado)
22. Testing de integración completa

### Fase 4: Mejoras y Producción
23. Integrar pasarela de pago real (si aplica)
24. Implementar tarea de expiración de tarjetas
25. Agregar auditoría y logs
26. Testing de seguridad
27. Documentación de usuario
28. Deploy a producción

---

## Notas Finales

- **Prioridad**: Implementar primero PBI-30 (base de pago) y luego PBI-27 (métodos guardados)
- **Seguridad**: Nunca almacenar CVV, considerar tokenización con pasarela
- **UX**: Proceso de pago debe ser fluido y con feedback claro
- **Testing**: Probar exhaustivamente antes de producción
- **Cumplimiento**: Verificar normativas locales sobre manejo de datos de pago (PCI DSS)
- **Alternativa**: Considerar usar Stripe Elements o PayPal SDK para manejo seguro de tarjetas sin tocar datos sensibles en tu servidor
