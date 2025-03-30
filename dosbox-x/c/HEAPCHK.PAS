unit HeapChk;

interface

uses Objects;

type
  PHeapCheck = ^THeapCheck;
  THeapCheck = Object(TObject)
    FreeSpace: longint;
    constructor Init;
    destructor Done; virtual;
    procedure PrintSize;
  end;

implementation

procedure THeapCheck.PrintSize;
begin
  writeln('available ', MemAvail, ' bytes');
end;

constructor THeapCheck.Init;
begin
  writeln('heap control started');
  PrintSize;
  FreeSpace := MemAvail;
end;

destructor THeapCheck.Done;
begin
  PrintSize;
  If FreeSpace <> MemAvail then 
    writeln('ERROR: leaked ', FreeSpace - MemAvail, 'byte(s)');
end;

end.
