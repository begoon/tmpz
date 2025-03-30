{$A+,B-,D+,E-,F+,G+,I+,L+,N-,O-,P-,Q-,R-,S-,T-,V-,X+,Y+}
{$M 16384,8192,655360}

program CRef;

uses Objects, Drivers, Views, Menus, Dialogs,
     StdDlg, MsgBox, App, GadGets, Words, XRef,
     HeapChk, About, TextLoad, ChkLine;

const

  Copyright = 
    'Cross-reference table maker  ' +
    'Version 1.0  ' +
	  'Copyright (c) 2025 by Alexander Demin';

  cmStart    = 200;
  cmCRef     = 201;
  cmConfig    = 202;
  cmAbout    = 204;

  hcHelp     = 100;
  hcResults  = 101;
  hcMain     = 102;

const
  Story: array[0..7] of string = (
    'What is all about?',
    '~Retro~ programming is fun!',
    ' ',
    'Borland Pascal 7.0 + Turbo Vision 2.0',
    ' ',
    'DOSBox-X + VSCode IDE',
    ' ',
    '~LDA / STA~'
);

type
  PCRefApp = ^TCRefApp;
  TCRefApp = object(TApplication)
    Heap: PHeapView;
    Clock: PClockView;

    AboutStrs: PAboutCollection;

    constructor Init;
    destructor Done; virtual;
    procedure HandleEvent(var Event: TEvent); virtual;
    procedure Idle; virtual;
    procedure InitStatusLine; virtual;
    procedure OutOfMemory; virtual;
    procedure MainMenu;
    procedure CRef;
    procedure Config;
    procedure About;
  end;

  PResults = ^TResults;
  TResults = Object(TScroller)
    Lines     : PSCollection;
    constructor Init(R : TRect; HB, VB : PScrollBar;
                      var fOut : text);
    procedure Draw; virtual;
    destructor Done; virtual;
  end;

  PCRefWindow = ^TCRefWindow;
  TCRefWindow = object(TWindow)
    Interrior : PResults;
    constructor Init(var R : TRect; var fOut : Text);
    procedure HandleEvent(var Event: TEvent); virtual;
  end;

const

  sIn       : FNameStr = 'IN.TXT';
  sOut      : FNameStr = 'OUT.TXT';
  sWords    : FNameStr = 'WORDS.TXT';

var

  CRefApp   : TCRefApp;
  guard       : THeapCheck;

  fIn       : text;
  fOut      : text;
  fWords    : text;

function LongToStr(D : longint): string;
var
  S: string;
begin
  Str(D:3, S);
  LongToStr := S;
end;

constructor TCRefWindow.Init;
var
  T : TRect;
  S : String;
begin
  inherited Init(R, 'Cross-reference table', wnNoNumber);
  T.Copy(R); T.Grow(-1, -1);
  Interrior:= New(PResults, Init(T,
    StandardScrollBar(sbHorizontal or sbHandleKeyboard),
    StandardScrollBar(sbVertical or sbHandleKeyboard),
    fOut));
  Insert(Interrior);
end;

procedure TCRefWindow.HandleEvent;
var
  R : TRect;
  i : integer;
begin
  case Event.What of
    evKeyDown: if Event.KeyCode=kbEsc then begin
                 EndModal(cmClose);
                 ClearEvent(Event);
               end;
    evCommand: case Event.Command of
                 cmClose: begin
                            EndModal(cmClose);
                            ClearEvent(Event);
                          end;
                 cmHelp : begin
                            R.Assign(16, 8, 65, 16);
                            MessageBoxRect(R,
                              ^C'Help system '+
                                'isn''t available in this version',
                                nil, mfInformation+mfOkButton);
                          end;
               end;
  end;
  inherited HandleEvent(Event);
end;

constructor TResults.Init;
var
  S : string;
begin
  inherited Init(R, HB, VB);                            
  GrowMode := gfGrowHiX+gfGrowHiY;                          
  Lines := New(PSCollection, Init(1, 1));               
  LoadTextFile(fOut, 'Loading result file', Lines, True, True);
  HelpCtx := hcResults;                                     
  SetLimit(255, Lines^.Count);                          
end;

