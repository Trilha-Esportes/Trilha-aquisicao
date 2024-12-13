import pandas as pd
import numpy as np
import os
import streamlit as st
from datetime import datetime

# ========== CONFIGURAÇÕES INICIAIS ==========
st.set_page_config(page_title="📊 Painel de Repasses e Vendas", layout="wide")

# Título da aplicação
st.title("📊 Painel de Repasses e Vendas")
st.markdown("Este painel permite filtrar, pesquisar e verificar divergências nos repasses de vendas.")

# ========== MAPA DE CÓDIGOS DE ERRO ==========
ERRO_MAP = {
    "Leitura_Erro": 1001,          # Erro ao ler o arquivo
    "Conversao_Tipo": 1002,        # Erro na conversão de tipo de dados
    "Valor_Nulo": 1003,            # Valor nulo inesperado
    "Divergencia": 1004,           # Divergência encontrada durante a conciliação
    "Falha_Consolidacao": 1005     # Falha na consolidação dos dados
}

# Inicializar lista para coletar erros
if 'lista_erros' not in st.session_state:
    st.session_state.lista_erros = []

# Função para registrar erros
def registrar_erro(arquivo, tipo_erro, mensagem):
    novo_log = {
        "Timestamp": datetime.now(),
        "Arquivo": arquivo,
        "Codigo_Erro": ERRO_MAP.get(tipo_erro, 9999),
        "Mensagem_Erro": mensagem
    }
    st.session_state.lista_erros.append(novo_log)

# ========== FUNÇÕES DE CONVERSÃO ==========
def convert_to_float(x):
    x = str(x).strip()
    if '.' in x and ',' in x:
        # Assume que '.' é separador de milhares e ',' é decimal
        x = x.replace('.', '').replace(',', '.')
    elif ',' in x:
        # Assume que ',' é separador decimal
        x = x.replace(',', '.')
    # Se apenas '.' está presente, assume que é separador decimal
    try:
        return float(x)
    except ValueError:
        # Retorna NaN se a conversão falhar
        return np.nan

def convert_to_date(x, dayfirst=True):
    """
    Converte uma data para o formato AAAAMMDD.

    Parâmetros:
    - x: valor da data.
    - dayfirst: booleano que indica se o primeiro elemento é o dia.

    Retorna:
    - String no formato AAAAMMDD ou NaN se a conversão falhar.
    """
    if pd.isnull(x):
        return np.nan
    try:
        # Tenta converter a string para datetime com a configuração de dayfirst
        parsed_date = pd.to_datetime(x, dayfirst=dayfirst, errors='coerce')
        if pd.isnull(parsed_date):
            return np.nan
        return parsed_date.strftime('%Y%m%d')  # Formato AAAAMMDD
    except Exception as e:
        registrar_erro("Conversao_Data", "Conversao_Tipo", f"Erro ao converter a data {x}: {e}")
        return np.nan

# ========== FUNÇÕES DE PROCESSAMENTO DE DADOS ==========
def processar_vendas(file_path):
    try:
        df = pd.read_excel(
            file_path,
            usecols=[
                "CÓDIGO PEDIDO", 
                "DATA PEDIDO", 
                "MARKETPLACE", 
                "STATUS", 
                "FRETE DO LOJISTA", 
                "FRETE", 
                "VALOR TOTAL DOS PRODUTOS", 
                "TOTAL DO PEDIDO"
            ]
        )
        
        # Garantir que as colunas categóricas sejam do tipo string
        df["CÓDIGO PEDIDO"] = df["CÓDIGO PEDIDO"].astype(str)
        df["MARKETPLACE"] = df["MARKETPLACE"].astype(str)
        df["STATUS"] = df["STATUS"].astype(str)
        
        # Aplicando a função de conversão personalizada para números
        df["FRETE"] = df["FRETE"].apply(convert_to_float)
        df["FRETE DO LOJISTA"] = df["FRETE DO LOJISTA"].apply(convert_to_float)
        df["VALOR TOTAL DOS PRODUTOS"] = df["VALOR TOTAL DOS PRODUTOS"].apply(convert_to_float)
        df["TOTAL DO PEDIDO"] = df["TOTAL DO PEDIDO"].apply(convert_to_float)
        
        # Criando a coluna "FRETE TOTAL" somando "FRETE" e "FRETE DO LOJISTA"
        df["FRETE TOTAL"] = df["FRETE"].fillna(0) + df["FRETE DO LOJISTA"].fillna(0)
        
        # Remover as colunas originais de frete
        df = df.drop(columns=["FRETE", "FRETE DO LOJISTA"])
        
        # Aplicando a função de conversão para datas com dayfirst=True
        df["DATA PEDIDO"] = df["DATA PEDIDO"].apply(lambda x: convert_to_date(x, dayfirst=True))
        
        # Criando a coluna "VALOR ESPERADO" = "TOTAL DO PEDIDO" - "FRETE TOTAL"
        df["VALOR ESPERADO"] = df["TOTAL DO PEDIDO"] - df["FRETE TOTAL"]
        
        # Remover duplicatas em Vendas: manter apenas uma ocorrência por "CÓDIGO PEDIDO" e "VALOR ESPERADO"
        df = df.drop_duplicates(subset=["CÓDIGO PEDIDO", "VALOR ESPERADO"], keep='first')
        
        return df
    except Exception as e:
        registrar_erro(os.path.basename(file_path), "Leitura_Erro", str(e))
        return pd.DataFrame()

