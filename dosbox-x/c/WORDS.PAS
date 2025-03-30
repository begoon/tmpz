{$A+,B-,E-,F+,G+,I+,L+,N-,O-,P-,Q-,R-,S-,T-,V-,X+,Y+}
{$M 16384,8192,655360}

Unit Words;

Interface

Uses Objects;

Type
  PDupStrCollection = ^TDupStrCollection;
  TDupStrCollection = object( TStringCollection )
    procedure InsStr( S : string ); virtual;
  end;

  PWord = ^TWord;
  TWord = object( TObject )
    Word  : String;
    State : String;
    Value : String;
    Lines : PDupStrCollection;
    constructor Init( AWord, AState, AValue : string );
    destructor Done; virtual;
  end;

  PWordCollection = ^TWordCollection;
  TWordCollection = object( TStringCollection )
    function Compare( Key1, Key2: Pointer): Integer;
                     virtual;
    procedure FreeItem( Item: Pointer ); virtual;
    function Find( S : string ) : integer;
    procedure InsNStr( n : integer; S : string );
  end;

  PSCollection = ^TSCollection;
  TSCollection = object( TCollection )
    procedure FreeItem( Item : Pointer ); virtual;
  end;

  function UpStr( S : string ) : string;

Implementation

function UpStr( S : string ) : string;
var
  i : integer;
begin
  for i:=1 to Length(S) do S[i]:=UpCase(S[i]);
  UpStr:=S;
end;

procedure TDupStrCollection.InsStr;
begin
  if IndexOf(@S)=-1 then Insert( NewStr(S) );
end;

constructor TWord.Init;
begin
  Word:=AWord;
  State:=AState;
  Value:=AValue;
  Lines:=New( PDupStrCollection, Init( 1, 1 ) );
end;

destructor TWord.Done;
begin
  Dispose( Lines, Done );
  Inherited Done;
end;

function TWordCollection.Compare;
begin
  Compare:=inherited Compare( @PWord(Key1)^.Word, @PWord(Key2)^.Word );
end;

procedure TWordCollection.FreeItem;
begin
  if Item<>nil then Dispose(PWord(Item), Done);
end;

function TWordCollection.Find;
var
  i : integer;
begin
  Find:=-1;
  for i:=0 to Count-1 do if S=PWord(At(i))^.Word then Find:=i;
end;

procedure TWordCollection.InsNStr;
begin
  PWord(At(n))^.Lines^.InsStr(S);
end;

procedure TSCollection.FreeItem;
begin
  DisposeStr( Item );
end;

end.