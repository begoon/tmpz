program task;
const
    Nmax = 20;
var
    fin, fout: TextFile;
    N: integer;
    i: integer;
    A: array[1..Nmax] of integer;

    minA, minI, maxA, maxI: integer;
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

    minA := A[1];
    minI := 1;
    maxA := A[1];
    maxI := 1;
    for i := 1 to N do begin
        if A[i] < minA then begin
            minA := A[i];
            minI := i;
        end;
        if A[i] > maxA then begin
            maxA := A[i];
            maxI := i;
        end;
    end;
    writeln(fout, maxI + minI);

    close(fin);
    close(fout);
end.
