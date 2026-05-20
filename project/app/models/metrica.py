from app.models import db


class Metrica(db.Model):
    __tablename__ = "metricas"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id", ondelete="CASCADE"),
        nullable=False,
    )
    data = db.Column(db.Date, nullable=False)
    cpl = db.Column(db.Numeric(10, 2), nullable=True)
    ctr = db.Column(db.Numeric(5, 2), nullable=True)
    cpc = db.Column(db.Numeric(10, 2), nullable=True)
    conversoes = db.Column(db.Integer, nullable=True)
    investimento = db.Column(db.Numeric(10, 2), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    cliente = db.relationship("Cliente", back_populates="metricas")
