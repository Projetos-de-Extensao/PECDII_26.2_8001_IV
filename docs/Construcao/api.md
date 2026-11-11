---
id: api
title: API REST
---

## 1 Objetivo

A API é a parte do sistema que deixa outros programas, como um site, buscar e enviar informações para o sistema da Playmakerz. Ela funciona pela internet, usando o HTTP, e troca os dados no formato JSON.

A API não cria regras novas. As regras do sistema já estão nos models e nos services que o grupo fez, então ela só recebe o pedido, chama esse código e devolve a resposta. Com ela dá para cadastrar espaços, equipamentos e atletas, ver os profissionais e os horários livres deles, e criar ou cancelar agendamentos.

## 2 Como acessar

Para rodar a API na sua máquina ou no Codespaces, siga estes passos:

1. Na raiz do projeto, instale as dependências com `pip install -r requirements.txt`.
2. Entre na pasta `src` e crie o banco de dados com `python manage.py migrate`.
3. Crie um usuário para entrar no sistema com `python manage.py createsuperuser`.
4. Ligue o servidor com `python manage.py runserver`.
5. Abra `/admin/login/` no navegador, entre com o superusuário que você criou e depois acesse `/api/` na mesma sessão.

!!! note "Se estiver usando o Codespaces"
    A página da API mostra links com `localhost:8000`, mas eles não abrem no Codespaces. Use o endereço da porta 8000 que o Codespaces gera (na aba **Portas**) e continue com o resto da rota, por exemplo `/api/profissionais/`.

!!! warning "Sobre o banco de dados"
    O arquivo `db.sqlite3` não vai para o GitHub, então cada pessoa tem o seu. Depois de dar `git pull`, rode `python manage.py migrate` de novo. Se der erro de migration, apague o arquivo `src/db.sqlite3` e rode o `migrate` outra vez. Os dados de teste vão ser perdidos, mas dá para criar de novo pelo admin.

## 3 Autenticação

Todas as rotas da API exigem que a pessoa esteja autenticada. Se alguém tentar acessar sem se identificar, a API responde com o código 403 e a mensagem `Authentication credentials were not provided.`

### 3.1 Formas de autenticação

A API aceita três formas de entrar:

| Forma | Como funciona | Quando usar |
| --- | --- | --- |
| Sessão | A pessoa faz login pelo navegador e o Django guarda o login em um cookie | Testar a API pela página do navegador |
| Basic | O usuário e a senha são enviados em toda requisição | Testes rápidos |
| Token | A pessoa faz login uma vez, recebe um código e envia esse código nas próximas requisições | Programas e aplicativos que usam a API |

### 3.2 Como pegar o token

Para pegar o token, envie o usuário e a senha para a rota `/api/token/` com o método POST:

```bash
curl -X POST http://localhost:8000/api/token/ -d "username=meu_usuario&password=minha_senha"
```

Se estiver tudo certo, a API devolve o token:

