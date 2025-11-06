// JavaScript para formulario de métodos de pago

document.addEventListener('DOMContentLoaded', function() {
    // Toggle entre campos de tarjeta y cuenta digital
    window.toggleCampos = function() {
        const tipoSeleccionado = document.querySelector('input[name="tipo"]:checked').value;
        const camposTarjeta = document.getElementById('camposTarjeta');
        const camposCuentaDigital = document.getElementById('camposCuentaDigital');

        if (tipoSeleccionado === 'TARJETA') {
            camposTarjeta.style.display = 'block';
            camposCuentaDigital.style.display = 'none';
            
            // Hacer campos de tarjeta requeridos
            document.getElementById('numero_tarjeta').required = true;
            document.getElementById('mes_expiracion').required = true;
            document.getElementById('anio_expiracion').required = true;
            document.getElementById('nombre_titular').required = true;
            
            // Remover requerido de cuenta digital
            if (document.getElementById('tipo_cuenta')) {
                document.getElementById('tipo_cuenta').required = false;
                document.getElementById('email_cuenta').required = false;
            }
        } else {
            camposTarjeta.style.display = 'none';
            camposCuentaDigital.style.display = 'block';
            
            // Remover requerido de tarjeta
            document.getElementById('numero_tarjeta').required = false;
            document.getElementById('mes_expiracion').required = false;
            document.getElementById('anio_expiracion').required = false;
            document.getElementById('nombre_titular').required = false;
            
            // Hacer campos de cuenta digital requeridos
            document.getElementById('tipo_cuenta').required = true;
            document.getElementById('email_cuenta').required = true;
        }
    };

    // Formatear número de tarjeta
    const numeroTarjetaInput = document.getElementById('numero_tarjeta');
    if (numeroTarjetaInput) {
        numeroTarjetaInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\s/g, '');
            let formattedValue = value.match(/.{1,4}/g)?.join(' ') || value;
            e.target.value = formattedValue;
        });
    }

    // Transformar nombre a mayúsculas
    const nombreTitularInput = document.getElementById('nombre_titular');
    if (nombreTitularInput) {
        nombreTitularInput.addEventListener('input', function(e) {
            e.target.value = e.target.value.toUpperCase();
        });
    }

    // Validación del formulario antes de enviar
    const form = document.getElementById('formMetodoPago');
    if (form) {
        form.addEventListener('submit', function(e) {
            const tipoSeleccionado = document.querySelector('input[name="tipo"]:checked').value;
            
            if (tipoSeleccionado === 'TARJETA') {
                const numeroTarjeta = document.getElementById('numero_tarjeta').value.replace(/\s/g, '');
                
                // Validar longitud de número de tarjeta
                if (numeroTarjeta.length < 13 || numeroTarjeta.length > 19) {
                    e.preventDefault();
                    alert('El número de tarjeta debe tener entre 13 y 19 dígitos');
                    return false;
                }
                
                // Validar que mes esté seleccionado
                const mes = document.getElementById('mes_expiracion').value;
                if (!mes) {
                    e.preventDefault();
                    alert('Selecciona el mes de expiración');
                    return false;
                }
                
                // Validar que año esté seleccionado
                const anio = document.getElementById('anio_expiracion').value;
                if (!anio) {
                    e.preventDefault();
                    alert('Selecciona el año de expiración');
                    return false;
                }
                
                // Validar que la tarjeta no esté expirada
                const hoy = new Date();
                const mesActual = hoy.getMonth() + 1;
                const anioActual = hoy.getFullYear();
                
                if (parseInt(anio) < anioActual || 
                    (parseInt(anio) === anioActual && parseInt(mes) < mesActual)) {
                    e.preventDefault();
                    alert('La tarjeta está expirada. Por favor verifica la fecha de expiración.');
                    return false;
                }
            }
        });
    }
});
