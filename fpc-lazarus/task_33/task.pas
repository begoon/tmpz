program task;
const
    Nmax = 20;
var
    fin, fout: TextFile;
    N: integer;
    i: integer;
    A, B: array[1..Nmax] of integer;

    max, v: real;
    maxI: integer;

function triange(a, b: real): real;
var
    c: real;
    s: real;
begin
    c := (a+b)/2;
    s := (a+b+c)/2;
    triange := sqrt(s*(s-a)*(s-b)*(s-c));
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
    for i := 1 to N do read(fin, B[i]);
    for i := 1 to N do write(fout, B[i], ' '); writeln(fout);

    max := triange(A[1], B[1]);
    maxI := 1;
    for i := 2 to 5 do begin
        v := triange(A[i], B[i]);
        if v > max then begin
            max := v;
            maxI := i;
        end;
    end;
    writeln(fout, maxI);

    close(fin);
    close(fout);
end.
