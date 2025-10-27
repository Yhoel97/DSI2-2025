document.addEventListener("DOMContentLoaded", function () {
  const pastelColors = [
    "#70d6ff", "#ff70a6", "#ff9770", "#ffd670", "#e9ff70",
    "#cdb4db", "#b5ead7", "#ffb5a7", "#a0c4ff", "#fdffb6"
  ];

  // --- Gráfico de Barras ---
  new Chart(document.getElementById("chartPeliculas"), {
    type: "bar",
    data: {
      labels: topPeliculas.map(p => p.pelicula__nombre),
      datasets: [{
        label: "Boletos Vendidos",
        data: topPeliculas.map(p => p.total_boletos),
        backgroundColor: pastelColors,
        borderColor: "#444",
        borderWidth: 1,
        hoverBackgroundColor: pastelColors.map(c => c + "cc") // más intenso al hover
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

  // --- Gráfico de Pastel ---
  new Chart(document.getElementById("chartFormatos"), {
    type: "pie",
    data: {
      labels: formatos.map(f => f.formato),
      datasets: [{
        data: formatos.map(f => f.total_boletos),
        backgroundColor: pastelColors,
        borderColor: "#fff",
        borderWidth: 2,
        hoverOffset: 20
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