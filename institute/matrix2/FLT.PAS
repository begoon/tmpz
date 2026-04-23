var
  s : string;
begin
  write(#27'!'#4);
  while not eof do begin
    readln(s);
    s:='                             '+s;
    writeln(s);
  end;
end.