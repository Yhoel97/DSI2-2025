# Análisis de Errores Reportados en el Sistema de Pagos

## Problema 1: Error de unique key al usar 2 veces la misma tarjeta

### 📍 Ubicación del problema:
- **Archivo:** `myapp/models.py`
- **Línea:** 490
- **Código:**
```python
class Meta:
    unique_together = ['usuario', 'alias']
```

### 🔍 Causa:
El modelo `MetodoPago` tiene una restricción `unique_together` en los campos `usuario` y `alias`. Esto significa que:
- Un usuario NO puede tener dos métodos de pago con el mismo alias
- Si el usuario intenta guardar una tarjeta con un alias que ya usó, fallará con error de unique constraint

### ❌ Escenario de falla:
1. Usuario completa compra y guarda tarjeta con alias "Mi Tarjeta"
2. En segunda compra, vuelve a marcar "guardar tarjeta" con mismo alias "Mi Tarjeta"
3. Error: `UNIQUE constraint failed: metodos_pago.usuario_id, metodos_pago.alias`

### ✅ Solución propuesta:
**Opción 1:** Validar antes de guardar y actualizar en lugar de crear duplicado
**Opción 2:** Agregar sufijo automático si existe (ej: "Mi Tarjeta (2)")
**Opción 3:** Mostrar error al usuario y pedirle un alias diferente

---

## Problema 2: Se crea reserva aunque falle validación del formulario

### 📍 Ubicación del problema:
- **Archivo:** `myapp/views.py`
- **Línea:** 733-900 (función `asientos`)

### 🔍 Análisis del flujo actual:
```python
# Línea 695-729: Validaciones de campos
if not nombre_cliente: errores.append(...)
if not cvv: errores.append(...)

# Línea 733: Protección con if not errores
if not errores:
    try:
        # Línea 754: Se llama simular_pago()
        resultado_pago = simular_pago(datos_tarjeta, monto)
        
        # Línea 758: Se crea Pago PENDIENTE
        pago = Pago(estado_pago="PENDIENTE")
        pago.save()
        
        # Línea 770: Se verifica si pago fue exitoso
        if resultado_pago["exitoso"]:
            # Línea 778: Se crea Reserva
            reserva = Reserva(...)
            reserva.save()
```

### ❓ Pregunta para validar:
El código tiene protección `if not errores:` que previene crear reservas si hay errores de validación. 

**¿El problema reportado es uno de estos?**

1. **Si el simulador de pago falla** (tarjeta rechazada), se crea registro de Pago PENDIENTE/RECHAZADO pero NO se crea Reserva ✅ Correcto

2. **Si hay error de validación** (CVV vacío), NO se procesa nada ✅ Correcto

3. **¿El problema real es que el objeto Pago se crea ANTES de saber si fue exitoso?**
   - Se crea Pago con estado PENDIENTE (línea 758)
   - Si falla, se actualiza a RECHAZADO (línea 893)
   - Esto deja registros de pagos fallidos en la BD
   - **¿Es esto lo que reportan?**

### ✅ Solución propuesta:
**Si el problema es #3:**
- Solo crear el objeto Pago DESPUÉS de confirmar que fue exitoso
- O usar transacciones atómicas para revertir si falla

**Si el problema es otro:**
- Necesito más información sobre el escenario exacto de falla

---

## 🧪 Plan de pruebas:

### Test 1: Duplicado de alias
1. Iniciar sesión como usuario_prueba
2. Comprar boletos con nueva tarjeta
3. Marcar "guardar tarjeta" con alias "Test 1"
4. Completar compra ✅
5. Hacer segunda compra
6. Marcar "guardar tarjeta" con MISMO alias "Test 1"
7. **Resultado esperado:** Error de unique constraint

### Test 2: CVV vacío
1. Iniciar sesión como usuario_prueba
2. Seleccionar boletos
3. Llenar todos los campos EXCEPTO CVV
4. Hacer clic en "Confirmar Reserva y Pagar"
5. **Resultado esperado:** Error "El CVV es obligatorio"
6. **Verificar:** ¿Se creó alguna reserva en la BD?

### Test 3: Tarjeta rechazada
1. Usar número de tarjeta que simule rechazo
2. Completar todos los campos correctamente
3. Hacer clic en "Confirmar Reserva y Pagar"
4. **Resultado esperado:** "Error en el pago"
5. **Verificar:** ¿Se creó reserva? ¿Se creó registro de Pago RECHAZADO?

---

## 📋 Siguiente paso:
Ejecutar los tests para reproducir y confirmar los problemas.

---

## 🔍 ANÁLISIS COMPLETO REALIZADO

### Problema 1: CONFIRMADO ✅
**Error:** `UNIQUE constraint failed: metodos_pago.usuario_id, metodos_pago.alias`
**Ubicación:** `myapp/models.py:490`
**Código problemático:**
```python
class Meta:
    unique_together = ['usuario', 'alias']
```

**Flujo del error:**
1. Usuario compra con nueva tarjeta
2. Marca "Guardar tarjeta" con alias "Mi Visa"
3. Compra exitosa, método guardado ✅
4. Segunda compra con nueva tarjeta
5. Marca "Guardar tarjeta" con MISMO alias "Mi Visa"
6. En línea 851 de views.py: `MetodoPago.objects.create(...)`
7. **ERROR:** IntegrityError por unique_together

### Problema 2: ANÁLISIS DETALLADO
**Estado actual del código (views.py líneas 733-900):**

