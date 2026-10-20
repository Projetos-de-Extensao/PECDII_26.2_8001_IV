# Guia de integração front-end — Agendamentos Playmakerz

**Data:** 20/10/2026  
**Status:** núcleo do backend implementado; API e interface ainda pendentes  
**Público:** equipes de front-end, backend e QA

## 1. Objetivo

Este documento explica como a interface de agendamentos deverá conversar com o backend do Playmakerz, quais regras já existem e o que ainda precisa ser construído antes da integração.

> Importante: o navegador ainda não consegue criar agendamentos diretamente. O modelo e o serviço de domínio estão implementados e testados, mas ainda não existe um endpoint HTTP para o front-end chamar.

## 2. Situação atual

| Componente | Situação |
|---|---|
| Modelo de agendamento | Implementado |
| Agendamento individual | Implementado no serviço de backend |
| Agendamento em grupo | Implementado no serviço de backend |
| Verificação de disponibilidade do profissional | Implementada |
| Conflitos de profissional, atleta, espaço e equipamento | Implementados |
| Capacidade do espaço | Implementada |
| Validação de menor com responsável | Implementada |
| Estados `agendado`, `cancelado` e `realizado` | Modelados |
| API REST de agendamentos | Não implementada |
| Tela de agendamento | Não implementada |
| Consulta de agenda | Não implementada |
| Remarcação | Não implementada |
| Cancelamento por endpoint próprio | Não implementado |
| Planos, créditos e estornos | Fora do escopo atual |
| Recorrência e notificações | Não implementadas |

## 3. Arquitetura esperada

```text
Interface web
    ↓ requisição HTTP
API Django/DRF (a implementar)
    ↓ converte IDs em objetos e identifica o usuário autenticado
services.py — criar_agendamento()
    ↓ valida regras e conflitos em uma transação
models.py / Django ORM
    ↓
Banco de dados
```

O front-end não deve tentar reproduzir as regras como fonte de verdade. Ele pode fazer validações para melhorar a experiência, mas o backend sempre fará a validação final.

## 4. Modelo atual

Um agendamento contém:

| Campo | Tipo | Obrigatório | Observação |
|---|---|---:|---|
| `id` | inteiro | Gerado | Identificador do agendamento |
| `profissional` | relação | Sim | Profissional responsável |
| `espaco` | relação | Sim | Local do atendimento |
| `atletas` | lista | Sim | Pelo menos um atleta |
| `equipamentos` | lista | Não | Pode ser vazia |
| `registrado_por` | relação | Sim | Funcionário autenticado que criou o registro |
| `inicio` | data e hora | Sim | Deve incluir fuso horário |
| `fim` | data e hora | Sim | Deve incluir fuso horário e ser posterior ao início |
| `situacao` | enum | Gerado | Começa como `agendado` |
| `observacoes` | texto | Não | Observação livre |
| `criado_em` | data e hora | Gerado | Auditoria |
| `atualizado_em` | data e hora | Gerado | Auditoria |

Um agendamento com um atleta é individual. Com mais de um atleta, é em grupo. Não é necessário enviar um campo separado para indicar o tipo.

## 5. Regras implementadas

### 5.1 Período

- O fim deve ser posterior ao início.
- Início e fim devem estar no mesmo dia, considerando o fuso configurado no backend.
- As datas precisam conter informação de fuso horário.
- O projeto atualmente usa `USE_TZ = True` e armazena os horários em UTC.

O front-end brasileiro deve enviar o deslocamento do horário local. Exemplo:

```json
{
  "inicio": "2026-10-26T14:00:00-03:00",
  "fim": "2026-10-26T15:00:00-03:00"
}
```

Não enviar apenas `2026-10-26T14:00:00`, pois esse valor não informa o fuso.

### 5.2 Atletas

- Deve existir pelo menos um atleta.
- Todos precisam estar previamente cadastrados e ativos.
- Todos precisam ter data de nascimento para agendar.
- Atleta menor de 18 anos precisa ter `Atleta.responsavel` preenchido.
- A relação com o responsável é direta: cada atleta possui no máximo um responsável; um responsável pode estar ligado a vários atletas.
- Não existem papéis de responsável principal ou secundário.

### 5.3 Profissional

- Deve estar ativo.
- O atendimento precisa estar inteiramente dentro de um período de disponibilidade cadastrado para o profissional.
- O profissional não pode participar de dois agendamentos sobrepostos.

### 5.4 Espaço

- O número de atletas não pode exceder a capacidade do espaço.
- O espaço não pode participar de dois agendamentos sobrepostos.

### 5.5 Equipamentos

- São opcionais.
- Um equipamento selecionado não pode participar de dois agendamentos sobrepostos.

### 5.6 Conflito de horário

Existe conflito quando:

```text
agendamento_existente.inicio < novo_agendamento.fim
e
agendamento_existente.fim > novo_agendamento.inicio
```

