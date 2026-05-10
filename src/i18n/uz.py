"""Uzbek (Latin) UI strings."""
from __future__ import annotations

MESSAGES: dict[str, str] = {
    # ---- onboarding & language ------------------------------------
    "language_choose": "🌐 Iltimos, tilni tanlang:\n\nPlease choose your language:",
    "language_set": "✅ Til o'zbekchaga o'rnatildi.\n\nMenga shubhali xabar, link yoki SMS yuboring — men uni phishing'ga tekshirib, sizga o'zbek tilida tushuntirib beraman.",
    # ---- /start ---------------------------------------------------
    "start": (
        "👋 *{bot_name}'ga xush kelibsiz!*\n\n"
        "Men oddiy odamlarni SMS, Telegram, email yoki WhatsApp orqali keladigan firibgarliklardan himoya qiladigan phishing detektoriman.\n\n"
        "*Qanday foydalanish:*\n"
        "• Shubhali xabarni nusxa ko'chiring yoki menga forward qiling\n"
        "• Men sizga aytaman: XAVFSIZ, SHUBHALI yoki PHISHING\n"
        "• Sababini sizning tilingizda tushuntiraman\n\n"
        "*Komandalar*\n"
        "/help – bot qanday ishlaydi\n"
        "/about – bot haqida\n"
        "/language – tilni o'zgartirish\n"
        "/privacy – maxfiylik siyosati\n\n"
        "⚠️ Men yordamchiman, kafolat emasman. Shubha tug'ilsa, hech narsani bosmang va bankka to'g'ridan-to'g'ri qo'ng'iroq qiling."
    ),
    # ---- /help ----------------------------------------------------
    "help": (
        "*{bot_name}'dan qanday foydalanish*\n\n"
        "1. Biror joydan shubhali xabar oldingiz (SMS, Telegram, email).\n"
        "2. Matnni to'liq nusxa ko'chiring yoki menga forward qiling.\n"
        "3. Men tahlil qilaman va uchta xulosadan birini aytaman:\n"
        "   ✅ *XAVFSIZ* — qonuniy ko'rinadi\n"
        "   ⚠️ *SHUBHALI* — ehtiyot bo'ling, tekshirib ko'ring\n"
        "   🚨 *PHISHING* — firibgarlik belgilari kuchli, hech narsani bosmang\n\n"
        "*Xavfsiz qolish maslahatlar:*\n"
        "• Banklar HECH QACHON xabar orqali to'liq karta raqami, CVV, SMS kod yoki parolni so'ramaydi.\n"
        "• Haqiqiy domenlar kompaniyaning rasmiy nomi bilan tugaydi (masalan, `uzcard.uz`) — `uzcard-bonus.com` emas.\n"
        "• \"Siz yutdingiz\" yoki \"shoshilinch harakat\" deb yozsa — to'xtang, o'ylang.\n"
        "• Shubha bo'lsa — kartangiz orqasidagi rasmiy raqamga qo'ng'iroq qiling.\n\n"
        "Tahlil uchun istalgan matnni yuboring."
    ),
    # ---- /about ---------------------------------------------------
    "about": (
        "*{bot_name} haqida*\n\n"
        "Open-source Telegram bot — sun'iy idrok yordamida xabarlar, linklar, SMS va emaillarni "
        "phishing'ga tekshiradi. O'zbekiston va Markaziy Osiyo foydalanuvchilari uchun mahalliy "
        "banklar, xizmatlar va firibgarlik usullarini bilib mo'ljallangan.\n\n"
        "Yaratuvchi: [@nodirsafarov](https://github.com/nodirsafarov).\n"
        "Manba kodi: https://github.com/nodirsafarov/securelife-bot\n\n"
        "_Bu bot — yordamchi vosita, kafolat emas. Har qanday xabar bo'yicha harakat qilishdan oldin tashkilotning rasmiy aloqasi orqali tekshiring._"
    ),
    # ---- /privacy -------------------------------------------------
    "privacy": (
        "*Maxfiylik*\n\n"
        "• Men faqat sizning Telegram ID va til tanlovingizni saqlayman.\n"
        "• Yuborgan xabarlaringiz matnini SAQLAMAYMAN.\n"
        "• Har bir xabar tahlil qilingach darhol o'chiriladi.\n"
        "• Faqat umumiy hisoblagichlar (nechta tahlil, qaysi xulosalar) saqlanadi — monitoring uchun.\n"
        "• Ma'lumotlar uchinchi tomonlarga berilmaydi — faqat tahlil qiluvchi AI modelga.\n\n"
        "Open source: har bir qator kodni shu yerda tekshirishingiz mumkin: https://github.com/nodirsafarov/securelife-bot"
    ),
    # ---- /language ------------------------------------------------
    "language_prompt": "🌐 Tilni tanlang:",
    # ---- analysis flow --------------------------------------------
    "analyzing": "🔍 Xabaringiz tahlil qilinmoqda…",
    "send_text_hint": "Tahlil qilish uchun shubhali xabar, link yoki SMS yuboring.",
    "input_too_short": "❌ Xabar tahlil qilish uchun juda qisqa. Iltimos, to'liq matnni yuboring.",
    "input_too_long": "❌ Xabar juda uzun ({max} belgi maksimum). Iltimos, qisqartirib qayta yuboring.",
    # ---- verdicts -------------------------------------------------
    "verdict_safe": "✅ *Xulosa: XAVFSIZ*",
    "verdict_suspicious": "⚠️ *Xulosa: SHUBHALI*",
    "verdict_phishing": "🚨 *Xulosa: PHISHING*",
    "verdict_unknown": "❓ *Xulosa: ANIQ EMAS*",
    "result_template": (
        "{verdict_line}\n"
        "*Xavf darajasi:* {risk_score}/100\n\n"
        "*Sabablari:*\n{reasons}\n\n"
        "*Nima qilish kerak:*\n{advice}\n\n"
        "_Eslatma: bu AI baholashi, kafolat emas. Shubha bo'lsa, kartangiz orqasidagi rasmiy raqamga qo'ng'iroq qiling._"
    ),
    # ---- rate limit -----------------------------------------------
    "rate_limited": "⏳ Soatlik chegaraga yetdingiz. Iltimos, {minutes} daqiqadan keyin qayta urinib ko'ring.",
    # ---- errors ---------------------------------------------------
    "error_generic": "😔 Kechirasiz, tahlil paytida xato yuz berdi. Iltimos, biroz vaqtdan so'ng qayta urinib ko'ring.",
    "error_ai_unavailable": "😔 AI xizmati vaqtinchalik mavjud emas. Iltimos, bir necha daqiqadan keyin qayta urinib ko'ring.",
    # ---- /stats (admin only) -------------------------------------
    "stats_title": "*SecureLife statistikasi*",
    "stats_body": (
        "Foydalanuvchilar: {total_users}\n"
        "Tahlillar: {total_analyses}\n"
        "✅ Xavfsiz: {verdict_safe}\n"
        "⚠️ Shubhali: {verdict_suspicious}\n"
        "🚨 Phishing: {verdict_phishing}"
    ),
    "not_admin": "❌ Bu komanda faqat administratorlar uchun.",
    # ---- buttons --------------------------------------------------
    "btn_english": "🇬🇧 English",
    "btn_uzbek": "🇺🇿 O'zbekcha",
}
