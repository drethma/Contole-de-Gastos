import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# Conexão com o banco de dados
conn = sqlite3.connect("financeiro.db", check_same_thread=False)
cursor = conn.cursor()

# Criar a tabela se não existir
cursor.execute('''
CREATE TABLE IF NOT EXISTS transacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    tipo TEXT,
    descricao TEXT,
    valor REAL
)
''')
conn.commit()

# Função para adicionar transações
def adicionar_transacao(data, tipo, descricao, valor):
    cursor.execute("INSERT INTO transacoes (data, tipo, descricao, valor) VALUES (?, ?, ?, ?)",
                   (data, tipo, descricao, valor))
    conn.commit()

# Função para buscar transações
def buscar_transacoes(mes=None):
    if mes:
        cursor.execute("SELECT * FROM transacoes WHERE strftime('%m', data) = ?", (mes,))
    else:
        cursor.execute("SELECT * FROM transacoes")
    return cursor.fetchall()

# Função para editar transações
def editar_transacao(id, data, tipo, descricao, valor):
    cursor.execute("""
        UPDATE transacoes 
        SET data = ?, tipo = ?, descricao = ?, valor = ? 
        WHERE id = ?
    """, (data, tipo, descricao, valor, id))
    conn.commit()

# Sidebar com menu suspenso e ícones Unicode
st.sidebar.title("🔖 Menu")
opcao = st.sidebar.selectbox(
    "Escolha uma opção:", 
    [
        "📥 Cadastro de Transações",
        "📊 Visualizador de Transações",
        "📈 Gráficos"
    ]
)

# Tela de Cadastro de Transações
if opcao == "📥 Cadastro de Transações":
    st.header("📥 Cadastro de Transações")
    with st.form("form_transacao"):
        data = st.date_input("📅 Data", value=datetime.today())
        tipo = st.selectbox("🔄 Tipo", ["Entrada", "Saída"])
        descricao = st.text_input("📝 Descrição")
        valor = st.number_input("💵 Valor", min_value=0.0, format="%.2f")
        submit = st.form_submit_button("➕ Adicionar")
    
    if submit:
        adicionar_transacao(data.strftime("%Y-%m-%d"), tipo, descricao, valor)
        st.success("✅ Transação adicionada com sucesso!")

# Tela de Visualizador de Transações
elif opcao == "📊 Visualizador de Transações":
    st.header("📊 Visualizador de Transações")
    mes = st.selectbox("📅 Filtrar por mês", ["Todos"] + [f"{i:02d}" for i in range(1, 13)])
    transacoes = buscar_transacoes(mes if mes != "Todos" else None)
    
    df = pd.DataFrame(transacoes, columns=["ID", "Data", "Tipo", "Descrição", "Valor"])
    st.dataframe(df)
    
    # Opção de editar transações com base no filtro
    if not df.empty:
        id_editar = st.selectbox("✏️ Selecione a transação para editar", df["ID"])
        transacao = df[df["ID"] == id_editar].iloc[0]
        data, tipo, descricao, valor = transacao["Data"], transacao["Tipo"], transacao["Descrição"], transacao["Valor"]
        data = datetime.strptime(data, "%Y-%m-%d").date()
        
        with st.form("form_edicao"):
            nova_data = st.date_input("📅 Data", value=data)
            novo_tipo = st.selectbox("🔄 Tipo", ["Entrada", "Saída"], index=0 if tipo == "Entrada" else 1)
            nova_descricao = st.text_input("📝 Descrição", value=descricao)
            novo_valor = st.number_input("💵 Valor", min_value=0.0, format="%.2f", value=valor)
            editar_submit = st.form_submit_button("💾 Salvar Edição")
        
        if editar_submit:
            editar_transacao(id_editar, nova_data.strftime("%Y-%m-%d"), novo_tipo, nova_descricao, novo_valor)
            st.success("✅ Transação editada com sucesso!")

