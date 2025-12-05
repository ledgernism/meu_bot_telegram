import os
import logging
import gzip
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from io import BytesIO

# --- BIBLIOTECAS QUE REQUEREM LINUX (CAIRO/GTK) ---
# Se rodar no Windows, vai quebrar; se rodar no servidor, vai funcionar!
from lottie.parsers.svg import parse_svg_file
from lottie.exporters.json_exporter import export_tgs # O caminho que funcionou no 0.6.0
# Se o erro de 'json_exporter' retornar, tente 'from lottie.exporters.tgs import export_tgs'

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

    file_obj = await arquivo.get_file()
    
    # 1. Baixar o SVG e salvar no disco temporário
    input_filename = f"temp_{user.id}.svg"
    output_filename_tgs = f"sticker_{user.id}.tgs"
    await file_obj.download_to_drive(input_filename)

    try:
        # 2. Parsear SVG
        animation = parse_svg_file(input_filename)

        # 3. Exportar para TGS
        # O export_tgs já faz o gzip e salva o arquivo
        export_tgs(animation, output_filename_tgs)

        # 4. Enviar de volta para o usuário
        with open(output_filename_tgs, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=f"sticker.tgs",
                caption="Aqui está o seu sticker! 🚀"
            )

    except Exception as e:
        await update.message.reply_text(f"Ocorreu um erro na conversão. O SVG pode ser muito complexo ou ter recursos não suportados. Erro: {str(e)}")
        print(f"Erro de Conversão: {e}")

    finally:
        # Limpeza
        for f in [input_filename, output_filename_tgs]:
            if os.path.exists(f):
                os.remove(f)

# --- INICIALIZAÇÃO ---

def main():
    # SUBSTITUA PELO SEU TOKEN AQUI
    TOKEN = "8511876574:AAG4_Kw7YV5qbRf4VJiCoyv6Q3xCHQCGqD4"
    
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, converter_svg))

    print("Bot rodando... Pressione Ctrl+C para parar.")
    application.run_polling()

if __name__ == '__main__':
    main()