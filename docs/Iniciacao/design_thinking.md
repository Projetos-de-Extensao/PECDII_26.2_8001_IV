---
id: dt
title: Design Thinking
author: Daniel Gusmao
---

# Design Thinking — Playmakerz

## Introdução

O projeto tem como objetivo desenvolver um sistema web para auxiliar a Playmakerz na organização de seus atendimentos.

O principal desafio identificado está na necessidade de coordenar diferentes recursos ao mesmo tempo, como atletas, profissionais, espaços e equipamentos, evitando conflitos de horário e reservas duplicadas.

---

## 1. Empatia

Nesta etapa foram analisadas as necessidades dos principais usuários do sistema:

- Funcionários da recepção;
- Profissionais e treinadores;
- Atletas;
- Pais ou responsáveis;
- Gestores;
- Funcionários responsáveis pela manutenção.

Entre as principais necessidades identificadas estão:

- Criar e alterar agendamentos rapidamente;
- Consultar horários disponíveis;
- Evitar conflitos entre agendamentos;
- Visualizar os atendimentos de forma organizada;
- Controlar o acesso às informações;
- Proteger dados pessoais dos atletas.

As informações foram obtidas a partir da pesquisa inicial, Brainstorming, 5W2H, mapa mental e levantamento de requisitos realizados pela equipe.

---

## 2. Definição

Com base na pesquisa realizada, foi definido o seguinte problema:

> **Como organizar os atendimentos da Playmakerz reunindo atletas, profissionais, espaços e equipamentos em um mesmo agendamento, evitando conflitos de horário?**

O sistema deverá centralizar essas informações e verificar automaticamente a disponibilidade dos recursos antes da confirmação do atendimento.

---

## 3. Ideação

Durante o Brainstorming foram levantadas diferentes funcionalidades para o sistema.

As principais ideias selecionadas foram:

- Login e controle de acesso;
- Cadastro de atletas e responsáveis;
- Cadastro de profissionais;
- Cadastro de espaços e equipamentos;
- Agenda de atendimentos;
- Verificação automática de conflitos;
- Agendamentos individuais, em grupo e recorrentes;
- Remarcação e cancelamento;
- Controle de presença e faltas;
- Bloqueio de recursos em manutenção;
- Confirmações e lembretes.

A **Gerência de Agendamentos** foi definida como a principal funcionalidade do projeto.

---

## 4. Prototipagem

Foi elaborado um protótipo de baixa fidelidade representando as principais telas e fluxos do sistema.

O fluxo principal de agendamento consiste em:

```text
Login
  ↓
Novo Agendamento
  ↓
Selecionar Atleta
  ↓
Selecionar Profissional
  ↓
Escolher Data e Horário
  ↓
Selecionar Espaço e Equipamentos
  ↓
Verificar Disponibilidade
  ↓
Confirmar Agendamento
```

Caso algum recurso esteja ocupado, o sistema deverá informar o conflito antes da confirmação.

---

## 5. Teste

Até o momento, não existem testes com usuários reais registrados no projeto.

A próxima etapa será validar o protótipo com os responsáveis e usuários da Playmakerz.

Os testes deverão verificar principalmente:

- Facilidade para criar um agendamento;
- Clareza das mensagens de conflito;
- Facilidade para consultar a agenda;
- Facilidade de utilização das principais funcionalidades.

Os resultados serão utilizados para ajustar o protótipo e os requisitos do sistema.

---

## Conclusão

O processo de Design Thinking permitiu organizar o problema e identificar que o principal desafio da Playmakerz está na gestão integrada dos atendimentos.

A solução proposta busca centralizar atletas, profissionais, espaços e equipamentos em um único sistema, permitindo verificar a disponibilidade dos recursos e reduzir conflitos de agendamento.

As próximas etapas envolvem validar essas hipóteses com a Playmakerz e aprimorar o protótipo antes da implementação.

---

## Autor(es)

| Data | Versão | Descrição | Autor(es) |
|------|--------|-----------|-----------|
| 30/09/2026 | 1.0 | Elaboração do Design Thinking | Daniel Gusmao |