from flask import Flask
from sqlalchemy import text

from app.models import db
from config import Config


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)

    # Register models metadata.
    from app.models.campanha import Campanha  # noqa: F401
    from app.models.campanha_metrica import CampanhaMetrica  # noqa: F401
    from app.models.cliente import Cliente  # noqa: F401
    from app.models.diario import Diario  # noqa: F401
    from app.models.metrica import Metrica  # noqa: F401

    with app.app_context():
        try:
            db.session.execute(text("SELECT 1"))
        except Exception as e:
            db.session.rollback()
            print("Erro ao conectar/criar banco:", e)
            print(
                "Não foi possível conectar ao MySQL. Certifique-se de que o banco "
                "'trafico_pago' existe e o MySQL está rodando."
            )
        else:
            try:
                db.session.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS campanhas (
                          id INT AUTO_INCREMENT PRIMARY KEY,
                          cliente_id INT NOT NULL,
                          campaign_id VARCHAR(100) NOT NULL,
                          nome VARCHAR(200) NOT NULL,
                          status VARCHAR(50) NULL,
                          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                          UNIQUE KEY uq_campanhas_cliente_campaign (cliente_id, campaign_id),
                          INDEX idx_campanhas_cliente_id (cliente_id),
                          CONSTRAINT fk_campanhas_cliente
                            FOREIGN KEY (cliente_id)
                            REFERENCES clientes(id)
                            ON DELETE CASCADE
                        )
                        """
                    )
                )
                db.session.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS campanhas_metricas (
                          id INT AUTO_INCREMENT PRIMARY KEY,
                          campanha_id INT NOT NULL,
                          cliente_id INT NOT NULL,
                          data DATE NOT NULL,
                          impressoes INT NULL,
                          cliques INT NULL,
                          conversoes INT NULL,
                          investimento DECIMAL(10,2) NULL,
                          cpl DECIMAL(10,2) NULL,
                          ctr DECIMAL(7,4) NULL,
                          cpc DECIMAL(10,2) NULL,
                          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                          UNIQUE KEY uq_campanhas_metricas_campanha_data (campanha_id, data),
                          INDEX idx_campanhas_metricas_cliente_data (cliente_id, data),
                          CONSTRAINT fk_campanhas_metricas_campanha
                            FOREIGN KEY (campanha_id)
                            REFERENCES campanhas(id)
                            ON DELETE CASCADE,
                          CONSTRAINT fk_campanhas_metricas_cliente
                            FOREIGN KEY (cliente_id)
                            REFERENCES clientes(id)
                        )
                        """
                    )
                )
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print("Erro ao conectar/criar banco:", e)

    from app.routes.campanhas import campanhas_bp
    from app.routes.clientes import clientes_bp
    from app.routes.meta import meta_bp
    from app.routes.diario import diario_bp
    from app.routes.metricas import metricas_bp
    from app.routes.views import views_bp

    app.register_blueprint(views_bp)
    app.register_blueprint(clientes_bp, url_prefix="/api")
    app.register_blueprint(meta_bp, url_prefix="/api")
    app.register_blueprint(campanhas_bp, url_prefix="/api")
    app.register_blueprint(metricas_bp, url_prefix="/api")
    app.register_blueprint(diario_bp, url_prefix="/api")

    return app
