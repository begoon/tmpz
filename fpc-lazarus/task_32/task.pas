program task;
const
    Nmax = 20;
var
    fin, fout: TextFile;
    N: integer;
    i: integer;
    A, C: array[1..Nmax] of integer;

    min, v: real;
    minI: integer;

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

    min := sqrt(abs(A[1] + C[1]*C[1]*C[1]));
    minI := 1;
    for i := 2 to N do begin
        v := sqrt(abs(A[i] + C[i]*C[i]*C[i]));
        if v < min then begin
            min := v;
            minI := i;
        end;
    end;
    writeln(fout, minI);

    close(fin);
    close(fout);
end.
