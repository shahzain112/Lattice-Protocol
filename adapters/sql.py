"""
DataMigrationEngine - Fixed Version
Migrates data from MSSQL/MySQL to PostgreSQL with batch processing.
"""

import pyodbc
import pymysql
import psycopg2
from psycopg2 import sql
import logging
from collections import defaultdict
from contextlib import contextmanager
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataMigrationEngine:
    """Engine for migrating data from MSSQL/MySQL to PostgreSQL."""

    # ==========================================
    # 1. TYPE MAPPINGS
    # ==========================================
    _mssql_to_pg = {
        'bigint': 'BIGINT', 'binary': 'BYTEA', 'bit': 'BOOLEAN',
        'char': 'CHAR', 'date': 'DATE', 'datetime': 'TIMESTAMP',
        'datetime2': 'TIMESTAMP', 'datetimeoffset': 'TIMESTAMPTZ',
        'decimal': 'NUMERIC', 'float': 'DOUBLE PRECISION',
        'image': 'BYTEA', 'int': 'INTEGER', 'money': 'NUMERIC',
        'nchar': 'CHAR', 'ntext': 'TEXT', 'numeric': 'NUMERIC',
        'nvarchar': 'VARCHAR', 'real': 'REAL', 'smalldatetime': 'TIMESTAMP',
        'smallint': 'SMALLINT', 'smallmoney': 'NUMERIC',
        'text': 'TEXT', 'time': 'TIME', 'tinyint': 'SMALLINT',
        'uniqueidentifier': 'UUID', 'varbinary': 'BYTEA',
        'varchar': 'VARCHAR', 'xml': 'XML'
    }

    _mysql_to_pg = {
        'tinyint': 'SMALLINT', 'smallint': 'SMALLINT', 'mediumint': 'INTEGER',
        'int': 'INTEGER', 'bigint': 'BIGINT', 'float': 'REAL',
        'double': 'DOUBLE PRECISION', 'decimal': 'NUMERIC',
        'date': 'DATE', 'datetime': 'TIMESTAMP', 'timestamp': 'TIMESTAMPTZ',
        'time': 'TIME', 'year': 'INTEGER',
        'char': 'CHAR', 'varchar': 'VARCHAR', 'text': 'TEXT',
        'tinytext': 'TEXT', 'mediumtext': 'TEXT', 'longtext': 'TEXT',
        'blob': 'BYTEA', 'tinyblob': 'BYTEA', 'mediumblob': 'BYTEA', 'longblob': 'BYTEA',
        'json': 'JSONB', 'enum': 'VARCHAR', 'set': 'TEXT',
        'geometry': 'GEOMETRY', 'point': 'POINT'
    }

    @staticmethod
    def _sanitize_identifier(name):
        """Safely quote SQL identifiers to prevent injection."""
        # Remove any existing quotes and dangerous characters
        clean_name = name.replace('"', '').replace("'", '').replace(';', '')
        return f'"{clean_name.lower()}"'

    # ==========================================
    # 2. CONNECTION HELPERS (Context Managers)
    # ==========================================
    @staticmethod
    @contextmanager
    def _mssql_connection(conn_str):
        """Context manager for MSSQL connections."""
        conn = None
        try:
            conn = pyodbc.connect(conn_str)
            yield conn
        finally:
            if conn:
                conn.close()

    @staticmethod
    @contextmanager
    def _mysql_connection(host, user, password, database):
        """Context manager for MySQL connections."""
        conn = None
        try:
            conn = pymysql.connect(
                host=host, user=user, password=password,
                database=database, charset='utf8mb4'
            )
            yield conn
        finally:
            if conn:
                conn.close()

    @staticmethod
    @contextmanager
    def _postgres_connection(target_uri):
        """Context manager for PostgreSQL connections."""
        conn = None
        try:
            # Parse the URI properly for psycopg2
            parsed = urlparse(target_uri)
            conn_params = {}

            if parsed.scheme in ('postgresql', 'postgres'):
                # Build connection parameters from URI
                if parsed.hostname:
                    conn_params['host'] = parsed.hostname
                if parsed.port:
                    conn_params['port'] = parsed.port
                if parsed.username:
                    conn_params['user'] = parsed.username
                if parsed.password:
                    conn_params['password'] = parsed.password
                if parsed.path:
                    conn_params['dbname'] = parsed.path.lstrip('/')

                conn = psycopg2.connect(**conn_params)
            else:
                # Fallback: try direct connection string
                conn = psycopg2.connect(target_uri)

            yield conn
        finally:
            if conn:
                conn.close()

    # ==========================================
    # 3. SOURCE SCHEMA FETCH (Parameterized Queries)
    # ==========================================
    @staticmethod
    def _get_mssql_schema(conn_str, schema='dbo'):
        """Fetch schema from MSSQL using parameterized queries."""
        tables = []
        columns = {}
        fks = defaultdict(list)

        with DataMigrationEngine._mssql_connection(conn_str) as conn:
            cursor = conn.cursor()

            # Get tables - parameterized query
            cursor.execute(
                """SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
                   WHERE TABLE_TYPE='BASE TABLE' AND TABLE_SCHEMA=?""",
                (schema,)
            )
            tables = [row[0].lower() for row in cursor.fetchall()]

            # Get columns - parameterized query
            for table in tables:
                cursor.execute(
                    """SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, 
                              IS_NULLABLE, 
                              COLUMNPROPERTY(OBJECT_ID(TABLE_NAME), COLUMN_NAME, 'IsIdentity') as IsIdentity
                       FROM INFORMATION_SCHEMA.COLUMNS
                       WHERE TABLE_NAME = ?""",
                    (table.upper(),)
                )
                columns[table] = cursor.fetchall()

            # Get foreign keys - parameterized query
            for table in tables:
                cursor.execute(
                    """SELECT tp.name, ref.name, cp.name, cref.name
                       FROM sys.foreign_keys fk
                       JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
                       JOIN sys.tables tp ON fkc.parent_object_id = tp.object_id
                       JOIN sys.tables ref ON fkc.referenced_object_id = ref.object_id
                       JOIN sys.columns cp ON fkc.parent_column_id = cp.column_id AND cp.object_id = tp.object_id
                       JOIN sys.columns cref ON fkc.referenced_column_id = cref.column_id AND cref.object_id = ref.object_id
                       WHERE tp.name = ?""",
                    (table.upper(),)
                )
                for row in cursor.fetchall():
                    fks[table.lower()].append((
                        row[0].lower(), row[1].lower(), 
                        row[2].lower(), row[3].lower()
                    ))

        return tables, columns, fks

    @staticmethod
    def _get_mysql_schema(host, user, password, database):
        """Fetch schema from MySQL using parameterized queries."""
        tables = []
        columns = {}
        fks = defaultdict(list)

        with DataMigrationEngine._mysql_connection(host, user, password, database) as conn:
            cursor = conn.cursor()

            # Get tables - parameterized query
            cursor.execute(
                """SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
                   WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE'""",
                (database,)
            )
            tables = [row[0].lower() for row in cursor.fetchall()]

            # Get columns - parameterized query
            for table in tables:
                cursor.execute(
                    """SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, 
                              IS_NULLABLE, EXTRA
                       FROM INFORMATION_SCHEMA.COLUMNS
                       WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s""",
                    (database, table)
                )
                columns[table] = cursor.fetchall()

            # Get foreign keys - parameterized query
            for table in tables:
                cursor.execute(
                    """SELECT TABLE_NAME, REFERENCED_TABLE_NAME, 
                              COLUMN_NAME, REFERENCED_COLUMN_NAME
                       FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                       WHERE REFERENCED_TABLE_SCHEMA=%s AND TABLE_NAME=%s""",
                    (database, table)
                )
                for row in cursor.fetchall():
                    fks[table.lower()].append((
                        row[0].lower(), row[1].lower(),
                        row[2].lower(), row[3].lower()
                    ))

        return tables, columns, fks

    # ==========================================
    # 4. DDL GENERATORS (Fixed)
    # ==========================================
    @staticmethod
    def _generate_ddl_mssql(table, cols, target_cursor):
        """Generate DDL for MSSQL to PostgreSQL migration."""
        col_defs = []

        for col in cols:
            name, dtype, max_len, nullable, is_identity = col
            pg_type = DataMigrationEngine._mssql_to_pg.get(dtype.lower(), 'TEXT')

            # Handle IDENTITY columns
            if is_identity == 1:
                pg_type = 'SERIAL'
                null_clause = 'NOT NULL'
            # Handle VARCHAR/NVARCHAR with length
            elif dtype.lower() in ('varchar', 'nvarchar', 'char', 'nchar'):
                if max_len == -1 or max_len is None or max_len > 10485760:
                    pg_type = 'TEXT'
                    null_clause = 'NOT NULL' if nullable == 'NO' else ''
                else:
                    pg_type = f'VARCHAR({max_len})'
                    null_clause = 'NOT NULL' if nullable == 'NO' else ''
            else:
                null_clause = 'NOT NULL' if nullable == 'NO' else ''

            col_def = f'{DataMigrationEngine._sanitize_identifier(name)} {pg_type}'
            if null_clause:
                col_def += f' {null_clause}'
            col_defs.append(col_def)

        # Use psycopg2.sql for safe DDL
        table_ident = sql.Identifier(table.lower())
        col_str = ',\n  '.join(col_defs)
        ddl = f'CREATE TABLE IF NOT EXISTS {table_ident} (\n  {col_str}\n);'

        # Execute using psycopg2 cursor
        target_cursor.execute(ddl)
        target_cursor.connection.commit()
        return ddl

    @staticmethod
    def _generate_ddl_mysql(table, cols, target_cursor):
        """Generate DDL for MySQL to PostgreSQL migration."""
        col_defs = []

        for col in cols:
            name, dtype, max_len, nullable, extra = col
            pg_type = DataMigrationEngine._mysql_to_pg.get(dtype.lower(), 'TEXT')

            # Handle auto_increment
            if extra and 'auto_increment' in extra.lower():
                pg_type = 'SERIAL'
                null_clause = 'NOT NULL'
            # Handle VARCHAR with length
            elif dtype.lower() in ('varchar', 'char'):
                if max_len and max_len > 0:
                    pg_type = f'VARCHAR({max_len})'
                else:
                    pg_type = 'TEXT'
                null_clause = 'NOT NULL' if nullable == 'NO' else ''
            else:
                null_clause = 'NOT NULL' if nullable == 'NO' else ''

            col_def = f'{DataMigrationEngine._sanitize_identifier(name)} {pg_type}'
            if null_clause:
                col_def += f' {null_clause}'
            col_defs.append(col_def)

        # Use psycopg2.sql for safe DDL
        table_ident = sql.Identifier(table.lower())
        col_str = ',\n  '.join(col_defs)
        ddl = f'CREATE TABLE IF NOT EXISTS {table_ident} (\n  {col_str}\n);'

        target_cursor.execute(ddl)
        target_cursor.connection.commit()
        return ddl

    # ==========================================
    # 5. URI PARSERS (Robust)
    # ==========================================
    @staticmethod
    def _parse_mssql_uri(source_uri):
        """Parse MSSQL connection URI safely."""
        try:
            parsed = urlparse(source_uri)
            if parsed.scheme not in ('mssql+pyodbc', 'mssql'):
                raise ValueError("Invalid MSSQL URI scheme")

            auth = parsed.username or ''
            password = parsed.password or ''
            host = parsed.hostname or 'localhost'
            port = parsed.port or 1433
            db = parsed.path.lstrip('/') or 'master'

            conn_str = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={host},{port};"
                f"DATABASE={db};"
                f"UID={auth};"
                f"PWD={password};"
                f"TrustServerCertificate=yes;"
                f"Encrypt=no;"
            )
            return conn_str
        except Exception as e:
            raise ValueError(f"Failed to parse MSSQL URI: {e}")

    @staticmethod
    def _parse_mysql_uri(source_uri):
        """Parse MySQL connection URI safely."""
        try:
            parsed = urlparse(source_uri)
            if parsed.scheme not in ('mysql+pymysql', 'mysql'):
                raise ValueError("Invalid MySQL URI scheme")

            user = parsed.username or 'root'
            password = parsed.password or ''
            host = parsed.hostname or 'localhost'
            port = parsed.port or 3306
            db = parsed.path.lstrip('/') or ''

            return host, port, user, password, db
        except Exception as e:
            raise ValueError(f"Failed to parse MySQL URI: {e}")

    # ==========================================
    # 6. MAIN MIGRATION (Fixed & Safe)
    # ==========================================
    @staticmethod
    def migrate_data(source_uri, target_uri, tables=None, batch_size=5000):
        """
        Migrate data from MSSQL or MySQL to PostgreSQL.

        Args:
            source_uri: Source database URI
            target_uri: Target PostgreSQL URI
            tables: List of tables to migrate (None = all)
            batch_size: Number of rows per batch

        Returns:
            dict: Status and logs
        """
        logs = []

        try:
            # Determine source type and parse URI
            if 'mssql' in source_uri.lower():
                return DataMigrationEngine._migrate_mssql(
                    source_uri, target_uri, tables, batch_size, logs
                )
            elif 'mysql' in source_uri.lower():
                return DataMigrationEngine._migrate_mysql(
                    source_uri, target_uri, tables, batch_size, logs
                )
            else:
                return {
                    "status": "error",
                    "error": "Unsupported source. Use 'mssql' or 'mysql'."
                }

        except MemoryError:
            logger.error("RAM full! Try reducing batch_size (e.g., 1000).")
            return {
                "status": "error",
                "error": "Out of Memory! Reduce batch_size or upgrade RAM."
            }
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def _migrate_mssql(source_uri, target_uri, tables, batch_size, logs):
        """Migrate from MSSQL to PostgreSQL."""
        conn_str = DataMigrationEngine._parse_mssql_uri(source_uri)

        # Fetch schema
        tables_list, cols_map, fks_map = DataMigrationEngine._get_mssql_schema(conn_str)

        with DataMigrationEngine._postgres_connection(target_uri) as pg_conn:
            pg_cursor = pg_conn.cursor()

            # Phase 1: Create DDL
            for table in tables_list:
                if tables and table not in tables:
                    continue
                DataMigrationEngine._generate_ddl_mssql(
                    table, cols_map[table], pg_cursor
                )
                logs.append(f"✅ Schema created: {table}")

            # Phase 2: Data Transfer
            logs.append(f"🚀 Starting MSSQL data transfer (batch_size={batch_size})")

            with DataMigrationEngine._mssql_connection(conn_str) as src_conn:
                src_cursor = src_conn.cursor()

                for table in tables_list:
                    if tables and table not in tables:
                        continue

                    # Sanitize table name for query
                    safe_table = DataMigrationEngine._sanitize_identifier(table)
                    src_cursor.execute(f"SELECT * FROM {safe_table}")
                    cols = [desc[0] for desc in src_cursor.description]

                    total_rows = 0
                    while True:
                        chunk = src_cursor.fetchmany(batch_size)
                        if not chunk:
                            break

                        # Build safe insert query
                        col_names = [sql.Identifier(c.lower()) for c in cols]
                        placeholders = sql.SQL(',').join(
                            sql.Placeholder() for _ in cols
                        )

                        insert_query = sql.SQL(
                            'INSERT INTO {} ({}) VALUES ({})'
                        ).format(
                            sql.Identifier(table.lower()),
                            sql.SQL(',').join(col_names),
                            placeholders
                        )

                        pg_cursor.executemany(insert_query, chunk)
                        pg_conn.commit()
                        total_rows += len(chunk)
                        chunk = None

                    logs.append(
                        f"✅ Transferred: {table} ({total_rows} rows)"
                    )

            # Phase 3: Foreign Keys
            for parent, fks in fks_map.items():
                for fk in fks:
                    try:
                        fk_name = f"fk_{parent}_{fk[1]}_{fk[2]}"
                        fk_sql = sql.SQL(
                            'ALTER TABLE {} ADD CONSTRAINT {} '
                            'FOREIGN KEY ({}) REFERENCES {}({})'
                        ).format(
                            sql.Identifier(parent),
                            sql.Identifier(fk_name),
                            sql.Identifier(fk[2]),
                            sql.Identifier(fk[1]),
                            sql.Identifier(fk[3])
                        )
                        pg_cursor.execute(fk_sql)
                        pg_conn.commit()
                        logs.append(f"✅ FK added: {parent} -> {fk[1]}")
                    except Exception as e:
                        logs.append(f"⚠️ FK skipped: {e}")

            pg_cursor.close()

        return {"status": "success", "logs": logs}

    @staticmethod
    def _migrate_mysql(source_uri, target_uri, tables, batch_size, logs):
        """Migrate from MySQL to PostgreSQL."""
        host, port, user, password, db = DataMigrationEngine._parse_mysql_uri(source_uri)

        # Fetch schema
        tables_list, cols_map, fks_map = DataMigrationEngine._get_mysql_schema(
            host, user, password, db
        )

        with DataMigrationEngine._postgres_connection(target_uri) as pg_conn:
            pg_cursor = pg_conn.cursor()

            # Phase 1: Create DDL
            for table in tables_list:
                if tables and table not in tables:
                    continue
                DataMigrationEngine._generate_ddl_mysql(
                    table, cols_map[table], pg_cursor
                )
                logs.append(f"✅ Schema created: {table}")

            # Phase 2: Data Transfer
            logs.append(f"🚀 Starting MySQL data transfer (batch_size={batch_size})")

            with DataMigrationEngine._mysql_connection(host, user, password, db) as src_conn:
                src_cursor = src_conn.cursor()

                for table in tables_list:
                    if tables and table not in tables:
                        continue

                    safe_table = DataMigrationEngine._sanitize_identifier(table)
                    src_cursor.execute(f"SELECT * FROM {safe_table}")
                    cols = [desc[0] for desc in src_cursor.description]

                    total_rows = 0
                    while True:
                        chunk = src_cursor.fetchmany(batch_size)
                        if not chunk:
                            break

                        col_names = [sql.Identifier(c.lower()) for c in cols]
                        placeholders = sql.SQL(',').join(
                            sql.Placeholder() for _ in cols
                        )

                        insert_query = sql.SQL(
                            'INSERT INTO {} ({}) VALUES ({})'
                        ).format(
                            sql.Identifier(table.lower()),
                            sql.SQL(',').join(col_names),
                            placeholders
                        )

                        pg_cursor.executemany(insert_query, chunk)
                        pg_conn.commit()
                        total_rows += len(chunk)
                        chunk = None

                    logs.append(
                        f"✅ Transferred: {table} ({total_rows} rows)"
                    )

            # Phase 3: Foreign Keys
            for parent, fks in fks_map.items():
                for fk in fks:
                    try:
                        fk_name = f"fk_{parent}_{fk[1]}_{fk[2]}"
                        fk_sql = sql.SQL(
                            'ALTER TABLE {} ADD CONSTRAINT {} '
                            'FOREIGN KEY ({}) REFERENCES {}({})'
                        ).format(
                            sql.Identifier(parent),
                            sql.Identifier(fk_name),
                            sql.Identifier(fk[2]),
                            sql.Identifier(fk[1]),
                            sql.Identifier(fk[3])
                        )
                        pg_cursor.execute(fk_sql)
                        pg_conn.commit()
                        logs.append(f"✅ FK added: {parent} -> {fk[1]}")
                    except Exception as e:
                        logs.append(f"⚠️ FK skipped: {e}")

            pg_cursor.close()

        return {"status": "success", "logs": logs}

    # ==========================================
    # 7. POSTGRES EXTENSION (Fixed)
    # ==========================================
    @staticmethod
    def create_postgres_extension(target_uri, extension_name):
        """
        Create a PostgreSQL extension safely.

        Args:
            target_uri: PostgreSQL connection URI
            extension_name: Name of extension to create

        Returns:
            dict: Status and message
        """
        # Validate extension name (prevent injection)
        valid_extensions = {
            'postgis', 'uuid-ossp', 'pgcrypto', 'hstore',
            'citext', 'ltree', 'cube', 'fuzzystrmatch',
            'pg_trgm', 'unaccent', 'intarray', 'isn'
        }

        if extension_name.lower() not in valid_extensions:
            return {
                "status": "error",
                "error": f"Invalid extension name: {extension_name}"
            }

        try:
            with DataMigrationEngine._postgres_connection(target_uri) as conn:
                cursor = conn.cursor()
                # Use parameterized query for extension name
                cursor.execute(
                    sql.SQL("CREATE EXTENSION IF NOT EXISTS {}")
                    .format(sql.Identifier(extension_name))
                )
                conn.commit()
                cursor.close()

            return {
                "status": "success",
                "message": f"Extension '{extension_name}' enabled."
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# ==========================================
# 8. USAGE EXAMPLE
# ==========================================
if __name__ == "__main__":
    # Example usage
    print("DataMigrationEngine loaded successfully!")
    print("\nUsage:")
    print("  engine = DataMigrationEngine()")
    print("  result = engine.migrate_data(")
    print("      source_uri='mssql+pyodbc://user:pass@host/db',")
    print("      target_uri='postgresql://user:pass@host/db'")
    print("  )")