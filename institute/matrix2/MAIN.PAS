{$A+,B-,D+,E+,F-,I+,L+,N-,O-,R-,S+,V-}
{$M 16384,0,655360}
{ ************************************************************************ }
{ *                                                                      * }
{ *  Модyль:     MAIN                                                    * }
{ *  Hазначение: Оpганизация основного меню                              * }
{ *  Веpсия:     2.0                                                     * }
{ *  Автоp:      Александp Демин, МАИ, каф. 302, 1995                    * }
{ *  Язык:       Turbo Pascal 5.5                                        * }
{ *                                                                      * }
{ ************************************************************************ }

Unit Main;

interface

uses Common, Message, Events, Crt, MatInput, Check, Ident, Texts,
     Trans,  MultNum, AddMat, MultMat, Screen, InpStr, Wins;

  procedure Start;          { Cтаpт пpогpаммы }

implementation

{ *********************************************************************** }
{ ---                  Оpганизация основного диалога                  --- }
{ *********************************************************************** }

procedure Start;
var
  i       : integer;                              { Выбоp меню }
  Res     : boolean;
begin
  repeat
    i:=Menu( False, 0, MainNum, MainButs );       { Главное меню }
    case i of
      cmInput     : InputMats;
      cmEqu       : CheckEqu( @MatrixA, @MatACol, @MatARow,
                              @MatrixB, @MatBCol, @MatBRow );
      cmAbout     : i:=MessageBox( AboutMsg, OkNum, OkButs );
      cmExit, 0   : begin
                      i:=MessageBox( ExitMsg, YesNum, YesButs );
                      if i=1 then i:=cmExit;
                    end;
      cmType      : begin
                      CheckType( @MatrixA, @MatACol, @MatARow );
                      PutBox( 1, 1, MainBackX-2, ScrBottom-1,
                              ' ', bcLightBlue );
                    end;
      cmDelay     : begin
                      ClearMainBox;
                      Res:=InpNumberMsg( DelayMsg, ShowDelay,
                                         DelayMin, DelayMax,
                                         False );
                    end;
      cmTrans     : Transpon( @MatrixA, @MatACol, @MatARow );
      cmMultNumber: MultNumber( @MatrixA, @MatACol, @MatARow );
      cmAdd       : AddMats( @MatrixA, @MatACol, @MatARow,
                             @MatrixB, @MatBCol, @MatBRow );
      cmMultMat   : MultMats( @MatrixA, @MatACol, @MatARow,
                              @MatrixB, @MatBCol, @MatBRow );
    end;
  until i=cmExit;
end;

end.