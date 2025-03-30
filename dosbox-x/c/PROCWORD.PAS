{$A+,B-,E-,F+,G+,I+,L+,N-,O-,P-,Q-,R-,S-,T-,V-,X+,Y+}
{$M 16384,8192,655360}

Unit ProcWord;

interface

Uses Objects, Words, TextLoad;

var

  ResWords  : PStringCollection;
  NewWords  : PWordCollection;
  PreWords  : PStringCollection;
  PstWords  : PStringCollection;

  procedure WordsInit( var fWords : text );
  procedure WordsDone;
  function IsResWord( S : string ) : boolean;
  function IsPstWord( S : string ) : boolean;
  function IsPreWord( S : string ) : boolean;
  function IsNewWord( S : string ) : boolean;

implementation

function IsResWord( S : string ) : boolean;
begin
  IsResWord:=ResWords^.IndexOf(@S)<>-1;
end;

function IsPstWord( S : string ) : boolean;
begin
  IsPstWord:=PstWords^.IndexOf(@S)<>-1;
end;

function IsPreWord( S : string ) : boolean;
begin
  IsPreWord:=PreWords^.IndexOf(@S)<>-1;
end;

function IsNewWord( S : string ) : boolean;
begin
  IsNewWord:=NewWords^.IndexOf(@S)<>-1;
end;

procedure WordsInit( var fWords : text );
begin

  ResWords:=New( PStringCollection, Init( 1, 1 ));
  NewWords:=New( PWordCollection, Init( 1, 1 ));

  LoadTextFile( fWords, 'Loading reserved words file', ResWords, True, True );

  PreWords:=New( PStringCollection, Init( 1, 1 ));
  With PreWords^ do begin
    Insert( NewStr( 'PROGRAM' ) );
    Insert( NewStr( 'PROCEDURE' ) );
    Insert( NewStr( 'FUNCTION' ) );
    Insert( NewStr( 'UNIT' ) );
  end;

  PstWords:=New( PStringCollection, Init( 1, 1 ));
  With PstWords^ do begin
    Insert( NewStr( 'VAR' ) );
    Insert( NewStr( 'LABEL' ) );
    Insert( NewStr( 'TYPE' ) );
    Insert( NewStr( 'CONST' ) );
  end;

end;

procedure WordsDone;
begin
  Dispose( NewWords, Done );
  Dispose( PreWords, Done );
  Dispose( PstWords, Done );
  Dispose( ResWords, Done );
end;

end.