def processar_centauro(file_path):
    try:
        df = pd.read_csv(
            file_path, 
            sep=';', 
            usecols=["Pedido", "DataPedido", "StatusAtendimento", "ValorPedido", "ValorFrete", "Comissao", "RepasseLiquido"]
        )
        
        # Renomeando as colunas para padronizar com 'vendas'
        df.rename(columns={
            "Pedido": "CÓDIGO PEDIDO",
            "DataPedido": "DATA PEDIDO",
            "StatusAtendimento": "STATUS",
            "ValorPedido": "TOTAL DO PEDIDO",
            "ValorFrete": "FRETE TOTAL",
            "Comissao": "COMISSAO",
            "RepasseLiquido": "VALOR TOTAL DOS PRODUTOS"
        }, inplace=True)
        
        # Garantir que as colunas categóricas sejam do tipo string
        df["CÓDIGO PEDIDO"] = df["CÓDIGO PEDIDO"].astype(str)
        df["STATUS"] = df["STATUS"].astype(str)
        
        # Aplicando a função de conversão para datas com dayfirst=False
        df["DATA PEDIDO"] = df["DATA PEDIDO"].apply(lambda x: convert_to_date(x, dayfirst=False))
        
        # Aplicando a função de conversão personalizada para números
        numeric_cols = ["VALOR TOTAL DOS PRODUTOS", "FRETE TOTAL", "COMISSAO", "TOTAL DO PEDIDO"]
        for col in numeric_cols:
            df[col] = df[col].apply(convert_to_float)
        
        # Adicionar coluna "Tipo" com base no valor
        df["Tipo"] = df["VALOR TOTAL DOS PRODUTOS"].apply(lambda x: "Extorno" if x < 0 else "Produto")
        
        # Garantir que 'STATUS' exista
        if 'STATUS' not in df.columns:
            df['STATUS'] = "Não informado"
        else:
            df['STATUS'] = df['STATUS'].fillna("Não informado")
        
        return df
    except Exception as e:
        registrar_erro(os.path.basename(file_path), "Leitura_Erro", str(e))
        return pd.DataFrame()

