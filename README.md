# Calculadora em segundo plano

Calculadora com interface gráfica que fica a correr em segundo plano, com um ícone na bandeja do sistema.

## Funcionalidades

- Interface simples com operações básicas, parênteses e potências (`^`).
- Ao fechar a janela, a calculadora continua ativa na bandeja.
- Clique no ícone (ou botão direito > **Mostrar**) para a abrir de novo.
- Botão direito > **Sair** para a fechar completamente.
- Atalhos: `Enter` calcula, `Esc` limpa.

## Requisitos

- Python 3.8 ou superior
- `pystray` e `pillow`

## Instalação

```bash
pip install -r requirements.txt
```

## Execução

Windows (sem janela de consola):

```bash
pythonw calculadora_segundo_plano.py
```

Outros sistemas:

```bash
python calculadora_segundo_plano.py
```

## Arranque automático (Windows)

Prime `Win + R`, escreve `shell:startup` e cria lá um atalho para o `calculadora_segundo_plano.py` (com `pythonw` como programa).

## Licença

MIT
