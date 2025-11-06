window.addEventListener('scroll', function() {
  const header = document.querySelector('header');
  if (window.scrollY > 50) {
    header.style.background = 'linear-gradient(to right, #e0f3ff, #d0e0ff, #e6d6ff)';
  } else {
    header.style.background = 'linear-gradient(to right, #ffffff, #e0f3ff, #f0e6ff)';
  }
});

document.addEventListener('DOMContentLoaded', function() {
  const dateButtons = document.querySelectorAll('.date-btn');
  const titleElement = document.querySelector('.date-selector-title-new');
  const carteleraSection = document.querySelector('#cartelera .peliculas-grid');
  
  if (dateButtons.length > 0 && titleElement && carteleraSection) {
    dateButtons.forEach(button => {
      button.addEventListener('click', function() {
        const selectedDate = this.getAttribute('data-fecha');
        
        // 1. Actualizar URL sin recargar
        const url = new URL(window.location.href);
        url.searchParams.set('fecha', selectedDate);
        window.history.pushState({}, '', url);
        
        // 2. Actualizar estado visual de botones
        dateButtons.forEach(btn => {
          btn.classList.remove('btn-active');
          btn.classList.add('btn-outline');
        });
        this.classList.remove('btn-outline');
        this.classList.add('btn-active');
        
        // 3. ANIMACIÓN DE CARGA EN EL SELECTOR DE FECHA
        const originalTitle = titleElement.innerHTML;
        titleElement.style.opacity = '0';
        setTimeout(() => {
          titleElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cargando cartelera...';
          titleElement.style.opacity = '1';
        }, 150);
        
        // 4. ANIMACIÓN DE CARGA EN EL GRID DE PELÍCULAS
        carteleraSection.style.opacity = '0';
        carteleraSection.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
          carteleraSection.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 3rem;">
              <div style="display: inline-block; animation: rotate 1.5s linear infinite;">
                <i class="fas fa-film" style="font-size: 5rem; color: #4A90E2; filter: drop-shadow(0 4px 12px rgba(74, 144, 226, 0.4));"></i>
              </div>
              <p style="color: #666; font-size: 1.1rem; font-weight: 500; margin-top: 1rem;">Cargando películas...</p>
              <style>
                @keyframes rotate {
                  from { transform: rotate(0deg); }
                  to { transform: rotate(360deg); }
                }
              </style>
            </div>
          `;
          carteleraSection.style.opacity = '1';
          carteleraSection.style.transform = 'translateY(0)';
        }, 200);
        
        // 5. Hacer petición AJAX con header especial
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
            // ANIMACIÓN SUAVE AL ACTUALIZAR TÍTULO
            titleElement.style.opacity = '0';
            setTimeout(() => {
              const esHoyTexto = data.es_hoy ? 'Hoy' : 'del';
              titleElement.innerHTML = `
                <i class="fas fa-calendar-week"></i> 
                Cartelera ${esHoyTexto} ${data.fecha_formateada}
              `;
              titleElement.style.opacity = '1';
            }, 150);
            
            // Actualizar el título de la sección
            const sectionTitle = document.querySelector('#cartelera .section-title');
            if (sectionTitle) {
              sectionTitle.style.opacity = '0';
              setTimeout(() => {
                sectionTitle.innerHTML = `
                  🎞️ Películas en Cartelera ${esHoyTexto} ${data.fecha_formateada}
                `;
                sectionTitle.style.opacity = '1';
              }, 150);
            }
            
            // ANIMACIÓN AL RENDERIZAR PELÍCULAS
            carteleraSection.style.opacity = '0';
            setTimeout(() => {
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
                  '<a href="/" class="btn btn-primary" style="display: inline-block; margin-top: 1rem; padding: 0.8rem 1.5rem; background: linear-gradient(to right, #00c6ff, #7b68ee); color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">Ver Cartelera de Hoy</a>' : '';
                
                carteleraSection.innerHTML = `
                  <div class="no-funciones" style="grid-column: 1/-1; text-align: center; padding: 3rem;">
                    <i class="fas fa-film fa-3x" style="color: #adb5bd; margin-bottom: 1rem;"></i>
                    <p style="color: #6c757d; font-size: 1.2rem; font-weight: 500; margin-bottom: 1.5rem;">No hay funciones programadas para esta fecha.</p>
                    ${volverHoyBtn}
                  </div>
                `;
              }
              
              // APLICAR ANIMACIÓN DE ENTRADA A LAS TARJETAS
              carteleraSection.style.opacity = '1';
              const cards = carteleraSection.querySelectorAll('.pelicula-card');
              cards.forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(40px) scale(0.9)';
                setTimeout(() => {
                  card.style.transition = 'all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
                  card.style.opacity = '1';
                  card.style.transform = 'translateY(0) scale(1)';
                }, 100 * index);
              });
            }, 200);
          })
          .catch(error => {
            console.error('Error al cargar películas:', error);
            
            // ANIMACIÓN DE ERROR
            titleElement.style.opacity = '0';
            setTimeout(() => {
              titleElement.innerHTML = originalTitle;
              titleElement.style.opacity = '1';
            }, 150);
            
            carteleraSection.style.opacity = '0';
            setTimeout(() => {
              carteleraSection.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 3rem;">
                  <i class="fas fa-exclamation-triangle fa-3x" style="color: #e74c3c; margin-bottom: 1rem;"></i>
                  <p style="color: #e74c3c; font-size: 1.1rem; font-weight: 500;">Error al cargar las películas. Por favor, intenta de nuevo.</p>
                  <button onclick="location.reload()" class="btn btn-primary" style="margin-top: 1rem; padding: 0.8rem 1.5rem; background: linear-gradient(to right, #00c6ff, #7b68ee); color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">
                    <i class="fas fa-sync-alt"></i> Recargar Página
                  </button>
                </div>
              `;
              carteleraSection.style.opacity = '1';
            }, 200);
          });
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