destructor TResults.Done;
begin
  Dispose(Lines, Done);
  inherited Done;
end;

procedure TResults.Draw;
var
  B : TDrawBuffer;
  S : String;
  i : integer;
begin
  for i:=0 to Pred(Size.Y) do begin
    MoveChar(B, ' ', GetColor(1), Size.X);
    if (i+Delta.Y<Lines^.Count) then begin
      S:=PString(Lines^.At(i+Delta.Y))^;
      S:=Copy(S, Delta.X+1, Length(S)-Delta.X);
      if Length(S)>Size.X then S[0]:=Chr(Size.X);
      MoveStr(B, S, GetColor(1));
    end;
    WriteBuf(0, i, Size.X, 1, B);
  end;
end;

constructor TCRefApp.Init;
var
  Event : TEvent;
  R     : TRect;
  i     : integer;
begin
  inherited Init;

  GetExtent(R);
  R.A.X := R.B.X - 9;
  R.B.Y := R.A.Y + 1;
  Clock := New(PClockView, Init(R));
  Insert(Clock);

  GetExtent(R);
  Dec(R.B.X);
  R.A.X := R.B.X - 9;
  R.A.Y := R.B.Y - 1;
  Heap := New(PHeapView, Init(R));
  Insert(Heap);

  AboutStrs := New(PAboutCollection, Init(1, 1));
  for i := Low(Story) to High(Story) do
    AboutStrs^.Insert(NewStr(Story[i]));

  Event.Command := cmStart;
  Event.What := evCommand;
  PutEvent(Event);
end;

destructor TCRefApp.Done;
begin
  Dispose(AboutStrs, Done);
  inherited Done;          
end;

procedure TCRefApp.Idle;
begin
  inherited Idle;
  Clock^.Update;
  Heap^.Update;
end;

procedure TCRefApp.InitStatusLine;
var
  R: TRect;
begin
  GetExtent(R);
  R.A.Y := R.B.Y - 1;
  StatusLine := New(PStatusLine, Init(R,
    NewStatusDef(hcResults, hcResults,
      NewStatusKey('~F1~ Help', kbF1, cmHelp,
      NewStatusKey('~Ctrl-F5~ Move/Resize', kbCtrlF5, cmResize,
      NewStatusKey('~Esc~ Close', kbAltF3, cmClose, nil))),
      NewStatusDef(hcAbout, hcAbout,
      NewStatusKey('~Alt-I~ Info about program', kbAltI, cmAboutView, nil),
      NewStatusDef(hcAboutView, hcAboutView,
      NewStatusKey('~Esc~ Close dialog', kbEsc, cmClose, nil),
    nil)))));
end;

procedure TCRefApp.HandleEvent;
begin
  if (Event.What and evCommand <> 0) and (Event.Command = cmStart) then
  begin
    MainMenu;
    Message(Application, evCommand, cmQuit, nil);
  end;
  inherited HandleEvent(Event);
end;

procedure TCRefApp.MainMenu;
var
  R      : TRect;
  M      : PMenuBox;
  Result : Word;
  Event  : TEvent;
begin
  R.Assign(25,6,60,20);
  M:=New(PMenuBox,Init(R,
           NewMenu(
              NewItem('~T~able    ','...',kbAlt1,cmCRef,hcNoContext,
              NewItem('~O~ptions  ','...',kbAlt2,cmConfig,hcNoContext,
              Newline(
              NewItem('~A~bout    ','',kbAlt3,cmAbout,hcNoContext,
              NewLine(
              NewItem('~E~xit     ','Alt-X',kbAltX,cmQuit,hcNoContext,
         nil))))))),
  nil));
  M^.Options:=M^.Options or ofCentered;
  Insert(M);
  repeat
    HelpCtx:=hcMain;
    Result:=M^.Execute;
    if (Result=cmCRef) or (Result=cmConfig) or (Result=cmAbout) then begin
      Delete(M);
      case Result of
        cmAbout: About;
        cmConfig: Config;
        cmCRef: CRef;
      end;
      Insert(M);
    end;
    Event.What := evNothing;
    M^.PutEvent(Event);
  until Result=cmQuit;
  Delete(M);
  DisposeMenu(M^.Menu);
  Dispose(M,Done);
