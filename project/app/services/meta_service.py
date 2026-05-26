from datetime import date
from decimal import Decimal

import requests
from requests import RequestException

from app.models import db
from app.models.campanha import Campanha
from app.models.campanha_metrica import CampanhaMetrica
from app.models.cliente import Cliente


GRAPH_API_VERSION = "v23.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class MetaApiError(Exception):
    pass


def sanitizar_access_token(token):
    if not token:
        return ""

    token = str(token).strip()

    if len(token) >= 2 and token[0] == token[-1] and token[0] in ('"', "'"):
        token = token[1:-1].strip()

    return token


def _sanitize_meta_account_id(meta_account_id):
    if not meta_account_id:
        return ""

    account_id = str(meta_account_id).strip()

    if account_id.startswith("act_"):
        return account_id[4:]

    return account_id


def _meta_get(url, params):
    try:
        response = requests.get(url, params=params, timeout=30)
    except RequestException as exc:
        raise MetaApiError(f"Falha de comunicação com a API da Meta: {str(exc)}") from exc

    try:
        data = response.json()
    except ValueError:
        raise MetaApiError(
            f"Resposta inválida da API da Meta. "
            f"HTTP {response.status_code}: {response.text[:500]}"
        )

    if not response.ok:
        if isinstance(data, dict) and "error" in data:
            error = data["error"]
            message = error.get("message", "Erro na API da Meta")
            code = error.get("code")
            error_subcode = error.get("error_subcode")
            error_type = error.get("type")

            raise MetaApiError(
                f"{message} | type={error_type} | code={code} | subcode={error_subcode}"
            )

        raise MetaApiError(
            f"Erro HTTP {response.status_code} na API da Meta: {data}"
        )

    if isinstance(data, dict) and "error" in data:
        error = data["error"]
        message = error.get("message", "Erro na API da Meta")
        code = error.get("code")
        error_subcode = error.get("error_subcode")
        error_type = error.get("type")

        raise MetaApiError(
            f"{message} | type={error_type} | code={code} | subcode={error_subcode}"
        )

    return data


def _fetch_paginated(url, params):
    items = []
    next_url = url
    next_params = dict(params)

    while next_url:
        data = _meta_get(next_url, next_params)

        items.extend(data.get("data", []))

        paging = data.get("paging", {})
        next_url = paging.get("next")

        # Quando a Meta retorna a URL completa em paging.next,
        # os parâmetros já estão embutidos nela.
        next_params = None

    return items


def listar_contas_anuncios(access_token):
    """Lista contas de anúncios que o token pode acessar."""
    token = sanitizar_access_token(access_token)

    if not token:
        raise MetaApiError("Informe o Access Token da Meta.")

    url = f"{BASE_URL}/me/adaccounts"

    params = {
        "fields": "id,name,account_id,account_status,currency",
        "limit": 100,
        "access_token": token,
    }

    contas_raw = _fetch_paginated(url, params)

    contas = []

    for item in contas_raw:
        account_id = item.get("account_id") or _sanitize_meta_account_id(item.get("id", ""))

        if not account_id:
            continue

        contas.append(
            {
                "account_id": str(account_id),
                "nome": item.get("name") or f"Conta {account_id}",
                "act_id": item.get("id") or f"act_{account_id}",
                "account_status": item.get("account_status"),
                "currency": item.get("currency"),
            }
        )

    return contas


def validar_conexao_meta(access_token, meta_account_id):
    """
    Valida token e acesso à conta antes de sincronizar.
    Retorna dict com ok, mensagem e contas, se o token for válido mas a conta estiver errada.
    """
    token = sanitizar_access_token(access_token)

    if not token:
        return {"ok": False, "mensagem": "Access Token é obrigatório."}

    account_id = _sanitize_meta_account_id(meta_account_id)

    if not account_id:
        return {"ok": False, "mensagem": "Meta Account ID é obrigatório."}

    try:
        _meta_get(
            f"{BASE_URL}/me",
            {
                "fields": "id,name",
                "access_token": token,
            },
        )
    except MetaApiError as exc:
        return {
            "ok": False,
            "mensagem": f"Token inválido ou expirado: {exc}",
        }

    try:
        contas = listar_contas_anuncios(token)
    except MetaApiError as exc:
        return {
            "ok": False,
            "mensagem": f"Token sem permissão para listar contas de anúncios: {exc}",
        }

    ids_acessiveis = {str(c["account_id"]) for c in contas}

    if account_id not in ids_acessiveis:
        nomes = ", ".join(
            f"{c['nome']} ({c['account_id']})"
            for c in contas[:5]
        )

        extra = f" e mais {len(contas) - 5}" if len(contas) > 5 else ""

        return {
            "ok": False,
            "mensagem": (
                f"A conta {account_id} não está disponível para este token. "
                f"Contas acessíveis: {nomes}{extra}."
            ),
            "contas": contas,
        }

    try:
        _meta_get(
            f"{BASE_URL}/act_{account_id}/campaigns",
            {
                "fields": "id",
                "limit": 1,
                "access_token": token,
            },
        )
    except MetaApiError as exc:
        return {
            "ok": False,
            "mensagem": str(exc),
            "contas": contas,
        }

    return {
        "ok": True,
        "mensagem": f"Conexão OK. {len(contas)} conta(s) disponível(is) para este token.",
        "contas": contas,
    }


