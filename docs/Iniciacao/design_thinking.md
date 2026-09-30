---
id: dt
title: Design Thinking
author: Daniel Gusmao
---

# Design Thinking — Sistema de Gestão da Playmakerz

## 1. Identificação do Projeto

- **Projeto:** Sistema de Gestão da Playmakerz
- **Organização:** Playmakerz
- **Equipe:** Grupo IV — PECDII_26.2_8001
- **Período:** 2026.2
- **Autor do documento:** Daniel Gusmao
- **Data:** 30/09/2026

---

## 2. Introdução

### 2.1 Contexto

A Playmakerz é um centro de treinamento voltado para alta performance esportiva, localizado na Barra da Tijuca, no Rio de Janeiro.

A rotina do centro envolve diferentes atletas, profissionais, espaços e equipamentos. Dessa forma, a realização de um atendimento depende da disponibilidade simultânea de diferentes recursos, o que aumenta a complexidade do processo de agendamento.

O projeto propõe o desenvolvimento de um sistema web capaz de centralizar essas informações e auxiliar na organização dos atendimentos, reduzindo conflitos de horário e reservas duplicadas.

Além da organização dos agendamentos, o sistema deverá considerar a segurança e a privacidade dos dados armazenados, especialmente porque a Playmakerz atende crianças e adolescentes.

### 2.2 Objetivo

Desenvolver um sistema de gestão esportiva que permita organizar os atendimentos da Playmakerz, integrando atletas, profissionais, espaços e equipamentos em uma mesma estrutura de agendamento.

Entre os principais objetivos estão:

- Centralizar a gestão de agendamentos;
- Evitar conflitos e reservas duplicadas;
- Facilitar a consulta da disponibilidade de profissionais e recursos;
- Permitir agendamentos individuais, em grupo e recorrentes;
- Registrar presença, faltas e cancelamentos;
- Permitir o bloqueio de espaços e equipamentos em manutenção;
- Enviar confirmações, lembretes e avisos;
- Controlar o acesso às informações de acordo com o perfil de cada usuário;
- Proteger dados pessoais e sensíveis de acordo com os princípios da LGPD.

### 2.3 Público-Alvo

Os principais usuários e stakeholders identificados no projeto são:

- Gestores da Playmakerz;
- Funcionários da recepção;
- Coordenadores;
- Treinadores e outros profissionais;
- Funcionários responsáveis pela manutenção;
- Atletas;
- Pais ou responsáveis por atletas menores de idade;
- Pró-Reitoria Acadêmica, como stakeholder do projeto de extensão.

### 2.4 Escopo

O escopo inicial contempla:

- Cadastro de atletas, responsáveis, profissionais e funcionários;
- Cadastro de espaços;
- Cadastro de equipamentos;
- Agenda de atendimentos;
- Verificação de conflitos de horário;
- Agendamentos individuais;
- Agendamentos em grupo;
- Agendamentos recorrentes;
- Remarcação e cancelamento de agendamentos;
- Controle de presença e faltas;
- Bloqueio de espaços e equipamentos em manutenção;
- Perfis de acesso com diferentes permissões;
- Confirmações, lembretes e avisos;
- Consulta da ocupação dos espaços.

Funcionalidades relacionadas a pagamentos, planos, informações financeiras e acompanhamento detalhado da evolução dos atletas não fazem parte do núcleo inicialmente definido e deverão ser validadas antes de serem incorporadas ao escopo.

!!! important "Limite das informações disponíveis"
    As informações iniciais sobre a rotina da Playmakerz foram obtidas por meio de pesquisa pública e dos documentos produzidos pela equipe. Ainda não há, no repositório, registro de entrevistas ou testes com usuários reais da organização. Por esse motivo, os perfis e necessidades apresentados neste documento devem ser tratados como hipóteses a serem validadas com os responsáveis pela Playmakerz.

---

# 3. Fases do Design Thinking

## 3.1 Empatia

A etapa de empatia busca compreender quem utilizará o sistema e quais dificuldades estão relacionadas à rotina que será apoiada pela solução.

### 3.1.1 Pesquisa

Para compreender o contexto do problema foram utilizadas as seguintes fontes e técnicas:

