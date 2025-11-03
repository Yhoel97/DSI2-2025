document.addEventListener("DOMContentLoaded", () => {
    // ==============================
    // 🔔 Notificaciones
    // ==============================
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach((alert, index) => {
            let timeout = 5000;
            if (alert.classList.contains('alert-search')) {
                timeout = 3000;
            }
            setTimeout(() => {
                alert.style.animation = 'fadeOut 0.5s forwards';
                setTimeout(() => alert.remove(), 500);
            }, timeout + (index * 200));
        });
    }, 500);

    // Botón de cierre manual
    document.querySelectorAll('.closeButton').forEach(button => {
        button.addEventListener('click', function() {
            const notification = this.closest('.alert');
            notification.style.animation = 'fadeOut 0.5s forwards';
            setTimeout(() => notification.remove(), 500);
        });
    });

    // ==============================
    // 📅 Validación de fecha estreno
    // ==============================
    const fechaInput = document.getElementById("fecha_estreno");
    const fechaError = document.getElementById("fechaError");

    if (fechaInput) {
        fechaInput.addEventListener("input", () => {
            if (!fechaInput.value) {
                fechaInput.classList.add("is-invalid");
                fechaError.style.display = "block";
            } else {
                fechaInput.classList.remove("is-invalid");
                fechaError.style.display = "none";
            }
        });
    }

    // ==============================
    // ✅ Validaciones del formulario
    // ==============================
    const form = document.querySelector(".ajax-form");
    if (form) {
        form.addEventListener("submit", (e) => {
            let valid = true;

            const nombre = document.getElementById("nombre");
            const anio = document.getElementById("anio");
            const director = document.getElementById("director");
            const imagen = document.getElementById("imagen_url");
            const trailer = document.getElementById("trailer_url");

            // Nombre
            if (!nombre.value.trim()) {
                nombre.classList.add("is-invalid");
                valid = false;
            } else {
                nombre.classList.remove("is-invalid");
            }

            // Año
            if (!anio.value || anio.value < 1900 || anio.value > 2099) {
                anio.classList.add("is-invalid");
                valid = false;
            } else {
                anio.classList.remove("is-invalid");
            }

            // Fecha
            if (!fechaInput.value) {
                fechaInput.classList.add("is-invalid");
                fechaError.style.display = "block";
                valid = false;
            } else {
                fechaInput.classList.remove("is-invalid");
                fechaError.style.display = "none";
            }

            // Director
            if (!director.value.trim()) {
                director.classList.add("is-invalid");
                valid = false;
            } else {
                director.classList.remove("is-invalid");
            }

            // Imagen URL
            try {
                new URL(imagen.value);
                imagen.classList.remove("is-invalid");
            } catch {
                imagen.classList.add("is-invalid");
                valid = false;
            }

            // Trailer URL
            try {
                new URL(trailer.value);
                trailer.classList.remove("is-invalid");
            } catch {
                trailer.classList.add("is-invalid");
                valid = false;
            }

            // Géneros (máx 3)
            const generos = document.querySelectorAll("input[name='generos']:checked");
            if (generos.length === 0) {
                alert("Debes seleccionar al menos un género.");
                valid = false;
            } else if (generos.length > 3) {
                alert("No puedes seleccionar más de 3 géneros.");
                valid = false;
            }

            // Salas (al menos 1)
            const salas = document.querySelectorAll("input[name='salas']:checked");
            if (salas.length === 0) {
                alert("Debes seleccionar al menos una sala.");
                valid = false;
            }

            if (!valid) {
                e.preventDefault();
            }
        });
    }
});