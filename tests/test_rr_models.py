import ast

from sqlalchemy import create_mock_engine
from sqlalchemy.sql.type_api import TypeEngine

from ukrr_models.rr_models import Base
from tests.table_extractor import TableNameExtractor


def mssql_dump(sql: TypeEngine, *args, **kwargs):
    dialect = sql.compile(dialect=mssql_engine.dialect)
    if sql_str := str(dialect).rstrip():
        print(f"{sql_str};")


mssql_engine = create_mock_engine("mssql+pyodbc://", mssql_dump)

with open("./ukrr_models/rr_models.py", "r") as file:
    code = file.read()

tree = ast.parse(code)
table_name_extractor = TableNameExtractor()
table_name_extractor.visit(tree)


def test_create_tables(capsys):
    Base.metadata.create_all(bind=mssql_engine, checkfirst=False)
    captured = capsys.readouterr()
    for table in table_name_extractor.table_names:
        assert (
            f"CREATE TABLE {table}" in captured.out
            or f"CREATE TABLE [{table}]" in captured.out
        )
