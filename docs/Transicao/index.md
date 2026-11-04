# Guia de integração front-end — Agendamentos Playmakerz

**Data:** 20/10/2026  
**Status:** núcleo e interface interna implementados; API REST ainda pendente
**Público:** equipes de front-end, backend e QA

## 1. Objetivo

Este documento explica como a interface de agendamentos deverá conversar com o backend do Playmakerz, quais regras já existem e o que ainda precisa ser construído antes da integração.

> Importante: existe uma interface interna de conferência em `/agendamentos/`, protegida pelo login de funcionário do Django Admin. A API REST destinada ao front-end definitivo ainda não foi implementada.

## 2. Situação atual

| Componente | Situação |
|---|---|
| Modelo de agendamento | Implementado |
| Agendamento individual | Implementado no serviço de backend |
| Agendamento em grupo e limite de participantes | Implementados no serviço de backend |
| Participação individual de cada atleta | Modelada; fluxos de presença e falta ainda pendentes |
| Aula experimental individual ou em grupo | Implementada no serviço e na interface interna |
| Cadastro rápido de interessado | Implementado na tela interna de agendamento |
| Verificação de disponibilidade do profissional | Implementada |
| Conflitos de profissional, atleta e equipamento | Implementados |
| Capacidade compartilhada do espaço | Implementada pela soma dos limites reservados |
| Validação de menor com responsável | Implementada |
| Estados `agendado`, `cancelado` e `realizado` | Modelados |
| API REST de agendamentos | Não implementada |
| Tela interna de agendamento | Implementada em `/agendamentos/` |
| Consulta de blocos de 30 minutos | Implementada na interface interna |
| Remarcação | Não implementada |
| Cancelamento individual e total | Implementado no serviço de backend |
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
| `modalidade` | enum | Sim | `individual` ou `grupo` |
| `limite_participantes` | inteiro | Sim | `1` no individual; definido pelo profissional no grupo |
| `atletas` | lista | Sim | Pelo menos um atleta |
| `equipamentos` | lista | Não | Pode ser vazia |
| `registrado_por` | relação | Sim | Funcionário autenticado que criou o registro |
| `inicio` | data e hora | Sim | Deve incluir fuso horário |
| `fim` | data e hora | Sim | Deve incluir fuso horário e ser posterior ao início |
| `situacao` | enum | Gerado | Começa como `agendado` |
| `observacoes` | texto | Não | Observação livre |
| `criado_em` | data e hora | Gerado | Auditoria |
| `atualizado_em` | data e hora | Gerado | Auditoria |

Individual e grupo são modalidades explícitas. Uma atividade individual possui limite `1`. Uma atividade em grupo possui limite mínimo `2`, definido pelo profissional, e pode começar com apenas um participante inscrito.

Cada atleta selecionado gera uma `ParticipacaoAgendamento`. Ela permite que um atendimento em grupo registre separadamente a situação de cada participante: `confirmada`, `cancelada`, `presente`, `falta` ou `falta_justificada`. O campo `tipo` identifica a participação como `regular` ou `experimental`, e `registrado_por` preserva qual funcionário fez a inscrição. A estrutura já existe, mas os endpoints para alterar presença e falta ainda não foram implementados.

O cadastro de `Atleta` possui e-mail próprio e pode continuar sem uma conta de acesso. O e-mail é opcional para o cadastro geral, mas obrigatório para uma aula experimental.

## 5. Regras implementadas

### 5.1 Período

- O fim deve ser posterior ao início.
- Início e fim devem estar no mesmo dia, considerando o fuso configurado no backend.
- Os horários são organizados em blocos de 30 minutos.
- Os blocos permitidos vão de `07:00` a `12:00` e de `13:00` a `20:00`.
- O período entre `12:00` e `13:00` não aceita agendamentos.
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
- O mesmo atleta não pode aparecer duas vezes no mesmo agendamento.
- Um aluno pode entrar em uma atividade em grupo existente enquanto houver vaga.
- A quantidade exibida usa o formato `PR:LM`, em que `PR` são participantes ativos e `LM` é o limite da atividade.
- Uma participação individual cancelada deixa de bloquear o atleta, sem necessariamente cancelar a aula dos demais participantes.

#### 5.2.1 Aula experimental

