console.log("🚀 Archivo asientos.js cargado");

document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ DOM cargado completamente");

    const form = document.getElementById("reserva-form");
    if (!form) {
        console.error("❌ No se encontró el formulario #reserva-form");
        return;
    }

    console.log("✅ Formulario encontrado");

    // Inputs que disparan recálculo automático
    const autoSubmitInputs = document.querySelectorAll(".auto-submit");
    console.log("📋 Total de elementos auto-submit:", autoSubmitInputs.length);

    if (autoSubmitInputs.length === 0) {
        console.warn("⚠️ No se encontraron elementos con clase .auto-submit");
        return;
    }

    autoSubmitInputs.forEach(function (input, index) {
        console.log("   [" + index + "] " + input.type + " - name: " + input.name);

        input.addEventListener("change", function () {
            console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            console.log("🔄 CAMBIO DETECTADO");
            console.log("   Tipo:", this.type);
            console.log("   Name:", this.name);
            console.log("   Value:", this.value);

            // Crear objeto con los datos del formulario
            const formData = new FormData(form);
            formData.append("accion", "recalcular");

            // Enviar vía fetch al backend
            fetch(form.action, {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
                .then(response => response.json())
                .then(data => {
                    console.log("✅ Respuesta AJAX recibida:", data);

                    // Actualizar resumen dinámicamente
                    const seatsDiv = document.querySelector(".selected-seats");
                    if (seatsDiv) {
                        seatsDiv.textContent = data.asientos.length > 0
                            ? data.asientos.join(", ")
                            : "Ningún asiento seleccionado";
                    }

                    const ticketCount = document.querySelector(".ticket-counter span:last-child");
                    if (ticketCount) ticketCount.textContent = data.cantidad_boletos;

                    const formatoDisplay = document.querySelector("#formato-display");
                    if (formatoDisplay) formatoDisplay.textContent = data.formato;

                    const precioBoletoDisplay = document.querySelector("#precio-boleto-display");
                    if (precioBoletoDisplay) precioBoletoDisplay.textContent = `$${data.precio_boleto.toFixed(2)}`;

                    const subtotalDisplay = document.querySelector("#subtotal-display");
                    if (subtotalDisplay) subtotalDisplay.textContent = `$${data.subtotal.toFixed(2)}`;

                    const totalPrice = document.querySelector("#total-price");
                    if (totalPrice) totalPrice.textContent = `Total: $${data.total.toFixed(2)}`;

                    const discountRow = document.getElementById("discount-row");
                    if (discountRow) {
                        if (data.descuento > 0) {
                            discountRow.style.display = "flex";
                            document.getElementById("discount-percent-display").textContent = data.descuento;
                            document.getElementById("discount-amount-display").textContent = `-$${data.descuento_monto.toFixed(2)}`;
                        } else {
                            discountRow.style.display = "none";
                        }
                    }

                    // Actualizar monto en botón de pago
                    const btnAmount = document.querySelector(".btn-amount");
                    if (btnAmount) btnAmount.textContent = `$${data.total.toFixed(2)}`;
                })
                .catch(error => {
                    console.error("❌ Error en AJAX:", error);
                });
        });
    });

    console.log("✅ Event listeners configurados correctamente");
});