def processar_netshoes_ns2(file_path):
    try:
        df = pd.read_excel(
            file_path, 
            skiprows=7, 
            usecols=[
                "Nr Pedido Netshoes", 
                "Data da Compra", 
                "Valor Total Frete Lojista", 
                "Valor Total Produtos Lojista", 
                "Valor Total Pedido Lojista", 
                "Tipo do Pedido", 
                "Tarifa fixa por pedido"
            ]
        )
        
        # Renomeando as colunas para padronizar com 'vendas'
        df.rename(columns={
            "Nr Pedido Netshoes": "CÓDIGO PEDIDO",
            "Valor Total Pedido Lojista": "TOTAL DO PEDIDO",
            "Data da Compra": "DATA PEDIDO",
            "Valor Total Frete Lojista": "FRETE TOTAL",
            "Valor Total Produtos Lojista": "VALOR TOTAL DOS PRODUTOS",
            "Tipo do Pedido": "STATUS",
            "Tarifa fixa por pedido": "FRETE FIXO"
        }, inplace=True)
        
        # Garantir que 'STATUS' exista
        if 'STATUS' not in df.columns:
            df['STATUS'] = "Não informado"
        else:
            df['STATUS'] = df['STATUS'].fillna("Não informado")
        
        # Aplicando a função de conversão personalizada para números
        monetary_columns = ["VALOR TOTAL DOS PRODUTOS", "FRETE TOTAL", "COMISSAO", "TOTAL DO PEDIDO", "FRETE FIXO"]
        for col in monetary_columns:
            if col in df.columns:
                df[col] = df[col].apply(convert_to_float)
        
        # Adicionar "FRETE FIXO" à "COMISSAO"
        if "COMISSAO" in df.columns and "FRETE FIXO" in df.columns:
            df["COMISSAO"] += df["FRETE FIXO"].fillna(0)
        
        # Remover a coluna "FRETE FIXO"
        if "FRETE FIXO" in df.columns:
            df = df.drop(columns=["FRETE FIXO"])
        
        # Adicionar coluna "Tipo" com base no valor
        df["Tipo"] = df["VALOR TOTAL DOS PRODUTOS"].apply(lambda x: "Extorno" if x < 0 else "Produto")
        
        return df
    except Exception as e:
        registrar_erro(os.path.basename(file_path), "Leitura_Erro", str(e))
        return pd.DataFrame()

def processar_netshoes_magalu(file_path):
    try:
        df = pd.read_excel(
            file_path,
            usecols=[
                "ID do pedido Netshoes", 
                "Data do pedido", 
                "Valor bruto do pedido", 
                "Valor Serviços de Marketplace", 
                "Tarifa fixa por pedido"
            ]
        )
        
        # Renomeando as colunas para padronizar com 'vendas'
        df.rename(columns={
            "ID do pedido Netshoes": "CÓDIGO PEDIDO",
            "Data do pedido": "DATA PEDIDO",
            "Valor bruto do pedido": "VALOR TOTAL DOS PRODUTOS",
            "Valor Serviços de Marketplace": "COMISSAO",
            "Tarifa fixa por pedido": "FRETE FIXO"
        }, inplace=True)
        
        # Garantir que as colunas categóricas sejam do tipo string
        df["CÓDIGO PEDIDO"] = df["CÓDIGO PEDIDO"].astype(str)
        
        # Aplicando a função de conversão personalizada para números
        monetary_columns = ["VALOR TOTAL DOS PRODUTOS", "FRETE TOTAL", "COMISSAO", "FRETE FIXO"]
        for col in monetary_columns:
            if col in df.columns:
                df[col] = df[col].apply(convert_to_float)
        
        # Calculando a coluna "TOTAL DO PEDIDO"
        if "VALOR TOTAL DOS PRODUTOS" in df.columns and "FRETE TOTAL" not in df.columns:
            df["FRETE TOTAL"] = 0.0  # Assume que não há frete total se não estiver presente
        if "TOTAL DO PEDIDO" not in df.columns:
            df["TOTAL DO PEDIDO"] = df["VALOR TOTAL DOS PRODUTOS"] + df["FRETE TOTAL"]
        
        # Adicionar "FRETE FIXO" à "COMISSAO"
        if "COMISSAO" in df.columns and "FRETE FIXO" in df.columns:
            df["COMISSAO"] += df["FRETE FIXO"].fillna(0)
        
        # Remover a coluna "FRETE FIXO"
        if "FRETE FIXO" in df.columns:
            df = df.drop(columns=["FRETE FIXO"])
        
        # Aplicando a função de conversão para datas com dayfirst=True
        df["DATA PEDIDO"] = df["DATA PEDIDO"].apply(lambda x: convert_to_date(x, dayfirst=True))
        
        # Adicionar coluna "Tipo" com base no valor
        df["Tipo"] = df["VALOR TOTAL DOS PRODUTOS"].apply(lambda x: "Extorno" if x < 0 else "Produto")
        
        # Garantir que 'STATUS' exista
        if 'STATUS' not in df.columns:
            df['STATUS'] = "Não informado"
        else:
            df['STATUS'] = df['STATUS'].fillna("Não informado")
        
        return df
    except Exception as e:
        registrar_erro(os.path.basename(file_path), "Leitura_Erro", str(e))
        return pd.DataFrame()

