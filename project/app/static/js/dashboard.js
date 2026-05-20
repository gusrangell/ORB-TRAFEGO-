const MODAL_TRANSITION_MS = 200;

const STATUS_CHART_COLORS = {
  otimo: "#34d399",
  bom: "#38bdf8",
  regular: "#fbbf24",
  ruim: "#fb923c",
  critico: "#f87171",
  sem_dados: "#94a3b8",
};

const STATUS_LABELS = {
  otimo: "Ótimo",
  bom: "Bom",
  regular: "Regular",
  ruim: "Ruim",
  critico: "Crítico",
  sem_dados: "Sem dados",
};

const BADGE_CLASSES = {
  green: "bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/30",
  blue: "bg-sky-500/15 text-sky-400 ring-1 ring-sky-500/30",
  yellow: "bg-amber-500/15 text-amber-300 ring-1 ring-amber-500/35",
  orange: "bg-orange-500/15 text-orange-400 ring-1 ring-orange-500/35",
  red: "bg-red-500/15 text-red-400 ring-1 ring-red-500/35",
  gray: "bg-slate-500/20 text-slate-400 ring-1 ring-slate-500/30",
};

let statusDonutChart = null;
let filtroStatusAtivo = "all";

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

function aplicarFiltroCards(status) {
  filtroStatusAtivo = status;
  document.querySelectorAll(".kpi-filter-card").forEach((card) => {
    const ativo = card.dataset.filtroStatus === status;
    card.classList.toggle("ring-2", ativo);
    card.classList.toggle("ring-green-500/40", ativo);
  });

  document.querySelectorAll(".cliente-card").forEach((card) => {
    if (status === "all") {
      card.classList.remove("hidden");
      return;
    }
    card.classList.toggle("hidden", card.dataset.status !== status);
  });
}

function renderStatusLegend(contagem) {
  const legend = document.getElementById("status-legend");
  if (!legend) return;

  const ordem = ["otimo", "bom", "regular", "ruim", "critico", "sem_dados"];
  legend.innerHTML = ordem
    .map((status) => {
      const total = contagem[status] || 0;
      return `
        <li class="flex items-center justify-between gap-4 min-w-[180px]">
          <span class="flex items-center gap-2 text-[#f1f5f9]">
            <span class="h-2.5 w-2.5 rounded-full" style="background-color: ${STATUS_CHART_COLORS[status]}"></span>
            ${STATUS_LABELS[status]}
          </span>
          <span class="font-semibold tabular-nums text-[#94a3b8]">${total}</span>
        </li>
      `;
    })
    .join("");
}

function renderStatusDonut(contagem) {
  const canvas = document.getElementById("statusDonutChart");
  if (!canvas) return;

  const labels = [];
  const data = [];
  const colors = [];
  const ordem = ["otimo", "bom", "regular", "ruim", "critico", "sem_dados"];

  ordem.forEach((status) => {
    const valor = contagem[status] || 0;
    if (valor > 0) {
      labels.push(STATUS_LABELS[status]);
      data.push(valor);
      colors.push(STATUS_CHART_COLORS[status]);
    }
  });

  if (statusDonutChart) {
    statusDonutChart.destroy();
    statusDonutChart = null;
  }

  if (data.length === 0) {
    return;
  }

  statusDonutChart = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data,
          backgroundColor: colors,
          borderColor: "#1e293b",
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "62%",
      plugins: {
        legend: { display: false },
      },
    },
  });
}

function renderAlertas(alertas) {
  const lista = document.getElementById("alertas-urgentes");
  if (!lista) return;

  if (!Array.isArray(alertas) || alertas.length === 0) {
    lista.innerHTML = '<li class="text-sm text-[#94a3b8]">Nenhum alerta no momento</li>';
    return;
  }

  lista.innerHTML = alertas
    .map((alerta) => {
      const badgeClass = BADGE_CLASSES[alerta.classe] || BADGE_CLASSES.gray;
      return `
        <li class="rounded-xl border border-[#334155] bg-[#0f172a]/50 p-4">
          <div class="flex flex-wrap items-start justify-between gap-2">
            <a href="/clientes/${alerta.id}" class="font-semibold text-[#f1f5f9] hover:text-white">${alerta.nome}</a>
            <span class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ${badgeClass}">${alerta.label}</span>
          </div>
          <p class="mt-2 text-sm text-[#94a3b8]">${alerta.motivo}</p>
        </li>
      `;
    })
    .join("");
}

function atualizarDashboardKpis(contagem) {
  const atencao = (contagem.ruim || 0) + (contagem.critico || 0);
  const titulo = document.getElementById("dashboard-atencao");
  if (titulo) {
    const texto = atencao === 1 ? "cliente exigindo" : "clientes exigindo";
    titulo.textContent = `Você tem ${atencao} ${texto} atenção hoje`;
  }

  const mapa = {
    "kpi-total": contagem.total,
    "kpi-otimo": contagem.otimo,
    "kpi-bom": contagem.bom,
    "kpi-regular": contagem.regular,
    "kpi-ruim": contagem.ruim,
    "kpi-critico": contagem.critico,
  };

  Object.entries(mapa).forEach(([id, valor]) => {
    const el = document.getElementById(id);
    if (el) el.textContent = valor ?? 0;
  });
}

