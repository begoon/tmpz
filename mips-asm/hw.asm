        .data
msg:    .asciiz "Hello, World!\n"

        .text
        .globl main
main:
        # Print the string at 'msg'
        la   $a0, msg       # $a0 = address of string
        li   $v0, 4         # syscall 4 = print_string
        syscall

        # Exit program
        li   $v0, 10        # syscall 10 = exit
        syscall

