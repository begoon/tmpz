unit Gadgets;

{$F+,O+,S-,D-,Q-}

interface

uses Dos, Objects, Views, App, Drivers;

type
  PHeapView = ^THeapView;
  THeapView = object(TView)
    OldMem : longint;
    constructor Init(var Bounds: TRect);
    procedure Draw; virtual;
    procedure Update;
  end;

  PClockView = ^TClockView;
  TClockView = object(TView)
    Rate: byte;
    LastTime: DateTime;
    TimeStr: string[10]; { HH:MM:SS }
    constructor Init(var Bounds: TRect);
    procedure Draw; virtual;
    function FormatTimeStr(H, M, S: Word): String; virtual;
    procedure Update; virtual;
  end;

implementation

constructor THeapView.Init(var Bounds: TRect);
begin
  inherited Init(Bounds);
  OldMem := 0;
end;

procedure THeapView.Draw;
var
  buf: TDrawBuffer;
  s: string;
  c: byte;
begin
  OldMem := MemAvail;
  Str(OldMem:Size.X, s);
  c := GetColor(2);
  MoveChar(buf, ' ', c, Size.X);
  MoveStr(buf, s, c);
  WriteLine(0, 0, Size.X, 1, buf);
end;


procedure THeapView.Update;
begin
  if (OldMem <> MemAvail) then DrawView;
end;

function PadZero(w: Word): String;
var s: String;
begin
  Str(w: 0, s);
  PadZero := Copy('00', 1, 2 - Length(s)) + s;
end;

constructor TClockView.Init(var Bounds: TRect);
begin
  inherited Init(Bounds);
  FillChar(LastTime, SizeOf(LastTime), #$FF);
  TimeStr := '';
  Rate := 1;
end;

procedure TClockView.Draw;
var
  buf: TDrawBuffer;
  color: byte;
begin
  color := GetColor(2);
  MoveChar(buf, ' ', color, Size.X);
  MoveStr(buf, TimeStr, color);
  WriteLine(0, 0, Size.X, 1, buf);
end;

procedure TClockView.Update;
var
  h, m, s, ms: word;
begin
  GetTime(h, m, s, ms);
  if Abs(s - LastTime.sec) >= Rate then
  begin
    with LastTime do
    begin
      Hour := h;
      Min := m;
      Sec := s;
    end;
    TimeStr := FormatTimeStr(h, m, s);
    DrawView;
  end;
end;

function TClockView.FormatTimeStr(H, M, S: Word): String;
begin
  FormatTimeStr := PadZero(h)+ ':'+ PadZero(m) + ':' + PadZero(s);
end;

function IntToStr(I : longint) : string;
var 
  s: string;
begin
  Str(I, S);
  IntToStr:=S;
end;

end.
