from tests.dialects.test_dialect import Validator


class TestAccess(Validator):
    dialect = "access"

    def test_bracket_identifiers(self):
        self.validate_all(
            "SELECT [Customer Name] FROM [Customers]",
            write={
                "": 'SELECT "Customer Name" FROM "Customers"',
                "redshift": 'SELECT "Customer Name" FROM "Customers"',
            },
        )

    def test_iif_function(self):
        self.validate_all(
            'SELECT IIF([Age] > 18, "Adult", "Minor") FROM [Users]',
            write={
                "": "SELECT CASE WHEN \"Age\" > 18 THEN 'Adult' ELSE 'Minor' END FROM \"Users\"",
                "redshift": "SELECT CASE WHEN \"Age\" > 18 THEN 'Adult' ELSE 'Minor' END FROM \"Users\"",
            },
        )

    def test_string_functions(self):
        self.validate_all(
            "SELECT LCASE([Name]) FROM [Users]",
            write={
                "": 'SELECT LOWER("Name") FROM "Users"',
                "redshift": 'SELECT LOWER("Name") FROM "Users"',
            },
        )

        self.validate_all(
            "SELECT UCASE([Title]) FROM [Books]",
            write={
                "": 'SELECT UPPER("Title") FROM "Books"',
                "redshift": 'SELECT UPPER("Title") FROM "Books"',
            },
        )

        self.validate_all(
            "SELECT MID([Description], 1, 10) FROM [Products]",
            write={
                "": 'SELECT SUBSTRING("Description", 1, 10) FROM "Products"',
                "redshift": 'SELECT SUBSTRING("Description" FROM 1 FOR 10) FROM "Products"',
            },
        )

    def test_now_function(self):
        self.validate_all(
            "SELECT NOW() FROM [Orders]",
            write={
                "": 'SELECT CURRENT_TIMESTAMP() FROM "Orders"',
                "redshift": 'SELECT GETDATE() FROM "Orders"',
            },
        )

    def test_like_wildcards(self):
        self.validate_all(
            "SELECT * FROM [Users] WHERE [Name] LIKE 'John*'",
            write={
                "": 'SELECT * FROM "Users" WHERE "Name" LIKE \'John%\'',
                "redshift": 'SELECT * FROM "Users" WHERE "Name" LIKE \'John%\'',
            },
        )

        self.validate_all(
            "SELECT * FROM [Users] WHERE [Name] LIKE 'J?hn'",
            write={
                "": 'SELECT * FROM "Users" WHERE "Name" LIKE \'J_hn\'',
                "redshift": 'SELECT * FROM "Users" WHERE "Name" LIKE \'J_hn\'',
            },
        )

    def test_date_literals(self):
        self.validate_all(
            "SELECT * FROM [Orders] WHERE [OrderDate] = #2023-01-15#",
            write={
                "": 'SELECT * FROM "Orders" WHERE "OrderDate" = \'2023-01-15\'',
                "redshift": 'SELECT * FROM "Orders" WHERE "OrderDate" = \'2023-01-15\'',
            },
        )

    def test_mod_operator(self):
        self.validate_all(
            "SELECT MOD([ID], 10) FROM [Users]",
            write={
                "": 'SELECT "ID" % 10 FROM "Users"',
                "tsql": "SELECT [ID] % 10 FROM [Users]",
            },
        )

    def test_nz_function(self):
        # NZ with default value
        self.validate_all(
            "SELECT NZ([Name], 'Unknown') FROM [Users]",
            write={
                "": 'SELECT COALESCE("Name", \'Unknown\') FROM "Users"',
                "redshift": 'SELECT COALESCE("Name", \'Unknown\') FROM "Users"',
            },
        )

        # NZ without default value (defaults to empty string)
        self.validate_all(
            "SELECT NZ([Name]) FROM [Users]",
            write={
                "": 'SELECT COALESCE("Name", \'\') FROM "Users"',
                "redshift": 'SELECT COALESCE("Name", \'\') FROM "Users"',
            },
        )

    def test_date_part_function(self):
        time_unit_mappings = {
            "yyyy": "year",
            "q": "quarter",
            "m": "month",
            "y": "dayofyear",
            "d": "day",
            "w": "dayofweek",
            "ww": "week",
            "h": "hour",
            "n": "minute",
            "s": "second",
        }

        for access_unit, standard_unit in time_unit_mappings.items():
            with self.subTest(access_unit=access_unit):
                self.validate_all(
                    f"SELECT DatePart('{access_unit}', [OrderDate]) FROM [Orders]",
                    write={
                        "": f'SELECT EXTRACT({standard_unit} FROM "OrderDate") FROM "Orders"',
                        "redshift": f'SELECT EXTRACT({standard_unit} FROM "OrderDate") FROM "Orders"',
                    },
                )

    def test_date_add_function(self):
        self.validate_all(
            "SELECT DateAdd('d', 30, [OrderDate]) FROM [Orders]",
            write={
                "": 'SELECT TS_OR_DS_ADD("OrderDate", 30, DAY) FROM "Orders"',
                "redshift": 'SELECT DATEADD(DAY, 30, "OrderDate") FROM "Orders"',
            },
        )

    def test_ampersand_concatenation(self):
        self.validate_all(
            "SELECT [Name] & ' - ' & [ID] FROM [Users]",
            write={
                "": 'SELECT "Name" || \' - \' || "ID" FROM "Users"',
                "redshift": 'SELECT "Name" || \' - \' || "ID" FROM "Users"',
            },
        )

    def test_exclamation_syntax(self):
        self.validate_all(
            "SELECT STAT_ORDANAEL_1!MC FROM [Orders]",
            write={
                "": 'SELECT STAT_ORDANAEL_1.MC FROM "Orders"',
                "redshift": 'SELECT STAT_ORDANAEL_1.MC FROM "Orders"',
            },
        )

    def test_isnull_function(self):
        self.validate_all(
            "SELECT IsNull([Name]) FROM [Users]",
            write={
                "": 'SELECT "Name" IS NULL FROM "Users"',
                "redshift": 'SELECT "Name" IS NULL FROM "Users"',
            },
        )

    def test_int_function(self):
        self.validate_all(
            "SELECT Int([Price] / 3.5) FROM [Products]",
            write={
                "": 'SELECT CAST("Price" / 3.5 AS INT) FROM "Products"',
                "redshift": 'SELECT CAST(CAST("Price" AS DOUBLE PRECISION) / 3.5 AS INTEGER) FROM "Products"',
            },
        )

    def test_date_diff_function(self):
        self.validate_all(
            'SELECT DateDiff("d", [StartDate], [EndDate]) FROM [Orders]',
            write={
                "": 'SELECT DATEDIFF("EndDate", "StartDate", DAY) FROM "Orders"',
                "redshift": 'SELECT DATEDIFF(DAY, "StartDate", "EndDate") FROM "Orders"',
            },
        )

    def test_date_function(self):
        self.validate_all(
            "SELECT Date() AS now",
            write={"": "SELECT CURRENT_TIMESTAMP() AS now", "redshift": "SELECT GETDATE() AS now"},
        )
