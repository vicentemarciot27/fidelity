# Testes Unitários - Fidelity API

Este diretório contém os testes unitários para a API de Fidelidade, seguindo a estratégia da pirâmide de testes com foco em validação de lógica de negócio e funcionalidades isoladas.

## Estrutura de Testes

```
tests/
├── __init__.py                 # Inicialização do pacote de testes
├── conftest.py                 # Configurações e fixtures do pytest
├── test_auth.py                # Testes de autenticação e autorização
├── test_pdv.py                 # Testes de operações de PDV
├── test_wallet.py              # Testes de carteira de pontos
├── test_offers.py              # Testes de ofertas e cupons
├── test_schemas.py             # Testes de validação de schemas Pydantic
├── test_business_logic.py      # Testes de lógica de negócio
└── README.md                   # Este arquivo
```

## Tipos de Testes

### 1. Testes de Routers (test_auth.py, test_pdv.py, test_wallet.py, test_offers.py)

Testam os endpoints da API, incluindo:
- Validação de entrada e saída
- Autenticação e autorização
- Tratamento de erros
- Integração com banco de dados (usando SQLite em memória)

### 2. Testes de Schemas (test_schemas.py)

Validam os modelos Pydantic:
- Validação de tipos de dados
- Campos obrigatórios e opcionais
- Conversões de tipos
- Casos extremos e validações de borda

### 3. Testes de Lógica de Negócio (test_business_logic.py)

Testam regras de negócio puras:
- Cálculo de pontos
- Cálculo de descontos
- Validação de cupons
- Expiração de pontos
- Hierarquia de regras

## Pré-requisitos

```bash
pip install -r requirements.txt
pip install pytest pytest-cov
```

## Executando os Testes

### Executar todos os testes
```bash
pytest
```

### Executar testes com cobertura
```bash
pytest --cov=app --cov-report=html
```

### Executar testes de um arquivo específico
```bash
pytest tests/test_auth.py
pytest tests/test_pdv.py
pytest tests/test_wallet.py
pytest tests/test_offers.py
pytest tests/test_schemas.py
pytest tests/test_business_logic.py
```

### Executar uma classe de teste específica
```bash
pytest tests/test_auth.py::TestRegisterEndpoint
pytest tests/test_pdv.py::TestEarnPointsEndpoint
```

### Executar um teste específico
```bash
pytest tests/test_auth.py::TestRegisterEndpoint::test_register_new_user_success
```

### Executar testes com saída verbose
```bash
pytest -v
```

### Executar testes e parar no primeiro erro
```bash
pytest -x
```

### Executar testes com pdb no erro
```bash
pytest --pdb
```

## Fixtures Disponíveis

O arquivo `conftest.py` fornece as seguintes fixtures:

- **db**: Sessão de banco de dados SQLite em memória
- **client**: Cliente de teste do FastAPI
- **sample_person**: Pessoa de exemplo
- **sample_user**: Usuário de exemplo
- **sample_admin_user**: Usuário administrador
- **sample_customer**: Cliente de exemplo
- **sample_franchise**: Franquia de exemplo
- **sample_store**: Loja de exemplo
- **sample_point_rule**: Regra de pontos de exemplo
- **sample_coupon_type**: Tipo de cupom de exemplo
- **sample_coupon_offer**: Oferta de cupom de exemplo
- **sample_coupon**: Cupom de exemplo
- **auth_headers**: Headers de autenticação

## Cobertura de Testes

Os testes cobrem:

### Autenticação (test_auth.py)
- ✅ Registro de usuário
- ✅ Login
- ✅ Refresh token
- ✅ Logout
- ✅ Registro de dispositivos PDV
- ✅ Validação de senhas

### PDV (test_pdv.py)
- ✅ Validação de cupons
- ✅ Resgate de cupons
- ✅ Acúmulo de pontos
- ✅ Cálculo de descontos
- ✅ Validação de SKUs específicos

### Wallet (test_wallet.py)
- ✅ Consulta de carteira
- ✅ Conversão pontos para BRL
- ✅ Filtro de pontos expirados
- ✅ Hierarquia de escopos
- ✅ Saldo de cupons

### Ofertas (test_offers.py)
- ✅ Listagem de ofertas
- ✅ Paginação
- ✅ Filtros
- ✅ Compra de cupons
- ✅ Geração de códigos e QR codes
- ✅ Validação de estoque
- ✅ Limite por cliente

### Schemas (test_schemas.py)
- ✅ Validação de todos os schemas Pydantic
- ✅ Campos obrigatórios e opcionais
- ✅ Conversões de tipos
- ✅ Casos extremos

### Lógica de Negócio (test_business_logic.py)
- ✅ Cálculo de pontos
- ✅ Cálculo de descontos
- ✅ Validação de cupons
- ✅ Expiração de pontos
- ✅ Hierarquia de regras
- ✅ Cálculo de saldo

## Melhores Práticas

1. **Isolamento**: Cada teste é independente e usa fixtures para configurar o estado inicial
2. **Nomenclatura Clara**: Nomes de testes descrevem claramente o que está sendo testado
3. **Arrange-Act-Assert**: Testes seguem o padrão AAA
4. **Banco de Dados em Memória**: Testes usam SQLite em memória para performance
5. **Fixtures Reutilizáveis**: Configurações comuns são extraídas para fixtures
6. **Testes de Casos Extremos**: Incluem validação de valores limite e casos de erro

## Estratégia de Testes

### Pirâmide de Testes

```
       /\
      /  \     E2E (Poucos)
     /----\
    /      \   Integration (Alguns)
   /--------\
  /          \
 /   Unit     \ (Muitos)
/--------------\
```

Este projeto foca em:
- **Testes de Unidade (70%)**: Lógica de negócio pura, cálculos, validações
- **Testes de Integração (25%)**: Endpoints da API com banco de dados mock
- **Testes E2E (5%)**: (Não implementados neste conjunto)

## Adicionando Novos Testes

Ao adicionar novos testes:

1. Use as fixtures existentes quando possível
2. Crie novas fixtures em `conftest.py` se necessário
3. Organize testes em classes lógicas
4. Teste casos de sucesso e casos de erro
5. Teste validações e casos extremos
6. Mantenha testes rápidos e focados

## Exemplo de Teste

```python
class TestMyFeature:
    """Test cases for my feature"""
    
    def test_feature_success(self, client, db, sample_user):
        """Test successful execution of feature"""
        # Arrange
        request_data = {"field": "value"}
        
        # Act
        response = client.post("/endpoint", json=request_data)
        
        # Assert
        assert response.status_code == 200
        assert response.json()["result"] == "expected"
```

## Troubleshooting

### Erro de importação
- Verifique se o PYTHONPATH está configurado corretamente
- Execute `export PYTHONPATH="${PYTHONPATH}:$(pwd)"` no Linux/Mac
- Execute `$env:PYTHONPATH="$env:PYTHONPATH;$(pwd)"` no Windows PowerShell

### Testes lentos
- Use `pytest -n auto` para executar testes em paralelo (requer pytest-xdist)
- Verifique se está usando banco de dados em memória
- Minimize operações de I/O nos testes

### Falhas intermitentes
- Verifique se testes não dependem de ordem de execução
- Garanta que fixtures limpam o estado após cada teste
- Evite usar timestamps fixos (use mocks para datas)

## Recursos Adicionais

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pydantic Validation](https://docs.pydantic.dev/latest/concepts/validation/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#using-a-sessionmaker)