end;

procedure TCRefApp.CRef;
var
  R      : TRect;
  S      : string;
  W      : PCrefWindow;
  MaxSize: longint;
  T      : file of byte;
begin
  Assign(T, sIn);
  Reset(T);
  MaxSize:=FileSize(T);
  Close(T);
  Assign(fIn, sIn);
  Reset(fIn);
  Assign(fWords, sWords);
  Reset(fWords);
  Assign(fOut, sOut);
  ReWrite(fOut);
  MakeCref(fIn, fWords, fOut, MaxSize);
  Close(fIn);
  Close(fOut);
  Close(fWords);

  DeskTop^.GetExtent(R);
  Assign(fOut, sOut);
  Reset(fOut);
  W:=New(PCRefWindow, Init(R, fOut));
  Close(fOut);
  DeskTop^.ExecView(W);
  Dispose(W, Done);

end;

procedure TCRefApp.Config;
var
  DataRec : record
              sdIn    : FNameStr;
              sdOut   : FNameStr;
              sdWords : FNameStr;
            end;
  D       : PDialog;
  R       : TRect;
  L       : PView;
begin
  R.Assign(0,0,40,13);
  D:=New(PDialog, init(R,'Options'));
  with D^ do begin
    Options:=Options or ofCentered;

    R.Assign(2, 2, 38, 3);
    L:=New(PCheckInputLine, Init(R, SizeOf(FNameStr)-1, True));
    R.Assign(2, 1, 38, 2);
    Insert(New(PLabel, Init(R, '~P~rocessing file', L)));
    Insert(L);

    R.Assign(2, 5, 38, 6);
    L:=New(PCheckInputLine, Init(R, SizeOf(FNameStr)-1, False));
    R.Assign(2, 4, 38, 5);
    Insert(New(PLabel, Init(R, '~O~utput file', L)));
    Insert(L);

    R.Assign(2, 8, 38, 9);
    L:=New(PCheckInputLine, Init(R, SizeOf(FNameStr)-1, True));
    R.Assign(2, 7, 38, 8);
    Insert(New(PLabel, Init(R, '~R~eserved words file', L)));
    Insert(L);

    R.Assign(1,10,19,12);
    Insert(New(PButton, Init(R, '~O~K', cmOk, bfDefault)));

    R.Assign(21,10,39,12);
    Insert(New(PButton, Init(R, '~C~ancel', cmCancel, bfNormal)));
  end;
  with DataRec do begin
    sdIn:=sIn;
    sdOut:=sOut;
    sdWords:=sWords;
  end;
  if Application^.ExecuteDialog(D,@DataRec) = cmOk then begin
    with DataRec do begin
      sIn:=sdIn;
      sOut:=sdOut;
      sWords:=sdWords;
    end;
  end;
end;

procedure TCRefApp.About;
var
  dialog: PAboutDialog;
  control: PView;
  R: TRect;
begin
  R.Assign(0, 0, 50, 12);
  dialog := New(PAboutDialog, Init(R, 'About', AboutStrs));
  with dialog^ do begin
    Options := Options or ofCentered;
    R.Assign(1, 2, 39, 3);
    control := New(PStaticText, Init(R, ^C'  Cross-reference table maker  '));
    control^.Options := control^.Options or ofFramed or ofCenterX;
    Insert(control);

    R.Assign(1, 5, 39, 11);
    control := New(PStaticText, Init(R, 
      ^C'Version 1.0 ' + 
      ^M^M +
      ^C'Copyright (c) 2025 by Alexander Demin'));
    control^.Options := control^.Options or ofCenterX;
    Insert(control);

    R.Assign(15, 9, 25, 11);
    control := New(PButton, Init(R, '~O~K', cmOk, bfDefault));
    control^.Options := control^.Options or ofCenterX;
    Insert(control);
  end;
  Application^.ExecuteDialog(dialog, nil);
end;

procedure TCrefApp.OutOfMemory;
begin
  MessageBox('~PANIC~: out of memory', nil, mfError + mfOKButton);
end;

begin
  guard.Init;

  CRefApp.Init;
  CRefApp.Run;
  CRefApp.Done;

  writeln(Copyright);

  guard.Done;
end.
