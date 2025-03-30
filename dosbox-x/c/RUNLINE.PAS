{$A+,B-,E-,F+,G+,I+,L+,N-,O-,P-,Q-,R-,S-,T-,V-,X+,Y+}
Unit RunLine;

Interface

Uses Dos, Objects, Drivers, App, Views;

Const
  riRunningLine = $01;
  riMaxCount    = $02;
  riCurrCount   = $04;
  riPercent     = $08;
  riExecTime    = $10;
  riMemAvail    = $20;
  riFullInf     = riRunningLine or riMaxCount or riCurrCount or
                  riPercent     or riExecTime or riMemAvail;
Type
  PRunningLine = ^TRunningLine;
  TRunningLine = Object(TWindow)
    constructor Init( ATitle : string; MaxCount : longint; LineSize : byte;
                      AOptions : byte);
    constructor InitRect( R : TRect; ATitle : string; MaxCount : longint;
                          AOptions: byte);
    procedure StatusDisplay( CurrCount : longint);
   private
    PInterior : PView;
  end;

Implementation

Type

  PRunningLineInterior = ^TRunningLineInterior;
  TRunningLineInterior = Object(TView)
    constructor Init( R : TRect; MaxCount : longint; AOptions : byte);
    procedure Draw; virtual;
    procedure SetCurrentCount( CurrCount : longint );
   private
    riOptions    : byte;
    CurrentCount : longint;
    MaximumCount : longint;
    Time         : longint;
    function FillTime : string;
    function LongToStr( D : longint) : string;
    function MakeStr( N : word ) : string;
  end;

Constructor TRunningLine.init;
var
  R   : TRect;
  Row : byte;
  i   : byte;
begin
  Row:=0;
  for i:=0 to 5 do
   if (AOptions and ($0001 shl i))<>0 then inc(Row);
  if not ( LineSize in [ 32 .. 79]) then LineSize:=32;
  R.Assign( 0, 0, LineSize, Row+4);
  R.Move((DeskTop^.Size.x-R.B.X) div 2, (DeskTop^.Size.y-R.B.Y) div 2);
  InitRect( R, ATitle, MaxCount, AOptions);
end;

Constructor TRunningLine.InitRect;
begin
  TWindow.init( R, ATitle, wnNoNumber);
  Options:=Options and ( not ofSelectable );
  GetExtent(R);
  R.Grow(-1,-1);
  PInterior:=New( PRunningLineInterior, Init( R, MaxCount, AOptions));
  Insert(PInterior);
  DeskTop^.Insert(@Self);
end;

procedure TRunningLine.StatusDisplay;
var
  PRL : PRunningLineInterior absolute PInterior;
begin
  PRL^.SetCurrentCount(CurrCount);
  PRL^.DrawView;
end;

constructor TRunningLineInterior.Init;
var
  H, M, S, S100 : word;
begin
  Inherited Init( R);
  riOptions:=AOptions;
  MaximumCount:=Abs(MaxCount);
  CurrentCount:=0;
  GetTime(H, M, S, S100);
  Time:=(H*60+M)*60+S;
end;

function TRunningLineInterior.FillTime : string;
var
  Res           : string;
  H, M, S, S100 : word;
  NewTime       : longint;
  Data          : record
                    H, M, S : longint;
                  end;
begin
  GetTime( H, M, S, S100);
  NewTime:=(H*60+M)*60+S-Time;
  if NewTime<0 then Inc( NewTime, 24*60+60);
  with Data do begin
    S := NewTime mod 60;
    M := (NewTime div 60) mod 60;
    H := NewTime div 3600;
  end;
  FormatStr( Res, '%02d:%02d:%02d', Data);
  FillTime:=Res;
end;

function TRunningLineInterior.MakeStr;
var
  S : string;
begin
  FillChar( S[1], N, ' ');
  S[0]:=chr(n);
  MakeStr:=s;
end;

function TRunningLineInterior.LongToStr;
var
  S : string;
begin
  Str( D:8, S);
  LongToStr:=S;
end;

procedure TRunningLineInterior.Draw;
const
  riFirstLine = $80;
  riMass: array [0..7] of byte =
    ( riFirstLine, riRunningLine, riMaxCount, riCurrCount,
      riPercent, riExecTime, riMemAvail, riFirstLine );
var
  Percent : byte;
  Color   : word;
  Cols    : byte;
  Row     : integer;
  S       : string;
  B       : TDrawBuffer;
  i       : byte;

procedure ProcStr( H, P : string );
begin
  S:=' '+H+MakeStr(Size.X-2-Length(H+P))+P+' ';
end;

begin
  if MaximumCount = 0
    then Percent:=0
    else Percent:=CurrentCount*100 div MaximumCount;
  Cols:=Percent*(Size.x-2) div 100;
  Color:=GetColor(1);
  Row:=-1;
  for i:=0 to 7 do begin
    S[0]:=CHR(0);
    case ((riOptions or riFirstLine) and riMass[i]) of
      riFirstLine  : ProcStr('','');
      riRunningLine: begin
                       while Length(S)<Cols do S:=S+#219;
                       while Length(S)<Size.x-2 do S:=S+#177;
                       S:=' '+S+' ';
                     end;
      riMaxCount  : ProcStr('Total', LongToStr(MaximumCount));
      riCurrCount : ProcStr('Count', LongToStr(CurrentCount));
      riPercent   : ProcStr('Percent', LongToStr(Percent)+'%');
      riExecTime  : ProcStr('Time', FillTime);
      riMemAvail  : ProcStr('Available memory',
                            LongToStr(MemAvail div 1024)+'kb');
    end;
    if Length(S)<>0 then begin
      Inc(Row);
      Movestr(B, S, Color);
      WriteLine(0, Row, Size.x, 1, B);
    end;
  end;
end;

procedure TRunningLineInterior.SetCurrentCount;
begin
  CurrentCount:=abs(CurrCount) mod ( MaximumCount+1 );
end;

end.