def _extract_leads(actions):
    if not actions:
        return 0

    action_map = {}

    for action in actions:
        action_type = action.get("action_type")
        value = action.get("value", 0)

        if not action_type:
            continue
     
        try:
            action_map[action_type] = int(float(value))
        except (TypeError, ValueError):
            action_map[action_type] = 0

    print("ACTIONS META MAP:", action_map)

    priority_action_types = [   
        "onsite_conversion.messaging_conversation_started_7d",
        "messaging_conversation_started_7d",
        "onsite_conversion.messaging_first_reply",
        "onsite_conversion.messaging_lead",
        "lead",
        "onsite_conversion.lead",
        "onsite_conversion.lead_grouped",
        "offsite_conversion.fb_pixel_lead",
        "leadgen_grouped",
        "complete_registration",
        "submit_application",
    ]

    for action_type in priority_action_types:
        if action_type in action_map:
            return action_map[action_type]

    return 0

def _parse_decimal(value):
    if value is None or value == "":
        return None

    return Decimal(str(value))


def _parse_int(value):
    if value is None or value == "":
        return None

    return int(float(value))


def _upsert_campanha(cliente_id, campaign_id, nome, status):
    campanha = Campanha.query.filter_by(
        cliente_id=cliente_id,
        campaign_id=campaign_id,
    ).first()

    if campanha is None:
        campanha = Campanha(
            cliente_id=cliente_id,
            campaign_id=campaign_id,
            nome=nome,
            status=status,
        )

        db.session.add(campanha)
        db.session.flush()
    else:
        campanha.nome = nome
        campanha.status = status

    return campanha


def _upsert_metrica(
    campanha,
    data_ref,
    impressoes,
    cliques,
    conversoes,
    investimento,
    ctr,
    cpc,
):
    investimento_float = float(investimento) if investimento is not None else 0.0
    conversoes_int = conversoes or 0

    cpl = (investimento_float / conversoes_int) if conversoes_int > 0 else None

    registro = CampanhaMetrica.query.filter_by(
        campanha_id=campanha.id,
        data=data_ref,
    ).first()

    if registro is None:
        registro = CampanhaMetrica(
            campanha_id=campanha.id,
            cliente_id=campanha.cliente_id,
            data=data_ref,
        )

        db.session.add(registro)

    registro.impressoes = impressoes
    registro.cliques = cliques
    registro.conversoes = conversoes
    registro.investimento = investimento
    registro.ctr = ctr
    registro.cpc = cpc
    registro.cpl = Decimal(str(round(cpl, 2))) if cpl is not None else None


def _fetch_campaigns(account_id, access_token):
    url = f"{BASE_URL}/act_{account_id}/campaigns"

    params = {
        "fields": "id,name,status",
        "access_token": access_token,
    }

    return _fetch_paginated(url, params)


def _fetch_campaign_insights(campaign_id, access_token):
    url = f"{BASE_URL}/{campaign_id}/insights"

    params = {
        "fields": "impressions,clicks,spend,actions,ctr,cpc,date_start",
        "time_increment": "1",
        "date_preset": "last_30d",
        "access_token": access_token,
    }

    return _fetch_paginated(url, params)


def _obter_access_token(cliente):
    return sanitizar_access_token(cliente.access_token)


def sincronizar_cliente(cliente_id, validar_antes=True):
    cliente = Cliente.query.get(cliente_id)

    if not cliente:
        return {
            "meta_sync": False,
            "meta_erro": "Cliente não encontrado",
        }

    if not cliente.meta_account_id:
        return {
            "meta_sync": False,
            "meta_erro": "Meta Account ID é necessário para sincronizar.",
        }

    access_token = _obter_access_token(cliente)

    if not access_token:
        return {
            "meta_sync": False,
            "meta_erro": "Access Token da Meta é necessário. Cadastre ou informe o token na sincronização.",
        }

    account_id = _sanitize_meta_account_id(cliente.meta_account_id)

    if validar_antes:
        check = validar_conexao_meta(access_token, account_id)

        if not check.get("ok"):
            return {
                "meta_sync": False,
                "meta_erro": check.get("mensagem"),
            }

    try:
        campaigns_data = _fetch_campaigns(account_id, access_token)

        campanhas_importadas = 0
        metricas_aviso = None

        for item in campaigns_data:
            campaign_id = str(item.get("id", "")).strip()

            if not campaign_id:
                continue

            campanha = _upsert_campanha(
                cliente_id=cliente.id,
                campaign_id=campaign_id,
                nome=item.get("name") or campaign_id,
                status=item.get("status"),
            )

            campanhas_importadas += 1

            try:
                insights = _fetch_campaign_insights(campaign_id, access_token)
            except MetaApiError as exc:
                metricas_aviso = str(exc)
                insights = []

            for insight in insights:
                date_start = insight.get("date_start")

                if not date_start:
                    continue

                data_ref = date.fromisoformat(date_start)

                impressoes = _parse_int(insight.get("impressions"))
                cliques = _parse_int(insight.get("clicks"))
                investimento = _parse_decimal(insight.get("spend"))
                conversoes = _extract_leads(insight.get("actions"))

                ctr_raw = insight.get("ctr")
                ctr = None

                if ctr_raw is not None and ctr_raw != "":
                    ctr = _parse_decimal(float(ctr_raw) / 100)

                cpc = _parse_decimal(insight.get("cpc"))

                _upsert_metrica(
                    campanha,
                    data_ref,
                    impressoes,
                    cliques,
                    conversoes,
                    investimento,
                    ctr,
                    cpc,
                )

        db.session.commit()

        result = {
            "meta_sync": True,
            "campanhas_importadas": campanhas_importadas,
        }

        if metricas_aviso:
            result["aviso"] = (
                f"Campanhas importadas, mas algumas métricas falharam: {metricas_aviso}"
            )

        return result

    except MetaApiError as exc:
        db.session.rollback()

        return {
            "meta_sync": False,
            "meta_erro": str(exc),
        }

    except Exception as exc:
        db.session.rollback()

        return {
            "meta_sync": False,
            "meta_erro": f"Erro inesperado ao sincronizar com a Meta: {str(exc)}",
        }