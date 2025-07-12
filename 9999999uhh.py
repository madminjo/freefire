import logging
import requests
import aiohttp
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, Application, CommandHandler, ContextTypes,
)

# BOT TOKEN жана CONSTANTS
TOKEN = ""
CHANNEL_USERNAME = "@ffleaks_scromnyi444"
BAN_API = "https://scromnyi.vercel.app/region/ban-info?uid={uid}"
LIKE_API = "https://likes-scromnyi.vercel.app/like?uid={uid}&region={region}&key=Scromnyi206"

# Timestamp -> readable формат
def timestamp_to_date(timestamp):
    try:
        return datetime.fromtimestamp(int(timestamp)).strftime("%b %d, %Y %I:%M %p")
    except:
        return "Unknown"

# Rank аты
def get_rank_name(rank_points):
    rank_map = {
        0: "Bronze", 1000: "Silver", 2000: "Gold",
        3000: "Platinum", 4000: "Diamond",
        5000: "Master", 6000: "Grandmaster"
    }
    for threshold, rank in sorted(rank_map.items(), reverse=True):
        if rank_points >= threshold:
            return rank
    return "Unranked"

# Player маалымат алуу
def get_player_info(uid):
    url = f"https://accinfo.vercel.app/player-info?region=SG&uid={uid}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

# Каналга кошулуу кнопкасы
def join_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")]
    ])

# Каналда мүчөбү?
async def is_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except:
        return False

# /info командасы
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat = message.chat
    if chat.type not in ["group", "supergroup"]:
        return await message.reply_text("❗ This command only works in groups.")

    command_text = message.text.split()
    if len(command_text) < 2:
        await message.reply_text("/info <UID>")
        return

    uid = command_text[1]
    if not uid.isdigit():
        await message.reply_text("UID must be a number.")
        return

    wait_msg = await message.reply_text("Loading account info please wait...")

    data = get_player_info(uid)
    if not data:
        await wait_msg.edit_text("UID not found or invalid.")
        return

    basic = data.get("basicInfo", {})
    profile = data.get("profileInfo", {})
    clan = data.get("clanBasicInfo", {})
    captain = data.get("captainBasicInfo", {})
    pet = data.get("petInfo", {})
    credit = data.get("creditScoreInfo", {})

    created_at = timestamp_to_date(basic.get("createAt", "0"))
    last_login = timestamp_to_date(basic.get("lastLoginAt", "0"))
    leader_created = timestamp_to_date(captain.get("createAt", "0"))
    leader_last_login = timestamp_to_date(captain.get("lastLoginAt", "0"))

    rank_points = basic.get("rankingPoints", 0)
    cs_points = basic.get("csRankingPoints", 0)
    rank = get_rank_name(rank_points)

    response = f"""
<b>👤 Account Information</b>
├ <b>Nickname:</b> {basic.get("nickname", "N/A")}
├ <b>UID:</b> {basic.get("accountId", "N/A")}
├ <b>Level:</b> {basic.get("level", "N/A")}
├ <b>Likes:</b> {basic.get("liked", 0)}
├ <b>Exp:</b> {basic.get("exp", 0)}
├ <b>Avatar ID:</b> {profile.get("avatarId", "N/A")}
├ <b>Rank:</b> {basic.get("rank", "N/A")} ({rank_points} pts)
├ <b>Badges:</b> {basic.get("badgeCnt", 0)}
├ <b>CS Rank:</b> {basic.get("csRank", "N/A")} ({cs_points} pts)
└ <b>Bio:</b> {basic.get("nickname", "N/A")}

<b>📆 Account History</b>
├ <b>Created At:</b> {created_at}
└ <b>Last Login:</b> {last_login}

<b>🛡️ Guild Info</b>
├ <b>Clan:</b> {clan.get("clanName", "N/A")} (ID: {clan.get("clanId", "N/A")})
├ <b>Level:</b> {clan.get("clanLevel", "N/A")}
├ <b>Members:</b> {clan.get("memberNum", 0)}/50
├ <b>Captain:</b> {captain.get("nickname", "N/A")} (UID: {captain.get("accountId", "N/A")})

<b>👑 Guild Leader Info</b>
├ <b>Nickname:</b> {captain.get("nickname", "N/A")}
├ <b>Level:</b> {captain.get("level", "N/A")}
├ <b>Exp:</b> {captain.get("exp", 0)}
├ <b>Rank:</b> {captain.get("rank", "N/A")} ({captain.get("rankingPoints", 0)} pts)
├ <b>CS Rank:</b> {captain.get("csRank", "N/A")} ({captain.get("csRankingPoints", 0)} pts)
├ <b>Likes:</b> {captain.get("liked", 0)}
├ <b>Badges:</b> {captain.get("badgeCnt", 0)}
├ <b>Created At:</b> {leader_created}
└ <b>Last Login:</b> {leader_last_login}

<b>📊 Credit Score Info</b>
├ <b>Credit Score:</b> {credit.get("creditScore", 0)}
├ <b>Illegal Count:</b> {credit.get("illegalCnt", 0)}
├ <b>Like Count:</b> {credit.get("likeCnt", 0)}
├ <b>Summary Start:</b> {timestamp_to_date(credit.get("summaryStartTime", "0"))}
├ <b>Summary End:</b> {timestamp_to_date(credit.get("summaryEndTime", "0"))}
└ <b>Reward Status:</b> {credit.get("rewardState", "N/A")}

<b>🐾 Pet Info</b>
├ <b>Pet Name:</b> {pet.get("name", "N/A")}
├ <b>Pet Level:</b> {pet.get("level", "N/A")}
├ <b>Exp:</b> {pet.get("exp", 0)}
├ <b>Selected:</b> {"✅" if pet.get("isSelected", False) else "❌"}
└ <b>Skin ID:</b> {pet.get("skinId", "N/A")}
"""
    await wait_msg.edit_text(response.strip(), parse_mode=ParseMode.HTML)

