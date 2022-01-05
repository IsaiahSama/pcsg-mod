from sqlite3.dbapi2 import Row
from typing import Union
from aiosqlite import connect

class Database:
    def __init__(self) -> None:
        """Class which handles all of the database connections and functions."""
        self.name = "moddb.sqlite3"
        self.reset = False
        self.table_names = ["MuteTable", "WarnTable", "MonitorTable", "LevelTable", "RoleTable"]
    
    async def setup(self):
        """Sets up all tables for the Database"""
        if self.reset:
            async with connect(self.name) as db:
                for table in self.table_names:
                    await db.execute(f"""DROP TABLE IF EXISTS {table}""")
                await db.commit()
                    
        async with connect(self.name) as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS MuteTable(
                USER_ID INTEGER PRIMARY KEY,
                ROLE_IDS TEXT
                )""")

            await db.execute("""CREATE TABLE IF NOT EXISTS WarnTable(
                USER_ID INTEGER PRIMARY KEY,
                WARN_COUNT INTEGER)""")

            await db.execute("""
            CREATE TABLE IF NOT EXISTS MonitorTable (
                USER_ID INTEGER PRIMARY KEY UNIQUE
                )""")

            await db.execute("""CREATE TABLE IF NOT EXISTS LevelTable (
                USER_ID INTEGER PRIMARY KEY UNIQUE,
                EXP INTEGER)""")

            await db.execute("""CREATE TABLE IF NOT EXISTS RoleTable (
                ID INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
                MESSAGE_ID INTEGER,
                EMOJI TEXT,
                ROLE_ID INTEGER,
                ROLE_NAME TEXT)
                """)

            await db.commit()
            print("Completed creating of database")

    async def mute_user(self, user_id:int, role_ids:list):
        """Adds a muted user and their roles to the database
        
        Args:
            user_id (int): The id of the user
            role_ids (list): A list of all of the ids of the user's roles """

        async with connect(self.name) as db:
            await db.execute("INSERT OR REPLACE INTO MuteTable (USER_ID, ROLE_IDS) VALUES (?, ?)", (user_id, ', '.join(str(rid) for rid in role_ids)))
            await db.commit()

    async def get_and_remove_muted_user(self, user_id:int) -> Union[Row, list]:
        """Requests a muted user from the database. Then removes them from the database
        
        Args:
            user_id (int): The id of the user to query
            
        Returns:
            Row | None"""

        async with connect(self.name) as db:
            cursor = await db.execute("SELECT * FROM MuteTable WHERE USER_ID = (?)", (user_id,))
            data = await cursor.fetchall()
            if data:
                await db.execute("DELETE FROM MuteTable WHERE USER_ID = (?)", (user_id, ))
                await db.commit()
            return data

    async def warn_user(self, user_id:int):
        """Increases the warns on a user by 1, and saves it.
        
        Args:
            user_id (int): The id of the user to query"""

        warned_user = await self.get_warned_user(user_id)
        if warned_user:
            to_add = list(warned_user)
            to_add[1] += 1
        else:
            to_add = [user_id, 1]
        
        async with connect(self.name) as db:
            await db.execute("INSERT OR REPLACE INTO WarnTable (USER_ID, WARN_COUNT) VALUES (?, ?)", tuple(to_add))
            await db.commit()
            return True

    async def get_warned_user(self, user_id:int) -> Row:
        """Checks if a user has been warned before, and returns it.
        
        Args:
            user_id (int): The id of the user to query
        
        Returns:
            Row | None"""

        async with connect(self.name) as db:
            cursor = await db.execute("SELECT * FROM WarnTable WHERE USER_ID = (?)", (user_id, ))
            return await cursor.fetchone()

    async def monitor(self, user_id:int) -> bool:
        """Toggles whether a user is to be monitored or not
        
        Args:
            user_id (int): An id of the user to monitor
            
        Returns:
            bool: True if the user is now being monitored, False if they are no longer being monitored"""
        
        if await self.is_monitored(user_id):
            async with connect(self.name) as db:
                await db.execute("DELETE FROM MonitorTable WHERE USER_ID = (?)", (user_id, ))
                await db.commit()
                return False
        else:
            async with connect(self.name) as db:
                await db.execute("INSERT OR REPLACE INTO MonitorTable USER_ID VALUES (?)", (user_id, ))
                await db.commit()
                return True

    async def is_monitored(self, user_id:int) -> bool:
        """Checks whether or not a user with a given id is being monitored
        
        Args:
            user_id (int): The ID of the user to check.
            
        Return:
            bool"""

        async with connect(self.name) as db:
            cursor = await db.execute("SELECT * FROM MonitorTable WHERE USER_ID = (?)", (user_id, ))
            monitored = await cursor.fetchall()
        return True if monitored else False

    async def get_user(self, user_id:int) -> Union[Row, list]:
        """Queries the database for a USER with Exp.
        
        Args:
            user_id (int): The ID of the user to query
            
        Returns:
            Row | None"""

        async with connect(self.name) as db:
            cursor = await db.execute("SELECT * FROM LevelTable WHERE USER_ID = (?)", (user_id, ))
            return await cursor.fetchone()

    async def add_exp_to_user(self, user_id: int):
        """Adds exp to a user, or creates the user anew.
        
        Args:
            user_id (int): The ID of the user to work on"""

        if user := await self.get_user(user_id):
            user_update = list(user)
            user_update[1] += 1
            to_add = tuple(user_update)
        else:
            to_add = (user_id, 1)

        async with connect(self.name) as db:
            await db.execute("INSERT OR REPLACE INTO LevelTable (USER_ID, EXP) VALUES (?, ?)", to_add)
            await db.commit()
        
        if not user:
            user = await self.get_user(user_id)
        
        return user
    
    async def query_all_users(self) -> Union[list, Row]:
        """Queries all users that have EXP from the database
        
        Returns:
            list| Row"""
        async with connect(self.name) as db:
            cursor = await db.execute("SELECT * FROM LevelTable")
            return await cursor.fetchall()

    async def add_role_react(self, role_dict:dict):
        """Sets up the roles and their reactions into the database
        
        Args:
            role_dict (dict): Dict containing the role menu."""

        """Role_dict format:
        {
            MESSAGE_ID : int,
            REACT_ROLES : {
                EMOJI (str): {
                    NAME: (str),
                    ID: (int)
                }
            }
        } """

        message_id = role_dict['MESSAGE_ID']
        react_roles = role_dict["REACT_ROLES"]

        for emoji, inner_dict in react_roles.items():
            async with connect(self.name) as db:
                await db.execute("INSERT OR REPLACE INTO RoleTable (MESSAGE_ID, EMOJI, ROLE_ID, ROLE_NAME) VALUES (?, ?, ?, ?)", (message_id, emoji, inner_dict['ID'], inner_dict['NAME']))
                await db.commit()
    
    async def get_role_menu(self, message_id:int) -> Union[Row, list, None]:
        """Retrieves a role menu via message_id
        
        Args:
            message_id (int): The id of the message to check for.
        
        Returns:
            Row | None"""
        
        async with connect(self.name) as db:
            cursor = await db.execute("SELECT * FROM RoleTable WHERE MESSAGE_ID = (?)", (message_id, ))
            results = await cursor.fetchall()
            return results

    async def check_table(self, table_name:str, temp:bool) -> Union[Row, str]:
        """Checks a given table within the database
        
        Args:
            table_name (str): The name of the table to check
            temp (bool): Whether to check the og table or the temporary one
        
        Returns:
            (Row, str)
            
        Raises:
            OperationalError"""

        name = "temp" + self.name if temp else self.name

        try:
            async with connect(name) as db:
                cursor = await db.execute(f"SELECT * FROM {table_name}")
                rows = await cursor.fetchall()
                return rows
        except Exception as err:
            return f"An error has occurred with table {table_name} in database {name}. {err}"

    async def update_database(self):
        """Used to update the database from the temporary database file downloaded from the server

        Returns: 
            str
        """

        for table_name in self.table_names:
            for state in [True, False]:
                msg = self.check_table(table_name, state)
                if isinstance(msg, str): return "Cancelling update. " + msg

        with open("temp"+self.name, "rb") as tempdb:
            temp_data = tempdb.read()

        with open(self.name, "wb") as current_db:
            current_db.write(temp_data)

        return "Update was successful"       

db = Database()