# Tela de Gráficos
elif opcao == "📈 Gráficos":
    st.header("📈 Gráficos de Entradas e Saídas")
    mes = st.selectbox("📅 Filtrar por mês", ["Todos"] + [f"{i:02d}" for i in range(1, 13)])
    transacoes = buscar_transacoes(mes if mes != "Todos" else None)
    
    df = pd.DataFrame(transacoes, columns=["ID", "Data", "Tipo", "Descrição", "Valor"])
    
    if not df.empty:
        # Calculando totais de entradas, saídas e saldo
        total_entradas = df[df["Tipo"] == "Entrada"]["Valor"].sum()
        total_saidas = df[df["Tipo"] == "Saída"]["Valor"].sum()
        saldo = total_entradas - total_saidas

        # Criando cartões
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### 💰 Entradas")
            st.info(f"R$ {total_entradas:,.2f}")

        with col2:
            st.markdown("### 📉 Saídas")
            st.warning(f"R$ {total_saidas:,.2f}")

        with col3:
            st.markdown("### 💵 Saldo")
            st.success(f"R$ {saldo:,.2f}")

        # Adicionando mês ao DataFrame
        df["Mês"] = pd.to_datetime(df["Data"]).dt.strftime("%Y-%m")
        df_agrupado = df.groupby(["Mês", "Tipo"], as_index=False).sum()
        
        # Gráfico principal
        fig = px.bar(
            df_agrupado, 
            x="Mês", 
            y="Valor", 
            color="Tipo", 
            barmode="group", 
            color_discrete_map={"Entrada": "green", "Saída": "red"},
            title="📊 Gráfico de Entradas e Saídas por Mês",
            labels={"Valor": "Valor (R$)", "Mês": "Mês"},
            text_auto=True
        )
        st.plotly_chart(fig)
        
        # Gráfico de barras ordenado por descrição
        df_ordenado = df.sort_values(by="Valor")
        fig2 = px.bar(
            df_ordenado, 
            x="Valor", 
            y="Descrição", 
            color="Tipo", 
            orientation="h", 
            color_discrete_map={"Entrada": "green", "Saída": "red"},
            title="📋 Gráfico Ordenado de Entradas e Saídas por Descrição",
            labels={"Valor": "Valor (R$)", "Descrição": "Descrição"},
            text_auto=True
        )
        st.plotly_chart(fig2)

        # Análise de IA sobre os gastos
        st.header("🤖 Análise Inteligente dos Gastos")

        if total_saidas > total_entradas:
            st.warning(f"⚠️ Suas saídas estão maiores que suas entradas. Você gastou R$ {total_saidas - total_entradas:,.2f} a mais do que recebeu.")
        elif total_entradas > total_saidas:
            st.success(f"✅ Suas entradas superam suas saídas. Você economizou R$ {total_entradas - total_saidas:,.2f} este mês!")
        else:
            st.info("ℹ️ Suas entradas e saídas estão equilibradas.")

        # Identificando a maior despesa
        if not df[df["Tipo"] == "Saída"].empty:
            maior_despesa = df[df["Tipo"] == "Saída"].sort_values(by="Valor", ascending=False).iloc[0]
            st.write(f"💸 **Sua maior despesa foi:** {maior_despesa['Descrição']} no valor de R$ {maior_despesa['Valor']:,.2f} em {maior_despesa['Data']}.")

        # Identificando a maior entrada
        if not df[df["Tipo"] == "Entrada"].empty:
            maior_entrada = df[df["Tipo"] == "Entrada"].sort_values(by="Valor", ascending=False).iloc[0]
            st.write(f"💹 **Sua maior entrada foi:** {maior_entrada['Descrição']} no valor de R$ {maior_entrada['Valor']:,.2f} em {maior_entrada['Data']}.")
        
    else:
        st.info("ℹ️ Nenhuma transação cadastrada ainda.")

# Fechar conexão com o banco de dados
conn.close()
