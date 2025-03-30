{$A+,B-,E-,F+,G+,I+,L+,N-,O-,P-,Q-,R-,S-,T-,V-,X+,Y+}
{$M 16384,8192,655360}
Unit TextLoad;

interface

Uses Objects, RunLine, Words;

procedure LoadTextFile( var fText : text; Title : string;
                        Lines : PCollection; Show, NeedUp : boolean );

implementation

procedure LoadTextFile;
var
  Runner : PRunningLine;
  Size   : Longint;
  S      : string;
  Maked  : Longint;
begin

  Reset( fText );
  asm
    les di, fText
    mov bx, es:[di]
    xor cx, cx
    xor dx, dx
    mov ax, 4202h
    int 21h
    mov word ptr Size, ax
    mov word ptr Size+2, dx
  end;

  if Show then Runner:=New( PRunningLine,
                            Init( Title, Size, 40, riRunningLine ) );

  Reset( fText );
  Maked:=0;
  while not Eof( fText ) do begin
    Readln( fText, S );
    if NeedUp then S:=UpStr(S);
    Lines^.Insert( NewStr( S ) );
    if Show then Runner^.StatusDisplay( Maked );
    Maked:=Maked+Length(S)+2;
  end;
  if Show then Runner^.StatusDisplay( Size );
  if Show then Dispose( Runner, Done );
end;

end.
