# -*- coding: utf-8 -*-
import io
import os
import zipfile
import pandas as pd
import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas

# Configura豪o da p㍑ina da aplica豪o
st.set_page_config(page_title="Gerador de Certificados", page_icon="??", layout="centered")

st.title("?? Gerador de Certificados em Lote")
st.markdown("Carregue o modelo do certificado (frente e verso) e a planilha com os dados dos alunos para gerar os arquivos individuais em PDF.")

# --- 躋EA DE UPLOAD ---
col1, col2 = st.columns(2)

with col1:
    arquivo_modelo = st.file_uploader("1. Modelo do Certificado (PDF com 2 p㍑inas)", type=["pdf"])

with col2:
    arquivo_excel = st.file_uploader("2. Lista de Participantes (Excel)", type=["xlsx", "xls"])

# --- FUNのO DE GERAのO DA CAMADA DE TEXTO ---
def criar_camada_texto(nome, matricula):
    packet = io.BytesIO()
    # Posi豪o em Paisagem (Landscape) A4
    can = canvas.Canvas(packet, pagesize=landscape(letter))
    
    # --- AJUSTE AS COORDENADAS (X, Y) AQUI CONFORME SEU MODELO ---
    # Nome do Aluno
    can.setFont("Helvetica-Bold", 24)
    can.drawString(150, 300, str(nome)) 
    
    # Matr団ula
    can.setFont("Helvetica", 14)
    can.drawString(150, 250, f"Matr団ula: {str(matricula)}") 
    
    can.save()
    packet.seek(0)
    return PdfReader(packet)

# --- PROCESSAMENTO ---
if st.button("?? Gerar Certificados", type="primary"):
    if not arquivo_modelo or not arquivo_excel:
        st.error("Por favor, fa溝 o upload de ambos os arquivos (Modelo PDF e Planilha Excel) antes de continuar.")
    else:
        try:
            with st.spinner("Processando certificados..."):
                # Carregar planilha
                df = pd.read_excel(arquivo_excel)
                
                # Valida豪o de colunas
                if 'Nome' not in df.columns or 'Matricula' not in df.columns:
                    st.error("A planilha Excel precisa conter obrigatoriamente as colunas com os nomes exatos: 'Nome' e 'Matricula'.")
                    st.stop()

                leitor_modelo_base = PdfReader(arquivo_modelo)
                
                if len(leitor_modelo_base.pages) < 2:
                    st.error("O modelo em PDF precisa conter pelo menos 2 p㍑inas (P㍑ina 1: Frente | P㍑ina 2: Verso).")
                    st.stop()

                # Buffer para armazenar o arquivo ZIP final em mem羊ia
                zip_buffer = io.BytesIO()

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for index, row in df.iterrows():
                        nome = str(row['Nome']).strip()
                        matricula = str(row['Matricula']).strip()

                        # Tratar o nome para evitar erros em caracteres de arquivo
                        nome_arquivo_valido = "".join(c for c in nome if c.isalnum() or c in (' ', '_', '-')).strip()
                        
                        # Recarregar o leitor a cada itera豪o para isolar as p㍑inas
                        leitor_modelo = PdfReader(arquivo_modelo)
                        pagina_frente = leitor_modelo.pages[0]
                        pagina_verso = leitor_modelo.pages[1]

                        # Criar e mesclar a camada de texto na Frente (P㍑ina 1)
                        pdf_texto = criar_camada_texto(nome, matricula)
                        pagina_frente.merge_page(pdf_texto.pages[0])

                        # Montar o PDF final do aluno (Frente + Verso)
                        escritor = PdfWriter()
                        escritor.add_page(pagina_frente)
                        escritor.add_page(pagina_verso)

                        # Salvar PDF individual no buffer
                        pdf_individual_buffer = io.BytesIO()
                        escritor.write(pdf_individual_buffer)
                        pdf_individual_buffer.seek(0)

                        # Adicionar o PDF dentro do arquivo ZIP
                        zip_file.writestr(f"{nome_arquivo_valido}.pdf", pdf_individual_buffer.getvalue())

                zip_buffer.seek(0)

                st.success("? Certificados gerados com sucesso!")
                
                # Bot黍 para baixar o ZIP
                st.download_button(
                    label="?? Baixar Todos os Certificados (.ZIP)",
                    data=zip_buffer,
                    file_name="certificados_gerados.zip",
                    mime="application/zip"
                )

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar os arquivos: {str(e)}")