// ═══════════════════════════════════════════════════════════════
// SISTEMA DE VALIDACIÓN DE PAGO - PBI-30
// ═══════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", function() {
    console.log("💳 Inicializando sistema de validación de pago");

    const numeroTarjetaInput = document.getElementById("numero_tarjeta");
    const fechaExpiracionInput = document.getElementById("fecha_expiracion");
    const cvvInput = document.getElementById("cvv");
    const nombreTitularInput = document.getElementById("nombre_titular");
    const btnConfirmPayment = document.getElementById("btn-confirm-payment");
    const processingIndicator = document.getElementById("processing-indicator");
    const form = document.getElementById("reserva-form");

    // Validar número de tarjeta
    if (numeroTarjetaInput) {
        numeroTarjetaInput.addEventListener("input", function(e) {
            let value = e.target.value.replace(/\s/g, '');
            let formattedValue = value.match(/.{1,4}/g)?.join(' ') || value;
            e.target.value = formattedValue;

            // Detectar tipo de tarjeta
            const cardIcon = document.getElementById("card-icon");
            if (value.startsWith('4')) {
                cardIcon.textContent = '💳'; // Visa
                cardIcon.className = 'card-icon visa';
            } else if (value.startsWith('5')) {
                cardIcon.textContent = '💳'; // Mastercard
                cardIcon.className = 'card-icon mastercard';
            } else if (value.startsWith('3')) {
                cardIcon.textContent = '💳'; // Amex
                cardIcon.className = 'card-icon amex';
            } else {
                cardIcon.textContent = '💳';
                cardIcon.className = 'card-icon';
            }

            // Validación
            validarNumeroTarjeta(value);
        });

        numeroTarjetaInput.addEventListener("blur", function() {
            const value = this.value.replace(/\s/g, '');
            validarNumeroTarjeta(value);
        });
    }

    function validarNumeroTarjeta(numero) {
        const errorSpan = document.getElementById("error-numero-tarjeta");
        const input = document.getElementById("numero_tarjeta");

        if (numero.length === 0) {
            errorSpan.textContent = "";
            input.classList.remove("error", "valid");
            return false;
        }

        if (!/^\d+$/.test(numero)) {
            errorSpan.textContent = "Solo se permiten números";
            input.classList.add("error");
            input.classList.remove("valid");
            return false;
        }

        if (numero.length !== 15 && numero.length !== 16) {
            errorSpan.textContent = "El número debe tener 15 o 16 dígitos";
            input.classList.add("error");
            input.classList.remove("valid");
            return false;
        }

        errorSpan.textContent = "";
        input.classList.remove("error");
        input.classList.add("valid");
        return true;
    }

    // Validar fecha de expiración
    if (fechaExpiracionInput) {
        fechaExpiracionInput.addEventListener("input", function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 2) {
                value = value.slice(0, 2) + '/' + value.slice(2, 4);
            }
            e.target.value = value;
            validarFechaExpiracion(value);
        });

        fechaExpiracionInput.addEventListener("blur", function() {
            validarFechaExpiracion(this.value);
        });
    }

    function validarFechaExpiracion(fecha) {
        const errorSpan = document.getElementById("error-fecha-expiracion");
        const input = document.getElementById("fecha_expiracion");

        if (fecha.length === 0) {
            errorSpan.textContent = "";
            input.classList.remove("error", "valid");
            return false;
        }

        if (!/^\d{2}\/\d{2}$/.test(fecha)) {
            errorSpan.textContent = "Formato debe ser MM/YY";
            input.classList.add("error");
            input.classList.remove("valid");
            return false;
        }

        const [mes, anio] = fecha.split('/').map(Number);
        if (mes < 1 || mes > 12) {
            errorSpan.textContent = "Mes inválido (01-12)";
            input.classList.add("error");
            input.classList.remove("valid");
            return false;
        }

        const ahora = new Date();
        const anioActual = ahora.getFullYear() % 100;
        const mesActual = ahora.getMonth() + 1;

        if (anio < anioActual || (anio === anioActual && mes < mesActual)) {
            errorSpan.textContent = "Tarjeta vencida";
            input.classList.add("error");
            input.classList.remove("valid");
            return false;
        }

        errorSpan.textContent = "";
        input.classList.remove("error");
        input.classList.add("valid");
        return true;
    }

    // Validar CVV
    if (cvvInput) {
        cvvInput.addEventListener("input", function(e) {
            let value = e.target.value.replace(/\D/g, '');
            e.target.value = value.slice(0, 4);
            validarCVV(value);
        });

        cvvInput.addEventListener("blur", function() {
            validarCVV(this.value);
        });
    }

    function validarCVV(cvv) {
        const errorSpan = document.getElementById("error-cvv");
        const input = document.getElementById("cvv");

        if (cvv.length === 0) {
            errorSpan.textContent = "";
            input.classList.remove("error", "valid");
            return false;
        }

        if (!/^\d{3,4}$/.test(cvv)) {
            errorSpan.textContent = "CVV debe tener 3 o 4 dígitos";
            input.classList.add("error");
            input.classList.remove("valid");
            return false;
        }

        errorSpan.textContent = "";
        input.classList.remove("error");
        input.classList.add("valid");
        return true;
    }

    // Validar nombre del titular
    if (nombreTitularInput) {
        nombreTitularInput.addEventListener("input", function() {
            this.value = this.value.toUpperCase();
        });

        nombreTitularInput.addEventListener("blur", function() {
            validarNombreTitular(this.value);
        });
    }

    function validarNombreTitular(nombre) {
        const errorSpan = document.getElementById("error-nombre-titular");
        const input = document.getElementById("nombre_titular");

        if (nombre.length === 0) {
            errorSpan.textContent = "";
            input.classList.remove("error", "valid");
            return false;
        }

        if (nombre.length < 3) {
            errorSpan.textContent = "Nombre muy corto";
            input.classList.add("error");
            input.classList.remove("valid");
            return false;
        }

        errorSpan.textContent = "";
        input.classList.remove("error");
        input.classList.add("valid");
        return true;
    }

    // Validación completa del formulario al enviar
    if (form) {
        form.addEventListener("submit", function(e) {
            const accion = e.submitter?.value;
            
            // Solo validar pago si la acción es "reservar"
            if (accion === "reservar") {
                // Verificar si se está usando un método guardado o nueva tarjeta
                const usandoMetodoGuardado = document.querySelector('input[name="usar_metodo_guardado"]:checked');
                const pagarConNuevaTarjeta = document.querySelector('#nueva-tarjeta:checked');
                
                // Si se está usando un método guardado, validar solo el CVV del método guardado
                if (usandoMetodoGuardado && !pagarConNuevaTarjeta) {
                    const cvvGuardadoInput = document.getElementById('saved-method-cvv');
                    if (cvvGuardadoInput) {
                        const cvvGuardado = cvvGuardadoInput.value.trim();
                        if (!cvvGuardado || cvvGuardado.length < 3 || cvvGuardado.length > 4 || !/^\d+$/.test(cvvGuardado)) {
                            e.preventDefault();
                            alert("⚠️ Por favor ingresa un CVV válido para tu tarjeta guardada");
                            return false;
                        }
                    }
                } else {
                    // Si se está pagando con nueva tarjeta, validar todos los campos
                    const numeroValido = validarNumeroTarjeta(numeroTarjetaInput.value.replace(/\s/g, ''));
                    const fechaValida = validarFechaExpiracion(fechaExpiracionInput.value);
                    const cvvValido = validarCVV(cvvInput.value);
                    const nombreValido = validarNombreTitular(nombreTitularInput.value);

                    if (!numeroValido || !fechaValida || !cvvValido || !nombreValido) {
                        e.preventDefault();
                        alert("⚠️ Por favor completa correctamente todos los datos de la tarjeta");
                        return false;
                    }
                }

                // Mostrar indicador de procesamiento
                if (btnConfirmPayment && processingIndicator) {
                    btnConfirmPayment.disabled = true;
                    btnConfirmPayment.textContent = "Procesando...";
                    processingIndicator.style.display = "flex";
                }
            }
        });
    }

    console.log("✅ Sistema de validación de pago inicializado");
});