```json
{
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

Se o usuário ou a senha estiverem errados, a API responde com o código 400:

```json
{
    "non_field_errors": [
        "Unable to log in with provided credentials."
    ]
}
```

### 3.3 Como usar o token

O token vai no cabeçalho `Authorization`, com a palavra `Token` antes do código:

```bash
curl -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" http://localhost:8000/api/profissionais/
```

Com o token correto, a API responde normalmente. Com o token errado ou sem token, ela responde com o código 403.

!!! warning "Cuidado com o token"
    O token funciona como uma senha. Não envie o token para outras pessoas e não coloque ele em arquivos que vão para o GitHub. Os tokens dos exemplos desta página são inventados.

## 4 Endpoints

Abaixo estão todas as rotas da API. Nas rotas com `{id}`, troque `{id}` pelo número do registro. Os exemplos completos estão na seção 5.

| Recurso | Métodos | Rota | O que faz |
| --- | --- | --- | --- |
| Token | POST | `/api/token/` | Recebe usuário e senha e devolve o token |
| Espaços | GET, POST | `/api/espacos/` | Lista e cadastra espaços |
| Espaços | GET, PUT, PATCH, DELETE | `/api/espacos/{id}/` | Consulta, edita e apaga um espaço |
| Equipamentos | GET, POST | `/api/equipamentos/` | Lista e cadastra equipamentos |
| Equipamentos | GET, PUT, PATCH, DELETE | `/api/equipamentos/{id}/` | Consulta, edita e apaga um equipamento |
| Atletas | GET, POST | `/api/atletas/` | Lista e cadastra atletas |
| Atletas | GET, PUT, PATCH, DELETE | `/api/atletas/{id}/` | Consulta, edita e apaga um atleta |
| Profissionais | GET | `/api/profissionais/` | Lista os profissionais ativos |
| Profissionais | GET | `/api/profissionais/{id}/` | Consulta um profissional |
| Profissionais | GET | `/api/profissionais/{id}/horarios/?data=AAAA-MM-DD` | Lista os horários livres e ocupados do dia |
| Agendamentos | POST | `/api/agendamentos/` | Cria um agendamento |
| Agendamentos | POST | `/api/agendamentos/{id}/cancelar/` | Cancela um agendamento |
| Agendamentos | POST | `/api/agendamentos/{id}/inscrever/` | Inscreve um atleta em uma atividade em grupo |
| Agendamentos | POST | `/api/agendamentos/{id}/participacoes/{participacao_id}/cancelar/` | Cancela a participação de um atleta |

### 4.1 O que enviar em cada rota

As rotas de envio (POST, PUT e PATCH) recebem os dados em JSON. Estes são os campos de cada uma:

| Rota | Campos | Observações |
| --- | --- | --- |
| Espaços | `nome`, `tipo`, `capacidade` | A capacidade é um número inteiro maior ou igual a zero |
| Equipamentos | `nome`, `tipo` | |
| Atletas | `nome`, `email`, `telefone`, `data_de_nascimento`, `objetivos`, `ativo`, `responsavel` | O telefone precisa ter pelo menos 11 dígitos. A data tem o formato `AAAA-MM-DD` e não pode ser no futuro. O campo `idade` é calculado pela API e só aparece na resposta. O `responsavel` é o id de um responsável |
| Criar agendamento | `profissional`, `espaco`, `atletas`, `registrado_por`, `inicio`, `fim` | Todos são obrigatórios. `profissional`, `espaco` e `registrado_por` são ids, e `atletas` é uma lista de ids. As datas ficam no formato `AAAA-MM-DDTHH:MM` |
| Criar agendamento (opcionais) | `equipamentos`, `modalidade`, `limite_participantes`, `observacoes`, `atletas_experimentais` | A `modalidade` pode ser `individual` ou `grupo`. Se usar `atletas_experimentais`, o `registrado_por` precisa ser um funcionário ativo com cargo `recepcionista`. |
| Inscrever em um agendamento | `atleta`, `experimental`, `registrado_por` | O `atleta` é obrigatório. O `experimental` é `true` ou `false` (o padrão é `false`). Se `experimental` for `true`, o `registrado_por` também é obrigatório e deve ser o id de um funcionário ativo com cargo `recepcionista` |
| Cancelar agendamento ou participação | `motivo` | O motivo é opcional |

As regras de negócio (por exemplo, conflito de horário ou grupo lotado) são aplicadas pelos services do sistema. Quando alguma regra é quebrada, a API responde com o código 400 e explica o motivo no corpo da resposta.

## 5 Exemplos de uso

Os exemplos abaixo usam o `curl` e o endereço `http://localhost:8000`. Troque `SEU_TOKEN` pelo token que você pegou na seção 3.

### 5.1 Listar os profissionais

```bash
curl -H "Authorization: Token SEU_TOKEN" http://localhost:8000/api/profissionais/
```

Resposta (código 200):

```json
[
    {
        "id": 1,
        "nome": "prof_teste",
        "especialidade": "Preparação física",
        "ativo": true
    }
]
```

### 5.2 Ver os horários de um profissional

Informe a data no formato `AAAA-MM-DD`. A API devolve os blocos de 30 minutos em que o profissional atende naquele dia da semana.

```bash
curl -H "Authorization: Token SEU_TOKEN" "http://localhost:8000/api/profissionais/1/horarios/?data=2026-11-16"
```

Resposta (código 200, mostrando só os dois primeiros blocos):

```json
[
    {
        "rotulo": "14:00",
        "inicio": "2026-11-16T14:00",
        "fim": "2026-11-16T14:30",
        "disponivel": true,
        "tipo": "livre",
        "agendamento_id": null,
        "inscritos": null,
        "limite": null
    },
    {
        "rotulo": "14:30",
        "inicio": "2026-11-16T14:30",
        "fim": "2026-11-16T15:00",
        "disponivel": true,
        "tipo": "livre",
        "agendamento_id": null,
        "inscritos": null,
        "limite": null
    }
]
```

Se o profissional não atende naquele dia da semana, a resposta é uma lista vazia (`[]`). Um horário sem agendamento vem com `tipo: "livre"` e `disponivel: true`. Se já existe um agendamento individual, ou um grupo lotado, o `disponivel` fica `false`. Se for um grupo com vagas, vem com `tipo: "grupo"` e `disponivel: true`, e os campos `inscritos` e `limite` mostram a ocupação. Nesse caso, use o `agendamento_id` na rota de inscrição do agendamento que já existe, em vez de criar outro agendamento.

### 5.3 Erros ao consultar os horários

Sem informar a data (código 400):

```json
{
    "data": [
        "Informe a data no formato AAAA-MM-DD."
    ]
}
```

Com a data em formato errado, como `11-11-2026` (código 400):

```json
{
    "data": [
        "Data inválida. Use o formato AAAA-MM-DD."
    ]
}
```

Com um profissional que não existe (código 404):

```json
{
    "detail": "No Profissional matches the given query."
}
```

### 5.4 Erros de validação ao cadastrar um atleta

