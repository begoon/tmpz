program task;
const
    Nmax = 20;
var
    fin, fout: TextFile;
    N: integer;
    i, j: integer;
    A, C: array[1..Nmax] of integer;

    max, sum: integer;
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

    max := A[1] * C[1];
    for i := 1 to N do begin
        sum := 0;
        for j := 1 to N do sum := sum + A[j] * C[j];
        if sum > max then max := sum;
    end;
    writeln(fout, max);

    close(fin);
    close(fout);
end.
