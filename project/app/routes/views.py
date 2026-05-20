from flask import Blueprint, abort, render_template, request

from app.services.cliente_service import (
    campanhas_consolidadas_cliente,
    classificar_cpl,
    consolidar_metricas_cliente,
    historico_diario_cliente,
    listar_clientes_com_status,
    obter_cliente_com_detalhes,
    parse_periodo,
)

views_bp = Blueprint("views", __name__)


@views_bp.app_template_filter("badge_classes")
def badge_classes_filter(cor):
    classes = {
        "green": "bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/30",
        "blue": "bg-sky-500/15 text-sky-400 ring-1 ring-sky-500/30",
        "yellow": "bg-amber-500/15 text-amber-300 ring-1 ring-amber-500/35",
        "orange": "bg-orange-500/15 text-orange-400 ring-1 ring-orange-500/35",
        "red": "bg-red-500/15 text-red-400 ring-1 ring-red-500/35",
        "gray": "bg-slate-500/20 text-slate-400 ring-1 ring-slate-500/30",
    }
    return classes.get(cor, classes["gray"])


@views_bp.get("/")
def index():
    clientes = listar_clientes_com_status()
    return render_template("index.html", clientes=clientes)


@views_bp.get("/clientes/<int:id>")
def cliente_detalhe(id):
    detalhes = obter_cliente_com_detalhes(id)
    if detalhes is None:
        abort(404)

    data_inicio, data_fim, erro = parse_periodo(
        data_inicio_str=request.args.get("data_inicio"),
        data_fim_str=request.args.get("data_fim"),
        usar_padrao=True,
    )
    if erro:
        abort(400, description=erro)

    kpis = consolidar_metricas_cliente(id, data_inicio, data_fim)
    historico = historico_diario_cliente(id, data_inicio, data_fim)
    campanhas = campanhas_consolidadas_cliente(id, data_inicio, data_fim)
    status = classificar_cpl(kpis["cpl"])
    chart_has_data = any(item["cpl"] is not None for item in historico)

    return render_template(
        "cliente.html",
        cliente=detalhes["cliente"],
        status=status,
        diarios=detalhes["diarios"],
        kpis=kpis,
        historico_json=historico,
        chart_has_data=chart_has_data,
        campanhas=campanhas,
        data_inicio=data_inicio.isoformat(),
        data_fim=data_fim.isoformat(),
    )
