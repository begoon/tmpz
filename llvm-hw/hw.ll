; declare the external printf function
declare i32 @printf(i8*, ...)

@.str = private constant [5 x i8] c"abc\0A\00" ; "abc\n" + null terminator

define i32 @main() {
entry:
  ; get a pointer to the string constant
  %0 = getelementptr [4 x i8], [4 x i8]* @.str, i32 0, i32 0
  ; call printf with the string
  %1 = call i32 (i8*, ...) @printf(i8* %0)
  ret i32 0
}