- Pesquisa inicial sobre a Playmakerz;
- Análise das características públicas da empresa;
- Identificação dos possíveis usuários do sistema;
- Análise de soluções semelhantes existentes no mercado;
- Aplicação da técnica 5W2H;
- Brainstorming realizado pela equipe;
- Construção de mapa mental;
- Levantamento de requisitos;
- Construção de protótipo de baixa fidelidade.

Na análise de mercado foram observadas soluções como Tecnofit, Aqqo, Kourtiva e Amilia.

Apesar de apresentarem funcionalidades relacionadas a academias, centros esportivos e reservas, o projeto da Playmakerz possui como ponto central a associação simultânea de **atleta, profissional, espaço e equipamento dentro de um mesmo agendamento**.

### 3.1.2 Principais Insights

A análise dos documentos produzidos durante a iniciação permitiu identificar os seguintes pontos:

1. **O agendamento é o núcleo do problema.**

    Um atendimento depende de diferentes elementos que precisam estar disponíveis no mesmo período.

2. **A disponibilidade deve ser verificada de forma integrada.**

    Não é suficiente verificar apenas o horário do profissional. O sistema também precisa considerar atletas, espaços, equipamentos e bloqueios de manutenção.

3. **Conflitos precisam ser identificados antes da confirmação.**

    O sistema não deve permitir que um mesmo recurso participe de agendamentos sobrepostos.

4. **A recepção possui papel importante na operação.**

    O processo de criação e alteração de agendamentos precisa ser simples e rápido para não dificultar o atendimento.

5. **Existem diferentes níveis de acesso à informação.**

    Um atleta não deve possuir a mesma visão do sistema que um gestor ou funcionário da recepção.

6. **Dados de menores de idade exigem atenção especial.**

    Atletas menores deverão estar associados a pais ou responsáveis, e os dados pessoais e sensíveis deverão possuir acesso restrito.

7. **Agendamentos recorrentes podem reduzir tarefas repetitivas.**

    Atividades realizadas periodicamente não devem exigir que a recepção cadastre manualmente cada ocorrência.

8. **Manutenções afetam diretamente a agenda.**

    Espaços ou equipamentos indisponíveis precisam ser bloqueados para impedir que sejam utilizados em novos agendamentos.

9. **Comunicação automática pode reduzir falhas.**

    Confirmações, lembretes, alterações e cancelamentos devem ser comunicados aos usuários envolvidos.

---

## 3.1.3 Proto-personas

Como ainda não há entrevistas documentadas com usuários reais, foram elaboradas **proto-personas**, construídas a partir dos papéis e necessidades identificados nos documentos do projeto.

### Proto-persona 1 — Funcionário da Recepção

**Objetivo:** organizar rapidamente os atendimentos da academia.

**Principais atividades:**

- Cadastrar atletas;
- Consultar profissionais;
- Consultar horários disponíveis;
- Criar agendamentos;
- Remarcar atendimentos;
- Cancelar atendimentos;
- Registrar informações necessárias ao cadastro.

**Necessidades:**

- Interface simples;
- Consulta rápida de disponibilidade;
- Identificação clara de conflitos;
- Visualização dos recursos envolvidos no atendimento;
- Redução de tarefas repetitivas.

**Principais problemas identificados:**

- Conflitos entre horários;
- Necessidade de verificar vários recursos;
- Alterações de agenda;
- Reservas duplicadas.

---

### Proto-persona 2 — Profissional/Treinador

**Objetivo:** consultar e organizar seus atendimentos.

**Principais atividades:**

- Consultar sua agenda;
- Verificar atletas agendados;
- Registrar presença ou falta;
- Acompanhar alterações em atendimentos.

**Necessidades:**

- Visualizar apenas informações relacionadas aos seus atendimentos;
- Receber informações atualizadas sobre mudanças na agenda;
- Ter acesso rápido à programação do dia.

---

### Proto-persona 3 — Atleta ou Responsável

**Objetivo:** acompanhar os próprios atendimentos ou os atendimentos do atleta pelo qual é responsável.

**Principais atividades:**

- Consultar agendamentos;
- Receber confirmações;
- Receber lembretes;
- Acompanhar alterações e cancelamentos.

**Necessidades:**

- Informações simples e claras;
- Privacidade;
- Acesso apenas aos próprios dados;
- Comunicação sobre mudanças importantes.

