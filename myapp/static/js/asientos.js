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

            // Si cambiamos de función, necesitamos actualizar los asientos ocupados
            const esCambioFuncion = this.name === "funcion_id";

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

                    // Si cambiamos de función, actualizar asientos ocupados
                    if (esCambioFuncion && data.asientos_ocupados) {
                        actualizarAsientosOcupados(data.asientos_ocupados);
                        // Limpiar selección actual
                        limpiarSeleccionAsientos();
                    }

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
                })
                .catch(error => {
                    console.error("❌ Error en AJAX:", error);
                });
        });
    });

    console.log("✅ Event listeners configurados correctamente");
});

/**
 * Actualiza visualmente los asientos ocupados en la interfaz
 */
function actualizarAsientosOcupados(asientosOcupados) {
    console.log("🔄 Actualizando asientos ocupados:", asientosOcupados);
    
    // Primero, quitar la clase 'reserved' de todos los asientos
    const todosLosAsientos = document.querySelectorAll(".seat");
    todosLosAsientos.forEach(seat => {
        seat.classList.remove("reserved");
        const checkbox = seat.closest(".seat-label")?.querySelector('input[type="checkbox"]');
        if (checkbox) {
            checkbox.disabled = false;
        }
    });

    // Luego, marcar como ocupados los que están en la lista
    asientosOcupados.forEach(asientoId => {
        const checkbox = document.querySelector(`input[type="checkbox"][value="${asientoId}"]`);
        if (checkbox) {
            const seat = checkbox.nextElementSibling;
            if (seat && seat.classList.contains("seat")) {
                seat.classList.add("reserved");
                checkbox.disabled = true;
                checkbox.checked = false; // Asegurar que no esté seleccionado
            }
        }
    });
}

/**
 * Limpia la selección actual de asientos
 */
function limpiarSeleccionAsientos() {
    console.log("🧹 Limpiando selección de asientos");
    const checkboxes = document.querySelectorAll('input[type="checkbox"][name="asientos_list"]');
    checkboxes.forEach(checkbox => {
        if (!checkbox.disabled) {
            checkbox.checked = false;
            const seat = checkbox.nextElementSibling;
            if (seat && seat.classList.contains("seat")) {
                seat.classList.remove("selected");
            }
        }
    });
}