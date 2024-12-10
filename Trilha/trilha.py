import pandas as pd
import numpy as np
import os
import streamlit as st

# ========== PARTE DE PROCESSAMENTO DE DADOS ==========

# Ajustar caminhos conforme sua necessidade
folder_path_vendas = './Vendas/'
files_vendas = os.listdir(folder_path_vendas)

all_dataframes_vendas = []
for file in files_vendas:
    file_path_vendas = os.path.join(folder_path_vendas, file)
    try:
        df_vendas = pd.read_excel(file_path_vendas, usecols=["CÓDIGO PEDIDO", "MARKETPLACE", "STATUS", "VALOR TOTAL DOS PRODUTOS"])
        df_vendas["CÓDIGO PEDIDO"] = df_vendas["CÓDIGO PEDIDO"].astype(str)
        df_vendas["MARKETPLACE"] = df_vendas["MARKETPLACE"].astype(str)
        df_vendas["STATUS"] = df_vendas["STATUS"].astype(str)
        all_dataframes_vendas.append(df_vendas)
    except Exception as e:
        print(f"Erro ao ler o arquivo {file}: {e}")

if all_dataframes_vendas:
    combined_df_vendas = pd.concat(all_dataframes_vendas, ignore_index=True)
    combined_df_vendas = combined_df_vendas.drop_duplicates(subset="CÓDIGO PEDIDO", keep="first")
    combined_df_vendas = combined_df_vendas.fillna(0)
else:
    combined_df_vendas = pd.DataFrame(columns=["CÓDIGO PEDIDO", "MARKETPLACE", "STATUS", "VALOR TOTAL DOS PRODUTOS"])

folder_path_centauro = './Repasse Centauro/'
files_centauro = os.listdir(folder_path_centauro)

all_dataframes_centauro = []
for file in files_centauro:
    file_path_centauro = os.path.join(folder_path_centauro, file)
    try:
        df_centauro = pd.read_csv(file_path_centauro, sep=';', usecols=["DataPedido", "Pedido", "StatusAtendimento", "Protocolo", "ValorPedido", "ValorFrete", "Comissao", "RepasseLiquido"])
        df_centauro.rename(columns={"Pedido": "CÓDIGO PEDIDO"}, inplace=True)
        df_centauro["CÓDIGO PEDIDO"] = df_centauro["CÓDIGO PEDIDO"].astype(str)
        df_centauro["StatusAtendimento"] = df_centauro["StatusAtendimento"].astype(str)

        df_centauro['ValorPedido'] = df_centauro['ValorPedido'].astype(str).replace('-', np.nan).str.replace(',', '.').astype(float)
        df_centauro['ValorFrete'] = df_centauro['ValorFrete'].astype(str).replace('-', np.nan).str.replace(',', '.').astype(float)
        df_centauro['Comissao'] = df_centauro['Comissao'].astype(str).replace('-', np.nan).str.replace(',', '.').astype(float)
        df_centauro['RepasseLiquido'] = df_centauro['RepasseLiquido'].astype(str).replace('-', np.nan).str.replace(',', '.').astype(float)

        all_dataframes_centauro.append(df_centauro)

    except Exception as e:
        print(f"Erro ao ler o arquivo {file}: {e}")

if all_dataframes_centauro:
    combined_df_centauro = pd.concat(all_dataframes_centauro, ignore_index=True)
    combined_df_centauro = combined_df_centauro.fillna(0)
else:
    combined_df_centauro = pd.DataFrame(columns=["CÓDIGO PEDIDO", "StatusAtendimento", "ValorPedido", "ValorFrete", "Comissao", "RepasseLiquido"])

folder_path_netshoes_ns2 = './Repasse Netshoes/NS2/'
files_netshoes_ns2 = os.listdir(folder_path_netshoes_ns2)

