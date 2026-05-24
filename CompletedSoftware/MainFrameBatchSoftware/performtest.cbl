       program-id. performtest.

       environment division.
       configuration section.

       data division.
       working-storage section.
       01  test-variable pic 9(2).
       01  test-bit pic 1.
       linkage section.

       procedure division.

       move 5 to test-variable.
       display test-variable.
       move 1 to test-bit.
       display test-bit.
       perform say-hi.
       perform program-done.

       say-hi.
           display "hi".

       program-done.
           stop run.

    
