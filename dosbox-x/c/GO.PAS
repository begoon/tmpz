uses dos;

var
  s: string;
  i: integer;

const
  w = 20;

begin
  writeln(DosVersion);
  Str(123:w, s);
  writeln(s);
  writeln(cseg, ' ', dseg, ' ', sseg);
  for i := 0 to EnvCount do writeln(EnvStr(i));
  readln;
end.
