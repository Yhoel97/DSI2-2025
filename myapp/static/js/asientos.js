// Variables globales
let selectedSeats = [];
const precioBase = 3.50;
let descuentoPorcentaje = parseFloat(document.getElementById('descuento_porcentaje_actual').value) || 0;
const STORAGE_KEY = `formData_${PELICULA_ID}`;
const SCROLL_KEY = `scrollPos_${PELICULA_ID}`;

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    inicializarEventListeners();
    cargarDatosGuardados();
    updateSummary();
});

function inicializarEventListeners() {
    // Event listeners para asientos
    document.querySelectorAll('.seat.available').forEach(seat => {
        seat.addEventListener('click', manejarClickAsiento);
    });

    // Event listeners para formato
    document.querySelectorAll('input[name="formato"]').forEach(radio => {
        radio.addEventListener('change', updateSummary);
    });

    // Event listener para combo
    document.getElementById('combo').addEventListener('change', actualizarAsientos);

    // Event listener para cupón
    document.getElementById('btn-aplicar-cupon').addEventListener('click', aplicarCupon);
}

function manejarClickAsiento(event) {
    const seat = event.currentTarget;
    const seatNumber = seat.getAttribute('data-seat');
    
    if (seat.classList.contains('selected')) {
        seat.classList.remove('selected');
        selectedSeats = selectedSeats.filter(s => s !== seatNumber);
    } else {
        seat.classList.add('selected');
        selectedSeats.push(seatNumber);
    }
    updateSummary();
}

function updateSummary() {
    const selectedSeatsElement = document.getElementById('selected-seats');
    const ticketCountElement = document.getElementById('ticket-count');
    const asientosInput = document.getElementById('asientos');

    const subtotalDisplay = document.getElementById('subtotal-display');
    const discountPercentDisplay = document.getElementById('discount-percent-display');
    const discountAmountDisplay = document.getElementById('discount-amount-display');
    const discountRow = document.getElementById('discount-row');
    const totalPriceElement = document.getElementById('total-price');

    // Actualizar asientos seleccionados
    selectedSeatsElement.textContent = selectedSeats.length > 0 ? selectedSeats.join(', ') : 'Ningún asiento seleccionado';
    ticketCountElement.textContent = selectedSeats.length;

    // Calcular precios
    const formatoSeleccionado = document.querySelector('input[name="formato"]:checked').value;
    let precioPorBoleto = precioBase;
    if (formatoSeleccionado === '3D') precioPorBoleto = 4.50;
    if (formatoSeleccionado === 'IMAX') precioPorBoleto = 6.00;

    // Cálculo Subtotal
    let subtotal = selectedSeats.length * precioPorBoleto;
    
    // Cálculo Descuento
    let montoDescuento = subtotal * (descuentoPorcentaje / 100);
    
    // Cálculo Total Final
    let totalFinal = subtotal - montoDescuento;

    // Actualizar displays
    subtotalDisplay.textContent = `$${subtotal.toFixed(2)}`;
    discountPercentDisplay.textContent = descuentoPorcentaje.toFixed(0);
    discountAmountDisplay.textContent = `-$${montoDescuento.toFixed(2)}`;
    totalPriceElement.textContent = `Total: $${totalFinal.toFixed(2)}`;
    
    // Ocultar la fila de descuento si no hay descuento
    discountRow.style.display = descuentoPorcentaje > 0 ? 'flex' : 'none';
    
    // Actualizar campo hidden de asientos
    asientosInput.value = selectedSeats.join(',');
}

function actualizarAsientos() {
    const combo = document.getElementById('combo').value;
    
    // Guardar datos del formulario en localStorage
    const formData = {};
    document.querySelectorAll('#reserva-form input, #reserva-form select').forEach(el => {
        if (el.type === 'radio') {
            if (el.checked) formData[el.name] = el.value;
        } else {
            formData[el.name] = el.value;
        }
    });
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(formData));
    localStorage.setItem(SCROLL_KEY, window.scrollY);
    
    // Redirigir con el nuevo combo
    window.location.href = `?combo=${encodeURIComponent(combo)}`;
}

function cargarDatosGuardados() {
    if (LIMPIAR_FORM) {
        localStorage.removeItem(STORAGE_KEY);
        localStorage.removeItem(SCROLL_KEY);
    } else {
        const savedData = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
        
        for (const name in savedData) {
            const el = document.querySelector(`[name="${name}"]`);
            if (el) {
                if (el.type === 'radio') {
                    if (el.value === savedData[name]) el.checked = true;
                } else {
                    el.value = savedData[name];
                }
            }
        }
        
        const scrollPos = localStorage.getItem(SCROLL_KEY);
        if (scrollPos) {
            window.scrollTo(0, parseInt(scrollPos));
            localStorage.removeItem(SCROLL_KEY);
        }
    }
}

async function aplicarCupon() {
    const codigo = document.getElementById('codigo_cupon').value;
    const cuponMessageElement = document.getElementById('cupon-message');

    if (codigo.length === 0) {
        cuponMessageElement.textContent = "Ingresa un código.";
        cuponMessageElement.style.color = 'orange';
        return;
    }

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    try {
        const response = await fetch(APLICAR_DESCUENTO_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken
            },
            body: `codigo=${codigo}`
        });

        const data = await response.json();

        cuponMessageElement.textContent = data.mensaje;
        
        if (data.success) {
            descuentoPorcentaje = data.descuento_porcentaje;
            cuponMessageElement.style.color = 'green';
            
            // Actualizar el campo hidden del descuento
            document.getElementById('descuento_porcentaje_actual').value = descuentoPorcentaje;
            
        } else {
            // Si falla, el descuento es cero
            descuentoPorcentaje = 0;
            document.getElementById('descuento_porcentaje_actual').value = 0;
            cuponMessageElement.style.color = 'red';
        }

        updateSummary();
        
    } catch (error) {
        cuponMessageElement.textContent = 'Error de conexión con el servidor.';
        cuponMessageElement.style.color = 'red';
        descuentoPorcentaje = 0;
        document.getElementById('descuento_porcentaje_actual').value = 0;
        updateSummary();
    }
}