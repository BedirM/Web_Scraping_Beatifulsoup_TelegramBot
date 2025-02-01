import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from colorama import Fore, Style
import asyncio
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os

# .env dosyasını yükle
load_dotenv()

# Çevresel değişkenlerden bot token'ı al
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_BOT_TOKEN)

def get_filename():
    today = datetime.today().strftime("%Y-%m-%d")
    return f"hacker_news_{today}.txt"

# Asenkron mesaj gönderme fonksiyonu
async def send_telegram_message(message):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        print(f"Telegram Error: {e}")

# Hacker News Scraping Fonksiyonu
async def scrape_hacker_news():
    url = "https://thehackernews.com/?m=1"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print("Failed to retrieve the page")
        return
    
    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.find_all("div", class_="body-post")
    
    existing_titles = set()
    json_filename = "hacker_news.json"
    try:
        with open(json_filename, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            for article in data:
                existing_titles.add(article["title"])
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    
    new_articles = []
    with open(get_filename(), "a", encoding="utf-8") as file:
        for article in articles:
            title_tag = article.find("h2", class_="home-title")
            link_tag = article.find("a")
            content_tag = article.find("div", class_="home-desc")
            
            if title_tag and link_tag and content_tag:
                title = title_tag.text.strip()
                link = link_tag["href"]
                content = content_tag.text.strip()
                
                if title not in existing_titles:
                    file.write(f"Title: {title}\nLink: {link}\nContent: {content}\n{'-'*80}\n")
                    print(f"{Fore.GREEN}New Article Found!{Style.RESET_ALL}")
                    print(f"Title: {title}\nLink: {link}\nContent: {content}\n{'-'*80}")
                    new_articles.append({"title": title, "link": link, "content": content})
                    
                    # Asenkron mesaj gönderme
                    await send_telegram_message(f"New Article:\n{title}\n{link}")
    
    if new_articles:
        data.extend(new_articles)
        with open(json_filename, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

# Asenkron haber çekme ve zamanlama
async def schedule_scraping():
    while True:
        await scrape_hacker_news()
        print("1 saat sonraki yeni güncellemeye kadar bekleniyor...")
        await asyncio.sleep(3600)  # 1 saat bekleme

# Telegram bot komutları
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hoş geldiniz! /haberler yazarak güncel haberleri alabilirsiniz.")

async def send_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(get_filename(), "rb") as file:
            await update.message.reply_document(file)
    except FileNotFoundError:
        await update.message.reply_text("Henüz haber bulunmamaktadır.")

if __name__ == "__main__":
    # Telegram uygulaması başlat
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("haberler", send_news))
    
    # Haber çekme işlemini asenkron başlat
    loop = asyncio.get_event_loop()
    loop.create_task(schedule_scraping())  # Asenkron görev başlat
    print("Bot çalışıyor, /start ile başlayabilirsiniz.")
    app.run_polling()