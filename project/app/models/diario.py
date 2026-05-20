import json

from app.models import db


class Diario(db.Model):
    __tablename__ = "diario"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id", ondelete="CASCADE"),
        nullable=False,
    )
    data = db.Column(db.Date, nullable=False)
    tipo = db.Column(
        db.Enum("criativo", "ajuste", "teste", "analise", "outro", name="tipo_diario"),
        nullable=False,
    )
    descricao = db.Column(db.Text, nullable=False)
    tags = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    cliente = db.relationship("Cliente", back_populates="diarios")

    @property
    def tags_list(self):
        if self.tags is None:
            return []
        if isinstance(self.tags, list):
            return self.tags
        if isinstance(self.tags, str):
            try:
                parsed = json.loads(self.tags)
                return parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                return []
        return []