# ========== FUNÇÃO DE CONCILIACAO ==========
def conciliar_dados(vendas, centauro, netshoes_ns2, netshoes_magalu):
    """
    Concilia os dados das diferentes fontes.

    Parâmetros:
    - vendas: DataFrame de Vendas
    - centauro: DataFrame de Centauro
    - netshoes_ns2: DataFrame de Netshoes NS2
    - netshoes_magalu: DataFrame de Netshoes Magalu

    Retorna:
    - DataFrame consolidado com conciliação e sinalização de divergências
    """
    # Criar um dicionário para armazenar os dados por "CÓDIGO PEDIDO"
    pedidos_dict = {}

    # Processar Vendas para obter "Valor Esperado"
    vendas_grouped = vendas.groupby("CÓDIGO PEDIDO").agg({
        "DATA PEDIDO": 'first',
        "MARKETPLACE": lambda x: ', '.join(x.dropna().unique()),
        "STATUS": lambda x: ', '.join(x.dropna().unique()),
        "VALOR ESPERADO": 'sum'
    }).reset_index()

    for _, row in vendas_grouped.iterrows():
        codigo = row["CÓDIGO PEDIDO"]
        pedidos_dict[codigo] = {
            "CÓDIGO PEDIDO": codigo,
            "DATA PEDIDO": row["DATA PEDIDO"],
            "MARKETPLACE": row["MARKETPLACE"],
            "STATUS": row["STATUS"],
            "Valor Esperado": row["VALOR ESPERADO"],
            "Valor Recebido": 0.0,  # Soma dos Produtos
            "Extorno": 0.0,         # Soma dos Extornos
            "Diferença": 0.0,
            "Conciliado": "OK",
            "Possível Motivo": "Nenhum",
            "Erro de Valor": "✅",
            "Outro Erro": "✅"
        }

    # Função para acumular valores recebidos e extornos
    def acumular_recebido_extorno(df, fonte):
        for _, row in df.iterrows():
            codigo = row["CÓDIGO PEDIDO"]
            valor = row.get("VALOR TOTAL DOS PRODUTOS", 0.0)
            tipo = row.get("Tipo", "Produto")
            if pd.isna(valor):
                valor = 0.0
            valor = float(valor)
            if codigo in pedidos_dict:
                if tipo == "Produto":
                    pedidos_dict[codigo]["Valor Recebido"] += valor
                elif tipo == "Extorno":
                    pedidos_dict[codigo]["Extorno"] += valor
            else:
                # Caso o pedido não esteja em vendas, adiciona com Valor Esperado = 0
                pedidos_dict[codigo] = {
                    "CÓDIGO PEDIDO": codigo,
                    "DATA PEDIDO": row.get("DATA PEDIDO", np.nan),
                    "MARKETPLACE": row.get("MARKETPLACE", ""),
                    "STATUS": row.get("STATUS", "Não informado"),
                    "Valor Esperado": 0.0,
                    "Valor Recebido": valor if tipo == "Produto" else 0.0,
                    "Extorno": valor if tipo == "Extorno" else 0.0,
                    "Diferença": 0.0,
                    "Conciliado": "Divergente",
                    "Possível Motivo": "Pedido não encontrado na planilha de vendas.",
                    "Erro de Valor": "❌",
                    "Outro Erro": "❌"
                }

    # Acumular valores de Centauro
    acumular_recebido_extorno(centauro, "Centauro")

    # Acumular valores de Netshoes NS2
    acumular_recebido_extorno(netshoes_ns2, "Netshoes NS2")

    # Acumular valores de Netshoes Magalu
    acumular_recebido_extorno(netshoes_magalu, "Netshoes Magalu")

    # Agora, calcular a diferença e conciliar
    for codigo, dados in pedidos_dict.items():
        dados["Diferença"] = dados["Valor Recebido"] - dados["Valor Esperado"]
        
        # Verificar Erro de Valor
        if abs(dados["Diferença"]) >= 0.01:
            dados["Erro de Valor"] = "❌"
            dados["Conciliado"] = "Divergente"
            dados["Possível Motivo"] = "Verificar discrepâncias no valor do pedido."
        else:
            dados["Erro de Valor"] = "✅"
        
        # Verificar se Extorno está balanceado
        if abs(dados["Extorno"]) >= 0.01:
            # Extorno deve balancear as devoluções
            # Aqui, você pode adicionar lógica adicional se houver requisitos específicos
            dados["Outro Erro"] = "❌"
            dados["Conciliado"] = "Divergente"
            if dados["Possível Motivo"] == "Nenhum":
                dados["Possível Motivo"] = "Verificar extornos do pedido."
        else:
            dados["Outro Erro"] = "✅"

    # Converter o dicionário para DataFrame
    final_df = pd.DataFrame.from_dict(pedidos_dict, orient='index').reset_index(drop=True)

    return final_df

