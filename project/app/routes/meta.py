from flask import Blueprint, jsonify, request

from app.services.meta_service import (
    MetaApiError,
    listar_contas_anuncios,
    sanitizar_access_token,
    validar_conexao_meta,
)

meta_bp = Blueprint("meta_api", __name__)


@meta_bp.post("/meta/contas")
def contas_anuncios():
    """Lista contas de anúncios acessíveis pelo token (não usa .env)."""
    try:
        payload = request.get_json(silent=True) or {}
        access_token = sanitizar_access_token(payload.get("access_token"))
        if not access_token:
            return jsonify({"error": "access_token é obrigatório"}), 400

        contas = listar_contas_anuncios(access_token)
        return jsonify({"contas": contas}), 200
    except MetaApiError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Erro ao buscar contas na Meta"}), 500


@meta_bp.post("/meta/testar")
def testar_conexao():
    """Valida token + conta antes de cadastrar ou sincronizar."""
    try:
        from app.models.cliente import Cliente

        payload = request.get_json(silent=True) or {}
        access_token = payload.get("access_token")
        meta_account_id = payload.get("meta_account_id")
        cliente_id = payload.get("cliente_id")

        if not access_token and cliente_id:
            cliente = Cliente.query.get(cliente_id)
            if cliente and cliente.access_token:
                access_token = cliente.access_token

        if not access_token:
            return jsonify({"error": "Informe o access_token ou teste a partir de um cliente já cadastrado."}), 400
        if not meta_account_id:
            return jsonify({"error": "meta_account_id é obrigatório"}), 400

        resultado = validar_conexao_meta(access_token, meta_account_id)
        status = 200 if resultado.get("ok") else 400
        return jsonify(resultado), status
    except Exception:
        return jsonify({"ok": False, "mensagem": "Erro ao testar conexão"}), 500
