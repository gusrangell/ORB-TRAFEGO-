from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from app.models import db
from app.models.cliente import Cliente
from app.services.cliente_service import (
    alertas_urgentes,
    campanhas_consolidadas_cliente,
    consolidar_metricas_cliente,
    contagem_por_status,
    historico_diario_cliente,
    listar_clientes_com_status,
    montar_cliente_resumo,
    parse_periodo,
)
from app.services.meta_service import sanitizar_access_token, sincronizar_cliente, validar_conexao_meta

clientes_bp = Blueprint("clientes_api", __name__)


@clientes_bp.post("/clientes")
def criar_cliente():
    try:
        payload = request.get_json(silent=True) or {}
        nome = (payload.get("nome") or "").strip()
        meta_account_id = (payload.get("meta_account_id") or "").strip()
        access_token = sanitizar_access_token(payload.get("access_token"))

        if not nome:
            return jsonify({"error": "nome é obrigatório"}), 400
        if not meta_account_id:
            return jsonify({"error": "meta_account_id é obrigatório"}), 400
        if not access_token:
            return jsonify({"error": "access_token é obrigatório"}), 400

        check = validar_conexao_meta(access_token, meta_account_id)
        if not check.get("ok"):
            return jsonify({"error": check.get("mensagem")}), 400

        cliente = Cliente(
            nome=nome,
            meta_account_id=meta_account_id,
            access_token=access_token,
        )
        db.session.add(cliente)
        db.session.commit()

        sync_result = sincronizar_cliente(cliente.id, validar_antes=False)
        response = {"id": cliente.id, "nome": cliente.nome}
        if sync_result.get("meta_sync"):
            response["meta_sync"] = True
            response["campanhas_importadas"] = sync_result.get("campanhas_importadas", 0)
        else:
            response["meta_sync"] = False
            response["meta_erro"] = sync_result.get("meta_erro", "Falha ao sincronizar com a Meta.")

        return jsonify(response), 201
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Falha ao criar cliente"}), 500
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno do servidor"}), 500


@clientes_bp.get("/clientes")
def listar_clientes():
    try:
        return jsonify(listar_clientes_com_status()), 200
    except Exception:
        return jsonify({"error": "Erro interno do servidor"}), 500


@clientes_bp.get("/dashboard")
def dashboard():
    try:
        return (
            jsonify(
                {
                    "contagem": contagem_por_status(),
                    "alertas": alertas_urgentes(),
                }
            ),
            200,
        )
    except Exception:
        return jsonify({"error": "Erro interno do servidor"}), 500


@clientes_bp.get("/clientes/<int:id>")
def obter_cliente(id):
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({"error": "Cliente não encontrado"}), 404
        return jsonify(montar_cliente_resumo(cliente)), 200
    except Exception:
        return jsonify({"error": "Erro interno do servidor"}), 500


@clientes_bp.delete("/clientes/<int:id>")
def remover_cliente(id):
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({"error": "Cliente não encontrado"}), 404
        db.session.delete(cliente)
        db.session.commit()
        return jsonify({"message": "Cliente removido"}), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Falha ao remover cliente"}), 500
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno do servidor"}), 500


@clientes_bp.post("/clientes/<int:id>/sincronizar")
def sincronizar_cliente_meta(id):
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({"error": "Cliente não encontrado"}), 404

        payload = request.get_json(silent=True) or {}
        access_token = sanitizar_access_token(payload.get("access_token"))
        if access_token:
            cliente.access_token = access_token

        meta_account_id = (payload.get("meta_account_id") or "").strip()
        if meta_account_id:
            cliente.meta_account_id = meta_account_id

        if access_token or meta_account_id:
            db.session.commit()

        result = sincronizar_cliente(id)
        if result.get("meta_sync"):
            return (
                jsonify(
                    {
                        "meta_sync": True,
                        "campanhas_importadas": result.get("campanhas_importadas", 0),
                    }
                ),
                200,
            )

        status_code = 400 if result.get("meta_erro") else 500
        return (
            jsonify(
                {
                    "meta_sync": False,
                    "meta_erro": result.get("meta_erro", "Falha ao sincronizar com a Meta."),
                }
            ),
            status_code,
        )
    except Exception:
        return jsonify({"meta_sync": False, "meta_erro": "Erro interno do servidor"}), 500


@clientes_bp.get("/clientes/<int:id>/metricas-consolidadas")
def metricas_consolidadas(id):
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({"error": "Cliente não encontrado"}), 404

        data_inicio, data_fim, erro = parse_periodo(
            request.args.get("data_inicio"),
            request.args.get("data_fim"),
            usar_padrao=True,
        )
        if erro:
            return jsonify({"error": erro}), 400

        consolidado = consolidar_metricas_cliente(id, data_inicio, data_fim)
        historico = historico_diario_cliente(id, data_inicio, data_fim)
        return (
            jsonify(
                {
                    "data_inicio": data_inicio.isoformat(),
                    "data_fim": data_fim.isoformat(),
                    **consolidado,
                    "historico": historico,
                }
            ),
            200,
        )
    except Exception:
        return jsonify({"error": "Erro interno do servidor"}), 500


@clientes_bp.get("/clientes/<int:id>/campanhas")
def campanhas_cliente(id):
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({"error": "Cliente não encontrado"}), 404

        data_inicio, data_fim, erro = parse_periodo(
            request.args.get("data_inicio"),
            request.args.get("data_fim"),
            usar_padrao=True,
        )
        if erro:
            return jsonify({"error": erro}), 400

        return jsonify(campanhas_consolidadas_cliente(id, data_inicio, data_fim)), 200
    except Exception:
        return jsonify({"error": "Erro interno do servidor"}), 500