Exemplos:

| Existente | Novo | Resultado |
|---|---|---|
| 14:00–15:00 | 14:00–15:00 | Conflito |
| 14:00–15:00 | 14:30–15:30 | Conflito |
| 14:00–15:00 | 13:30–14:30 | Conflito |
| 14:00–15:00 | 15:00–16:00 | Permitido |

Agendamentos com situação `cancelado` não bloqueiam horários. Atualmente, `agendado` e `realizado` são considerados na busca de conflitos.

## 6. Serviço existente no backend

O backend possui a função:

```python
criar_agendamento(
    profissional=profissional,
    espaco=espaco,
    atletas=atletas,
    registrado_por=funcionario,
    inicio=inicio,
    fim=fim,
    equipamentos=equipamentos,
    observacoes=observacoes,
)
```

Ela executa as validações e salva tudo em uma transação atômica. Se alguma regra falhar, nenhum registro parcial deve permanecer no banco.

A futura API deve obrigatoriamente chamar esse serviço. Não deve usar diretamente:

```python
Agendamento.objects.create(...)
```

Esse acesso direto não executaria todas as verificações que envolvem atletas e equipamentos.

## 7. Contrato recomendado para a API

Esta seção é uma proposta de contrato. Os endpoints ainda precisam ser implementados e alinhados entre as equipes.

### 7.1 Criar agendamento

```http
POST /api/agendamentos/
Content-Type: application/json
```

Payload recomendado:

```json
{
  "profissional_id": 12,
  "espaco_id": 3,
  "atleta_ids": [25],
  "equipamento_ids": [4, 8],
  "inicio": "2026-10-26T14:00:00-03:00",
  "fim": "2026-10-26T15:00:00-03:00",
  "observacoes": "Primeira avaliação"
}
```

Para um grupo, basta enviar mais IDs:

```json
{
  "atleta_ids": [25, 31, 47]
}
```

O front-end não deve enviar `registrado_por_id`. O backend deve obtê-lo da sessão ou token do funcionário autenticado. Isso impede que alguém atribua a operação a outro funcionário.

Resposta de sucesso sugerida (`201 Created`):

```json
{
  "id": 91,
  "situacao": "agendado",
  "profissional": {
    "id": 12,
    "nome": "Vinicius"
  },
  "espaco": {
    "id": 3,
    "nome": "Sala 1"
  },
  "atletas": [
    {
      "id": 25,
      "nome": "Ana Souza"
    }
  ],
  "equipamentos": [
    {
      "id": 4,
      "nome": "Bola suíça"
    }
  ],
  "inicio": "2026-10-26T17:00:00Z",
  "fim": "2026-10-26T18:00:00Z",
  "observacoes": "Primeira avaliação"
}
```

O backend pode responder em UTC. O front-end deve converter para o fuso local ao exibir.

### 7.2 Formato recomendado para erros

Resposta sugerida (`400 Bad Request`):

```json
{
  "errors": {
    "profissional": [
      "O profissional já possui um agendamento nesse horário."
    ],
    "espaco": [
      "O espaço já possui um agendamento nesse horário."
    ]
  }
}
```

Outro exemplo:

```json
{
  "errors": {
    "atletas": [
      "João: Atletas menores de 18 anos precisam de um responsável para realizar agendamentos."
    ]
  }
}
```

A interface deve associar mensagens ao campo correspondente e também mostrar um resumo no topo ou em um alerta acessível.

### 7.3 Consultas auxiliares necessárias

O front-end também precisará de endpoints semelhantes a:

```http
GET /api/atletas/?ativo=true&search=ana
GET /api/profissionais/?ativo=true&search=vinicius
GET /api/profissionais/12/disponibilidades/
GET /api/espacos/
GET /api/equipamentos/
GET /api/agendamentos/?inicio=2026-10-26T00:00:00-03:00&fim=2026-10-27T00:00:00-03:00
GET /api/agendamentos/91/
```

Esses endpoints ainda não existem. Os nomes e formatos finais devem ser acordados antes da implementação.

### 7.4 Operações futuras

Não assumir que estes endpoints já existem:

```http
POST /api/agendamentos/91/cancelar/
POST /api/agendamentos/91/remarcar/
```

Cancelamento e remarcação precisam de serviços próprios no backend. O front-end não deve alterar `situacao`, `inicio` ou `fim` diretamente até essas regras serem implementadas.

## 8. Fluxo recomendado da tela

### Passo 1 — selecionar atleta(s)

- Permitir busca por nome.
- Permitir um ou vários atletas.
- Exibir claramente quando o atendimento se tornar em grupo.
- Não permitir envio com lista vazia.

### Passo 2 — selecionar profissional

- Mostrar apenas profissionais ativos.
- Se possível, apresentar especialidade e disponibilidade.

### Passo 3 — selecionar data e período