all_dataframes_netshoes_ns2 = []
for file in files_netshoes_ns2:
    file_path_netshoes_ns2 = os.path.join(folder_path_netshoes_ns2, file)
    try:
        df_netshoes_ns2 = pd.read_excel(file_path_netshoes_ns2, skiprows=7, usecols=["Nr Pedido Netshoes", "Valor Total Produtos Lojista", "Valor Repasse", "Status Pedido"])
        df_netshoes_ns2.rename(columns={"Nr Pedido Netshoes": "CÓDIGO PEDIDO"}, inplace=True)
        df_netshoes_ns2["CÓDIGO PEDIDO"] = df_netshoes_ns2["CÓDIGO PEDIDO"].astype(str)

        # Limpeza de Valor Repasse
        df_netshoes_ns2["Valor Repasse"] = (
            df_netshoes_ns2["Valor Repasse"]
            .astype(str)
            .str.replace(r'R\$', '', regex=True)
            .str.replace(' ', '', regex=False)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
            .astype(float)
        )

        df_netshoes_ns2["Valor Total Produtos Lojista"] = (
            df_netshoes_ns2["Valor Total Produtos Lojista"]
            .astype(str)
            .str.replace(r'R\$', '', regex=True)
            .str.replace(' ', '', regex=False)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
            .astype(float)
        )

        all_dataframes_netshoes_ns2.append(df_netshoes_ns2)
    except Exception as e:
        print(f"Erro ao ler o arquivo {file}: {e}")

if all_dataframes_netshoes_ns2:
    combined_df_netshoes_ns2 = pd.concat(all_dataframes_netshoes_ns2, ignore_index=True)
    combined_df_netshoes_ns2 = combined_df_netshoes_ns2.fillna(0)
else:
    combined_df_netshoes_ns2 = pd.DataFrame(columns=["CÓDIGO PEDIDO", "Valor Total Produtos Lojista", "Valor Repasse", "Status Pedido"])

folder_path_netshoes_magalu = './Repasse Netshoes/Magalu Pagamentos/'
files_netshoes_magalu = os.listdir(folder_path_netshoes_magalu)

all_dataframes_netshoes_magalu = []
for file in files_netshoes_magalu:
    file_path_netshoes_magalu = os.path.join(folder_path_netshoes_magalu, file)
    try:
        df_netshoes_magalu = pd.read_excel(file_path_netshoes_magalu, usecols=["ID do pedido Netshoes", "Valor bruto seller"])
        df_netshoes_magalu.rename(columns={"ID do pedido Netshoes": "CÓDIGO PEDIDO"}, inplace=True)
        df_netshoes_magalu["CÓDIGO PEDIDO"] = df_netshoes_magalu["CÓDIGO PEDIDO"].astype(str)
        df_netshoes_magalu["Valor bruto seller"] = df_netshoes_magalu["Valor bruto seller"].astype(float)
        all_dataframes_netshoes_magalu.append(df_netshoes_magalu)
    except Exception as e:
        print(f"Erro ao ler o arquivo {file}: {e}")

if all_dataframes_netshoes_magalu:
    combined_df_netshoes_magalu = pd.concat(all_dataframes_netshoes_magalu, ignore_index=True)
    combined_df_netshoes_magalu = combined_df_netshoes_magalu.drop_duplicates(subset="CÓDIGO PEDIDO", keep="first")
    combined_df_netshoes_magalu = combined_df_netshoes_magalu.fillna(0)
else:
    combined_df_netshoes_magalu = pd.DataFrame(columns=["CÓDIGO PEDIDO", "Valor bruto seller"])

# Agora juntamos os dados em um único DataFrame de referência.
# Começaremos com as vendas e faremos merges com as outras tabelas.

final_df = combined_df_vendas.copy()

# Merge com Centauro (Exemplo)
final_df = pd.merge(final_df, combined_df_centauro[["CÓDIGO PEDIDO","ValorPedido","Comissao","RepasseLiquido","StatusAtendimento"]], on="CÓDIGO PEDIDO", how="left")

# Merge com Netshoes NS2
final_df = pd.merge(final_df, combined_df_netshoes_ns2[["CÓDIGO PEDIDO","Valor Total Produtos Lojista","Valor Repasse","Status Pedido"]], on="CÓDIGO PEDIDO", how="left")

# Merge com Netshoes Magalu
final_df = pd.merge(final_df, combined_df_netshoes_magalu[["CÓDIGO PEDIDO","Valor bruto seller"]], on="CÓDIGO PEDIDO", how="left")

# Tratando colunas: Vamos consolidar o Valor Pedido. Caso não tenha em Centauro, usar o da venda.
final_df["Valor Pedido Consolidado"] = final_df["VALOR TOTAL DOS PRODUTOS"]
final_df.loc[final_df["ValorPedido"].notna(), "Valor Pedido Consolidado"] = final_df["ValorPedido"]

