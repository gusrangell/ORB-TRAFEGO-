const MODAL_TRANSITION_MS = 200;
const NEON_GREEN = "#39ff91";
let cplChartInstance = null;

function setSubmitLoading(button, loading) {
  if (!button || button.type !== "submit") return;
  if (loading) {
    if (!button.dataset.defaultLabel) {
      button.dataset.defaultLabel = button.textContent.trim();
    }
    button.classList.add("is-loading");
    button.disabled = true;
    button.textContent = "Salvando…";
  } else {
    button.disabled = false;
    button.textContent = button.dataset.defaultLabel || "Salvar";
    button.classList.remove("is-loading");
  }
}

function openModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.remove("hidden");
  modal.classList.add("flex");
  requestAnimationFrame(() => {
    modal.classList.add("is-open");
  });
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.remove("is-open");
  modal.querySelectorAll(".btn-submit.is-loading").forEach((btn) => {
    btn.classList.remove("is-loading");
    btn.disabled = false;
    if (btn.dataset.defaultLabel) {
      btn.textContent = btn.dataset.defaultLabel;
    }
  });
  window.setTimeout(() => {
    modal.classList.add("hidden");
    modal.classList.remove("flex");
    const form = modal.querySelector("form");
    if (form) {
      form.reset();
    }
  }, MODAL_TRANSITION_MS);
}

document.getElementById("btn-open-modal-diario")?.addEventListener("click", () => {
  openModal("modal-diario");
});

document.querySelectorAll(".close-modal").forEach((button) => {
  button.addEventListener("click", () => closeModal(button.dataset.target));
});

["modal-diario"].forEach((id) => {
  document.getElementById(id)?.addEventListener("click", (event) => {
    if (event.target.id === id) closeModal(id);
  });
});

function formatMoeda(value) {
  if (value === null || value === undefined) return "—";
  return `R$ ${Number(value).toFixed(2).replace(".", ",")}`;
}

function formatPercent(value) {
  if (value === null || value === undefined) return "—";
  return `${(Number(value) * 100).toFixed(2).replace(".", ",")}%`;
}