# /check командасы
async def check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat = message.chat
    if chat.type not in ["group", "supergroup"]:
        return await message.reply_text("❗ This command only works in groups.")

    command_text = message.text.split()
    if len(command_text) < 2:
        await message.reply_text("/check <UID>")
        return

    uid = command_text[1]
    if not uid.isdigit():
        await message.reply_text("UID must be a number.")
        return

    wait_msg = await message.reply_text("Checking ban status...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(BAN_API.format(uid=uid)) as resp:
                content_type = resp.headers.get("Content-Type", "")
                if "application/json" not in content_type:
                    text = await resp.text()
                    raise Exception(f"Unexpected content-type: {content_type}\n{text}")
                data = await resp.json()

        ban_status = str(data.get("ban_status", "")).lower()
        if ban_status == "ban":
            await wait_msg.edit_text("😥 Account banned permanently")
        else:
            await wait_msg.edit_text("😊 Account not banned")

    except Exception as e:
        await wait_msg.edit_text(f"Error: {e}")

# /like командасы
async def like_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat = message.chat
    if chat.type not in ["group", "supergroup"]:
        return await message.reply_text("❗ This command only works in groups.")

    user = message.from_user
    if not await is_member(user.id, context):
        return await message.reply_text("Please join the required channel first.", reply_markup=join_button())

    args = context.args
    if len(args) != 2:
        return await message.reply_text("/like <region> <uid>")

    region, uid = args
    wait_msg = await message.reply_text("Sending likes, please wait...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(LIKE_API.format(uid=uid, region=region)) as resp:
                content_type = resp.headers.get("Content-Type", "")
                if "application/json" not in content_type:
                    text = await resp.text()
                    raise Exception(f"Unexpected content-type: {content_type}\n{text}")
                data = await resp.json()

        if data.get("LikesGivenByAPI") == 0:
            await wait_msg.edit_text("Player has reached max likes today.")
        else:
            text = (
                "✅ Likes Sent\n"
                f"Player Name: {data['PlayerNickname']}\n"
                f"UID: {data['UID']}\n"
                f"Likes Before: {data['LikesBeforeCommand']}\n"
                f"Likes Given: {data['LikesGivenByAPI']}\n"
                f"Likes After: {data['LikesAfterCommand']}"
            )
            await wait_msg.edit_text(text)

    except Exception as e:
        await wait_msg.edit_text(f"Error occurred: {e}")

# Ботту иштетүү
def main():
    logging.basicConfig(level=logging.INFO)
    app: Application = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler(["info", "Info"], info_command))
    app.add_handler(CommandHandler("check", check_handler))
    app.add_handler(CommandHandler("like", like_handler))
    print("🤖 Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
