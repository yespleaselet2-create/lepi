import os, json, random, uuid, re, time, io, math
from fastapi import FastAPI, Query, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import anthropic
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="LEPI", description="Free APIs by LEPI 🍋")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API"))

# In-memory captcha store
captcha_store = {}

# ── AI HELPERS ────────────────────────────────────────────────
def ai(prompt: str, system: str = "") -> str:
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=system or "Reply only with exactly what is asked. No extra text.",
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text.strip()
    except Exception as e:
        return f"error: {str(e)}"

def ai_json(prompt: str) -> dict:
    try:
        raw = ai(prompt + " Reply ONLY with valid JSON. No markdown. No explanation.")
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except:
        return {"error": "AI failed to return valid JSON"}

# ═══════════════════════════════════════════════════════
# FUN APIS
# ═══════════════════════════════════════════════════════

@app.get("/api/joke")
async def joke():
    data = ai_json('Create one original funny joke. JSON: {"setup":"...","punchline":"..."}')
    return {"success": True, "joke": data}

@app.get("/api/roast")
async def roast():
    text = ai("Write one savage but funny roast. Just the roast, nothing else.")
    return {"success": True, "roast": text}

@app.get("/api/trivia")
async def trivia(category: str = ""):
    cat = f" about {category}" if category else ""
    data = ai_json(f'Create a trivia question{cat}. JSON: {{"question":"...","options":["a","b","c","d"],"answer":"...","category":"..."}}')
    return {"success": True, "trivia": data}

@app.get("/api/fakeperson")
async def fakeperson():
    data = ai_json('Generate a realistic fake person. JSON: {"name":"...","age":25,"gender":"...","email":"...","phone":"...","city":"...","country":"...","job":"...","hobby":"...","username":"...","bio":"..."}')
    return {"success": True, "person": data}

@app.get("/api/rps")
async def rps(pick: str = ""):
    choices = ["rock", "paper", "scissors"]
    bot = random.choice(choices)
    pick = pick.lower().strip()
    if pick not in choices:
        return {"success": False, "error": "pick must be rock, paper, or scissors"}
    if pick == bot: result = "tie"
    elif (pick=="rock" and bot=="scissors") or (pick=="paper" and bot=="rock") or (pick=="scissors" and bot=="paper"): result = "win"
    else: result = "lose"
    return {"success": True, "your_pick": pick, "bot_pick": bot, "result": result}

@app.get("/api/coinflip")
async def coinflip():
    return {"success": True, "result": random.choice(["heads", "tails"])}

@app.get("/api/dice")
async def dice(sides: int = 6):
    if sides < 2 or sides > 1000:
        return {"success": False, "error": "sides must be 2-1000"}
    return {"success": True, "sides": sides, "roll": random.randint(1, sides)}

@app.get("/api/8ball")
async def eightball(q: str = ""):
    question = q or "Will I be lucky?"
    text = ai(f'Someone asked a magic 8 ball: "{question}". Give a mystical creative 8 ball response. Just the answer.')
    return {"success": True, "question": question, "answer": text}

@app.get("/api/wyr")
async def wyr():
    data = ai_json('Create a creative "Would You Rather" question. JSON: {"option_a":"...","option_b":"..."}')
    return {"success": True, "would_you_rather": data}

@app.get("/api/compliment")
async def compliment():
    text = ai("Write one genuine heartfelt compliment. Just the compliment.")
    return {"success": True, "compliment": text}

@app.get("/api/fact")
async def fact():
    text = ai("Give me one surprising and interesting fact. Just the fact.")
    return {"success": True, "fact": text}

@app.get("/api/quote")
async def quote():
    data = ai_json('Give me an original inspirational or funny quote. JSON: {"quote":"...","author":"..."}')
    return {"success": True, "quote": data}

# ═══════════════════════════════════════════════════════
# UTILITY APIS
# ═══════════════════════════════════════════════════════

@app.get("/api/password")
async def password(length: int = 16, symbols: bool = True, numbers: bool = True):
    import string
    chars = string.ascii_letters
    if numbers: chars += string.digits
    if symbols: chars += "!@#$%^&*"
    if length < 4 or length > 128:
        return {"success": False, "error": "length must be 4-128"}
    pwd = "".join(random.choices(chars, k=length))
    return {"success": True, "password": pwd, "length": length}

@app.get("/api/username")
async def username():
    data = ai_json('Generate 5 creative unique usernames. JSON: {"usernames":["...","...","...","...","..."]}')
    return {"success": True, "usernames": data.get("usernames", [])}