No caso de atletas menores de idade, o sistema deverá considerar o vínculo com um pai ou responsável.

---

## 3.1.4 Jornada Resumida do Agendamento

A partir do fluxo identificado durante o Brainstorming e detalhado posteriormente nos casos de uso, foi possível representar a jornada principal da seguinte maneira:

| Etapa | Ação | Necessidade do usuário | Oportunidade para o sistema |
|------|------|-------------------------|-----------------------------|
| 1 | Acessar o sistema | Entrar de forma segura | Autenticação individual |
| 2 | Consultar profissional | Saber quem está disponível | Consulta de profissionais e horários |
| 3 | Informar atendimento | Selecionar todos os recursos necessários | Reunir atleta, profissional, espaço e equipamento |
| 4 | Verificar disponibilidade | Saber se o horário pode ser utilizado | Verificação automática de conflitos |
| 5 | Resolver conflito | Encontrar alternativa quando algo estiver ocupado | Mensagem clara indicando o recurso indisponível |
| 6 | Confirmar atendimento | Garantir a reserva dos recursos | Registro único do agendamento |
| 7 | Acompanhar atendimento | Evitar esquecimento ou perda de informação | Confirmações, lembretes e avisos |

---

## 3.2 Definição

Com base nos insights obtidos, foi definido o problema central do projeto.

### 3.2.1 Problema Central

> **Como podemos permitir que a Playmakerz organize seus atendimentos reunindo atletas, profissionais, espaços e equipamentos em um mesmo agendamento, evitando conflitos de horário e reservas duplicadas, ao mesmo tempo em que protegemos os dados e limitamos o acesso de acordo com o perfil de cada usuário?**

### 3.2.2 Pontos de Vista — POV

#### Recepção

A recepção precisa criar e alterar agendamentos de forma rápida, pois cada atendimento depende da disponibilidade simultânea de diferentes recursos e a verificação manual pode gerar conflitos.

#### Profissional

O profissional precisa consultar sua agenda de maneira clara, pois alterações de horários e atendimentos precisam ser identificadas rapidamente.

#### Atleta ou Responsável

O atleta ou responsável precisa acompanhar seus próprios agendamentos e receber avisos importantes, sem ter acesso às informações de outros usuários.

#### Gestão

Os gestores precisam possuir uma visão mais ampla da operação e controlar permissões, pois diferentes usuários necessitam de diferentes níveis de acesso às informações.

#### Manutenção

Os responsáveis pela manutenção precisam informar quando espaços ou equipamentos estão indisponíveis, pois esses recursos não podem ser utilizados durante o período de manutenção.

---

## 3.3 Ideação

### 3.3.1 Brainstorming

Durante o Brainstorming realizado pela equipe foram discutidas funcionalidades relacionadas a:

- Login e autenticação;
- Cadastro de alunos;
- Documentos necessários ao cadastro;
- Autorização de responsáveis;
- Exames médicos;
- Consulta de profissionais;
- Consulta de horários disponíveis;
- Agendamentos;
- Confirmações;
- Lembretes;
- Notificações;
- Comunicados;
- Relatórios;
- Evolução dos alunos;
- Informações financeiras.

Essas ideias foram posteriormente comparadas com o escopo definido na pesquisa e com os requisitos levantados.

### 3.3.2 Critérios de Seleção

As ideias foram analisadas considerando:

1. Relação com o problema central;
2. Impacto na rotina da Playmakerz;
3. Viabilidade de desenvolvimento durante o projeto;
4. Dependência de outras funcionalidades;
5. Segurança e privacidade;
6. Necessidade de validação com a organização.

### 3.3.3 Priorização das Ideias

| Ideia | Situação |
|------|----------|
| Autenticação individual | Priorizada |
| Cadastro de atletas e responsáveis | Priorizada |
| Cadastro de profissionais | Priorizada |
| Cadastro de espaços | Priorizada |
| Cadastro de equipamentos | Priorizada |
| Agenda integrada | Priorizada |
| Verificação automática de conflitos | Priorizada |
| Agendamento individual | Priorizada |
| Agendamento em grupo | Priorizada |
| Agendamento recorrente | Priorizada |
| Remarcação e cancelamento | Priorizada |
| Bloqueio por manutenção | Priorizada |
| Perfis e permissões | Priorizada |
| Confirmações e lembretes | Priorizada |
| Controle de presença e faltas | Priorizada |
| Consulta da ocupação dos espaços | Priorizada |
| Avaliações e evolução do atleta | Necessita validação |
| Relatórios de evolução | Necessita validação |
| Informações financeiras | Necessita validação |

