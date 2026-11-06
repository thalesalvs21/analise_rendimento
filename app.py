from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PASTA = Path(__file__).parent
BASE_PADRAO = PASTA / "dados" / "rendimento_responsaveis.csv"

SALARIO_MINIMO = {2010: 510, 2022: 1212}
COLUNAS = ["ano", "regiao", "uf", "cod_municipio", "municipio", "situacao",
           "responsaveis", "renda_media", "populacao_municipio", "porte"]
ORDEM_PORTE = ["Até 20 mil hab.", "20 mil a 100 mil hab.", "100 mil a 500 mil hab.", "Mais de 500 mil hab."]
ORDEM_REGIAO = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
CORES_REGIAO = {"Norte": "#2a78d6", "Nordeste": "#eb6834", "Centro-Oeste": "#1baf7a",
                "Sudeste": "#eda100", "Sul": "#e87ba4"}
COR_ANO = {2010: "#2a78d6", 2022: "#eb6834"}


def reais(valor):
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + texto


def numero(valor, casas=0):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def ler_arquivo(arquivo):
    if arquivo.name.lower().endswith(".xlsx"):
        return pd.read_excel(arquivo)
    return pd.read_csv(arquivo, sep=None, engine="python", encoding="utf-8-sig")


@st.cache_data
def ler_base_padrao():
    return pd.read_csv(BASE_PADRAO, encoding="utf-8-sig")


def limpar(df):
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    faltando = [c for c in COLUNAS if c not in df.columns]
    if faltando:
        return None, faltando

    df = df[COLUNAS]
    for col in ["ano", "cod_municipio", "responsaveis", "renda_media", "populacao_municipio"]:
        if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
            texto = df[col].astype(str).str.strip()
            com_virgula = texto.str.contains(",", regex=False)
            texto[com_virgula] = texto[com_virgula].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
            df[col] = texto
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["regiao", "uf", "municipio", "situacao", "porte"]:
        df[col] = df[col].astype(str).str.strip()

    df = df.dropna(subset=["ano", "cod_municipio", "responsaveis", "renda_media"])
    df = df[(df["renda_media"] > 0) & (df["responsaveis"] > 0)]
    df = df.drop_duplicates()
    df["ano"] = df["ano"].astype(int)
    df["situacao"] = df["situacao"].str.title()
    return df, []


def juntar_por_municipio(df):
    df = df.copy()
    df["renda_x_resp"] = df["renda_media"] * df["responsaveis"]
    chaves = ["ano", "regiao", "uf", "cod_municipio", "municipio", "porte", "populacao_municipio"]
    tabela = df.groupby(chaves, as_index=False)[["renda_x_resp", "responsaveis"]].sum()
    tabela["renda_rs"] = tabela["renda_x_resp"] / tabela["responsaveis"]
    tabela["renda_sm"] = tabela["renda_rs"] / tabela["ano"].map(SALARIO_MINIMO)
    return tabela.drop(columns="renda_x_resp")


def faixa_sm(valor_sm):
    if valor_sm <= 1:
        return "Até 1 SM"
    if valor_sm <= 2:
        return "1 a 2 SM"
    if valor_sm <= 3:
        return "2 a 3 SM"
    if valor_sm <= 5:
        return "3 a 5 SM"
    return "Mais de 5 SM"


def estatisticas(serie, faixas):
    q1 = serie.quantile(0.25)
    q3 = serie.quantile(0.75)
    iqr = q3 - q1
    return {
        "media": serie.mean(),
        "mediana": serie.median(),
        "moda": faixas.mode()[0],
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "minimo": serie.min(),
        "maximo": serie.max(),
        "amplitude": serie.max() - serie.min(),
        "variancia": serie.var(ddof=0),
        "desvio": serie.std(ddof=0),
        "cv": serie.std(ddof=0) / serie.mean() * 100,
        "lim_inf": q1 - 1.5 * iqr,
        "lim_sup": q3 + 1.5 * iqr,
    }


st.set_page_config(page_title="Rendimento dos Responsáveis | IBGE", layout="wide")

st.sidebar.header("Rendimento dos Responsáveis")
arquivo = st.sidebar.file_uploader("Enviar base do IBGE (CSV ou XLSX)", type=["csv", "xlsx"])

