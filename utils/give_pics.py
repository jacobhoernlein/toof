"""Gives the given user all the ToofPics."""

import sqlite3
import sys

from toof.cogs.pics import ToofPic, ToofPics


if __name__ == "__main__":
    user_id = 978022589882568794

    conn = sqlite3.connect(sys.argv[1])
    cursor = conn.execute("SELECT * FROM pics WHERE user_id = 0")
    all_pics = ToofPics([ToofPic(row[1], row[2]) for row in cursor])

    cursor = conn.execute(f"SELECT * FROM pics WHERE user_id = {user_id}")
    user_collection = ToofPics([ToofPic(row[1], row[2]) for row in cursor])
    cursor.close()

    for pic in all_pics:
        if pic not in user_collection and pic.rarity.name == "rare":
            conn.execute(f"INSERT INTO pics VALUES ({user_id}, '{pic.id}', '{pic.link}')")
    conn.commit()
    conn.close()