A **Gerência de Agendamentos** foi definida como funcionalidade central do sistema.

---

## 3.4 Prototipagem

### 3.4.1 Objetivo do Protótipo

O protótipo de baixa fidelidade foi utilizado para transformar os principais requisitos em um fluxo inicial de interação.

Nesta etapa, o foco foi representar as funcionalidades mais importantes para o início da utilização do sistema.

### 3.4.2 Tela de Login e Cadastro

O protótipo prevê:

#### Login

- E-mail;
- Senha;
- Botão de entrada;
- Criação de conta;
- Recuperação de senha.

O acesso deverá respeitar o perfil de cada usuário.

#### Cadastro

- Nome;
- E-mail;
- Telefone;
- Senha;
- Confirmação da senha;
- Tipo de usuário.

Para atletas menores de idade, deverá existir associação com pai ou responsável.

Perfis de funcionários e profissionais poderão depender de autorização administrativa.

### 3.4.3 Tela de Agendamento

O fluxo de agendamento contempla:

- Tipo de agendamento;
- Atleta ou atletas participantes;
- Profissional;
- Data;
- Horário inicial;
- Horário final;
- Espaço;
- Equipamentos;
- Repetição do agendamento;
- Verificação de disponibilidade;
- Confirmação.

### 3.4.4 Verificação de Disponibilidade

Antes da confirmação do atendimento, o sistema deverá verificar:

- Disponibilidade do atleta;
- Disponibilidade do profissional;
- Disponibilidade do espaço;
- Disponibilidade dos equipamentos;
- Bloqueios de manutenção.

Caso exista conflito, o usuário deverá ser informado sobre a indisponibilidade antes que o agendamento seja confirmado.

### 3.4.5 Fluxo do Protótipo

```text
Login
  ↓
Consulta/Cadastro
  ↓
Novo Agendamento
  ↓
Selecionar Atleta(s)
  ↓
Selecionar Profissional
  ↓
Selecionar Data e Horário
  ↓
Selecionar Espaço
  ↓
Selecionar Equipamentos
  ↓
Verificar Disponibilidade
  ↓
┌─────────────────────┐
│ Existe conflito?    │
└─────────────────────┘
       ↓          ↓
      Sim        Não
       ↓          ↓
Informar       Exibir resumo
conflito           ↓
       ↓       Confirmar
Alterar dados      ↓
       └────→ Agendamento criado
```

O protótipo completo está documentado em [Prototipagem de Baixa Fidelidade](prototipo_baixa_fidelidade.md).

---

## 3.5 Teste

### 3.5.1 Situação Atual

Até o momento desta documentação, **não existem testes de usabilidade ou entrevistas de validação com usuários reais da Playmakerz registrados no repositório**.

Consequentemente, não devem ser apresentados feedbacks ou resultados como se já tivessem sido obtidos.

### 3.5.2 Validações Necessárias

Antes da consolidação da solução, deverão ser confirmados com a Playmakerz:

- Quais perfis de usuários realmente existem;
- Quais funções cada perfil poderá executar;
- Como a recepção realiza atualmente os agendamentos;
- Quais recursos precisam obrigatoriamente fazer parte de um agendamento;
- Quais informações dos atletas são realmente necessárias;
- Como deverão funcionar autorizações para menores de idade;
- Se informações financeiras farão parte do sistema;
- Se o acompanhamento da evolução do atleta será necessário;
- Quais avaliações e relatórios seriam utilizados pelos profissionais;
- Quais tipos de notificação são necessários.

### 3.5.3 Testes Planejados

O protótipo poderá ser validado por meio de tarefas práticas.

#### Cenário 1 — Criar um agendamento

O participante deverá:

1. Acessar o sistema;
2. Iniciar um novo agendamento;
3. Selecionar um atleta;
4. Selecionar um profissional;
5. Escolher espaço e equipamento;
6. Escolher data e horário;
7. Verificar disponibilidade;
8. Confirmar o agendamento.