if arquivo is not None:
    try:
        bruto = ler_arquivo(arquivo)
        st.sidebar.success(f"Arquivo carregado: {arquivo.name}")
    except Exception as erro:
        st.sidebar.error(f"Não consegui ler o arquivo: {erro}")
        st.stop()
else:
    bruto = ler_base_padrao()
    st.sidebar.caption("Usando a base padrão do projeto (Censo 2010 e 2022).")

base, faltando = limpar(bruto)
if base is None:
    st.error("O arquivo enviado não tem as colunas esperadas. Faltam: " + ", ".join(faltando))
    st.write("Colunas que o arquivo precisa ter:", ", ".join(COLUNAS))
    st.stop()

st.sidebar.subheader("Filtros")
anos = sorted(base["ano"].unique())
ano = st.sidebar.radio("Ano do Censo", anos, index=len(anos) - 1, horizontal=True)

regioes_existentes = [r for r in ORDEM_REGIAO if r in base["regiao"].unique()]
regioes = st.sidebar.multiselect("Região", regioes_existentes, default=regioes_existentes)

ufs_existentes = sorted(base[base["regiao"].isin(regioes)]["uf"].unique())
ufs = st.sidebar.multiselect("UF", ufs_existentes, default=ufs_existentes)

situacoes_existentes = sorted(base["situacao"].unique(), reverse=True)
situacoes = st.sidebar.multiselect("Situação do domicílio", situacoes_existentes, default=situacoes_existentes)

portes_existentes = [p for p in ORDEM_PORTE if p in base["porte"].unique()]
portes = st.sidebar.multiselect("Porte do município", portes_existentes, default=portes_existentes)

unidade = st.sidebar.radio("Mostrar valores em", ["Reais (R$)", "Salários mínimos (SM)"])

filtro = (base["regiao"].isin(regioes) & base["uf"].isin(ufs)
          & base["situacao"].isin(situacoes) & base["porte"].isin(portes))
recorte_todos_anos = juntar_por_municipio(base[filtro])
dados = recorte_todos_anos[recorte_todos_anos["ano"] == ano].copy()

if dados.empty:
    st.warning("Nenhum município com esses filtros. Marque pelo menos uma opção em cada filtro.")
    st.stop()

em_reais = unidade == "Reais (R$)"
coluna = "renda_rs" if em_reais else "renda_sm"
if em_reais:
    rotulo = "Renda média do responsável (R$)"
else:
    rotulo = "Renda média do responsável (salários mínimos)"


def formatar(valor):
    if em_reais:
        return reais(valor)
    return numero(valor, 2) + " SM"


dados["faixa"] = dados["renda_sm"].apply(faixa_sm)
est = estatisticas(dados[coluna], dados["faixa"])
dados["outlier"] = np.where(dados[coluna] > est["lim_sup"], "Acima do limite",
                            np.where(dados[coluna] < est["lim_inf"], "Abaixo do limite", "Dentro do padrão"))
acima = dados[dados["outlier"] == "Acima do limite"]
abaixo = dados[dados["outlier"] == "Abaixo do limite"]
sem_outliers = dados[dados["outlier"] == "Dentro do padrão"]

media_ponderada = (dados[coluna] * dados["responsaveis"]).sum() / dados["responsaveis"].sum()
assimetria = dados[coluna].skew()

st.title("Rendimento dos Responsáveis pelo Domicílio")
st.caption(f"Indicador 5 · IBGE, Censo Demográfico {ano} · cada ponto dos gráficos é um município")
st.markdown(
    "Quanto ganha, por mês, a pessoa responsável por cada casa no Brasil? "
    "Como startup de análise de dados, usamos os números do Censo para mostrar aos gestores públicos "
    "**onde a renda é mais baixa, o quanto ela varia entre os territórios e por que a média sozinha engana**."
)

abas = st.tabs(["Visão geral", "Outliers", "2010 x 2022", "Perguntas de negócio", "Notícias", "Dados e método"])

