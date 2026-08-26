# GitHub Workflows

## Objetivo
Apresentar, de forma prática, o fluxo básico de trabalho com GitHub usando **branches**, **features**, **merges** e **pull requests (PRs)**.

## 1) Conceitos Essenciais
- **Branch**: linha de desenvolvimento isolada.
- **Feature branch**: branch criada para uma funcionalidade específica.
- **Merge**: integração das mudanças de uma branch em outra.
- **Pull Request (PR)**: solicitação formal para revisar e integrar código.

## 2) Fluxo Padrão (visão geral)
1. Atualizar a branch principal (`main`).
2. Criar uma nova branch de feature.
3. Implementar alterações e realizar commits pequenos.
4. Publicar a branch no GitHub.
5. Abrir Pull Request para `main`.
6. Revisar, ajustar e aprovar.
7. Fazer merge e remover a branch de feature.

## 3) Passo a Passo com Comandos

### 3.1 Atualizar `main`
```bash
git checkout main
git pull origin main
```

### 3.2 Criar branch de feature
> Sugestão de nome: `feature/<descricao-curta>`

```bash
git checkout -b feature/login-basico
```

### 3.3 Desenvolver e versionar
```bash
git add .
git commit -m "feat: adiciona tela inicial de login"
```

### 3.4 Enviar branch para o GitHub
```bash
git push -u origin feature/login-basico
```

### 3.5 Abrir Pull Request
No GitHub:
- Base: `main`
- Compare: `feature/login-basico`
- Descrever:
    - O que foi feito
    - Como testar
    - Pontos de atenção

### 3.6 Revisão e ajustes
Se solicitado, aplicar mudanças e enviar novos commits:
```bash
git add .
git commit -m "refactor: ajusta validação de campos"
git push
```

### 3.7 Merge e limpeza
Após aprovação:
- Fazer **Merge pull request**
- Remover branch no GitHub
- Localmente:
```bash
git checkout main
git pull origin main
git branch -d feature/login-basico
```

## 4) Boas Práticas para Iniciantes
- Criar **1 branch por tarefa**.
- Commits curtos e com mensagem clara.
- Evitar mudanças grandes em um único PR.
- Solicitar revisão antes do merge.
- Manter a `main` sempre estável.

## 5) Exercício Guiado (20–30 min)
1. Criar branch `feature/apresentacao-aluno`.
2. Adicionar arquivo `aluno.md` com nome e curso.
3. Commit + push.
4. Abrir PR para `main`.
5. Revisar PR de um colega.
6. Fazer merge após aprovação.

## 6) Resultado Esperado
Ao final, o aluno deverá:
- Criar e gerenciar branches de feature.
- Abrir e atualizar Pull Requests.
- Entender o processo de revisão e merge com segurança.