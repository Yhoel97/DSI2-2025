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
- Formulario con campos:
  - Número de tarjeta (input con formato automático)
  - Fecha de expiración (MM/YY)
  - CVV (3-4 dígitos)
  - Nombre del titular
- Si usuario autenticado:
  - Checkbox: "Guardar esta tarjeta para futuras compras" (para Fase 2)
- Si usuario NO autenticado:
  - Mensaje informativo: "Inicia sesión para guardar tus métodos de pago"
- Botón "Confirmar Reserva y Pagar" (reemplaza el actual "Confirmar Reserva")
- Indicador de carga durante procesamiento del pago

#### 2.2 Modificar CSS `asientos.css`
- Estilos para sección de pago
- Estilos para campos de tarjeta
- Iconos de tipos de tarjeta
- Indicador de procesamiento con spinner
- Animaciones de transición

#### 2.3 Modificar JavaScript `asientos.js`
- Validación de número de tarjeta en tiempo real
  - Aplicar formato automático (espacios cada 4 dígitos)
  - Detectar tipo de tarjeta (Visa, Mastercard, Amex) por prefijo
  - Mostrar icono correspondiente
  - Validar longitud según tipo (16 o 15 dígitos)
- Validación de fecha de expiración
  - Formato automático MM/YY
  - Validar que no esté vencida
  - Validar formato correcto (mes 01-12)
- Validación de CVV
  - Solo números
  - Longitud según tipo de tarjeta (3 o 4 dígitos)
- Validación de nombre del titular
  - Solo letras y espacios
  - Transformar a mayúsculas automáticamente
- Indicador de procesamiento de pago
  - Mostrar spinner y mensaje "Procesando pago..."
  - Deshabilitar botón de confirmar durante procesamiento
  - Prevenir múltiples envíos del formulario
- Validación completa antes de enviar formulario

### 3. Lógica de Backend

#### 3.1 Modificar vista `asientos(request, pelicula_id)`
- Mantener toda la lógica actual de selección de asientos y cálculo de precios
- Al confirmar reserva (POST con accion='reservar'):
  - Extraer datos de tarjeta del formulario
  - Validar campos de tarjeta (número, fecha exp, CVV, titular)
  - Crear registro en modelo `Pago` con estado 'PENDIENTE'
  - Llamar función `simular_pago()` con datos de tarjeta y monto
  - **Si pago exitoso:**
    - Actualizar Pago: estado='APROBADO', numero_transaccion=generado
    - Crear Reserva: pago_completado=True, fecha_pago=ahora
    - Registrar en modelo Venta
    - Generar PDF del ticket
    - Enviar email con ticket adjunto
    - Mostrar mensaje de éxito con código de reserva
  - **Si pago fallido:**
    - Actualizar Pago: estado='RECHAZADO', guardar mensaje de error
    - NO crear Reserva
    - NO registrar Venta
    - NO generar PDF ni enviar email
    - Mostrar mensaje de error y permitir reintentar

#### 3.2 Crear función `simular_pago()` en `utils/payment_simulator.py`
- Parámetros: numero_tarjeta, nombre_titular, fecha_expiracion, cvv, monto
- Validaciones internas:
  - Verificar que monto > 0
  - Validar formato de número de tarjeta
  - Validar que la fecha de expiración no ha pasado
  - Validar longitud de CVV (3 o 4 dígitos)
- **Lógica de simulación:**
  - Generar número de transacción único: formato `TXN-YYYYMMDDHHMMSS-XXXXXX`
  - Usar configuración `PAYMENT_SUCCESS_RATE` para determinar éxito/fallo
  - Tipos de error simulados (10% de casos):
    - "Fondos insuficientes"
    - "Tarjeta rechazada por el banco"
    - "Error de conexión temporal"
    - "Tarjeta expirada"
    - "CVV incorrecto"
- Retornar diccionario:
  ```python
  {
      'exitoso': bool,
      'numero_transaccion': str,
      'mensaje': str,
      'tipo_tarjeta': str,
      'numero_tarjeta_enmascarado': str
  }
  ```

### 4. Configuración

