import asyncio
from discord.channel import TextChannel
from discord.ext.commands import Cog, Bot
from discord import Embed, Activity, ActivityType
from discord.member import Member, VoiceState
from discord.message import Message
from discord.raw_models import RawReactionActionEvent
from config import config
from random import randint
from time import ctime
from database import db

class EventHandler(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot 

    # Event Handlers
    @Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        print("PCSG MOD v2 IS UP AND READY!")
        activity = Activity(name=f"{config['constants']['prefix']}MOD POWA", type=ActivityType.playing)
        await self.bot.change_presence(activity=activity)
        await db.setup()


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

        embed = Embed(title="!!!", description=f"{member.mention} has just joined the server", color=randint(0, 0xffffff))
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
        
        await self.update_member_count(member)

    @Cog.listener()
    async def on_member_remove(self, member:Member):
        join = member.guild.get_channel(config['channels']['join-logs'])

        embed = Embed(title="'-'", description=f"{member} has just left the server", color=randint(0, 0xffffff))
        if join:
            await join.send(embed=embed)

        await self.update_member_count(member)

    @Cog.listener()
    async def on_member_ban(self, member:Member):
        join = member.guild.get_channel(config['channels']['join-logs'])

        embed = Embed(title="BANNED!!!", description=f"{member} with id {member.id} has been banned.")
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
    async def on_raw_reaction_add(self, payload:RawReactionActionEvent):
        await self.handle_reaction(payload)

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload:RawReactionActionEvent):
        await self.handle_reaction(payload)
    
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
            changed = "status"
        elif before.nick != after.nick:
            changed = "nick"
        elif before.roles != after.roles:
            changed = "roles"
        elif before.pending != after.pending:
            changed = "pending"
        else: return False

        embed.description = f"{before.name}'s {changed} has been changed"
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
            name = member_count_channel.name.split(": ")[0]
            try:
                await member_count_channel.edit(name=f"{name}: {sum(not user.bot for user in member.guild.members)}")
            except:
                pass

def setup(bot: Bot):
    bot.add_cog(EventHandler(bot))