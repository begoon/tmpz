program task;
const
    Nmax = 20;
var
    fin, fout: TextFile;
    N: integer;
    i: integer;
    A, C: array[1..Nmax] of integer;

    minA, minC: integer;
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

    minA := A[1];
    minC:= A[1];
    for i := 1 to N do begin
        if A[i] < minA then minA := A[i];
        if C[i] < minC then minC := C[i];
    end;

    writeln(fout, (minA + minC)/2);

    close(fin);
    close(fout);
end.
