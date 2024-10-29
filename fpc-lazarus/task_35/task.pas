program task;
const
    Nmax = 20;
var
    fin, fout: TextFile;
    N: integer;
    i: integer;
    A, B: array[1..Nmax] of integer;

    minSquare, minPerimeter, v, c: real;

function sideC(a, b: real): real;
begin
    sideC := 4.0/(3.0)/(a+b);
end;

function triangeSquare(a, b, c: real): real;
var
    s: real;
begin
    s := (a+b+c)/2;
    triangeSquare := sqrt(s*(s-a)*(s-b)*(s-c));
end;

function triangePerimeter(a, b, c: real): real;
begin
    triangePerimeter := a+b+c;
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

    minSquare := 0;
    minPerimeter := 0;
    for i := 1 to N do begin
        c := sideC(A[i], B[i]);
        v := triangeSquare(A[i], B[i], c);
        if (minSquare = 0) or (v < minSquare) then begin
            minSquare := v;
            minPerimeter := triangePerimeter(A[i], B[i], c);
        end;
    end;
    writeln(fout, minPerimeter);

    close(fin);
    close(fout);
end.
