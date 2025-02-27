program task;
const
    Nmax = 20;
var
    fin, fout: TextFile;
    N: integer;
    i, j: integer;
    A: array[1..Nmax] of integer;

    max, maxAbs: integer;
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

    max := A[1];
    maxAbs := abs(A[1]);
    for i := 1 to N do begin
        if A[i] > max then max := A[i];
        if abs(A[i]) > maxAbs then maxAbs := abs(A[i]);
    end;
    writeln(fout, max, ' ', maxAbs);

    close(fin);
    close(fout);
end.
