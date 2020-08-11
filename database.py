import MySQLdb.cursors


def connection():
    conn = MySQLdb.connect(host="localhost",
                           user="root",
                           password="santosh16+",
                           db="Attendence",
                           cursorclass=MySQLdb.cursors.DictCursor
                           )
    c = conn.cursor()
    return c, conn
