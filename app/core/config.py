"""
Application configuration settings
"""
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_PREFIX = "Bearer "

# Tags para documentação da API
API_TAGS = [
    {
        "name": "auth",
        "description": "Endpoints para autenticação e autorização. Inclui login, registro, refresh de tokens e gerenciamento de dispositivos PDV."
    },
    {
        "name": "wallet",
        "description": "Endpoints para consulta de carteira de pontos e cupons do usuário."
    },
    {
        "name": "offers",
        "description": "Endpoints para listagem e consulta de ofertas de cupons disponíveis."
    },
    {
        "name": "coupons",
        "description": "Endpoints para compra e gerenciamento de cupons pelos usuários."
    },
    {
        "name": "pdv",
        "description": "Endpoints específicos para Ponto de Venda (PDV). Inclui validação e resgate de cupons, além de registro de pontos."
    }
]

# Configuração do FastAPI
APP_CONFIG = {
    "title": "Fidelity API",
    "description": "API para sistema de fidelidade e cupons com suporte a gerenciamento de pontos, cupons e ofertas. O sistema suporta múltiplos tenants (Customer → Franchise → Store) e controle de acesso baseado em perfis.",
    "version": "1.0.0",
    "docs_url": "/docs",
    "redoc_url": "/redoc",
    "openapi_url": "/openapi.json"
}

# Configuração do Swagger UI
SWAGGER_UI_PARAMETERS = {
    "persistAuthorization": True,
    "displayOperationId": True,
    "operationsSorter": "method",
}

# Configuração CORS
CORS_CONFIG = {
    "allow_origins": ["*"],  # Defina origins específicas em produção
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