#### 4.1 Agregar en `settings.py`
- Constante: `PAYMENT_MODE = 'SIMULATION'`
- Configuración: `PAYMENT_SUCCESS_RATE = 0.9` (90% de éxito)
- Documentar que el sistema usa simulación, no procesamiento real

### 5. Panel de Administración

#### 5.1 Registrar modelo `Pago` en `admin.py`
- Configurar `PagoAdmin` con:
  - list_display: id, numero_transaccion, monto, estado_pago, fecha_pago, código de reserva
  - list_filter: estado_pago, metodo_pago, fecha_pago
  - search_fields: numero_transaccion, reserva__codigo_reserva, reserva__email
  - readonly_fields: fecha_pago, numero_transaccion, detalles_pago
  - Deshabilitar permisos de agregar/eliminar para preservar auditoría

### 6. Testing

#### 6.1 Casos de prueba básicos
- Pago exitoso con tarjeta válida
- Pago rechazado por simulación (10% de casos)
- Validación de campos de tarjeta
- Manejo de errores y excepciones
- Verificar creación de registros (Pago, Reserva, Venta)
- Verificar generación de PDF y envío de email solo tras pago exitoso

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
#### 4.1 Crear `MetodoPagoForm` en `forms.py`
- Campo: tipo (ChoiceField: 'TARJETA', 'CUENTA_DIGITAL')
- Campo: alias (CharField para nombre personalizado)
- Campos para tarjeta: numero_tarjeta, fecha_expiracion, cvv, nombre_titular
- Campos para cuenta digital: tipo_cuenta, email_cuenta
- Campo: es_predeterminado (BooleanField)
- Validaciones personalizadas por tipo

### 5. Integración de Métodos Guardados

#### 5.1 Modificar template `asientos.html`
- Si usuario autenticado y tiene métodos guardados:
  - Mostrar sección "Métodos de pago guardados"
  - Radio buttons para cada método (mostrar últimos 4 dígitos)
  - Campo CVV adicional al seleccionar método guardado
  - Link "Administrar métodos de pago"
- Opción "Usar nueva tarjeta"
- Toggle entre formulario de método guardado y nueva tarjeta

#### 5.2 Modificar vista `asientos()`
- Cargar métodos guardados si usuario autenticado
- Pasar al template en contexto
- Detectar si usa método guardado o nuevo
- Si usa guardado: desencriptar y procesar
- Si usa nuevo con checkbox marcado: guardar en MetodoPago después de pago exitoso

#### 5.3 JavaScript para alternancia
- Mostrar/ocultar formularios según selección
- Validar CVV cuando usa método guardado
- Habilitar/deshabilitar campos apropiadamente

### 6. URLs para Gestión de Métodos

#### 6.1 Agregar en `urls.py`
- `path('mis-metodos-pago/', views.mis_metodos_pago, name='mis_metodos_pago')`
- `path('metodos-pago/agregar/', views.agregar_metodo_pago, name='agregar_metodo_pago')`
- `path('metodos-pago/editar/<int:metodo_id>/', views.editar_metodo_pago, name='editar_metodo_pago')`
- `path('metodos-pago/eliminar/<int:metodo_id>/', views.eliminar_metodo_pago, name='eliminar_metodo_pago')`
- `path('metodos-pago/predeterminado/<int:metodo_id>/', views.marcar_predeterminado, name='marcar_predeterminado')`

### 7. Navegación

#### 7.1 Enlaces en navbar
- "Mis Métodos de Pago" en menú de usuario (solo si autenticado)
- Icono de tarjeta (Font Awesome)

## Orden de Implementación Recomendado

### Fase 1: Base del Sistema de Pago Integrado (PBI-30) ✅ COMPLETADO
1. ✅ Crear modelo `Pago` y modificar modelo `Reserva` - Commit: a710402
2. ✅ Crear migraciones y aplicarlas (0016_reserva_fecha_pago_reserva_pago_completado_pago)
3. ✅ Crear archivo `utils/payment_simulator.py` con función `simular_pago()`
   - Validaciones: número de tarjeta, CVV, fecha de expiración
   - Generación de número de transacción único (TXN-YYYYMMDDHHMMSS-XXXXXX)
   - Simulación con 90% de éxito configurable
