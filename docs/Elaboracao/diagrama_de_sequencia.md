---
id: diagrama_de_sequencia
title: Diagrama de Sequência
---

### Diagrama de Sequência

O Diagrama de Sequência é uma representação visual que mostra a interação entre objetos ou componentes ao longo do tempo. Ele é usado para modelar o comportamento dinâmico de um sistema, ilustrando como os objetos colaboram para realizar uma funcionalidade específica.	

#### Objetivo

Definir um padrão para elaboração e registro dos Diagramas de Sequência, garantindo rastreabilidade com:

- Casos de Uso
- Diagrama de Casos de Uso
- Documento de Levantamento de Requisitos
- Protótipo de Baixa Fidelidade

#### Instruções de Preenchimento

1. Selecione um Caso de Uso prioritário.
2. Identifique os requisitos funcionais e regras de negócio relacionados.
3. Mapeie as telas/fluxos no protótipo de baixa fidelidade.
4. Modele a interação entre ator(es), fronteira, controle e entidade.
5. Valide consistência com o fluxo principal e fluxos alternativos.


#### Template — Diagrama de Sequência por Caso de Uso

##### 1. Identificação

- **Caso de Uso:**  
- **ID do Caso de Uso:**  
- **Ator(es):**  
- **Prioridade:**  
- **Responsável:**  
- **Data:**  

##### 2. Referências

- **Requisitos relacionados (ID):**  
- **Diagrama de Caso de Uso (link/imagem):**  
- **Protótipo de Baixa Fidelidade (tela/fluxo):**  
- **Regra(s) de negócio associada(s):**  

##### 3. Cenário Modelado

- **Objetivo do cenário:**  
- **Pré-condições:**  
- **Pós-condições:**  
- **Gatilho de início:**  

##### 4. Participantes (Lifelines)

- **Ator:**  
- **Boundary (Interface/Tela):**  
- **Control (Orquestração):**  
- **Entity (Dados/Serviços):**  
- **Sistemas externos (se houver):**  

##### 5. Fluxo Principal (mensagens)

| Passo | Remetente | Destinatário | Mensagem/Ação | Tipo (sync/async/retorno) |
|------:|-----------|--------------|---------------|----------------------------|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |

##### 6. Fluxos Alternativos e Exceções

| ID | Condição | Descrição do fluxo | Impacto |
|----|----------|--------------------|---------|
| A1 |  |  |  |
| E1 |  |  |  |

##### 7. Regras de Negócio Aplicadas

- **RN-xx:**  
- **RN-yy:**  

##### 8. Pontos de Validação

- [ ] Fluxo compatível com Caso de Uso  
- [ ] Mensagens consistentes com requisitos funcionais  
- [ ] Alternativas/exceções representadas  
- [ ] Participantes aderentes à arquitetura  
- [ ] Correspondência com protótipo de baixa fidelidade  

##### 9. Artefatos

- **Imagem do Diagrama de Sequência:**  
- **Arquivo fonte (PlantUML):**  
- **Versão:**  

---

#### Exemplo de estrutura textual mínima (opcional)

```text
Ator inicia ação na Tela X
Tela X envia solicitação para Controlador Y
Controlador Y valida regra RN-01
Controlador Y consulta Entidade/Serviço Z
Entidade/Serviço Z retorna resultado
Controlador Y responde à Tela X
Tela X apresenta confirmação ao Ator
```