with abas[0]:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Municípios no recorte", numero(len(dados)))
    c2.metric("Média", formatar(est["media"]))
    c3.metric("Mediana", formatar(est["mediana"]))
    c4.metric("Desvio padrão", formatar(est["desvio"]))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("1º quartil (Q1)", formatar(est["q1"]))
    c2.metric("3º quartil (Q3)", formatar(est["q3"]))
    c3.metric("Intervalo interquartil (IQR)", formatar(est["iqr"]))
    c4.metric("Amplitude", formatar(est["amplitude"]))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Moda (faixa de renda)", est["moda"])
    c2.metric("Coeficiente de variação", numero(est["cv"], 1) + "%")
    c3.metric("Municípios outliers", numero(len(acima) + len(abaixo)))
    c4.metric("Média por domicílio", formatar(media_ponderada),
              help="Média de todos os responsáveis do recorte juntos. Aqui cada casa conta uma vez, "
                   "então as cidades grandes pesam mais do que nas medidas acima, que contam cada município uma vez.")

    st.subheader("Distribuição da renda entre os municípios")
    hist = px.histogram(dados, x=coluna, nbins=150, labels={coluna: rotulo},
                        color_discrete_sequence=["#86b6ef"])
    hist.update_traces(marker_line_color="white", marker_line_width=1,
                       hovertemplate="Faixa: %{x}<br>Municípios: %{y}<extra></extra>")
    hist.add_vline(x=est["media"], line_color="#eb6834", line_width=2,
                   annotation_text="Média " + formatar(est["media"]), annotation_position="top right",
                   annotation_y=0.9)
    hist.add_vline(x=est["mediana"], line_color="#0d366b", line_width=2, line_dash="dash",
                   annotation_text="Mediana " + formatar(est["mediana"]), annotation_position="top left")
    hist.update_layout(yaxis_title="Quantidade de municípios", bargap=0.02)
    st.plotly_chart(hist, width="stretch")
    st.caption(f"A distribuição tem uma cauda comprida para a direita (assimetria de {numero(assimetria, 2)}): "
               "a maioria dos municípios fica na mesma região do gráfico, e poucos se espalham para os valores altos. "
               "Esses poucos puxam a média para a direita, enquanto a mediana fica no meio da fila.")

    st.subheader("Boxplot por região")
    regioes_no_recorte = [r for r in ORDEM_REGIAO if r in dados["regiao"].unique()]
    caixa = px.box(dados, x="regiao", y=coluna, color="regiao", points="outliers",
                   category_orders={"regiao": regioes_no_recorte}, color_discrete_map=CORES_REGIAO,
                   hover_data={"municipio": True, "uf": True, "regiao": False},
                   labels={"regiao": "Região", coluna: rotulo, "municipio": "Município", "uf": "UF"})
    caixa.update_layout(showlegend=False)
    st.plotly_chart(caixa, width="stretch")
    st.caption("A caixa vai do Q1 ao Q3 (metade central dos municípios), a linha no meio é a mediana "
               "e os pontos soltos são os outliers pela regra de 1,5 × IQR.")

    st.subheader("Comparação entre as UFs")
    por_uf = dados.groupby(["uf", "regiao"], as_index=False)[coluna].agg(
        media="mean", mediana="median", desvio=lambda s: s.std(ddof=0),
        q1=lambda s: s.quantile(0.25), q3=lambda s: s.quantile(0.75), municipios="count")
    por_uf["iqr"] = por_uf["q3"] - por_uf["q1"]
    por_uf = por_uf.sort_values("mediana", ascending=False)

    barras = px.bar(por_uf, x="uf", y="mediana", color="regiao", color_discrete_map=CORES_REGIAO,
                    category_orders={"regiao": regioes_no_recorte, "uf": por_uf["uf"].tolist()},
                    labels={"uf": "UF", "mediana": "Mediana municipal", "regiao": "Região"},
                    hover_data={"media": ":.2f", "municipios": True})
    barras.update_layout(legend_title_text="Região")
    st.plotly_chart(barras, width="stretch")

    tabela_uf = por_uf.rename(columns={"uf": "UF", "regiao": "Região", "municipios": "Municípios",
                                       "media": "Média", "mediana": "Mediana", "desvio": "Desvio padrão",
                                       "q1": "Q1", "q3": "Q3", "iqr": "IQR"})
    tabela_uf = tabela_uf[["UF", "Região", "Municípios", "Média", "Mediana", "Q1", "Q3", "IQR", "Desvio padrão"]]
    st.dataframe(tabela_uf, hide_index=True, width="stretch",
                 column_config={c: st.column_config.NumberColumn(format="%.2f")
                                for c in ["Média", "Mediana", "Q1", "Q3", "IQR", "Desvio padrão"]})

