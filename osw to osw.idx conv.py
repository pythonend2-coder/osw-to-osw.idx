import asyncio
import logging
import zipfile
import os
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from aiogram import F

BOT_TOKEN = ""

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# logi
logging.basicConfig(level=logging.INFO)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("отправь GERNL.osw а я сделаю GENRL.osw.idx")

@dp.message(F.document)
async def doc_idx(message: Message):
    document = message.document

    if document.file_name != "GENRL.osw":
        await message.answer("отправь GENRL.OSW")
        return

    file_info = await bot.get_file(document.file_id)
    file_path = file_info.file_path

    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)

    # сохраняем файл
    osw_file_path = temp_dir / "GENRL.osw"
    idx_file_path = temp_dir / "GENRL.osw.idx"

    try:
        # качаем файл
        await bot.download_file(file_path, destination=osw_file_path)

        if not zipfile.is_zipfile(osw_file_path):
            await message.answer("ошибка")
            return

        generate_idx_file(osw_file_path, idx_file_path)

        idx_file = FSInputFile(idx_file_path, filename="GENRL.osw.idx")
        await message.answer_document(idx_file, caption="idx готов")

    except Exception as e:
        await message.answer(f"ошибка : {str(e)}")
    finally:
        if osw_file_path.exists():
            os.remove(osw_file_path)
        if idx_file_path.exists():
            os.remove(idx_file_path)

def generate_idx_file(osw_path: Path, idx_path: Path):
    entries_info = []

    with zipfile.ZipFile(osw_path, 'r') as zip_file:
        cumulative_offset = 0

        for entry in zip_file.infolist():
            if entry.is_dir():
                continue

            # смещение idx
            cumulative_offset += len(entry.filename) + 30
            compressed_size = entry.compress_size

            # запись .idx в фвйл
            entries_info.append({
                'offset': cumulative_offset,
                'compressed_size': compressed_size,
                'filename': entry.filename
            })

            cumulative_offset += compressed_size

    with open(idx_path, 'wb') as idx_file:
        idx_file.write(len(entries_info).to_bytes(4, byteorder='little'))

        for entry in entries_info:
            idx_file.write(entry['offset'].to_bytes(4, byteorder='little'))
            idx_file.write(entry['compressed_size'].to_bytes(4, byteorder='little'))
            filename_bytes = entry['filename'].encode('ISO-8859-1')
            idx_file.write(len(filename_bytes).to_bytes(2, byteorder='little'))
            idx_file.write(filename_bytes)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())