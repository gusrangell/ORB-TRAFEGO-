from datetime import date, timedelta

from app import create_app
from app.models import db
from app.models.campanha import Campanha
from app.models.campanha_metrica import CampanhaMetrica
from app.models.cliente import Cliente


def dias_recentes(total=14):
    hoje = date.today()
    return [hoje - timedelta(days=offset) for offset in range(total - 1, -1, -1)]


def calcular_snapshot(investimento, conversoes, cliques, impressoes):
    cpl = (investimento / conversoes) if conversoes else None
    cpc = (investimento / cliques) if cliques else None
    ctr = (cliques / impressoes) if impressoes else None
    return cpl, ctr, cpc


def upsert_campanha(cliente_id, campaign_id, nome, status):
    campanha = Campanha.query.filter_by(cliente_id=cliente_id, campaign_id=campaign_id).first()
    if campanha is None:
        campanha = Campanha(
            cliente_id=cliente_id,
            campaign_id=campaign_id,
            nome=nome,
            status=status,
        )
        db.session.add(campanha)
        db.session.flush()
    else:
        campanha.nome = nome
        campanha.status = status
    return campanha


def upsert_metrica_campanha(campanha, data_ref, impressoes, cliques, conversoes, investimento):
    cpl, ctr, cpc = calcular_snapshot(investimento, conversoes, cliques, impressoes)
    registro = CampanhaMetrica.query.filter_by(campanha_id=campanha.id, data=data_ref).first()
    if registro is None:
        registro = CampanhaMetrica(campanha_id=campanha.id, cliente_id=campanha.cliente_id, data=data_ref)
        db.session.add(registro)

    registro.impressoes = impressoes
    registro.cliques = cliques
    registro.conversoes = conversoes
    registro.investimento = investimento
    registro.cpl = cpl
    registro.ctr = ctr
    registro.cpc = cpc


def popular_campanhas_cliente(cliente, indice_cliente):
    campanhas_base = [
        ("META-ACT-1", "Captação Leads", "ACTIVE"),
        ("META-ACT-2", "Remarketing", "ACTIVE"),
        ("META-PAU-1", "Teste Criativos", "PAUSED"),
    ]
    total_campanhas = 3 if indice_cliente % 2 == 0 else 2
    for indice_campanha, base in enumerate(campanhas_base[:total_campanhas]):
        campaign_id = f"{cliente.id}-{base[0]}"
        nome = f"{base[1]} {cliente.nome.split()[0]}"
        status = base[2]
        campanha = upsert_campanha(cliente.id, campaign_id, nome, status)

        for dia_idx, dia in enumerate(dias_recentes(14)):
            fator = (indice_cliente + 1) * (indice_campanha + 1)
            impressoes = 900 + (dia_idx * 35) + (fator * 22)
            cliques = 35 + (dia_idx % 7) * 3 + fator
            conversoes = max(0, (cliques // (6 + indice_campanha)) - (dia_idx % 2))
            investimento = round(70 + dia_idx * 4.8 + fator * 9.5, 2)
            upsert_metrica_campanha(campanha, dia, impressoes, cliques, conversoes, investimento)


def run_seed():
    app = create_app()
    with app.app_context():
        clientes = Cliente.query.order_by(Cliente.id.asc()).all()
        if not clientes:
            print("Nenhum cliente encontrado. Cadastre clientes antes de executar o seed.")
            return

        for indice, cliente in enumerate(clientes):
            popular_campanhas_cliente(cliente, indice)

        db.session.commit()
        print("Seed de campanhas concluído com sucesso (idempotente).")


if __name__ == "__main__":
    run_seed()
