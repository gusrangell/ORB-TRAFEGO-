from app.models import db


class Campanha(db.Model):
    __tablename__ = "campanhas"
    __table_args__ = (
        db.UniqueConstraint("cliente_id", "campaign_id", name="uq_campanhas_cliente_campaign"),
        db.Index("idx_campanhas_cliente_id", "cliente_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id", ondelete="CASCADE"),
        nullable=False,
    )
    campaign_id = db.Column(db.String(100), nullable=False)
    nome = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    cliente = db.relationship("Cliente", back_populates="campanhas")
    metricas = db.relationship(
        "CampanhaMetrica",
        back_populates="campanha",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
