import discord
from discord.ext import commands
import datetime
import json
import os

# ⚙️ Paramètres du bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 📁 Fichier où on va sauvegarder l'activité
ACTIVITY_FILE = "activity.json"
# 🔔 ID du salon où envoyer les logs
LOG_CHANNEL_ID = 1421820045964607548
# 👑 Ton ID Discord (exclusivité pour !logs)
OWNER_ID = 732823055008530462


# ------------------------------
# 📂 Gestion des données
# ------------------------------
def load_activity():
    if os.path.exists(ACTIVITY_FILE):
        with open(ACTIVITY_FILE, "r") as f:
            return json.load(f)
    return {}


def save_activity(data):
    with open(ACTIVITY_FILE, "w") as f:
        json.dump(data, f)


# ------------------------------
# 📌 Fonction centrale pour enregistrer et logger
# ------------------------------
async def update_activity(user_id: int, action: str, guild: discord.Guild):
    data = load_activity()
    history = data.get("history", [])
    timestamp = str(datetime.datetime.utcnow())
    history.append({"user": user_id, "action": action, "time": timestamp})

    # On garde que les 1000 dernières activités
    data["history"] = history[-1000:]
    data[str(user_id)] = timestamp
    save_activity(data)

    # ✅ Envoyer un log en embed
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        user = guild.get_member(user_id)
        if user:
            if action == "message":
                emoji, action_text = "✍️", "a envoyé un message"
            elif action == "réaction":
                emoji, action_text = "😀", "a réagi à un message"
            elif action == "vocal":
                emoji, action_text = "🎤", "a rejoint un vocal"
            else:
                emoji, action_text = "📌", "activité détectée"

            embed = discord.Embed(
                title=f"{emoji} Activité détectée",
                description=f"**{user.display_name}** {action_text}.",
                color=0xFF0000
            )
            embed.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/1225735168762052628/1421815161257332867/telechargement_1111.png"
            )
            embed.set_image(
                url="https://cdn.discordapp.com/attachments/1225735168762052628/1417518827108831232/ChatGPT_Image_1_juin_2025_23_09_50.png"
            )
            embed.set_footer(text=f"{datetime.datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')}")
            await channel.send(embed=embed)


# ------------------------------
# 🚀 Events
# ------------------------------
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await update_activity(message.author.id, "message", message.guild)
    await bot.process_commands(message)


@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    await update_activity(user.id, "réaction", reaction.message.guild)


@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    if after.channel is not None:
        await update_activity(member.id, "vocal", member.guild)


# ------------------------------
# ⚡ Commandes
# ------------------------------
@bot.command()
async def ping(ctx):
    embed = discord.Embed(
        title="🏓 Pong !",
        description="Ton bot est bien en ligne ✅",
        color=0xFF0000
    )
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/1225735168762052628/1421815161257332867/telechargement_1111.png"
    )
    embed.set_image(
        url="https://cdn.discordapp.com/attachments/1225735168762052628/1417518827108831232/ChatGPT_Image_1_juin_2025_23_09_50.png"
    )
    await ctx.send(embed=embed)


# 🔎 Commande : voir les membres inactifs (admins seulement)
@bot.command()
@commands.has_permissions(manage_guild=True)
async def inactifs(ctx, jours: int = 30):
    limite = datetime.datetime.utcnow() - datetime.timedelta(days=jours)
    data = load_activity()
    inactifs = []

    for member in ctx.guild.members:
        if member.bot:
            continue

        last_seen = data.get(str(member.id))
        if not last_seen:
            inactifs.append(f"❌ **{member.name}** – *jamais vu*")
        else:
            last_seen_date = datetime.datetime.fromisoformat(last_seen)
            if last_seen_date < limite:
                date_str = last_seen_date.strftime("%d/%m/%Y %H:%M UTC")
                inactifs.append(f"🔴 **{member.name}** – vu le *{date_str}*")

    if not inactifs:
        embed = discord.Embed(
            title="✅ Activité OK",
            description=f"Aucun membre inactif depuis {jours} jours.",
            color=0x00FF00
        )
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1225735168762052628/1421815161257332867/telechargement_1111.png"
        )
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/1225735168762052628/1417518827108831232/ChatGPT_Image_1_juin_2025_23_09_50.png"
        )
        return await ctx.send(embed=embed)

    # Pagination 15 membres par page
    chunk_size = 15
    pages = []
    for i in range(0, len(inactifs), chunk_size):
        description = "\n".join(inactifs[i:i+chunk_size])
        embed = discord.Embed(
            title=f"📋 Membres inactifs depuis {jours} jours ({len(inactifs)} trouvés)",
            description=description,
            color=0xFF0000
        )
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1225735168762052628/1421815161257332867/telechargement_1111.png"
        )
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/1225735168762052628/1417518827108831232/ChatGPT_Image_1_juin_2025_23_09_50.png"
        )
        embed.set_footer(text=f"Page {len(pages)+1}/{(len(inactifs)-1)//chunk_size+1}")
        pages.append(embed)

    class InactifsView(discord.ui.View):
        def __init__(self, pages):
            super().__init__(timeout=120)
            self.pages = pages
            self.index = 0

        @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary)
        async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.index > 0:
                self.index -= 1
                await interaction.response.edit_message(embed=self.pages[self.index], view=self)

        @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
        async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.index < len(self.pages) - 1:
                self.index += 1
                await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    view = InactifsView(pages)
    await ctx.send(embed=pages[0], view=view)


# 🔒 Commande réservée à toi : voir les derniers logs
@bot.command()
async def logs(ctx, limit: int = 20):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Tu n'as pas la permission d'utiliser cette commande.")

    data = load_activity()
    history = data.get("history", [])
    if not history:
        return await ctx.send("📭 Aucun log trouvé.")

    history = history[-limit:]
    description = ""
    for h in history:
        user = ctx.guild.get_member(h["user"])
        if not user:
            continue
        time_str = datetime.datetime.fromisoformat(h["time"]).strftime("%d/%m %H:%M UTC")

        if h["action"] == "message":
            emoji, txt = "✍️", "a envoyé un message"
        elif h["action"] == "réaction":
            emoji, txt = "😀", "a réagi à un message"
        elif h["action"] == "vocal":
            emoji, txt = "🎤", "a rejoint un vocal"
        else:
            emoji, txt = "📌", "activité détectée"

        description += f"{emoji} **{user.display_name}** {txt} — *{time_str}*\n"

    embed = discord.Embed(
        title=f"📜 Dernières activités ({len(history)})",
        description=description,
        color=0xFF0000
    )
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/1225735168762052628/1421815161257332867/telechargement_1111.png"
    )
    embed.set_image(
        url="https://cdn.discordapp.com/attachments/1225735168762052628/1417518827108831232/ChatGPT_Image_1_juin_2025_23_09_50.png"
    )
    embed.set_footer(text=f"Généré le {datetime.datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')}")
    await ctx.send(embed=embed)


# 🚀 Lancement
bot.run("MTI1MTE3MDIwOTQzNjQwMTY5Ng.GM2WJM.EoZAljyhLapN2eMzPTQD4BcuqIbPyUkHxjfvn0")
