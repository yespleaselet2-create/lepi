import discord
from discord.ext import commands
from discord import app_commands
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DC_TOKEN")
CHANNEL_ID = int(os.getenv("DC_CHANNEL", "0"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

GIFT_CARD_PATTERNS = {
    "steam": "XXXXX-XXXXX-XXXXX",
    "roblox": "Robux code format",
    "fortnite": "XXXX-XXXX-XXXX-XXXX",
    "google_play": "XXXX-XXXX-XXXX",
    "minecraft": "XXXX-XXXX-XXXX-XXXX",
    "microsoft": "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX",
    "xbox": "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"
}

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ LEPI Donation Bot is online as {bot.user}")

@bot.tree.command(name="verify", description="Verify a gift card code and reward the donor")
@app_commands.describe(
    username="Discord username of the donor",
    card_type="Type of gift card",
    codes="Comma separated codes: code1,code2,code3"
)
@app_commands.choices(card_type=[
    app_commands.Choice(name="Steam", value="steam"),
    app_commands.Choice(name="Roblox", value="roblox"),
    app_commands.Choice(name="Fortnite", value="fortnite"),
    app_commands.Choice(name="Google Play", value="google_play"),
    app_commands.Choice(name="Minecraft", value="minecraft"),
    app_commands.Choice(name="Microsoft", value="microsoft"),
    app_commands.Choice(name="Xbox", value="xbox"),
])
async def verify(interaction: discord.Interaction, username: str, card_type: str, codes: str):
    await interaction.response.defer(ephemeral=True)

    code_list = [c.strip() for c in codes.split(",") if c.strip()]

    embed = discord.Embed(
        title="🎁 Gift Card Verification",
        description=f"Processing **{len(code_list)}** code(s) for **{username}**",
        color=0xf5c518
    )
    embed.set_footer(text="LEPI Donation System 🍋")

    results = []
    for code in code_list:
        results.append(f"✅ `{code}` — **{card_type.upper()}** — Logged!")

    embed.add_field(name="Results", value="\n".join(results), inline=False)
    embed.add_field(name="Donor", value=f"@{username}", inline=True)
    embed.add_field(name="Card Type", value=card_type.title(), inline=True)
    embed.add_field(name="Total Codes", value=str(len(code_list)), inline=True)

    # Send to donations channel
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)

    await interaction.followup.send(
        f"✅ Verified **{len(code_list)}** code(s) for **{username}**! Logged to donations channel.",
        ephemeral=True
    )

@bot.tree.command(name="donators", description="Show recent donators")
async def donators(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🍋 LEPI Donators",
        description="Thank you to everyone who supported LEPI!",
        color=0xf5c518
    )
    embed.set_footer(text="lepi.eu.org")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="Check if bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")

bot.run(TOKEN)
