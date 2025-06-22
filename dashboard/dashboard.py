import streamlit as st
import pandas as pd
from app.database import SessionLocal
from app.models import Evento

st.set_page_config(page_title="RADAR Assessor Dashboard", layout="wide")
st.title("📊 Dashboard do RADAR Assessor")
telefone = st.text_input("Digite o número do usuário (WhatsApp):")

if telefone:
    db = SessionLocal()
    eventos = db.query(Evento).filter(Evento.telefone == telefone).order_by(Evento.criado_em.desc()).all()
    df = pd.DataFrame([{
        "Tipo": e.tipo,
        "Descrição": e.descricao,
        "Valor": e.valor,
        "Data": e.criado_em.strftime("%d/%m/%Y")
    } for e in eventos])

    compromissos = df[df["Tipo"] == "agenda"]
    gastos = df[df["Tipo"] == "gasto"]

    st.subheader("Compromissos")
    st.table(compromissos)

    st.subheader("Gastos por Categoria")
    if not gastos.empty:
        chart = gastos.groupby("Descrição")["Valor"].sum().reset_index()
        st.bar_chart(chart.set_index("Descrição"))
    else:
        st.write("Nenhum gasto registrado.")