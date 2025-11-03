console.log("🚀 Archivo asientos.js cargado");

document.addEventListener("DOMContentLoaded", function() {
    console.log("✅ DOM cargado completamente");
    
    const form = document.getElementById("reserva-form");
    
    if (!form) {
        console.error("❌ No se encontró el formulario #reserva-form");
        return;
    }
    
    console.log("✅ Formulario encontrado");
    
    // Todos los inputs que deben disparar recálculo automático
    const autoSubmitInputs = document.querySelectorAll(".auto-submit");
    
    console.log("📋 Total de elementos auto-submit:", autoSubmitInputs.length);
    
    if (autoSubmitInputs.length === 0) {
        console.warn("⚠️ No se encontraron elementos con clase .auto-submit");
        console.log("Verificando elementos en el DOM:");
        console.log("  - Radio buttons:", document.querySelectorAll('input[type="radio"]').length);
        console.log("  - Checkboxes:", document.querySelectorAll('input[type="checkbox"]').length);
        return;
    }

    // Listar todos los elementos auto-submit
    autoSubmitInputs.forEach(function(input, index) {
        console.log("   [" + index + "] " + input.type + " - name: " + input.name);
    });

    // Variable para evitar múltiples submits
    let isSubmitting = false;

    autoSubmitInputs.forEach(function(input) {
        input.addEventListener("change", function() {
            console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            console.log("🔄 CAMBIO DETECTADO");
            console.log("   Tipo:", this.type);
            console.log("   Name:", this.name);
            console.log("   Value:", this.value);
            
            // Evitar múltiples submits simultáneos
            if (isSubmitting) {
                console.log("⚠️ Ya hay un submit en proceso, ignorando...");
                return;
            }
            
            isSubmitting = true;
            
            // Crear o actualizar el input hidden para la acción
            let accionInput = document.querySelector('input[name="accion"][type="hidden"]');
            
            if (!accionInput) {
                console.log("   ➕ Creando input hidden para 'accion'");
                accionInput = document.createElement('input');
                accionInput.type = 'hidden';
                accionInput.name = 'accion';
                form.appendChild(accionInput);
            }
            
            // Establecer la acción como "recalcular"
            accionInput.value = 'recalcular';
            console.log("   ✅ Acción establecida: recalcular");
            
            console.log("   🚀 Enviando formulario...");
            console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            
            // Enviar el formulario
            try {
                form.submit();
            } catch (error) {
                console.error("❌ Error al enviar formulario:", error);
                isSubmitting = false;
            }
        });
    });
    
    console.log("✅ Event listeners configurados correctamente");
    
    // Log del botón de confirmar
    const btnConfirm = document.querySelector('.btn-confirm');
    if (btnConfirm) {
        console.log("✅ Botón de confirmar encontrado");
        console.log("   - Type:", btnConfirm.type);
        console.log("   - Name:", btnConfirm.name);
        console.log("   - Value:", btnConfirm.value);
    } else {
        console.warn("⚠️ No se encontró el botón .btn-confirm");
    }
});