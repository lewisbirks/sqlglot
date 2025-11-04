from __future__ import annotations

from sqlglot import exp
from sqlglot.dialects.dialect import Dialect
from sqlglot.generator import Generator
from sqlglot.parser import Parser
from sqlglot.tokens import Tokenizer, TokenType


def _convert_like_wildcards(expression):
    """Convert Access wildcards (* and ?) to SQL wildcards (% and _)"""
    if isinstance(expression, exp.Like) and isinstance(expression.expression, exp.Literal):
        pattern = expression.expression.this
        if isinstance(pattern, str):
            pattern = pattern.replace("*", "%").replace("?", "_")
            expression.expression.this = pattern
    return expression


class Access(Dialect):
    class Tokenizer(Tokenizer):
        IDENTIFIERS = [("[", "]")]  # Access uses square brackets for identifiers
        QUOTES = ["'", '"', ("#", "#")]  # Access supports both single and double quotes, and # for dates
        
        KEYWORDS = {
            **Tokenizer.KEYWORDS,
            "YESNO": TokenType.BOOLEAN,
            "CURRENCY": TokenType.DECIMAL,
            "MEMO": TokenType.TEXT,
            "AUTOINCREMENT": TokenType.AUTO_INCREMENT,
        }

    class Parser(Parser):
        FUNCTIONS = {
            **Parser.FUNCTIONS,
            "IIF": lambda args: exp.If(
                this=args[0] if args else None,
                true=args[1] if len(args) > 1 else None,
                false=args[2] if len(args) > 2 else None,
            ),
            "LCASE": lambda args: exp.Lower(this=args[0] if args else None),
            "UCASE": lambda args: exp.Upper(this=args[0] if args else None),
            "MID": lambda args: exp.Substring(
                this=args[0] if args else None,
                start=args[1] if len(args) > 1 else None,
                length=args[2] if len(args) > 2 else None,
            ),
            "NOW": lambda args: exp.CurrentTimestamp(),
            "MOD": lambda args: exp.Mod(
                this=args[0] if args else None,
                expression=args[1] if len(args) > 1 else None,
            ),
            "NZ": lambda args: exp.Coalesce(
                this=args[0] if args else None,
                expressions=[args[1]] if len(args) > 1 else [exp.Literal.string("")],
            ),
        }

        # SQLGlot normalizes function names to uppercase
        FUNCTION_PARSERS = {
            **Parser.FUNCTION_PARSERS,
            "DATEPART": lambda self: self._parse_date_part(),
            "DATEADD": lambda self: self._parse_date_add(),
        }

        _ACCESS_TIME_UNITS = {
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

        def _parse_date_add(self) -> exp.Expression:
            unit = self._parse_bitwise()
            self._match(TokenType.COMMA)
            number = self._parse_bitwise()
            self._match(TokenType.COMMA)
            date = self._parse_bitwise()

            if unit and isinstance(unit, exp.Literal):
                # Map Access time units to standard units
                unit_str = unit.this.lower() if isinstance(unit.this, str) else str(unit.this)
                mapped_unit = self._ACCESS_TIME_UNITS.get(unit_str, unit_str)
                unit = exp.var(mapped_unit)

            return self.expression(exp.TsOrDsAdd, this=date, expression=number, unit=unit)

        def _parse_date_part(self) -> exp.Expression:
            part = self._parse_bitwise()
            self._match(TokenType.COMMA)
            value = self._parse_bitwise()
            
            if part and isinstance(part, exp.Literal):
                # Map Access time units to standard units
                unit = part.this.lower() if isinstance(part.this, str) else str(part.this)
                mapped_unit = self._ACCESS_TIME_UNITS.get(unit, unit)
                part = exp.var(mapped_unit)
            
            return self.expression(exp.Extract, this=part, expression=value)

        RANGE_PARSERS = {
            **Parser.RANGE_PARSERS,
            TokenType.LIKE: lambda self: self._parse_access_like,
        }

        def _parse_access_like(self, this):
            """Parse LIKE with Access wildcard conversion"""
            expression = self._parse_bitwise()
            if isinstance(expression, exp.Literal) and isinstance(expression.this, str):
                # Convert Access wildcards to SQL wildcards
                pattern = expression.this.replace("*", "%").replace("?", "_")
                expression = exp.Literal.string(pattern)
            return self._parse_escape(self.expression(exp.Like, this=this, expression=expression))

    class Generator(Generator):
        TYPE_MAPPING = {
            **Generator.TYPE_MAPPING,
            exp.DataType.Type.BOOLEAN: "YESNO",
            exp.DataType.Type.DECIMAL: "CURRENCY",
            exp.DataType.Type.TEXT: "MEMO",
        }
