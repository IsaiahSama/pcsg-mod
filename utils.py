from discord.channel import TextChannel
from discord import Embed, Member
from discord.ext.commands import Bot, Cog
from discord_slash import SlashContext, cog_ext
from discord_slash.context import ComponentContext
from discord_slash.utils.manage_commands import create_choice, create_option
from discord_slash.utils.manage_components import create_actionrow, create_select_option, create_select, wait_for_component
from config import config
from database import db
from random import randint, shuffle

class Utils(Cog):
    def __init__(self, bot:Bot):
        self.bot = bot

    @cog_ext.cog_slash(name="portal", description="Creates a link to another channel.", guild_ids=config['guild_ids'], 
    options=[create_option(name="channel", description="Provides a link to the selected channel", option_type=TextChannel, required=True)])
    async def portal(self, ctx:SlashContext, channel:TextChannel):
        await ctx.send(channel.mention)

    @cog_ext.cog_slash(name="rank", description="Displays your rank based on level.", guild_ids=config['guild_ids'], options=[
        create_option(
        name="member", description="Optional: The person who's rank you want to check", option_type=Member, required=False)])
    async def rank(self, ctx:SlashContext, member:Member=None):
        target = member or ctx.author
        all_users = await db.query_all_users()
        user = [user for user in all_users if user[0] == target.id]
        if user:
            user = user[0]
            all_users.sort(key=lambda x: x[1], reverse=True)
            embed = Embed(title=f"Showing Activity Level for {target.name}", color=randint(0, 0xffffff))
            embed.add_field(name="Rank", value=f"{all_users.index(user)} of {len(all_users)} members")
            embed.add_field(name="Exp", value=user[1])
            await ctx.send(embed=embed)
        else:
            await ctx.send("Stange... you're not in the database... Try being a bit more active and checking again later.")

    @cog_ext.cog_slash(name="top", description="Displays the 5 most active users.", guild_ids=config['guild_ids'])
    async def top(self, ctx:SlashContext):
        all_users = await db.query_all_users()
        all_users.sort(key=lambda x: x[1], reverse=True)
        embed = Embed(title="SHowing top 5 most active", color=randint(0, 0xffffff))
        for user in all_users[:5]:
            embed.add_field(name="Name:", value=ctx.guild.get_member(user[0]) or "Unknown User")
            embed.add_field(name="Exp:", value=user[1])
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="style", description="Used to view and choose your learning style", guild_ids=config['guild_ids'],
    options=[
        create_option("learn", "Select a learning style that you want to learn more about", str, False, choices=[create_choice(value, name) for value, name in zip(config['styles'].keys(), [name.split("\n")[0] for name in config['styles'].values()])]),
        create_option("choose", "Select your learning style from the provided options", str, False, choices=[create_choice(value, name) for value, name in zip(config['styles'].keys(), [name.split("\n")[0] for name in config['styles'].values()])]),
        create_option("find", "Finds other students that have a similar learning style to you", str, False, choices=[create_choice(value, name) for value, name in zip(config['styles'].keys(), [name.split("\n")[0] for name in config['styles'].values()])])
    ])
    async def style(self, ctx:SlashContext, learn:str='', choose:str='', find:str=''):
        # await ctx.defer()
        if not any((find, learn, choose)): await ctx.send("Nothing was selected", delete_after=5); return False 
        if learn:
            await ctx.send(config['styles'][learn])
        elif choose:
            try:
                role_id = config['roles'][choose]
                role = ctx.guild.get_role(role_id)
                await ctx.author.add_roles(role) if role not in ctx.author.roles else ctx.author.remove_roles(role)
                await ctx.send(f"You have successfully {'removed' if role in ctx.author.roles else 'gain'} the {role.name} role")
            except KeyError:
                await ctx.send("Sorry, we're still waiting on the roles to be created before this can work.")
        else:
            try:
                role_id = config['roles'][choose]
                role = ctx.guild.get_role(role_id)
                similar = [member for member in ctx.guild.members if role in member.roles]
                if not similar: await ctx.send(f"Sorry, can't find anyone with a similar learning style to {role.name}... not yet anyway :)")
                else:
                    await ctx.send(f"Showing all students with the {role.name} learning style.\n{', '.join([str(student) for student in similar])}")
            except KeyError:
                await ctx.send("Sorry, we're still waiting on the roles to be created before this can work.")

    # @cog_ext.cog_slash(name="matchfind", description="Used to find students who do similar subjects to you.", guild_ids=config['guild_ids'],
    # options=[
    #     create_option(name="criteria", description="The criteria you want to use to find your matches.", option_type=str, required=True, choices=[
    #         create_choice(value="subject", name="By Subject"),
    #         create_choice(value="year", name="By Year"),
    #         create_choice(value="country", name="By Country")
    #     ])
    # ])

    @cog_ext.cog_slash(name="matchfind", description="Used to find students who do similar subjects to you.", guild_ids=config['guild_ids'],
    options=[
        create_option(name="learning_style", description="Determines whether to filter by learning style.", option_type=str, required=True, choices=[create_choice(value, name) for value, name in zip([*config['styles'].keys(), "none"], [name.split("\n")[0] for name in [*config['styles'].values(), "None"]])
        ]),
    ])
    async def matchfind(self, ctx:SlashContext, learning_style:str):
        await ctx.defer()

        countries = ['Anguilla', 'Antigua and Barbuda', 'Bahamas', 'Barbados', 'Belize', 'British Virgin Islands', 'Cayman Islands', 'Dominica', 'Germany', 'Grenada', 'Guyana', 'Haiti', 'Jamaica', 'Montserrat', 'St.Kitts and Nevis', 'St.Lucia', 'St.Vincent and the Grenadines', 'Suriname', 'Trinidad and Tobago']

        options = [
            create_select_option(label="By Subject", value="subject", description="Filter by subjects"),
            create_select_option(label="By Year", value="year", description="Filter by form level/year"),
            create_select_option(label="By Proficiency", value="pro", description="Filter by CAPE, CSEC or PRE-CSEC"),
            create_select_option(label="By Country", value="country", description="Filter by country"),
        ]

        select = create_select(options=options, custom_id=str(ctx.author.id), placeholder="Select criteria for match find below.", max_values=4, min_values=1)

        actionrow = create_actionrow(select)

        await ctx.send("Criteria Select", components=[actionrow])
        select_ctx: ComponentContext = await wait_for_component(self.bot, components=actionrow)
        if not select_ctx.selected_options:
            return
        criteria = select_ctx.selected_options

        matches = ctx.guild.members
        # Starting the filter

        if "subject" in criteria:
            student_subjects = [role for role in ctx.author.roles if role.name[0] in ["3", "4", "5", "6"]]
            matches = [student for student in matches if any(subject in student.roles for subject in student_subjects)]
        if "year" in criteria:
            student_year = [role for role in ctx.author.roles if role.name.split(" ")[0] in ["Unit", "Form"]]
            matches = [student for student in matches if any(year in student.roles for year in student_year)]
        if "pro" in criteria:
            student_proficieny = [role for role in ctx.author.roles if any(pro.lower() in role.name.lower() for pro in ["csec", "cape"])]
            matches = [student for student in matches if any(pro in student.roles for pro in student_proficieny)]
        if "country" in criteria:
            student_country = [role for role in ctx.author.roles if role.name in countries]
            matches = [student for student in matches if any(country in student.roles for country in student_country)]
        if learning_style != "none":
            role = config['roles'][learning_style]
            matches = [student for student in matches if role in student.roles]
        
        await select_ctx.edit_origin(content="Done")
        if not matches:
            await ctx.send("Sorry, couldn't find anyone matching those criteria. Make sure that you have your roles selected, or try changing your criteria :sweat_smile:")
        else:
            embed = Embed(title=f"Matchfind for {str(ctx.author)}", description=f"Found {len(matches)} in total, and showing {len(matches[:25])} students that match your criteria of {criteria}", color=randint(0, 0xffffff))
            shuffle(matches)
            [embed.add_field(name=f"Match {i}", value=v) for i, v in enumerate(matches[:25])]
            await ctx.send(embed=embed)

def setup(bot:Bot):
    bot.add_cog(Utils(bot))