- Somente um recepcionista ativo pode registrar uma aula experimental.
- A experimental pode ser individual ou uma inscrição em atividade em grupo.
- Nome, e-mail, telefone e data de nascimento são obrigatórios.
- O cadastro rápido é destinado a maiores de 18 anos.
- Para menores, o recepcionista deve fazer antes o cadastro completo do atleta e do responsável.
- Cada atleta pode possuir apenas uma experimental não cancelada em todo o histórico.
- `presente`, `falta` e `falta_justificada` consomem o direito à experimental.
- Uma participação cancelada permite que o recepcionista marque outra experimental.
- A experimental ocupa horário, vaga e capacidade normalmente.
- A tela interna permite cadastrar o interessado sem criar usuário ou senha.
- O cadastro rápido e o agendamento são atômicos: se o agendamento falhar, o novo atleta também não é salvo.
- Nenhum e-mail é enviado nesta etapa; o endereço é apenas armazenado.

### 5.3 Cancelamento

- Em um atendimento individual, cancelar a única participação cancela também o agendamento e libera todos os recursos.
- Em um atendimento em grupo, cancelar um atleta mantém a aula enquanto existir outro participante não cancelado.
- Quando o último participante cancela, o agendamento inteiro é cancelado.
- Cancelar o agendamento inteiro cancela todas as participações ainda confirmadas.
- O registro não é apagado: data e motivo do cancelamento são preservados.
- Agendamentos realizados não podem ser cancelados.

### 5.4 Profissional

- Deve estar ativo.
- O atendimento precisa estar inteiramente dentro de um período de disponibilidade cadastrado para o profissional.
- A disponibilidade deve ser cadastrada separadamente para manhã (`07:00`–`12:00`) e tarde/noite (`13:00`–`20:00`), sempre em intervalos de 30 minutos.
- O profissional não pode participar de dois agendamentos sobrepostos.

### 5.5 Espaço

- Atividades simultâneas podem compartilhar o mesmo espaço.
- Cada atividade reserva seu `limite_participantes`, e não apenas a quantidade atual de inscritos.
- A soma dos limites das atividades sobrepostas não pode superar a capacidade do espaço.
- Reservar os limites impede que duas turmas sejam criadas com vagas que, quando preenchidas, ultrapassariam a capacidade do local.

### 5.6 Equipamentos

- São opcionais.
- Um equipamento selecionado não pode participar de dois agendamentos sobrepostos.

### 5.7 Conflito de horário

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
    modalidade="grupo",
    limite_participantes=6,
    atletas_experimentais=[atleta_experimental],
)
```

Ela executa as validações, cria uma participação para cada atleta e salva tudo em uma transação atômica. Se alguma regra falhar, nenhum registro parcial deve permanecer no banco.

A futura API deve obrigatoriamente chamar esse serviço. Não deve usar diretamente:

```python
Agendamento.objects.create(...)
```

Esse acesso direto não executaria todas as verificações que envolvem atletas e equipamentos.

Para entrar em uma turma existente, o backend possui:

```python
inscrever_em_atividade_grupo(
    agendamento=agendamento,
    atleta=atleta,
    experimental=True,
    registrado_por=recepcionista,
)
```

O serviço impede inscrição duplicada, conflito do atleta e entrada depois que o limite foi atingido.

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
  "modalidade": "individual",
  "limite_participantes": 1,
  "atleta_ids": [25],
  "equipamento_ids": [4, 8],
  "inicio": "2026-10-26T14:00:00-03:00",
  "fim": "2026-10-26T15:00:00-03:00",
  "observacoes": "Primeira avaliação"
}
```

Para criar um grupo, informe a modalidade e o limite definido pelo profissional:

```json
{
  "modalidade": "grupo",
  "limite_participantes": 6,
  "atleta_ids": [25]
}
```

Uma inscrição posterior deve usar um endpoint próprio para entrar no agendamento existente, sem criar outro agendamento para o mesmo professor e horário.

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
      "O espaço escolhido está lotado nesse horário. Capacidade: 8; vagas já reservadas: 6; novo limite: 4."
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
GET /api/profissionais/12/horarios/?data=2026-10-26
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

