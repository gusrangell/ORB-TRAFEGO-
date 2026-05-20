CREATE DATABASE IF NOT EXISTS trafico_pago
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE trafico_pago;

-- Tabelas legadas preservadas para ambientes já populados.

CREATE TABLE clientes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(100) NOT NULL,
  meta_account_id VARCHAR(50) NULL,
  access_token TEXT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE metricas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  cliente_id INT NOT NULL,
  data DATE NOT NULL,
  cpl DECIMAL(10,2) NULL,
  ctr DECIMAL(5,2) NULL,
  cpc DECIMAL(10,2) NULL,
  conversoes INT NULL,
  investimento DECIMAL(10,2) NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_metricas_cliente
    FOREIGN KEY (cliente_id)
    REFERENCES clientes(id)
    ON DELETE CASCADE
);

CREATE TABLE diario (
  id INT AUTO_INCREMENT PRIMARY KEY,
  cliente_id INT NOT NULL,
  data DATE NOT NULL,
  tipo ENUM('criativo','ajuste','teste','analise','outro') NOT NULL,
  descricao TEXT NOT NULL,
  tags JSON NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_diario_cliente
    FOREIGN KEY (cliente_id)
    REFERENCES clientes(id)
    ON DELETE CASCADE
);

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
);

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
);