# Definir Valor Esperado = Valor Pedido Consolidado - Comissão (quando disponível)
final_df["Valor Esperado"] = final_df["Valor Pedido Consolidado"] - final_df["Comissao"].fillna(0)

# Valor Recebido: Podemos priorizar RepasseLiquido se existir, senão Valor Repasse (Netshoes NS2), senão Valor bruto seller (Magalu)
final_df["Valor Recebido"] = np.nan
final_df.loc[final_df["RepasseLiquido"].notna(), "Valor Recebido"] = final_df["RepasseLiquido"]
final_df.loc[final_df["Valor Recebido"].isna() & final_df["Valor Repasse"].notna(), "Valor Recebido"] = final_df["Valor Repasse"]
final_df.loc[final_df["Valor Recebido"].isna() & final_df["Valor bruto seller"].notna(), "Valor Recebido"] = final_df["Valor bruto seller"]

# Diferença entre Valor Recebido e Valor Esperado
final_df["Diferença"] = final_df["Valor Recebido"] - final_df["Valor Esperado"]

# Coluna Conciliado
final_df["Conciliado"] = final_df["Diferença"].apply(lambda x: "OK" if abs(x) < 0.01 else "Divergente")

# Possível motivo (simples - você pode aprimorar conforme sua lógica)
final_df["Possível Motivo"] = np.where(
    final_df["Conciliado"] == "Divergente",
    "Verificar descontos adicionais, devoluções ou frete reverso",
    "Nenhum"
)

# Verificar se desconto foi aplicado mais de uma vez: Contar quantas entradas por CÓDIGO PEDIDO
counts_pedido = final_df["CÓDIGO PEDIDO"].value_counts()
final_df["Desconto_Múltiplo"] = final_df["CÓDIGO PEDIDO"].apply(lambda x: "Sim" if counts_pedido[x] > 1 else "Não")

# Se tiver Devolução (STATUS = "Devolvido" por ex.) e não há diferença, pode ser falha
final_df["Erro_Nao_Devolucao"] = np.where(
    (final_df["STATUS"].str.contains("Devolvido", case=False, na=False)) & (final_df["Conciliado"] == "OK"),
    "Possível falha: Não houve desconto de devolução",
    ""
)

# Cálculo de Desconto_Frete_Reverso (exemplo simplificado)
final_df["Desconto_Frete_Reverso"] = final_df["Valor Pedido Consolidado"] - final_df["Valor Recebido"]

# ========== PARTE DE INTERFACE COM STREAMLIT ==========

st.title("Painel de Repasses e Vendas")

st.write("Este painel permite filtrar, pesquisar e verificar divergências nos repasses.")

# Filtros
marketplaces = final_df["MARKETPLACE"].dropna().unique().tolist()
status_vendas = final_df["STATUS"].dropna().unique().tolist()

selected_marketplace = st.multiselect("Selecione Marketplace:", marketplaces, default=marketplaces)
selected_status = st.multiselect("Selecione Status da Venda:", status_vendas, default=status_vendas)

valor_min = st.number_input("Valor Mínimo do Pedido:", value=0.0)
valor_max = st.number_input("Valor Máximo do Pedido:", value=float(final_df["Valor Pedido Consolidado"].max() if not final_df.empty else 0))

codigo_pedido_input = st.text_input("Pesquisar por CÓDIGO PEDIDO:")

df_filtrado = final_df.copy()

if selected_marketplace:
    df_filtrado = df_filtrado[df_filtrado["MARKETPLACE"].isin(selected_marketplace)]

if selected_status:
    df_filtrado = df_filtrado[df_filtrado["STATUS"].isin(selected_status)]

df_filtrado = df_filtrado[(df_filtrado["Valor Pedido Consolidado"] >= valor_min) & (df_filtrado["Valor Pedido Consolidado"] <= valor_max)]

if codigo_pedido_input:
    df_filtrado = df_filtrado[df_filtrado["CÓDIGO PEDIDO"].str.contains(codigo_pedido_input, case=False, na=False)]

# Destaque de divergentes
def highlight_differences(row):
    if row['Conciliado'] == 'Divergente':
        return ['background-color: #ffa07a']*len(row)
    else:
        return ['']*len(row)

st.dataframe(df_filtrado.style.apply(highlight_differences, axis=1))

st.write("Linhas marcadas em cor são divergências detectadas.")
st.write("Possíveis Motivos:", df_filtrado["Possível Motivo"].unique().tolist())
