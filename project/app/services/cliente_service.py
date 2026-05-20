from datetime import date, timedelta

from sqlalchemy import func, or_

from app.models.campanha import Campanha
from app.models.campanha_metrica import CampanhaMetrica
from app.models.cliente import Cliente
from app.models.diario import Diario

CANCELAMENTO_KEYWORDS = (
    "cancelamento",
    "cancelar",
    "cancelando",
    "quer cancelar",
    "vai cancelar",
)


STATUS_ORDER = {
    "critico": 0,
    "ruim": 1,
    "regular": 2,
    "bom": 3,
    "otimo": 4,
    "sem_dados": 5,
}


def classificar_cpl(cpl):
    if cpl is None:
        return {"status": "sem_dados", "label": "Sem dados", "classe": "gray"}

    cpl = float(cpl)
    if cpl < 8:
        return {"status": "otimo", "label": "Ótimo", "classe": "green"}
    if cpl < 10:
        return {"status": "bom", "label": "Bom", "classe": "blue"}
    if cpl < 20:
        return {"status": "regular", "label": "Regular", "classe": "yellow"}
    if cpl < 40:
        return {"status": "ruim", "label": "Ruim", "classe": "orange"}
    return {"status": "critico", "label": "Crítico", "classe": "red"}


def _as_float(value):
    return float(value) if value is not None else None


def _as_int(value):
    return int(value) if value is not None else 0


def periodo_padrao_7_dias():
    hoje = date.today()
    return hoje - timedelta(days=6), hoje


def periodo_status_dashboard():
    hoje = date.today()
    return hoje - timedelta(days=7), hoje


def parse_periodo(data_inicio_str=None, data_fim_str=None, usar_padrao=True):
    if usar_padrao and (not data_inicio_str or not data_fim_str):
        data_inicio, data_fim = periodo_padrao_7_dias()
        return data_inicio, data_fim, None

    try:
        data_inicio = date.fromisoformat(data_inicio_str) if data_inicio_str else None
        data_fim = date.fromisoformat(data_fim_str) if data_fim_str else None
    except ValueError:
        return None, None, "Formato de data inválido. Use YYYY-MM-DD."

    if data_inicio is None or data_fim is None:
        return None, None, "data_inicio e data_fim devem ser enviados juntos."

    if data_inicio > data_fim:
        return None, None, "data_inicio não pode ser maior que data_fim."

    return data_inicio, data_fim, None


def consolidar_metricas_cliente(cliente_id, data_inicio, data_fim):
    resultado = (
        CampanhaMetrica.query.with_entities(
            func.sum(CampanhaMetrica.investimento),
            func.sum(CampanhaMetrica.conversoes),
            func.sum(CampanhaMetrica.cliques),
            func.sum(CampanhaMetrica.impressoes),
        )
        .filter(
            CampanhaMetrica.cliente_id == cliente_id,
            CampanhaMetrica.data >= data_inicio,
            CampanhaMetrica.data <= data_fim,
        )
        .first()
    )

    investimento_total = _as_float(resultado[0]) or 0.0
    conversoes_total = _as_int(resultado[1])
    cliques_total = _as_int(resultado[2])
    impressoes_total = _as_int(resultado[3])

    cpl = (investimento_total / conversoes_total) if conversoes_total > 0 else None
    cpc = (investimento_total / cliques_total) if cliques_total > 0 else None
    ctr = (cliques_total / impressoes_total) if impressoes_total > 0 else None

    return {
        "cpl": cpl,
        "ctr": ctr,
        "cpc": cpc,
        "conversoes": conversoes_total,
        "investimento": investimento_total,
    }


def historico_diario_cliente(cliente_id, data_inicio, data_fim):
    linhas = (
        CampanhaMetrica.query.with_entities(
            CampanhaMetrica.data,
            func.sum(CampanhaMetrica.investimento),
            func.sum(CampanhaMetrica.conversoes),
        )
        .filter(
            CampanhaMetrica.cliente_id == cliente_id,
            CampanhaMetrica.data >= data_inicio,
            CampanhaMetrica.data <= data_fim,
        )
        .group_by(CampanhaMetrica.data)
        .order_by(CampanhaMetrica.data.asc())
        .all()
    )

    mapa = {linha[0]: {"investimento": _as_float(linha[1]) or 0.0, "conversoes": _as_int(linha[2])} for linha in linhas}
    historico = []
    dia = data_inicio
    while dia <= data_fim:
        investimento = mapa.get(dia, {}).get("investimento", 0.0)
        conversoes = mapa.get(dia, {}).get("conversoes", 0)
        cpl = (investimento / conversoes) if conversoes > 0 else None
        historico.append(
            {
                "data": dia.isoformat(),
                "cpl": cpl,
                "investimento": investimento,
                "conversoes": conversoes,
            }
        )
        dia += timedelta(days=1)
    return historico


