# HackInScience CLI

This is a POC of what we could do on command line:

```bash
$ hkis list
Django view
Hello World
Print 42
Number of seconds in a year
Using operators
Characters counting
...

$ hkis get Print 42
Downloaded print-42.py, you can upload it back using:

$ hkis check print-42.py
Your code printed nothing, did you forgot to call the
[print](https://docs.python.org/3/library/functions.html#print) function?

$ echo 'print(42)' >> print-42.py
$ hkis check print-42.py
 `42` is the answer. Well done!
```