with abas[1]:
    st.subheader("Regra de 1,5 × IQR")
    st.markdown(
        f"- Limite de baixo: Q1 − 1,5 × IQR = **{formatar(est['lim_inf'])}**\n"
        f"- Limite de cima: Q3 + 1,5 × IQR = **{formatar(est['lim_sup'])}**\n"
        f"- Municípios acima do limite: **{len(acima)}** · abaixo do limite: **{len(abaixo)}**"
    )
    if est["lim_inf"] < 0:
        st.caption("O limite de baixo deu negativo, e nenhuma renda é negativa. "
                   "Por isso não existe outlier para baixo: o problema da distribuição está na ponta de cima.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Média com outliers", formatar(est["media"]))
    c2.metric("Média sem outliers", formatar(sem_outliers[coluna].mean()))
    c3.metric("Mediana com outliers", formatar(est["mediana"]))
    st.markdown(
        f"Tirando os outliers, a média cai {formatar(est['media'] - sem_outliers[coluna].mean())}. "
        f"A mediana quase não depende deles: sem os outliers ela seria {formatar(sem_outliers[coluna].median())}. "
        "Por isso, para dizer qual é a renda **típica** de um município, a mediana é a medida mais honesta."
    )

    mostrar = ["municipio", "uf", "regiao", coluna, "populacao_municipio"]
    nomes = {"municipio": "Município", "uf": "UF", "regiao": "Região", coluna: rotulo,
             "populacao_municipio": "População"}
    formato = {rotulo: st.column_config.NumberColumn(format="%.2f"),
               "População": st.column_config.NumberColumn(format="%d")}
    st.subheader("Municípios com renda muito acima do padrão")
    st.dataframe(acima.sort_values(coluna, ascending=False)[mostrar].rename(columns=nomes),
                 hide_index=True, width="stretch", column_config=formato)
    if not abaixo.empty:
        st.subheader("Municípios com renda muito abaixo do padrão")
        st.dataframe(abaixo.sort_values(coluna)[mostrar].rename(columns=nomes),
                     hide_index=True, width="stretch", column_config=formato)

    st.subheader("Os 10 municípios com menor renda")
    st.dataframe(dados.nsmallest(10, coluna)[mostrar].rename(columns=nomes),
                 hide_index=True, width="stretch", column_config=formato)

with abas[2]:
    if recorte_todos_anos["ano"].nunique() < 2:
        st.info("A base carregada tem só um ano, então não dá para comparar.")
    else:
        st.markdown(
            "Para comparar anos diferentes usamos **salários mínimos (SM)**, porque o dinheiro de 2010 "
            "valia mais que o de 2022. O SM era R$ 510 em 2010 e R$ 1.212 em 2022. "
            "Atenção: entre esses anos o SM subiu mais que a inflação, então uma queda em SM "
            "não quer dizer que as pessoas ficaram mais pobres. Quer dizer que a renda subiu menos que o salário mínimo."
        )
        evolucao = recorte_todos_anos.groupby(["uf", "ano"], as_index=False)["renda_sm"].median()
        evolucao["ano"] = evolucao["ano"].astype(str)
        ordem_uf = evolucao[evolucao["ano"] == "2022"].sort_values("renda_sm", ascending=False)["uf"].tolist()
        comparacao = px.bar(evolucao, x="uf", y="renda_sm", color="ano", barmode="group",
                            category_orders={"uf": ordem_uf, "ano": ["2010", "2022"]},
                            color_discrete_map={"2010": COR_ANO[2010], "2022": COR_ANO[2022]},
                            labels={"uf": "UF", "renda_sm": "Mediana municipal (SM)", "ano": "Ano"})
        st.plotly_chart(comparacao, width="stretch")

        resumo = recorte_todos_anos.groupby("ano")["renda_rs"].agg(["mean", "median"])
        resumo_sm = recorte_todos_anos.groupby("ano")["renda_sm"].agg(["mean", "median"])
        c1, c2 = st.columns(2)
        c1.metric("Mediana municipal 2022 (R$)", reais(resumo.loc[2022, "median"]),
                  f"{(resumo.loc[2022, 'median'] / resumo.loc[2010, 'median'] - 1) * 100:.0f}% desde 2010")
        c2.metric("Mediana municipal 2022 (SM)", numero(resumo_sm.loc[2022, "median"], 2) + " SM",
                  f"{resumo_sm.loc[2022, 'median'] - resumo_sm.loc[2010, 'median']:+.2f} SM desde 2010".replace(".", ","))

