{$A+,B-,D+,E-,F+,G+,I+,L+,N-,O-,P-,Q-,R-,S-,T-,V-,X+,Y+}
{$M 16384,8192,655360}

Unit XRef;

interface

Uses Dos, Objects, RunLine, Words, ProcWord;

Const

  HiComma     = '''';
  Power       = '^';
  LetChars    = ['A'..'Z'];
  IDChars     = LetChars+['0'..'9', '_'];
  StSize      = 25;
  VlSize      = 15;
  TpSize      = 10;
  IdSize      = 32;

Var

  ID        : string;
  LastID    : string;
  LastState : Boolean;
  ScanedFlag: Boolean;
  ScanedChar: Char;
  Lines     : integer;
  Process   : PRunningLine;
  NowCount  : longint;
  State     : string;

  procedure MakeCRef( var fIn, fWords, fOut : Text; MaxCount : longint );

implementation

function ExpNStr( S : string; N : integer ) : string;
begin
  while Length(S)<N do S:=S+' ';
  ExpNStr:=S;
end;

function MakeStr( N : integer ) : string;
var
  S : string;
begin
  FillChar( S, N+1, ' ');
  S[0]:=Chr(N);
  MakeStr:=S;
end;

function LineToStr : string;
var
  S : string;
begin
  Str( Lines, S );
  LineToStr:=S;
end;

procedure MakeCRef;

function ScanWord : string;
var
  Post : boolean;
  Sym  : char;
  Res  : string;
  Cts  : boolean;
begin
  Res:='';
  Post:=False;
  Cts:=false;
  while not ( Eof(fIn) or Post ) do begin
    if ScanedFlag
      then begin
        Sym:=ScanedChar;
        ScanedFlag:=False;
      end
      else begin
        Read( fIn, Sym );
        Inc( NowCount );
      end;
    if Sym=#10 then Inc( Lines );
    if Cts then Res:=Res+Sym
    else begin
      if UpCase(Sym) in IDChars
        then Res:=Res+Sym
        else if Sym in [' ',#13,#10]
          then Post:=Length(Res)<>0
          else begin
            if Length(Res)=0
              then Res:=Sym
              else begin
                ScanedFlag:=True;
                ScanedChar:=Sym;
              end;
            Post:=True;
          end;
    end;
    if Sym=HiComma then
      if Cts then begin
        Cts:=False;
        Post:=True;
      end else
        if Res[1]=HiComma then begin
          Cts:=True;
          Post:=False;
        end;
  end;
  ScanWord:=Res;
end;

function ScanItem : string;
var
  S     : string;
  Sym   : char;
  Last  : string;
  Post  : boolean;
  State : Boolean;
begin
  Sym:=#0;
  State:=False;
  repeat
    S:=ScanWord;
    LastState:=State;
    if Length(S)=1 then begin
      Last:=Sym;
      Sym:=S[1];
      case Sym of
        '{' : If not State then State:=True;
        '}' : If State then State:=False;
        '*' : If (Last='(') and (not State) then State:=True;
        ')' : If (Last='*') and State then State:=False;
      end;
    end;
    Post:=not ( LastState or State );
  until Post;
  ScanItem:=S;
end;

function GetNStrs( Lines : PStringCollection; var Idx : integer ) : string;
var
  S : string;
begin
  S:='';
  while (Idx<Lines^.Count) and (Length(S)<StSize-6) do begin
    S:=S+PString(Lines^.At(Idx))^+' ';
    Inc(Idx);
  end;
  GetNStrs:=S;
end;

procedure MakeTStr( Id, Tp, Vl, St : string );
begin
  Writeln( fOut, '1 ', ExpNStr( Id, IdSize),
                 '2 ', ExpNStr( Tp, TpSize),
                 '3 ', ExpNStr( Vl, VlSize),
                 '4 ', ExpNStr( St, StSize),
                 '5 ' );
end;

{ ------------------------------------------------------------------------ }
{  ��ନ஢�⥫� ��ப ��� ࠧ�������
}
procedure MakeDelim( S : string );
begin
  Writeln( fOut, S[1], MakeStr(IdSize+1),
                 S[2], MakeStr(TpSize+1),
                 S[2], MakeStr(VlSize+1),
                 S[2], MakeStr(StSize+2),
                 S[3] );
end;

var
  Idx     : integer;
  flFirst : boolean;
  S       : string;
  i, j    : integer;

begin

  WordsInit( fWords );
  ScanedFlag:=false;
  ID:='';
  Lines:=1;

  NowCount:=0;
  Process:=New( PRunningLine,
                Init( 'Analysing source file', MaxCount, 50,
                      riRunningLine or riPercent or
                      riExecTime or riMemAvail ) );

  State:='';
  While Not Eof( fIn ) do begin
    Process^.StatusDisplay(NowCount);
    LastID:=ID;
    ID:=UpStr(ScanItem);
    if ID[1] in LetChars then begin
      if IsPreWord(ID) then begin
        State:=ID;
        ID:=UpStr(ScanItem);
        if not IsResWord(ID) then begin
          i:=NewWords^.Find(ID);
          if i=-1 then begin
            NewWords^.Insert( New( PWord,
                              Init(ID, State, 'FAR')));
            i:=NewWords^.Find(ID);
          end;
          NewWords^.InsNStr(i, '#'+LineToStr);
        end;
        State:='';
      end
      else if IsPstWord(ID) then State:=ID
      else if ID='BEGIN' then begin
        i:=1;
        repeat
          Process^.StatusDisplay(NowCount);
          ID:=UpStr(ScanItem);
          if (ID='BEGIN') or (ID='CASE') then inc( i );
          if ID='END' then dec( i );
          if not IsResWord(ID) then begin
            j:=NewWords^.Find(ID);
            if j<>-1 then NewWords^.InsNStr(j, LineToStr);
          end;
        until i=0;
        State:='';
      end
      else
      if IsPstWord(State) and (not IsResWord(ID)) and (LastID<>Power)
      then begin
        S:='';
        if State<>'LABEL' then begin
          S:=UpStr(ScanItem);
          S:=UpStr(ScanItem);
        end;
        i:=NewWords^.Find(ID);
        if i=-1 then begin
          NewWords^.Insert(
            New( PWord, Init(ID, State, S) ));
          i:=NewWords^.Find(ID);
        end;
        NewWords^.InsNStr(i, '#'+LineToStr);
        i:=0;
        ID:=S;
        flFirst:=True;
        repeat
          Process^.StatusDisplay(NowCount);
          if flFirst then begin
            ID:=S;
            flFirst:=False;
          end
          else ID:=UpStr(ScanItem);
          if (ID='CASE') or (ID='RECORD') then inc( i );
          if ID='END' then dec( i );
          if not IsResWord(ID) then begin
            j:=NewWords^.Find(ID);
            if j<>-1 then NewWords^.InsNStr(j, LineToStr);
          end;
        until ((i=0) and (ID=';')) or Eof(fIn);
      end;
    end;
  end;

  Process^.StatusDisplay(NowCount);
  Dispose( Process, Done );

  Process:=New( PRunningLine,
                Init( 'Building the table',
                      NewWords^.Count, 50,
                      riRunningLine or riPercent or
                      riExecTime or riMemAvail ) );
  MakeDelim('0');
  MakeTStr('Identifiers', 'Sorts',
           'Values', 'Strings numbers' );
  MakeDelim('0');
  for i:=0 to NewWords^.Count-1 do
    with PWord(NewWords^.At(i))^ do begin
      Process^.StatusDisplay( i );
      Idx:=0;
      MakeTStr(Word, State, Value, GetNStrs(Lines, Idx) );
      while Idx<Lines^.Count do
        MakeTStr( '', '', '', GetNStrs(Lines, Idx) );
    end;
  MakeDelim('9');

  Dispose( Process, Done );
  WordsDone;

end;

end.