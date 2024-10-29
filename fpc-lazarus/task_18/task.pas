program task;
const
    Nmax = 20;
var
    fin, fout: TextFile;
    N: integer;
    i: integer;
    A: array[1..Nmax] of integer;

    max, v: real;
    maxI: integer;
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

    max := sqrt(exp(A[1]));
    maxI := 1;
    for i := 2 to N do begin
        v := sqrt(exp(A[i]));
        if v > max then begin
            max := v;
            maxI := i;
        end;
    end;
    writeln(fout, maxI);

    close(fin);
    close(fout);
end.
