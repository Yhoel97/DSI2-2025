window.addEventListener('scroll', function() {
  const header = document.querySelector('header');
  if (window.scrollY > 50) {
    header.style.background = 'linear-gradient(to right, #e0f3ff, #d0e0ff, #e6d6ff)';
  } else {
    header.style.background = 'linear-gradient(to right, #ffffff, #e0f3ff, #f0e6ff)';
  }
});

document.addEventListener('DOMContentLoaded', function() {
  const dateSelector = document.querySelector('.date-dropdown-new');
  const titleElement = document.querySelector('.date-selector-title-new');
  const carteleraSection = document.querySelector('#cartelera .peliculas-grid');
  
  if (dateSelector && titleElement && carteleraSection) {
    dateSelector.addEventListener('change', function() {
      const selectedDate = this.value;
      
      // 1. Actualizar URL sin recargar
      const url = new URL(window.location.href);
      url.searchParams.set('fecha', selectedDate);
      window.history.pushState({}, '', url);
      
      // 2. Mostrar estado de carga
      const originalTitle = titleElement.innerHTML;
      titleElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cargando cartelera...';
      
      // Mostrar esqueleto de carga en las películas
      carteleraSection.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 3rem;">
          <i class="fas fa-film fa-3x fa-spin" style="color: #667eea; margin-bottom: 1rem;"></i>
          <p style="color: #666; font-size: 1.1rem;">Cargando películas...</p>
        </div>
      `;
      
      // 3. Hacer petición AJAX con header especial
      fetch(`?fecha=${selectedDate}`, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
        .then(response => {
          if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
          }
          return response.json();
        })
        .then(data => {
          // Actualizar el título
          const esHoyTexto = data.es_hoy ? 'Hoy' : 'del';
          titleElement.innerHTML = `
            <i class="fas fa-calendar-week"></i> 
            Cartelera ${esHoyTexto} ${data.fecha_formateada}
          `;
          
          // Actualizar el título de la sección
          const sectionTitle = document.querySelector('#cartelera .section-title');
          if (sectionTitle) {
            sectionTitle.innerHTML = `
              🎞️ Películas en Cartelera ${esHoyTexto} ${data.fecha_formateada}
            `;
          }
          
          // Renderizar películas
          if (data.peliculas && data.peliculas.length > 0) {
            carteleraSection.innerHTML = data.peliculas.map(pelicula => `
              <div class="pelicula-card">
                <div class="poster-container">
                  <img src="${pelicula.imagen_url}" alt="${pelicula.nombre}" class="movie-poster responsive-img">
                </div>

                <div class="pelicula-info">
                  <h3 class="movie-title">${pelicula.nombre}</h3>

                  <div class="movie-details">
                    <p><span class="detail-label">Género:</span> ${pelicula.generos.join(', ')}</p>
                    <p><span class="detail-label">Director:</span> ${pelicula.director}</p>
                    <p><span class="detail-label">Clasificación:</span> ${pelicula.clasificacion}</p>
                    <p><span class="detail-label">Idioma:</span> ${pelicula.idioma}</p>
                    <p><span class="detail-label">Año:</span> ${pelicula.anio}</p>

                    <div class="horarios-container">
                      <span class="detail-label">Horarios disponibles:</span>
                      <div class="horarios-list">
                        ${pelicula.funciones.map(funcion => `
                          <div class="horario-item">
                            <i class="fas fa-clock"></i> 
                            ${funcion.horario} - 
                            ${funcion.sala} - 
                            ${funcion.formato}
                          </div>
                        `).join('')}
                      </div>
                    </div>
                  </div>

                  <div class="movie-rating">
                    <div class="rating-stars">
                      ${generarEstrellas(pelicula.rating)}
                    </div>
                    <div class="rating-info">
                      <span class="rating-score">${pelicula.rating_promedio}/5</span>
                      <span class="rating-count">(${pelicula.total_valoraciones} valoración${pelicula.total_valoraciones !== 1 ? 'es' : ''})</span>
                    </div>
                  </div>

                  <div class="movie-actions flex">
                    <a href="${pelicula.trailer_url}" target="_blank" class="btn trailer-btn">
                      <i class="fab fa-youtube"></i> Ver Tráiler
                    </a>
                    <a href="/pelicula/${pelicula.id}/" class="btn review-btn">
                      <i class="fas fa-star"></i> Ver Reseñas
                    </a>
                    <a href="/asientos/${pelicula.id}/?fecha=${selectedDate}" class="btn buy-btn">
                      <i class="fas fa-ticket-alt"></i> Comprar Boletos
                    </a>
                  </div>
                </div>
              </div>
            `).join('');
          } else {
            // No hay funciones para esta fecha
            const volverHoyBtn = !data.es_hoy ? 
              '<a href="/" class="btn btn-primary">Ver Cartelera de Hoy</a>' : '';
            
            carteleraSection.innerHTML = `
              <div class="no-funciones" style="grid-column: 1/-1; text-align: center; padding: 3rem;">
                <i class="fas fa-film fa-3x" style="color: #667eea; margin-bottom: 1rem;"></i>
                <p style="color: #666; font-size: 1.1rem;">No hay funciones programadas para esta fecha.</p>
                ${volverHoyBtn}
              </div>
            `;
          }
        })
        .catch(error => {
          console.error('Error al cargar películas:', error);
          titleElement.innerHTML = originalTitle;
          carteleraSection.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 3rem;">
              <i class="fas fa-exclamation-triangle fa-3x" style="color: #e74c3c; margin-bottom: 1rem;"></i>
              <p style="color: #e74c3c; font-size: 1.1rem;">Error al cargar las películas. Por favor, intenta de nuevo.</p>
              <button onclick="location.reload()" class="btn btn-primary" style="margin-top: 1rem;">
                Recargar Página
              </button>
            </div>
          `;
        });
    });
  }
  
  // Manejar navegación con botones atrás/adelante
  window.addEventListener('popstate', function() {
    window.location.reload();
  });
});

// Función auxiliar para generar estrellas de rating
function generarEstrellas(ratingData) {
  const estrellas = [];
  for (let i = 1; i <= 5; i++) {
    if (i <= ratingData.llenas) {
      estrellas.push('<i class="fas fa-star star-filled"></i>');
    } else if (i === ratingData.llenas + 1 && ratingData.media) {
      estrellas.push('<i class="fas fa-star-half-alt star-filled"></i>');
    } else {
      estrellas.push('<i class="far fa-star star-empty"></i>');
    }
  }
  return estrellas.join('');
}