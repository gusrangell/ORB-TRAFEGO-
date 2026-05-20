from app.models import db


class CampanhaMetrica(db.Model):
    __tablename__ = "campanhas_metricas"
    __table_args__ = (
        db.UniqueConstraint("campanha_id", "data", name="uq_campanhas_metricas_campanha_data"),
        db.Index("idx_campanhas_metricas_cliente_data", "cliente_id", "data"),
    )

    id = db.Column(db.Integer, primary_key=True)
    campanha_id = db.Column(
        db.Integer,
        db.ForeignKey("campanhas.id", ondelete="CASCADE"),
        nullable=False,
    )
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    data = db.Column(db.Date, nullable=False)
    impressoes = db.Column(db.Integer, nullable=True)
    cliques = db.Column(db.Integer, nullable=True)
    conversoes = db.Column(db.Integer, nullable=True)
    investimento = db.Column(db.Numeric(10, 2), nullable=True)
    cpl = db.Column(db.Numeric(10, 2), nullable=True)
    ctr = db.Column(db.Numeric(7, 4), nullable=True)
    cpc = db.Column(db.Numeric(10, 2), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    campanha = db.relationship("Campanha", back_populates="metricas")
    cliente = db.relationship("Cliente", back_populates="campanhas_metricas")