```python
# Línea 733: Validación de errores
if not errores:
    try:
        # Línea 754: Procesar pago
        resultado_pago = simular_pago(...)
        
        # Línea 758-769: Crear Pago PENDIENTE
        pago = Pago(estado_pago="PENDIENTE", ...)
        pago.save()  # ⚠️ SE GUARDA EN BD
        
        # Línea 770: Verificar si fue exitoso
        if resultado_pago["exitoso"]:
            pago.estado_pago = "APROBADO"
            pago.save()
            
            # Línea 778-796: Crear Reserva
            reserva = Reserva(...)
            reserva.save()  # ✅ SOLO SI PAGO EXITOSO
            
            # ... PDF, correo, etc.
        else:
            # Línea 893: Pago rechazado
            pago.estado_pago = "RECHAZADO"
            pago.save()  # ⚠️ QUEDA EN BD
            messages.error(...)
```

**Hallazgos:**
1. ✅ La Reserva SOLO se crea si `resultado_pago["exitoso"]` = True
2. ⚠️ El objeto Pago se crea ANTES de saber si fue exitoso
3. ⚠️ Si el pago falla, queda un registro de Pago RECHAZADO en BD
4. ❌ Si hay una excepción durante el proceso, puede quedar inconsistencia

**Posibles escenarios del reporte:**
- **Escenario A:** Se crean registros de Pago fallidos (no Reservas)
- **Escenario B:** JavaScript permite doble submit
- **Escenario C:** Exception durante el proceso deja datos inconsistentes

---

## ✅ SOLUCIONES PROPUESTAS

### Solución 1: Error de unique key en alias
```python
# En views.py línea 841-861, ANTES de crear MetodoPago:

if guardar_tarjeta and request.user.is_authenticated:
    try:
        # Verificar si ya existe un método con este alias
        metodo_existente = MetodoPago.objects.filter(
            usuario=request.user,
            alias=alias_tarjeta
        ).first()
        
        if metodo_existente:
            # Actualizar el existente en lugar de crear duplicado
            datos_encriptados = encrypt_card_data_full(...)
            metodo_existente.datos_encriptados = datos_encriptados
            metodo_existente.ultimos_4_digitos = numero_tarjeta[-4:]
            metodo_existente.tipo_tarjeta = resultado_pago.get("tipo_tarjeta", "OTRA")
            metodo_existente.mes_expiracion = int(fecha_expiracion.split('/')[0])
            metodo_existente.anio_expiracion = int('20' + fecha_expiracion.split('/')[1])
            metodo_existente.nombre_titular = nombre_titular
            metodo_existente.activo = True
            metodo_existente.save()
            messages.success(request, f"✓ Método '{alias_tarjeta}' actualizado")
        else:
            # Crear nuevo
            MetodoPago.objects.create(...)
            messages.success(request, f"✓ Método '{alias_tarjeta}' guardado")
    except Exception as e:
        messages.warning(request, f"No se pudo guardar: {str(e)}")
```

### Solución 2: Prevenir doble submit en JavaScript
```javascript
// En asientos.js, línea 314:
let isSubmitting = false;  // Flag para prevenir doble submit

form.addEventListener("submit", function(e) {
    const accion = e.submitter?.value;
    
    if (accion === "reservar") {
        // Prevenir doble submit
        if (isSubmitting) {
            e.preventDefault();
            console.log("⚠️ Ya hay un pago en proceso");
            return false;
        }
        
        // Validaciones...
        
        // Marcar como procesando
        isSubmitting = true;
        
        // Desactivar botón
        btnConfirmPayment.disabled = true;
        
        // Si hay error de validación, reactivar
        if (error_de_validacion) {
            isSubmitting = false;
            btnConfirmPayment.disabled = false;
        }
    }
});
```

### Solución 3: Usar transacciones atómicas
```python
from django.db import transaction

# En views.py línea 733:
if not errores:
    try:
        with transaction.atomic():  # ✅ Todo o nada
            funcion = get_object_or_404(Funcion, id=funcion_id)
            # ... cálculos ...
            
            resultado_pago = simular_pago(...)
            
            # Solo crear Pago si fue exitoso
            if resultado_pago["exitoso"]:
                pago = Pago(estado_pago="APROBADO", ...)
                pago.save()
                
                reserva = Reserva(...)
                reserva.save()
                
                pago.reserva = reserva
                pago.save()
                
                # ... resto del flujo ...
            else:
                # NO crear nada si falla
                messages.error(request, resultado_pago.get('error_message'))
                return redirect(...)  # Salir sin guardar
    except Exception as e:
        # Si hay cualquier error, se revierte todo
        messages.error(request, f"Error: {str(e)}")
```

---

## 🧪 PLAN DE IMPLEMENTACIÓN

### Paso 1: Aplicar fix del unique key (Crítico)
- Modificar views.py línea 841
- Detectar y actualizar en lugar de crear duplicado

### Paso 2: Prevenir doble submit (Alta prioridad)
- Modificar asientos.js
- Agregar flag isSubmitting

### Paso 3: Refactorizar flujo de pago (Opcional pero recomendado)
- Usar transaction.atomic()
- Solo crear registros si pago exitoso
- Eliminar creación de Pago PENDIENTE/RECHAZADO

### Paso 4: Testing
1. Test unique key resuelto
2. Test doble submit prevenido
3. Test rollback en error

---

## 📝 NOTAS FINALES

**Prioridad de implementación:**
1. 🔴 Fix unique key (bloqueante)
2. 🟡 Prevenir doble submit (importante)
3. 🟢 Transacciones atómicas (mejora)