@app.get("/api/color")
async def color():
    r, g, b = random.randint(0,255), random.randint(0,255), random.randint(0,255)
    hex_color = f"#{r:02x}{g:02x}{b:02x}"
    return {"success": True, "hex": hex_color, "rgb": {"r": r, "g": g, "b": b}}

@app.get("/api/uuid")
async def generate_uuid():
    return {"success": True, "uuid": str(uuid.uuid4())}

@app.get("/api/base64")
async def base64_encode(text: str = "", decode: str = ""):
    import base64
    if text:
        encoded = base64.b64encode(text.encode()).decode()
        return {"success": True, "action": "encode", "input": text, "result": encoded}
    elif decode:
        try:
            decoded = base64.b64decode(decode.encode()).decode()
            return {"success": True, "action": "decode", "input": decode, "result": decoded}
        except:
            return {"success": False, "error": "Invalid base64 string"}
    return {"success": False, "error": "Provide text= or decode="}

@app.get("/api/wordcount")
async def wordcount(text: str = ""):
    if not text:
        return {"success": False, "error": "Provide text="}
    words = len(text.split())
    chars = len(text)
    chars_no_space = len(text.replace(" ", ""))
    sentences = text.count(".") + text.count("!") + text.count("?")
    return {"success": True, "words": words, "characters": chars, "characters_no_spaces": chars_no_space, "sentences": sentences}

@app.get("/api/timestamp")
async def timestamp():
    import datetime
    now = datetime.datetime.utcnow()
    return {
        "success": True,
        "unix": int(time.time()),
        "utc": now.strftime("%Y-%m-%d %H:%M:%S"),
        "iso": now.isoformat() + "Z",
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S")
    }

@app.get("/api/ip")
async def get_ip(request: Request):
    ip = request.headers.get("x-forwarded-for", request.client.host)
    return {"success": True, "ip": ip}

# ═══════════════════════════════════════════════════════
# DISCORD BOT HELPER APIS
# ═══════════════════════════════════════════════════════

@app.get("/api/discord/snowflake")
async def snowflake(id: str = ""):
    if not id or not id.isdigit():
        return {"success": False, "error": "Provide a valid Discord ID"}
    snowflake_int = int(id)
    timestamp_ms = ((snowflake_int >> 22) + 1420070400000)
    import datetime
    created_at = datetime.datetime.utcfromtimestamp(timestamp_ms / 1000)
    return {"success": True, "id": id, "created_at": str(created_at), "timestamp_ms": timestamp_ms}

@app.get("/api/discord/timestamp")
async def discord_timestamp(date: str = ""):
    if not date:
        unix = int(time.time())
    else:
        try:
            import datetime
            dt = datetime.datetime.fromisoformat(date)
            unix = int(dt.timestamp())
        except:
            return {"success": False, "error": "Invalid date format. Use ISO format: 2024-01-01T00:00:00"}
    return {
        "success": True,
        "unix": unix,
        "formats": {
            "short_time": f"<t:{unix}:t>",
            "long_time": f"<t:{unix}:T>",
            "short_date": f"<t:{unix}:d>",
            "long_date": f"<t:{unix}:D>",
            "short_datetime": f"<t:{unix}:f>",
            "long_datetime": f"<t:{unix}:F>",
            "relative": f"<t:{unix}:R>"
        }
    }

@app.get("/api/discord/colorconvert")
async def color_convert(hex: str = ""):
    hex = hex.lstrip("#")
    if len(hex) != 6:
        return {"success": False, "error": "Provide a valid 6-digit hex color"}
    try:
        decimal = int(hex, 16)
        r = int(hex[0:2], 16)
        g = int(hex[2:4], 16)
        b = int(hex[4:6], 16)
        return {"success": True, "hex": f"#{hex}", "decimal": decimal, "rgb": {"r": r, "g": g, "b": b}}
    except:
        return {"success": False, "error": "Invalid hex color"}

@app.get("/api/discord/permissions")
async def permissions(value: int = 0):
    perms = {
        "CREATE_INSTANT_INVITE": 1 << 0, "KICK_MEMBERS": 1 << 1, "BAN_MEMBERS": 1 << 2,
        "ADMINISTRATOR": 1 << 3, "MANAGE_CHANNELS": 1 << 4, "MANAGE_GUILD": 1 << 5,
        "ADD_REACTIONS": 1 << 6, "VIEW_AUDIT_LOG": 1 << 7, "SEND_MESSAGES": 1 << 11,
        "MANAGE_MESSAGES": 1 << 13, "EMBED_LINKS": 1 << 14, "ATTACH_FILES": 1 << 15,
        "READ_MESSAGE_HISTORY": 1 << 16, "MENTION_EVERYONE": 1 << 17, "CONNECT": 1 << 20,
        "SPEAK": 1 << 21, "MUTE_MEMBERS": 1 << 22, "DEAFEN_MEMBERS": 1 << 23,
        "MOVE_MEMBERS": 1 << 24, "MANAGE_ROLES": 1 << 28, "MANAGE_WEBHOOKS": 1 << 29,
        "MANAGE_EMOJIS": 1 << 30
    }
    granted = [name for name, bit in perms.items() if value & bit]
    return {"success": True, "value": value, "granted_permissions": granted}

