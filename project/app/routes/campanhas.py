from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models import db
from app.models.campanha import Campanha
from app.models.campanha_metrica import CampanhaMetrica
from app.models.cliente import Cliente

campanhas_bp = Blueprint("campanhas_api", __name__)


@campanhas_bp.post("/campanhas")
def criar_campanha():
    try:
        payload = request.get_json(silent=True) or {}
        cliente_id = payload.get("cliente_id")
        campaign_id = payload.get("campaign_id")
        nome = payload.get("nome")
        status = payload.get("status")

        if not cliente_id or not campaign_id or not nome:
            return jsonify({"error": "cliente_id, campaign_id e nome são obrigatórios"}), 400

        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({"error": "Cliente não encontrado"}), 404

        campanha = Campanha(
            cliente_id=cliente_id,
            campaign_id=str(campaign_id).strip(),
            nome=str(nome).strip(),
            status=status,
        )
        db.session.add(campanha)
        db.session.commit()
        return jsonify({"id": campanha.id, "nome": campanha.nome}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Campanha já cadastrada para este cliente"}), 409
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Falha ao criar campanha"}), 500
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno do servidor"}), 500


@campanhas_bp.post("/campanhas-metricas")
def upsert_campanha_metrica():
    try:
        payload = request.get_json(silent=True) or {}
        campanha_id = payload.get("campanha_id")
        cliente_id = payload.get("cliente_id")
        data_str = payload.get("data")
        if not campanha_id or not cliente_id or not data_str:
            return jsonify({"error": "campanha_id, cliente_id e data são obrigatórios"}), 400

        campanha = Campanha.query.get(campanha_id)
        if not campanha or campanha.cliente_id != cliente_id:
            return jsonify({"error": "Campanha não encontrada para este cliente"}), 404

        data_ref = date.fromisoformat(data_str)
        registro = CampanhaMetrica.query.filter_by(campanha_id=campanha_id, data=data_ref).first()
        if registro is None:
            registro = CampanhaMetrica(campanha_id=campanha_id, cliente_id=cliente_id, data=data_ref)
            db.session.add(registro)

        registro.impressoes = payload.get("impressoes")
        registro.cliques = payload.get("cliques")
        registro.conversoes = payload.get("conversoes")
        registro.investimento = payload.get("investimento")
        registro.cpl = payload.get("cpl")
        registro.ctr = payload.get("ctr")
        registro.cpc = payload.get("cpc")

        db.session.commit()
        return jsonify({"id": registro.id, "campanha_id": registro.campanha_id, "data": registro.data.isoformat()}), 201
    except ValueError:
        return jsonify({"error": "Data inválida, use YYYY-MM-DD"}), 400
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Falha ao salvar métrica de campanha"}), 500
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro interno do servidor"}), 500
