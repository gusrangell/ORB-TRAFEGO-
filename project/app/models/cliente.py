from app.models import db


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    meta_account_id = db.Column(db.String(50), nullable=True)
    access_token = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    metricas = db.relationship(
        "Metrica",
        back_populates="cliente",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    diarios = db.relationship(
        "Diario",
        back_populates="cliente",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    campanhas = db.relationship(
        "Campanha",
        back_populates="cliente",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    campanhas_metricas = db.relationship(
        "CampanhaMetrica",
        back_populates="cliente",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
