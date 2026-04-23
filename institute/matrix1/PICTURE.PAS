uses Graph, Crt;

var
 grDriver: Integer;
 grMode: Integer;
 ErrCode: Integer;
 i : integer;
 s: string;
begin
 grDriver := VGA;
 grMode   := VGAMed;
 InitGraph(grDriver, grMode,'');
 ErrCode := GraphResult;
 if ErrCode = grOk then
 begin  { Do graphics }
   for i:=1 to 9 do begin
     SetTextStyle( TriplexFont, HorizDir, i );
     SetColor( i );
     OutTextXY( i*1, i*3, 'Alexander');
     Delay( 100 );
     SetColor( Black );
     OutTextXY( i*1, i*3, 'Alexander');
   end;
   SetColor( i );
   OutTextXY( i*1, i*3, 'Alexander');
   for i:=1 to 9 do begin
     SetTextStyle( TriplexFont, HorizDir, i );
     SetColor( i );
     OutTextXY( i*1, GetMaxY-i*3, 'Demin');
     Delay( 100 );
     SetColor( Black );
     OutTextXY( i*1, GetMaxY-i*3, 'Demin');
   end;
   SetColor( i );
   OutTextXY( i*1, GetMaxY-i*3, 'Demin');

   Readln;
   CloseGraph;
 end
 else
   Writeln('Graphics error:', GraphErrorMsg(ErrCode));
end.