#### Cenário 2 — Resolver um conflito

O participante deverá tentar selecionar um horário no qual algum recurso já esteja ocupado.

O objetivo é verificar se a mensagem apresentada permite compreender:

- Qual recurso está indisponível;
- O motivo da indisponibilidade;
- O período do conflito;
- O que deve ser alterado para continuar.

#### Cenário 3 — Consultar agenda

Profissionais, atletas e responsáveis deverão localizar seus próximos atendimentos utilizando apenas as funções disponíveis para seus respectivos perfis.

### 3.5.4 Critérios de Avaliação

Durante os testes deverão ser observados:

- Conclusão ou não da tarefa;
- Quantidade de erros;
- Pontos de dúvida;
- Clareza das mensagens;
- Facilidade para encontrar funcionalidades;
- Facilidade para compreender conflitos;
- Tempo necessário para realizar um agendamento;
- Percepção do usuário sobre o fluxo.

### 3.5.5 Feedback e Ajustes

Esta etapa permanece **pendente de validação com usuários**.

Após a realização dos testes, os feedbacks deverão ser registrados e utilizados para revisar o protótipo, os requisitos e os fluxos do sistema.

---

# 4. Conclusão

A aplicação do Design Thinking permitiu consolidar as informações obtidas durante a iniciação e organizar o projeto em torno das necessidades dos principais usuários.

O principal problema identificado está relacionado à gestão de atendimentos que dependem simultaneamente de atletas, profissionais, espaços e equipamentos.

A solução proposta é um sistema web capaz de reunir esses elementos em um mesmo agendamento e verificar automaticamente sua disponibilidade antes da confirmação.

Também foram identificados aspectos importantes relacionados à segurança, privacidade, manutenção de recursos, agendamentos recorrentes, notificações e diferentes níveis de acesso.

O protótipo de baixa fidelidade representa o início da materialização dessas ideias, porém ainda deverá ser validado com usuários reais da Playmakerz.

## 4.1 Resultados Obtidos

Até esta etapa foram produzidos:

- Definição do contexto do problema;
- Identificação dos stakeholders;
- Definição do público-alvo;
- Identificação das principais necessidades;
- Definição do problema central;
- Brainstorming de funcionalidades;
- Priorização das principais ideias;
- Definição da Gerência de Agendamentos como núcleo do produto;
- Protótipo de baixa fidelidade;
- Levantamento inicial de requisitos;
- Casos de uso;
- Identificação dos principais pontos que ainda precisam ser validados.

## 4.2 Próximos Passos

Os próximos passos do processo são:

1. Validar as hipóteses com responsáveis e usuários da Playmakerz;
2. Confirmar os perfis e permissões existentes;
3. Validar o fluxo de agendamento;
4. Testar o protótipo de baixa fidelidade;
5. Registrar o feedback recebido;
6. Ajustar os requisitos quando necessário;
7. Refinar o protótipo;
8. Prosseguir com a modelagem e implementação do sistema.

## 4.3 Aprendizados

O processo demonstrou que o problema não está apenas em armazenar agendamentos, mas em coordenar diferentes recursos simultaneamente.

Também foi possível identificar que segurança, privacidade e controle de acesso fazem parte do funcionamento principal da aplicação e não devem ser tratados apenas como funcionalidades adicionais.

Por fim, ficou evidente a importância da validação com a Playmakerz, já que parte das necessidades levantadas até o momento ainda representa hipóteses construídas pela equipe.

---

# 5. Documentos Relacionados

As informações utilizadas neste Design Thinking foram consolidadas a partir dos documentos já existentes no projeto:

- [Pesquisa](pesquisa.md)
- [5W2H](5w2h.md)
- [Brainstorming](Brainstorm.md)
- [Mapa Mental](mapa_mental.md)
- [Protótipo de Baixa Fidelidade](prototipo_baixa_fidelidade.md)
- [Levantamento de Requisitos](../Elaboracao/levreq.md)
- [Casos de Uso](../Elaboracao/casos_de_uso.md)

---

## Autor(es)

| Data | Versão | Descrição | Autor(es) |
|------|--------|-----------|-----------|
| 30/09/2026 | 1.0 | Elaboração e consolidação do Design Thinking | Daniel Gusmao |