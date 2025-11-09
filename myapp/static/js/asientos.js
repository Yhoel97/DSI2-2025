// ===== CONFIGURACIÓN INICIAL =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎬 Sistema de reservas cargado');
    
    // Elementos del DOM
    const form = document.getElementById('reserva-form');
    const btnConfirm = document.getElementById('btn-confirm-payment');
    const processingIndicator = document.getElementById('processing-indicator');
    
    // ===== ACTUALIZACIÓN DINÁMICA (AJAX) =====
    function enviarFormularioAjax() {
        const formData = new FormData(form);
        
        fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('📊 Datos recibidos:', data);
            actualizarUI(data);
        })
        .catch(error => {
            console.error('❌ Error en AJAX:', error);
        });
    }

    // ===== ACTUALIZAR INTERFAZ =====
    function actualizarUI(data) {
        // Actualizar asientos seleccionados
        const selectedSeatsDiv = document.getElementById('selected-seats');
        if (selectedSeatsDiv) {
            selectedSeatsDiv.textContent = data.asientos.length > 0 
                ? data.asientos.join(', ') 
                : 'Ningún asiento seleccionado';
        }

        // Actualizar contador de boletos
        const ticketCount = document.getElementById('ticket-count');
        if (ticketCount) {
            ticketCount.textContent = data.cantidad_boletos;
        }

        // Actualizar formato
        const formatoDisplay = document.getElementById('formato-display');
        if (formatoDisplay) {
            formatoDisplay.textContent = data.formato;
        }

        // Actualizar precio por boleto
        const precioBoletoDisplay = document.getElementById('precio-boleto-display');
        if (precioBoletoDisplay) {
            precioBoletoDisplay.textContent = `$${data.precio_boleto.toFixed(2)}`;
        }

        // Actualizar subtotal
        const subtotalDisplay = document.getElementById('subtotal-display');
        if (subtotalDisplay) {
            subtotalDisplay.textContent = `$${data.subtotal.toFixed(2)}`;
        }

        // Actualizar descuento
        const discountRow = document.getElementById('discount-row');
        if (data.descuento > 0) {
            if (discountRow) {
                discountRow.style.display = 'flex';
                const discountSpans = discountRow.querySelectorAll('span');
                if (discountSpans.length >= 2) {
                    discountSpans[0].textContent = `Descuento (${data.descuento}%):`;
                    discountSpans[1].textContent = `-$${data.descuento_monto.toFixed(2)}`;
                }
            }
        } else {
            if (discountRow) {
                discountRow.style.display = 'none';
            }
        }

        // Actualizar total
        const totalPrice = document.getElementById('total-price');
        if (totalPrice) {
            totalPrice.textContent = `Total: $${data.total.toFixed(2)}`;
        }

        // Actualizar monto en botón de pago
        const btnAmount = document.querySelector('.btn-amount');
        if (btnAmount) {
            btnAmount.textContent = `$${data.total.toFixed(2)}`;
        }

        // ===== ACTUALIZAR ASIENTOS OCUPADOS =====
        actualizarAsientosOcupados(data.asientos_ocupados || []);
    }

    // ===== FUNCIÓN CLAVE: Actualizar estado visual de los asientos =====
    function actualizarAsientosOcupados(asientosOcupados) {
        console.log('🔄 Actualizando asientos ocupados:', asientosOcupados);
        
        // Obtener todos los checkboxes de asientos
        const todosLosCheckboxes = document.querySelectorAll('input[name="asientos_list"]');
        
        todosLosCheckboxes.forEach(checkbox => {
            const asiento = checkbox.value;
            const seatDiv = checkbox.nextElementSibling;
            
            if (asientosOcupados.includes(asiento)) {
                // Asiento ocupado
                checkbox.disabled = true;
                checkbox.checked = false;
                seatDiv.classList.remove('available', 'selected');
                seatDiv.classList.add('reserved');
            } else {
                // Asiento disponible
                checkbox.disabled = false;
                seatDiv.classList.remove('reserved');
                
                if (checkbox.checked) {
                    seatDiv.classList.add('selected');
                    seatDiv.classList.remove('available');
                } else {
                    seatDiv.classList.add('available');
                    seatDiv.classList.remove('selected');
                }
            }
        });
    }

    // ===== EVENTO: Cambio en asientos =====
    const asientosCheckboxes = document.querySelectorAll('input[name="asientos_list"]');
    asientosCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const seatDiv = this.nextElementSibling;
            
            if (this.checked) {
                seatDiv.classList.add('selected');
                seatDiv.classList.remove('available');
            } else {
                seatDiv.classList.remove('selected');
                seatDiv.classList.add('available');
            }
            
            enviarFormularioAjax();
        });
    });

    // ===== EVENTO: Cambio de función (sala/horario) =====
    const funcionesRadios = document.querySelectorAll('input[name="funcion_id"]');
    funcionesRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            console.log('🎯 Cambio de función detectado:', this.value);
            
            // Desmarcar todos los asientos seleccionados
            asientosCheckboxes.forEach(checkbox => {
                if (checkbox.checked && !checkbox.disabled) {
                    checkbox.checked = false;
                    const seatDiv = checkbox.nextElementSibling;
                    seatDiv.classList.remove('selected');
                    seatDiv.classList.add('available');
                }
            });
            
            // Enviar formulario para obtener nuevos asientos ocupados
            enviarFormularioAjax();
        });
    });

    // ===== VALIDACIÓN Y ENVÍO DEL FORMULARIO =====
    form.addEventListener('submit', function(e) {
        const accion = e.submitter ? e.submitter.value : '';
        
        // Solo validar cuando sea "reservar"
        if (accion === 'reservar') {
            e.preventDefault();
            
            // Validar que haya asientos seleccionados
            const asientosSeleccionados = Array.from(asientosCheckboxes)
                .filter(cb => cb.checked && !cb.disabled);
            
            if (asientosSeleccionados.length === 0) {
                alert('⚠️ Por favor, selecciona al menos un asiento');
                return;
            }

            // Validar método de pago
            const usarMetodoGuardado = document.querySelector('input[name="usar_metodo_guardado"]:checked');
            
            if (usarMetodoGuardado && usarMetodoGuardado.value !== 'false') {
                // Validar CVV de método guardado
                const cvvGuardado = document.getElementById('cvv_guardado');
                if (!cvvGuardado || !cvvGuardado.value.trim()) {
                    alert('⚠️ Por favor, ingresa el CVV de tu tarjeta guardada');
                    cvvGuardado?.focus();
                    return;
                }
            } else {
                // Validar nueva tarjeta
                const numeroTarjeta = document.getElementById('numero_tarjeta');
                const nombreTitular = document.getElementById('nombre_titular');
                const fechaExpiracion = document.getElementById('fecha_expiracion');
                const cvv = document.getElementById('cvv');
                
                if (!numeroTarjeta?.value.trim()) {
                    alert('⚠️ Por favor, ingresa el número de tarjeta');
                    numeroTarjeta?.focus();
                    return;
                }
                
                if (!nombreTitular?.value.trim()) {
                    alert('⚠️ Por favor, ingresa el nombre del titular');
                    nombreTitular?.focus();
                    return;
                }
                
                if (!fechaExpiracion?.value.trim()) {
                    alert('⚠️ Por favor, ingresa la fecha de expiración');
                    fechaExpiracion?.focus();
                    return;
                }
                
                if (!cvv?.value.trim()) {
                    alert('⚠️ Por favor, ingresa el CVV');
                    cvv?.focus();
                    return;
                }
            }

            // Mostrar indicador de procesamiento
            if (btnConfirm) btnConfirm.disabled = true;
            if (processingIndicator) processingIndicator.style.display = 'flex';
            
            // Enviar formulario normalmente
            form.submit();
        }
    });

    // ===== MANEJO DE MÉTODOS DE PAGO =====
    const paymentRadios = document.querySelectorAll('input[name="usar_metodo_guardado"]');
    const savedMethodCvv = document.getElementById('saved-method-cvv');
    const newCardForm = document.getElementById('new-card-form');

    paymentRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.value === 'false') {
                // Nueva tarjeta
                if (savedMethodCvv) savedMethodCvv.style.display = 'none';
                if (newCardForm) newCardForm.style.display = 'block';
            } else {
                // Método guardado
                if (savedMethodCvv) savedMethodCvv.style.display = 'block';
                if (newCardForm) newCardForm.style.display = 'none';
            }
        });
    });

    // Inicializar estado de métodos de pago
    const selectedPaymentMethod = document.querySelector('input[name="usar_metodo_guardado"]:checked');
    if (selectedPaymentMethod) {
        if (selectedPaymentMethod.value === 'false') {
            if (savedMethodCvv) savedMethodCvv.style.display = 'none';
            if (newCardForm) newCardForm.style.display = 'block';
        } else {
            if (savedMethodCvv) savedMethodCvv.style.display = 'block';
            if (newCardForm) newCardForm.style.display = 'none';
        }
    }

    // ===== GUARDAR TARJETA =====
    const guardarTarjetaCheckbox = document.getElementById('guardar_tarjeta');
    const aliasInput = document.getElementById('alias-input');

    if (guardarTarjetaCheckbox) {
        guardarTarjetaCheckbox.addEventListener('change', function() {
            if (aliasInput) {
                aliasInput.style.display = this.checked ? 'block' : 'none';
            }
        });
    }

    // ===== FORMATEO DE INPUTS =====
    const numeroTarjetaInput = document.getElementById('numero_tarjeta');
    if (numeroTarjetaInput) {
        numeroTarjetaInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\s/g, '');
            let formattedValue = value.match(/.{1,4}/g)?.join(' ') || value;
            e.target.value = formattedValue;
            
            // Detectar tipo de tarjeta
            const cardIcon = document.getElementById('card-icon');
            if (cardIcon) {
                if (value.startsWith('4')) {
                    cardIcon.textContent = '💳'; // Visa
                } else if (value.startsWith('5')) {
                    cardIcon.textContent = '💳'; // Mastercard
                } else if (value.startsWith('3')) {
                    cardIcon.textContent = '💳'; // Amex
                } else {
                    cardIcon.textContent = '💳';
                }
            }
        });
    }

    const fechaExpiracionInput = document.getElementById('fecha_expiracion');
    if (fechaExpiracionInput) {
        fechaExpiracionInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 2) {
                value = value.slice(0, 2) + '/' + value.slice(2, 4);
            }
            e.target.value = value;
        });
    }

    const cvvInput = document.getElementById('cvv');
    if (cvvInput) {
        cvvInput.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '').slice(0, 4);
        });
    }

    const cvvGuardadoInput = document.getElementById('cvv_guardado');
    if (cvvGuardadoInput) {
        cvvGuardadoInput.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '').slice(0, 4);
        });
    }

    console.log('✅ Sistema de reservas inicializado correctamente');
});