---
id: diagrama_de_cclasses
title: Diagrama de Classes
---

## Diagrama de Classes

### Objetivo

O Diagrama de Classes é uma representação visual das classes, seus atributos, métodos e os relacionamentos entre elas. Ele é fundamental para a modelagem orientada a objetos e serve como base para a implementação do sistema.

### Componentes do Diagrama de Classes

Este documento define um modelo para:

1. **Inserção do Diagrama de Classes Conceitual** (visão de domínio).  
2. **Evolução para o Diagrama de Classes de Especificação** (visão de projeto).  

Ambos devem ser derivados de:

- Casos de uso;
- Diagrama de casos de uso;
- Documento de levantamento de requisitos;
- Protótipo de baixa fidelidade.

### Fontes de entrada obrigatórias

- **Levantamento de requisitos**: requisitos funcionais e não funcionais.
- **Casos de uso**: atores, fluxos principal e alternativos.
- **Diagrama de casos de uso**: escopo e fronteiras do sistema.
- **Protótipo de baixa fidelidade**: entidades percebidas na interface e regras de navegação.

### 1) Diagrama de Classes Conceitual

#### 1.1 Finalidade

Representar conceitos do domínio, suas responsabilidades e relacionamentos, sem detalhes de implementação.

#### 1.2 Escopo

- Entidades de negócio;
- Objetos de valor;
- Regras de associação e cardinalidade;
- Generalizações relevantes.

#### 1.3 Notação mínima

Para cada classe conceitual:

- **Nome**;
- **Descrição curta**;
- **Atributos de domínio** (sem tipos técnicos, quando possível);
- **Relacionamentos** com multiplicidade;
- **Restrições de negócio** (opcional).

#### 1.4 Rastreabilidade

| Classe Conceitual | Requisito(s) | Caso(s) de Uso | Tela/Protótipo |
|---|---|---|---|
| `<Classe>` | `RF-xx` | `UC-xx` | `Tela xx` |

#### 1.5 Critérios de validação

- Cada classe deve ter vínculo com ao menos um requisito/caso de uso;
- Não incluir classes técnicas (ex.: repositório, controller);
- Terminologia alinhada ao domínio do problema.

### 2) Transição para Diagrama de Classes de Especificação

#### 2.1 Objetivo
Refinar o modelo conceitual para uma estrutura orientada à implementação.

#### 2.2 Regras de refinamento

- Converter conceitos em classes de software quando aplicável;
- Definir tipos de atributos e visibilidade;
- Incluir operações principais;
- Aplicar estereótipos quando necessário (ex.: `<<entity>>`, `<<service>>`, `<<boundary>>`);
- Preservar rastreabilidade com requisitos e casos de uso.

#### 2.3 Itens esperados por classe

- **Nome da classe**;
- **Atributos** (`nome: tipo [visibilidade]`);
- **Métodos/operações** (`assinatura`);
- **Responsabilidade**;
- **Dependências e associações**;
- **Restrições/invariantes** (quando houver).


### 3) Diagrama de Classes de Especificação

#### 3.1 Conteúdo mínimo

- Classes de domínio e de apoio à aplicação;
- Interfaces relevantes;
- Associações, agregações/composições e heranças;
- Multiplicidades e navegabilidade;
- Operações alinhadas aos fluxos dos casos de uso.

#### 3.2 Rastreabilidade

| Classe de Especificação | Origem Conceitual | Requisito(s) | Caso(s) de Uso |
|---|---|---|---|
| `<ClasseSpec>` | `<ClasseConceitual>` | `RF-xx` | `UC-xx` |

#### 3.3 Critérios de qualidade

- Cobertura dos requisitos funcionais;
- Coesão alta e acoplamento controlado;
- Nomes consistentes com o domínio;
- Ausência de classes sem responsabilidade clara.


### 4) Estrutura de versionamento e revisão

- **Versão**: `v0.1`, `v0.2`...
- **Data**: `dd/mm/aaaa`
- **Autor(es)**: `<nome>`
- **Revisor(es)**: `<nome>`
- **Resumo da alteração**: `<descrição curta>`

### 5) Entregáveis

- Diagrama de Classes Conceitual (imagem + fonte);
- Diagrama de Classes de Especificação (imagem + fonte);
- Tabelas de rastreabilidade preenchidas;
- Registro de validação com equipe e stakeholders.