# ========== FUNÇÃO DE CONCILIACAO FINAL ==========
def conciliar_e_calcular(vendas, centauro, netshoes_ns2, netshoes_magalu):
    final_df = conciliar_dados(vendas, centauro, netshoes_ns2, netshoes_magalu)
    return final_df

# ========== FUNÇÃO DE CARREGAMENTO DOS ARQUIVOS ==========
@st.cache_data
def carregar_dados_locais():
    """
    Carrega os dados das fontes locais.

    Retorna:
    - DataFrames combinados de cada fonte
    """
    base_dir = os.getcwd()  # Diretório atual

    folder_path_vendas = os.path.join(base_dir, 'Vendas')
    folder_path_centauro = os.path.join(base_dir, 'Repasse Centauro')
    folder_path_netshoes_ns2 = os.path.join(base_dir, 'Repasse Netshoes', 'NS2')
    folder_path_netshoes_magalu = os.path.join(base_dir, 'Repasse Netshoes', 'Magalu Pagamentos')

    # Verificar se as pastas existem
    for path in [folder_path_vendas, folder_path_centauro, folder_path_netshoes_ns2, folder_path_netshoes_magalu]:
        if not os.path.exists(path):
            registrar_erro(path, "Leitura_Erro", f"Pasta não encontrada: {path}")

    # Listar arquivos em cada pasta
    files_vendas = [os.path.join(folder_path_vendas, f) for f in os.listdir(folder_path_vendas) if f.endswith(('.xlsx', '.xls'))] if os.path.exists(folder_path_vendas) else []
    files_centauro = [os.path.join(folder_path_centauro, f) for f in os.listdir(folder_path_centauro) if f.endswith('.csv')] if os.path.exists(folder_path_centauro) else []
    files_netshoes_ns2 = [os.path.join(folder_path_netshoes_ns2, f) for f in os.listdir(folder_path_netshoes_ns2) if f.endswith(('.xlsx', '.xls'))] if os.path.exists(folder_path_netshoes_ns2) else []
    files_netshoes_magalu = [os.path.join(folder_path_netshoes_magalu, f) for f in os.listdir(folder_path_netshoes_magalu) if f.endswith(('.xlsx', '.xls'))] if os.path.exists(folder_path_netshoes_magalu) else []

    # Processar Vendas
    all_vendas = []
    for file in files_vendas:
        df_vendas = processar_vendas(file)
        if not df_vendas.empty:
            all_vendas.append(df_vendas)

    if all_vendas:
        combined_vendas = pd.concat(all_vendas, ignore_index=True)
    else:
        combined_vendas = pd.DataFrame(columns=["CÓDIGO PEDIDO", "DATA PEDIDO", "MARKETPLACE", "STATUS", "VALOR ESPERADO"])

    # Processar Centauro
    all_centauro = []
    for file in files_centauro:
        df_centauro = processar_centauro(file)
        if not df_centauro.empty:
            all_centauro.append(df_centauro)

    if all_centauro:
        combined_centauro = pd.concat(all_centauro, ignore_index=True)
    else:
        combined_centauro = pd.DataFrame(columns=["CÓDIGO PEDIDO", "VALOR TOTAL DOS PRODUTOS"])

    # Processar Netshoes NS2
    all_netshoes_ns2 = []
    for file in files_netshoes_ns2:
        df_netshoes_ns2 = processar_netshoes_ns2(file)
        if not df_netshoes_ns2.empty:
            all_netshoes_ns2.append(df_netshoes_ns2)

    if all_netshoes_ns2:
        combined_netshoes_ns2 = pd.concat(all_netshoes_ns2, ignore_index=True)
    else:
        combined_netshoes_ns2 = pd.DataFrame(columns=["CÓDIGO PEDIDO", "VALOR TOTAL DOS PRODUTOS", "Tipo"])

    # Processar Netshoes Magalu
    all_netshoes_magalu = []
    for file in files_netshoes_magalu:
        df_netshoes_magalu = processar_netshoes_magalu(file)
        if not df_netshoes_magalu.empty:
            all_netshoes_magalu.append(df_netshoes_magalu)

    if all_netshoes_magalu:
        combined_netshoes_magalu = pd.concat(all_netshoes_magalu, ignore_index=True)
    else:
        combined_netshoes_magalu = pd.DataFrame(columns=["CÓDIGO PEDIDO", "VALOR TOTAL DOS PRODUTOS", "Tipo"])

    return combined_vendas, combined_centauro, combined_netshoes_ns2, combined_netshoes_magalu