with abas[3]:
    mediana_regiao = dados.groupby("regiao")[coluna].median()
    regiao_baixa = mediana_regiao.idxmin()
    regiao_alta = mediana_regiao.idxmax()
    uf_alta = por_uf.iloc[0]
    uf_baixa = por_uf.iloc[-1]
    ate_1sm = (dados["renda_sm"] <= 1).mean() * 100
    ate_2sm = (dados["renda_sm"] <= 2).mean() * 100
    maior = dados.loc[dados[coluna].idxmax()]
    menor = dados.loc[dados[coluna].idxmin()]
    outliers_grandes = (acima["populacao_municipio"] > 100000).sum()
    outliers_pequenos = (acima["populacao_municipio"] <= 20000).sum()
    lado = "acima" if est["media"] >= est["mediana"] else "abaixo"
    aviso_df = ""
    if uf_alta["municipios"] == 1:
        aviso_df = " (mas ali só existe um município, então a comparação é com uma cidade inteira)"

    st.markdown(f"""
#### 1. Qual é a renda típica do responsável pelo domicílio?
A mediana é **{formatar(est['mediana'])}**: metade dos municípios do recorte fica abaixo desse valor.
A média dos municípios ({formatar(est['media'])}) fica um pouco {lado} da mediana, puxada pelos outliers.
A diferença grande aparece quando cada casa conta uma vez: a **média por domicílio é {formatar(media_ponderada)}**,
bem acima da mediana, porque as cidades grandes têm mais gente e renda mais alta.
Ou seja, a "renda média" que sai no jornal descreve mais as cidades grandes do que o município típico.
A faixa mais comum (moda) é **{est['moda']}**, e em {numero(ate_2sm, 1)}% dos municípios
a renda média do responsável não passa de 2 salários mínimos ({numero(ate_1sm, 1)}% não passam de 1 SM).

#### 2. Quais municípios fogem do padrão?
Pela regra de 1,5 × IQR, **{len(acima)} municípios** estão acima de {formatar(est['lim_sup'])}. Eles formam dois grupos:
- **{outliers_grandes} cidades com mais de 100 mil habitantes**: capitais e cidades ricas das regiões metropolitanas,
  onde a renda alta está concentrada.
- **{outliers_pequenos} municípios com até 20 mil habitantes**: como têm poucas casas, algumas famílias de renda alta
  já mudam a média do município inteiro. Esses valores pedem cautela.

O maior valor é {maior['municipio']} ({maior['uf']}, {numero(maior['populacao_municipio'])} habitantes),
com {formatar(maior[coluna])}, e o menor é {menor['municipio']} ({menor['uf']}), com {formatar(menor[coluna])}.
A amplitude entre os dois é de {formatar(est['amplitude'])}.

#### 3. Quão desigual é a renda entre os territórios?
O desvio padrão é {formatar(est['desvio'])} e o coeficiente de variação é {numero(est['cv'], 1)}%:
a renda dos municípios varia bastante em volta da média.
A metade central dos municípios (entre Q1 e Q3) vai de {formatar(est['q1'])} a {formatar(est['q3'])}.
Na comparação por UF, {uf_alta['uf']} tem a maior mediana ({formatar(uf_alta['mediana'])}){aviso_df}
e {uf_baixa['uf']} a menor ({formatar(uf_baixa['mediana'])}).
Por região, a mediana dos municípios é mais baixa no **{regiao_baixa}** ({formatar(mediana_regiao[regiao_baixa])})
e mais alta no **{regiao_alta}** ({formatar(mediana_regiao[regiao_alta])}).

#### 4. O que isso significa para os gestores?
- Usar a **mediana**, e não a média, para definir metas e públicos de programas de renda.
- Priorizar os municípios abaixo do Q1 ({formatar(est['q1'])}), que são o quarto mais pobre do recorte.
- Tratar os outliers como casos à parte: eles distorcem a média estadual e escondem a pobreza dos municípios menores.
""")
    st.caption("Os números deste texto mudam sozinhos conforme os filtros da barra lateral.")

