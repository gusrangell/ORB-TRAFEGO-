from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models so SQLAlchemy metadata is aware of all tables.
from app.models.campanha import Campanha  # noqa: E402,F401
from app.models.campanha_metrica import CampanhaMetrica  # noqa: E402,F401
from app.models.cliente import Cliente  # noqa: E402,F401
from app.models.diario import Diario  # noqa: E402,F401
from app.models.metrica import Metrica  # noqa: E402,F401
