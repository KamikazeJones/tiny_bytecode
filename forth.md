# data Stack

# parse Numbers

# dictionary

## dictionary entry format

| name   | example         | length in bytes | description                                          |
|--------|-----------------|-----------------|------------------------------------------------------|
| length | `[4]`           | 1               | length of the word name                              |
| name   | `[DRO]`         | 3               | first three letters of the name (padded with spaces) |
| link   | `[LA-lo LA-hi]` | 2               | link address to previous word header                 |
| cfield | `[CA-lo CA-hi]` | 2               | code field                                           |
| pfield | `mc or tc`      | n               | parameter field, n bytes, machine- or threaded code  |

---

## header (caddr u -- pfa)

- `caddr` : caddr of name  
- `u`     : length of name  
- `pfa`   : parameter field address

Global variables used: 
- `h` - header pointer to next free dictionary entry 
- `l` - latest word pointer

### "header" written in c-like pseudocode

```c
int *header(int *caddr, int u) {
    // ; store length
    *h = (unsigned char) u;

    // ; store 3 bytes of name, padded with spaces 
    for (int i = 0; i < 3; i++) {
        *(h + 1 + i) = (i < u ? *(caddr + i) : ' ');
    }

    // set link
    *(h+4) = (unsigned char) (l | 0xff)
    *(h+5) = (unsigned char) (l >> 8)

    // return code field address
    return h+6;
}
```
### "Prolog"
```Python
$b$a - > o!        # store 1 into o

b b @b @b @b ?  # jump to label b
:a:b
```

### "header" written in tiny bytecode
```Python
# header (caddr u -- cfieldaddr)
u!               # store length to u
c!               # store caddr to c

# store length
u@ h@ !          # store u to h-pointer

# store 3 bytes of name, padded with spaces
o@<<<<< s!             # s = 0x20 (space)
h@ o@ + t!             # t = h+1
o@ < o@ + d!           # d = 3
o@ o@ - i!             # i = 0           
$e e!                  # e := end of loop
$f f!                  # f:= start of for loop
$k k!                  # k := skip read char, stay with space
$n n!                  # n := noskip, read char from caddr+i
:f 
     s@ x!             # x = s 
     i@ u@ n@ k@ k@ ?  # i >= u? then use space
:n
     c@ i@ + @ x!      # x = *(c+i); read character from caddr+i
:k  
     x@ t@ i@ + !      # *(t+i) = x; store character in header
     i@ o@ + i!        # i += 1
     i@ d@ f@ e@ e@ ?  # i<3? then jump to start (f) of for-loop     
:e
l@ h@ o@<< + !   # *(*h+4) = l; store link to previous word
h@ o@<< + o@< +   # return (*h+6)
;
```