// ═══════════════════════════════════════════════════════════════
// TOGGLE DE MÉTODOS DE PAGO (GUARDADOS vs NUEVA TARJETA) - PBI-30
// ═══════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", function() {
    console.log("🔄 Inicializando toggle de métodos de pago");

    const paymentRadios = document.querySelectorAll('input[name="usar_metodo_guardado"]');
    const newCardForm = document.getElementById("new-card-form");
    const savedMethodCvv = document.getElementById("saved-method-cvv");
    const guardarTarjetaCheckbox = document.getElementById("guardar_tarjeta");
    const aliasInput = document.getElementById("alias-input");

    if (paymentRadios.length === 0) {
        console.log("ℹ️ No hay métodos de pago guardados para este usuario");
        return;
    }

    // Función para actualizar la visibilidad de los formularios
    function updatePaymentForms() {
        const selectedRadio = document.querySelector('input[name="usar_metodo_guardado"]:checked');
        
        if (!selectedRadio) {
            console.warn("⚠️ No hay radio seleccionado");
            return;
        }

        const selectedValue = selectedRadio.value;
        console.log("💳 Método de pago seleccionado:", selectedValue);

        if (selectedValue === "false") {
            // Mostrar formulario de nueva tarjeta
            if (newCardForm) {
                newCardForm.style.display = "block";
                const inputs = newCardForm.querySelectorAll('input[type="text"]');
                inputs.forEach(input => input.removeAttribute('disabled'));
            }
            if (savedMethodCvv) {
                savedMethodCvv.style.display = "none";
                const cvvGuardadoInput = document.getElementById("cvv_guardado");
                if (cvvGuardadoInput) {
                    cvvGuardadoInput.setAttribute('disabled', 'disabled');
                    cvvGuardadoInput.value = '';
                }
            }
        } else {
            // Mostrar solo campo CVV para método guardado
            if (newCardForm) {
                newCardForm.style.display = "none";
                const inputs = newCardForm.querySelectorAll('input[type="text"]');
                inputs.forEach(input => input.setAttribute('disabled', 'disabled'));
            }
            if (savedMethodCvv) {
                savedMethodCvv.style.display = "block";
                const cvvGuardadoInput = document.getElementById("cvv_guardado");
                if (cvvGuardadoInput) {
                    cvvGuardadoInput.removeAttribute('disabled');
                    cvvGuardadoInput.focus();
                }
            }
        }
    }

    // Agregar event listeners a los radios
    paymentRadios.forEach(radio => radio.addEventListener("change", updatePaymentForms));

    // Toggle de campo alias al marcar "guardar tarjeta"
    if (guardarTarjetaCheckbox && aliasInput) {
        guardarTarjetaCheckbox.addEventListener("change", function() {
            if (this.checked) {
                aliasInput.style.display = "block";
                const aliasInputField = document.getElementById("alias_tarjeta");
                if (aliasInputField) aliasInputField.focus();
            } else {
                aliasInput.style.display = "none";
                const aliasInputField = document.getElementById("alias_tarjeta");
                if (aliasInputField) aliasInputField.value = '';
            }
        });
    }

    // Validación del CVV guardado
    const cvvGuardadoInput = document.getElementById("cvv_guardado");
    if (cvvGuardadoInput) {
        cvvGuardadoInput.addEventListener("input", function(e) {
            this.value = this.value.replace(/\D/g, '');
            if (this.value.length > 4) this.value = this.value.substring(0, 4);

            const errorSpan = document.getElementById("error-cvv-guardado");
            if (this.value.length >= 3) {
                this.classList.remove("error");
                this.classList.add("valid");
                if (errorSpan) errorSpan.textContent = "";
            } else {
                this.classList.remove("valid");
                if (this.value.length > 0) {
                    this.classList.add("error");
                    if (errorSpan) errorSpan.textContent = "CVV debe tener 3-4 dígitos";
                }
            }
        });
    }

    // Ejecutar al cargar
    updatePaymentForms();
    console.log("✅ Toggle de métodos de pago inicializado");
});