function renderChart(data) {
  const chartWrapper = document.getElementById("chart-wrapper");
  const emptyState = document.getElementById("chart-empty");
  const hasData = Array.isArray(data) && data.some((item) => item.cpl !== null && item.cpl !== undefined);

  if (!hasData) {
    chartWrapper?.classList.add("hidden");
    emptyState?.classList.remove("hidden");
    if (cplChartInstance) {
      cplChartInstance.destroy();
      cplChartInstance = null;
    }
    return;
  }

  chartWrapper?.classList.remove("hidden");
  emptyState?.classList.add("hidden");

  const chartElement = document.getElementById("cplChart");
  if (chartElement) {
    const gridColor = "rgba(51, 65, 85, 0.6)";
    const tickColor = "#94a3b8";

    if (cplChartInstance) {
      cplChartInstance.destroy();
    }
    cplChartInstance = new Chart(chartElement, {
      type: "line",
      data: {
        labels: data.map((item) => item.data),
        datasets: [
          {
            label: "CPL",
            data: data.map((item) => item.cpl),
            borderColor: NEON_GREEN,
            backgroundColor: "transparent",
            borderWidth: 2,
            tension: 0.4,
            fill: false,
            pointRadius: 3,
            pointBackgroundColor: NEON_GREEN,
            pointBorderColor: "#0f172a",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          intersect: false,
          mode: "index",
        },
        plugins: {
          legend: {
            labels: { color: tickColor },
          },
        },
        scales: {
          x: {
            grid: { color: gridColor },
            ticks: { color: tickColor },
          },
          y: {
            grid: { color: gridColor },
            ticks: {
              color: tickColor,
              callback(value) {
                return `R$ ${Number(value).toFixed(2).replace(".", ",")}`;
              },
            },
          },
        },
      },
    });
  }
}

function renderCampanhas(campanhas) {
  const tbody = document.getElementById("campanhas-body");
  if (!tbody) return;

  if (!Array.isArray(campanhas) || campanhas.length === 0) {
    tbody.innerHTML =
      '<tr><td class="px-4 py-4 text-center text-[#94a3b8]" colspan="7">Nenhuma campanha encontrada</td></tr>';
    return;
  }

  tbody.innerHTML = campanhas
    .map((campanha) => {
      let statusClass = "bg-slate-500/20 text-slate-300";
      if (campanha.status === "ACTIVE") statusClass = "bg-emerald-500/20 text-emerald-300";
      if (campanha.status === "PAUSED") statusClass = "bg-amber-500/20 text-amber-300";
      return `
        <tr>
          <td class="px-4 py-3">${campanha.nome}</td>
          <td class="px-4 py-3"><span class="inline-flex rounded-md px-2 py-0.5 text-xs font-semibold ${statusClass}">${campanha.status || "—"}</span></td>
          <td class="px-4 py-3 text-right">${formatMoeda(campanha.cpl)}</td>
          <td class="px-4 py-3 text-right">${formatPercent(campanha.ctr)}</td>
          <td class="px-4 py-3 text-right">${formatMoeda(campanha.cpc)}</td>
          <td class="px-4 py-3 text-right">${campanha.conversoes ?? 0}</td>
          <td class="px-4 py-3 text-right">${formatMoeda(campanha.investimento ?? 0)}</td>
        </tr>
      `;
    })
    .join("");
}

async function aplicarFiltroPeriodo() {
  const dataInicio = document.getElementById("data_inicio")?.value;
  const dataFim = document.getElementById("data_fim")?.value;
  const erroEl = document.getElementById("filtro-erro");

  if (erroEl) {
    erroEl.classList.add("hidden");
    erroEl.textContent = "";
  }

  const params = new URLSearchParams();
  if (dataInicio) params.set("data_inicio", dataInicio);
  if (dataFim) params.set("data_fim", dataFim);
  const query = params.toString();

  try {
    const [metricasResp, campanhasResp] = await Promise.all([
      fetch(`/api/clientes/${clienteId}/metricas-consolidadas${query ? `?${query}` : ""}`),
      fetch(`/api/clientes/${clienteId}/campanhas${query ? `?${query}` : ""}`),
    ]);

    const metricasData = await metricasResp.json();
    if (!metricasResp.ok) throw new Error(metricasData.error || "Falha ao aplicar filtro.");

    const campanhasData = await campanhasResp.json();
    if (!campanhasResp.ok) throw new Error(campanhasData.error || "Falha ao buscar campanhas.");

    document.getElementById("data_inicio").value = metricasData.data_inicio;
    document.getElementById("data_fim").value = metricasData.data_fim;

    document.getElementById("kpi-cpl").textContent = formatMoeda(metricasData.cpl);
    document.getElementById("kpi-ctr").textContent = formatPercent(metricasData.ctr);
    document.getElementById("kpi-cpc").textContent = formatMoeda(metricasData.cpc);
    document.getElementById("kpi-conversoes").textContent = `${metricasData.conversoes ?? 0}`;
    document.getElementById("kpi-investimento").textContent = formatMoeda(metricasData.investimento ?? 0);

    renderChart(metricasData.historico || []);
    renderCampanhas(campanhasData || []);
  } catch (error) {
    if (erroEl) {
      erroEl.textContent = error.message;
      erroEl.classList.remove("hidden");
    }
  }
}

document.getElementById("btn-aplicar-filtro")?.addEventListener("click", aplicarFiltroPeriodo);

function mostrarFeedbackMeta(el, texto, tipo) {
  if (!el) return;
  el.textContent = texto;
  el.classList.remove("hidden", "text-red-400", "text-emerald-400", "text-[#94a3b8]");
  if (tipo === "erro") el.classList.add("text-red-400");
  else if (tipo === "ok") el.classList.add("text-emerald-400");
  else el.classList.add("text-[#94a3b8]");
}

async function buscarContasMetaCliente() {
  const tokenInput = document.getElementById("meta-access-token");
  const selectEl = document.getElementById("meta-account-select");
  const feedback = document.getElementById("sync-meta-feedback");
  const token = tokenInput?.value?.trim();
  if (!token) {
    mostrarFeedbackMeta(feedback, "Cole o Access Token para buscar contas.", "erro");
    feedback?.classList.remove("hidden");
    return;
  }
  mostrarFeedbackMeta(feedback, "Buscando contas…", "info");
  feedback?.classList.remove("hidden");
  try {
    const response = await fetch("/api/meta/contas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ access_token: token }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Falha ao buscar contas.");
    const contas = data.contas || [];
    selectEl.innerHTML =
      '<option value="">Selecione para trocar a conta</option>' +
      contas.map((c) => `<option value="${c.account_id}">${c.nome} (${c.account_id})</option>`).join("");
    selectEl.disabled = false;
    mostrarFeedbackMeta(feedback, `${contas.length} conta(s) listada(s).`, "ok");
  } catch (error) {
    mostrarFeedbackMeta(feedback, error.message, "erro");
  }
}

async function testarConexaoMeta() {
  const feedback = document.getElementById("sync-meta-feedback");
  const tokenInput = document.getElementById("meta-access-token");
  const selectEl = document.getElementById("meta-account-select");
  const token = tokenInput?.value?.trim();
  const accountId = selectEl?.value || clienteMetaAccountId || null;

  const body = { meta_account_id: accountId, cliente_id: clienteId };
  if (token) body.access_token = token;

  if (!accountId) {
    mostrarFeedbackMeta(feedback, "Selecione uma conta (busque pelo token) ou cadastre o cliente com a conta correta.", "erro");
    feedback?.classList.remove("hidden");
    return;
  }

  feedback?.classList.remove("hidden");
  mostrarFeedbackMeta(feedback, "Testando conexão…", "info");
  try {
    const response = await fetch("/api/meta/testar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.mensagem || data.error || "Falha no teste.");
    mostrarFeedbackMeta(feedback, data.mensagem, "ok");
  } catch (error) {
    mostrarFeedbackMeta(feedback, error.message, "erro");
  }
}

async function sincronizarComMeta() {
  const btn = document.getElementById("btn-sincronizar-meta");
  const feedback = document.getElementById("sync-meta-feedback");
  if (!btn) return;

  const defaultLabel = btn.dataset.defaultLabel || btn.textContent.trim();
  btn.dataset.defaultLabel = defaultLabel;
  btn.disabled = true;
  btn.textContent = "Sincronizando…";
  if (feedback) {
    feedback.classList.add("hidden");
    feedback.textContent = "";
  }

  const tokenInput = document.getElementById("meta-access-token");
  const selectEl = document.getElementById("meta-account-select");
  const token = tokenInput?.value?.trim();
  const accountId = selectEl?.value?.trim();
  const body = {};
  if (token) body.access_token = token;
  if (accountId) body.meta_account_id = accountId;

  try {
    const response = await fetch(`/api/clientes/${clienteId}/sincronizar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json();

    if (!response.ok || !data.meta_sync) {
      throw new Error(data.meta_erro || "Falha ao sincronizar com a Meta.");
    }

    if (feedback) {
      feedback.textContent = `${data.campanhas_importadas} campanha(s) atualizada(s)`;
      feedback.className = "w-full text-sm text-emerald-400";
      feedback.classList.remove("hidden");
    }

    if (tokenInput && token) {
      tokenInput.value = "";
    }

    await aplicarFiltroPeriodo();
  } catch (error) {
    if (feedback) {
      feedback.textContent = error.message;
      feedback.className = "w-full text-sm text-red-400";
      feedback.classList.remove("hidden");
    }
  } finally {
    btn.disabled = false;
    btn.textContent = defaultLabel;
  }
}

document.getElementById("btn-buscar-contas-meta")?.addEventListener("click", buscarContasMetaCliente);
document.getElementById("btn-testar-meta")?.addEventListener("click", testarConexaoMeta);
document.getElementById("btn-sincronizar-meta")?.addEventListener("click", sincronizarComMeta);

renderChart(Array.isArray(chartData) ? chartData : []);

document.getElementById("form-diario")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const submitBtn = event.submitter;
  const formData = new FormData(form);
  const tagsRaw = (formData.get("tags") || "").toString();
  const tags = tagsRaw
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  const payload = {
    cliente_id: Number(formData.get("cliente_id")),
    data: formData.get("data"),
    tipo: formData.get("tipo"),
    descricao: formData.get("descricao"),
    tags,
  };

  setSubmitLoading(submitBtn, true);
  try {
    const response = await fetch("/api/diario", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Falha ao salvar entrada.");
    form.reset();
    window.location.reload();
  } catch (error) {
    alert(error.message);
    form.reset();
  } finally {
    setSubmitLoading(submitBtn, false);
  }
});
