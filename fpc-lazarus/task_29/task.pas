program task;
const
    Nmax = 20;
var
    fin, fout: TextFile;
    N: integer;
    i, j: integer;
    A: array[1..Nmax] of integer;

    min, mult: real;
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

    min := 0;
    minI := 1;
    for i := 1 to N do begin
        mult := 1;
        for j := 1 to i do mult := mult * sqrt(abs(A[j]));
        if mult < min then begin
            min := mult;
            minI := i;
        end;
    end;
    writeln(fout, minI);

    close(fin);
    close(fout);
end.
