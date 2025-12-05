import os
import logging
import httpx # Usamos httpx em vez de requests, mais moderno
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from io import BytesIO

# --- API DE CONVERSÃO EXTERNA (Mais estável que as anteriores) ---
CONVERSION_API_URL = "https://svg2tgs.tgstools.com/convert"

# Configuração de Log
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Envie o seu arquivo SVG para que eu possa convertê-lo para TGS."
    )

async def converter_svg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    arquivo = update.message.document

    if not arquivo.file_name.lower().endswith('.svg'):
        await update.message.reply_text("Por favor, envie apenas arquivos com extensão .svg.")
        return

    await update.message.reply_text("Aguarde enquanto convertemos... ⏳")

    try:
        # 1. Obter o objeto do arquivo
        file_obj = await arquivo.get_file()
        
        # 2. Baixar o conteúdo como bytes
        # Usamos download_as_bytearray, que corrige o erro do início da conversa.
        svg_bytes = await file_obj.download_as_bytearray()
        
        # 3. Enviar para a API externa
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {'file': ('sticker.svg', svg_bytes, 'image/svg+xml')}
            response = await client.post(CONVERSION_API_URL, files=files)

        # 4. Checar a resposta da API
        if response.status_code == 200:
            # A API retorna o arquivo TGS
            tgs_bytes = response.content
            
            await update.message.reply_document(
                document=tgs_bytes,
                filename="sticker.tgs",
                caption="Aqui está o seu sticker! 🚀"
            )
        else:
            await update.message.reply_text(
                f"Ocorreu um erro na conversão. Código de erro HTTP: {response.status_code}. "
                f"Mensagem: {response.text[:100]}"
            )

    except Exception as e:
        await update.message.reply_text(
            f"Ocorreu um erro ao conectar ao servidor de conversão. Tente novamente mais tarde. Erro: {type(e).__name__}: {str(e)}"
        )
        print(f"Erro de Conversão/Conexão: {e}")

# --- INICIALIZAÇÃO ---

def main():
    # Garantindo que o TOKEN seja lido da variável de ambiente no Render
    TOKEN = os.environ.get("TOKEN")

    if not TOKEN:
        # Se for rodar localmente, o TOKEN precisa ser definido aqui
        # Para o Render, esta linha deve ser ignorada se o TOKEN for definido lá.
        raise ValueError("Token do Telegram não encontrado. Defina a variável TOKEN no Render.")
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, converter_svg))
    
    print("Bot rodando... Pressione Ctrl+C para parar.")
    # Usamos run_polling() para ambientes simples como o Render
    application.run_polling(poll_interval=10, timeout=15)

if __name__ == '__main__':
    main()