- Escolher data, hora inicial e hora final ou duração.
- Converter o horário local para ISO 8601 com deslocamento antes do envio.
- Não desabilitar horários apenas com lógica local como garantia definitiva; outro usuário pode reservar o horário antes da confirmação.

### Passo 4 — selecionar espaço e equipamentos

- Mostrar a capacidade do espaço.
- Alertar visualmente quando a quantidade de atletas ultrapassar a capacidade, mesmo sabendo que o backend repetirá a validação.
- Equipamentos são opcionais.

### Passo 5 — revisar e confirmar

- Mostrar atleta(s), profissional, data, período, espaço e equipamentos.
- Desabilitar o botão enquanto a requisição estiver em andamento para reduzir envios duplicados.
- Considerar a operação concluída apenas depois de receber `201 Created`.

### Passo 6 — tratar o resultado

- Em sucesso, mostrar confirmação e o identificador do agendamento.
- Em erro, manter os dados preenchidos.
- Destacar os campos retornados em `errors`.
- Em conflito, oferecer retorno rápido à seleção de horário ou recurso.

## 9. Estados mínimos da interface

A tela deve prever:

- carregando cadastros;
- formulário pronto;
- enviando agendamento;
- sucesso;
- erro de validação;
- conflito de horário;
- sessão expirada ou sem permissão;
- falha inesperada de rede/servidor;
- ausência de profissionais ou espaços disponíveis.

Não usar somente cor para indicar erros. Mensagens devem ser legíveis por leitores de tela e associadas aos campos.

## 10. Responsabilidades por equipe

### Backend — pendências antes da integração

- [ ] Aplicar a migração `agendamentos.0001_initial` no ambiente apropriado.
- [ ] Criar serializer de entrada.
- [ ] Criar endpoint `POST /api/agendamentos/`.
- [ ] Obter `registrado_por` do usuário autenticado.
- [ ] Buscar IDs e rejeitar registros inexistentes ou sem acesso.
- [ ] Chamar exclusivamente `criar_agendamento()`.
- [ ] Normalizar `ValidationError` no formato acordado.
- [ ] Implementar autenticação e permissões.
- [ ] Implementar endpoints auxiliares de consulta.
- [ ] Definir paginação e filtros da agenda.
- [ ] Criar serviços próprios antes de expor remarcação e cancelamento.

### Front-end

- [ ] Criar formulário/tela de agenda.
- [ ] Consumir os endpoints de atletas, profissionais, espaços e equipamentos.
- [ ] Enviar datas ISO 8601 com fuso.
- [ ] Não enviar `registrado_por_id`.
- [ ] Tratar erros por campo.
- [ ] Preservar o formulário quando houver erro.
- [ ] Prevenir duplo clique durante o envio.
- [ ] Converter datas UTC recebidas para o horário local.
- [ ] Não implementar créditos ou estornos nesta fase.

### QA

- [ ] Validar agendamento individual.
- [ ] Validar agendamento em grupo dentro da capacidade.
- [ ] Validar grupo acima da capacidade.
- [ ] Validar menor com e sem responsável.
- [ ] Validar profissional inativo e fora da disponibilidade.
- [ ] Validar conflitos de cada recurso separadamente.
- [ ] Validar horários adjacentes.
- [ ] Validar que cancelados não bloqueiam horários quando o cancelamento estiver disponível.
- [ ] Validar mensagens e acessibilidade dos erros.

## 11. Critérios de aceite da primeira integração

A primeira entrega front-end/backend pode ser considerada pronta quando:

1. um funcionário autenticado conseguir criar um agendamento individual;
2. o mesmo fluxo aceitar vários atletas sem ultrapassar a capacidade;
3. horários forem enviados com fuso e exibidos corretamente;
4. conflitos de profissional, atleta, espaço e equipamento forem mostrados sem perda dos dados do formulário;
5. um menor sem responsável for rejeitado pelo backend;
6. o front-end não puder informar outro funcionário como autor;
7. falhas não deixarem registros parciais;
8. os testes automatizados do backend e os testes de integração passarem.

## 12. Fora do escopo desta entrega

- planos e créditos;
- débito e estorno de sessões;
- pagamentos;
- recorrência;
- notificações e lembretes;
- bloqueios de manutenção;
- política completa de faltas;
- alteração em série;
- relatórios.

Esses itens devem ser tratados em etapas posteriores, sem alterar o contrato básico de criação sem alinhamento entre as equipes.

## 13. Referências no código

- `src/agendamentos/models.py`: estrutura e validações diretas do agendamento.
- `src/agendamentos/services.py`: criação transacional e regras que envolvem múltiplos recursos.
- `src/agendamentos/tests.py`: exemplos executáveis dos comportamentos esperados.
- `src/agendamentos/migrations/0001_initial.py`: criação das tabelas e índices.
- `src/usuarios/models.py`: `Atleta.validar_para_agendamento()` e disponibilidade profissional.