Os serviços de cancelamento já existem no backend, mas ainda precisam ser expostos por um endpoint autenticado. A remarcação ainda precisa de um serviço próprio. O front-end não deve alterar `situacao`, `inicio` ou `fim` diretamente.

## 8. Fluxo recomendado da tela

### Passo 1 — selecionar profissional e data

- Mostrar blocos de 30 minutos derivados da disponibilidade profissional.
- Mostrar somente blocos entre `07:00` e `12:00` e entre `13:00` e `20:00`; não exibir blocos no intervalo de almoço.
- Horário individual ocupado deve ficar desabilitado.
- Grupo com vaga deve continuar selecionável e mostrar `PR:LM`, por exemplo `3:6`.
- Grupo lotado deve ficar desabilitado e mostrar, por exemplo, `6:6`.

### Passo 2 — selecionar atleta

- Ao selecionar um grupo existente, incluir o atleta naquele agendamento.
- Em um horário livre, continuar para a criação de uma nova atividade.

### Passo 3 — configurar uma nova atividade

- Escolher `individual` ou `grupo`.
- No grupo, solicitar o limite definido pelo profissional.
- Escolher espaço e equipamentos.
- Alertar quando os limites já reservados deixarem o espaço sem capacidade.
- Converter o horário local para ISO 8601 com deslocamento antes do envio.
- Não desabilitar horários apenas com lógica local como garantia definitiva; outro usuário pode reservar o horário antes da confirmação.

### Passo 4 — revisar e confirmar

- Mostrar atleta(s), profissional, data, período, espaço e equipamentos.
- Desabilitar o botão enquanto a requisição estiver em andamento para reduzir envios duplicados.
- Considerar a operação concluída apenas depois de receber `201 Created`.

### Passo 5 — tratar o resultado

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

- [ ] Aplicar as migrações de usuários até `0003_atleta_email` e de agendamentos até `0005_participacao_experimental` no ambiente apropriado.
- [ ] Criar serializer de entrada.
- [ ] Criar endpoint `POST /api/agendamentos/`.
- [ ] Obter `registrado_por` do usuário autenticado.
- [ ] Buscar IDs e rejeitar registros inexistentes ou sem acesso.
- [ ] Chamar exclusivamente `criar_agendamento()`.
- [ ] Normalizar `ValidationError` no formato acordado.
- [ ] Implementar autenticação e permissões.
- [ ] Implementar endpoints auxiliares de consulta.
- [ ] Definir paginação e filtros da agenda.
- [ ] Criar endpoints que chamem `cancelar_participacao()` e `cancelar_agendamento()`.
- [ ] Criar um serviço próprio antes de expor remarcação.

### Front-end

- [ ] Criar formulário/tela de agenda.
- [ ] Reproduzir no front-end definitivo o cadastro rápido de interessado experimental.
- [ ] Exibir os blocos de 30 minutos e os estados disponível, ocupado e lotado.
- [ ] Mostrar a ocupação de grupos no formato `PR:LM`.
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
- [ ] Validar que cada atleta do grupo recebe uma participação própria.
- [ ] Validar grupo acima da capacidade.
- [ ] Validar menor com e sem responsável.
- [ ] Validar experimental individual e em grupo.
- [ ] Validar que uma segunda experimental é bloqueada depois de presença ou falta.
- [ ] Validar que o cancelamento permite remarcar a experimental.
- [ ] Validar rollback do cadastro rápido quando o agendamento falha.
- [ ] Validar profissional inativo e fora da disponibilidade.
- [ ] Validar conflitos de cada recurso separadamente.
- [ ] Validar horários adjacentes.
- [ ] Validar que o cancelamento individual libera somente o atleta correspondente.
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

- `src/agendamentos/models.py`: estruturas de agendamento e participação, além das validações diretas.
- `src/agendamentos/services.py`: criação transacional e regras que envolvem múltiplos recursos.
- `src/agendamentos/tests.py`: exemplos executáveis dos comportamentos esperados.
- `src/agendamentos/migrations/0001_initial.py`: criação das tabelas e índices.
- `src/agendamentos/migrations/0005_participacao_experimental.py`: tipo da participação, recepcionista e garantia de uma experimental.
- `src/usuarios/models.py`: validação do atleta, dados da experimental e disponibilidade profissional.

