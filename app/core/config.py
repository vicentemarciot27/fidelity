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
    },
    {
        "name": "admin-business",
        "description": "Endpoints administrativos para gerenciamento de tenants: Customers, Franchises e Stores."
    },
    {
        "name": "admin-users",
        "description": "Endpoints administrativos para gerenciamento de usuários e atribuição de staff às lojas."
    },
    {
        "name": "admin-config",
        "description": "Endpoints administrativos para configuração de regras de pontos e marketplace."
    },
    {
        "name": "admin-coupons",
        "description": "Endpoints administrativos para gerenciamento completo de tipos de cupons, ofertas, assets e operações em massa."
    },
    {
        "name": "admin-catalog",
        "description": "Endpoints administrativos para gerenciamento de catálogo de produtos (SKUs e categorias)."
    },
    {
        "name": "admin-system",
        "description": "Endpoints administrativos para gerenciamento de recursos do sistema: dispositivos PDV, chaves de API e logs de auditoria."
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
