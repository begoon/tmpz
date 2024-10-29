program task;
const
    Nmax = 20;
var
    fin, fout: TextFile;
    N: integer;
    i: integer;
    A: array[1..Nmax] of integer;

    min, delta: integer;
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

    min := abs(A[1]) - abs(A[N]);
    for i := 1 to N do begin
        delta := abs(A[i]) - abs(A[N-i+1]);
        if delta < min then min := delta;
    end;
    writeln(fout, min);

    close(fin);
    close(fout);
end.
