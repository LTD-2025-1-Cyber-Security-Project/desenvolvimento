import PyPDF2
import os

def extract_text_from_pdf(pdf_path):
    """
    Extrai texto de um arquivo PDF usando PyPDF2.
    
    Args:
        pdf_path (str): Caminho para o arquivo PDF
        
    Returns:
        str: Texto extraído do PDF
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"O arquivo {pdf_path} não foi encontrado.")
    
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() or ""
        
        # Se o texto extraído for substancial, retorne-o
        if len(text.strip()) > 10:
            return text
        else:
            raise Exception("Texto extraído muito curto ou vazio")
    except Exception as e:
        print(f"Erro ao extrair texto com PyPDF2: {e}")
        
        # Como removemos pdfminer.six, vamos retornar um erro mais descritivo
        raise Exception(f"Não foi possível extrair texto do PDF fornecido: {str(e)}. " +
                        "Verifique se o PDF tem conteúdo de texto selecionável e não apenas imagens.")