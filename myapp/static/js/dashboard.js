// Función para crear degradados lineales (para barras y pastel)
function createGradient(ctx, color) {
  const gradient = ctx.createLinearGradient(0, 0, 0, 400);
  gradient.addColorStop(0, color);
  gradient.addColorStop(1, "#ffffff");
  return gradient;
}

document.addEventListener("DOMContentLoaded", function () {
  // Paleta pastel ajustada: reemplazamos el naranja (#ff9770) por verde (#b5ead7)
  const pastelColors = [
    "#70d6ff", // azul
    "#ff70a6", // rosa
    "#b5ead7", // verde pastel (en lugar del naranja)
    "#ffd670", // amarillo
    "#e9ff70", // lima
    "#cdb4db", // lila
    "#ffb5a7", // coral suave
    "#a0c4ff", // celeste
    "#fdffb6"  // amarillo claro
  ];

  // === Gráfico de Barras (Top Películas) ===
  const ctxPeliculas = document.getElementById("chartPeliculas").getContext("2d");
  new Chart(ctxPeliculas, {
    type: "bar",
    data: {
      labels: topPeliculas.map(p => p.pelicula__nombre),
      datasets: [{
        label: "Boletos Vendidos",
        data: topPeliculas.map(p => p.total_boletos),
        backgroundColor: pastelColors.map(c => createGradient(ctxPeliculas, c)),
        borderColor: pastelColors,
        borderWidth: 2,
        borderRadius: 8,
        borderSkipped: false
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 2000,
        easing: "easeOutElastic"
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: function(context) {
              const i = context.dataIndex;
              const pelicula = topPeliculas[i];
              return `🎟️ ${pelicula.total_boletos} boletos — 💵 $${parseFloat(pelicula.total_venta).toFixed(2)}`;
            }
          }
        }
      },
      scales: {
        y: { beginAtZero: true }
      }
    }
  });

  // === Gráfico de Pastel (Formatos) ===
  const ctxFormatos = document.getElementById("chartFormatos").getContext("2d");
  new Chart(ctxFormatos, {
    type: "pie",
    data: {
      labels: formatos.map(f => f.formato),
      datasets: [{
        data: formatos.map(f => f.total_boletos),
        backgroundColor: pastelColors.map(c => createGradient(ctxFormatos, c)), // mismo degradado que barras
        borderColor: pastelColors, // mismo borde que barras
        borderWidth: 2,
        hoverOffset: 25
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        animateScale: true,
        animateRotate: true,
        duration: 2000
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: function(context) {
              const i = context.dataIndex;
              const formato = formatos[i];
              return `🎟️ ${formato.total_boletos} boletos — 💵 $${parseFloat(formato.total_venta).toFixed(2)}`;
            }
          }
        },
        legend: {
          position: "bottom"
        }
      }
    }
  });
});