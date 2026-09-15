import discord
from discord.ext import commands
from discord.ui import Select, View
from discord import app_commands
import asyncio
import io
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID", "0"))
TICKET_NUMBER = int(os.getenv("TICKET_NUMBER", "0"))
INACTIVITY_DAYS = int(os.getenv("INACTIVITY_DAYS", "7"))

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Add it to your .env file.")

auto_close_tasks = {}


class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒 Close Ticket",
        style=discord.ButtonStyle.red,
        custom_id="close_ticket_button"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel

        await interaction.response.send_message(
            "✅ Ticket will be closed in 5 seconds and transcript will be sent...",
            ephemeral=True
        )

        await asyncio.sleep(5)
        await close_ticket_channel(channel, reason="manual")


class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Purchase & Information",
                description="For purchases & information",
                emoji="🛒"
            ),
            discord.SelectOption(
                label="Technical Support",
                description="Technical support for your purchase",
                emoji="🛠️"
            ),
            discord.SelectOption(
                label="Upgrade & Renewal",
                description="Upgrade specs or extend service",
                emoji="🔄"
            ),
            discord.SelectOption(
                label="Refund & Complaint",
                description="Transaction issue or refund request",
                emoji="📄"
            )
        ]

        super().__init__(
            placeholder="Select your support...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        global TICKET_NUMBER

        guild = interaction.guild
        author = interaction.user
        category = guild.get_channel(TICKET_CATEGORY_ID)

        if not category:
            await interaction.response.send_message(
                "❌ Ticket category not found.",
                ephemeral=True
            )
            return

        # cek duplicate ticket
        for channel in category.text_channels:
            if channel.topic == str(author.id):
                await interaction.response.send_message(
                    f"❌ You already have an open ticket: {channel.mention}",
                    ephemeral=True
                )
                return

        TICKET_NUMBER += 1
        channel_name = f"ticket-{TICKET_NUMBER}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=False
            ),
            author: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                attach_files=True
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True
            )
        }

        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=str(author.id)
        )

        embed = discord.Embed(
            title="📩 Ticket Created",
            description=(
                f"Hello {author.mention}, your **{self.values[0]}** "
                f"ticket has been created.\n"
                f"To close this ticket, click the button below."
            ),
            color=discord.Color.green()
        )

        owner = guild.get_member(OWNER_ID)

        content = author.mention

        if owner:
            content += f" {owner.mention}"

        await channel.send(
        content=content,
        embed=embed,
        view=CloseTicketView(),
        allowed_mentions=discord.AllowedMentions(
         users=True,
         roles=False,
         everyone=False
    )
)

        await interaction.response.send_message(
            f"✅ Ticket created: {channel.mention}",
            ephemeral=True
        )

        schedule_auto_close(channel)


class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())


async def close_ticket_channel(channel, reason="manual"):
    try:
        messages = []

        async for msg in channel.history(limit=None, oldest_first=True):
            messages.append(
                f"[{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"{msg.author.name}: {msg.content}"
            )

        transcript_text = "\n".join(messages) if messages else "No messages."

        opener = None
        if channel.topic and channel.topic.isdigit():
            opener = channel.guild.get_member(int(channel.topic))

        if opener:
            try:
                file = discord.File(
                    fp=io.BytesIO(transcript_text.encode()),
                    filename="transcript.txt"
                )

                if reason == "inactive":
                    msg = (
                        f"Ticket `{channel.name}` otomatis ditutup "
                        f"karena tidak ada aktivitas selama {INACTIVITY_DAYS} hari."
                    )
                else:
                    msg = f"Berikut transcript ticket `{channel.name}`."

                await opener.send(msg, file=file)

            except Exception as e:
                print(f"Gagal kirim transcript: {e}")

        task = auto_close_tasks.pop(channel.id, None)
        if task:
            task.cancel()

        if channel.topic and channel.topic.isdigit():
            await channel.delete()

    except Exception as e:
        print(f"Close ticket error: {e}")


def schedule_auto_close(channel):
    old_task = auto_close_tasks.pop(channel.id, None)

    if old_task:
        old_task.cancel()

    auto_close_tasks[channel.id] = asyncio.create_task(
        auto_close_ticket(channel)
    )


async def auto_close_ticket(channel):
    try:
        await asyncio.sleep(INACTIVITY_DAYS * 24 * 60 * 60)

        # kalau channel udah ga ada
        if bot.get_channel(channel.id) is None:
            return

        # bukan ticket
        if channel.topic is None or not channel.topic.isdigit():
            return

        try:
            await channel.send(
                f"⏰ Ticket otomatis ditutup karena tidak ada aktivitas selama {INACTIVITY_DAYS} hari."
            )
        except:
            pass

        await close_ticket_channel(channel, reason="inactive")

    except asyncio.CancelledError:
        return
    except Exception as e:
        print(f"Auto close error: {e}")


@bot.event
async def on_ready():
    print(f"Bot ready: {bot.user}")
    print("Ticket system is running.")

    bot.add_view(CloseTicketView())

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(e)


@bot.event
async def on_message(message):
    if (
        message.guild
        and not message.author.bot
        and message.channel.category_id == TICKET_CATEGORY_ID
        and message.channel.topic is not None
        and message.channel.topic.isdigit()
    ):
        schedule_auto_close(message.channel)

    await bot.process_commands(message)


@bot.tree.command(
    name="ticket",
    description="Create ticket panel"
)
async def ticket(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message(
            "❌ You are not allowed to use this command.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="Support Ticket System",
        color=discord.Color.green()
    )

    embed.description = (
        "Select your support from the dropdown below to create a ticket."
    )

    await interaction.response.send_message(
        embed=embed,
        view=TicketView()
    )


bot.run(TOKEN)