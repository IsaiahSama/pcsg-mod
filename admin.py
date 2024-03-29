import asyncio
from os import path
from requests import post
from discord.ext.commands import Cog, Bot, command, has_guild_permissions
import discord
from discord.ext.commands.context import Context
from discord.permissions import PermissionOverwrite
from database import db
from config import config

class Admin(Cog):
    def __init__(self, bot: Bot):
        """Class where all ADMIN commands will be located"""
        self.bot = bot
        

    @command(name="kick", brief="Kicks a user", help="Used to kick a user from the server", usage="@member reason")
    @has_guild_permissions(kick_members=True)
    async def kick(self, ctx: Context, member:discord.Member, *, reason:str):
        try:
            await member.send(f"You have been kicked from {ctx.guild.name} by {ctx.author}. Reason: {reason}")
        except:
            pass 
        await member.kick(reason=reason)
        await ctx.send(f"{member} has been kicked from the server by {ctx.author}. Reason: {reason}")

    @command(name="ban", brief="Bans a user from the server", help="Used to ban a user from the server", usage="@user|user_id reason")
    @has_guild_permissions(ban_members=True)
    async def ban(self, ctx:Context, user:discord.User, *, reason:str):
        try:
            await user.send(f"You have been banned from PCSG. Reason: {reason}")
        except:
            pass 
        await ctx.guild.ban(user, reason=reason)
        await ctx.send(f"{user} has been banned by {ctx.author}. Reason: {reason}")

    @command(name="mute", brief="Mutes a user from the server for a given time", help="Prevents a user from speaking in the server for a given duration.", usage="@member time_in_minutes reason")
    @has_guild_permissions(manage_messages=True)
    async def mute(self, ctx:Context, member:discord.Member, timeout:int, *, reason:str):
        muted_role = discord.utils.get(ctx.guild.roles, name="E-Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="E-Muted")
            [await channel.edit(overwrites=channel.overwrites.update({muted_role: PermissionOverwrite(send_messages=False)})) for channel in ctx.guild.text_channels]
        
        await db.mute_user(member.id, [role.id for role in member.roles])
        await member.edit(roles=muted_role, reason=reason)
        await ctx.send(f"{member.mention} has been muted by {ctx.author}. Reason: {reason}")
        await asyncio.sleep(timeout * 60)
        muted_member = await db.get_and_remove_muted_user(member.id)
        if muted_member:
            role_ids = [(int(role_id)) for role_id in muted_member[1].split(", ")]
            roles = [ctx.guild.get_role(role_id) for role_id in role_ids]
            await member.edit(roles=[role for role in roles if role])
    
    @command(name="unmute", brief="Unmutes a muted user", help="Used to unmute someone that has been muted.", usage="@member")
    @has_guild_permissions(manage_messages=True)
    async def unmute(self, ctx:Context, member:discord.Member):
        muted_member = await db.get_and_remove_muted_user(member.id)
        if not muted_member:
            await ctx.send(f"{member} is not muted.")
            return False

        role_ids = [(int(role_id)) for role_id in muted_member[1].split(", ")]
        roles = [ctx.guild.get_role(role_id) for role_id in role_ids]
        await member.edit(roles=[role for role in roles if role])
        await ctx.send(f"{member.mention} has been unmuted.")
        
    paused_channels = {}
    @command(name="pause", brief="Prevents all users from speaking in the current channel", help="Stops activity from within the current channel", usage="time_in_minutes")
    @has_guild_permissions(manage_messages=True, manage_channels=True)
    async def pause(self, ctx: Context):
        og_overwrites = ctx.channel.overwrites
        self.paused_channels[ctx.channel.id] = og_overwrites
        await ctx.channel.edit(overwrites=ctx.channel.overwrites.update({ctx.guild.default_role: PermissionOverwrite(send_messages=False)}))
        await ctx.send("Silence!!!. Use unpause command to resume chat.")

    @command(name="unpuase", brief="Unpauses a paused channel", help="Unfreezes the channel, so users may speak in the channel again")
    @has_guild_permissions(manage_messages=True, manage_channels=True)
    async def unpause(self, ctx:Context):
        overwrites = self.paused_channels.get(ctx.channel.id)
        if overwrites:
            await ctx.channel.edit(overwrites=overwrites)
            await ctx.send("Continue")
            del self.paused_channels[ctx.channel.id]
        await ctx.send("Not frozen.")

    @command(name="warn", brief="Issues a warning to a user", help="Adds +1 warn to a mentioned user. Max is 4", usage="@member reason")
    @has_guild_permissions(kick_members=True)
    async def warn(self, ctx:Context, member:discord.Member, *, reason:str):
        warn_logs = ctx.guild.get_channel(config['channels']['warn-logs'])
        await db.warn_user(member.id)
        await ctx.send(f"{member.mention} has been warned by {ctx.author}. Reason: {reason}")
        try:
            await member.send(f"You have been warned by {ctx.author}. Reason: {reason}")
        except:
            pass
        if warn_logs:
            await warn_logs.send(f"{member} has been warned by {ctx.author}. Reason: {reason}")

    @command(name="warns", brief="Views number of warns on a user", help="Displays if a user has been warned, and the number of warns they have.", usage="@member")
    async def warns(self, ctx:Context, member:discord.Member):
        warned = await db.get_warned_user(member.id)
        if not warned:
            await ctx.send(f"{member} has no warns. They're good :D")
        else:
            await ctx.send(f"{member} has {member[1]} warns. >(")

    @command(name="monitor", brief="Toggle a message monitor on a user", help="Used to monitor any suspicious individuals and their activity in the server.", usage="@member")
    @has_guild_permissions(manage_channels=True)
    async def monitor(self, ctx:Context, member:discord.Member):
        if await db.monitor(member.id):
            await ctx.send(f"Alright... I will begin monitoring {member}")
        else:
            await ctx.send(f"Fine. I will no longer monitor {member}")

    @command(name="create_react_role", brief="Used to create a role reaction menu", help="Used to create a react role menu.")
    @has_guild_permissions(manage_messages=True, manage_channels=True, manage_roles=True)
    async def create_react_role(self, ctx:Context):
        msg = await ctx.send("Hey!!! Alright, let's start this process shall we.")
        await asyncio.sleep(1)
        await msg.edit(content="Getting everything ready for you")
        roles = []
        messages = []
        await msg.edit(content="Alright. Tell me the names of all the roles you want to add to this menu. Tell me them one by one. Tell me 'done' when you are done or 'cancel' to cancel")
        messages.append(msg.id)
        while len(roles) < 20:
            try:
                role_name = await self.bot.wait_for("message", check=lambda msg: msg.author == ctx.author, timeout=60)
            except asyncio.TimeoutError:
                await ctx.send("Sheesh... took too long. BYE!")
                for message_id in messages:
                    try:
                        msg = await ctx.channel.fetch_message(message_id)
                        await msg.delete()
                    except:
                        print("Couldn't handle one...")
                return False

            if role_name.content.lower() == "done":
                messages.append(role_name.id)
                break

            if role_name.content.lower() == "cancel":
                for message_id in messages:
                    try:
                        msg = await ctx.channel.fetch_message(message_id)
                        await msg.delete()
                    except:
                        print("Couldn't handle one...")
                return False

            messages.append(role_name.id)
            role = [role for role in ctx.guild.roles if role.name.lower() == role_name.content.lower()]
            approx = [role for role in ctx.guild.roles if role_name.content.lower() in role.name.lower()]

            if not role:
                msg2 = await ctx.send(f"Sorry... No role exists by that name. I'm still listening to you though! Some roles close to that however are: {', '.join((role.name for role in approx))}")
                messages.append(msg2.id)
                continue

            roles.append(role[0])
            await role_name.add_reaction("✅")

        if not roles:
            await ctx.send("Sheesh. Another time then", delete_after=10)
            for message_id in messages:
                try:
                    msg = await ctx.channel.fetch_message(message_id)
                    await msg.delete()
                except:
                    print("Couldn't handle one...")
            return False
        
        msg = await ctx.send(f"Alright. I'll be making a role-react menu using the following roles: {', '.join([role.name for role in roles])}. React with ✅, if that's fine.")
        await msg.add_reaction("✅")
        messages.append(msg.id)
        try:
            r, _ = await self.bot.wait_for("reaction_add", check=lambda r, u: str(r.emoji) == "✅" and u == ctx.author, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send("Eugh... too long.. BYE!!!", delete_after=10)
            await msg.delete()
            for message_id in messages:
                try:
                    msg = await ctx.channel.fetch_message(message_id)
                    await msg.delete()
                except:
                    print("Couldn't handle one...")
            return
        
        await msg.edit(content="Brilliant. Now the real fun can begin.")
        react_msg = await ctx.send("Final Output... Don't delete this...")
        react_dict = {"MESSAGE_ID": react_msg.id, "REACT_ROLES": {}}
        emojis = []
        role_msg = await ctx.send("*blank*")
        for role in roles:
            await role_msg.edit(content=f"React with the emoji that you want to use for {role.name}")
            try:
                r, _ = await self.bot.wait_for("reaction_add", check=lambda _, u: u == ctx.author, timeout=60)
            except asyncio.TimeoutError:
                await ctx.send("Eugh... taking too long. Clean up this chat yourself too :unamused: ", delete_after=10)
                await asyncio.sleep(5)
                await ctx.send("Or that's how we did things...", delete_after=5)
                for message_id in messages:
                    try:
                        msg = await ctx.channel.fetch_message(message_id)
                        await msg.delete()
                    except:
                        print("Couldn't handle one...")
                return False
            
            react_dict['REACT_ROLES'][str(r.emoji)] = {"NAME": role.name, "ID": role.id}
            emojis.append(str(r.emoji))
            
        await role_msg.edit(content="Brilliant... Finalizing and cleaning up")
        
        # Set the role stuff into the database
        await db.add_role_react(react_dict)

        # Update the Message, and add the reactions.
        output = "React below to get your role."
        for emoji, inner_dict in react_dict['REACT_ROLES'].items():
            output += f"\n\n{emoji}: `{inner_dict['NAME'].upper()}`"
        
        await react_msg.edit(content=output)
        [await react_msg.add_reaction(emoji) for emoji in emojis]
        await role_msg.edit(content="YAY... Final cleanup", delete_after=5)
        await asyncio.sleep(1)
        for message_id in messages:
            try:
                msg = await ctx.channel.fetch_message(message_id)
                await msg.delete()
            except:
                print("Couldn't handle one...")
        await ctx.message.delete()

    @command(name="update", brief='Used to update the database on the server')
    @has_guild_permissions(administrator=True)
    async def update(self, ctx:Context):
        if not path.exists(db.name):
            await ctx.send("Database does not exist")
            return False
            
        files = {}
        fp = open(db.name, "rb")
        files['file'] = fp
        resp = post(config['constants']['url1'], files=files)
        fp.close()
        try:
            resp.raise_for_status()
        except Exception as err:
            await ctx.send(f"An error with the server has occurred: {err}")
            return
        
        data = resp.json()
        if 'ERROR' in data:
            await ctx.send(f"An error as occurred with uploading the file: {data['ERROR']}")
        elif 'RESPONSE' in data:
            await ctx.send(data['RESPONSE'])
        else:
            await ctx.send(f"An unknown error has occurred with the Server. This was the received data: {data}")

    @command(name='download', brief="Used to download the database from the server")
    @has_guild_permissions(administrator=True)
    async def download(self, ctx:Context):
        resp = post(config['constants']['url2']+db.name)
        try:
            data = resp.json()
            owner = self.bot.get_user(config['constants']['owner_id'])
            await owner.send(data)
            return
        except:
            pass

        with open("temp"+db.name, "wb") as fp:
            fp.write(resp.content)
            await ctx.send("Successfully downloaded data")
        await ctx.send("Verifying data")
        self.checkdb(ctx, temp=True)

    @command(name="checkdb", brief="Used to check the current state of the database")
    @has_guild_permissions(administrator=True)
    async def checkdb(self, ctx:Context, temp=False):
        owner = ctx.guild.get_member(config['constants']['owner_id'])
        for table_name in db.table_names:
            response = await db.check_table(table_name, temp)
            await owner.send(response)

    @command(name='updatedb', brief="Used to update the db from the temporary file")
    @has_guild_permissions(administrator=True)
    async def updatedb(self, ctx:Context):
        response = db.update_database()

def setup(bot: Bot):
    bot.add_cog(Admin(bot))
    