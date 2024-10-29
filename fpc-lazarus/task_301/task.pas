program task;
const
    Nmax = 20;
var
    N: integer;
    i: integer;
    X, Y, Z: array[1..Nmax] of integer;

procedure order_variables(var x, y, z: integer);
var
  temp: integer;
begin
  if x > y then
  begin
    temp := x;
    x := y;
    y := temp;
  end;
  if y > z then
  begin
    temp := y;
    y := z;
    z := temp;
  end;
  if x > y then
  begin
    temp := x;
    x := y;
    y := temp;
  end;
end;

begin
    readln(N);

    for i := 1 to N do read(X[i]);
    for i := 1 to N do read(Y[i]);
    for i := 1 to N do read(Z[i]);

    for i := 1 to N do begin
        order_variables(X[i], Y[i], Z[i]);
    end;

    for i := 1 to N do write(X[i], ' '); writeln();
    for i := 1 to N do write(Y[i], ' '); writeln();
    for i := 1 to N do write(Z[i], ' '); writeln();
end.
