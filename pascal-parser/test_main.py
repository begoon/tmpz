import textwrap
import unittest

from main import dump, parse

expected = textwrap.dedent(
    """
        Program demo
          Block:
          Variables:
            x, y: integer
            msg: string
          Procedures:
            procedure incx(a:integer)
              Block:
              Body:
                Compound:
                  Assign x := (x + a)
          Body:
            Compound:
              Assign x := 1
              Assign y := ((2 * (x + 3)) DIV 2)
              If (y >= 4) then BlockStatementt:
                Compound:
                  Assign msg := 'hi'
                  Call incx(y) else While (x < 10) do Assign x := (x + 1)
        """
).strip()


class TestPascalParser(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def test_parse(self):
        parsed = dump(parse())
        self.assertEqual(parsed, expected)


if __name__ == "__main__":
    unittest.main()
