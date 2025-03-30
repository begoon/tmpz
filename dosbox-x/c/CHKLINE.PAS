{$A+,B-,E-,F+,G+,I+,L+,N-,O-,P-,Q-,R-,S-,T-,V-,X+,Y+}
{$M 16384,8192,655360}
Unit ChkLine;

Interface

Uses Objects, Dialogs, MsgBox, Views, Words;

Type

  PCheckInputLine = ^TCheckInputLine;
  TCheckInputLine = object ( TInputLine )
    LType : boolean;
    constructor Init( var Bounds: TRect; AMaxLen: Integer; AType : boolean );
    function Valid( Command : word ) : boolean; virtual;
  end;

implementation

function Min ( x, y : integer ) : integer;
begin
   if x>y then Min:=y else Min:=x;
end;

constructor TCheckInputLine.Init;
begin
  inherited Init( Bounds, AMaxLen );
  LType:=AType;
end;

function TCheckInputLine.Valid;
var
  fCheck : file of byte;
  R      : TRect;
begin
  if not ( Command in [cmValid, cmCancel] ) then begin
    Select;
    if Data^='' then begin
      R.Assign( 18, 8, 62, 16 );
      MessageBoxRect( R, ^C'File name can''t be empty!', nil,
                      mfError+mfOkButton );
      Valid:=False;
    end else begin
      Assign( fCheck, Data^ );
      {$I-} if LType then Reset( fCheck ) else ReWrite( fCheck ); {$I+}
      if IOResult<>0 then begin
        R.Assign( 10, 8, 70, 16 );
        Data^:=UpStr( Data^ );
        Valid:=False;
        if LType
          then MessageBoxRect( R, ^C'File '''+Data^+''' doesn''t exist',
                               nil, mfError+mfOkButton )
          else MessageBoxRect( R, ^C'Unable to create '''+Data^+''' file',
                               nil, mfError+mfOkButton )
      end
    end;
  end
  else Valid:=Inherited Valid( Command );
end;

end.