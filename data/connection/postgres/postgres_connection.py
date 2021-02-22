import psycopg2


def get_connection():
    # if not ps_connection or ps_connection.closed:
    connection = psycopg2.connect(
        user="postgres", password="Mm123456", host="127.0.0.1", port="5432", database="postgres")
    # cursor = connection.cursor()
    # else:
    #    connection = ps_connection
    return connection

