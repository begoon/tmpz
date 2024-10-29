program task;
const
    Nmax = 20;
var
    fin, fout: TextFile;
    N: integer;
    i, j: integer;
    A, C: array[1..Nmax] of integer;

    min, v, sum, mult: real;

function power(a: integer; n: integer): real;
begin
    power := exp(n*ln(a))
end;

begin
    if ParamCount<2 then begin 
        writeln('Не заданы параметры программы: входной и выходной файлы.'); 
        readln;
        exit 
    end;

    Assign(fin, ParamStr(1));
    Assign(fout, ParamStr(2));
    Reset(fin);
    Rewrite(fout);

    readln(fin, N);
    writeln(fout, N);

    for i := 1 to N do read(fin, A[i]);
    for i := 1 to N do write(fout, A[i], ' '); writeln(fout);
    for i := 1 to N do read(fin, C[i]);
    for i := 1 to N do write(fout, C[i], ' '); writeln(fout);

    min := A[1] / (1 + abs(C[1]));
    for i := 2 to N do begin
        mult := 1;
        for j := 1 to i do mult := mult * A[j] * A[j];
        sum := 0;
        for j := 1 to i do sum := sum + C[j];
        v := mult / (1 + abs(sum));
        if v < min then min := v;
    end;
    writeln(fout, min);

    close(fin);
    close(fout);
end.
