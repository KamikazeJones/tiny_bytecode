# VM Operationen in TBC (tiny bytecode)

"Die 17 Grundoperationen der virtuellen Maschine, das Kommentarzeichen (#) und sowie die optionale Vorlauf-Logik zum Entfernen von Leerzeichen und Kommentaren werden hier dokumentiert."

**Operationen**:

1. `+`    : Addition
2. `-`    : Subtraktion
3. `*`    : Verdoppeln (×2, Bitshift left)
4. `/`    : Halbieren (÷2, Bitshift right)
5. `@`    : Dereferenzieren (read)
6. `!`    : Schreiben (write)
7. `&`    : "Jump Subroutine" – legt Rücksprung-Adresse auf den Return-Stack
8. `;`    : "Return from Subroutine"
9. `>`    : Wert von Data-Stack auf Return-Stack
10. `<`   : Wert von Return-Stack auf Data-Stack
11. `?`   : Conditional Jump – springt zu in Variable gespeicherter Adresse, falls Wert auf Stack > 0
12. `$x`  : Legt Adresse vom nächsten Label `:x` auf den Stack
13. `:x`  : Definiert ein Label `x`
14. `.`   : Pop Wert von Data-Stack und schreibe das Zeichen (ASCII) des (Wert & 0xFF) auf stdout
15. `,`   : Lese ein Zeichen von stdin und lege dessen Byte-Wert (0-255) auf den Data-Stack; bei EOF wird -1 gelegt
16. `^`   : Halt — beendet die VM sofort, sobald dieses Opcode ausgeführt wird
17. `#`   : Kommentar – alles nach `#` bis Zeilenende wird ignoriert

**Parser/Vorlauf**:
- Vor der Interpretation können **Kommentare** und **Leerzeichen** entfernt werden.
- Kommentare starten mit `#` und gehen bis zum Ende der aktuellen Zeile.
- Leerzeichen sind für die Ausführung nicht relevant.
- Eine naive Implementation des Bytecode-Interpreters - z.B. in Maschinencode - kann den Vorlauf auch auslassen.

---

**Motivation:**
Die VM soll möglichst simpel gehalten werden, damit sie ohne Assembler direkt in Maschinensprache umgesetzt werden kann. Dies betrifft insbesondere die Operationen und das Parsing.

**Tasks:**
- Dokumentation der 13+1 Operationen und des Parsing-Vorlaufs im Repository.
- Beispielimplementierung für den Vorlauf (Entfernen von Leerzeichen und Kommentaren).
- Kommentare im Code entsprechend auszeichnen.

**Optional:** Vorschläge für die Erweiterbarkeit oder Implementierung können in den Kommentaren ergänzt werden.