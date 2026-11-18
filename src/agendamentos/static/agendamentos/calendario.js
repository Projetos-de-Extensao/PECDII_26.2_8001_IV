(() => {
    const campos = document.querySelectorAll("[data-calendario]");
    if (!campos.length || typeof HTMLDialogElement === "undefined") return;

    const calendario = document.createElement("dialog");
    calendario.className = "calendario";
    calendario.setAttribute("aria-labelledby", "calendario-titulo");
    calendario.innerHTML = `
        <h2 id="calendario-titulo">Selecionar data</h2>
        <div class="calendario-controles">
            <button type="button" data-anterior aria-label="Mês anterior">‹</button>
            <select aria-label="Mês"></select>
            <input type="number" min="1" max="9999" step="1" aria-label="Ano">
            <button type="button" data-proximo aria-label="Próximo mês">›</button>
        </div>
        <div class="calendario-dias"></div>
        <button type="button" class="button button-small button-secondary" data-fechar>Fechar</button>
    `;
    document.body.append(calendario);

    const mes = calendario.querySelector("select");
    const ano = calendario.querySelector("input");
    const dias = calendario.querySelector(".calendario-dias");
    const anterior = calendario.querySelector("[data-anterior]");
    const proximo = calendario.querySelector("[data-proximo]");
    const hoje = new Date();
    const nomeMes = new Intl.DateTimeFormat("pt-BR", { month: "long", timeZone: "UTC" });

    function dataUTC(ano, mes, dia) {
        const data = new Date(0);
        data.setUTCFullYear(ano, mes, dia);
        return data;
    }

    function formatar(data) {
        const dia = String(data.getUTCDate()).padStart(2, "0");
        const mes = String(data.getUTCMonth() + 1).padStart(2, "0");
        const ano = String(data.getUTCFullYear()).padStart(4, "0");
        return `${dia}/${mes}/${ano}`;
    }

    function interpretar(valor) {
        const partes = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(valor.trim());
        if (!partes) return null;
        const [, dia, mes, ano] = partes.map(Number);
        const data = dataUTC(ano, mes - 1, dia);
        return ano >= 1 && data.getUTCFullYear() === ano &&
            data.getUTCMonth() === mes - 1 && data.getUTCDate() === dia ? data : null;
    }

    for (let indice = 0; indice < 12; indice += 1) {
        mes.add(new Option(nomeMes.format(dataUTC(2000, indice, 1)), indice));
    }

    let campo;
    let mesAtual;
    let minima;
    let maxima;

    function limites(entrada) {
        return {
            minima: interpretar(entrada.dataset.minima || "") || dataUTC(1, 0, 1),
            maxima: interpretar(entrada.dataset.maxima || "") || dataUTC(9999, 11, 31),
        };
    }

    function mensagemData(entrada) {
        if (!entrada.value) return "";
        const data = interpretar(entrada.value);
        if (!data) return "Informe uma data válida no formato dd/mm/aaaa.";
        const { minima, maxima } = limites(entrada);
        if (data < minima) return "Escolha a data de hoje ou uma data futura.";
        if (data > maxima) {
            return entrada.dataset.calendario === "nascimento"
                ? "A data de nascimento não pode ser futura."
                : `Escolha uma data até ${formatar(maxima)}.`;
        }
        return "";
    }

    function aplicarMascara(entrada) {
        const valor = entrada.value;
        const fim = entrada.selectionEnd ?? valor.length;
        const posicao = valor.slice(0, fim).replace(/[^0-9]/g, "").length;
        const digitos = valor.replace(/[^0-9]/g, "").slice(0, 8);
        const formatado = [digitos.slice(0, 2), digitos.slice(2, 4), digitos.slice(4)]
            .filter(Boolean).join("/");
        if (valor === formatado) return;

        entrada.value = formatado;
        let cursor = 0;
        let contagem = 0;
        while (cursor < formatado.length && contagem < posicao) {
            if (formatado[cursor] !== "/") contagem += 1;
            cursor += 1;
        }
        if (formatado[cursor] === "/") cursor += 1;
        entrada.setSelectionRange(cursor, cursor);
    }

    function mesDisponivel(ano, mes) {
        return dataUTC(ano, mes + 1, 0) >= minima && dataUTC(ano, mes, 1) <= maxima;
    }

    function abrirMes(data) {
        const dentroDoIntervalo = data < minima ? minima : data > maxima ? maxima : data;
        mesAtual = dataUTC(dentroDoIntervalo.getUTCFullYear(), dentroDoIntervalo.getUTCMonth(), 1);
        mostrarMes();
    }

    function mostrarMes() {
        const anoAtual = mesAtual.getUTCFullYear();
        const mesSelecionado = mesAtual.getUTCMonth();
        mes.value = mesSelecionado;
        ano.value = anoAtual;
        ano.min = minima.getUTCFullYear();
        ano.max = maxima.getUTCFullYear();
        anterior.disabled = !mesDisponivel(anoAtual, mesSelecionado - 1);
        proximo.disabled = !mesDisponivel(anoAtual, mesSelecionado + 1);
        for (const opcao of mes.options) {
            opcao.disabled = !mesDisponivel(anoAtual, Number(opcao.value));
        }
        dias.replaceChildren();

        for (const nome of ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]) {
            const cabecalho = document.createElement("span");
            cabecalho.textContent = nome;
            dias.append(cabecalho);
        }
        for (let dia = 0; dia < mesAtual.getUTCDay(); dia += 1) {
            dias.append(document.createElement("span"));
        }

        const selecionada = interpretar(campo.value);
        const totalDias = dataUTC(anoAtual, mesSelecionado + 1, 0).getUTCDate();
        for (let dia = 1; dia <= totalDias; dia += 1) {
            const data = dataUTC(anoAtual, mesSelecionado, dia);
            const valor = formatar(data);
            const botao = document.createElement("button");
            botao.type = "button";
            botao.textContent = dia;
            botao.disabled = data < minima || data > maxima;
            botao.setAttribute("aria-label", valor);
            botao.setAttribute("aria-pressed", data.getTime() === selecionada?.getTime());
            botao.addEventListener("click", () => {
                campo.value = valor;
                campo.dispatchEvent(new Event("input", { bubbles: true }));
                campo.dispatchEvent(new Event("change", { bubbles: true }));
                calendario.close();
            });
            dias.append(botao);
        }
    }

    function mudarMes(direcao) {
        abrirMes(dataUTC(mesAtual.getUTCFullYear(), mesAtual.getUTCMonth() + direcao, 1));
        if (document.activeElement === document.body) mes.focus();
    }

    anterior.addEventListener("click", () => mudarMes(-1));
    proximo.addEventListener("click", () => mudarMes(1));
    mes.addEventListener("change", () => {
        abrirMes(dataUTC(mesAtual.getUTCFullYear(), Number(mes.value), 1));
    });
    ano.addEventListener("change", () => {
        if (ano.value && ano.validity.valid) {
            abrirMes(dataUTC(ano.valueAsNumber, Number(mes.value), 1));
        } else {
            ano.value = mesAtual.getUTCFullYear();
        }
    });
    calendario.querySelector("[data-fechar]").addEventListener("click", () => calendario.close());

    for (const entrada of campos) {
        const controle = document.createElement("div");
        controle.className = "campo-calendario";
        entrada.before(controle);
        controle.append(entrada);

        const erro = document.createElement("div");
        erro.className = "field-error";
        erro.id = `${entrada.id}-calendario-erro`;
        erro.setAttribute("role", "status");
        controle.after(erro);
        entrada.setAttribute("aria-describedby",
            [entrada.getAttribute("aria-describedby"), erro.id].filter(Boolean).join(" ")
        );

        function validar(mostrar) {
            const mensagem = mensagemData(entrada);
            entrada.setCustomValidity(mensagem);
            erro.textContent = mostrar ? mensagem : "";
            if (mostrar && mensagem) entrada.setAttribute("aria-invalid", "true");
            else entrada.removeAttribute("aria-invalid");
        }

        entrada.addEventListener("input", () => {
            aplicarMascara(entrada);
            validar(entrada.value.length === 10);
        });
        entrada.addEventListener("blur", () => validar(true));
        entrada.addEventListener("invalid", () => validar(true));

        const abrir = document.createElement("button");
        abrir.type = "button";
        abrir.className = "button button-small button-secondary";
        abrir.textContent = "Calendário";
        abrir.setAttribute("aria-haspopup", "dialog");
        abrir.addEventListener("click", () => {
            campo = entrada;
            ({ minima, maxima } = limites(entrada));
            const data = interpretar(entrada.value) ||
                dataUTC(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
            abrirMes(data);
            calendario.showModal();
            mes.focus();
        });
        controle.append(abrir);
    }
})();