@app.get("/api/discord/embedbuilder")
async def embed_builder(title: str = "", description: str = "", color: str = "5865F2", footer: str = ""):
    hex_clean = color.lstrip("#")
    try: decimal_color = int(hex_clean, 16)
    except: decimal_color = 5865F2
    embed = {"embeds": [{"title": title, "description": description, "color": decimal_color, "footer": {"text": footer} if footer else None}]}
    embed["embeds"][0] = {k: v for k, v in embed["embeds"][0].items() if v is not None}
    return {"success": True, "embed_json": embed}

# ═══════════════════════════════════════════════════════
# BOT HELPER APIS
# ═══════════════════════════════════════════════════════

@app.get("/api/bot/useragent")
async def random_useragent():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    ]
    agent = random.choice(agents)
    return {"success": True, "user_agent": agent}

@app.get("/api/bot/profanity")
async def profanity_check(text: str = ""):
    if not text:
        return {"success": False, "error": "Provide text="}
    data = ai_json(f'Check if this text has profanity: "{text}". JSON: {{"has_profanity": true/false, "censored": "censored version", "words_found": ["list of bad words found or empty"]}}')
    return {"success": True, "original": text, **data}

@app.get("/api/bot/antispam")
async def antispam(text: str = ""):
    if not text:
        return {"success": False, "error": "Provide text="}
    data = ai_json(f'Analyze if this text is spam: "{text}". JSON: {{"is_spam": true/false, "confidence": "high/medium/low", "reason": "..."}}')
    return {"success": True, "text": text, **data}

@app.get("/api/bot/tokengen")
async def token_gen(length: int = 32):
    import secrets, string
    if length < 8 or length > 256:
        return {"success": False, "error": "length must be 8-256"}
    token = secrets.token_urlsafe(length)[:length]
    return {"success": True, "token": token, "length": len(token)}

@app.get("/api/bot/regex")
async def regex_test(pattern: str = "", text: str = ""):
    if not pattern or not text:
        return {"success": False, "error": "Provide pattern= and text="}
    try:
        matches = re.findall(pattern, text)
        is_match = bool(re.search(pattern, text))
        return {"success": True, "pattern": pattern, "text": text, "is_match": is_match, "matches": matches, "match_count": len(matches)}
    except re.error as e:
        return {"success": False, "error": f"Invalid regex: {str(e)}"}

@app.get("/api/bot/json")
async def json_format(text: str = "", minify: bool = False):
    if not text:
        return {"success": False, "error": "Provide text="}
    try:
        parsed = json.loads(text)
        if minify:
            result = json.dumps(parsed, separators=(",", ":"))
        else:
            result = json.dumps(parsed, indent=2)
        return {"success": True, "result": result, "valid": True}
    except:
        return {"success": False, "valid": False, "error": "Invalid JSON"}

# ═══════════════════════════════════════════════════════
# ROBLOX APIS
# ═══════════════════════════════════════════════════════

@app.get("/api/roblox/username")
async def roblox_username():
    data = ai_json('Generate 5 creative Roblox-style usernames (no spaces, 3-20 chars). JSON: {"usernames":["...","...","...","...","..."]}')
    return {"success": True, "usernames": data.get("usernames", [])}

@app.get("/api/roblox/user")
async def roblox_user(id: str = ""):
    if not id:
        return {"success": False, "error": "Provide id="}
    try:
        import requests as req
        r = req.get(f"https://users.roblox.com/v1/users/{id}", timeout=5)
        if r.status_code == 200:
            data = r.json()
            return {"success": True, "user": {"id": data.get("id"), "name": data.get("name"), "display_name": data.get("displayName"), "description": data.get("description"), "created": data.get("created")}}
        return {"success": False, "error": "User not found"}
    except:
        return {"success": False, "error": "Failed to fetch Roblox API"}

# ═══════════════════════════════════════════════════════
# CAPTCHA APIS
# ═══════════════════════════════════════════════════════

