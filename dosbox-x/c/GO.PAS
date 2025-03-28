uses App;

type
  TVivoApplication = object(TApplication)
  end;

var
  Application: TVivoApplication;

begin
  Application.Init;
  Application.Run;
  Application.Done;
end.
