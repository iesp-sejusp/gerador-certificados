import io
import os
import zipfile
import pandas as pd
import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
import base64

# Configuração da página da aplicação
st.set_page_config(page_title="Gerador de Certificados", page_icon="📜", layout="centered")

# --- FUNÇÃO PARA CONVERTER IMAGEM EM BASE64 (PARA O CSS DO FUNDO) ---
def get_base64_of_bin_file(bin_file):
    if not os.path.exists(bin_file):
        return None
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --- CONFIGURAÇÃO DA LOGO E IMAGEM DE FUNDO ---
# Certifique-se de subir esses arquivos para o seu repositório no GitHub
CAMINHO_LOGO = "logo.png"   # Nome do arquivo da logo no topo
CAMINHO_FUNDO = "fundo.jpg" # Nome do arquivo da imagem de fundo

# Aplicando Estilos CSS para Fundo Responsivo e Layout
bin_fundo = get_base64_of_bin_file(CAMINHO_FUNDO)
if bin_fundo:
    css_fundo = f"""
    <style>
    .stApp {{
        background-image: linear-gradient(rgba(15, 23, 42, 0.85), rgba(15, 23, 42, 0.85)), url("data:image/jpg;base64,{bin_fundo}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    /* Tornando textos legíveis sobre o fundo escuro */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {{
        color: #FFFFFF !important;
    }}
    </style>
    """
    st.markdown(css_fundo, unsafe_allow_html=True)

# --- EXIBIR LOGO NO TOPO ---
if os.path.exists(CAMINHO_LOGO):
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.image(CAMINHO_LOGO, use_container_width=True)

st.title("📜 Gerador de Certificados em Lote")
st.markdown("Carregue o modelo do certificado (frente e verso) e a planilha com os dados dos alunos para gerar os arquivos individuais em PDF.")

# --- ÁREA DE UPLOAD ---
col1, col2 = st.columns(2)

with col1:
    arquivo_modelo = st.file_uploader("1. Modelo do Certificado (PDF com 2 páginas)", type=["pdf"])

with col2:
    arquivo_excel = st.file_uploader("2. Lista de Participantes (Excel)", type=["xlsx", "xls"])

# --- FUNÇÃO DE GERAÇÃO DA CAMADA DE TEXTO ---
def criar_camada_texto(nome, matricula):
    packet = io.BytesIO()
    # Dimensões do A4 Paisagem: Largura = 841.89, Altura = 595.27
    largura_pagina = 841.89
    can = canvas.Canvas(packet, pagesize=landscape(letter))
    
    try:
        nome_str = str(nome)
        matricula_str = f"Matrícula: {str(matricula)}"
        
        # --- NOME DO ALUNO (Centralizado) ---
        fonte_nome = "Helvetica-Bold"
        tamanho_fonte_nome = 26
        can.setFont(fonte_nome, tamanho_fonte_nome)
        
        largura_texto_nome = can.stringWidth(nome_str, fonte_nome, tamanho_fonte_nome)
        pos_x_nome = (largura_pagina - largura_texto_nome) / 2
        pos_y_nome = 320 # Altura do nome (ajuste aqui se precisar descer mais)
        
        can.drawString(pos_x_nome, pos_y_nome, nome_str) 
        
        # --- MATRÍCULA (Centralizada e abaixo do nome) ---
        fonte_mat = "Helvetica"
        tamanho_fonte_mat = 14
        can.setFont(fonte_mat, tamanho_fonte_mat)
        
        largura_texto_mat = can.stringWidth(matricula_str, fonte_mat, tamanho_fonte_mat)
        pos_x_mat = (largura_pagina - largura_texto_mat) / 2
        pos_y_mat = 270 # Altura da matrícula
        
        can.drawString(pos_x_mat, pos_y_mat, matricula_str) 
        
    except Exception as e:
        can.setFont("Helvetica-Bold", 24)
        can.drawString(150, 320, str(nome))
        can.setFont("Helvetica", 14)
        can.drawString(150, 270, f"Matrícula: {str(matricula)}")

    can.save()
    packet.seek(0)
    return PdfReader(packet)

# --- PROCESSAMENTO ---
if st.button("🚀 Gerar Certificados", type="primary"):
    if not arquivo_modelo or not arquivo_excel:
        st.error("Por favor, faça o upload de ambos os arquivos (Modelo PDF e Planilha Excel) antes de continuar.")
    else:
        try:
            with st.spinner("Processando certificados..."):
                # Carregar planilha
                df = pd.read_excel(arquivo_excel)
                
                # Validação de colunas
                if 'Nome' not in df.columns or 'Matricula' not in df.columns:
                    st.error("A planilha Excel precisa conter obrigatoriamente as colunas com os nomes exatos: 'Nome' e 'Matricula'.")
                    st.stop()

                leitor_modelo_base = PdfReader(arquivo_modelo)
                
                if len(leitor_modelo_base.pages) < 2:
                    st.error("O modelo em PDF precisa conter pelo menos 2 páginas (Página 1: Frente | Página 2: Verso).")
                    st.stop()

                # Buffer para armazenar o arquivo ZIP final em memória
                zip_buffer = io.BytesIO()

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for index, row in df.iterrows():
                        nome = str(row['Nome']).strip()
                        matricula = str(row['Matricula']).strip()

                        # Tratar o nome mantendo acentos para os arquivos
                        nome_arquivo_valido = "".join(c for c in nome if c.isalnum() or c in (' ', '_', '-', 'á','é','í','ó','ú','ã','õ','â','ê','ô','ç','Á','É','Í','Ó','Ú','Ã','Õ','Â','Ê','Ô','Ç')).strip()
                        if not nome_arquivo_valido:
                            nome_arquivo_valido = f"certificado_{index+1}"
                        
                        # Recarregar o leitor a cada iteração para isolar as páginas
                        leitor_modelo = PdfReader(arquivo_modelo)
                        pagina_frente = leitor_modelo.pages[0]
                        pagina_verso = leitor_modelo.pages[1]

                        # Criar e mesclar a camada de texto na Frente (Página 1)
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

                st.success("✅ Certificados gerados com sucesso!")
                
                # Botão para baixar o ZIP
                st.download_button(
                    label="📦 Baixar Todos os Certificados (.ZIP)",
                    data=zip_buffer,
                    file_name="certificados_gerados.zip",
                    mime="application/zip"
                )

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar os arquivos: {str(e)}")

# --- RODAPÉ PERSONALIZADO ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #FFFFFF; font-size: 14px;'>Desenvolvido por Luciano Moresco</div>", 
    unsafe_allow_html=True
)