@app.get("/api/captcha/math")
async def captcha_math():
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    ops = ["+", "-", "*"]
    op = random.choice(ops)
    if op == "+": answer = a + b
    elif op == "-": answer = a - b
    else: answer = a * b
    cid = str(uuid.uuid4())[:8]
    captcha_store[cid] = {"answer": str(answer), "expires": time.time() + 300}
    return {"success": True, "id": cid, "question": f"What is {a} {op} {b}?", "expires_in": 300}

@app.get("/api/captcha/text")
async def captcha_text():
    import string, random
    chars = string.ascii_uppercase + string.digits
    text = "".join(random.choices(chars, k=6))
    cid = str(uuid.uuid4())[:8]
    captcha_store[cid] = {"answer": text, "expires": time.time() + 300}
    # Generate image
    img = Image.new("RGB", (200, 70), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    # Add noise lines
    for _ in range(8):
        x1, y1 = random.randint(0,200), random.randint(0,70)
        x2, y2 = random.randint(0,200), random.randint(0,70)
        draw.line([(x1,y1),(x2,y2)], fill=(random.randint(100,200), random.randint(100,200), random.randint(100,200)), width=2)
    # Draw text with noise
    for i, char in enumerate(text):
        x = 15 + i * 28 + random.randint(-3, 3)
        y = random.randint(10, 25)
        r, g, b = random.randint(180,255), random.randint(180,255), random.randint(180,255)
        draw.text((x, y), char, fill=(r, g, b))
    # Add dots
    for _ in range(200):
        x, y = random.randint(0,200), random.randint(0,70)
        draw.point((x,y), fill=(random.randint(50,150), random.randint(50,150), random.randint(50,150)))
    img = img.filter(ImageFilter.SMOOTH)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png", headers={"X-Captcha-ID": cid})

@app.get("/api/captcha/emoji")
async def captcha_emoji():
    all_emojis = ["😀","😎","🔥","⭐","🍕","🎮","🐱","🌙","🎯","💎","🚀","🍋","🎲","🌈","🦊"]
    target = random.choice(all_emojis)
    decoys = random.sample([e for e in all_emojis if e != target], 4)
    options = decoys + [target]
    random.shuffle(options)
    cid = str(uuid.uuid4())[:8]
    captcha_store[cid] = {"answer": target, "expires": time.time() + 300}
    return {"success": True, "id": cid, "instruction": f"Click the {target} emoji", "target": target, "options": options, "expires_in": 300}

@app.get("/api/captcha/checkbox")
async def captcha_checkbox():
    cid = str(uuid.uuid4())[:8]
    captcha_store[cid] = {"answer": "checked", "expires": time.time() + 300}
    return {"success": True, "id": cid, "instruction": "Check the box to verify you are human", "expires_in": 300}

@app.post("/api/captcha/verify")
async def captcha_verify(request: Request):
    try:
        body = await request.json()
        cid = body.get("id", "")
        answer = str(body.get("answer", "")).strip().upper()
    except:
        return {"success": False, "error": "Invalid request body"}
    if cid not in captcha_store:
        return {"success": False, "error": "Invalid or expired captcha ID"}
    stored = captcha_store[cid]
    if time.time() > stored["expires"]:
        del captcha_store[cid]
        return {"success": False, "error": "Captcha expired"}
    correct = str(stored["answer"]).upper()
    if answer == correct:
        del captcha_store[cid]
        return {"success": True, "message": "Captcha solved correctly!"}
    return {"success": False, "error": "Wrong answer"}

# ═══════════════════════════════════════════════════════
# DONATION FORM
# ═══════════════════════════════════════════════════════

@app.post("/api/donate")
async def donate(
    username: str = Form(...),
    card_type: str = Form(...),
    code: str = Form(...),
    email: str = Form("")
):
    import aiohttp, asyncio
    channel_id = os.getenv("DC_CHANNEL")
    dc_token = os.getenv("DC_TOKEN")
    if not channel_id or not dc_token:
        return JSONResponse({"success": False, "error": "Bot not configured"})
    # Send to Discord
    message = f"🎁 **NEW DONATION!**\n👤 Username: `{username}`\n🎮 Card Type: `{card_type}`\n🔑 Code: `||{code}||`\n📧 Email: `{email or 'not provided'}`"
    try:
        import requests as req
        req.post(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            headers={"Authorization": f"Bot {dc_token}", "Content-Type": "application/json"},
            json={"content": message}
        )
    except:
        pass
    return JSONResponse({"success": True})

# ═══════════════════════════════════════════════════════
# SERVE FRONTEND
# ═══════════════════════════════════════════════════════

app.mount("/", StaticFiles(directory="public", html=True), name="static")
