switch_graph();

function switch_graph(x_data, y_data, bg_colors, title) {


    // full candidate
  if(true == true){
    const ctx = document.getElementById("graph1");

    title.innerHTML = "<h5>Staafdiagram uitleg voor de match (u4119, j147542):</h5>"

    var lgd = document.querySelectorAll(".legend_text");    
    lgd.forEach(function(item) { 
      item.style.display = "block";
    });

    let chartStatus = Chart.getChart("graph1"); 
    if (chartStatus != undefined) {
      chartStatus.destroy();
    }

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: xvalues,
            datasets: [{
              label: "Belangrijkheid",
              data: yvalues,
              backgroundColor: bg_colors,
              borderColor: border_colors
            }],
            
        },
        options: {
          plugins: {
            legend: {
              display: false,
            },
            title: {
              display: true,
              text: "Volledige kanidaat-gerichte uitleg"
            }
          },
          indexAxis: 'y',
          scales: {
            x: {
                max: 12,
                title: {
                  display: true,
                  text: "Belangrijkheid"
                }
              }
            }
          }
        });
  }
  // Simple candidate
  else if(simple.checked == true && company.checked == false){
    const ctx = document.getElementById("graph1");

    title.innerHTML = "<h5>Staafdiagram uitleg voor de match (u4119, j147542):</h5>"

    var lgd = document.querySelectorAll(".legend_text");    
    lgd.forEach(function(item) {
      item.style.display = "none";
    });

    let chartStatus = Chart.getChart("graph1"); 
    if (chartStatus != undefined) {
      chartStatus.destroy();
    }

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: xvalues_simple,
            datasets: [{
              label: "Belangrijkheid",
              data: yvalues_simple,
              backgroundColor: bg_colors_simple,
              borderColor: border_colors_simple
            }]
        },
        options: {
          plugins: {
            legend: {
              display: false,
            },
            title: {
              display: true,
              text: "Simpele kandidaat-gerichte uitleg"
            }
          },
          indexAxis: 'y',
          scales: {
            x: {
                max: 30,
                title: {
                  display: true,
                  text: "Belangrijkheid (categorie)"
                }
              }
            }
          }
        });
  }
// Full company
else if(simple.checked == false && company.checked == true){
  const ctx = document.getElementById("graph1");

  title.innerHTML = "<h5>Staafdiagram uitleg voor de match (j147542, u4119):</h5>"

  var lgd = document.querySelectorAll(".legend_text");    
    lgd.forEach(function(item) { 
      item.style.display = "block";
    });

  let chartStatus = Chart.getChart("graph1"); 
    if (chartStatus != undefined) {
      chartStatus.destroy();
    }

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: xvalues_company,
            datasets: [{
              label: "Belangrijkheid",
              data: yvalues_company,
              backgroundColor: bg_colors_company,
              borderColor: border_colors_company
          }]
        },
        options: {
          plugins: {
            legend: {
              display: false,
            },
            title: {
              display: true,
              text: "Volledige bedrijf-gerichte uitleg"
            }
          },
          indexAxis: 'y',
          scales: {
            x: {
                max: 12,
                title: {
                  display: true,
                  text: "Belangrijkheid"
                }
              }
            }
          }
        });
}
// Simple company
else{
  const ctx = document.getElementById("graph1");
  let chartStatus = Chart.getChart("graph1"); 

  title.innerHTML = "<h5>Staafdiagram uitleg voor de match (j147542, u4119):</h5>"
  
  var lgd = document.querySelectorAll(".legend_text");    
    lgd.forEach(function(item) { 
      item.style.display = "none";
    });

  if (chartStatus != undefined) {
    chartStatus.destroy();
  }

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: xvalues_company_simple,
            datasets: [{
            label: "Belangrijkheid",
            data: yvalues_company_simple,
            backgroundColor: bg_colors_company_simple,
            borderColor: border_colors_company_simple
            }]
        },
        options: {
          plugins: {
            legend: {
              display: false,
            },
            title: {
              display: true,
              text: "Simpele bedrijf-gerichte uitleg"
            }
          },
          indexAxis: 'y',
          scales: {
            x: {
                max: 30,
                title: {
                  display: true,
                  text: "Belangrijkheid (categorie)"
                }
              }
            }
          }
        });
  }
};