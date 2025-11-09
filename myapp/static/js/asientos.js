// ============================================
// 🎬 SISTEMA DE SELECCIÓN DE ASIENTOS - CINEDOT
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🎬 Sistema de asientos inicializado');

    const form = document.getElementById('reserva-form');
    const seatCheckboxes = document.querySelectorAll('.seat-checkbox');
    const funcionRadios = document.querySelectorAll('.funcion-radio');
    const btnConfirm = document.getElementById('btn-confirm-payment');
    const processingIndicator = document.getElementById('processing-indicator');

    // ============================================
    // 📊 ACTUALIZAR RESUMEN (SIN RECARGAR)
    // ============================================
    function actualizarResumen() {
        const asientosSeleccionados = Array.from(seatCheckboxes)
            .filter(cb => cb.checked && !cb.disabled)
            .map(cb => cb.value);

        const funcionSeleccionada = document.querySelector('input[name="funcion_id"]:checked');
        const funcionId = funcionSeleccionada ? funcionSeleccionada.value : null;

        console.log('📊 Actualizando resumen:', {
            asientos: asientosSeleccionados,
            funcion: funcionId
        });

        // Actualizar UI inmediatamente
        const selectedSeatsDiv = document.getElementById('selected-seats');
        if (selectedSeatsDiv) {
            selectedSeatsDiv.textContent = 
                asientosSeleccionados.length > 0 ? asientosSeleccionados.join(', ') : 'Ningún asiento seleccionado';
        }

        const ticketCount = document.getElementById('ticket-count');
        if (ticketCount) {
            ticketCount.textContent = asientosSeleccionados.length;
        }

        // Enviar AJAX para calcular precios y obtener asientos ocupados
        if (funcionId) {
            enviarAjaxActualizacion(asientosSeleccionados, funcionId);
        } else {
            // Reset precios si no hay función seleccionada
            resetearPrecios();
        }
    }

    // ============================================
    // 🔄 RESETEAR PRECIOS
    // ============================================
    function resetearPrecios() {
        const elementos = {
            'subtotal-display': '$0.00',
            'total-price': 'Total: $0.00'
        };

        Object.entries(elementos).forEach(([id, valor]) => {
            const elem = document.getElementById(id);
            if (elem) elem.textContent = valor;
        });

        if (btnConfirm) {
            const btnAmount = btnConfirm.querySelector('.btn-amount');
            if (btnAmount) btnAmount.textContent = '$0.00';
        }

        const discountRow = document.getElementById('discount-row');
        if (discountRow) {
            discountRow.style.display = 'none';
        }
    }

    // ============================================
    // 📡 AJAX: ACTUALIZAR PRECIOS Y ASIENTOS OCUPADOS
    // ============================================
    function enviarAjaxActualizacion(asientos, funcionId) {
        const formData = new FormData(form);
        
        // ✅ CRÍTICO: Limpiar y re-agregar asientos seleccionados
        formData.delete('asientos_list');
        asientos.forEach(asiento => {
            formData.append('asientos_list', asiento);
        });

        // Asegurar que se envía la función correcta
        formData.set('funcion_id', funcionId);

        console.log('📡 Enviando AJAX - Función:', funcionId, 'Asientos:', asientos);

        fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('✅ Respuesta AJAX recibida:', data);

            // Actualizar formato y precios
            actualizarPreciosUI(data);

            // ✅ ACTUALIZAR ASIENTOS OCUPADOS DINÁMICAMENTE
            if (data.asientos_ocupados) {
                console.log('🔄 Actualizando asientos ocupados:', data.asientos_ocupados);
                actualizarAsientosOcupados(data.asientos_ocupados);
            }
        })
        .catch(error => {
            console.error('❌ Error en AJAX:', error);
            // No mostrar alert para no interrumpir la experiencia
        });
    }

    // ============================================
    // 💰 ACTUALIZAR PRECIOS EN LA UI
    // ============================================
    function actualizarPreciosUI(data) {
        // Formato
        const formatoDisplay = document.getElementById('formato-display');
        if (formatoDisplay) {
            formatoDisplay.textContent = data.formato || '2D';
        }

        // Precio por boleto
        const precioBoletoDisplay = document.getElementById('precio-boleto-display');
        if (precioBoletoDisplay && data.precio_boleto !== undefined) {
            precioBoletoDisplay.textContent = `$${data.precio_boleto.toFixed(2)}`;
        }

        // Subtotal
        const subtotalDisplay = document.getElementById('subtotal-display');
        if (subtotalDisplay && data.subtotal !== undefined) {
            subtotalDisplay.textContent = `$${data.subtotal.toFixed(2)}`;
        }

        // Total
        const totalPrice = document.getElementById('total-price');
        if (totalPrice && data.total !== undefined) {
            totalPrice.textContent = `Total: $${data.total.toFixed(2)}`;
        }

        // Botón de pago
        if (btnConfirm && data.total !== undefined) {
            const btnAmount = btnConfirm.querySelector('.btn-amount');
            if (btnAmount) {
                btnAmount.textContent = `$${data.total.toFixed(2)}`;
            }
        }

        // Descuento
        const discountRow = document.getElementById('discount-row');
        if (discountRow) {
            if (data.descuento > 0) {
                discountRow.style.display = 'flex';
                const descuentoLabel = discountRow.querySelector('span:first-child');
                const descuentoMonto = discountRow.querySelector('span:last-child');
                
                if (descuentoLabel) {
                    descuentoLabel.textContent = `Descuento (${data.descuento}%):`;
                }
                if (descuentoMonto && data.descuento_monto !== undefined) {
                    descuentoMonto.textContent = `-$${data.descuento_monto.toFixed(2)}`;
                }
            } else {
                discountRow.style.display = 'none';
            }
        }
    }

    // ============================================
    // 🔄 ACTUALIZAR ASIENTOS OCUPADOS (DINÁMICO)
    // ============================================
    function actualizarAsientosOcupados(asientosOcupados) {
        const asientosOcupadosSet = new Set(asientosOcupados);
        
        seatCheckboxes.forEach(checkbox => {
            const asiento = checkbox.value;
            const seatDiv = checkbox.nextElementSibling;

            if (!seatDiv) return;

            if (asientosOcupadosSet.has(asiento)) {
                // Marcar como ocupado
                if (!checkbox.disabled) {
                    console.log(`🔒 Bloqueando asiento: ${asiento}`);
                }
                checkbox.disabled = true;
                checkbox.checked = false;
                seatDiv.classList.remove('available', 'selected');
                seatDiv.classList.add('reserved');
            } else if (checkbox.disabled && !checkbox.checked) {
                // Liberar si ya no está ocupado y no está seleccionado
                console.log(`🔓 Liberando asiento: ${asiento}`);
                checkbox.disabled = false;
                seatDiv.classList.remove('reserved', 'selected');
                seatDiv.classList.add('available');
            }
        });

        // Recalcular resumen después de actualizar asientos
        actualizarResumen();
    }

    // ============================================
    // 🎯 EVENTOS: SELECCIÓN DE ASIENTOS
    // ============================================
    seatCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            const seatDiv = e.target.nextElementSibling;
            
            if (!seatDiv) return;
            
            if (e.target.checked) {
                seatDiv.classList.remove('available');
                seatDiv.classList.add('selected');
                console.log(`✅ Asiento ${e.target.value} seleccionado`);
            } else {
                seatDiv.classList.remove('selected');
                seatDiv.classList.add('available');
                console.log(`❌ Asiento ${e.target.value} deseleccionado`);
            }

            // Actualizar resumen en tiempo real
            actualizarResumen();
        });
    });

    // ============================================
    // 🎯 EVENTOS: CAMBIO DE FUNCIÓN (SIN RECARGAR PÁGINA)
    // ============================================
    funcionRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            console.log('🔄 Función cambiada a ID:', radio.value);
            console.log('📍 Formato:', radio.dataset.formato, 'Precio:', radio.dataset.precio);
            
            // Deseleccionar todos los asientos (pero no los deshabilitados)
            seatCheckboxes.forEach(cb => {
                if (!cb.disabled && cb.checked) {
                    cb.checked = false;
                    const seatDiv = cb.nextElementSibling;
                    if (seatDiv) {
                        seatDiv.classList.remove('selected');
                        seatDiv.classList.add('available');
                    }
                }
            });

            // Actualizar resumen (esto cargará los nuevos asientos ocupados vía AJAX)
            actualizarResumen();
        });
    });

    // ============================================
    // 💳 GESTIÓN DE MÉTODOS DE PAGO
    // ============================================
    const paymentRadios = document.querySelectorAll('.payment-radio');
    const newCardForm = document.getElementById('new-card-form');
    const savedMethodCvv = document.getElementById('saved-method-cvv');
    const guardarTarjetaCheckbox = document.getElementById('guardar_tarjeta');
    const aliasInput = document.getElementById('alias-input');

    function togglePaymentForms() {
        const selectedRadio = document.querySelector('.payment-radio:checked');
        const isNewCard = selectedRadio && selectedRadio.value === 'false';

        if (newCardForm) {
            newCardForm.style.display = isNewCard ? 'block' : 'none';
            
            // Limpiar campos si no es nueva tarjeta
            if (!isNewCard) {
                const inputs = newCardForm.querySelectorAll('input');
                inputs.forEach(input => {
                    if (input.type !== 'checkbox') {
                        input.removeAttribute('required');
                    }
                });
            }
        }

        if (savedMethodCvv) {
            savedMethodCvv.style.display = isNewCard ? 'none' : 'block';
        }

        console.log('💳 Método de pago:', isNewCard ? 'Nueva tarjeta' : 'Método guardado');
    }

    if (paymentRadios.length > 0) {
        paymentRadios.forEach(radio => {
            radio.addEventListener('change', togglePaymentForms);
        });
        togglePaymentForms(); // Inicializar estado
    }

    if (guardarTarjetaCheckbox && aliasInput) {
        guardarTarjetaCheckbox.addEventListener('change', (e) => {
            aliasInput.style.display = e.target.checked ? 'block' : 'none';
            const aliasInputField = document.getElementById('alias_tarjeta');
            if (aliasInputField) {
                if (e.target.checked) {
                    aliasInputField.setAttribute('required', 'required');
                } else {
                    aliasInputField.removeAttribute('required');
                }
            }
        });
    }

    // ============================================
    // 🎨 FORMATO DE NÚMERO DE TARJETA
    // ============================================
    const numeroTarjetaInput = document.getElementById('numero_tarjeta');
    const cardIcon = document.getElementById('card-icon');

    if (numeroTarjetaInput) {
        numeroTarjetaInput.addEventListener('input', (e) => {
            // Solo números
            let valor = e.target.value.replace(/\s/g, '').replace(/\D/g, '');
            
            // Limitar a 16 dígitos
            valor = valor.substring(0, 16);
            
            // Formatear con espacios cada 4 dígitos
            let formatted = valor.match(/.{1,4}/g)?.join(' ') || valor;
            e.target.value = formatted;

            // Detectar tipo de tarjeta
            if (cardIcon) {
                if (valor.startsWith('4')) {
                    cardIcon.textContent = '💳 Visa';
                } else if (valor.startsWith('5')) {
                    cardIcon.textContent = '💳 Mastercard';
                } else if (valor.startsWith('37') || valor.startsWith('34')) {
                    cardIcon.textContent = '💳 Amex';
                } else {
                    cardIcon.textContent = '💳';
                }
            }
        });
    }

    // ============================================
    // 🎨 FORMATO DE FECHA DE EXPIRACIÓN
    // ============================================
    const fechaExpInput = document.getElementById('fecha_expiracion');
    if (fechaExpInput) {
        fechaExpInput.addEventListener('input', (e) => {
            let valor = e.target.value.replace(/\D/g, '');
            
            if (valor.length >= 2) {
                let mes = valor.substring(0, 2);
                let anio = valor.substring(2, 4);
                
                // Validar mes (01-12)
                if (parseInt(mes) > 12) {
                    mes = '12';
                }
                if (parseInt(mes) === 0) {
                    mes = '01';
                }
                
                valor = mes + (anio ? '/' + anio : '');
            }
            
            e.target.value = valor;
        });

        // Formatear al pegar
        fechaExpInput.addEventListener('paste', (e) => {
            setTimeout(() => {
                let valor = e.target.value.replace(/\D/g, '');
                if (valor.length >= 2) {
                    valor = valor.substring(0, 2) + '/' + valor.substring(2, 4);
                }
                e.target.value = valor;
            }, 10);
        });
    }

    // ============================================
    // 🎨 VALIDAR CVV (SOLO NÚMEROS)
    // ============================================
    const cvvInputs = document.querySelectorAll('#cvv, #cvv_guardado');
    cvvInputs.forEach(input => {
        if (input) {
            input.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/\D/g, '');
            });
        }
    });

    // ============================================
    // ✅ VALIDACIÓN ANTES DE ENVIAR (EVENTO SUBMIT)
    // ============================================
    if (form) {
        form.addEventListener('submit', (e) => {
            // Solo validar si la acción es "reservar" (no para "recalcular" cupón)
            const submitButton = document.activeElement;
            if (submitButton && submitButton.value === 'recalcular') {
                // Permitir recalcular sin validaciones completas
                return true;
            }

            console.log('🔍 Validando formulario antes de envío...');

            // Validar que haya asientos seleccionados
            const asientosSeleccionados = Array.from(seatCheckboxes)
                .filter(cb => cb.checked && !cb.disabled);

            if (asientosSeleccionados.length === 0) {
                e.preventDefault();
                alert('⚠️ Por favor selecciona al menos un asiento antes de continuar.');
                return false;
            }

            console.log(`✅ ${asientosSeleccionados.length} asiento(s) seleccionado(s)`);

            // Validar datos del cliente
            const nombreCliente = document.getElementById('nombre_cliente');
            const apellidoCliente = document.getElementById('apellido_cliente');
            const emailCliente = document.getElementById('email');

            if (!nombreCliente || !nombreCliente.value.trim()) {
                e.preventDefault();
                alert('⚠️ Por favor ingresa tu nombre');
                nombreCliente?.focus();
                return false;
            }

            if (!apellidoCliente || !apellidoCliente.value.trim()) {
                e.preventDefault();
                alert('⚠️ Por favor ingresa tu apellido');
                apellidoCliente?.focus();
                return false;
            }

            if (!emailCliente || !emailCliente.value.trim() || !emailCliente.value.includes('@')) {
                e.preventDefault();
                alert('⚠️ Por favor ingresa un email válido');
                emailCliente?.focus();
                return false;
            }

            // Validar método de pago
            const selectedPayment = document.querySelector('.payment-radio:checked');
            if (!selectedPayment) {
                e.preventDefault();
                alert('⚠️ Por favor selecciona un método de pago');
                return false;
            }

            const isNewCard = selectedPayment.value === 'false';

            if (isNewCard) {
                // Validar nueva tarjeta
                const numeroTarjeta = document.getElementById('numero_tarjeta');
                const nombreTitular = document.getElementById('nombre_titular');
                const fechaExp = document.getElementById('fecha_expiracion');
                const cvv = document.getElementById('cvv');

                if (!numeroTarjeta || !numeroTarjeta.value.replace(/\s/g, '')) {
                    e.preventDefault();
                    alert('⚠️ Por favor ingresa el número de tarjeta');
                    numeroTarjeta?.focus();
                    return false;
                }

                const numeroLimpio = numeroTarjeta.value.replace(/\s/g, '');
                if (numeroLimpio.length < 13) {
                    e.preventDefault();
                    alert('⚠️ El número de tarjeta debe tener al menos 13 dígitos');
                    numeroTarjeta?.focus();
                    return false;
                }

                if (!nombreTitular || !nombreTitular.value.trim()) {
                    e.preventDefault();
                    alert('⚠️ Por favor ingresa el nombre del titular');
                    nombreTitular?.focus();
                    return false;
                }

                if (!fechaExp || !fechaExp.value || !fechaExp.value.includes('/')) {
                    e.preventDefault();
                    alert('⚠️ Por favor ingresa la fecha de expiración (MM/YY)');
                    fechaExp?.focus();
                    return false;
                }

                if (!cvv || !cvv.value || cvv.value.length < 3) {
                    e.preventDefault();
                    alert('⚠️ Por favor ingresa un CVV válido (3-4 dígitos)');
                    cvv?.focus();
                    return false;
                }

                // Si quiere guardar la tarjeta, validar alias
                const guardarTarjeta = document.getElementById('guardar_tarjeta');
                const aliasTarjeta = document.getElementById('alias_tarjeta');
                if (guardarTarjeta && guardarTarjeta.checked) {
                    if (!aliasTarjeta || !aliasTarjeta.value.trim()) {
                        e.preventDefault();
                        alert('⚠️ Por favor ingresa un nombre para guardar esta tarjeta');
                        aliasTarjeta?.focus();
                        return false;
                    }
                }
            } else {
                // Validar CVV de método guardado
                const cvvGuardado = document.getElementById('cvv_guardado');
                if (!cvvGuardado || !cvvGuardado.value || cvvGuardado.value.length < 3) {
                    e.preventDefault();
                    alert('⚠️ Por favor ingresa el CVV de tu tarjeta guardada (3-4 dígitos)');
                    cvvGuardado?.focus();
                    return false;
                }
            }

            // ✅ TODO VALIDADO - Mostrar indicador de procesamiento
            console.log('✅ Formulario validado correctamente');
            console.log('📋 Asientos finales:', asientosSeleccionados.map(cb => cb.value));
            console.log('🚀 Enviando formulario al servidor...');
            
            // Mostrar indicador de procesamiento DESPUÉS de validar
            if (processingIndicator) {
                processingIndicator.style.display = 'flex';
            }
            
            // Deshabilitar botón DESPUÉS de que el navegador haya iniciado el submit
            setTimeout(() => {
                if (btnConfirm) {
                    btnConfirm.disabled = true;
                    btnConfirm.style.opacity = '0.6';
                    btnConfirm.style.cursor = 'not-allowed';
                }
            }, 0);

            // Permitir que el formulario se envíe normalmente
            return true;
        });
    }

    // ============================================
    // 🔄 INICIALIZACIÓN
    // ============================================
    console.log('📊 Estado inicial:');
    console.log('  - Asientos en DOM:', seatCheckboxes.length);
    console.log('  - Funciones disponibles:', funcionRadios.length);
    console.log('  - Métodos de pago:', paymentRadios.length);

    // Actualizar resumen inicial
    actualizarResumen();

    // Inicializar formulario de pago
    if (paymentRadios.length > 0) {
        togglePaymentForms();
    }

    console.log('✅ Sistema de asientos completamente inicializado');
});