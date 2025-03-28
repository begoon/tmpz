uses App, Objects, Menus, MsgBox, Drivers, Views;

type
  TExtApplication = object(TApplication)
    procedure HandleEvent(var Event: TEvent); virtual;
    procedure InitMenuBar; virtual;
    procedure InitStatusLine; virtual;
  end;

var
  Application: TExtApplication;

const
  cmAbout = 1000;
  cmManifest = 1001;

procedure TExtApplication.HandleEvent(var Event: TEvent);
var
  R: TRect;
begin
  inherited HandleEvent(Event);
  if Event.What = evCommand then
  begin
    case Event.Command of
      cmAbout:
        begin
          MessageBox(
            #3'Aloha!'#13#13#3'"Ready or not, here I come!"', 
            nil, mfInformation or mfOKButton);
          ClearEvent(Event);
        end;
    end;
  end;
end;

procedure TExtApplication.InitMenuBar;
var
  R: TRect;
begin
  GetExtent(R);
  R.B.Y := R.A.Y + 1;
  MenuBar := New(PMenuBar, Init(R, NewMenu(
    NewSubMenu(#240, hcNoContext, NewMenu(
      NewItem('~A~bout...', '', kbNoKey, cmAbout, hcNoContext,
      nil)),
    nil)
  )));
end;

procedure TExtApplication.InitStatusLine;
var
  R: TRect;
begin
  GetExtent(R);
  R.A.Y := R.B.Y - 1;
  New(StatusLine, Init(R,
    NewStatusDef(0, $EFFF,
      NewStatusKey('~Alt+X~ Exit', kbAltX, cmQuit,
      nil),
    nil)));
end;

begin
  Application.Init;
  Application.Run;
  Application.Done;
end.
