"use strict";
// No client-side calculations: values are serialised from the Flask backend.
document.addEventListener("DOMContentLoaded", () => {
  const node = document.getElementById("dashboard-chart-data");
  if (!node) return;
  const error = document.getElementById("dashboard-chart-error");
  if (typeof Chart === "undefined") {
    if (error) {
      error.hidden = false;
      error.textContent = "The charts could not load. Check your internet connection to load Chart.js.";
    }
    return;
  }

  let data;
  try { data = JSON.parse(node.textContent); }
  catch (_) {
    if (error) { error.hidden = false; error.textContent = "The chart data could not be displayed."; }
    return;
  }

  const styles = () => {
    const computed = getComputedStyle(document.documentElement);
    return {
      text: computed.getPropertyValue("--text-main").trim() || "#111827",
      muted: computed.getPropertyValue("--text-muted").trim() || "#6b7280",
      border: computed.getPropertyValue("--border").trim() || "#e5e7eb",
    };
  };

  const charts = [];
  function createChart(id, config) {
    const canvas = document.getElementById(id);
    if (canvas) charts.push(new Chart(canvas, config));
  }
  function axis(s) {
    return {
      beginAtZero: true,
      ticks: { color: s.muted, precision: 0 },
      grid: { color: s.border },
    };
  }
  const s = styles();
  const legend = { labels: { color: s.text, usePointStyle: true, boxWidth: 12 } };

  createChart("taskStatusChart", {
    type: "doughnut",
    data: {
      labels: data.status_labels,
      datasets: [{
        data: data.status_values,
        backgroundColor: ["#16a34a", "#2563eb", "#e11d48"],
        borderWidth: 0,
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: "67%",
      plugins: { legend: { position: "bottom", ...legend } },
    },
  });

  createChart("weeklyActivityChart", {
    type: "bar",
    data: {
      labels: data.week_labels,
      datasets: [
        { label: "Recorded actions", data: data.weekly_activity, backgroundColor: "#2563eb", borderRadius: 5, maxBarThickness: 28 },
        { label: "Tasks completed", data: data.weekly_completed, backgroundColor: "#16a34a", borderRadius: 5, maxBarThickness: 28 },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: "bottom", ...legend } },
      scales: { x: { ticks: { color: s.muted }, grid: { display: false } }, y: axis(s) },
    },
  });

  createChart("indicatorBreakdownChart", {
    type: "bar",
    data: {
      labels: data.score_labels,
      datasets: [{ label: "Score (0–100)", data: data.score_values, backgroundColor: ["#2563eb", "#7c3aed", "#0d9488"], borderRadius: 6, maxBarThickness: 32 }],
    },
    options: {
      indexAxis: "y", responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ...axis(s), max: 100, ticks: { color: s.muted, callback: value => value + "%" } },
        y: { ticks: { color: s.muted }, grid: { display: false } },
      },
    },
  });

  // Update chart text and grid lines when the existing sidebar theme switch changes theme.
  const observer = new MutationObserver(() => {
    const current = styles();
    charts.forEach(chart => {
      if (chart.options.plugins?.legend?.labels) chart.options.plugins.legend.labels.color = current.text;
      if (chart.options.scales) {
        Object.values(chart.options.scales).forEach(scale => {
          if (scale.ticks) scale.ticks.color = current.muted;
          if (scale.grid && scale.grid.display !== false) scale.grid.color = current.border;
        });
      }
      chart.update("none");
    });
  });
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
});