with abas[4]:
    noticias = [
        ("Municípios nordestinos têm a menor renda vinda do trabalho, aponta o Censo",
         "Movimento Econômico · 09/10/2025",
         "Com os dados de trabalho e rendimento do Censo 2022, a matéria mostra que o Nordeste concentra "
         "os municípios de menor renda e que em 520 cidades a renda média do trabalho não chegava a um salário mínimo.",
         "https://movimentoeconomico.com.br/censo/2025/10/09/ibge-municipios-nordestinos-tem-menor-renda-vinda-do-trabalho/"),
        ("IBGE: 9,3% dos municípios têm renda do trabalho inferior a um salário mínimo",
         "A Tarde · 09/10/2025",
         "Segundo o Censo 2022, 35,3% dos trabalhadores do país recebiam até um salário mínimo, "
         "e a diferença entre regiões e grupos de cor ou raça continua grande.",
         "https://atarde.com.br/economia/ibge-93-dos-municipios-tem-renda-inferior-a-um-salario-minimo-1363891"),
        ("DF tem a maior renda e a maior desigualdade do país",
         "Correio Braziliense · 10/10/2025",
         "A renda domiciliar por pessoa foi de R$ 900 no Maranhão a quase R$ 3 mil no Distrito Federal, "
         "que também teve o maior índice de Gini entre as UFs.",
         "https://www.correiobraziliense.com.br/economia/2025/10/7267370-ibge-df-tem-as-maiores-renda-e-desigualdade-do-pais.html"),
        ("Censo mostra renda menor entre indígenas e nas regiões Norte e Nordeste",
         "O Imparcial · 10/2025",
         "Cerca de 41% dos indígenas viviam com menos de 1/4 de salário mínimo por pessoa, "
         "contra 13,3% da população em geral.",
         "https://oimparcial.com.br/brasil/2025/10/censo-mostra-renda-menor-de-indigenas-e-nas-regioes-norte-e-nordeste-maranhao-aparece-5-vezes-na-lista/"),
    ]
    col_noticias, col_imagens = st.columns([3, 2])
    with col_noticias:
        st.subheader("Na imprensa")
        for titulo, fonte, resumo, link in noticias:
            with st.container(border=True):
                st.markdown(f"**[{titulo}]({link})**")
                st.caption(fonte)
                st.write(resumo)
        st.markdown("Publicação oficial: [IBGE, Censo 2022 – Trabalho e rendimento]"
                    "(https://biblioteca.ibge.gov.br/visualizacao/livros/liv102211.pdf)")
    with col_imagens:
        st.subheader("Para entender")
        st.image(str(PASTA / "imagens" / "media_x_mediana.png"),
                 caption="Um único valor muito alto muda a média, mas quase não mexe na mediana.")
        st.image(str(PASTA / "imagens" / "como_ler_boxplot.png"),
                 caption="Como ler o boxplot usado neste painel.")

with abas[5]:
    st.markdown(f"""
**Fonte:** IBGE, Censo Demográfico 2010 e 2022, Agregados por Setores Censitários
(variável V06004 em 2022 e V007 em 2010: rendimento nominal médio mensal das pessoas responsáveis
com rendimento, em domicílios particulares permanentes).

**Como a base foi tratada (ETL):**
1. Leitura dos dados de cada setor censitário (pedaços de bairro com cerca de 200 domicílios).
2. Retirada dos setores sem renda informada (o IBGE esconde valores de setores muito pequenos).
3. Junção dos setores de cada município numa **média ponderada** pelo número de responsáveis,
   separando a parte urbana da rural.
4. Inclusão da população e do porte de cada município.

**Cuidados:**
- Valores nominais, ou seja, sem correção pela inflação. Para comparar anos, use salários mínimos.
- A unidade analisada é o **município**: as estatísticas descrevem como a renda varia entre cidades,
  não entre pessoas.
- O Censo por setor não separa a renda por sexo nem por faixa etária do responsável.
  Por isso os recortes da barra lateral são região, UF, situação urbana ou rural e porte do município.
""")
    st.download_button("Baixar os dados filtrados (CSV)",
                       dados.drop(columns=["faixa"]).to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"rendimento_responsaveis_{ano}_filtrado.csv", mime="text/csv")
