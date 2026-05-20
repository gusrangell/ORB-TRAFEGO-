from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from app.models import db
from app.models.cliente import Cliente
from app.models.diario import Diario

diario_bp = Blueprint("diario_api", __name__)


@diario_bp.post("/diario")
def criar_entrada_diario():
    try:
        payload = request.get_json(silent=True) or {}
        cliente_id = payload.get("cliente_id")
        data_str = payload.get("data")
        tipo = payload.get("tipo")
        descricao = payload.get("descricao")
        if not cliente_id or not data_str or not tipo or not descricao:
            return jsonify({"error": "cliente_id, data, tipo e descricao são obrigatórios"}), 400

        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({"error": "Cliente não encontrado"}), 404

        tags = payload.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        entrada = Diario(
            cliente_id=cliente_id,
            data=date.fromisoformat(data_str),
            tipo=tipo,
            descricao=descricao.strip(),
            tags=tags,
        )
        db.session.add(entrada)
        db.session.commit()
        return (
            jsonify(
                {
                    "id": entrada.id,
                    "cliente_id": entrada.cliente_id,
                    "data": entrada.data.isoformat(),
                    "tipo": entrada.tipo,
                }
            ),
            201,
        )
    except ValueError:
        return jsonify({"error": "Data inválida, use YYYY-MM-DD"}), 400
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Falha ao criar entrada de diário"}), 500
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno do servidor"}), 500


@diario_bp.get("/diario/<int:cliente_id>")
def listar_diario(cliente_id):
    try:
        entradas = (
            Diario.query.filter_by(cliente_id=cliente_id)
            .order_by(Diario.data.desc(), Diario.id.desc())
            .all()
        )
        return (
            jsonify(
                [
                    {
                        "id": entrada.id,
                        "data": entrada.data.isoformat(),
                        "tipo": entrada.tipo,
                        "descricao": entrada.descricao,
                        "tags": entrada.tags_list,
                    }
                    for entrada in entradas
                ]
            ),
            200,
        )
    except Exception:
        return jsonify({"error": "Erro interno do servidor"}), 500
