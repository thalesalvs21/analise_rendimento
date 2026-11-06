# Rendimento dos Responsáveis pelo Domicílio (IBGE)

Parte individual do Projeto Integrado Python/Matemática "Números que Falam", **indicador 5**.

**Aluno:** Thales Alves Gomes

Dashboard em Streamlit com a renda média do responsável pelo domicílio em cada município do Brasil,
segundo o Censo 2010 e o Censo 2022. Mostra média, mediana, moda, quartis, IQR, amplitude, variância,
desvio padrão e outliers (regra de 1,5 × IQR).

## Arquivos
- `app.py`: o dashboard (upload, filtros, indicadores, gráficos, notícias)
- `etl_rendimento.py`: baixa os dados do IBGE e gera a base tratada
- `dados/rendimento_responsaveis.csv`: base tratada (um registro por município, ano e situação urbana/rural)
- `analise_descritiva.md`: interpretação dos resultados
- `gerar_imagens.py` e `imagens/`: imagens ilustrativas da seção de notícias

## Como rodar
```
pip install -r requirements.txt
streamlit run app.py
```

A base tratada já vem pronta. Para gerar de novo a partir dos dados brutos, rode `python etl_rendimento.py`.

## Fonte
IBGE, Censo Demográfico 2010 e 2022, Agregados por Setores Censitários
(V06004 em 2022 e V007 em 2010). Arquivos brutos obtidos pela cópia em parquet do IPEA (pacote censobr).
