# VM Operationen in TBC (tiny bytecode)

Die 17 Grundoperationen der virtuellen Maschine, das Kommentarzeichen (#) und sowie die optionale Vorlauf-Logik zum Entfernen von Leerzeichen und Kommentaren werden hier dokumentiert.

**Stack-Notation**: Die Operationen werden mit der FORTH-Konvention `( before -- after )` beschrieben. Links vom `--` stehen die Eingabewerte auf dem Stack (von unten nach oben), rechts die Ausgabewerte nach der Operation. Der oberste Stack-Wert steht jeweils ganz rechts. Bei Operationen, die den Return-Stack verwenden, wird dieser mit `| R:` getrennt in derselben Klammer notiert: `( before -- after | R: before -- after )`.

**Operationen**:

1. `+` **( a b -- a+b )** : Addition (add)  
   Nimmt die beiden obersten Werte vom Stack, addiert sie und legt das Ergebnis zurück auf den Stack.
2. `-` **( a b -- a-b )** : Subtraktion (sub)  
   Nimmt die beiden obersten Werte vom Stack, subtrahiert b von a und legt das Ergebnis zurück auf den Stack.
3. `*` **( n -- n*2 )** : Verdoppeln (shl)  
   Nimmt den obersten Wert vom Stack, verdoppelt ihn (Bitshift nach links) und legt das Ergebnis zurück.
4. `/` **( n -- n/2 )** : Halbieren (shr)  
   Nimmt den obersten Wert vom Stack, halbiert ihn (Bitshift nach rechts) und legt das Ergebnis zurück.
5. `@` **( addr -- value )** : Dereferenzieren (fetch)  
   Nimmt eine Adresse vom Stack, liest den Wert an dieser Speicheradresse und legt ihn auf den Stack.
6. `!` **( value addr -- )** : Schreiben (store)  
   Nimmt einen Wert und eine Adresse vom Stack und schreibt den Wert an die Speicheradresse. Der Stack wird dabei geleert.
7. `&` **( addr -- | R: -- return_addr )** : Subroutinen-Sprung (call)  
   Nimmt eine Sprungadresse vom Data-Stack, legt die aktuelle Rücksprung-Adresse auf den Return-Stack und springt zur angegebenen Adresse.
8. `;` **( -- | R: return_addr -- )** : Rückkehr aus Subroutine (return)  
   Nimmt die Rücksprung-Adresse vom Return-Stack und springt zu dieser Adresse zurück.
9. `>` **( n -- | R: -- n )** : Auf Return-Stack (to-r)  
   Nimmt den obersten Wert vom Data-Stack und legt ihn auf den Return-Stack. Entspricht `>R` in FORTH.
10. `<` **( -- n | R: n -- )** : Von Return-Stack (from-r)  
   Nimmt den obersten Wert vom Return-Stack und legt ihn auf den Data-Stack. Entspricht `R>` in FORTH.
11. `?` **( n addr -- )** : Bedingter Sprung (branch-if)  
   Nimmt einen Wert und eine Sprungadresse vom Stack. Wenn der Wert größer als 0 ist, springt die Ausführung zur angegebenen Adresse.
12. `$x` **( -- addr )** : Label-Adresse laden (label-ref)  
   Liest das folgende Byte als Labelnamen `x`, sucht **vorwärts** ab der aktuellen Position nach dem nächsten Label `:x` im Code und legt dessen Adresse auf den Stack. Das Label muss daher im Code **nach** der `$x` Referenz definiert sein.
13. `:x` **( -- )** : Label definieren (label-def)  
   Liest das folgende Byte als Labelnamen `x` und definiert ein Label an der aktuellen Position. Der Interpreter führt beim Erreichen eines Labels keine Aktion aus und setzt die Ausführung direkt danach fort.
14. `.` **( n -- )** : Zeichen ausgeben (emit)  
   Nimmt den obersten Wert vom Stack, maskiert ihn mit 0xFF (um ein Byte zu erhalten) und gibt das entsprechende ASCII-Zeichen auf stdout aus.
15. `,` **( -- n )** : Zeichen einlesen (key)  
   Liest ein Zeichen von stdin und legt dessen Byte-Wert (0-255) auf den Stack. Bei EOF wird -1 auf den Stack gelegt.
16. `^` **( -- )** : Halt (halt)  
   Beendet die VM sofort. Die Ausführung wird an dieser Stelle abgebrochen.
17. `#` **( -- )** : Kommentar (comment)  
   Markiert den Beginn eines Kommentars. Alles nach `#` bis zum Zeilenende wird vom Interpreter ignoriert.
18. `x` **( -- addr )** : Variable (var)  
   Legt die Speicheradresse der Variablen `x` (beliebiger Buchstabe a-z) auf den Stack. Variablen dienen als Speicherplätze. Um den Wert einer Variablen zu lesen, schreibt man `x@`. Man schreibt den Wert auf dem Stack mit  `x!` nach Variable `x`. Beispiel: `o@** x!` lädt 1 aus Variable `o`, verdoppelt zweimal (ergibt 4) und speichert den Wert in Variable x. 

---

**Code-Layout und Initialisierung:**

Der Bytecode liegt linear im Speicher. Jede Operation belegt genau 1 Byte, außer `:x` und `$x`, die jeweils 2 Bytes belegen (Opcode + Labelname).

**Initialisierung der Konstante 1:**

Da die VM keine Operation zum direkten Laden von Literal-Werten besitzt, wird die Konstante 1 durch die Differenz zweier aufeinanderfolgender Labels erzeugt:
```
$b $a - / o !    # Berechne (addr_b - addr_a) / 2 = ((X+2) - X) / 2 = 2/2 = 1
:a:b:            # Zwei Labels direkt hintereinander, Abstand = 2 Bytes
```

Diese Methode ist portabel, solange garantiert ist, dass jedes Label `:x` genau 2 Bytes belegt. Mit der in Variable `o` gespeicherten 1 können alle anderen benötigten Konstanten durch Addition, Subtraktion und Shift-Operationen (`*`, `/`) erzeugt werden.

**Parser/Vorlauf**:
- Vor der Interpretation können **Kommentare** und **Leerzeichen** entfernt werden.
- Kommentare starten mit `#` und gehen bis zum Ende der aktuellen Zeile.
- Leerzeichen sind für die Ausführung nicht relevant.
- Eine naive Implementation des Bytecode-Interpreters - z.B. in Maschinencode - kann den Vorlauf auch auslassen.

---

**Motivation:**
Die VM soll möglichst simpel gehalten werden, damit sie ohne Assembler direkt in Maschinensprache umgesetzt werden kann. Dies betrifft insbesondere die Operationen und das Parsing.

**Tasks:**
- Dokumentation der 17 Operationen und des Parsing-Vorlaufs im Repository.
- Beispielimplementierung für den Vorlauf (Entfernen von Leerzeichen und Kommentaren).
- Tesfunktion schreiben, die nach der Ausführung den Stack vergleicht mit den Sollwerten.

**Optional:** Vorschläge für die Erweiterbarkeit oder Implementierung können in den Kommentaren ergänzt werden.