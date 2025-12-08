# ES2-Externo

**Sistema de Pagamentos e Notificações para Aluguel de Bicicletas**

Microsserviço responsável pelo processamento de pagamentos, validação de cartões de crédito e envio de notificações por email, desenvolvido como parte de um sistema distribuído de aluguel de bicicletas.

---

## Sumário

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Tecnologias](#tecnologias)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso da API](#uso-da-api)
- [Testes](#testes)
- [Integração Contínua](#integração-contínua)
- [Estrutura do Projeto](#estrutura-do-projeto)

---

## Visão Geral

Este microsserviço faz parte de uma arquitetura distribuída e é responsável por:

- **Validação de Cartões de Crédito**: Integração com gateway de pagamento Mercado Pago para validar dados de cartões
- **Processamento de Cobranças**: Gerenciamento do ciclo de vida de cobranças (criação, processamento, consulta)
- **Fila de Cobranças**: Sistema de enfileiramento para processamento assíncrono de pagamentos
- **Notificações por Email**: Envio de emails transacionais (confirmações, notificações de cobrança)

O sistema foi projetado seguindo princípios de Clean Architecture, com separação clara entre entidades, casos de uso e interfaces externas.

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API Gateway                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ES2-Externo (FastAPI)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                       │
│  │   /cartao    │  │  /cobranca   │  │   /email     │                       │
│  │   Router     │  │   Router     │  │   Router     │                       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                       │
│         │                 │                 │                                │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐                       │
│  │ MercadoPago  │  │   Asyncpg    │  │    Email     │                       │
│  │   Manager    │  │   Manager    │  │   Manager    │                       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                       │
└─────────┼─────────────────┼─────────────────┼───────────────────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
   │ Mercado Pago│   │ PostgreSQL  │   │ SMTP Server │
   │     API     │   │  Database   │   │             │
   └─────────────┘   └─────────────┘   └─────────────┘
```

### Comunicação entre Serviços

O microsserviço se comunica com:

- **Serviço de Ciclistas**: Consulta dados de cartão cadastrado do ciclista
- **Mercado Pago**: Validação de cartões e processamento de pagamentos
- **Servidor SMTP**: Envio de emails transacionais
- **PostgreSQL**: Persistência de cobranças

---

## Tecnologias

| Categoria | Tecnologia | Versão |
|-----------|------------|--------|
| Runtime | Python | 3.13 |
| Framework | FastAPI | 0.122.0 |
| ORM/Database | asyncpg | - |
| Gateway de Pagamento | mercadopago | - |
| Email | fastapi-mail | 1.5.8 |
| HTTP Client | httpx | 0.27.2 |
| Validação | Pydantic | 2.12.5 |
| Servidor | Uvicorn | 0.38.0 |
| Testes | pytest | 8.3.5 |
| Cobertura | pytest-cov | 6.0.0 |

---

## Instalação

### Pré-requisitos

- Python 3.13+
- PostgreSQL 14+
- Conta no Mercado Pago (para credenciais de sandbox/produção)
- Servidor SMTP (ou conta Gmail/SendGrid para testes)

### Passos

1. Clone o repositório:
```bash
git clone https://github.com/pablozr/ES2-Externo.git
cd ES2-Externo
```

2. Crie e ative o ambiente virtual:
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente (veja seção [Configuração](#configuração))

5. Execute a aplicação:
```bash
uvicorn main:app --reload --port 8000
```

---

## Configuração

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Banco de Dados
DB_URL=postgresql://usuario:senha@localhost:5432/nome_banco

# Serviço de Ciclistas (microsserviço externo)
CICLISTA_SERVICE_URL=http://localhost:8080/ciclistas/

# Mercado Pago
MP_ACCESS_TOKEN=seu_access_token_mercado_pago

# Email (SMTP)
MAIL_USERNAME=seu_email@gmail.com
MAIL_PASSWORD=sua_senha_de_app
MAIL_FROM=seu_email@gmail.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com

# Servidor
PORT=8000
```

### Configuração do Banco de Dados

Execute o script SQL para criar a tabela de cobranças:

```sql
CREATE TABLE cobrancas (
    id SERIAL PRIMARY KEY,
    status VARCHAR(20) NOT NULL,
    hora_solicitacao TIMESTAMP NOT NULL,
    hora_finalizacao TIMESTAMP,
    valor DECIMAL(10, 2) NOT NULL,
    ciclista INTEGER NOT NULL
);

CREATE INDEX idx_cobrancas_status ON cobrancas(status);
CREATE INDEX idx_cobrancas_ciclista ON cobrancas(ciclista);
```

---

## Uso da API

### Endpoints Disponíveis

A documentação interativa está disponível em `/docs` (Swagger UI) ou `/redoc` (ReDoc).

#### Cartão de Crédito

**POST** `/validaCartaoDeCredito`

Valida os dados de um cartão de crédito através do gateway de pagamento.

```json
{
  "nomeTitular": "NOME COMO NO CARTAO",
  "numero": "4509953566233704",
  "validade": "2030-12-01",
  "cvv": "123"
}
```

#### Cobrança

**POST** `/cobranca`

Realiza uma cobrança imediata no cartão do ciclista.

```json
{
  "valor": 15.50,
  "ciclista": 1
}
```

**GET** `/cobranca/{id}`

Consulta os detalhes de uma cobrança específica.

**POST** `/filaCobranca`

Adiciona uma cobrança à fila para processamento posterior.

**POST** `/processaCobrancasEmFila`

Processa todas as cobranças pendentes na fila.

#### Email

**POST** `/enviarEmail`

Envia um email transacional.

```json
{
  "email": "destinatario@exemplo.com",
  "assunto": "Confirmação de Pagamento",
  "mensagem": "<h1>Pagamento Confirmado</h1><p>Valor: R$ 15,50</p>"
}
```

### Códigos de Resposta

| Código | Descrição |
|--------|-----------|
| 200 | Operação realizada com sucesso |
| 400 | Erro de validação ou regra de negócio |
| 404 | Recurso não encontrado |
| 422 | Erro de validação dos dados de entrada |
| 500 | Erro interno do servidor |

---

## Testes

O projeto possui cobertura de testes de **100%** no código de produção.

### Estrutura de Testes

```
tests/
├── conftest.py                 # Fixtures globais
├── entities/                   # Testes de entidades (modelos Pydantic)
│   ├── test_cartao.py
│   ├── test_cobranca.py
│   └── test_email.py
├── functions/                  # Testes de managers/serviços
│   ├── test_asyncpg_manager.py
│   ├── test_ciclista_manager.py
│   ├── test_email_manager.py
│   └── test_mercado_pago_manager.py
├── routes/                     # Testes de rotas/endpoints
│   ├── test_cartao_router.py
│   ├── test_cobranca_router.py
│   └── test_email_router.py
└── integration/                # Testes de integração
    ├── test_cartao_integration.py
    ├── test_cobranca_integration.py
    ├── test_email_integration.py
    └── test_fluxo_completo.py
```

### Executar Testes

```bash
# Instalar dependências de teste
pip install -r requirements-test.txt

# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=entities --cov=functions --cov=routes --cov-report=term-missing

# Executar apenas testes unitários
pytest tests/entities tests/functions tests/routes

# Executar apenas testes de integração
pytest tests/integration

# Gerar relatório HTML de cobertura
pytest --cov=entities --cov=functions --cov=routes --cov-report=html
```

### Métricas de Teste

| Categoria | Quantidade |
|-----------|------------|
| Testes Unitários | 118 |
| Testes de Integração | 35 |
| **Total** | **153** |
| Cobertura | **100%** |

---

## Integração Contínua

O projeto está configurado com GitHub Actions para CI/CD e SonarCloud para análise de qualidade.

### Pipeline

```yaml
# .github/workflows/ci.yml
- Test: Executa testes com cobertura
- SonarCloud: Análise de código e qualidade
```

### SonarCloud

O projeto utiliza SonarCloud para:

- Análise estática de código
- Métricas de cobertura de testes
- Detecção de code smells e bugs
- Quality Gate

Acesse o dashboard em: [SonarCloud - ES2-Externo](https://sonarcloud.io/project/overview?id=pablozr_ES2-Externo)

---

## Estrutura do Projeto

```
ES2-Externo/
├── entities/                    # Modelos de domínio (Pydantic)
│   ├── cartao/
│   │   └── cartao.py           # Modelo de cartão de crédito
│   ├── cobranca/
│   │   └── cobranca.py         # Modelo de cobrança
│   └── email/
│       └── email.py            # Modelo de email
│
├── functions/                   # Lógica de negócio e integrações
│   ├── database/
│   │   └── asyncpg_manager.py  # Gerenciador de banco de dados
│   ├── email/
│   │   └── email_manager.py    # Gerenciador de envio de emails
│   ├── integration/
│   │   └── ciclista_manager.py # Cliente do serviço de ciclistas
│   └── mercado_pago/
│       └── mercado_pago_manager.py  # Cliente do Mercado Pago
│
├── routes/                      # Endpoints da API
│   ├── cartao/
│   │   └── router.py
│   ├── cobranca/
│   │   └── router.py
│   └── email/
│       └── router.py
│
├── tests/                       # Testes automatizados
│   ├── entities/
│   ├── functions/
│   ├── routes/
│   └── integration/
│
├── .github/
│   └── workflows/
│       └── ci.yml              # Pipeline de CI/CD
│
├── main.py                      # Ponto de entrada da aplicação
├── requirements.txt             # Dependências de produção
├── requirements-test.txt        # Dependências de teste
├── sonar-project.properties     # Configuração do SonarCloud
└── pytest.ini                   # Configuração do pytest
```

---

## Decisões Técnicas

### Por que FastAPI?

- Performance assíncrona nativa com suporte a async/await
- Validação automática de dados com Pydantic
- Documentação OpenAPI gerada automaticamente
- Type hints integrados ao desenvolvimento

### Por que asyncpg?

- Driver PostgreSQL assíncrono de alta performance
- Connection pooling nativo
- Suporte a prepared statements

### Por que Mercado Pago?

- Gateway de pagamento amplamente utilizado no Brasil
- Ambiente de sandbox para desenvolvimento
- SDK oficial para Python

---

## Contribuição

Este é um projeto acadêmico. Para contribuir:

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

---

## Licença

Este projeto foi desenvolvido para fins acadêmicos como parte da disciplina de Engenharia de Software II.

---

## Autores

Desenvolvido por estudantes de Engenharia de Software.

