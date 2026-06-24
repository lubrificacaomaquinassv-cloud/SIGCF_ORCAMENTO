from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from config import DEFAULT_XLSB_PATH, UPLOAD_DIR
from data_loader import (
    filter_dataframe,
    load_budget_data,
    merge_technical_sources,
    summarize_by_category,
    summarize_by_item_category,
    summarize_technical_by_category,
    summarize_technical_by_fornecedor,
)
from lancamentos import (
    add_lancamento,
    delete_lancamento,
    export_lancamentos_csv,
    import_lancamentos_csv,
    load_lancamentos,
)
from sigcf_auth import exigir_acesso
from ui import aplicar_tema, render_header, render_modulos


def _format_currency(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@st.cache_data(show_spinner="Carregando planilha...")
def get_planilha(file_path: str, file_mtime: float) -> pd.DataFrame:
    del file_mtime
    return load_budget_data(file_path)


def _resolve_planilha_path() -> tuple[str | None, str]:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    uploaded = st.session_state.get("planilha_uploaded")

    with st.sidebar:
        st.markdown("### Fonte de dados")
        st.markdown(
            '<div class="ctx-box">'
            "<b>Recomendado:</b> suba a planilha .xlsb consolidada da controladoria. "
            "Use lancamento manual apenas para NFEs novas ainda nao incluidas no arquivo."
            "</div>",
            unsafe_allow_html=True,
        )
        planilha_file = st.file_uploader("Planilha .xlsb", type=["xlsb"], key="upload_planilha")

        if planilha_file is not None:
            saved = UPLOAD_DIR / "gestao_orcamentaria_atual.xlsb"
            saved.write_bytes(planilha_file.getbuffer())
            st.session_state["planilha_uploaded"] = str(saved)
            uploaded = str(saved)
            st.success("Planilha carregada do upload.")

        if DEFAULT_XLSB_PATH.exists():
            usar_rede = st.checkbox("Usar planilha da rede V:\\", value=uploaded is None)
            if usar_rede:
                return str(DEFAULT_XLSB_PATH), "rede"

        if uploaded and Path(uploaded).exists():
            return uploaded, "upload"

        st.warning("Envie a planilha .xlsb para iniciar a analise.")
        return None, "pendente"


def _resolve_lancamentos() -> pd.DataFrame:
    with st.sidebar:
        st.markdown("### Lancamentos manuais")
        lanc_file = st.file_uploader(
            "Importar lancamentos.csv",
            type=["csv"],
            key="upload_lancamentos",
            help="Use para restaurar lancamentos manuais no Streamlit Cloud.",
        )
        if lanc_file is not None:
            import_lancamentos_csv(lanc_file.getvalue())
            st.success("Lancamentos importados.")

        lancamentos = load_lancamentos()
        if not lancamentos.empty:
            st.download_button(
                "Exportar lancamentos.csv",
                data=export_lancamentos_csv(),
                file_name="lancamentos.csv",
                mime="text/csv",
                use_container_width=True,
            )
        st.caption(f"{len(lancamentos)} lancamento(s) manual(is)")
    return lancamentos


def _render_novo_lancamento(planilha: pd.DataFrame) -> None:
    st.markdown('<div class="sec">Registrar lancamento de custo</div>', unsafe_allow_html=True)
    st.caption("Fornecedor · ID SAP · Categoria · Valor")

    fornecedores = sorted(planilha["FORNECEDORES"].dropna().unique()) if not planilha.empty else []
    categorias = sorted(planilha["CATEGORIA"].dropna().unique()) if not planilha.empty else []
    mapa_sap = (
        planilha.groupby("FORNECEDORES")["ID_FORNECEDOR_SAP"]
        .agg(lambda s: s.dropna().astype(str).mode().iloc[0] if not s.dropna().empty else "")
        .to_dict()
        if not planilha.empty
        else {}
    )

    with st.form("form_lancamento", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            data_lanc = st.date_input("Data", value=pd.Timestamp.today().date())
            if fornecedores:
                fornecedor = st.selectbox("Fornecedor", options=fornecedores + ["Outro..."])
            else:
                fornecedor = "Outro..."
            if fornecedor == "Outro...":
                fornecedor = st.text_input("Nome do fornecedor")
        with c2:
            id_sap = st.text_input(
                "ID Fornecedor SAP",
                value=mapa_sap.get(fornecedor, "") if fornecedor and fornecedor != "Outro..." else "",
                placeholder="Ex: F00014",
            )
            if categorias:
                categoria = st.selectbox("Categoria", options=categorias + ["Outra..."])
            else:
                categoria = "Outra..."
            if categoria == "Outra...":
                categoria = st.text_input("Nome da categoria")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")

        submitted = st.form_submit_button("Registrar lancamento", type="primary", use_container_width=True)

    if submitted:
        if not fornecedor or not id_sap or not categoria or valor <= 0:
            st.error("Preencha Fornecedor, ID SAP, Categoria e Valor maior que zero.")
        else:
            add_lancamento(
                fornecedor=fornecedor,
                id_fornecedor_sap=id_sap,
                categoria=categoria,
                valor=valor,
                data_lancamento=pd.Timestamp.combine(data_lanc, pd.Timestamp.min.time()),
            )
            st.success("Lancamento registrado. Exporte o CSV na barra lateral para guardar no Streamlit Cloud.")
            st.rerun()


def _render_consultar_lancamentos(lancamentos: pd.DataFrame) -> None:
    st.markdown('<div class="sec">Consultar lancamentos manuais</div>', unsafe_allow_html=True)
    if lancamentos.empty:
        st.info("Nenhum lancamento manual registrado ainda.")
        return

    view = lancamentos.copy()
    view["DATA_LANCAMENTO"] = pd.to_datetime(view["DATA_LANCAMENTO"]).dt.strftime("%d/%m/%Y")
    view["VALOR_FMT"] = view["VALOR"].map(_format_currency)
    st.dataframe(
        view[["ID", "DATA_LANCAMENTO", "FORNECEDOR", "ID_FORNECEDOR_SAP", "CATEGORIA", "VALOR_FMT", "ORIGEM"]].rename(
            columns={"VALOR_FMT": "VALOR"}
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    c1, c2 = st.columns([3, 1])
    with c1:
        lancamento_id = st.selectbox("Selecionar lancamento para excluir", lancamentos["ID"].tolist())
    with c2:
        if st.button("Excluir lancamento", use_container_width=True):
            delete_lancamento(lancamento_id)
            st.success("Lancamento excluido.")
            st.rerun()


def _render_visao_tecnica(tecnico: pd.DataFrame) -> None:
    st.markdown('<div class="sec">Visao tecnica de custos por categoria</div>', unsafe_allow_html=True)
    st.caption("Quanto cada categoria consome do total. Base para cruzamento futuro com frota e pecas.")

    categorias_opts = sorted(tecnico["CATEGORIA"].dropna().unique())
    fornecedores_opts = sorted(tecnico["FORNECEDOR"].dropna().unique())

    c1, c2, c3 = st.columns(3)
    with c1:
        categorias_sel = st.multiselect("Filtrar categorias", categorias_opts)
    with c2:
        fornecedores_sel = st.multiselect("Filtrar fornecedores", fornecedores_opts)
    with c3:
        origem_sel = st.multiselect("Origem", ["PLANILHA", "MANUAL"], default=["PLANILHA", "MANUAL"])

    filtered = tecnico.copy()
    if categorias_sel:
        filtered = filtered[filtered["CATEGORIA"].isin(categorias_sel)]
    if fornecedores_sel:
        filtered = filtered[filtered["FORNECEDOR"].isin(fornecedores_sel)]
    if origem_sel:
        filtered = filtered[filtered["ORIGEM"].isin(origem_sel)]

    total = filtered["VALOR"].sum()
    by_category = summarize_technical_by_category(filtered)

    m1, m2, m3 = st.columns(3)
    m1.metric("Total analisado", _format_currency(total))
    m2.metric("Categorias", filtered["CATEGORIA"].nunique())
    m3.metric("Fornecedores", filtered["FORNECEDOR"].nunique())

    left, right = st.columns([1.2, 1])
    with left:
        fig_bar = px.bar(
            by_category.head(20),
            x="VALOR",
            y="CATEGORIA",
            orientation="h",
            title="Consumo por categoria",
            labels={"VALOR": "Valor (R$)", "CATEGORIA": "Categoria"},
        )
        fig_bar.update_layout(yaxis={"categoryorder": "total ascending"}, height=650, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)
    with right:
        fig_pie = px.pie(
            by_category.head(12),
            names="CATEGORIA",
            values="VALOR",
            title="Participacao das 12 maiores categorias",
            hole=0.35,
        )
        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_pie, use_container_width=True)

    st.dataframe(
        by_category.assign(VALOR=by_category["VALOR"].map(_format_currency)),
        use_container_width=True,
        hide_index=True,
    )

    if by_category.empty:
        return

    st.divider()
    categoria_drill = st.selectbox("Detalhar fornecedores da categoria", by_category["CATEGORIA"].tolist())
    fornecedores_cat = summarize_technical_by_fornecedor(filtered, categoria_drill)
    st.subheader(f"{categoria_drill} — {_format_currency(fornecedores_cat['VALOR'].sum())}")

    fig_forn = px.bar(
        fornecedores_cat.head(20),
        x="FORNECEDOR",
        y="VALOR",
        color="ID_FORNECEDOR_SAP",
        title=f"Top fornecedores em {categoria_drill}",
        labels={"VALOR": "Valor (R$)", "FORNECEDOR": "Fornecedor"},
    )
    fig_forn.update_layout(xaxis_tickangle=-30, height=450, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_forn, use_container_width=True)


def _render_painel_planilha(planilha: pd.DataFrame) -> None:
    with st.sidebar:
        min_date = planilha["DATA_EMISSAO"].min()
        max_date = planilha["DATA_EMISSAO"].max()
        if pd.notna(min_date) and pd.notna(max_date):
            date_range = st.date_input(
                "Periodo",
                value=(min_date.date(), max_date.date()),
                min_value=min_date.date(),
                max_value=max_date.date(),
            )
            if isinstance(date_range, tuple) and len(date_range) == 2:
                data_inicio = pd.Timestamp(date_range[0])
                data_fim = pd.Timestamp(date_range[1])
            else:
                data_inicio = pd.Timestamp(date_range)
                data_fim = pd.Timestamp(date_range)
        else:
            data_inicio = None
            data_fim = None

        categorias_opts = sorted(planilha["CATEGORIA"].dropna().unique())
        itens_opts = sorted(planilha["ITEM"].dropna().unique())
        centros_opts = sorted(planilha["CENTRO_CUSTO"].dropna().unique())
        categorias_sel = st.multiselect("Categorias", categorias_opts)
        itens_sel = st.multiselect("Itens", itens_opts)
        centros_sel = st.multiselect("Centro de custo", centros_opts)

    filtered = filter_dataframe(
        planilha,
        categorias=categorias_sel or None,
        itens=itens_sel or None,
        centros_custo=centros_sel or None,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )

    total = filtered["VALOR_TOTAL_GESTAO"].sum()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de custos", _format_currency(total))
    c2.metric("Registros", f"{len(filtered):,}".replace(",", "."))
    c3.metric("Categorias", filtered["CATEGORIA"].nunique())
    c4.metric("Itens", filtered["ITEM"].nunique())

    by_category = summarize_by_category(filtered)
    tab_resumo, tab_categoria, tab_item, tab_detalhe = st.tabs(
        ["Resumo", "Por Categoria", "Item x Categoria", "Detalhamento"]
    )

    with tab_resumo:
        left, right = st.columns([1.2, 1])
        with left:
            fig_bar = px.bar(by_category.head(20), x="VALOR", y="CATEGORIA", orientation="h")
            fig_bar.update_layout(yaxis={"categoryorder": "total ascending"}, height=650, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar, use_container_width=True)
        with right:
            fig_pie = px.pie(by_category.head(10), names="CATEGORIA", values="VALOR", hole=0.35)
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab_detalhe:
        display_cols = [
            "DATA_EMISSAO", "FORNECEDORES", "ITEM", "CATEGORIA",
            "SUBGRUPO", "CENTRO_CUSTO", "DESTINACAO", "FROTA", "VALOR_TOTAL_GESTAO",
        ]
        detail = filtered[display_cols].copy()
        detail["DATA_EMISSAO"] = detail["DATA_EMISSAO"].dt.strftime("%d/%m/%Y")
        st.dataframe(detail, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(
        page_title="SIGCF — Gestao Orcamentaria",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    aplicar_tema()
    exigir_acesso("SIGCF — Gestao Orcamentaria", "Santa Virgínia · Controladoria · Custos por categoria")

    render_header("SIGCF ORCAMENTO", "SANTA VIRGÍNIA · GESTÃO ORÇAMENTÁRIA · CUSTOS POR CATEGORIA")
    st.divider()
    render_modulos()
    st.divider()

    planilha_path, origem = _resolve_planilha_path()
    lancamentos = _resolve_lancamentos()

    if not planilha_path:
        st.stop()

    try:
        mtime = Path(planilha_path).stat().st_mtime
        planilha = get_planilha(planilha_path, mtime)
    except Exception as exc:
        st.error(f"Erro ao ler planilha: {exc}")
        st.stop()

    tecnico = merge_technical_sources(planilha, lancamentos)

    with st.sidebar:
        st.success(f"Planilha ({origem}): {len(planilha):,} registros".replace(",", "."))

    tab_lanc, tab_consulta, tab_tecnica, tab_planilha = st.tabs(
        ["Novo Lancamento", "Consultar", "Visao Tecnica", "Painel Planilha"]
    )
    with tab_lanc:
        _render_novo_lancamento(planilha)
    with tab_consulta:
        _render_consultar_lancamentos(lancamentos)
    with tab_tecnica:
        _render_visao_tecnica(tecnico)
    with tab_planilha:
        _render_painel_planilha(planilha)


if __name__ == "__main__":
    main()
