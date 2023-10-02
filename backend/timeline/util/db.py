

def show_query(query):
    from sqlalchemy.sql import table, column, select
    from sqlalchemy.dialects import mysql
    print(query.statement.compile(compile_kwargs={"literal_binds": True, "dialect": mysql.dialect()}))