A API usa as mesmas regras do model. Com um telefone de menos de 11 dígitos (código 400):

```json
{
    "telefone": [
        "O telefone deve conter pelo menos 11 dígitos."
    ]
}
```

Com uma data de nascimento no futuro (código 400):

```json
{
    "data_de_nascimento": [
        "A data de nascimento não pode ser futura."
    ]
}
```

### 5.5 Cadastrar um atleta

```bash
curl -X POST http://localhost:8000/api/atletas/ \
  -H "Authorization: Token SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nome": "Atleta Teste Um", "email": "atleta1@exemplo.com", "telefone": "21999990001", "data_de_nascimento": "2010-05-20", "objetivos": "Melhorar o condicionamento", "ativo": true}'
```

Resposta (código 201):

```json
{
    "id": 1,
    "nome": "Atleta Teste Um",
    "email": "atleta1@exemplo.com",
    "telefone": "21999990001",
    "data_de_nascimento": "2010-05-20",
    "idade": 16,
    "objetivos": "Melhorar o condicionamento",
    "ativo": true,
    "responsavel": null
}
```

Repare que o campo `idade` não foi enviado e a própria API calculou a partir da data de nascimento.

### 5.6 Erro de regra de negócio ao criar um agendamento

Atletas menores de 18 anos precisam ter um responsável cadastrado. Ao tentar agendar um atleta menor sem responsável, a API responde com o código 400:

```json
{
    "atletas": [
        "Atleta Teste Um: Atletas menores de 18 anos precisam de um responsável para realizar agendamentos."
    ]
}
```

### 5.7 Criar um agendamento

Neste exemplo, o atleta de id 2 é um atleta maior de idade (cadastrado como no exemplo 5.5, mas com data de nascimento em 1995), e o espaço e o funcionário de id 1 já estavam cadastrados.

```bash
curl -X POST http://localhost:8000/api/agendamentos/ \
  -H "Authorization: Token SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"profissional": 1, "espaco": 1, "atletas": [2], "registrado_por": 1, "inicio": "2026-11-16T14:00", "fim": "2026-11-16T15:00"}'
```

Resposta (código 201):

```json
{
    "id": 1,
    "profissional": 1,
    "espaco": 1,
    "modalidade": "individual",
    "limite_participantes": 1,
    "atletas": [2],
    "equipamentos": [],
    "registrado_por": 1,
    "inicio": "2026-11-16T14:00:00Z",
    "fim": "2026-11-16T15:00:00Z",
    "situacao": "agendado",
    "observacoes": "",
    "motivo_cancelamento": "",
    "cancelado_em": null,
    "criado_em": "2026-11-11T02:09:07.743214Z",
    "atualizado_em": "2026-11-11T02:09:07.743214Z"
}
```

Como não foram enviados os campos opcionais, a API usou os valores padrão: agendamento individual, com limite de 1 participante.

### 5.8 Erro de conflito de horário

Se o profissional ou algum atleta já tiver um agendamento naquele horário, a API recusa o novo agendamento com o código 400:

```json
{
    "profissional": [
        "O profissional já possui um agendamento nesse horário."
    ],
    "atletas": [
        "Um ou mais atletas já possuem agendamento nesse horário."
    ]
}
```

### 5.9 Cancelar um agendamento

O motivo é opcional.

```bash
curl -X POST http://localhost:8000/api/agendamentos/1/cancelar/ \
  -H "Authorization: Token SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"motivo": "Atleta pediu para remarcar"}'
```

Resposta (código 200):

```json
{
    "id": 1,
    "profissional": 1,
    "espaco": 1,
    "modalidade": "individual",
    "limite_participantes": 1,
    "atletas": [2],
    "equipamentos": [],
    "registrado_por": 1,
    "inicio": "2026-11-16T14:00:00Z",
    "fim": "2026-11-16T15:00:00Z",
    "situacao": "cancelado",
    "observacoes": "",
    "motivo_cancelamento": "Atleta pediu para remarcar",
    "cancelado_em": "2026-11-11T02:17:08.861093Z",
    "criado_em": "2026-11-11T02:09:07.743214Z",
    "atualizado_em": "2026-11-11T02:17:08.861928Z"
}
```

## 6 Códigos de resposta

| Código | Significado | Quando acontece |
| --- | --- | --- |
| 200 OK | Deu certo | Consultas, edições, cancelamentos e o pedido do token |
| 201 Created | Registro criado | Cadastro de espaço, equipamento, atleta ou agendamento |
| 204 No Content | Apagado | Exclusão de um espaço, equipamento ou atleta |
| 400 Bad Request | Dados inválidos | Campo errado, ou uma regra do sistema foi quebrada (telefone curto, horário em conflito, atleta menor sem responsável) |
| 403 Forbidden | Sem acesso | A pessoa não enviou o login ou o token, ou o token está errado |
| 404 Not Found | Não encontrado | O registro pedido não existe |
| 405 Method Not Allowed | Método não permitido | Usar um método que a rota não aceita, por exemplo POST em `/api/profissionais/` |