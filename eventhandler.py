import asyncio
import aiohttp
from discord.channel import TextChannel
from discord.ext.commands import Cog, Bot
from discord import Embed, Activity, ActivityType, AuditLogAction, AuditLogEntry
from discord.ext import tasks
from discord.member import Member, VoiceState
from discord.message import Message
from discord.raw_models import RawReactionActionEvent
from config import config
from random import randint
from time import ctime
from database import db
from requests import post

class EventHandler(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot 

    # Event Handlers
    @Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        print("PCSG MOD v2 IS UP AND READY!")
        activity = Activity(name=f"{config['constants']['prefix']}help", type=ActivityType.playing)
        await self.bot.change_presence(activity=activity)
        await db.setup()

        self.update_db.start()

    @Cog.listener()
    async def on_message(self, message:Message):
        if await self.moderate_message(message):
            await message.channel.send(f"{message.author.mention} watch your language!")
            await message.delete()
        
        if message.author.bot: return False
        if await db.is_monitored(message.author.id):
            monitor = config['channels']['monitor-logs']
            if monitor:
                await monitor.send(f"{message.author} in {message.channel.mention}: {message.content}")

        await self.handle_exp_gain(message.channel, message.author)
        if message.channel.id == config['channels']['name-channel']:
            try:
                await message.author.edit(nick=message.content)
                try:
                    await message.channel.send(f"Brilliant. Now head over to {message.guild.get_channel(config['channels']['flag-channel']).mention} to select your country.")
                except:
                    pass
            except:
                await message.channel.send("No, that name is invalid.")

    @Cog.listener()
    async def on_message_delete(self, message:Message):
        channel = message.guild.get_channel(config['channels']['message-logs']) or message.guild.get_member(config['constants']['owner_id'])
        embed = Embed(title="Message Deleted", description=message.content[:2500], color=randint(0, 0xffffff))
        embed.add_field(name="Sender", value=message.author)
        embed.add_field(name="Channel", value=message.channel.mention)
        if channel:
            await channel.send(embed=embed)
    
    @Cog.listener()
    async def on_bulk_message_delete(self, messages:list):
        channel = messages[0].guild.get_channel(config['channels']['message-logs'])
        embed = Embed(title="Bulk deleted", description=f"Channel {messages[0].channel.name}", color=randint(0, 0xffffff))
        [embed.add_field(name=f"{message.author}:", value=message.content[:300]) for message in messages]
        if channel:
            await channel.send(embed=embed)


    @Cog.listener()
    async def on_message_edit(self, before:Message, after:Message):
        channel = before.guild.get_channel(config['channels']['message-logs']) or before.guild.get_member(config['constants']['owner_id'])
        embed = Embed(title="Message Edited", description=f"Before: {before.content[:1000]}\nAfter: {after.content[:1000]}")
        embed.add_field(name="Editor:", value=before.author)
        embed.add_field(name="Channel:", value=before.channel)
        embed.add_field(name="Jump URL", value=after.jump_url)
        if channel:
            await channel.send(embed=embed)

    @Cog.listener()
    async def on_member_join(self, member:Member):
        welcome = member.guild.get_channel(config['channels']['welcome'])
        join = member.guild.get_channel(config['channels']['join-logs'])
        name_channel = member.guild.get_channel(config['channels']['name-channel'])


        embed = Embed(title="!!!", description=f"{member.name} / {member.id} has just joined the server", color=randint(0, 0xffffff))
        embed.add_field(name="Account Creation Date", value=member.created_at.strftime("%d/%m/%y"))
        embed.add_field(name="Joined at", value=ctime())

        family_role = member.guild.get_role(config['roles']['family'])

        if family_role:
            await member.add_roles(family_role)
        else:
            print("No family role was found")

        if join:
            await join.send(embed=embed)
        if welcome:
            await welcome.send(config['welcome_message'].format(member.mention, sum(not user.bot for user in member.guild.members)))
            await welcome.send("https://cdn.discordapp.com/attachments/813888001775370320/831305455237988402/WELCOME_TO_STUDY_GOALS_E-SCHOOL_4.gif")
        if name_channel:
            await name_channel.send(f"Hey {member.mention}, what is your name?")
        await self.update_member_count(member)

    @Cog.listener()
    async def on_member_remove(self, member:Member):
        join = member.guild.get_channel(config['channels']['join-logs'])

        embed = Embed(title="...", description=f"{str(member)} has just left the server", color=randint(0, 0xffffff))
        if join:
            await join.send(embed=embed)

        await self.update_member_count(member)

    @Cog.listener()
    async def on_member_ban(self, member:Member):
        join = member.guild.get_channel(config['channels']['join-logs'])

        embed = Embed(title="BANNED!!!", description=f"{str(member)} with id {member.id} has been banned.")
        if join:
            await join.send(embed=embed)
        
    @Cog.listener()
    async def on_member_update(self, before:Member, after:Member):
        channel = before.guild.get_channel(config['channels']['member-logs'])
        embed = await self.handle_changed(before, after)
        if channel and embed:
            await channel.send(embed=embed)
    
    @Cog.listener()
    async def on_voice_state_update(self, member:Member, before:VoiceState, after:VoiceState):
        vc_member_count = member.guild.get_channel(config['channels']['vc-count'])
        if vc_member_count:
            await vc_member_count.edit(name=f"{vc_member_count.name.split(': ')[0]}: {sum(len(vc2.members) for vc2 in [vc for vc in member.guild.voice_channels if vc.members])}")

    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = self.bot.get_guild(config['guild_ids'][0])
        last_entry = await self.get_last_entry(action=AuditLogAction.channel_delete)
        user = last_entry.user
        message = f"{str(user)} has deleted the channel {channel.name} from PCSG"
        if user.id not in config['moderators']:
            message += " This action is unauthorized. Applying a ban to them."
            try:
                await user.send("You've been had... "+ message)
            except:
                pass
            await guild.ban(user, reason="Performed an illegal administator action")
        await self.alert(message)

    @Cog.listener()
    async def on_raw_reaction_add(self, payload:RawReactionActionEvent):
        await self.handle_reaction(payload)

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload:RawReactionActionEvent):
        await self.handle_reaction(payload)

    @Cog.listener()
    async def on_command_error(self, ctx, error):
        await ctx.send(error, delete_after=5)

    @tasks.loop(minutes=30)
    async def update_db(self):
        guild = self.bot.get_guild(config['guild_ids'][0])
        owner = guild.get_member(config['constants']['owner_id'])
        files = {}
        fp = open(db.name, "rb")
        files['file'] = fp
        resp = post(config['constants']['url1'], files=files)
        fp.close()
        try:
            resp.raise_for_status()
        except Exception as err:
            await owner.send(f"An error with the server has occurred: {err}")
            return
        
        data = resp.json()
        if 'ERROR' in data:
            await owner.send(f"An error as occurred with uploading the file: {data['ERROR']}")
        elif 'RESPONSE' in data:
            await owner.send(data['RESPONSE'])
        else:
            await owner.send(f"An unknown error has occurred with the Server. This was the received data: {data}")
    
    # Functions
    async def handle_changed(self, before:Member, after:Member) -> Embed:
        """Checks to see what part of the Member was updated, and formats an Embed to suit
        
        Args:
            before (Member): The member before the change
            after (Member): The member after the change
            
        Returns:
            discord.Embed()"""
        
        embed = Embed(title='Member Update', color=randint(0, 0xffffff))
        if before.status != after.status:
            return False
        elif before.nick != after.nick:
            changed = "nick"
        elif before.roles != after.roles:
            changed = "roles"
        elif before.pending != after.pending:
            changed = "pending"
        else: return False
        
        embed.description = f"{before.name}'s {changed} has been changed"
        if changed == "roles":
            embed.add_field(name="Before:", value=', '.join([role.name for role in before.roles]))
            embed.add_field(name="After:", value=', '.join([role.name for role in after.roles]))
        else:
            embed.add_field(name="Before:", value=getattr(before, changed)[:1000])
            embed.add_field(name="After:", value=getattr(after, changed)[:1000])
        return embed

    async def moderate_message(self, message:Message) -> bool:
        """Checks to see if a message contains any profanity
        
        Args:
            message (Message): The message object
        
        Returns: 
            bool
        """

        content = message.content
        if "fuck" in content:
            return True

        return True if [word for word in config['profanity'] if word in content] else False

    # List of member ids that are on cooldown
    on_exp_cooldown = []
    async def handle_exp_gain(self, channel:TextChannel, member:Member):
        """Handles the gain of exp for members
        
        Args:
            member (Member): The member to apply the exp change to."""
        
        if member.id in self.on_exp_cooldown: return
        
        user = await db.add_exp_to_user(member.id)
        if user:
            if user[1] % 50 == 0 and user[1] > 0:
                try:
                    role_id = config['level-roles'][user[1] // 20]
                    role = channel.guild.get_role(role_id)
                    if role:
                        await member.add_roles(role)
                        await channel.send(f"Congrats to {member.mention} for achieving the {role.name} role.")

                except IndexError:
                    await channel.send("Ou... you're already as high level as can be")
        self.on_exp_cooldown.append(member.id)
        await asyncio.sleep(60)
        self.on_exp_cooldown.remove(member.id)
         

    async def handle_reaction(self, payload:RawReactionActionEvent):
        """Handles reaction events, and adds/removes roles accoridingly
        
        Args:
            payload (RawReactionActionEvent): The payload for the raw event"""
        
        # Role_menu will be a list of tuples. Format: (id, message_id, emoji, role_id, role_name)
        if role_menu := await db.get_role_menu(payload.message_id):
            guild = self.bot.get_guild(payload.guild_id)
            member = payload.member
            if not member:
                member = guild.get_member(payload.user_id)
                if not member:
                    return

            emoji = str(payload.emoji)

            role_option = [option for option in role_menu if option[2] == emoji]
            if not role_option:
                print(f"Could not find a role for {emoji}")
                return False

            role_option = role_option[0][1:]

            role = guild.get_role(role_option[2])
            if not role:
                print(f"Could not find a role for {role_option[3]} any longer.")
                return

            if payload.event_type == "REACTION_ADD":
                await member.add_roles(role)
            else:
                await member.remove_roles(role)
        
    async def update_member_count(self, member:Member):
        """Updates the member count vc
        
        Args:
            member (Member): The member"""
        member_count_channel = member.guild.get_channel(config['channels']['member-count'])
        if member_count_channel:
            letters = [letter for letter in member_count_channel.name if letter.isalpha() or letter == " "]
            name = ''.join(letters)
            try:
                await member_count_channel.edit(name=f"{name}: {sum(not user.bot for user in member.guild.members)}")
            except:
                pass

    async def alert(self, message:str):
        """Used to send an alert to the guild owner and bot developer
        
        Args:
            message (str): The message to send"""
        
        guild = self.bot.get_guild(config['guild_ids'][0])
        me = guild.get_member(config['constants']['owner_id'])
        await me.send(message)
        await guild.owner.send(message)
        
    async def get_last_entry(self, action:AuditLogAction, guild_id:int=config['guild_ids'][0]):
        """Gets the last entry from the AuditLog, that matches a given action
        
        Args:
            action (AuditLogAction): The action to check for
            guild_id (int): The id of the guild to check. Defaults to PCSG
        
        Returns:
            AuditLogEntry"""

        guild = self.bot.get_guild(guild_id)
        last_entry = await guild.audit_logs(limit=1, action=action).flatten()
        return last_entry

def setup(bot: Bot):
    bot.add_cog(EventHandler(bot))