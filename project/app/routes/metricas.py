from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from app.models import db
from app.models.cliente import Cliente
from app.models.metrica import Metrica

metricas_bp = Blueprint("metricas_api", __name__)


@metricas_bp.post("/metricas")
def criar_metrica():
    try:
        payload = request.get_json(silent=True) or {}
        cliente_id = payload.get("cliente_id")
        data_str = payload.get("data")
        if not cliente_id or not data_str:
            return jsonify({"error": "cliente_id e data são obrigatórios"}), 400

        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({"error": "Cliente não encontrado"}), 404

        metrica = Metrica(
            cliente_id=cliente_id,
            data=date.fromisoformat(data_str),
            cpl=payload.get("cpl"),
            ctr=payload.get("ctr"),
            cpc=payload.get("cpc"),
            conversoes=payload.get("conversoes"),
            investimento=payload.get("investimento"),
        )
        db.session.add(metrica)
        db.session.commit()
        return (
            jsonify(
                {
                    "id": metrica.id,
                    "cliente_id": metrica.cliente_id,
                    "data": metrica.data.isoformat(),
                    "cpl": float(metrica.cpl) if metrica.cpl is not None else None,
                }
            ),
            201,
        )
    except ValueError:
        return jsonify({"error": "Data inválida, use YYYY-MM-DD"}), 400
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Falha ao criar métrica"}), 500
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno do servidor"}), 500


@metricas_bp.get("/metricas/<int:cliente_id>")
def listar_metricas(cliente_id):
    try:
        metricas = (
            Metrica.query.filter_by(cliente_id=cliente_id)
            .order_by(Metrica.data.desc(), Metrica.id.desc())
            .all()
        )
        return (
            jsonify(
                [
                    {
                        "id": metrica.id,
                        "data": metrica.data.isoformat(),
                        "cpl": float(metrica.cpl) if metrica.cpl is not None else None,
                        "ctr": float(metrica.ctr) if metrica.ctr is not None else None,
                        "cpc": float(metrica.cpc) if metrica.cpc is not None else None,
                        "conversoes": metrica.conversoes,
                        "investimento": (
                            float(metrica.investimento)
                            if metrica.investimento is not None
                            else None
                        ),
                    }
                    for metrica in metricas
                ]
            ),
            200,
        )
    except Exception:
        return jsonify({"error": "Erro interno do servidor"}), 500
