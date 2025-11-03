document.addEventListener('DOMContentLoaded', function() {
    const peliculaSelect = document.getElementById('peliculaSelect');
    const horariosContainer = document.getElementById('horariosContainer');
    const agregarHorarioBtn = document.getElementById('agregarHorario');
    const funcionForm = document.getElementById('funcionForm');
    
    // Guardar datos del formulario en sessionStorage
    function guardarDatosFormulario() {
        const formData = {
            pelicula: peliculaSelect.value,
            fecha_inicio: document.getElementById('fechaInput').value,
            semanas: document.querySelector('select[name="semanas"]').value,
            horarios: [],
            salas: []
        };
        
        // Guardar horarios y salas
        const horarioSelects = document.querySelectorAll('select[name="horario[]"]');
        const salaSelects = document.querySelectorAll('select[name="sala[]"]');
        
        horarioSelects.forEach((select, index) => {
            formData.horarios.push(select.value);
            formData.salas.push(salaSelects[index].value);
        });
        
        sessionStorage.setItem('funcionFormData', JSON.stringify(formData));
    }
    
    // Cargar datos del formulario desde sessionStorage
    function cargarDatosFormulario() {
        const savedData = sessionStorage.getItem('funcionFormData');
        if (savedData) {
            const formData = JSON.parse(savedData);
            
            // Restaurar datos básicos
            peliculaSelect.value = formData.pelicula;
            document.getElementById('fechaInput').value = formData.fecha_inicio;
            document.querySelector('select[name="semanas"]').value = formData.semanas;
            
            // Actualizar salas según la película seleccionada
            if (formData.pelicula) {
                actualizarSalas().then(() => {
                    // Restaurar horarios y salas
                    if (formData.horarios.length > 0) {
                        // Limpiar horarios existentes excepto el primero
                        const horarioItems = horariosContainer.querySelectorAll('.horario-item');
                        horarioItems.forEach((item, index) => {
                            if (index > 0) item.remove();
                        });
                        
                        // Restaurar primer horario
                        const primerHorario = horariosContainer.querySelector('select[name="horario[]"]');
                        const primerSala = horariosContainer.querySelector('select[name="sala[]"]');
                        if (primerHorario && formData.horarios[0]) {
                            primerHorario.value = formData.horarios[0];
                        }
                        if (primerSala && formData.salas[0]) {
                            // Buscar opción equivalente en las nuevas opciones
                            const opcionesSala = Array.from(primerSala.options);
                            const opcionEquivalente = opcionesSala.find(opt => opt.value === formData.salas[0]);
                            if (opcionEquivalente) {
                                primerSala.value = formData.salas[0];
                            }
                        }
                        
                        // Agregar horarios adicionales
                        for (let i = 1; i < formData.horarios.length; i++) {
                            agregarHorarioConValores(formData.horarios[i], formData.salas[i]);
                        }
                        
                        actualizarBotonesEliminar();
                    }
                });
            }
        }
    }
    
    function actualizarSalas() {
        return new Promise((resolve) => {
            const opcionSeleccionada = peliculaSelect.options[peliculaSelect.selectedIndex];
            const salasDisponibles = opcionSeleccionada ? opcionSeleccionada.getAttribute('data-salas') : null;
            
            // Obtener valores actuales de salas para preservarlos
            const salaSelects = document.querySelectorAll('.sala-select');
            const valoresActuales = Array.from(salaSelects).map(select => select.value);
            
            // Actualizar todos los selects de sala
            salaSelects.forEach((select, index) => {
                const valorActual = valoresActuales[index];
                
                // Limpiar opciones actuales (excepto la primera opción por defecto)
                while (select.options.length > 1) {
                    select.remove(1);
                }
                
                // Agregar nuevas opciones si hay salas disponibles
                if (salasDisponibles) {
                    const salasArray = salasDisponibles.split(';').filter(sala => sala.trim());
                    salasArray.forEach(salaCompleta => {
                        // ✅ CORRECCIÓN: Separar nombre de sala y formato
                        const partes = salaCompleta.trim().split(' - ');
                        const nombreSala = partes[0].trim(); // "Sala 1"
                        const formato = partes[1] ? partes[1].trim() : ''; // "2D"
                        
                        const option = document.createElement('option');
                        option.value = nombreSala; // ✅ Solo el nombre de la sala
                        option.textContent = salaCompleta.trim(); // "Sala 1 - 2D" para mostrar
                        select.appendChild(option);
                    });
                    
                    // Restaurar el valor anterior si existe en las nuevas opciones
                    if (valorActual) {
                        const opcionExistente = Array.from(select.options).find(opt => opt.value === valorActual);
                        if (opcionExistente) {
                            select.value = valorActual;
                        } else if (select.options.length > 1) {
                            // Si no existe, seleccionar la primera opción disponible
                            select.selectedIndex = 1;
                        }
                    } else if (select.options.length > 1) {
                        // Si no hay valor actual, seleccionar la primera opción disponible
                        select.selectedIndex = 1;
                    }
                } else {
                    // Si no hay salas disponibles, mantener solo la opción por defecto
                    select.selectedIndex = 0;
                }
            });
            resolve();
        });
    }
    
    function agregarHorario() {
        agregarHorarioConValores('', '');
    }
    
    function agregarHorarioConValores(horarioValor, salaValor) {
        const horarioItem = document.createElement('div');
        horarioItem.className = 'horario-item mt-3';
        horarioItem.innerHTML = `
            <div class="row g-3">
                <div class="col-md-6">
                    <label class="form-label">Horario</label>
                    <select name="horario[]" class="form-select" required>
                        <option value="">-- Selecciona horario --</option>
                        ${generarOpcionesHorarios()}
                    </select>
                </div>
                <div class="col-md-5">
                    <label class="form-label">Sala / Formato</label>
                    <select name="sala[]" class="form-select sala-select" required>
                        <option value="">-- Selecciona una sala --</option>
                    </select>
                </div>
                <div class="col-md-1 d-flex align-items-end">
                    <button type="button" class="btn btn-outline-danger remove-horario">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
        
        horariosContainer.appendChild(horarioItem);
        
        // Actualizar salas para el nuevo select
        actualizarSalas().then(() => {
            // Establecer valores si se proporcionaron
            const horarioSelect = horarioItem.querySelector('select[name="horario[]"]');
            const salaSelect = horarioItem.querySelector('select[name="sala[]"]');
            
            if (horarioValor && horarioSelect) {
                horarioSelect.value = horarioValor;
            }
            if (salaValor && salaSelect) {
                // Buscar opción equivalente
                const opcionesSala = Array.from(salaSelect.options);
                const opcionEquivalente = opcionesSala.find(opt => opt.value === salaValor);
                if (opcionEquivalente) {
                    salaSelect.value = salaValor;
                } else if (salaSelect.options.length > 1) {
                    salaSelect.selectedIndex = 1;
                }
            } else if (salaSelect && salaSelect.options.length > 1) {
                salaSelect.selectedIndex = 1;
            }
        });
        
        // Agregar evento al botón de eliminar
        const removeBtn = horarioItem.querySelector('.remove-horario');
        removeBtn.addEventListener('click', function() {
            horarioItem.remove();
            actualizarBotonesEliminar();
            guardarDatosFormulario();
        });
        
        // Agregar eventos para guardar datos
        const horarioSelect = horarioItem.querySelector('select[name="horario[]"]');
        const salaSelect = horarioItem.querySelector('select[name="sala[]"]');
        
        if (horarioSelect) {
            horarioSelect.addEventListener('change', guardarDatosFormulario);
        }
        if (salaSelect) {
            salaSelect.addEventListener('change', guardarDatosFormulario);
        }
        
        actualizarBotonesEliminar();
        guardarDatosFormulario();
    }
    
    function generarOpcionesHorarios() {
        const horarioBase = document.querySelector('select[name="horario[]"]');
        if (horarioBase) {
            const options = horarioBase.querySelectorAll('option');
            let html = '';
            options.forEach(option => {
                if (option.value) {
                    html += `<option value="${option.value}">${option.textContent}</option>`;
                }
            });
            return html;
        }
        return '';
    }
    
    function actualizarBotonesEliminar() {
        const horarioItems = horariosContainer.querySelectorAll('.horario-item');
        const removeButtons = horariosContainer.querySelectorAll('.remove-horario');
        
        // Mostrar botón de eliminar solo si hay más de un horario
        if (horarioItems.length > 1) {
            removeButtons.forEach(btn => {
                btn.style.display = 'block';
            });
        } else {
            removeButtons.forEach(btn => {
                btn.style.display = 'none';
            });
        }
    }
    
    // Event Listeners
    if (peliculaSelect) {
        peliculaSelect.addEventListener('change', function() {
            actualizarSalas().then(() => {
                guardarDatosFormulario();
            });
        });
    }
    
    const fechaInput = document.getElementById('fechaInput');
    if (fechaInput) {
        fechaInput.addEventListener('change', guardarDatosFormulario);
    }
    
    const semanasSelect = document.querySelector('select[name="semanas"]');
    if (semanasSelect) {
        semanasSelect.addEventListener('change', guardarDatosFormulario);
    }
    
    if (agregarHorarioBtn) {
        agregarHorarioBtn.addEventListener('click', function() {
            agregarHorario();
        });
    }
    
    // Event delegation para botones de eliminar existentes
    if (horariosContainer) {
        horariosContainer.addEventListener('click', function(e) {
            if (e.target.closest('.remove-horario')) {
                e.preventDefault();
                const horarioItem = e.target.closest('.horario-item');
                if (horarioItem) {
                    horarioItem.remove();
                    actualizarBotonesEliminar();
                    guardarDatosFormulario();
                }
            }
        });
        
        // Event delegation para cambios en horarios existentes
        horariosContainer.addEventListener('change', function(e) {
            if (e.target.name === 'horario[]' || e.target.name === 'sala[]') {
                guardarDatosFormulario();
            }
        });
    }
    
    // Limpiar datos al enviar el formulario exitosamente
    if (funcionForm) {
        funcionForm.addEventListener('submit', function() {
            sessionStorage.removeItem('funcionFormData');
        });
    }
    
    // Limpiar datos al cancelar edición
    const cancelarBtn = document.querySelector('a[href*="administrar_funciones"]');
    if (cancelarBtn) {
        cancelarBtn.addEventListener('click', function() {
            sessionStorage.removeItem('funcionFormData');
        });
    }
    
    // Limpiar datos al cargar la página si estamos en modo edición
    const funcionEditar = document.querySelector('input[name="funcion_id"]');
    if (funcionEditar) {
        sessionStorage.removeItem('funcionFormData');
    }
    
    // Inicializar
    function inicializar() {
        if (peliculaSelect && peliculaSelect.value) {
            actualizarSalas();
        }
        actualizarBotonesEliminar();
        
        // Solo cargar datos guardados si no estamos en modo edición
        if (!funcionEditar) {
            cargarDatosFormulario();
        }
    }
    
    // Esperar un poco para asegurar que el DOM esté completamente listo
    setTimeout(inicializar, 100);
});