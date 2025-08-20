# Sistema de Fidelidade e Cupons

Este projeto implementa um sistema de fidelidade, pontos e cupons para um marketplace com estrutura multi-tenant (Cliente → Franquia → Loja).

## Funcionalidades

- **Carteira de pontos** com suporte a diferentes escopos (GLOBAL, CUSTOMER, FRANCHISE, STORE)
- **Ofertas de cupons** com regras de validade, estoque e limites por cliente
- **Tipos de cupons** flexíveis (valor fixo, percentual, SKU específico)
- **PDV (Ponto de Venda)** para validação e resgate de cupons
- **Acúmulo de pontos** por compras com regras configuráveis por tenant
- **Segurança multi-tenant** e autenticação via tokens JWT

## Pré-requisitos

- Python 3.8+
- PostgreSQL 13+
- Dependências listadas em `requirements.txt`

## Configuração

1. **Criar o banco de dados PostgreSQL**:
   ```sql
   CREATE DATABASE fidelity;
   ```

2. **Instalar dependências**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variáveis de ambiente** (crie um arquivo `.env`):
   ```
   DATABASE_URL=postgresql://usuario:senha@localhost/fidelity
   SECRET_KEY=sua-chave-secreta-aqui
   ```

## Execução

```bash
uvicorn main:app --reload
```

A API estará disponível em `http://localhost:8000` e a documentação Swagger em `http://localhost:8000/docs`.

## Estrutura do Projeto

- **database.py**: Configuração de conexão com o banco de dados
- **models.py**: Modelos SQLAlchemy para todas as entidades do sistema
- **main.py**: Aplicação FastAPI com rotas e lógica de negócio

## Endpoints principais

### Autenticação
- `POST /auth/login`: Login e obtenção de tokens
- `POST /auth/refresh`: Refresh de tokens expirados
- `POST /auth/logout`: Logout e revogação de tokens
- `POST /auth/pdv/register-device`: Registro de dispositivos PDV

### Marketplace
- `GET /wallet`: Retorna saldo de pontos e cupons disponíveis
- `GET /offers`: Lista ofertas de cupons disponíveis
- `GET /offers/{offer_id}`: Detalhes de uma oferta específica
- `POST /coupons/buy`: Compra/emissão de um cupom
- `GET /coupons/my`: Lista cupons do usuário atual

### PDV (Ponto de Venda)
- `POST /pdv/attempt-coupon`: Tenta validar um cupom
- `POST /pdv/redeem`: Confirma o resgate de um cupom
- `POST /pdv/earn-points`: Registra pontos para um pedido
