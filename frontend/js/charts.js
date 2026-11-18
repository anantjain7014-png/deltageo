class SatelliteCharts {
  constructor() {
    this.barChart = null;
    this.donutChart = null;
  }

  // Consistent color mapping based on legend
  getColorForCategory(category) {
    if (category.includes('Building')) return '#ef4444';
    if (category.includes('Road')) return '#2563eb';
    if (category.includes('Vehicle')) return '#f59e0b';
    if (category.includes('Industrial')) return '#8b5cf6';
    if (category.includes('Excavation')) return '#10b981';
    return '#9ca3af';
  }

  renderHorizontalBarChart(canvasId, classDistribution, totalArea) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    // Sort entries by area descending
    const entries = Object.entries(classDistribution).sort((a, b) => b[1] - a[1]);
    const labels = entries.map(e => e[0]);
    const dataValues = entries.map(e => e[1]);
    const bgColors = labels.map(l => this.getColorForCategory(l));

    if (this.barChart) {
      this.barChart.destroy();
    }

    const ctx = canvas.getContext('2d');
    
    // Custom plugin to draw labels at the end of bars
    const barLabelsPlugin = {
      id: 'barLabels',
      afterDatasetsDraw(chart, args, options) {
        const { ctx, data, chartArea: { left, right, top, bottom, width, height }, scales: { x, y } } = chart;
        ctx.save();
        chart.getDatasetMeta(0).data.forEach((datapoint, index) => {
          const val = data.datasets[0].data[index];
          if (val === 0) return;
          const percentage = totalArea > 0 ? ((val / totalArea) * 100).toFixed(1) : 0;
          
          ctx.font = '11px Inter, sans-serif';
          ctx.fillStyle = '#6b7280';
          ctx.textAlign = 'left';
          ctx.textBaseline = 'middle';
          
          // Draw text outside the bar
          ctx.fillText(`${percentage}% (${Math.round(val)} m²)`, datapoint.x + 8, datapoint.y);
        });
        ctx.restore();
      }
    };

    this.barChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          data: dataValues,
          backgroundColor: bgColors,
          barThickness: 16,
          borderRadius: 4
        }]
      },
      plugins: [barLabelsPlugin],
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        layout: {
          padding: {
            right: 80 // Space for labels
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function(context) {
                const val = context.raw || 0;
                return ` ${val.toLocaleString()} m²`;
              }
            }
          }
        },
        scales: {
          x: {
            display: true,
            grid: { color: '#f3f4f6' },
            border: { display: false },
            ticks: { display: false }
          },
          y: {
            grid: { display: false },
            border: { display: false },
            ticks: {
              color: '#374151',
              font: { family: 'Inter', size: 12 },
              crossAlign: 'near'
            }
          }
        }
      }
    });
  }

  renderDonutChart(canvasId, humanArea, naturalArea) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    if (this.donutChart) {
      this.donutChart.destroy();
    }

    const total = humanArea + naturalArea;
    const humanPct = total > 0 ? Math.round((humanArea / total) * 100) : 0;
    const naturalPct = total > 0 ? Math.round((naturalArea / total) * 100) : 0;

    const ctx = canvas.getContext('2d');
    
    // Custom plugin for center text
    const centerTextPlugin = {
      id: 'centerText',
      beforeDraw(chart) {
        const { ctx, chartArea: { left, right, top, bottom, width, height } } = chart;
        ctx.save();
        
        ctx.textAlign = 'center';
        
        ctx.font = '10px Inter, sans-serif';
        ctx.fillStyle = '#111827';
        ctx.fillText('Total Detected', left + width / 2, top + height / 2 - 12);
        
        ctx.font = '10px Inter, sans-serif';
        ctx.fillStyle = '#111827';
        ctx.fillText('Change Area', left + width / 2, top + height / 2 + 2);
        
        ctx.font = 'bold 18px Inter, sans-serif';
        ctx.fillStyle = '#111827';
        ctx.fillText('100%', left + width / 2, top + height / 2 + 22);
        
        ctx.restore();
      }
    };

    this.donutChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Human-Related', 'Natural / Filtered'],
        datasets: [{
          data: [humanArea, naturalArea],
          backgroundColor: ['#166534', '#9ca3af'], // Dark green and gray
          borderWidth: 0,
          hoverOffset: 4
        }]
      },
      plugins: [centerTextPlugin],
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '70%',
        layout: {
          padding: { right: 220 }
        },
        plugins: {
          legend: {
            position: 'right',
            labels: {
              color: '#374151',
              font: { family: 'Inter', size: 12, weight: 'bold' },
              usePointStyle: true,
              pointStyle: 'rectRounded',
              padding: 20,
              generateLabels: function(chart) {
                const data = chart.data;
                if (data.labels.length && data.datasets.length) {
                  return data.labels.map(function(label, i) {
                    const meta = chart.getDatasetMeta(0);
                    const style = meta.controller.getStyle(i);
                    const val = data.datasets[0].data[i];
                    const pct = i === 0 ? humanPct : naturalPct;
                    return {
                      text: `${label}`,
                      fillStyle: style.backgroundColor,
                      strokeStyle: style.borderColor,
                      lineWidth: style.borderWidth,
                      hidden: isNaN(data.datasets[0].data[i]) || meta.data[i].hidden,
                      index: i
                    };
                  });
                }
                return [];
              }
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const val = context.raw || 0;
                return ` ${val.toLocaleString()} m²`;
              }
            }
          }
        }
      }
    });

    // Custom legend text rendering via DOM since ChartJS limits complex multiline HTML legends easily
    // We will append a custom HTML legend block next to canvas if it doesn't exist
    let customLegend = document.getElementById('customDonutLegend');
    if (!customLegend) {
      customLegend = document.createElement('div');
      customLegend.id = 'customDonutLegend';
      customLegend.style.position = 'absolute';
      customLegend.style.right = '0px';
      customLegend.style.top = '50%';
      customLegend.style.transform = 'translateY(-50%)';
      customLegend.style.display = 'flex';
      customLegend.style.flexDirection = 'column';
      customLegend.style.gap = '20px';
      canvas.parentNode.appendChild(customLegend);
    }
    
    // Hide native legend
    this.donutChart.options.plugins.legend.display = false;
    this.donutChart.update();

    customLegend.innerHTML = `
      <div>
        <div class="d-flex align-items-center gap-2 mb-1">
          <span style="display:inline-block; width: 12px; height: 12px; background-color: #166534; border-radius: 2px;"></span>
          <span class="small fw-bold text-dark">Human-Related</span>
        </div>
        <div class="small text-secondary ps-4">${humanPct}% (${humanArea.toLocaleString()} m²)</div>
      </div>
      <div>
        <div class="d-flex align-items-center gap-2 mb-1">
          <span style="display:inline-block; width: 12px; height: 12px; background-color: #9ca3af; border-radius: 2px;"></span>
          <span class="small fw-bold text-dark">Natural / Filtered</span>
        </div>
        <div class="small text-secondary ps-4">${naturalPct}% (${naturalArea.toLocaleString()} m²)</div>
      </div>
    `;
  }
}