def campanhas_consolidadas_cliente(cliente_id, data_inicio, data_fim):
    linhas = (
        Campanha.query.outerjoin(
            CampanhaMetrica,
            (CampanhaMetrica.campanha_id == Campanha.id)
            & (CampanhaMetrica.data >= data_inicio)
            & (CampanhaMetrica.data <= data_fim),
        )
        .with_entities(
            Campanha.id,
            Campanha.campaign_id,
            Campanha.nome,
            Campanha.status,
            func.sum(CampanhaMetrica.investimento),
            func.sum(CampanhaMetrica.conversoes),
            func.sum(CampanhaMetrica.cliques),
            func.sum(CampanhaMetrica.impressoes),
        )
        .filter(Campanha.cliente_id == cliente_id)
        .group_by(Campanha.id, Campanha.campaign_id, Campanha.nome, Campanha.status)
        .order_by(Campanha.nome.asc())
        .all()
    )

    campanhas = []
    for linha in linhas:
        investimento_total = _as_float(linha[4]) or 0.0
        conversoes_total = _as_int(linha[5])
        cliques_total = _as_int(linha[6])
        impressoes_total = _as_int(linha[7])
        campanhas.append(
            {
                "id": linha[0],
                "campaign_id": linha[1],
                "nome": linha[2],
                "status": linha[3],
                "cpl": (investimento_total / conversoes_total) if conversoes_total > 0 else None,
                "ctr": (cliques_total / impressoes_total) if impressoes_total > 0 else None,
                "cpc": (investimento_total / cliques_total) if cliques_total > 0 else None,
                "conversoes": conversoes_total,
                "investimento": investimento_total,
            }
        )
    return campanhas


def status_atual_cliente(cliente_id):
    inicio, fim = periodo_status_dashboard()
    consolidado = consolidar_metricas_cliente(cliente_id, inicio, fim)
    return classificar_cpl(consolidado["cpl"])


def montar_cliente_resumo(cliente):
    consolidado = consolidar_metricas_cliente(cliente.id, *periodo_status_dashboard())
    cpl_atual = consolidado["cpl"]
    classificacao = status_atual_cliente(cliente.id)
    return {
        "id": cliente.id,
        "nome": cliente.nome,
        "created_at": cliente.created_at.isoformat() if cliente.created_at else None,
        "cpl_atual": cpl_atual,
        **classificacao,
    }


def listar_clientes_com_status():
    clientes = Cliente.query.order_by(Cliente.nome.asc()).all()
    dados = [montar_cliente_resumo(cliente) for cliente in clientes]
    return sorted(dados, key=lambda item: STATUS_ORDER[item["status"]])


def obter_cliente_com_detalhes(cliente_id):
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return None

    diarios = (
        Diario.query.filter_by(cliente_id=cliente_id)
        .order_by(Diario.data.desc(), Diario.id.desc())
        .all()
    )
    return {"cliente": cliente, "diarios": diarios}


def _cliente_tem_risco_cancelamento(cliente_id):
    filtros = [func.lower(Diario.descricao).like(f"%{palavra}%") for palavra in CANCELAMENTO_KEYWORDS]
    return Diario.query.filter(Diario.cliente_id == cliente_id).filter(or_(*filtros)).first() is not None


def contagem_por_status():
    contagem = {
        "otimo": 0,
        "bom": 0,
        "regular": 0,
        "ruim": 0,
        "critico": 0,
        "sem_dados": 0,
        "total": 0,
    }
    clientes = Cliente.query.all()
    for cliente in clientes:
        status = status_atual_cliente(cliente.id)["status"]
        if status in contagem:
            contagem[status] += 1
        contagem["total"] += 1
    return contagem


def alertas_urgentes():
    alertas = []
    clientes = Cliente.query.order_by(Cliente.nome.asc()).all()
    inicio, fim = periodo_status_dashboard()

    for cliente in clientes:
        consolidado = consolidar_metricas_cliente(cliente.id, inicio, fim)
        cpl = consolidado["cpl"]
        classificacao = status_atual_cliente(cliente.id)
        risco_cancelamento = _cliente_tem_risco_cancelamento(cliente.id)
        cpl_critico = cpl is not None and float(cpl) >= 30

        if not risco_cancelamento and not cpl_critico:
            continue

        if risco_cancelamento:
            motivo = "Risco de cancelamento"
        else:
            motivo = f"CPL crítico (R$ {float(cpl):.2f})"

        alertas.append(
            {
                "id": cliente.id,
                "nome": cliente.nome,
                "motivo": motivo,
                "cpl": float(cpl) if cpl is not None else None,
                "status": classificacao["status"],
                "label": classificacao["label"],
                "classe": classificacao["classe"],
                "risco_cancelamento": risco_cancelamento,
            }
        )

    alertas.sort(
        key=lambda item: (
            0 if item["risco_cancelamento"] else 1,
            -(item["cpl"] if item["cpl"] is not None else 0),
        )
    )

    for item in alertas:
        item.pop("risco_cancelamento", None)

    return alertas
