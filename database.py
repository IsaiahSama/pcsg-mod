from sqlite3.dbapi2 import Row
from aiosqlite import connect

class Database:
    def __init__(self) -> None:
        """Class which handles all of the database connections and functions."""
        self.name = "moddb.sqlite3"
    
    async def setup(self):
        """Sets up all tables for the Database"""
        async with connect(self.name) as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS MuteTable(
                USER_ID INTEGER PRIMARY KEY,
                ROLE_IDS TEXT
                )""")

            await db.commit()

    async def mute_user(self, user_id:int, role_ids:list):
        """Adds a muted user and their roles to the database
        
        Args:
            user_id (int): The id of the user
            role_ids (list): A list of all of the ids of the user's roles """

        async with connect(self.name) as db:
            await db.execute("INSERT OR REPLACE INTO MuteTable (USER_ID, ROLE_IDS) VALUES (?, ?)", (user_id, ', '.join(str(rid) for rid in role_ids)))
            await db.commit()

    async def get_and_remove_muted_user(self, user_id:int) -> Row:
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

db = Database()