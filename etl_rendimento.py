import os
import urllib.request
import pandas as pd

PASTA_BRUTOS = "dados/brutos"
ARQUIVO_FINAL = "dados/rendimento_responsaveis.csv"
LINK = "https://github.com/ipea/censobr_prep_data/releases/download/v1.0.0/"

ARQUIVOS = [
    "2022_tracts_ResponsavelRenda_v1.0.0.parquet",
    "2022_tracts_Basico_v1.0.0.parquet",
    "2010_tracts_Basico_v1.0.0.parquet",
]

SIGLAS = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL", 28: "SE", 29: "BA",
    31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS",
    50: "MS", 51: "MT", 52: "GO", 53: "DF",
}


def baixar_brutos():
    os.makedirs(PASTA_BRUTOS, exist_ok=True)
    for nome in ARQUIVOS:
        caminho = os.path.join(PASTA_BRUTOS, nome)
        if not os.path.exists(caminho):
            print("baixando", nome)
            urllib.request.urlretrieve(LINK + nome, caminho)


def porte(pop):
    if pop <= 20000:
        return "Até 20 mil hab."
    if pop <= 100000:
        return "20 mil a 100 mil hab."
    if pop <= 500000:
        return "100 mil a 500 mil hab."
    return "Mais de 500 mil hab."


def agrupar(setores, ano, pop_municipio):
    setores = setores.dropna(subset=["renda", "responsaveis"])
    setores = setores[setores["responsaveis"] > 0].copy()

    setores["renda_x_resp"] = setores["renda"] * setores["responsaveis"]

    grupo = setores.groupby(["regiao", "uf", "cod_municipio", "municipio", "situacao"], as_index=False)
    tabela = grupo[["renda_x_resp", "responsaveis"]].sum()
    tabela["renda_media"] = (tabela["renda_x_resp"] / tabela["responsaveis"]).round(2)
    tabela = tabela.drop(columns="renda_x_resp")

    tabela = tabela.merge(pop_municipio, on="cod_municipio", how="left")
    tabela["porte"] = tabela["populacao_municipio"].apply(porte)
    tabela.insert(0, "ano", ano)
    return tabela


baixar_brutos()

renda22 = pd.read_parquet(os.path.join(PASTA_BRUTOS, ARQUIVOS[0]))
basico22 = pd.read_parquet(os.path.join(PASTA_BRUTOS, ARQUIVOS[1]))

setores22 = pd.DataFrame({
    "regiao": renda22["name_region"].astype(str),
    "uf": renda22["code_state"].astype(int).map(SIGLAS),
    "cod_municipio": renda22["code_muni"].astype(int),
    "municipio": renda22["name_muni"].astype(str),
    "situacao": renda22["situacao"].astype(str),
    "responsaveis": pd.to_numeric(renda22["V06001"], errors="coerce"),
    "renda": pd.to_numeric(renda22["V06004"], errors="coerce"),
})
pop22 = basico22.groupby("code_muni", as_index=False)["V0001"].sum()
pop22.columns = ["cod_municipio", "populacao_municipio"]
pop22["cod_municipio"] = pop22["cod_municipio"].astype(int)

basico10 = pd.read_parquet(os.path.join(PASTA_BRUTOS, ARQUIVOS[2]))
basico10 = basico10.dropna(subset=["code_muni"])

setores10 = pd.DataFrame({
    "regiao": basico10["name_region"].astype(str),
    "uf": basico10["abbrev_state"].astype(str),
    "cod_municipio": basico10["code_muni"].astype(int),
    "municipio": basico10["name_muni"].astype(str),
    "situacao": basico10["Situacao_setor"].astype(int).apply(lambda s: "Urbana" if s <= 3 else "Rural"),
    "responsaveis": pd.to_numeric(basico10["V001"], errors="coerce"),
    "renda": pd.to_numeric(basico10["V007"], errors="coerce"),
})
pop10 = basico10.groupby("code_muni", as_index=False)["V002"].sum()
pop10.columns = ["cod_municipio", "populacao_municipio"]
pop10["cod_municipio"] = pop10["cod_municipio"].astype(int)

final = pd.concat([agrupar(setores10, 2010, pop10), agrupar(setores22, 2022, pop22)])

nomes22 = setores22.drop_duplicates("cod_municipio").set_index("cod_municipio")["municipio"]
final["municipio"] = final["cod_municipio"].map(nomes22).fillna(final["municipio"].str.title())
final["responsaveis"] = final["responsaveis"].astype(int)
final["populacao_municipio"] = final["populacao_municipio"].astype(int)

os.makedirs("dados", exist_ok=True)
final.to_csv(ARQUIVO_FINAL, index=False, encoding="utf-8-sig")
print("pronto:", ARQUIVO_FINAL, final.shape)