# ========== EXECUÇÃO ==========
def main():
    # Carregar os dados automaticamente ao iniciar a aplicação
    with st.spinner("🔄 Carregando dados..."):
        vendas, centauro, netshoes_ns2, netshoes_magalu = carregar_dados_locais()

    if not (vendas.empty and centauro.empty and netshoes_ns2.empty and netshoes_magalu.empty):
        # Conciliação e Cálculos
        final_df = conciliar_e_calcular(vendas, centauro, netshoes_ns2, netshoes_magalu)
        
        # Redução de Colunas: Selecionar apenas as colunas essenciais
        colunas_essenciais = [
            "CÓDIGO PEDIDO",
            "DATA PEDIDO",
            "MARKETPLACE",
            "STATUS",
            "Valor Esperado",
            "Valor Recebido",
            "Extorno",
            "Diferença",
            "Conciliado",
            "Possível Motivo",
            "Erro de Valor",
            "Outro Erro"
        ]
        # Garantir que todas as colunas essenciais existam
        colunas_presentes = [col for col in colunas_essenciais if col in final_df.columns]
        final_df_reduzido = final_df[colunas_presentes]

        # Adicionar colunas de ícones para "Erro de Valor" e "Outro Erro"
        final_df_reduzido["Erro de Valor Icone"] = final_df_reduzido["Erro de Valor"]
        final_df_reduzido["Outro Erro Icone"] = final_df_reduzido["Outro Erro"]

        # Filtros na barra lateral
        st.sidebar.header("🔍 Filtros")

        # Filtrar por Marketplace
        marketplaces = final_df_reduzido["MARKETPLACE"].dropna().unique().tolist()
        selected_marketplace = st.sidebar.multiselect(
            "Selecione Marketplace:", 
            marketplaces, 
            default=marketplaces
        )

        # Filtrar por Status
        status_vendas = final_df_reduzido["STATUS"].dropna().unique().tolist()
        selected_status = st.sidebar.multiselect(
            "Selecione Status da Venda:", 
            status_vendas, 
            default=status_vendas
        )

        # Slider para intervalo de valores
        valor_min = float(final_df_reduzido["Valor Esperado"].min()) if not final_df_reduzido.empty else 0.0
        valor_max = float(final_df_reduzido["Valor Esperado"].max()) if not final_df_reduzido.empty else 0.0
        valor_min_input, valor_max_input = st.sidebar.slider(
            "Intervalo de Valor Esperado:",
            min_value=0.0,
            max_value=valor_max,
            value=(valor_min, valor_max)
        )

        # Campo de pesquisa por código do pedido
        codigo_pedido_input = st.sidebar.text_input("🔎 Pesquisar por CÓDIGO PEDIDO:")

        # Filtro por Tipo de Erro
        st.sidebar.header("⚠️ Filtros de Erro")
        tipos_erro = list(ERRO_MAP.keys()) + ["Divergente"]  # Adiciona "Divergente" como tipo de erro
        selected_tipo_erro = st.sidebar.multiselect(
            "Filtrar por Tipo de Erro:", 
            tipos_erro, 
            default=tipos_erro
        )

        # Checkbox para incluir/excluir sem erros
        incluir_sem_erros = st.sidebar.checkbox("🔒 Incluir Pedidos sem Erros", value=True)

        # Aplicar filtros
        df_filtrado = final_df_reduzido.copy()

        if selected_marketplace:
            df_filtrado = df_filtrado[df_filtrado["MARKETPLACE"].isin(selected_marketplace)]

        if selected_status:
            df_filtrado = df_filtrado[df_filtrado["STATUS"].isin(selected_status)]

        df_filtrado = df_filtrado[
            (df_filtrado["Valor Esperado"] >= valor_min_input) &
            (df_filtrado["Valor Esperado"] <= valor_max_input)
        ]

        if codigo_pedido_input:
            df_filtrado = df_filtrado[df_filtrado["CÓDIGO PEDIDO"].str.contains(codigo_pedido_input, case=False, na=False)]

        # Filtro por Tipo de Erro
        if selected_tipo_erro:
            conditions = []
            if "Divergente" in selected_tipo_erro:
                conditions.append(df_filtrado["Conciliado"] == "Divergente")
            if "Erro de Valor" in selected_tipo_erro:
                conditions.append(df_filtrado["Erro de Valor Icone"] == "❌")
            if "Outro Erro" in selected_tipo_erro:
                conditions.append(df_filtrado["Outro Erro Icone"] == "❌")
            if conditions:
                mask = conditions[0]
                for condition in conditions[1:]:
                    mask |= condition
                df_filtrado = df_filtrado[mask]

        # Filtro para incluir/excluir sem erros
        if not incluir_sem_erros:
            df_filtrado = df_filtrado[
                (df_filtrado["Erro de Valor Icone"] == "❌") |
                (df_filtrado["Outro Erro Icone"] == "❌") |
                (df_filtrado["Conciliado"] == "Divergente")
            ]

        # Aplicar estilos
        def highlight_errors(row):
            if row['Conciliado'] == 'Divergente':
                return ['background-color: #FFA07A'] * len(row)  # Salmão claro
            else:
                return [''] * len(row)

        styled_df_filtrado = df_filtrado.style.apply(highlight_errors, axis=1)

        # Layout Melhorado com Tabs
        tabs = st.tabs(["📄 Conciliação", "📈 Estatísticas", "📝 Log de Erros"])

        with tabs[0]:
            st.subheader("Pedidos Consolidados")
            # Exibir DataFrame com estilos
            st.dataframe(styled_df_filtrado, height=600)

            # Adicionar funcionalidade para visualizar RAW DATA
            st.markdown("### 📋 RAW DATA")
            selected_pedido = st.selectbox("Selecione um CÓDIGO PEDIDO para ver os dados brutos:", df_filtrado["CÓDIGO PEDIDO"].unique())
            if selected_pedido:
                # Obter dados brutos de todas as fontes para o pedido selecionado
                raw_data_vendas = vendas[vendas["CÓDIGO PEDIDO"] == selected_pedido]
                raw_data_centauro = centauro[centauro["CÓDIGO PEDIDO"] == selected_pedido]
                raw_data_netshoes_ns2 = netshoes_ns2[netshoes_ns2["CÓDIGO PEDIDO"] == selected_pedido]
                raw_data_netshoes_magalu = netshoes_magalu[netshoes_magalu["CÓDIGO PEDIDO"] == selected_pedido]
                
                st.markdown("#### Vendas")
                st.dataframe(raw_data_vendas, height=200)
                
                st.markdown("#### Centauro")
                st.dataframe(raw_data_centauro, height=200)
                
                st.markdown("#### Netshoes NS2")
                st.dataframe(raw_data_netshoes_ns2, height=200)
                
                st.markdown("#### Netshoes Magalu")
                st.dataframe(raw_data_netshoes_magalu, height=200)

            # Legenda
            st.markdown("### 🗒️ Legenda")
            st.markdown("✅ **OK**: Conciliado sem divergências.")
            st.markdown("❌ **Divergente**: Há divergências nos dados.")
            st.markdown("❌ **Erro de Valor**: Discrepância no valor.")
            st.markdown("❌ **Outro Erro**: Há outros erros.")

        with tabs[1]:
            st.subheader("📊 Estatísticas")
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("Total de Pedidos", len(final_df_reduzido))
            with col_b:
                st.metric("Pedidos Conciliados", len(final_df_reduzido[final_df_reduzido['Conciliado'] == "OK"]))
            with col_c:
                st.metric("Pedidos Divergentes", len(final_df_reduzido[final_df_reduzido['Conciliado'] == "Divergente"]))
            with col_d:
                st.metric("Total Extornos", final_df_reduzido["Extorno"].sum())

            # Gráfico de Distribuição de Erros
            st.subheader("📉 Distribuição de Erros")
            erro_counts = final_df_reduzido["Conciliado"].value_counts().reset_index()
            erro_counts.columns = ["Conciliado", "Quantidade"]
            st.bar_chart(erro_counts.set_index("Conciliado"))

        with tabs[2]:
            st.subheader("📝 Log de Erros")
            
            # Convertendo lista de erros para DataFrame
            if st.session_state.lista_erros:
                log_erros_df = pd.DataFrame(st.session_state.lista_erros)
                
                # Mapeamento de códigos de erro para descrição
                log_erros_df["Descricao_Erro"] = log_erros_df["Codigo_Erro"].map({
                    1001: "Erro ao ler o arquivo",
                    1002: "Erro na conversão de tipo de dados",
                    1003: "Valor nulo inesperado",
                    1004: "Divergência encontrada",
                    1005: "Falha na consolidação dos dados"
                }).fillna("Erro desconhecido")
                
                # Filtro para tipos de erro
                tipos_erro_log = list(ERRO_MAP.keys())
                selected_tipo_erro_log = st.multiselect(
                    "🔍 Filtrar por Tipo de Erro:", 
                    tipos_erro_log, 
                    default=tipos_erro_log
                )
                
                # Filtrar o log de erros
                if selected_tipo_erro_log:
                    codigos_filtrados = [ERRO_MAP[tipo] for tipo in selected_tipo_erro_log]
                    df_log_filtrado = log_erros_df[log_erros_df["Codigo_Erro"].isin(codigos_filtrados)]
                else:
                    df_log_filtrado = log_erros_df.copy()
                
                if not df_log_filtrado.empty:
                    # Reordenar colunas para melhor visualização
                    df_log_filtrado = df_log_filtrado[["Timestamp", "Arquivo", "Codigo_Erro", "Descricao_Erro", "Mensagem_Erro"]]
                    
                    # Exibir DataFrame de log de erros
                    st.dataframe(df_log_filtrado, height=300)
                else:
                    st.write("Nenhum erro registrado para os tipos selecionados.")
            else:
                st.write("Nenhum erro registrado.")

        # Botão para baixar a planilha consolidada
        st.sidebar.header("💾 Download")
        st.sidebar.download_button(
            label="📥 Baixar Planilha Consolidada",
            data=final_df_reduzido.to_csv(index=False).encode('utf-8'),
            file_name='consolidado_repasses_vendas.csv',
            mime='text/csv'
        )
    else:
        st.info("📁 Certifique-se de que as pastas estejam corretamente organizadas e contenham os arquivos necessários.")
        st.markdown("""
        **Estrutura de Diretórios Esperada:**
        
        ```
        /seu_diretorio_projeto/
        │
        ├── trilha.py
        ├── Vendas/
        │   ├── arquivo1.xlsx
        │   ├── arquivo2.xlsx
        │   └── ...
        ├── Repasse Centauro/
        │   ├── arquivo1.csv
        │   ├── arquivo2.csv
        │   └── ...
        ├── Repasse Netshoes/
        │   ├── NS2/
        │   │   ├── arquivo1.xlsx
        │   │   ├── arquivo2.xlsx
        │   │   └── ...
        │   └── Magalu Pagamentos/
        │       ├── arquivo1.xlsx
        │       ├── arquivo2.xlsx
        │       └── ...
        ```
        
        **Observações:**
        - Verifique se os nomes das colunas nos arquivos correspondem exatamente aos utilizados no script.
        - Certifique-se de que os arquivos estejam no formato correto (XLSX, XLS para Excel e CSV para Centauro).
        """)

if __name__ == "__main__":
    main()
