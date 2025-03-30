{$A+,B-,E-,F+,G+,I+,L+,N-,O-,P-,Q-,R-,S-,T-,V-,X+,Y+}
{$M 16384,8192,655360}
unit About;

interface

uses
  Dos, Objects, Drivers, Views, Dialogs, App;

const
  hcAbout     = 401;
  hcAboutView = 402;
  
  cmAboutView = 300;

  DeltaTicks  = 70;

type
  PAboutCollection = ^TAboutCollection;
  TAboutCollection = object(TCollection)
    procedure FreeItem(Item: Pointer); virtual;
  end;

  PAboutView = ^TAboutView;
  TAboutView = object(TView)
    LastTick: longint;
    InitialOffset: integer;
    Offset: integer;
    AboutStrs: PAboutCollection;
    constructor Init(R: TRect; AStrs: PAboutCollection);
    procedure  Draw; virtual;
    procedure  Update;
  end;

  PAboutDialog = ^TAboutDialog;
  TAboutDialog = object (TDialog)
    AboutStrs: PAboutCollection;
    AboutView: PAboutView;
    constructor Init(R: TRect; ATitle: String; AStrs: PAboutCollection);
    procedure HandleEvent(var Event: TEvent); virtual;
    procedure GetEvent( var Event : TEvent ) ; virtual;
  end;

implementation

procedure TAboutCollection.FreeItem;
begin
  DisposeStr(Item);
end;

constructor TAboutView.Init;
begin
  inherited Init(R);
  InitialOffset := -AStrs^.Count+3;
  Offset := InitialOffset;
  AboutStrs := AStrs;
end;

procedure TAboutView.Draw;
var
  buf: TDrawBuffer;
  s: string;
  color: word;
  i, j: integer;
begin
  color := Owner^.GetColor($0807);  
  MoveChar(buf, ' ', color, Size.X);

  s := PString(AboutStrs^.At(0))^;
  MoveCStr(buf[(Size.X - CStrLen(s)) div 2], s, color);
  WriteLine(0, 0, Size.X, 1, buf);

  MoveChar(buf, ' ', color, Size.X);
  WriteLine(0, 1, Size.X, 1, buf);

  for i := 2 to Size.Y-1 do begin
    j := Offset + i - 2;
    MoveChar(buf, ' ', color, Size.X);
    if j in [1..AboutStrs^.Count-1] then begin
      s := PString(AboutStrs^.At(j))^;
      MoveCStr(buf[(Size.X - CStrLen(s)) div 2], s, color);
    end;
    WriteLine(0, i, Size.X, 1, buf);
  end;
end;

procedure TAboutView.Update;
var
  H, M, S, MS: word;
  time       : longint;
  i          : longint;
  count      : integer;
begin
  GetTime(H, M, S, MS);
  time := MS + longint(S) * 100 + longint(M) * 6000;
  count := AboutStrs^.Count;
  if Abs(time - LastTick) > DeltaTicks then begin
    Inc(Offset);
    if Offset > count-1 then begin
      Offset := InitialOffset;
    end;
    LastTick := time;
    DrawView;
  end;
end;

constructor TAboutDialog.Init;
begin
  inherited Init(R, ATitle);
  HelpCtx := hcAbout;
  AboutStrs := AStrs;
end;

procedure TAboutDialog.GetEvent(var event: TEvent);
begin
  if AboutView <> nil then AboutView^.Update;
  inherited GetEvent(event);
end;

procedure TAboutDialog.HandleEvent(var event: TEvent);
var
  R: TRect;
begin
  inherited HandleEvent(event);
  case Event.What of
    evCommand: begin
      if (Event.Command = cmAboutView) or (Event.What and evMouse <> 0) then begin
        if AboutView = nil then begin
          Desktop^.TopView^.GetExtent(R);
          R.Grow(-1,-1); 
          Dec(R.B.Y, 3);
          New(AboutView, Init(R, AboutStrs));
          HelpCtx := hcAboutView;
          PGroup(Desktop^.TopView)^.Insert(AboutView);
        end
      end else Exit;
      ClearEvent(event);
    end;
  end;
end;

end.