async function carregarDashboard() {
  try {
    const response = await fetch("/api/dashboard");
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Falha ao carregar dashboard.");

    const contagem = data.contagem || {};
    atualizarDashboardKpis(contagem);
    renderStatusLegend(contagem);
    renderStatusDonut(contagem);
    renderAlertas(data.alertas || []);
  } catch (error) {
    const titulo = document.getElementById("dashboard-atencao");
    if (titulo) titulo.textContent = "Não foi possível carregar o painel";
    const lista = document.getElementById("alertas-urgentes");
    if (lista) {
      lista.innerHTML = `<li class="text-sm text-red-400">${error.message}</li>`;
    }
  }
}

async function removerCliente(id, nome, cardElement) {
  const confirmacao = window.confirm(
    `Tem certeza que deseja remover ${nome}? Esta ação não pode ser desfeita.`
  );
  if (!confirmacao) return;

  try {
    const response = await fetch(`/api/clientes/${id}`, { method: "DELETE" });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Falha ao remover cliente.");

    cardElement?.remove();
    await carregarDashboard();
    aplicarFiltroCards(filtroStatusAtivo);

    const lista = document.getElementById("lista-clientes");
    if (lista && lista.querySelectorAll(".cliente-card").length === 0) {
      window.location.reload();
    }
  } catch (error) {
    alert(error.message);
  }
}

document.getElementById("btn-open-modal-cliente")?.addEventListener("click", () => {
  openModal("modal-cliente");
});

document.getElementById("btn-empty-open-modal-cliente")?.addEventListener("click", () => {
  openModal("modal-cliente");
});

document.querySelectorAll(".close-modal").forEach((button) => {
  button.addEventListener("click", () => {
    closeModal(button.dataset.target);
  });
});

document.getElementById("modal-cliente")?.addEventListener("click", (event) => {
  if (event.target.id === "modal-cliente") {
    closeModal("modal-cliente");
  }
});

document.querySelectorAll(".kpi-filter-card").forEach((card) => {
  card.addEventListener("click", () => {
    aplicarFiltroCards(card.dataset.filtroStatus || "all");
  });
});

document.getElementById("lista-clientes")?.addEventListener("click", (event) => {
  const btn = event.target.closest(".btn-remover-cliente");
  if (!btn) return;
  event.preventDefault();
  event.stopPropagation();
  const card = btn.closest(".cliente-card");
  removerCliente(btn.dataset.id, btn.dataset.nome, card);
});

function mostrarFeedbackMeta(el, texto, tipo) {
  if (!el) return;
  el.textContent = texto;
  el.classList.remove("hidden", "text-red-400", "text-emerald-400", "text-[#94a3b8]");
  if (tipo === "erro") el.classList.add("text-red-400");
  else if (tipo === "ok") el.classList.add("text-emerald-400");
  else el.classList.add("text-[#94a3b8]");
}

async function buscarContasMeta(tokenInput, selectEl, feedbackEl) {
  const token = tokenInput?.value?.trim();
  if (!token) {
    mostrarFeedbackMeta(feedbackEl, "Cole o Access Token antes de buscar contas.", "erro");
    return;
  }
  mostrarFeedbackMeta(feedbackEl, "Buscando contas na Meta…", "info");
  try {
    const response = await fetch("/api/meta/contas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ access_token: token }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Falha ao buscar contas.");

    const contas = data.contas || [];
    if (!contas.length) {
      selectEl.innerHTML = '<option value="">Nenhuma conta encontrada para este token</option>';
      selectEl.disabled = true;
      mostrarFeedbackMeta(feedbackEl, "Nenhuma conta de anúncios acessível com este token.", "erro");
      return;
    }

    selectEl.innerHTML =
      '<option value="">Selecione a conta de anúncios</option>' +
      contas
        .map(
          (c) =>
            `<option value="${c.account_id}">${c.nome} (${c.account_id})</option>`
        )
        .join("");
    selectEl.disabled = false;
    mostrarFeedbackMeta(
      feedbackEl,
      `${contas.length} conta(s) encontrada(s). Selecione a correta.`,
      "ok"
    );
  } catch (error) {
    mostrarFeedbackMeta(feedbackEl, error.message, "erro");
  }
}

document.getElementById("btn-buscar-contas-meta")?.addEventListener("click", () => {
  buscarContasMeta(
    document.getElementById("access_token"),
    document.getElementById("meta_account_id"),
    document.getElementById("meta-contas-feedback")
  );
});

document.getElementById("form-cliente")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const submitBtn = event.submitter;
  const formData = new FormData(form);
  const accountId = formData.get("meta_account_id");
  if (!accountId) {
    alert("Busque as contas pelo token e selecione uma conta de anúncios.");
    return;
  }

  const payload = {
    nome: formData.get("nome"),
    meta_account_id: accountId,
    access_token: formData.get("access_token"),
  };

  setSubmitLoading(submitBtn, true);
  try {
    const response = await fetch("/api/clientes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Falha ao cadastrar cliente.");
    }

    closeModal("modal-cliente");

    if (data.meta_sync) {
      alert(
        `Cliente "${data.nome}" cadastrado com sucesso. ${data.campanhas_importadas} campanha(s) importada(s) da Meta.`
      );
    } else {
      alert(
        `Cliente "${data.nome}" cadastrado, mas a sincronização com a Meta falhou: ${data.meta_erro || "erro desconhecido"}.`
      );
    }
    window.location.reload();
  } catch (error) {
    alert(error.message);
  } finally {
    setSubmitLoading(submitBtn, false);
  }
});

carregarDashboard();
