# SIGCF — Gestão Orçamentária

Painel Streamlit para análise de custos por **Fornecedor · ID SAP · Categoria · Valor**, com layout padronizado Santa Virgínia (SIGRH/SIGCF).

## Fluxo recomendado de dados

| Origem | Quando usar |
|--------|-------------|
| **Upload da planilha .xlsb** | Base principal — dados consolidados da controladoria |
| **Lançamento manual** | NFEs novas ainda não incluídas na planilha |
| **Exportar/importar lancamentos.csv** | Persistir lançamentos manuais no Streamlit Cloud (sem banco) |

## Executar localmente

```powershell
cd D:\pwa-comboio-posto-abastecimento\SIGCF_ORCAMENTO
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Com acesso à rede, marque **Usar planilha da rede V:\\** na barra lateral.

## Publicar no GitHub

```powershell
cd D:\pwa-comboio-posto-abastecimento\SIGCF_ORCAMENTO
gh auth login
git init
git add .
git commit -m "SIGCF Orcamento: painel de custos por categoria"
gh repo create SIGCF_ORCAMENTO --private --source=. --push
```

Use o mesmo e-mail da conta GitHub/Streamlit nos commits (configure globalmente se ainda não estiver).

## Publicar no Streamlit Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io) com o **mesmo e-mail** do GitHub.
2. **New app** → selecione o repositório `SIGCF_ORCAMENTO`.
3. Main file: `app.py`
4. Em **Secrets**, opcionalmente:

```toml
APP_PIN = "seu_pin"
```

5. Deploy. Na primeira abertura, faça **upload da planilha .xlsb** na barra lateral.

## Estrutura

```
SIGCF_ORCAMENTO/
├── app.py              # Interface principal
├── config.py           # Caminhos e colunas
├── data_loader.py      # Leitura .xlsb e agregações
├── lancamentos.py      # Lançamentos manuais (CSV)
├── sigcf_auth.py       # PIN opcional + logo
├── ui.py               # CSS e layout SIGCF
├── data/lancamentos.csv
├── .streamlit/config.toml
└── requirements.txt
```

## Próximos módulos (em breve)

- Meta x realizado por categoria
- Cruzamento com frota (peças, motos, veículos)