4. ✅ Configurar settings.py (PAYMENT_MODE='SIMULATION', PAYMENT_SUCCESS_RATE=0.9)
5. ✅ Modificar template `asientos.html` - agregar sección de pago
   - Formulario con campos: número_tarjeta, nombre_titular, fecha_expiracion, cvv
   - Checkbox guardar_tarjeta (para usuarios autenticados)
   - Indicador de procesamiento con spinner
6. ✅ Modificar CSS `asientos.css` - estilos de pago (+300 líneas)
   - Estilos para payment-section, new-card-form
   - Animaciones de spinner y transiciones
   - Diseño responsive
7. ✅ Modificar JavaScript `asientos.js` - validaciones de tarjeta (+200 líneas)
   - Validación en tiempo real: número, CVV, fecha, nombre
   - Formato automático de número de tarjeta
   - Detección de tipo de tarjeta (Visa/Mastercard/Amex)
8. ✅ Modificar vista `asientos()` - integrar procesamiento de pago
   - Llamar simular_pago() antes de crear Reserva
   - Crear registro Pago con estado PENDIENTE
   - Solo crear Reserva si pago exitoso (APROBADO)
   - Manejo de errores y mensajes para pagos rechazados
9. ✅ Registrar modelo `Pago` en admin.py - Commit: 952a4d7
   - list_display, list_filter, search_fields
   - Campos readonly para auditoría
   - Permisos restringidos (no agregar/eliminar)
10. ✅ Testing básico del flujo de pago
    - Pago exitoso con tarjeta válida ✓
    - Pago rechazado por simulación ✓
    - Validaciones frontend funcionando ✓
    - Generación de PDF y email solo tras pago exitoso ✓

### Fase 2: Sistema de Métodos de Pago Guardados (PBI-27) - PENDIENTE
11. Crear modelo `MetodoPago` (con campos para tarjetas y encriptación)
12. Crear migraciones y aplicarlas
13. Implementar utilidad de encriptación en `utils/encryption.py`
14. Crear templates de gestión:
    - `mis_metodos_pago.html` (listar métodos)
    - `agregar_metodo_pago.html` (formulario agregar)
    - `editar_metodo_pago.html` (formulario editar)
15. Crear CSS `metodos_pago.css`
16. Implementar vistas CRUD de métodos:
    - `mis_metodos_pago()` - Listar
    - `agregar_metodo_pago()` - Crear
    - `editar_metodo_pago()` - Actualizar
    - `eliminar_metodo_pago()` - Eliminar (soft delete)
    - `marcar_predeterminado()` - Cambiar predeterminado
17. Crear formulario `MetodoPagoForm` en `forms.py`
18. Agregar URLs de gestión de métodos
19. Testing de CRUD de métodos

### Fase 3: Integración de Métodos Guardados con Pago - PENDIENTE
20. Modificar template `asientos.html`: mostrar métodos guardados
21. Modificar contexto de vista `asientos()`: cargar métodos guardados
22. Modificar lógica de procesamiento en vista `asientos()`: manejar métodos guardados
23. Modificar JavaScript `asientos.js`: toggle entre método guardado y nuevo
24. Agregar enlaces de navegación a gestión de métodos
25. Testing de integración completa

### Fase 4: Mejoras, Seguridad y Testing Final - PENDIENTE
26. Implementar validaciones de seguridad
27. Implementar auditoría y logging
28. Tarea de expiración de tarjetas (opcional)
29. Testing exhaustivo de seguridad
30. Documentación de usuario
31. Deploy a producción

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
- Reduce complejidad del despliegue

---

## Notas Finales

- **Prioridad**: Implementar primero PBI-30 (base de pago) ✅ COMPLETADO, luego PBI-27 (métodos guardados)
- **Seguridad**: Nunca almacenar CVV, implementar encriptación para datos de tarjetas
- **UX**: Proceso de pago integrado en una sola pantalla (asientos.html)
- **Testing**: Probar exhaustivamente cada fase antes de continuar
- **Auditoría**: Todos los intentos de pago se registran en modelo Pago para trazabilidad

