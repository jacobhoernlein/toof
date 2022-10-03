"""Gives the given user all the ToofPics."""

import sqlite3
import sys

from pics import ToofPic, ToofPics


if __name__ == "__main__":
    user_id = int(sys.argv[1])

    conn = sqlite3.connect("toof.sqlite")
    cursor = conn.execute("SELECT * FROM pics WHERE user_id = 0")
    all_pics = ToofPics([ToofPic(row[1], row[2]) for row in cursor])

    cursor = conn.execute(f"SELECT * FROM pics WHERE user_id = {user_id}")
    user_collection = ToofPics([ToofPic(row[1], row[2]) for row in cursor])
    cursor.close()

    for pic in all_pics:
        if pic not in user_collection:
            conn.execute(f"INSERT INTO pics VALUES ({user_id}, '{pic.id}', '{pic.link}')")
    conn.commit()
    conn.close()
